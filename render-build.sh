#!/bin/bash

set -e  # Exit on error
set -x  # Enable debug logging

# Define paths
CHROMIUM_DIR="/opt/render/chromium"
CHROMEDRIVER_DIR="/opt/render/chromedriver"
CHROME_BIN="$CHROMIUM_DIR/chrome-linux64/chrome"
CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

# Function to fetch the latest Chromium version
get_chromium_version() {
    curl -s "https://chromiumdash.appspot.com/fetch_releases?platform=Linux&num=1" | jq -r '.[0].version'
}

# Fetch the latest Chromium build version
LATEST_CHROMIUM_VERSION=$(get_chromium_version)

if [[ -z "$LATEST_CHROMIUM_VERSION" ]]; then
    echo "❌ Failed to retrieve Chromium version!"
    exit 1
fi

# Construct download URL for Chromium
CHROMIUM_ZIP_URL="https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/${LATEST_CHROMIUM_VERSION}/chrome-linux.zip"

echo "✅ Downloading Chromium from: $CHROMIUM_ZIP_URL"
mkdir -p "$CHROMIUM_DIR"
wget -O "$CHROMIUM_DIR/chrome-linux.zip" "$CHROMIUM_ZIP_URL" || { echo "❌ Chromium download failed!"; exit 1; }

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
LATEST_CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone.json" | jq -r '.milestones["122"].downloads.chromedriver[] | select(.platform=="linux64") | .url')

if [[ -z "$LATEST_CHROMEDRIVER_VERSION" ]]; then
    echo "❌ Failed to retrieve ChromeDriver download URL!"
    exit 1
fi

echo "✅ Downloading ChromeDriver from: $LATEST_CHROMEDRIVER_VERSION"
mkdir -p "$CHROMEDRIVER_DIR"
wget -O "$CHROMEDRIVER_DIR/chromedriver-linux64.zip" "$LATEST_CHROMEDRIVER_VERSION"

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

