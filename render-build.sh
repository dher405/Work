#!/usr/bin/env bash

echo "Installing Chromium..."

# Define installation directory
CHROMIUM_DIR="$HOME/chromium"
mkdir -p $CHROMIUM_DIR
cd $CHROMIUM_DIR

# Get the latest Chromium revision number
LASTCHANGE_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2FLAST_CHANGE?alt=media"
REVISION=$(curl -s -S $LASTCHANGE_URL)

echo "Latest Chromium revision is $REVISION"

# If the latest version is already installed, exit early
if [ -d "$REVISION" ]; then
  echo "Already have the latest version installed."
  exit 0
fi

ZIP_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F$REVISION%2Fchrome-linux.zip?alt=media"
ZIP_FILE="${REVISION}-chrome-linux.zip"

echo "Fetching Chromium from: $ZIP_URL"

# Remove old versions and create a fresh directory
rm -rf $REVISION
mkdir $REVISION
pushd $REVISION

# Download and extract Chromium
curl -# -o $ZIP_FILE $ZIP_URL
echo "Unzipping Chromium..."
unzip $ZIP_FILE
popd

# Create a symlink to the latest version
rm -f ./latest
ln -s $REVISION/chrome-linux/ ./latest

# Set the correct Chromium binary path
export CHROME_BIN="$CHROMIUM_DIR/latest/chrome"

# Validate Chromium installation
if [ -f "$CHROME_BIN" ]; then
    echo "Chromium installed successfully at $CHROME_BIN"
else
    echo "ERROR: Chromium installation failed!"
    exit 1
fi

