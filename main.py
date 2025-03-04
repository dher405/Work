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
from selenium.webdriver.chrome.options import Options

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
        response = requests.get(website_url, timeout=10)
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
        
        return found_links
    except requests.RequestException:
        return set()

def extract_text_from_url(url):
    """Extract text content from a given webpage. Uses Selenium if needed."""
    if not url:
        return ""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = "\n".join(p.get_text() for p in soup.find_all(['p', 'li', 'span', 'div', 'body']))
        return re.sub(r'\s+', ' ', text.strip())
    except requests.RequestException:
        print(f"Requests failed for {url}. Trying Selenium...")
        
        # Use Selenium as fallback
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        text = driver.find_element("xpath", "//body").text
        driver.quit()
        return text

def normalize_text(text):
    """Normalize text to improve matching accuracy."""
    return re.sub(r'[^a-zA-Z0-9 ]', '', text).lower()

def check_compliance(privacy_text, terms_text, legal_text):
    """Send extracted text to GPT-4o-mini for compliance check."""
    
    # Combine all extracted text from crawled pages
    all_text = f"{privacy_text} {terms_text} {legal_text}"
    normalized_text = normalize_text(all_text)

    # Define an exact match phrase to detect SMS consent language
    sms_consent_exact_phrase = normalize_text(
        "Information obtained as part of the SMS consent process won’t be shared with third parties."
    )

    # Check for the exact SMS consent statement
    sms_consent_found = sms_consent_exact_phrase in normalized_text

    print(f"Extracted Privacy Text:\n{privacy_text[:500]}\n")
    print(f"Normalized Combined Text:\n{normalized_text[:500]}\n")

    # If missing, explicitly notify GPT
    missing_sms_consent = "" if sms_consent_found else (
        "**WARNING:** Privacy Policy does NOT explicitly state that SMS consent information is not shared with third parties.\n\n"
    )

    prompt = f"""
    You are an expert in TCR compliance checking. The website may have compliance details spread across multiple linked pages. Carefully analyze all extracted text before determining compliance.

    {missing_sms_consent}

    **Privacy Policy Compliance:**
    - Must state that SMS consent information will not be shared with third parties.
    - Must explain how user information is used, collected, and shared.

    **Terms & Conditions Compliance:**
    - Must specify the types of messages users can expect (e.g., order updates, job application status, etc.).
    - Must include standard messaging disclosures:
      - Messaging frequency may vary.
      - Message and data rates may apply.
      - Opt-out by texting "STOP".
      - Help available by texting "HELP".
      - Links to Privacy Policy and Terms of Service.

    **Extracted Compliance Text (From Multiple Pages):**\n\n{all_text[:4000] if all_text else 'No relevant text found'}\n\n
    ⚠️ **Important:** If the required information appears anywhere in the extracted text, do NOT mark it as missing.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a compliance auditor."},
                  {"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.replace("\n", "\n\n")

@app.get("/check_compliance")
def check_compliance_endpoint(website_url: str):
    website_url = ensure_https(website_url)
    crawled_links = crawl_website(website_url, max_depth=2)

    print(f"Crawled Links for {website_url}: {crawled_links}")  # Debugging

    privacy_text, terms_text, legal_text = "", "", ""

    for link in crawled_links:
        page_text = extract_text_from_url(link)
        print(f"Extracted text from {link}: {page_text[:500]}")  # Debug first 500 characters
        
        if "privacy" in link:
            privacy_text += " " + page_text
        elif "terms" in link or "conditions" in link or "terms-of-service" in link:
            terms_text += " " + page_text
        elif "legal" in link:
            legal_text += " " + page_text

    if not privacy_text and not terms_text and not legal_text:
        raise HTTPException(status_code=400, detail=f"Could not extract text from any relevant pages. Crawled Links: {crawled_links}")

    compliance_report = check_compliance(privacy_text, terms_text, legal_text)
    return {"compliance_report": compliance_report}


