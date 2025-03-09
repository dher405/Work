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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# Function to extract text from website pages
def extract_text_from_website(base_url):
    pages_to_check = [base_url]
    extracted_text = ""

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.set_page_load_timeout(300)  # 🔹 Increased timeout to 300 seconds

        for attempt in range(2):  # 🔹 Retry up to 2 times
            try:
                driver.get(base_url)
                WebDriverWait(driver, 60).until(  # 🔹 Increased wait time to 60 seconds
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                break  # Success, exit loop
            except Exception as e:
                logger.warning(f"Retry {attempt + 1}: Failed to load {base_url}, error: {e}")
                if attempt == 1:  # Last attempt failed
                    raise

        soup = BeautifulSoup(driver.page_source, "html.parser")

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if any(keyword in href.lower() for keyword in ["privacy", "terms", "legal"]):
                absolute_url = urljoin(base_url, href)
                pages_to_check.append(absolute_url)

                # Try loading subpages with retry logic
                try:
                    driver.set_page_load_timeout(300)
                    driver.get(absolute_url)
                    time.sleep(6)
                    sub_soup = BeautifulSoup(driver.page_source, "html.parser")
                    for sub_link in sub_soup.find_all("a", href=True):
                        sub_href = sub_link["href"]
                        if any(keyword in sub_href.lower() for keyword in ["privacy", "terms", "legal"]):
                            pages_to_check.append(urljoin(absolute_url, sub_href))
                except Exception as e:
                    logger.warning(f"Skipping {absolute_url} due to error: {e}")

        # Extract text from all pages
        for page in set(pages_to_check):  
            logger.info(f"Scraping page: {page}")
            try:
                driver.set_page_load_timeout(300)
                driver.get(page)
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                soup = BeautifulSoup(driver.page_source, "html.parser")
                extracted_text += soup.get_text(separator="\n", strip=True) + "\n\n"
            except Exception as e:
                logger.warning(f"Skipping {page} due to error: {e}")

        if len(extracted_text) < 100:
            logger.warning(f"Extracted text from {base_url} appears too short.")

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


