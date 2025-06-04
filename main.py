import os
import time
import json
import requests
import logging
import undetected_chromedriver as uc
from urllib.parse import urljoin, urlparse
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# Driver Pool
driver_pool = []
pool_lock = Lock()
pool_size = 5

def initialize_driver():
    try:
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        driver = uc.Chrome(options=options, user_data_dir='/tmp/udc-profile')
        return driver
    except Exception as e:
        logger.error(f"Failed to start Undetected ChromeDriver: {e}")
        raise HTTPException(status_code=500, detail="Failed to start browser session with stealth mode.")

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

def enforce_www(website_url):
    if "www." not in website_url:
        website_url = website_url.replace("https://", "https://www.", 1) if website_url.startswith("https://") else f"https://www.{website_url}"
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

    try:
        soup = fetch_page(driver, base_url)
        if soup is None:
            return "", {}

        non_www_privacy_url = f"{base_url.replace('www.', '')}/privacy-policy/"
        if "www." not in original_base_url:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'}
                response = requests.get(non_www_privacy_url, headers=headers, timeout=10)
                logger.info(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    pages_to_check = [non_www_privacy_url]
                time.sleep(2)
            except requests.exceptions.RequestException:
                pass

        logger.info(f"pages_to_check before link parsing: {pages_to_check}")

        for link in soup.find_all("a", href=True):
            try:
                href = link["href"].strip()
                if href.startswith("mailto:"):
                    continue
                parsed_href = urlparse(urljoin(base_url, href))
                if parsed_href.netloc and parsed_href.netloc != base_domain:
                    continue

                link_text = link.get_text(strip=True).lower()
                if any(keyword in link_text or keyword in href.lower() for keyword in ["privacy", "terms", "legal"]):
                    absolute_url = urljoin(base_url, href)
                    pages_to_check.append(absolute_url)

                    sub_soup = fetch_page(driver, absolute_url)
                    if sub_soup is None:
                        continue

                    for sub_link in sub_soup.find_all("a", href=True):
                        sub_href = sub_link["href"].strip()
                        if sub_href.startswith("mailto:"):
                            continue
                        parsed_sub_href = urlparse(urljoin(absolute_url, sub_href))
                        if parsed_sub_href.netloc and parsed_sub_href.netloc != base_domain:
                            continue
                        if any(keyword in sub_href.lower() for keyword in ["privacy", "terms", "legal"]):
                            pages_to_check.append(urljoin(absolute_url, sub_href))
            except Exception as e:
                logger.error(f"Error processing link: {e}")
                continue

        logger.info(f"pages_to_check after link parsing: {pages_to_check}")

        for page in set(pages_to_check):
            logger.info(f"Scraping page: {page}")
            soup = fetch_page(driver, page)
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

def fetch_page(driver, url, max_wait=30, max_retries=3):
    for attempt in range(max_retries):
        try:
            logger.info(f"Loading page: {url} (Attempt {attempt + 1})")
            driver.set_page_load_timeout(60)
            driver.get(url)

            WebDriverWait(driver, max_wait).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            page_source = driver.page_source.lower()
            if "verify you are human" in page_source or "enable javascript and cookies" in page_source:
                logger.warning(f"Bot protection still active (Attempt {attempt + 1}). Waiting and retrying...")
                time.sleep(5)
                continue
            return BeautifulSoup(driver.page_source, "html.parser")

        except Exception as e:
            logger.error(f"Failed to fetch page {url} on attempt {attempt + 1}: {e}")
            time.sleep(3)

    logger.error(f"Bot protection could not be bypassed after {max_retries} attempts.")
    return None

@app.get("/check_compliance")
def check_website_compliance(website_url: str = Query(..., title="Website URL", description="URL of the website to check")):
    logger.info(f"Checking compliance for: {website_url}")

    extracted_text, source_urls = extract_text_from_website(website_url)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Failed to extract text from website.")

    # Placeholder: Return raw text for now
    response_data = {
        "url": website_url,
        "text_snippet": extracted_text[:1000],
        "source_urls": list(source_urls.keys())
    }

    response = Response(content=json.dumps(response_data), media_type="application/json")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.options("/check_compliance")
def options_check_compliance():
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response
