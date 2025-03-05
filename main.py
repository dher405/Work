import os
import requests
from bs4 import BeautifulSoup
import openai
import re
import logging
from fastapi import FastAPI, HTTPException, Query
from urllib.parse import urljoin, urlparse
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure Chrome and ChromeDriver paths are set
CHROME_BIN = os.environ.get("CHROME_BIN", "/home/render/chromium/chrome-linux/chrome")
CHROMEDRIVER_BIN = os.environ.get("CHROMEDRIVER_BIN", "/home/render/chromedriver/chromedriver-linux64/chromedriver")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
        response = requests.get(website_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
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
        
        logger.info(f"Crawled {website_url}, Found Links: {found_links}")  # Debugging
        return found_links
    except requests.RequestException as e:
        logger.error(f"Failed to crawl {website_url}: {e}")
        return set()

def extract_text_from_url(url):
    """Extract text content from a given webpage. Uses Selenium if needed."""
    if not url:
        return ""

    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = "\n".join(p.get_text() for p in soup.find_all(['p', 'li', 'span', 'div', 'body']))
        text = re.sub(r'\s+', ' ', text.strip())

        logger.info(f"Extracted text from {url}: {text[:500]}")  # Debugging

        if not text.strip():
            logger.info(f"Requests failed to extract meaningful text from {url}. Trying Selenium...")

            chrome_options = Options()
            chrome_options.binary_location = CHROME_BIN
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(service=Service(CHROMEDRIVER_BIN), options=chrome_options)
            driver.get(url)
            text = driver.find_element("xpath", "//body").text
            driver.quit()

            logger.info(f"Extracted text from Selenium for {url}: {text[:500]}")  # Debugging

        return text

    except requests.RequestException:
        logger.error(f"Requests completely failed for {url}. Falling back to Selenium.")

        chrome_options = Options()
        chrome_options.binary_location = CHROME_BIN
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_BIN), options=chrome_options)
        driver.get(url)
        text = driver.find_element("xpath", "//body").text
        driver.quit()

        logger.info(f"Extracted text from Selenium for {url}: {text[:500]}")  # Debugging
        return text

def analyze_compliance(privacy_text, terms_text):
    """Use AI to analyze website compliance with TCR SMS standards."""
    prompt = f"""
    Analyze the following website text for compliance with TCR SMS requirements.

    Privacy Policy:
    {privacy_text[:4000]}

    Terms and Conditions:
    {terms_text[:4000]}

    Required elements:
    1. Privacy Policy must include:
       - Statement that SMS consent data is not shared with third parties.
       - Explanation of how consumer data is collected, used, and shared.
    2. Terms of Service must include:
       - The types of messages recipients will receive.
       - Standard messaging disclosures (e.g., "Message and data rates may apply. Reply STOP to opt-out.")
    
    Provide a JSON response indicating whether each requirement is met.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt}],
        response_format="json_object"
    )

    return response.json()

@app.get("/check_compliance")
def check_compliance_endpoint(website_url: str):
    """Endpoint to check website compliance."""
    website_url = ensure_https(website_url)
    crawled_links = crawl_website(website_url, max_depth=2)

    privacy_text, terms_text = "", ""

    for link in crawled_links:
        page_text = extract_text_from_url(link)
        logger.info(f"Extracted text from {link}: {page_text[:500]}")

        if "privacy" in link:
            privacy_text += " " + page_text
        elif "terms" in link or "conditions" in link or "terms-of-service" in link:
            terms_text += " " + page_text

    if not privacy_text and not terms_text:
        raise HTTPException(status_code=400, detail="Could not extract text from any relevant pages.")

    compliance_report = analyze_compliance(privacy_text, terms_text)
    return {"compliance_report": compliance_report}

@app.get("/debug_chrome")
def debug_chrome():
    """Check if Chrome and ChromeDriver are properly installed."""
    try:
        chrome_options = Options()
        chrome_options.binary_location = CHROME_BIN
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_BIN), options=chrome_options)
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        return {"status": "success", "title": title}
    except Exception as e:
        return {"error": str(e)}

