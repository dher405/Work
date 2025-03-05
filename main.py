import os
import time
import json
import requests
import logging
from fastapi import FastAPI, Query, HTTPException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ✅ Enable CORS to allow requests from your front-end domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend-kbjv.onrender.com"],  # Change to "*" to allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers

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

# Function to extract text from a URL
def extract_text_from_url(url):
    options = Options()
    options.binary_location = get_chrome_binary()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(get_chromedriver_binary())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(3)  # Allow time for page to load
        extracted_text = driver.find_element("tag name", "body").text
        return extracted_text
    except Exception as e:
        logger.error(f"Failed to extract text from {url}: {e}")
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
        "model": "gpt-4-turbo",
        "messages": [
            {"role": "system", "content": "You are an AI that checks website compliance for SMS regulations. Respond **only** in JSON format."},
            {"role": "user", "content": f"Analyze the following text for SMS compliance and return the results in **valid JSON**:\n{text}"}
        ],
        "response_format": {"type": "json_object"}  # ✅ Correct format
    }

    logger.info(f"Sending OpenAI request with payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"OpenAI API Response: {json.dumps(response_data, indent=2)}")
        return response_data
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err.response.text}")
        return {"error": f"OpenAI API Error: {http_err.response.text}"}
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred: {req_err}")
        return {"error": "AI processing failed due to request issue."}

@app.get("/check_compliance")
def check_website_compliance(website_url: str = Query(..., title="Website URL", description="URL of the website to check")):
    logger.info(f"Checking compliance for: {website_url}")

    extracted_text = extract_text_from_url(website_url)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Failed to extract text from website.")

    compliance_result = check_compliance(extracted_text)
    return compliance_result

@app.get("/debug_chrome")
def debug_chrome():
    try:
        chrome_version = os.popen(f"{get_chrome_binary()} --version").read().strip()
        driver_version = os.popen(f"{get_chromedriver_binary()} --version").read().strip()
        return {"chrome_version": chrome_version, "driver_version": driver_version}
    except FileNotFoundError as e:
        return {"error": str(e)}

