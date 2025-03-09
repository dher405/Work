import os
import time
import json
import requests
import logging
from urllib.parse import urljoin
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS Configuration
origins = [
    "https://frontend-kbjv.onrender.com",
    "https://testfrontend-z8t3.onrender.com",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Function to get Chrome binary
def get_chrome_binary():
    chrome_binary = os.environ.get("CHROME_BIN", "/opt/render/chromium/chrome-linux64/chrome")
    if not os.path.exists(chrome_binary):
        raise FileNotFoundError("Chrome binary not found! Check installation.")
    return chrome_binary

# Function to get ChromeDriver binary
def get_chromedriver_binary():
    chromedriver_binary = os.environ.get("CHROMEDRIVER_BIN", "/opt/render/chromedriver/chromedriver-linux64/chromedriver")
    if not os.path.exists(chromedriver_binary):
        raise FileNotFoundError("ChromeDriver binary not found! Check installation.")
    return chromedriver_binary

# Function to initialize Selenium WebDriver
def initialize_driver():
    options = Options()
    options.binary_location = get_chrome_binary()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    
    service = Service(get_chromedriver_binary())
    try:
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        logger.error(f"Failed to start ChromeDriver: {e}")
        raise HTTPException(status_code=500, detail="Failed to start browser session. Check server configuration.")

# Function to extract text from website
def extract_text_from_website(base_url):
    driver = initialize_driver()
    extracted_text = ""

    try:
        driver.set_page_load_timeout(300)
        driver.get(base_url)
        time.sleep(15)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract text
        extracted_text = soup.get_text(separator="\n", strip=True)

        if len(extracted_text) < 100:
            logger.warning(f"Extracted text from {base_url} appears too short, might have missed content.")

        return extracted_text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from {base_url}: {e}")
        if "www." not in base_url:
            logger.warning("Retrying with www. prepended to the domain after timeout...")
            new_url = base_url.replace("https://", "https://www.", 1) if base_url.startswith("https://") else f"https://www.{base_url}"
            try:
                driver.get(new_url)
                time.sleep(15)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                extracted_text = soup.get_text(separator="\n", strip=True)
                if extracted_text:
                    return extracted_text.strip()
            except Exception as retry_exception:
                logger.error(f"Retry with www. failed: {retry_exception}")
        return None
    finally:
        driver.quit()

# Function to retry with www. if initial request fails with 400
def retry_with_www(website_url):
    extracted_text = extract_text_from_website(website_url)
    if extracted_text:
        return extracted_text
    if "www." not in website_url:
        logger.warning("Retrying with www. prepended to the domain...")
        new_url = website_url.replace("https://", "https://www.", 1) if website_url.startswith("https://") else f"https://www.{website_url}"
        extracted_text = extract_text_from_website(new_url)
        if extracted_text:
            return extracted_text
        logger.error("Retry with www. failed.")
    raise HTTPException(status_code=400, detail="Failed to extract text from website.")

# Function to check compliance using OpenAI API
def check_compliance(text):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("Missing OpenAI API key.")
        return {"error": "Missing API key."}

    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are an AI that checks website compliance for SMS regulations. Respond **only** in JSON format containing 'json' in a key."
            },
            {
                "role": "user",
                "content": f"""
                Analyze the following website text for TCR SMS compliance. The compliance check should include:
                
                **Privacy Policy must contain:**
                - Explicit statement that SMS consent data will not be shared with third parties.
                - Clear explanation of how consumer data is collected, used, and shared.

                **Terms & Conditions must contain:**
                - Explanation of what type of SMS messages users will receive.
                - Mandatory disclosures including:
                    - Messaging frequency may vary.
                    - Message and data rates may apply.
                    - Opt-out instructions ('Reply STOP').
                    - Assistance instructions ('Reply HELP' or contact support URL').

                **Response Format (include actual found statements if detected):**

                {{
                    "json": {{
                        "compliance_analysis": {{
                            "privacy_policy": {{
                                "sms_consent_statement": {{
                                    "status": "found/not_found",
                                    "statement": "actual statement found or empty"
                                }},
                                "data_usage_explanation": {{
                                    "status": "found/not_found",
                                    "statement": "actual statement found or empty"
                                }}
                            }},
                            "terms_conditions": {{
                                "message_types_specified": {{
                                    "status": "found/not_found",
                                    "statement": "actual statement found or empty"
                                }},
                                "mandatory_disclosures": {{
                                    "status": "found/not_found",
                                    "statement": "actual statement found or empty"
                                }}
                            }},
                            "overall_compliance": "compliant/partially_compliant/non_compliant",
                            "recommendations": [
                                "Recommendation 1",
                                "Recommendation 2"
                            ]
                        }}
                    }}
                }}

                Here is the extracted website text:
                {text}
                """
            }
        ],
        "response_format": {"type": "json_object"}
    }
    
    return {}

@app.get("/check_compliance")
def check_website_compliance(website_url: str = Query(..., title="Website URL", description="URL of the website to check")):
    logger.info(f"Checking compliance for: {website_url}")

    extracted_text = extract_text_from_website(website_url)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Failed to extract text from website.")

    compliance_result = check_compliance(extracted_text)

    response = Response(content=json.dumps(compliance_result), media_type="application/json")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"

    return response

@app.options("/check_compliance")
def options_check_compliance():
    """Handle CORS preflight requests explicitly"""
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.get("/debug_chrome")
def debug_chrome():
    try:
        chrome_version = os.popen(f"{get_chrome_binary()} --version").read().strip()
        driver_version = os.popen(f"{get_chromedriver_binary()} --version").read().strip()
        return {"chrome_version": chrome_version, "driver_version": driver_version}
    except FileNotFoundError as e:
        return {"error": str(e)}
