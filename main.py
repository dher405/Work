import os
import requests
from bs4 import BeautifulSoup
import openai
import re
import warnings
import traceback
from fastapi import FastAPI, HTTPException
from urllib.parse import urljoin, urlparse, unquote
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)

# Load OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# FastAPI setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (or specify your frontend URL)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ensure_https(url: str) -> str:
    """Ensure the URL starts with https://, adding it if necessary."""
    url = unquote(url)
    if not url.startswith("http"):
        return "https://" + url
    return url

def crawl_website(website_url, max_depth=1, visited=None):
    """Recursively crawl a website up to a limited depth to avoid long processing times."""
    if visited is None:
        visited = set()

    if max_depth == 0 or website_url in visited:
        return set()

    visited.add(website_url)
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(website_url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        found_links = set()

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(website_url, href)
            parsed_url = urlparse(full_url)
            if parsed_url.netloc == urlparse(website_url).netloc and full_url not in visited:
                found_links.add(full_url)
                if max_depth > 1:
                    found_links.update(crawl_website(full_url, max_depth - 1, visited))

        return found_links
    except requests.RequestException:
        return set()

def extract_text_from_url(url):
    """Extract text from a webpage using requests first, then fallback to Selenium if needed."""
    if not url:
        return ""

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = "\n".join(p.get_text() for p in soup.find_all(['p', 'li', 'span', 'div', 'body']))
        text = re.sub(r'\s+', ' ', text.strip())

        if not text.strip():  # Fallback to Selenium if empty
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            chrome_binary = os.getenv("CHROME_BIN", "/home/render/chromium/chrome-linux64/chrome")
            chromedriver_binary = os.getenv("CHROMEDRIVER_BIN", "/home/render/chromedriver/chromedriver-linux64/chromedriver")

            if not os.path.exists(chrome_binary) or not os.path.exists(chromedriver_binary):
                return "Chromium or ChromeDriver binary not found."

            chrome_options.binary_location = chrome_binary
            driver = None
            try:
                service = Service(executable_path=chromedriver_binary)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.get(url)
                text = driver.find_element("xpath", "//body").text
            except Exception as e:
                text = f"Selenium extraction failed: {traceback.format_exc()}"  # Improved error message
            finally:
                if driver:
                    driver.quit()

        return text

    except requests.RequestException:
        return "Request failed."

@app.get("/check_compliance")
def check_compliance_endpoint(website_url: str):
    """Check if a website's Privacy Policy and Terms & Conditions comply with TCR SMS requirements."""
    website_url = ensure_https(website_url)
    crawled_links = crawl_website(website_url, max_depth=1)

    privacy_text, terms_text, legal_text = "", "", ""

    # **Speed Improvement: Use Multithreading to Extract Text Faster**
    num_threads = max(2, os.cpu_count() or 4)  # Dynamically allocate thread count
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(extract_text_from_url, crawled_links))

    for link, page_text in zip(crawled_links, results):
        if "privacy" in link:
            privacy_text += " " + page_text
        elif "terms" in link or "conditions" in link or "terms-of-service" in link:
            terms_text += " " + page_text
        elif "legal" in link:
            legal_text += " " + page_text

    compliance_results = check_tcr_compliance(privacy_text, terms_text)
    return compliance_results

def check_tcr_compliance(privacy_text, terms_text):
    """Check compliance with TCR SMS requirements."""

    privacy_requirements = {
        "SMS Consent Information Not Shared with Third Parties": "won’t be shared with third parties",
        "Explanation of How Consumer Information is Used and Collected": "how your consumer information is used",
    }

    terms_requirements = {
        "Message Types Disclosure": "types of messages the recipient can expect",
        "Messaging Frequency Disclosure": "messaging frequency may vary",
        "Message and Data Rates Disclosure": "message and data rates may apply",
        "Opt-out Information": "opt out at any time by texting STOP",
        "Help Information": "For assistance, text HELP",
    }

    privacy_compliance = {key: (value.lower() in privacy_text.lower()) for key, value in privacy_requirements.items()}
    terms_compliance = {key: (value.lower() in terms_text.lower()) for key, value in terms_requirements.items()}

    return {
        "privacy_policy": {
            "text_length": len(privacy_text),
            "found": len(privacy_text) > 100,
            "requirements_met": privacy_compliance,
        },
        "terms_conditions": {
            "text_length": len(terms_text),
            "found": len(terms_text) > 100,
            "requirements_met": terms_compliance,
        },
        "overall_compliance": all(privacy_compliance.values()) and all(terms_compliance.values()),
    }



