import os
import requests
from bs4 import BeautifulSoup
import openai
import json
import psutil
import time
from fastapi import FastAPI, HTTPException
from urllib.parse import urljoin, urlparse, unquote
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor

# Suppress warnings for cleaner logs
import warnings
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
    allow_origins=[FRONTEND_URL],  
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

def crawl_website(website_url, max_depth=4, visited=None):
    """Recursively crawl a website up to a set depth, prioritizing policy-related pages."""
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

            if any(keyword in full_url.lower() for keyword in ["privacy", "terms", "policy", "legal", "conditions"]):
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

        text = " ".join(p.get_text() for p in soup.find_all(['p', 'li', 'span', 'div', 'meta'])[:300])
        return text[:10000]  
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
        time.sleep(4)  
        text = driver.find_element("xpath", "//body").text
    except Exception:
        text = "Selenium extraction failed."
    finally:
        driver.quit()
        kill_chrome_processes()  

    return text

def kill_chrome_processes():
    """Kill ChromeDriver processes to reduce memory usage."""
    for process in psutil.process_iter(attrs=['pid', 'name']):
        if "chrome" in process.info['name'].lower():
            try:
                process.terminate()
            except psutil.NoSuchProcess:
                pass

@app.get("/check_compliance")
def check_compliance_endpoint(website_url: str):
    """Check if a website's Privacy Policy and Terms & Conditions comply with TCR SMS requirements."""
    website_url = ensure_https(website_url)
    crawled_links = crawl_website(website_url, max_depth=4)

    privacy_text, terms_text = "", ""

    num_threads = max(2, os.cpu_count() or 4)
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(extract_text_from_url, crawled_links))

    for link, page_text in zip(crawled_links, results):
        if "privacy" in link:
            privacy_text += " " + page_text
        elif any(keyword in link for keyword in ["terms", "conditions", "policy", "legal"]):
            terms_text += " " + page_text

    compliance_results = check_tcr_compliance_with_chatgpt(privacy_text, terms_text)
    return compliance_results

def check_tcr_compliance_with_chatgpt(privacy_text, terms_text):
    """Optimized ChatGPT request enforcing structured JSON format."""

    compliance_prompt = f"""
    You are an expert in TCR SMS compliance. Analyze the Privacy Policy and Terms & Conditions for compliance.

    - Privacy Policy: {privacy_text[:4000]}
    - Terms & Conditions: {terms_text[:4000]}

    **STRICT REQUIREMENT: ONLY mark an item as 'not_found' if you are CERTAIN it does not exist.**
    - If wording is different but means the same thing, mark it as 'found'.
    - If unsure, provide the closest matching text and label it 'partially_found'.

    **Return JSON ONLY in the following format:**
    {{
        "compliance_analysis": {{
            "privacy_policy": {{
                "consent": "found/not_found/partially_found",
                "data_collection": "explicit/not_explicit/partially_explicit",
                "opt_out": "found/not_found/partially_found",
                "contact_information": "present/not_present",
                "third_party_sharing": "explicit/not_explicit/partially_explicit"
            }},
            "terms_conditions": {{
                "SMS_usage": "found/not_found/partially_found",
                "clear_terms": "found/not_found/partially_found",
                "consent": "explicit/not_explicit/partially_explicit",
                "user_rights": "explicit/not_explicit/partially_explicit",
                "contact_information": "present/not_present"
            }},
            "overall_compliance": "Compliant/Non-compliant",
            "recommendations": ["List specific recommendations."]
        }}
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": compliance_prompt}],
        max_tokens=1200  
    )

    try:
        chatgpt_response = response.choices[0].message.content.strip()
        chatgpt_response = chatgpt_response.replace("```json", "").replace("```", "").strip()
        return json.loads(chatgpt_response)
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response. Response format invalid."}
