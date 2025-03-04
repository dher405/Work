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
    allow_origins=["*"],  # Allow frontend to call backend
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
    """Check if a website's Privacy Policy and Terms & Conditions comply with TCR SMS requirements using ChatGPT."""
    website_url = ensure_https(website_url)
    crawled_links = crawl_website(website_url, max_depth=1)

    privacy_text, terms_text, legal_text = "", "", ""

    num_threads = max(2, os.cpu_count() or 4)
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(extract_text_from_url, crawled_links))

    for link, page_text in zip(crawled_links, results):
        if "privacy" in link:
            privacy_text += " " + page_text
        elif "terms" in link or "conditions" in link or "terms-of-service" in link:
            terms_text += " " + page_text
        elif "legal" in link:
            legal_text += " " + page_text

    compliance_results = check_tcr_compliance_with_chatgpt(privacy_text, terms_text)
    return compliance_results

def check_tcr_compliance_with_chatgpt(privacy_text, terms_text):
    """Use ChatGPT to check if the extracted policies meet TCR SMS compliance with enhanced accuracy."""

    compliance_prompt = f"""
    You are an expert in SMS compliance regulations. Your task is to analyze the given Privacy Policy and Terms & Conditions 
    from a website and determine if they comply with TCR SMS compliance requirements.

    **Privacy Policy:**
    {privacy_text[:4000]}

    **Terms and Conditions:**
    {terms_text[:4000]}

    **TCR SMS Compliance Standards:**
    The following requirements must be met for full compliance:

    ### Privacy Policy Requirements:
    1. **Clear Statement on SMS Consent and Third-Party Sharing**:
        - The Privacy Policy must explicitly state that information obtained via SMS consent will not be shared with third parties.
        - **Examples of Compliant Wording**:
            - "We do not sell or share customer information."
            - "Personal data is not disclosed to external parties."
            - "We will not share user data unless legally required."

    2. **Explanation of Consumer Information Usage, Collection, and Sharing**:
        - The Privacy Policy must explain how consumer information is collected, used, and shared.

    ### Terms & Conditions Requirements:
    1. **Types of Messages Users Will Receive**:
        - The Terms must describe the **types of messages users will receive** (e.g., order updates, job notifications).

    2. **Standard Messaging Disclosures**:
        - The Terms must include the following:
            - "Messaging frequency may vary."
            - "Message and data rates may apply."
            - "You can opt out at any time by texting STOP."
            - "For assistance, text HELP or visit [Privacy Policy URL] and [Terms of Service URL]."

    **Assessment Instructions**:
    - **Check for exact and similar wording** in the provided text.
    - If a requirement is met, **provide the exact sentence found**.
    - If missing, **explain what is missing and how it can be fixed**.
    """

    # Call OpenAI API for response
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": compliance_prompt}],
        max_tokens=1000
    )

    return {
        "privacy_policy": {
            "text_length": len(privacy_text),
            "found": len(privacy_text) > 100,
            "compliance_report": response.choices[0].message.content
        },
        "terms_conditions": {
            "text_length": len(terms_text),
            "found": len(terms_text) > 100,
            "compliance_report": response.choices[0].message.content
        }
    }

