#!/bin/bash

set -e  # Exit on error
set -x  # Enable debug logging

# Define paths
CHROMIUM_DIR="$HOME/chromium"
CHROMEDRIVER_DIR="$HOME/chromedriver"
CHROME_BIN="$CHROMIUM_DIR/chrome-linux64/chrome"
CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

echo "🚀 Fetching the latest stable Chromium version..."
LATEST_CHROMIUM_VERSION=$(curl -s "https://download-chromium.appspot.com/LAST_CHANGE")
CHROMIUM_ZIP_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F${LATEST_CHROMIUM_VERSION}%2Fchrome-linux.zip?alt=media"

echo "✅ Latest Chromium Version: $LATEST_CHROMIUM_VERSION"
echo "🔽 Downloading Chromium from: $CHROMIUM_ZIP_URL"
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

# Fetch ChromeDriver version matching Chromium
echo "🚀 Fetching compatible ChromeDriver version..."
LATEST_DRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone.json" | jq -r '.milestones["'${LATEST_CHROMIUM_VERSION:0:3}'"].downloads.chromedriver[] | select(.platform=="linux64") | .url')

echo "✅ ChromeDriver URL: $LATEST_DRIVER_VERSION"
mkdir -p "$CHROMEDRIVER_DIR"
wget -O "$CHROMEDRIVER_DIR/chromedriver-linux64.zip" "$LATEST_DRIVER_VERSION"

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
