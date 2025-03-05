import os
import requests
from bs4 import BeautifulSoup
import openai
import re
import warnings
import traceback
import json
import psutil
from fastapi import FastAPI, HTTPException
from urllib.parse import urljoin, urlparse, unquote
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor

# Suppress warnings for cleaner logs
warnings.filterwarnings("ignore", category=UserWarning)

# Load OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# FastAPI setup
app = FastAPI()

FRONTEND_URL = "https://frontend-kbjv.onrender.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # ✅ Only allow the frontend domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

def ensure_https(url: str) -> str:
    """Ensure the URL starts with https://, adding it if necessary."""
    url = unquote(url)
    if not url.startswith("http"):
        return "https://" + url
    return url

def crawl_website(website_url, max_depth=2, visited=None):
    """Recursively crawl a website up to a limited depth to find relevant pages."""
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
    """Extract text from a webpage using requests first, then Selenium if needed."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract only first 10,000 characters
        text = " ".join(p.get_text() for p in soup.find_all(['p', 'li', 'span'])[:200])
        return text[:10000]  # Limit text size
    except requests.RequestException:
        return selenium_extract_text(url)

def selenium_extract_text(url):
    """Extracts webpage text using Selenium as a fallback method."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_binary = os.getenv("CHROME_BIN", "/home/render/chromium/chrome-linux64/chrome")
        chromedriver_binary = os.getenv("CHROMEDRIVER_BIN", "/home/render/chromedriver/chromedriver-linux64/chromedriver")

        if not os.path.exists(chrome_binary) or not os.path.exists(chromedriver_binary):
            return "Chromium or ChromeDriver binary not found."

        chrome_options.binary_location = chrome_binary
        service = Service(executable_path=chromedriver_binary)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        text = driver.find_element("xpath", "//body").text
    except Exception:
        text = "Selenium extraction failed."
    finally:
        driver.quit()
        kill_chrome_processes()  # Kill Chrome processes to free memory

    return text

def kill_chrome_processes():
    """Kill ChromeDriver processes to reduce memory usage."""
    for process in psutil.process_iter(attrs=['pid', 'name']):
        if "chrome" in process.info['name'].lower():
            try:
                process.terminate()
            except psutil.NoSuchProcess:
                pass

def standardize_response(api_data):
    """
    Ensures the API response follows a single, consistent format.
    """
    standardized_data = {
        "compliance_analysis": {
            "privacy_policy": {
                "sms_consent_data": None,
                "data_collection_usage": None
            },
            "terms_conditions": {
                "message_types": None,
                "mandatory_disclosures": None
            },
            "compliance_status": None
        }
    }

    # Normalize Privacy Policy fields
    if "PrivacyPolicy" in api_data or "privacy_policy" in api_data:
        policy_data = api_data.get("PrivacyPolicy", api_data.get("privacy_policy", {}))
        standardized_data["compliance_analysis"]["privacy_policy"]["sms_consent_data"] = policy_data.get(
            "SMSConsentData", policy_data.get("sms_consent_data", "Not available.")
        )
        standardized_data["compliance_analysis"]["privacy_policy"]["data_collection_usage"] = policy_data.get(
            "DataCollectionUsage", policy_data.get("data_collection_usage", "Not available.")
        )

    # Normalize Terms & Conditions fields
    if "TermsConditions" in api_data or "terms_conditions" in api_data:
        terms_data = api_data.get("TermsConditions", api_data.get("terms_conditions", {}))
        standardized_data["compliance_analysis"]["terms_conditions"]["message_types"] = terms_data.get(
            "MessageTypes", terms_data.get("message_types", "Not available.")
        )
        standardized_data["compliance_analysis"]["terms_conditions"]["mandatory_disclosures"] = terms_data.get(
            "MandatoryDisclosures", terms_data.get("mandatory_disclosures", "Not available.")
        )

    # Normalize Compliance Status
    standardized_data["compliance_analysis"]["compliance_status"] = api_data.get(
        "ComplianceStatus", api_data.get("compliance_status", "Not available.")
    )

    return standardized_data

@app.get("/check_compliance")
def check_compliance_endpoint(website_url: str):
    """Check if a website's Privacy Policy and Terms & Conditions comply with TCR SMS requirements."""
    website_url = ensure_https(website_url)
    crawled_links = crawl_website(website_url, max_depth=2)

    privacy_text, terms_text = "", ""

    num_threads = max(2, os.cpu_count() or 4)
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(extract_text_from_url, crawled_links))

    for link, page_text in zip(crawled_links, results):
        if "privacy" in link:
            privacy_text += " " + page_text
        elif "terms" in link or "conditions" in link or "terms-of-service" in link or "legal" in link:
            terms_text += " " + page_text

    ai_response = check_tcr_compliance_with_chatgpt(privacy_text, terms_text)

    # Ensure AI response is properly formatted
    standardized_response = standardize_response(ai_response)

    return standardized_response

def check_tcr_compliance_with_chatgpt(privacy_text, terms_text):
    """Optimize ChatGPT request to reduce token usage."""
    
    compliance_prompt = f"""
    You are an expert in SMS compliance regulations. Analyze the Privacy Policy and Terms & Conditions for TCR SMS compliance.
    {privacy_text[:2000]}
    {terms_text[:2000]}
    Return a **pure JSON response** without Markdown formatting.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": compliance_prompt}],
        max_tokens=800
    )

    try:
        chatgpt_response = response.choices[0].message.content.strip()
        chatgpt_response = chatgpt_response.replace("```json", "").replace("```", "").strip()
        return json.loads(chatgpt_response)
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response."}
