#!/usr/bin/env bash

echo "Installing Chrome..."

# Create a directory for Chrome
mkdir -p $HOME/chrome
cd $HOME/chrome

# Download the latest Chrome binary
wget -qO- https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb > chrome.deb

# Extract Chrome without sudo
ar x chrome.deb
tar -xvf data.tar.xz

# Move Chrome binary to a usable directory
mv opt/google/chrome $HOME/chrome-bin
export CHROME_BIN="$HOME/chrome-bin/google-chrome"

echo "Chrome installed successfully at $CHROME_BIN"
