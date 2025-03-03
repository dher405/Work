from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
import requests
from bs4 import BeautifulSoup
import logging
import csv
import io
import re
import sqlite3

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Database setup
def get_db_connection():
    conn = sqlite3.connect("validation_results.db")
    conn.execute('''CREATE TABLE IF NOT EXISTS validations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        business_type TEXT,
                        brand_status TEXT,
                        campaign_id TEXT,
                        campaign_status TEXT
                    )''')
    return conn

# Function to save validation results
def save_validation_result(business_type, brand_status, campaign_id=None, campaign_status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO validations (business_type, brand_status, campaign_id, campaign_status) VALUES (?, ?, ?, ?)",
                   (business_type, brand_status, campaign_id, campaign_status))
    conn.commit()
    conn.close()

# Function to fetch rejection error codes
def fetch_rejection_codes():
    try:
        url = "https://support.ringcentral.com/article-v2/Troubleshooting-TCR-rejection-codes.html"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
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

# Function to check campaign approval status
def check_campaign_status(campaign_id: str):
    try:
        url = f"https://csp.campaignregistry.com/api/campaigns/{campaign_id}/status"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking campaign status: {str(e)}")
        return {"error": "Failed to fetch campaign status. Please check the campaign ID or network connectivity."}

# Function to process bulk CSV validation
def process_bulk_csv(file_content):
    results = []
    csv_reader = csv.DictReader(io.StringIO(file_content.decode("utf-8")))
    for row in csv_reader:
        business_check = check_prohibited_business(row.get("business_type", ""))
        brand_check = validate_brand_info(row)
        save_validation_result(row.get("business_type", ""), brand_check["status"])
        results.append({"business": business_check, "brand": brand_check})
    return results

@app.get("/validate/error_codes")
def validate_error_codes():
    error_codes = fetch_rejection_codes()
    if "error" in error_codes:
        raise HTTPException(status_code=500, detail=error_codes["error"])
    return {"status": "Success", "error_codes": error_codes}

@app.get("/validate/business")
def validate_business(business_type: str):
    result = check_prohibited_business(business_type)
    save_validation_result(business_type, result["status"])
    return result

@app.post("/validate/brand")
def validate_brand(brand_data: dict):
    result = validate_brand_info(brand_data)
    save_validation_result(brand_data.get("Legal Business Name", "Unknown"), result["status"])
    return result

@app.get("/validate/campaign_status")
def validate_campaign_status(campaign_id: str):
    result = check_campaign_status(campaign_id)
    save_validation_result("N/A", "N/A", campaign_id, result.get("status", "Error"))
    return result

@app.post("/validate/bulk_csv")
def validate_bulk_csv(file: UploadFile = File(...)):
    try:
        file_content = file.file.read()
        results = process_bulk_csv(file_content)
        return {"status": "Success", "results": results}
    except Exception as e:
        logging.error(f"Error processing CSV file: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing CSV file.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

