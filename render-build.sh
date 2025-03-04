#!/usr/bin/env bash

echo "Installing Chrome..."

# Define the installation directory
CHROME_DIR="$HOME/chrome"
mkdir -p $CHROME_DIR
cd $CHROME_DIR

# Correct download URL for latest Google Chrome
wget -q -O $CHROME_DIR/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# Verify the download
if [ ! -f "$CHROME_DIR/chrome.deb" ]; then
    echo "ERROR: Chrome download failed!"
    exit 1
fi

# Extract Chrome manually (without sudo)
dpkg-deb -x $CHROME_DIR/chrome.deb $CHROME_DIR

# Verify the extraction
if [ ! -d "$CHROME_DIR/opt/google/chrome" ]; then
    echo "ERROR: Chrome extraction failed!"
    exit 1
fi

# Set the correct Chrome binary path
export CHROME_BIN="$CHROME_DIR/opt/google/chrome/google-chrome"

# Validate Chrome binary exists
if [ -f "$CHROME_BIN" ]; then
    echo "Chrome installed successfully at $CHROME_BIN"
else
    echo "ERROR: Chrome installation failed!"
    exit 1
fi

