#!/usr/bin/env bash

echo "Installing Chrome..."

# Define the installation directory
CHROME_DIR="$HOME/chrome"
mkdir -p $CHROME_DIR

# Download and extract the latest stable Chrome binary
wget -qO- https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb > $CHROME_DIR/chrome.deb

# Extract Chrome manually without sudo
dpkg-deb -x $CHROME_DIR/chrome.deb $CHROME_DIR

# Set the correct Chrome binary path
export CHROME_BIN="$CHROME_DIR/opt/google/chrome/google-chrome"

echo "Chrome installed successfully at $CHROME_BIN"
