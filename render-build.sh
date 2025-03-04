#!/usr/bin/env bash

echo "Installing Chrome..."

# Download and extract Chrome
CHROME_VERSION="google-chrome-stable_current_amd64.deb"
wget https://dl.google.com/linux/direct/$CHROME_VERSION
dpkg -x $CHROME_VERSION $HOME/chrome
mv $HOME/chrome/opt/google/chrome $HOME/chrome-bin
rm $CHROME_VERSION

# Set Chrome binary path
export CHROME_BIN="$HOME/chrome-bin/google-chrome"

echo "Chrome installed at $CHROME_BIN"
