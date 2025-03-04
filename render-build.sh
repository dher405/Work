#!/usr/bin/env bash

echo "Installing Chromium..."

# Define installation directory
CHROMIUM_DIR="$HOME/chromium"
mkdir -p $CHROMIUM_DIR

# Install Chromium via apt (without sudo)
apt-get update && apt-get install -y chromium-browser

# Set the correct Chromium binary path
export CHROME_BIN="/usr/bin/chromium-browser"

# Validate Chromium installation
if [ -f "$CHROME_BIN" ]; then
    echo "Chromium installed successfully at $CHROME_BIN"
else
    echo "ERROR: Chromium installation failed!"
    exit 1
fi
