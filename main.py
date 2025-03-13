import os
import time
import json
import requests
import logging
from urllib.parse import urljoin, urlparse
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from threading import Lock

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

# Driver Pool
driver_pool = []
pool_lock = Lock()
pool_size = 5  # adjust as needed.

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
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    service = Service(get_chromedriver_binary())
    try:
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        logger.error(f"Failed to start ChromeDriver: {e}")
        raise HTTPException(status_code=500, detail="Failed to start browser session. Check server configuration.")

def get_driver_from_pool():
    with pool_lock:
        if driver_pool:
            return driver_pool.pop()
        if len(driver_pool) < pool_size:
            return initialize_driver()
        else:
            return initialize_driver()

def return_driver_to_pool(driver):
    with pool_lock:
        driver_pool.append(driver)

# Function to enforce www. on website URL
def enforce_www(website_url):
    if "www." not in website_url:
        website_url = website_url.replace("https://", "https://www.", 1) if website_url.startswith(
            "https://"
        ) else f"https://www.{website_url}"
    return website_url

def extract_text_from_website(base_url):
    original_base_url = base_url
    base_url = enforce_www(base_url)
    logger.info(f"Checking compliance for: {base_url}")
    driver = get_driver_from_pool()
    extracted_text = ""
    pages_to_check = [base_url]
    base_domain = urlparse(base_url).netloc
    source_urls = {}

    def fetch_page(url):
        try:
            driver.set_page_load_timeout(300)
            driver.get(url)
            time.sleep(15)

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

            return BeautifulSoup(driver.page_source, "html.parser")
        except Exception as e:
            logger.error(f"Failed to fetch page {url}: {e}")
            return None

    try:
        soup = fetch_page(base_url)
        if soup is None:
            return "", {}

        # Explicitly check non-www privacy policy first
        non_www_privacy_url = f"{base_url.replace('www.', '')}/privacy-policy/"
        if "www." not in original_base_url:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(non_www_privacy_url, allow_redirects=True, timeout=10, headers=headers)
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {response.headers}")
                if response.status_code == 200:
                    pages_to_check = [non_www_privacy_url]  # Start ONLY with this page
                    logger.info(f"Forced pages_to_check: {pages_to_check}")  # Log forced URLs
                time.sleep(2) #Add delay.
            except requests.exceptions.RequestException:
                pass

        logger.info(f"pages_to_check before link parsing: {pages_to_check}")

        for link in soup.find_all("a", href=True):
            try:  # Add a try block here
                href = link["href"].strip()
                if href.startswith("mailto:"):
                    continue
                parsed_href = urlparse(urljoin(base_url, href))
                if parsed_href.netloc and parsed_href.netloc != base_domain:
                    continue

                link_text = link.get_text(strip=True).lower()
                if any(keyword in link_text or keyword in href.lower() for keyword in ["privacy", "terms", "legal", "policy"]):
                    absolute_url = urljoin(base_url, href)
                    pages_to_check.append(absolute_url)

                    sub_soup = fetch_page(absolute_url)
                    if sub_soup is None:
                        continue

                    for sub_link in sub_soup.find_all("a", href=True):
                        sub_href = sub_link["href"].strip()
                        if sub_href.startswith("mailto:"):
                            continue
                        parsed_sub_href = urlparse(urljoin(absolute_url, sub_href))
                        if parsed_sub_href.netloc and parsed_sub_href != base_domain:
                            continue
                        if any(keyword in sub_href.lower() for keyword in ["privacy", "terms", "legal"]):
                            pages_to_check.append(urljoin(absolute_url, sub_href))
            except Exception as e:  # Add except block
                logger.error(f"Error processing link: {e}")
                continue

        logger.info(f"pages_to_check after link parsing: {pages_to_check}")

        www_privacy_url = f"{base_url}/privacy-policy/"

        if "www." not in original_base_url:
            if non_www_privacy_url not in pages_to_check:
                try:
                    response = requests.head(non_www_privacy_url, allow_redirects=False, timeout=10)
                    if response.status_code == 200:
                        pages_to_check.append(non_www_privacy_url)
                except requests.exceptions.RequestException:
                    pass
        else:
            try:
                response = requests.head(www_privacy_url, allow_redirects=False, timeout=10)
                if response.status_code == 200:
                    if www_privacy_url not in pages_to_check:
                        pages_to_check.append(www_privacy_url)
            except requests.exceptions.RequestException:
                pass

        logger.info(f"pages_to_check before scraping: {pages_to_check}")

        for page in set(pages_to_check):
            logger.info(f"Scraping page: {page}")
            soup = fetch_page(page)
            if soup is None:
                continue
            page_text = soup.get_text(separator="\n", strip=True)
            extracted_text += page_text + "\n"
            source_urls[page] = page_text

        if len(extracted_text) < 100:
            logger.warning(f"Extracted text from {base_url} appears too short, might have missed content.")

        return extracted_text.strip(), source_urls

    except Exception as e:
        logger.error(f"Failed to extract text from {base_url}: {e}")
        return "", {}

    finally:
        return_driver_to_pool(driver)

# Function to check compliance using OpenAI API
def check_compliance(text, source_urls):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("Missing OpenAI API key.")
        return {"error": "Missing API key."}

    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are an AI that checks website compliance for SMS regulations. Respond **only** in JSON format containing 'json' in a key."
            },
            {
                "role": "user",
                "content": f"""
                Analyze the following website text for TCR SMS compliance. The compliance check should include **all extracted website pages**, not just the Privacy Policy and Terms & Conditions.

                **Key Compliance Requirements (Check All Pages for These Statements):**

                **Privacy Policy must contain:**
                - **Explicit statement** that SMS consent data **will not be shared** with third parties or used for marketing purposes.
                - **Clear explanation** of how consumer data is collected, used, and stored.
                - **Example Compliant Wording (AI must detect even partial matches):**
                    - "Your phone number and consent will remain confidential."
                    - "We will not sell or share your information with third parties or affiliates for marketing purposes."
                    - "SMS communication is used strictly to facilitate interactions related to our services."
                    - "We do not disclose your phone number to marketing partners."
                    - "We respect your privacy and will not use your data for promotional purposes."

                **Terms & Conditions must contain:**
                - **Description of SMS messages** users will receive.
                - **Mandatory disclosures including:**
                    - **Messaging frequency**: "Message frequency varies", "We may send multiple messages", or similar wording.
                    - **Data rates**: "Standard message and data rates may apply."
                    - **Opt-out instructions**: "To opt out, reply 'STOP' at any time." (Detect variations like "Text STOP to cancel").
                    - **Assistance instructions**: "For help, reply 'HELP' or contact support at [support URL or phone number]."
                - **Example Compliant Wording (AI should match similar phrases, even if not exact):**
                    - "Message frequency varies. Standard message and data rates may apply."
                    - "To opt out, reply 'STOP' at any time."
                    - "For help, reply 'HELP' or contact us at www.example.com or (123) 456-7890."
                    - "You can unsubscribe by texting STOP."
                    - "Messaging rates apply. Reply STOP to end messages."

                **🚀 Force AI to List All Possible Matches**
                - Before marking anything as "not found," AI must **return all similar statements found in the text**.
                - If a statement is **not counted as compliant**, AI must explain **why** it was rejected.

                **Response Format (Include detected statements, even if rejected):**
                {{
                    "json": {{
                        "compliance_analysis": {{
                            "privacy_policy": {{
                                "sms_consent_statement": {{
                                    "status": "found/not_found",
                                    "statement": "actual statement found or empty",
                                    "url": "URL where found or empty",
                                    "detected_candidates": ["list of similar statements found, even if rejected"],
                                    "rejection_reason": "If rejected, explain why here"
                                }},
                                "data_usage_explanation": {{
                                    "status": "found/not_found",
                                    "statement": "actual statement found or empty",
                                    "url": "URL where found or empty",
                                    "detected_candidates": ["list of similar statements found, even if rejected"],
                                    "rejection_reason": "If rejected, explain why here"
                                }}
                            }},
                            "terms_conditions": {{
                                "message_types_specified": {{
                                    "status": "found/not_found",
                                    "statement": "actual statement found or empty",
                                    "url": "URL where found or empty",
                                    "detected_candidates": ["list of similar statements found, even if rejected"],
                                    "rejection_reason": "If rejected, explain why here"
                                }},
                                "mandatory_disclosures": {{
                                    "status": "found/not_found",
                                    "statement": "actual statement found or empty",
                                    "url": "URL where found or empty",
                                    "detected_candidates": ["list of similar statements found, even if rejected"],
                                    "rejection_reason": "If rejected, explain why here"
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

                **🚨 Important:**
                - **Do NOT assume these statements are only in Privacy Policies or Terms & Conditions. Check all extracted pages.**
                - **Match compliance wording even if phrased differently (e.g., "We will not share your data" vs. "Your consent remains confidential").**
                - **If any statement is detected, return BOTH the found statement and its URL.**
                - **If multiple compliant statements exist, return ALL of them.**
                - **If AI is unsure, double-check all extracted text before marking a category as "not found."**
                - **Recheck the following terms before making a final determination:** ["message frequency", "reply STOP", "data sharing", "consent protection", "HELP for support"].

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

    extracted_text, source_urls = extract_text_from_website(website_url)  # get source_urls
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Failed to extract text from website.")

    compliance_result = check_compliance(extracted_text, source_urls)  # pass source_urls to check_compliance

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
