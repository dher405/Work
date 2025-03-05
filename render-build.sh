#!/bin/bash

set -e  # Exit on error
set -x  # Enable debug logging

# Define paths
CHROMIUM_DIR="/opt/render/chromium"
CHROMEDRIVER_DIR="/opt/render/chromedriver"
CHROME_BIN="$CHROMIUM_DIR/chrome-linux64/chrome"
CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

# Fetch the latest stable Chrome version
LATEST_STABLE=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json | jq -r '.milestones | to_entries | max_by(.key | tonumber) | .value.chromeVersion')

echo "Latest stable Chrome version: $LATEST_STABLE"

# Fetch Chromium download URL
CHROMIUM_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json | jq -r ".milestones | to_entries | max_by(.key | tonumber) | .value.downloads.chrome| select(.platform == \"linux64\") | .url")

if [[ -z "$CHROMIUM_URL" ]]; then
    echo "❌ Failed to retrieve Chromium download URL!"
    exit 1
fi

echo "✅ Downloading Chrome from: $CHROMIUM_URL"
mkdir -p "$CHROMIUM_DIR"
wget -O "$CHROMIUM_DIR/chrome-linux.zip" "$CHROMIUM_URL" || { echo "❌ Chrome download failed!"; exit 1; }

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

# Fetch ChromeDriver download URL
CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json | jq -r ".milestones | to_entries | max_by(.key | tonumber) | .value.downloads.chromedriver| select(.platform == \"linux64\") | .url")

if [[ -z "$CHROMEDRIVER_URL" ]]; then
    echo "❌ Failed to retrieve ChromeDriver download URL!"
    exit 1
fi

echo "✅ Downloading ChromeDriver from: $CHROMEDRIVER_URL"
mkdir -p "$CHROMEDRIVER_DIR"
wget -O "$CHROMEDRIVER_DIR/chromedriver-linux64.zip" "$CHROMEDRIVER_URL"

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
