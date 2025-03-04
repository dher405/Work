import traceback

def extract_text_from_url(url):
    """Extract text content from a given webpage. Uses Selenium if needed."""
    if not url:
        return ""

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = "\n".join(p.get_text() for p in soup.find_all(['p', 'li', 'span', 'div', 'body']))
        text = re.sub(r'\s+', ' ', text.strip())

        if not text.strip():
            print(f"Requests failed to extract meaningful text from {url}. Trying Selenium...")

            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            # Use the manually installed Chromium and ChromeDriver
            chrome_binary = os.getenv("CHROME_BIN", "/home/render/chromium/chrome-linux64/chrome")
            chromedriver_binary = os.getenv("CHROMEDRIVER_BIN", "/home/render/chromedriver/chromedriver-linux64/chromedriver")

            if not os.path.exists(chrome_binary):
                print(f"ERROR: Chromium binary not found at {chrome_binary}. Exiting.")
                return ""

            if not os.path.exists(chromedriver_binary):
                print(f"ERROR: ChromeDriver binary not found at {chromedriver_binary}. Exiting.")
                return ""

            chrome_options.binary_location = chrome_binary

            print(f"Using Chromium binary at: {chrome_binary}")
            print(f"Using ChromeDriver binary at: {chromedriver_binary}")

            driver = None
            try:
                service = Service(executable_path=chromedriver_binary)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.get(url)
                text = driver.find_element("xpath", "//body").text
            except Exception:
                print("ERROR: Selenium extraction failed!")
                print(traceback.format_exc())
                text = ""  # Ensure text is not None
            finally:
                if driver:
                    driver.quit()

        return text

    except requests.RequestException:
        print(f"Requests completely failed for {url}. Falling back to Selenium.")
        print(traceback.format_exc())
        return ""
