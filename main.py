import os
import time
import json
import requests
import logging
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

# ✅ CORS Configuration
origins = [
    "https://frontend-kbjv.onrender.com",  # ✅ Allow frontend to call API
    "http://localhost:3000"  # ✅ Allow local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # ✅ Explicitly allow these methods
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

# Function to extract text from website pages
def extract_text_from_website(base_url):
    pages_to_check = [
        base_url,
        f"{base_url}/privacy-policy",
        f"{base_url}/terms-of-service"
    ]
    extracted_text = ""

    options = Options()
    options.binary_location = get_chrome_binary()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(get_chromedriver_binary())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        for page in pages_to_check:
            logger.info(f"Scraping page: {page}")
            driver.get(page)
            time.sleep(5)  # Allow full page load
            soup = BeautifulSoup(driver.page_source, "html.parser")
            extracted_text += soup.get_text(separator="\n", strip=True) + "\n\n"

        if len(extracted_text) < 100:
            logger.warning(f"Extracted text from {base_url} appears too short, might have missed content.")
        
        return extracted_text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from {base_url}: {e}")
        return ""
    finally:
        driver.quit()

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
        "response_format": {"type": "json_object"}  # ✅ Ensures JSON consistency
    }

    logger.info(f"Sending OpenAI request with payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"OpenAI API Response: {json.dumps(response_data, indent=2)}")

        if "choices" in response_data and response_data["choices"]:
            return json.loads(response_data["choices"][0]["message"]["content"])
        else:
            return {"error": "Invalid AI response format."}

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err.response.text}")
        return {"error": f"OpenAI API Error: {http_err.response.text}"}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred: {req_err}")
        return {"error": "AI processing failed due to request issue."}

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

    return response

@app.options("/check_compliance")
def options_check_compliance():
    """Handle CORS preflight requests explicitly"""
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
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
