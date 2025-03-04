import os
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import openai
import re
import warnings
from fastapi import FastAPI, HTTPException
from urllib.parse import urljoin, urlparse, unquote
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Suppress XML warnings to clean up logs
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Load API Key from environment variable
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
        
        print(f"Crawled {website_url}, Found Links: {found_links}")  # Debugging
        return found_links
    except requests.RequestException:
        print(f"Failed to crawl {website_url}")
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

        print(f"Extracted text from {url}: {text[:500]}")  # Debugging

        # If extracted text is empty, use Selenium
        if not text.strip():
            print(f"Requests failed to extract meaningful text from {url}. Trying Selenium...")
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Use the correct Chrome binary path
            chrome_binary = os.getenv("CHROME_BIN", "/home/render/chrome/opt/google/chrome/google-chrome")
            chrome_options.binary_location = chrome_binary

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(url)
            text = driver.find_element("xpath", "//body").text
            driver.quit()
            
            print(f"Extracted text from Selenium for {url}: {text[:500]}")  # Debugging
        
        return text

    except requests.RequestException:
        print(f"Requests completely failed for {url}. Falling back to Selenium.")

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Ensure we are using the correct Chrome binary path
        chrome_binary = os.getenv("CHROME_BIN", "/home/render/chrome/opt/google/chrome/google-chrome")
        chrome_options.binary_location = chrome_binary

        # Debugging: Print Chrome binary location
        print(f"Using Chrome binary at: {chrome_binary}")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        text = driver.find_element("xpath", "//body").text
        driver.quit()
        
        print(f"Extracted text from Selenium for {url}: {text[:500]}")  # Debugging
        return text

@app.get("/check_compliance")
def check_compliance_endpoint(website_url: str):
    website_url = ensure_https(website_url)
    crawled_links = crawl_website(website_url, max_depth=2)
    
    privacy_text, terms_text, legal_text = "", "", ""
    
    for link in crawled_links:
        page_text = extract_text_from_url(link)
        print(f"Extracted text from {link}: {page_text[:500]}")
        if "privacy" in link:
            privacy_text += " " + page_text
        elif "terms" in link or "conditions" in link or "terms-of-service" in link:
            terms_text += " " + page_text
        elif "legal" in link:
            legal_text += " " + page_text
    
    if not privacy_text and not terms_text and not legal_text:
        raise HTTPException(status_code=400, detail="Could not extract text from any relevant pages.")
    
    compliance_report = check_compliance(privacy_text, terms_text, legal_text)
    return {"compliance_report": compliance_report}

# ✅ Fix: Added check_compliance() function
def check_compliance(privacy_text, terms_text, legal_text):
    """Placeholder function for compliance checking. Implement logic as needed."""
    return f"Privacy Text: {len(privacy_text)} characters\nTerms Text: {len(terms_text)} characters\nLegal Text: {len(legal_text)} characters"


