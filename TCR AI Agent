from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import logging

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to fetch rejection error codes
def fetch_rejection_codes():
    try:
        url = "https://support.ringcentral.com/article-v2/Troubleshooting-TCR-rejection-codes.html"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract and parse error codes (modify based on actual page structure)
        error_codes = {code.text: description.text for code, description in zip(soup.find_all('code'), soup.find_all('p'))}
        return error_codes
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching rejection codes: {str(e)}")
        return {"error": "Failed to fetch rejection codes. Please check the URL or network connectivity."}

# Function to check prohibited business categories
def check_prohibited_business(business_type: str):
    prohibited_categories = [
        "Indirect Lending", "High-Risk Investment", "Gambling/Sweepstakes", "Debt Relief", "Multi-Level Marketing",
        "Regulated Items", "Lead Generation"
    ]
    if business_type in prohibited_categories:
        return {"status": "Rejected", "reason": f"{business_type} is a prohibited business category."}
    return {"status": "Approved"}

# Function to validate brand information
def validate_brand_info(brand_data: dict):
    required_fields = ["Legal Business Name", "Brand Name", "Legal Classification", "EIN", "Website URL"]
    missing_fields = [field for field in required_fields if field not in brand_data]
    if missing_fields:
        return {"status": "Rejected", "missing_fields": missing_fields}
    return {"status": "Approved"}

@app.get("/validate/error_codes")
def validate_error_codes():
    error_codes = fetch_rejection_codes()
    if "error" in error_codes:
        raise HTTPException(status_code=500, detail=error_codes["error"])
    return {"status": "Success", "error_codes": error_codes}

@app.get("/validate/business")
def validate_business(business_type: str):
    return check_prohibited_business(business_type)

@app.post("/validate/brand")
def validate_brand(brand_data: dict):
    return validate_brand_info(brand_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
