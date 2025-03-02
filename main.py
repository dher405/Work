from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
import requests
from bs4 import BeautifulSoup
import logging
import os
import openai
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import asyncpg
from pydantic import BaseModel

app = FastAPI()

# Load OpenAI API Key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY as an environment variable.")
openai.api_key = OPENAI_API_KEY

# Load Supabase Database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL. Set this in environment variables.")

# Set up database connection
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Pydantic model for request validation
class PolicyRequest(BaseModel):
    domain: str

# Function to find Privacy Policy and Terms of Service URLs using OpenAI
def find_policy_urls(domain):
    prompt = f"""
    Given the domain {domain}, determine the most likely URLs where the Privacy Policy and Terms of Service pages are located.
    Consider standard locations like /privacy-policy, /privacy, /legal/privacy-policy, /terms, /terms-of-service, /legal/terms.
    Return the URLs as JSON:
    {{"privacy_policy": "URL", "terms_of_service": "URL"}}
    """
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a web crawling assistant."},
                  {"role": "user", "content": prompt}],
        max_tokens=100
    )
    
    import json
    return json.loads(response.choices[0].message.content)

# Function to fetch page content
def extract_text_from_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return " ".join([p.get_text() for p in soup.find_all("p")])
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching URL {url}: {str(e)}")
        return None

# Function to analyze policy compliance using GPT
def analyze_compliance(text, policy_type):
    prompt = f"""
    Analyze the following {policy_type} and determine if it contains:
    - Data collection & sharing disclosures
    - Opt-out & SMS consent details
    - Third-party data handling (for Privacy Policy)
    - Message frequency, opt-out, and HELP instructions (for Terms of Service)
    - Links to Privacy Policy & Terms of Service
    
    Return a JSON response with:
    {{"status": "Pass" or "Fail", "missing_elements": ["list of missing elements"], "recommendations": "suggestions for compliance"}}
    
    Text:
    {text}
    """
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a compliance expert analyzing website policies."},
                  {"role": "user", "content": prompt}],
        max_tokens=200
    )
    
    import json
    return json.loads(response.choices[0].message.content)

# API Endpoint to validate Privacy Policy & Terms of Service and store results in Supabase
@app.post("/validate/policies")
async def check_policies(request: PolicyRequest, db: AsyncSession = Depends(get_db)):
    domain = request.domain
    policy_urls = find_policy_urls(domain)
    
    if not policy_urls:
        raise HTTPException(status_code=400, detail="Unable to determine policy URLs.")
    
    privacy_text = extract_text_from_url(policy_urls.get("privacy_policy"))
    terms_text = extract_text_from_url(policy_urls.get("terms_of_service"))
    
    privacy_result = analyze_compliance(privacy_text, "Privacy Policy") if privacy_text else {"status": "Fail", "reason": "Privacy Policy not accessible"}
    terms_result = analyze_compliance(terms_text, "Terms of Service") if terms_text else {"status": "Fail", "reason": "Terms of Service not accessible"}
    
    # Store results in Supabase
    from sqlalchemy import text

    query = text("""
    INSERT INTO policy_compliance (domain, privacy_policy_status, terms_status, privacy_missing, terms_missing)
    VALUES (:domain, :privacy_status, :terms_status, :privacy_missing, :terms_missing)
    """)
    await db.execute(query, {
        "domain": domain,
        "privacy_status": privacy_result.get("status"),
        "terms_status": terms_result.get("status"),
        "privacy_missing": str(privacy_result.get("missing_elements", [])),
        "terms_missing": str(terms_result.get("missing_elements", []))
    })
    await db.commit()
    
    return {"privacy_policy": privacy_result, "terms_of_service": terms_result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

