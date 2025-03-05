#!/bin/bash

set -e  # Exit on error
set -x  # Enable debug logging

# Define paths
CHROMIUM_DIR="/opt/render/chromium"
CHROMEDRIVER_DIR="/opt/render/chromedriver"
CHROME_BIN="$CHROMIUM_DIR/chrome-linux64/chrome"
CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

# Function to fetch the latest stable Chrome version with fallback
get_latest_stable_version() {
    local version=$(curl -s https://chromiumdash.appspot.com/fetch_releases?platform=Linux&num=1 | jq -r '.[0].version')
    if [[ -z "$version" || "$version" == "null" ]]; then
        echo "WARNING: Failed to retrieve latest Chrome version. Trying fallback..."
        curl -s https://versionhistory.googleapis.com/v1/chrome/platforms/linux/channels/stable/versions | jq -r '.versions[0].version'
    else
        echo "$version"
    fi
}

LATEST_STABLE=$(get_latest_stable_version)

if [[ -z "$LATEST_STABLE" || "$LATEST_STABLE" == "null" ]]; then
    echo "ERROR: Failed to retrieve the latest Chromium version!"
    exit 1
fi

echo "Latest stable Chrome version: $LATEST_STABLE"

CHROMIUM_URL="https://download-chromium.appspot.com/dl/Linux_x64?type=snapshots"

echo "Downloading Chromium from: $CHROMIUM_URL"
mkdir -p "$CHROMIUM_DIR"
wget -O "$CHROMIUM_DIR/chrome-linux.zip" "$CHROMIUM_URL" || { echo "❌ Chrome download failed!"; exit 1; }

echo "📂 Extracting Chrome..."
unzip -o "$CHROMIUM_DIR/chrome-linux.zip" -d "$CHROMIUM_DIR"
chmod +x "$CHROME_BIN"

if [[ ! -f "$CHROME_BIN" ]]; then
    echo "❌ Chrome installation failed!"
    exit 1
fi

echo "✅ Chrome installed at: $CHROME_BIN"
"$CHROME_BIN" --version

# --- Install the Correct ChromeDriver ---

get_latest_chromedriver_version() {
    local version=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
    if [[ -z "$version" || "$version" == "null" ]]; then
        echo "WARNING: Failed to retrieve latest ChromeDriver version. Using Chrome version fallback."
        echo "$LATEST_STABLE"
    else
        echo "$version"
    fi
}

LATEST_CHROMEDRIVER_VERSION=$(get_latest_chromedriver_version)

if [[ -z "$LATEST_CHROMEDRIVER_VERSION" || "$LATEST_CHROMEDRIVER_VERSION" == "null" ]]; then
    echo "ERROR: Failed to retrieve the latest ChromeDriver version!"
    exit 1
fi

CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${LATEST_CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip"

echo "Downloading ChromeDriver from: $CHROMEDRIVER_URL"
mkdir -p "$CHROMEDRIVER_DIR"
wget -O "$CHROMEDRIVER_DIR/chromedriver-linux.zip" "$CHROMEDRIVER_URL" || { echo "❌ ChromeDriver download failed!"; exit 1; }

echo "📂 Extracting ChromeDriver..."
unzip -o "$CHROMEDRIVER_DIR/chromedriver-linux.zip" -d "$CHROMEDRIVER_DIR"
chmod +x "$CHROMEDRIVER_BIN"

if [[ ! -f "$CHROMEDRIVER_BIN" ]]; then
    echo "❌ ChromeDriver installation failed!"
    exit 1
fi

echo "✅ ChromeDriver installed at: $CHROMEDRIVER_BIN"
"$CHROMEDRIVER_BIN" --version
