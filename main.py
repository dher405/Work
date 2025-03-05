import os
import requests
import subprocess
import re
import openai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ✅ Load API Key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ Initialize FastAPI app
app = FastAPI()

# ✅ Allow CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Debugging Endpoint for Chrome & ChromeDriver
@app.get("/debug_chrome")
def debug_chrome():
    try:
        chrome_version = subprocess.check_output(["/home/render/chromium/latest/chrome", "--version"], stderr=subprocess.STDOUT, text=True)
        chromedriver_version = subprocess.check_output(["/home/render/chromedriver/chromedriver-linux64/chromedriver", "--version"], stderr=subprocess.STDOUT, text=True)

        return {
            "chrome_version": chrome_version.strip(),
            "chromedriver_version": chromedriver_version.strip(),
            "chrome_path": os.getenv("CHROME_BIN"),
            "chromedriver_path": os.getenv("CHROMEDRIVER_BIN")
        }
    except Exception as e:
        return {"error": str(e)}

# ✅ Ensure HTTPS for input URLs
def ensure_https(url: str) -> str:
    if not url.startswith("http"):
        return "https://" + url
    return url

# ✅ Crawl and extract text from multiple pages
def crawl_website(base_url, max_depth=2, visited=None):
    if visited is None:
        visited = set()

    if max_depth == 0 or base_url in visited:
        return visited

    visited.add(base_url)
    try:
        response = requests.get(base_url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            full_url = requests.compat.urljoin(base_url, link)
            if full_url.startswith(base_url) and full_url not in visited:
                visited.update(crawl_website(full_url, max_depth - 1, visited))
        
        return visited
    except requests.RequestException:
        return visited

# ✅ Extract text from a webpage using BeautifulSoup or Selenium
def extract_text_from_url(url):
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = " ".join(p.get_text() for p in soup.find_all(['p', 'li', 'span', 'div', 'body'])).strip()
        
        if len(text) < 100:  # If too short, try Selenium
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.binary_location = os.getenv("CHROME_BIN")

            driver = webdriver.Chrome(service=Service(os.getenv("CHROMEDRIVER_BIN")), options=chrome_options)
            driver.get(url)
            text = driver.find_element("xpath", "//body").text
            driver.quit()
        
        return re.sub(r'\s+', ' ', text)
    
    except Exception as e:
        return f"Error extracting text from {url}: {str(e)}"

# ✅ Process compliance using OpenAI
def check_compliance(privacy_text, terms_text):
    prompt = f"""
    Analyze the following privacy policy and terms & conditions for compliance with SMS communication standards.

    **Privacy Policy:**
    {privacy_text}

    **Terms & Conditions:**
    {terms_text}

    **Checklist:**
    - Does the privacy policy state that SMS consent data will not be shared with third parties?
    - Does it clearly explain data collection and usage?
    - Do the terms specify the types of messages users will receive?
    - Are mandatory disclosures like opt-out instructions included?

    Return JSON format.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a compliance auditor."},
                      {"role": "user", "content": prompt}],
            response_format="json_object"
        )
        return response.choices[0].message.content
    except Exception as e:
        return {"error": f"AI processing failed: {str(e)}"}

# ✅ FastAPI route to check compliance
@app.get("/check_compliance")
def check_compliance_endpoint(website_url: str):
    website_url = ensure_https(website_url)
    crawled_pages = crawl_website(website_url, max_depth=2)

    privacy_text, terms_text = "", ""

    for link in crawled_pages:
        page_text = extract_text_from_url(link)
        if "privacy" in link:
            privacy_text += " " + page_text
        elif "terms" in link or "conditions" in link or "terms-of-service" in link:
            terms_text += " " + page_text

    if not privacy_text and not terms_text:
        raise HTTPException(status_code=400, detail="Could not extract relevant text from the website.")

    compliance_report = check_compliance(privacy_text, terms_text)
    return {"compliance_analysis": compliance_report}
