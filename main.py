import os
import requests
from bs4 import BeautifulSoup
import openai
import re
from fastapi import FastAPI, HTTPException
from urllib.parse import urljoin
from fastapi.middleware.cors import CORSMiddleware


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
    if not url.startswith("http"):
        return "https://" + url
    return url

def crawl_website(website_url):
    """Crawl the website to find Privacy Policy, Terms & Conditions, and Legal pages."""
    try:
        website_url = ensure_https(website_url)
        response = requests.get(website_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        found_links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].lower()
            full_url = urljoin(website_url, href)
            found_links.add(full_url)
        
        privacy_url = next((link for link in found_links if "privacy" in link), None)
        terms_url = next((link for link in found_links if "terms" in link or "conditions" in link or "terms-of-service" in link), None)
        legal_url = next((link for link in found_links if "legal" in link), None)
        
        return privacy_url, terms_url, legal_url
    except requests.RequestException:
        return None, None, None

def extract_text_from_url(url):
    """Extract text content from a given webpage."""
    if not url:
        return ""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = "\n".join(p.get_text() for p in soup.find_all(['p', 'li', 'span', 'div']))
        return re.sub(r'\s+', ' ', text.strip())
    except requests.RequestException:
        return ""

def normalize_text(text):
    """Normalize text to improve matching accuracy."""
    return re.sub(r'[^a-zA-Z0-9 ]', '', text).lower()

def check_compliance(privacy_text, terms_text, legal_text):
    """Send extracted text to GPT-4o-mini for compliance check."""
    
    # Normalize privacy policy text for better matching
    normalized_privacy_text = normalize_text(privacy_text)

    # Define an exact match phrase to detect SMS consent language
    sms_consent_exact_phrase = normalize_text(
        "Information obtained as part of the SMS consent process won’t be shared with third parties."
    )

    # Check for the exact SMS consent statement
    sms_consent_found = sms_consent_exact_phrase in normalized_privacy_text

    # Debugging: Print extracted privacy text (optional, useful for logging)
    print(f"Extracted Privacy Text:\n{privacy_text}\n")
    print(f"Normalized Privacy Text:\n{normalized_privacy_text}\n")

    # If missing, explicitly notify GPT
    missing_sms_consent = "" if sms_consent_found else (
        "**WARNING:** Privacy Policy does NOT explicitly state that SMS consent information is not shared with third parties.\n\n"
    )

    prompt = f"""
    You are an expert in TCR compliance checking. Analyze the provided Privacy Policy, Terms of Service, and Legal page.

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

    **Legal Compliance:**
    - Check for any additional regulatory or compliance-related text.

    **Privacy Policy Extract:**\n\n{privacy_text[:2000] if privacy_text else 'No privacy policy found'}\n\n
    **Terms & Conditions Extract:**\n\n{terms_text[:2000] if terms_text else 'No terms & conditions found'}\n\n
    **Legal Page Extract:**\n\n{legal_text[:2000] if legal_text else 'No legal page found'}\n\n
    Return a well-formatted compliance report indicating if the required elements are present or missing, using line breaks and bullet points where necessary.
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
    privacy_url, terms_url, legal_url = crawl_website(website_url)
    
    if not privacy_url and not terms_url and not legal_url:
        raise HTTPException(status_code=400, detail="Could not find Privacy Policy, Terms & Conditions, or Legal pages.")
    
    privacy_text = extract_text_from_url(privacy_url)
    terms_text = extract_text_from_url(terms_url)
    legal_text = extract_text_from_url(legal_url)
    
    if not privacy_text and not terms_text and not legal_text:
        raise HTTPException(status_code=400, detail="Could not extract text from any of the pages.")
    
    compliance_report = check_compliance(privacy_text, terms_text, legal_text)
    return {"compliance_report": compliance_report}

