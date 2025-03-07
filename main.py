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
    pages_to_check = [base_url]
    extracted_text = ""

    options = Options()
    options.binary_location = get_chrome_binary()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36")

    service = Service(get_chromedriver_binary())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.set_page_load_timeout(180)  # Increased timeout
        driver.get(base_url)

        # Wait for the page to fully load
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find links to privacy/terms pages (up to 2 levels deep)
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if any(keyword in href.lower() for keyword in ["privacy", "terms", "legal"]):
                absolute_url = urljoin(base_url, href)
                pages_to_check.append(absolute_url)

                # Check one level deeper for these pages
                driver.get(absolute_url)
                time.sleep(3)
                sub_soup = BeautifulSoup(driver.page_source, "html.parser")
                for sub_link in sub_soup.find_all("a", href=True):
                    sub_href = sub_link["href"]
                    if any(keyword in sub_href.lower() for keyword in ["privacy", "terms", "legal"]):
                        pages_to_check.append(urljoin(absolute_url, sub_href))

        # Extract text from all collected pages
        for page in set(pages_to_check):  # Use set to remove duplicates
            logger.info(f"Scraping page: {page}")
            driver.get(page)

            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

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
