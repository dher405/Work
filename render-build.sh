#!/bin/bash

echo "🔹 Starting Chrome & ChromeDriver installation..."

# Ensure dependencies are installed
apt-get update && apt-get install -y wget unzip jq curl

# Install Chromium
echo "🔹 Installing Chromium..."
mkdir -p $HOME/chromium
cd $HOME/chromium
wget -qO- https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb > google-chrome.deb
dpkg -x google-chrome.deb $HOME/chromium/
export CHROME_BIN="$HOME/chromium/opt/google/chrome/google-chrome"
echo "✅ Chromium installed at $CHROME_BIN"

# Fetch latest ChromeDriver version dynamically
echo "🔹 Fetching latest ChromeDriver version..."
LATEST_CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform == "linux64") | .url' | head -1)

if [ -z "$LATEST_CHROMEDRIVER_URL" ]; then
    echo "❌ Failed to fetch latest ChromeDriver version!"
    exit 1
fi

# Install ChromeDriver
echo "🔹 Installing ChromeDriver..."
mkdir -p $HOME/chromedriver
cd $HOME/chromedriver
wget "$LATEST_CHROMEDRIVER_URL" -O chromedriver-linux64.zip
unzip chromedriver-linux64.zip
export CHROMEDRIVER_BIN="$HOME/chromedriver/chromedriver-linux64/chromedriver"
chmod +x $CHROMEDRIVER_BIN
echo "✅ ChromeDriver installed at $CHROMEDRIVER_BIN"

# Export Paths
export PATH=$CHROME_BIN:$CHROMEDRIVER_BIN:$PATH
echo "✅ Chrome & ChromeDriver setup complete."
