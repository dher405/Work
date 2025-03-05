#!/bin/bash
set -e  # Exit on error

echo "🚀 Fetching the latest stable Chromium version..."
LATEST_CHROMIUM_VERSION=$(curl -s https://download-chromium.appspot.com/rev/Linux_x64?type=snapshots | jq -r '.content')

if [[ -z "$LATEST_CHROMIUM_VERSION" ]]; then
    echo "❌ Failed to fetch the latest Chromium version!"
    exit 1
fi

CHROMIUM_DOWNLOAD_URL="https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/$LATEST_CHROMIUM_VERSION/chrome-linux.zip"
CHROMEDRIVER_DOWNLOAD_URL="https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/$LATEST_CHROMIUM_VERSION/chromedriver_linux64.zip"

echo "📥 Downloading Chromium build $LATEST_CHROMIUM_VERSION..."
wget -q --show-progress "$CHROMIUM_DOWNLOAD_URL" -O chrome-linux.zip || { echo "❌ Failed to download Chromium."; exit 1; }

echo "📥 Downloading ChromeDriver for build $LATEST_CHROMIUM_VERSION..."
wget -q --show-progress "$CHROMEDRIVER_DOWNLOAD_URL" -O chromedriver-linux64.zip || { echo "❌ Failed to download ChromeDriver."; exit 1; }

echo "📦 Extracting Chromium and ChromeDriver..."
mkdir -p /opt/render/chromium /opt/render/chromedriver
unzip -q chrome-linux.zip -d /opt/render/chromium || { echo "❌ Failed to extract Chromium."; exit 1; }
unzip -q chromedriver-linux64.zip -d /opt/render/chromedriver || { echo "❌ Failed to extract ChromeDriver."; exit 1; }

echo "🔍 Verifying Chromium installation..."
ls -l /opt/render/chromium/chrome-linux/

# Ensure binaries are correctly set
export CHROME_BIN="/opt/render/chromium/chrome-linux/chrome"
export CHROMEDRIVER_BIN="/opt/render/chromedriver/chromedriver"

if [[ ! -f "$CHROME_BIN" ]]; then
    echo "❌ Chrome binary not found at $CHROME_BIN!"
    exit 1
fi

if [[ ! -f "$CHROMEDRIVER_BIN" ]]; then
    echo "❌ ChromeDriver binary not found at $CHROMEDRIVER_BIN!"
    exit 1
fi

echo "✅ Chromium and ChromeDriver installed successfully."
echo "🌍 Chrome binary set to: $CHROME_BIN"
echo "🌍 ChromeDriver binary set to: $CHROMEDRIVER_BIN"

