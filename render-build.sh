#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status.

echo "🚀 Fetching the latest stable Chromium version..."
LATEST_CHROMIUM_BUILD=$(curl -s https://download-chromium.appspot.com/rev/Linux_x64?type=snapshots | jq -r '.content')

if [[ -z "$LATEST_CHROMIUM_BUILD" ]]; then
    echo "❌ Failed to fetch the latest Chromium version!"
    exit 1
fi

CHROMIUM_DOWNLOAD_URL="https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/$LATEST_CHROMIUM_BUILD/chrome-linux.zip"
CHROMEDRIVER_DOWNLOAD_URL="https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/$LATEST_CHROMIUM_BUILD/chromedriver_linux64.zip"

echo "📥 Downloading Chromium build $LATEST_CHROMIUM_BUILD..."
wget -q --show-progress "$CHROMIUM_DOWNLOAD_URL" -O chrome-linux.zip || { echo "❌ Failed to download Chromium."; exit 1; }

echo "📥 Downloading ChromeDriver for build $LATEST_CHROMIUM_BUILD..."
wget -q --show-progress "$CHROMEDRIVER_DOWNLOAD_URL" -O chromedriver-linux64.zip || { echo "❌ Failed to download ChromeDriver."; exit 1; }

echo "📦 Extracting Chromium and ChromeDriver..."
mkdir -p /opt/render/chromium /opt/render/chromedriver
unzip -q chrome-linux.zip -d /opt/render/chromium || { echo "❌ Failed to extract Chromium."; exit 1; }
unzip -q chromedriver-linux64.zip -d /opt/render/chromedriver || { echo "❌ Failed to extract ChromeDriver."; exit 1; }

echo "🔍 Verifying installation..."
ls -lh /opt/render/chromium/
ls -lh /opt/render/chromedriver/

# **Fix: Locate Chrome and ChromeDriver binaries**
CHROME_BIN=$(find /opt/render/chromium/ -type f -name "chrome" | head -n 1)
CHROMEDRIVER_BIN=$(find /opt/render/chromedriver/ -type f -name "chromedriver" | head -n 1)

if [[ ! -f "$CHROME_BIN" ]]; then
    echo "❌ Chrome binary not found!"
    ls -lh /opt/render/chromium/
    exit 1
fi

if [[ ! -f "$CHROMEDRIVER_BIN" ]]; then
    echo "❌ ChromeDriver binary not found!"
    ls -lh /opt/render/chromedriver/
    exit 1
fi

echo "✅ Chromium and ChromeDriver installed successfully."
echo "🌍 Chrome binary set to: $CHROME_BIN"
echo "🌍 ChromeDriver binary set to: $CHROMEDRIVER_BIN"

# **Set environment variables for system**
export CHROME_BIN="$CHROME_BIN"
export CHROMEDRIVER_BIN="$CHROMEDRIVER_BIN"
