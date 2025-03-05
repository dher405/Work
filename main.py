import os
import requests
from bs4 import BeautifulSoup
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import openai
import json

# Load OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

# Initialize FastAPI
app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_url(url):
    """Extracts text from the correct sections of a webpage."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # ✅ Extract from the correct section
        main_content = soup.find("div", {"id": "page-content"})
        if main_content:
            policy_section = main_content.find("section", {"id": "text-only"})
            if policy_section:
                text = "\n".join(p.get_text(strip=True) for p in policy_section.find_all("p"))
            else:
                text = "\n".join(p.get_text(strip=True) for p in main_content.find_all("p"))
        else:
            text = "\n".join(p.get_text(strip=True) for p in soup.find_all("p"))

        # ✅ Ensure we have meaningful content
        if len(text) < 50:
            print(f"⚠️ Requests extraction failed for {url}, switching to Selenium...")
            return selenium_extract_text(url)

        print(f"✅ Extracted from {url} (cleaned): {text[:500]}...")
        return text[:10000]  # Limit to prevent excessive token usage

    except requests.RequestException:
        return selenium_extract_text(url)

def selenium_extract_text(url):
    """Extracts full webpage text using Selenium."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_binary = os.getenv("CHROME_BIN", "/home/render/chromium/chrome-linux64/chrome")
        chromedriver_binary = os.getenv("CHROMEDRIVER_BIN", "/home/render/chromedriver/chromedriver-linux64/chromedriver")

        if not os.path.exists(chrome_binary) or not os.path.exists(chromedriver_binary):
            return "⚠️ Chromium or ChromeDriver binary not found."

        chrome_options.binary_location = chrome_binary
        service = Service(executable_path=chromedriver_binary)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        time.sleep(5)  # Allow JavaScript to load content

        # ✅ Extract all visible text
        text = driver.find_element("xpath", "//body").text
        driver.quit()

        print(f"✅ Extracted from Selenium {url}: {text[:500]}...")  # Debugging
        return text  
    except Exception as e:
        return f"Selenium extraction failed: {str(e)}"

def analyze_compliance(privacy_text, terms_text):
    """Analyzes the extracted text for TCR SMS compliance using ChatGPT."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
    Review the following Privacy Policy and Terms & Conditions for compliance with TCR SMS guidelines.

    **Privacy Policy:**
    {privacy_text[:5000]}

    **Terms & Conditions:**
    {terms_text[:5000]}

    Ensure the following:
    - **Privacy Policy** must state SMS consent data is not shared with third parties.
    - **Privacy Policy** must explain how consumer data is collected, used, and shared.
    - **Terms & Conditions** must specify the types of messages sent (e.g., transactional, marketing).
    - **Terms & Conditions** must include mandatory SMS disclosures: opt-out instructions, frequency, and costs.

    Provide a **valid JSON** response with these exact keys:
    ```json
    {{
        "compliance_analysis": {{
            "privacy_policy": {{
                "sms_consent": "found" or "not_found",
                "data_usage": "explicit" or "not_explicit"
            }},
            "terms_conditions": {{
                "message_types": "found" or "not_found",
                "mandatory_disclosures": "found" or "not_found"
            }},
            "overall_compliance": "Compliant" or "Non-compliant"
        }}
    }}
    ```
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Analyze the following for SMS compliance."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json"}  # ✅ FIXED: Corrected response_format
        )

        ai_response = response.choices[0].message.content
        print(f"🔍 Raw AI Response: {ai_response}")  # Debugging

        return json.loads(ai_response)
    except Exception as e:
        print(f"❌ AI Processing Error: {str(e)}")
        return {"error": "Failed to process compliance analysis."}

@app.get("/check_compliance")
def check_compliance(website_url: str):
    """Checks a website's Privacy Policy and Terms of Service for SMS compliance."""
    try:
        website_url = website_url if website_url.startswith("http") else "https://" + website_url

        # Crawl for pages
        crawled_pages = {
            website_url,
            website_url.rstrip("/") + "/privacy-policy",
            website_url.rstrip("/") + "/terms-of-service"
        }

        privacy_text, terms_text = "", ""

        for page in crawled_pages:
            text = extract_text_from_url(page)
            print(f"Extracted from {page}: {text[:500]}")  # Debugging

            if "privacy" in page:
                privacy_text += text + "\n"
            elif "terms" in page:
                terms_text += text + "\n"

        if not privacy_text and not terms_text:
            raise HTTPException(status_code=400, detail="No relevant pages found.")

        # Call ChatGPT for compliance analysis
        compliance_report = analyze_compliance(privacy_text, terms_text)

        return compliance_report
    except Exception as e:
        return {"error": str(e)}
