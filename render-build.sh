#!/bin/bash

# Install dependencies
apt-get update && apt-get install -y wget unzip

# Define directories
CHROME_DIR="$HOME/chromium"
CHROMEDRIVER_DIR="$HOME/chromedriver"
LATEST_CHROME_VERSION=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json | jq -r '.channels.Stable.version')

# Download and install Chrome
mkdir -p $CHROME_DIR
wget -O chrome-linux.zip "https://storage.googleapis.com/chrome-for-testing-public/$LATEST_CHROME_VERSION/linux64/chrome-linux.zip"
unzip chrome-linux.zip -d $CHROME_DIR
rm chrome-linux.zip

# Download and install ChromeDriver
mkdir -p $CHROMEDRIVER_DIR
wget -O chromedriver-linux64.zip "https://storage.googleapis.com/chrome-for-testing-public/$LATEST_CHROME_VERSION/linux64/chromedriver-linux64.zip"
unzip chromedriver-linux64.zip -d $CHROMEDRIVER_DIR
rm chromedriver-linux64.zip

# Set permissions
chmod +x $CHROME_DIR/chrome-linux/chrome
chmod +x $CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver

# Export paths for Chrome and ChromeDriver
export CHROME_BIN="$CHROME_DIR/chrome-linux/chrome"
export CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"
