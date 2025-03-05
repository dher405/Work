#!/bin/bash

set -e  # Exit on error
set -x  # Enable debug logging

# Define paths
CHROMIUM_DIR="$HOME/chromium"
CHROMEDRIVER_DIR="$HOME/chromedriver"
CHROME_BIN="$CHROMIUM_DIR/chrome-linux64/chrome"
CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

# Function to fetch the latest Chromium version
get_chromium_version() {
    curl -s "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone.json" | jq -r '.milestones["122"].downloads.chromium[] | select(.platform=="linux64") | .url'
}

# Fetch the latest Chromium build
CHROMIUM_ZIP_URL=$(get_chromium_version)

if [[ -z "$CHROMIUM_ZIP_URL" ]]; then
    echo "❌ Failed to retrieve Chromium download URL!"
    exit 1
fi

echo "✅ Downloading Chromium from: $CHROMIUM_ZIP_URL"
mkdir -p "$CHROMIUM_DIR"
wget -O "$CHROMIUM_DIR/chrome-linux.zip" "$CHROMIUM_ZIP_URL"

echo "📂 Extracting Chromium..."
unzip -o "$CHROMIUM_DIR/chrome-linux.zip" -d "$CHROMIUM_DIR"
chmod +x "$CHROME_BIN"

# Verify Chromium installation
if [[ ! -f "$CHROME_BIN" ]]; then
    echo "❌ Chromium installation failed!"
    exit 1
fi

echo "✅ Chromium installed at: $CHROME_BIN"
"$CHROME_BIN" --version

# Fetch the latest ChromeDriver version
CHROMEDRIVER_ZIP_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone.json" | jq -r '.milestones["122"].downloads.chromedriver[] | select(.platform=="linux64") | .url')

if [[ -z "$CHROMEDRIVER_ZIP_URL" ]]; then
    echo "❌ Failed to retrieve ChromeDriver download URL!"
    exit 1
fi

echo "✅ Downloading ChromeDriver from: $CHROMEDRIVER_ZIP_URL"
mkdir -p "$CHROMEDRIVER_DIR"
wget -O "$CHROMEDRIVER_DIR/chromedriver-linux64.zip" "$CHROMEDRIVER_ZIP_URL"

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

