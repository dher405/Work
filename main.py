import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def extract_text_from_website(url, max_retries=3):
    """Extracts text from the given website URL using Selenium with improved error handling."""
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}: Scraping {url}...")

            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")  # Helps prevent crashes in headless mode
            chrome_options.add_argument("--window-size=1920x1080")  # Ensures the page renders fully

            # Start Chrome WebDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.get(url)

            # Wait for the page to fully load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Extract text from the page
            page_text = driver.find_element(By.TAG_NAME, "body").text

            # Close the driver
            driver.quit()

            # Return extracted text
            return page_text.strip()

        except Exception as e:
            print(f"❌ Error extracting text from {url} (Attempt {attempt}/{max_retries}): {e}")
            if attempt == max_retries:
                return f"Failed to extract text from {url} after {max_retries} attempts."
            time.sleep(5)  # Wait before retrying

    return "Text extraction failed."

# Example API function
def check_website_compliance(website_url):
    """Check compliance of the website and return analysis."""
    print(f"INFO: Checking compliance for: {website_url}")

    extracted_text = extract_text_from_website(website_url)

    if "Failed to extract text" in extracted_text:
        return {"error": "Failed to extract text. The website may be blocking requests."}

    # Debugging: Print first 500 characters of extracted text
    print(f"Extracted text preview: {extracted_text[:500]}...")

    # (Your existing OpenAI API call for compliance checking)
    response_data = {
        "compliance_analysis": {
            "privacy_policy": {"status": "checked"},
            "terms_conditions": {"status": "checked"},
            "overall_compliance": "pending_analysis"
        }
    }

    return response_data
