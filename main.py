import os
import requests
from bs4 import BeautifulSoup
import openai
import re

# Load API Key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

openai.api_key = OPENAI_API_KEY

def get_policy_links(website_url):
    """Find Privacy Policy and Terms & Conditions links from the homepage."""
    try:
        response = requests.get(website_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        privacy_url, terms_url = None, None
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].lower()
            if "privacy" in href:
                privacy_url = href if "http" in href else website_url.rstrip('/') + '/' + href.lstrip('/')
            if "terms" in href or "conditions" in href:
                terms_url = href if "http" in href else website_url.rstrip('/') + '/' + href.lstrip('/')
        
        return privacy_url, terms_url
    except requests.RequestException as e:
        print(f"Error fetching website: {e}")
        return None, None

def extract_text_from_url(url):
    """Extract text content from a given webpage."""
    if not url:
        return None
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = " ".join(p.get_text() for p in soup.find_all(['p', 'li', 'span', 'div']))
        return re.sub(r'\s+', ' ', text.strip())
    except requests.RequestException as e:
        print(f"Error fetching page {url}: {e}")
        return None

def check_compliance(privacy_text, terms_text):
    """Send extracted text to GPT-4o-mini for compliance check."""
    prompt = f"""
    You are an expert in TCR compliance checking. Analyze the provided Privacy Policy and Terms of Service.
    
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
    
    **Privacy Policy Extract:** {privacy_text[:2000]}
    **Terms & Conditions Extract:** {terms_text[:2000]}
    
    Return a compliance report indicating if the required elements are present or missing.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a compliance auditor."},
                  {"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    return response['choices'][0]['message']['content']

def main():
    website_url = input("Enter customer website URL: ")
    privacy_url, terms_url = get_policy_links(website_url)
    
    if not privacy_url or not terms_url:
        print("Could not find Privacy Policy or Terms & Conditions pages.")
        return
    
    print(f"Found Privacy Policy: {privacy_url}\nFound Terms & Conditions: {terms_url}")
    
    privacy_text = extract_text_from_url(privacy_url)
    terms_text = extract_text_from_url(terms_url)
    
    if not privacy_text or not terms_text:
        print("Could not extract text from one or both pages.")
        return
    
    compliance_report = check_compliance(privacy_text, terms_text)
    print("\nTCR Compliance Report:\n", compliance_report)
    
if __name__ == "__main__":
    main()

