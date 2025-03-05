#!/bin/bash

set -e  # Exit on error
set -x  # Enable debug logging

# Define paths
CHROMIUM_DIR="$HOME/chromium"
CHROMEDRIVER_DIR="$HOME/chromedriver"
CHROME_BIN="$CHROMIUM_DIR/chrome-linux64/chrome"
CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

# Function to fetch the latest stable Chrome version with fallback
get_latest_stable_version() {
    local version=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json | jq -r '.milestones | to_entries | max_by(.key | tonumber) | .value.chromeVersion')
    if [[ -z "$version" || "$version" == "null" ]]; then
        echo "WARNING: Failed to retrieve latest Chrome version from primary source. Trying fallback..."
        curl -s https://versionhistory.googleapis.com/v1/chrome/platforms/linux/channels/stable/versions | jq -r '.versions[0].version'
    else
        echo "$version"
    fi
}

# Extract only the version number using awk
LATEST_STABLE=$(get_latest_stable_version | awk 'END {print}')

if [[ -z "$LATEST_STABLE" || "$LATEST_STABLE" == "null" ]]; then
    echo "ERROR: Failed to retrieve the latest Chromium version!"
    exit 1
fi

echo "Latest stable Chrome version: $LATEST_STABLE"

# Temporarily use the secondary source to construct the Chromium download URL
CHROMIUM_URL="https://storage.googleapis.com/chrome-for-testing-public/${LATEST_STABLE}/linux64/chrome-linux64.zip"

echo "Downloading Chromium from: $CHROMIUM_URL"
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

# --- Install the Correct ChromeDriver ---

# Fetch ChromeDriver download URL (using the same fallback logic as for Chrome version)
get_latest_chromedriver_version() {
    local version=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json | jq -r ".milestones | to_entries | max_by(.key | tonumber) | .value.downloads.chromedriver| select(.platform == \"linux64\") | .url" | cut -d'/' -f6)
    if [[ -z "$version" || "$version" == "null" ]]; then
        echo "WARNING: Failed to retrieve latest ChromeDriver version from primary source. Trying fallback..."
        # For ChromeDriver, we'll just use the Chrome version as a fallback for now
        echo "$LATEST_STABLE"
    else
        echo "$version"
    fi
}

LATEST_CHROMEDRIVER_VERSION=$(get_latest_chromedriver_version)

if [[ -z "$LATEST_CHROMEDRIVER_VERSION" || "$LATEST_CHROMEDRIVER_VERSION" == "null" ]]; then
    echo "ERROR: Failed to retrieve the latest ChromeDriver version!"
    exit 1
