#!/usr/bin/env bash

echo "Installing Chrome..."

# Define installation directory
CHROME_DIR="$HOME/chrome"
mkdir -p $CHROME_DIR
cd $CHROME_DIR

# Download and extract the latest Chrome binary for Linux
wget -qO- https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_current_amd64.tar.gz | tar -xz

# Locate and set Chrome binary path
export CHROME_BIN=$(find $CHROME_DIR -name "google-chrome" | head -n 1)

echo "Chrome installed successfully at $CHROME_BIN"
