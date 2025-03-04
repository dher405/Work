#!/usr/bin/env bash

echo "Installing Chrome..."

# Set the Chrome version (latest stable)
CHROME_VERSION="stable"

# Define the installation directory
CHROME_DIR="$HOME/chrome"
mkdir -p $CHROME_DIR

# Download the Chrome binary from a stable source
wget -O $CHROME_DIR/chrome-linux.zip "https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-$CHROME_VERSION/google-chrome-$CHROME_VERSION_current_amd64.deb"

# Extract Chrome without requiring sudo
unzip $CHROME_DIR/chrome-linux.zip -d $CHROME_DIR
export CHROME_BIN="$CHROME_DIR/chrome-linux/google-chrome"

echo "Chrome installed successfully at $CHROME_BIN"
