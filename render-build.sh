#!/bin/bash

set -e  # Exit on error
set -x  # Enable debug logging

# Define paths
CHROMIUM_DIR="/opt/render/chromium"
CHROMEDRIVER_DIR="/opt/render/chromedriver"
CHROME_BIN="$CHROMIUM_DIR/chrome-linux64/chrome"
CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

# Function to fetch the latest stable Chrome for Testing version
get_latest_chromium_url() {
    curl -s "https://versionhistory.googleapis.com/v1/chrome/platforms/linux/channels/stable/versions" | \
    jq -r '.versions[0].downloads.chromium| select(.platform != null and (.platform | contains("linux64"))) | .url'
}

# Fetch the latest Chrome download URL
CHROMIUM_ZIP_URL=$(get_latest_chromium_url)

if [[ -z "$CHROMIUM_ZIP_URL" ]]; then
    echo "❌ Failed to retrieve Chromium download URL!"
    exit 1
fi

echo "✅ Downloading Chrome from: $CHROMIUM_ZIP_URL"
mkdir -p "$CHROMIUM_DIR"
wget -O "$CHROMIUM_DIR/chrome-linux.zip" "$CHROMIUM_ZIP_URL" || { echo "❌ Chrome download failed!"; exit 1; }

echo "📂 Extracting Chrome..."
unzip -o "$CHROMIUM_DIR/chrome-linux.zip" -d "$CHROMIUM_DIR"
chmod +x "$CHROME_BIN"

# Verify Chrome installation
if [[ ! -f "$CHROME_BIN" ]]; then
    echo "❌ Chrome installation failed!"
    exit 1
fi

echo "✅ Chrome installed at: $CHROME_BIN"
"$CHROME_BIN" --version

# Fetch the latest ChromeDriver version that matches Chromium
get_latest_chromedriver_url() {
    curl -s "https://versionhistory.googleapis.com/v1/chrome/platforms/linux/channels/stable/versions" | \
    jq -r '.versions[0].downloads.chromedriver| select(.platform != null and (.platform | contains("linux64"))) | .url'
}

LATEST_CHROMEDRIVER_URL=$(get_latest_chromedriver_url)

if [[ -z "$LATEST_CHROMEDRIVER_URL" ]]; then
    echo "❌ Failed to retrieve ChromeDriver download URL!"
    exit 1
fi

echo "✅ Downloading ChromeDriver from: $LATEST_CHROMEDRIVER_URL"
mkdir -p "$CHROMEDRIVER_DIR"
wget -O "$CHROMEDRIVER_DIR/chromedriver-linux64.zip" "$LATEST_CHROMEDRIVER_URL"

echo "📂 Extracting ChromeDriver..."
unzip -o "$CHROMEDRIVER_DIR/chromedriver-linux64.zip" -d "$CHROMEDRIVER_DIR"
chmod +x "$CHROMEDRIVER_BIN"

# Verify ChromeDriver installation
if [[ ! -f "$CHROMEDRIVER_BIN" ]]; then
    echo "❌ ChromeDriver installation failed!"
    exit 1
fi

echo "✅ ChromeDriver installed at: $CHROMEDRIVER_BIN"
"$CHROMEDRIVER_BIN" --version

# Export paths for runtime
export CHROME_BIN="$CHROME_BIN"
export CHROMEDRIVER_BIN="$CHROMEDRIVER_BIN"

# Start the application
echo "🚀 Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 10000
