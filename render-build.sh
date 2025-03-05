#!/bin/bash
set -e

echo "Fetching the latest stable Chromium version..."
LATEST_CHROMIUM_URL=$(curl -s https://download-chromium.appspot.com/rev/Linux_x64?type=snapshots)

if [[ -z "$LATEST_CHROMIUM_URL" ]]; then
    echo "❌ Failed to fetch the latest Chromium version!"
    exit 1
fi

CHROMIUM_DOWNLOAD_URL="https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/$LATEST_CHROMIUM_URL/chrome-linux.zip"
CHROMEDRIVER_DOWNLOAD_URL="https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/$LATEST_CHROMIUM_URL/chromedriver_linux64.zip"

echo "Downloading Chromium build $LATEST_CHROMIUM_URL..."
wget -q --show-progress "$CHROMIUM_DOWNLOAD_URL" -O chrome-linux.zip || { echo "❌ Failed to download Chromium."; exit 1; }

echo "Downloading ChromeDriver for build $LATEST_CHROMIUM_URL..."
wget -q --show-progress "$CHROMEDRIVER_DOWNLOAD_URL" -O chromedriver-linux64.zip || { echo "❌ Failed to download ChromeDriver."; exit 1; }

echo "Extracting Chromium and ChromeDriver..."
mkdir -p /opt/render/chromium /opt/render/chromedriver
unzip -q chrome-linux.zip -d /opt/render/chromium || { echo "❌ Failed to extract Chromium."; exit 1; }
unzip -q chromedriver-linux64.zip -d /opt/render/chromedriver || { echo "❌ Failed to extract ChromeDriver."; exit 1; }

echo "✅ Chromium and ChromeDriver installed successfully."

# Ensure binaries are in correct paths
export CHROME_BIN="/opt/render/chromium/chrome-linux/chrome"
export CHROMEDRIVER_BIN="/opt/render/chromedriver/chromedriver"

echo "Chromium binary set to: $CHROME_BIN"
echo "ChromeDriver binary set to: $CHROMEDRIVER_BIN"
