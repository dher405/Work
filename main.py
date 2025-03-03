import os
import requests
from bs4 import BeautifulSoup
import openai
import re
from fastapi import FastAPI, HTTPException
from urllib.parse import urljoin

# Load API Key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

openai.api_key = OPENAI_API_KEY

app = FastAPI()

def crawl_website(website_url):
    """Crawl the website to find Privacy Policy, Terms & Conditions, and Legal pages."""
    try:
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
        text = " ".join(p.get_text() for p in soup.find_all(['p', 'li', 'span', 'div']))
        return re.sub(r'\s+', ' ', text.strip())
    except requests.RequestException:
        return ""

def check_compliance(privacy_text, terms_text, legal_text):
    """Send extracted text to GPT-4o-mini for compliance check."""
    prompt = f"""
    You are an expert in TCR compliance checking. Analyze the provided Privacy Policy, Terms of Service, and Legal page.
    
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
    
    **Privacy Policy Extract:** {privacy_text[:2000] if privacy_text else 'No privacy policy found'}
    **Terms & Conditions Extract:** {terms_text[:2000] if terms_text else 'No terms & conditions found'}
    **Legal Page Extract:** {legal_text[:2000] if legal_text else 'No legal page found'}
    
    Return a compliance report indicating if the required elements are present or missing.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a compliance auditor."},
                  {"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    return response['choices'][0]['message']['content']

@app.get("/check_compliance")
def check_compliance_endpoint(website_url: str):
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
