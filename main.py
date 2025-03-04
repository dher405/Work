import os
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import openai
import re
import warnings
import logging
import traceback
from fastapi import FastAPI, HTTPException
from urllib.parse import urljoin, urlparse, unquote
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Suppress XML warnings to clean up logs
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Configure detailed logging for debugging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("uvicorn.error")

# Load API Key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify your frontend URL)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_https(url: str) -> str:
    """Ensure the URL starts with https://, adding it if necessary."""
    url = unquote(url)  # Decode URL
    if not url.startswith("http"):
        return "https://" + url
    return url

def crawl_website(website_url, max_depth=2, visited=None):
    """Recursively crawl a website up to a maximum depth."""
    if visited is None:
        visited = set()
    
    if max_depth == 0 or website_url in visited:
        return set()
    
    visited.add(website_url)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        }
        response = requests.get(website_url, timeout=30, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        found_links = set()

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(website_url, href)
            parsed_url = urlparse(full_url)
            if parsed_url.netloc == urlparse(website_url).netloc:  # Only follow internal links
                found_links.add(full_url)
                found_links.update(crawl_website(full_url, max_depth - 1, visited))
        
        logger.debug(f"Crawled {website_url}, Found Links: {found_links}")  # Debugging
        return found_links
    except requests.RequestException as e:
        logger.error(f"Failed to crawl {website_url}: {e}", exc_info=True)
        return set()

def extract_text_from_url(url):
    """Extract text content from a given webpage. Uses Selenium if needed."""
    if not url:
        return ""

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = "\n".join(p.get_text() for p in soup.find_all(['p', 'li', 'span', 'div', 'body']))
        text = re.sub(r'\s+', ' ', text.strip())

        if not text.strip():
            logger.warning(f"Requests failed to extract meaningful text from {url}. Trying Selenium...")

            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Use the manually installed Chromium and ChromeDriver
            chrome_binary = os.getenv("CHROME_BIN", "/home/render/chromium/chrome-linux64/chrome")
            chromedriver_binary = os.getenv("CHROMEDRIVER_BIN", "/home/render/chromedriver/chromedriver-linux64/chromedriver")

            if not os.path.exists(chrome_binary):
                logger.error(f"ERROR: Chromium binary not found at {chrome_binary}. Exiting.")
                return "Chromium binary not found."

            if not os.path.exists(chromedriver_binary):
                logger.error(f"ERROR: ChromeDriver binary not found at {chromedriver_binary}. Exiting.")
                return "ChromeDriver binary not found."

            chrome_options.binary_location = chrome_binary

            logger.debug(f"Using Chromium binary at: {chrome_binary}")
            logger.debug(f"Using ChromeDriver binary at: {chromedriver_binary}")

            driver = None
            try:
                service = Service(executable_path=chromedriver_binary)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.get(url)
                text = driver.find_element("xpath", "//body").text
            except Exception as e:
                logger.error("ERROR: Selenium extraction failed!", exc_info=True)
                text = "Selenium extraction failed."
            finally:
                if driver:
                    driver.quit()

        return text

    except requests.RequestException as e:
        logger.error(f"Requests completely failed for {url}: {e}", exc_info=True)
        return "Request failed."

@app.get("/check_compliance")
def check_compliance_endpoint(website_url: str):
    website_url = ensure_https(website_url)
    crawled_links = crawl_website(website_url, max_depth=2)
    
    privacy_text, terms_text, legal_text = "", "", ""
    
    for link in crawled_links:
        page_text = extract_text_from_url(link)
        logger.debug(f"Extracted text from {link}: {page_text[:500]}")
        if "privacy" in link:
            privacy_text += " " + page_text
        elif "terms" in link or "conditions" in link or "terms-of-service" in link:
            terms_text += " " + page_text
        elif "legal" in link:
            legal_text += " " + page_text
    
    return check_compliance(privacy_text, terms_text, legal_text)

def check_compliance(privacy_text, terms_text, legal_text):
    """Basic Compliance Check - Expand this logic as needed."""
    return {
        "privacy_text_length": len(privacy_text),
        "terms_text_length": len(terms_text),
        "legal_text_length": len(legal_text),
        "privacy_policy_found": len(privacy_text) > 100,
        "terms_found": len(terms_text) > 100,
        "legal_section_found": len(legal_text) > 100
    }
