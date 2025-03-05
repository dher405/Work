#!/bin/bash

echo "🔹 Starting Chrome & ChromeDriver installation..."

# Install Chromium
echo "🔹 Installing Chromium..."
mkdir -p $HOME/chromium
cd $HOME/chromium
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -x google-chrome-stable_current_amd64.deb $HOME/chromium/
export CHROME_BIN="$HOME/chromium/opt/google/chrome/google-chrome"
echo "✅ Chromium installed at $CHROME_BIN"

# Fetch latest ChromeDriver version dynamically
echo "🔹 Fetching latest ChromeDriver version..."
LATEST_VERSION=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform == "linux64") | .url' | head -1)

if [ -z "$LATEST_VERSION" ]; then
    echo "❌ Failed to fetch latest ChromeDriver version!"
    exit 1
fi

# Install ChromeDriver
echo "🔹 Installing ChromeDriver..."
mkdir -p $HOME/chromedriver
cd $HOME/chromedriver
wget "$LATEST_VERSION" -O chromedriver-linux64.zip
unzip chromedriver-linux64.zip
export CHROMEDRIVER_BIN="$HOME/chromedriver/chromedriver-linux64/chromedriver"
echo "✅ ChromeDriver installed at $CHROMEDRIVER_BIN"

# Export Paths
export PATH=$CHROME_BIN:$CHROMEDRIVER_BIN:$PATH
echo "✅ Chrome & ChromeDriver setup complete."
