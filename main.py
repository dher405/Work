import os
import requests
from bs4 import BeautifulSoup
import openai
import re
import logging
from fastapi import FastAPI, HTTPException
from urllib.parse import urljoin, urlparse, unquote
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ✅ Enable logging for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Load OpenAI API Key securely
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# ✅ Allow cross-origin requests for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify if needed for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_chrome_binary():
    """Detects the Chrome binary location dynamically."""
    possible_paths = [
        "/opt/render/chromium/latest/chrome",
        "/opt/render/chromium/chrome-linux64/chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Chrome binary not found! Check installation.")

CHROME_BIN = get_chrome_binary()

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
        
        logging.info(f"Crawled {website_url}, Found Links: {found_links}")  # Debugging
        return found_links
    except requests.RequestException:
        logging.warning(f"Failed to crawl {website_url}")
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

        logging.info(f"Extracted text from {url}: {text[:500]}")  # Debugging

        # If extracted text is empty, use Selenium
        if not text.strip():
            logging.warning(f"Requests failed to extract meaningful text from {url}. Trying Selenium...")
            
            chrome_options = Options()
            chrome_options.binary_location = CHROME_BIN
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(url)
            text = driver.find_element("xpath", "//body").text
            driver.quit()
            
            logging.info(f"Extracted text from Selenium for {url}: {text[:500]}")  # Debugging
        
        return text

    except requests.RequestException:
        logging.error(f"Requests completely failed for {url}. Falling back to Selenium.")
        
        chrome_options = Options()
        chrome_options.binary_location = CHROME_BIN
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        text = driver.find_element("xpath", "//body").text
        driver.quit()
        
        logging.info(f"Extracted text from Selenium for {url}: {text[:500]}")  # Debugging
        return text

@app.get("/check_compliance")
def check_compliance_endpoint(website_url: str):
    website_url = ensure_https(website_url)
    crawled_links = crawl_website(website_url, max_depth=2)
    
    privacy_text, terms_text, legal_text = "", "", ""
    
    for link in crawled_links:
        page_text = extract_text_from_url(link)
        logging.info(f"Extracted text from {link}: {page_text[:500]}")
        if "privacy" in link:
            privacy_text += " " + page_text
        elif "terms" in link or "conditions" in link or "terms-of-service" in link:
            terms_text += " " + page_text
        elif "legal" in link:
            legal_text += " " + page_text
    
    if not privacy_text and not terms_text and not legal_text:
        raise HTTPException(status_code=400, detail="Could not extract text from any relevant pages.")
    
    # ✅ AI compliance check with OpenAI
    try:
        response = client.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Analyze the following text for TCR SMS compliance."},
                {"role": "user", "content": f"Privacy Policy: {privacy_text} \n\nTerms & Conditions: {terms_text}"}
            ],
            response_format="json_object"
        )
        compliance_report = response.choices[0].message["content"]
    except Exception as e:
        logging.error(f"AI Processing Error: {e}")
        raise HTTPException(status_code=500, detail="AI processing failed.")

    return {"compliance_report": compliance_report}

@app.get("/debug_chrome")
def debug_chrome():
    """Check if Chrome and ChromeDriver are properly installed."""
    try:
        chrome_path = get_chrome_binary()
        chromedriver_path = os.getenv("CHROMEDRIVER_BIN", "/home/render/chromedriver/chromedriver-linux64/chromedriver")

        if not os.path.exists(chromedriver_path):
            return {"error": f"ChromeDriver not found at {chromedriver_path}"}

        chrome_options = Options()
        chrome_options.binary_location = chrome_path
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=Service(chromedriver_path), options=chrome_options)
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        return {"status": "success", "title": title}
    except Exception as e:
        return {"error": str(e)}
