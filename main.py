import os
import requests
from bs4 import BeautifulSoup
import openai
import re
import warnings
import traceback
import json
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

def crawl_website(website_url, max_depth=2, visited=None):
    """Recursively crawl a website up to a limited depth to find all relevant pages."""
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

    compliance_results = check_tcr_compliance_with_chatgpt(privacy_text, terms_text)
    return compliance_results

import json  # Import JSON for proper parsing

def check_tcr_compliance_with_chatgpt(privacy_text, terms_text):
    """Use ChatGPT to check if the extracted policies meet TCR SMS compliance with enhanced accuracy."""

    compliance_prompt = f"""
    You are an expert in SMS compliance regulations. Your task is to analyze the given Privacy Policy and Terms & Conditions 
    from a website and determine if they comply with TCR SMS compliance requirements.

    **Privacy Policy Content:**
    {privacy_text[:4000]}

    **Terms and Conditions Content:**
    {terms_text[:4000]}

    **TCR SMS Compliance Standards:**
    - Privacy Policy must explicitly state that information obtained via SMS consent will not be shared with third parties.
    - Privacy Policy must explain how consumer information is collected, used, and shared.
    - Terms must describe the **types of messages users will receive**.
    - Terms must include required messaging disclosures.

    **Return the results in structured JSON format without Markdown formatting. DO NOT wrap the response in triple backticks or any other formatting characters:**
    {{
      "privacy_policy": {{
        "assessment": "Summary of privacy policy compliance, including missing elements."
      }},
      "terms_conditions": {{
        "assessment": "Summary of terms and conditions compliance, including missing elements."
      }},
      "summary_of_compliance": "Overall compliance status, requirements met, and key recommendations."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": compliance_prompt}],
        max_tokens=1000
    )

    try:
        # Extract response text and clean it
        chatgpt_response = response.choices[0].message.content.strip()

        # **Fix: Remove any Markdown-style JSON formatting**
        chatgpt_response = chatgpt_response.replace("```json", "").replace("```", "").strip()

        # Convert cleaned response to JSON
        parsed_response = json.loads(chatgpt_response)

        return {
            "privacy_policy": {
                "text_length": len(privacy_text),
                "found": bool(privacy_text.strip()),
                "assessment": parsed_response.get("privacy_policy", {}).get("assessment", "No details available.")
            },
            "terms_conditions": {
                "text_length": len(terms_text),
                "found": bool(terms_text.strip()),
                "assessment": parsed_response.get("terms_conditions", {}).get("assessment", "No details available.")
            },
            "summary_of_compliance": parsed_response.get("summary_of_compliance", "No summary available.")
        }

    except json.JSONDecodeError:
        return {
            "error": "Failed to parse AI response. Check OpenAI output format.",
            "raw_response": chatgpt_response  # Return raw response for debugging
        }
