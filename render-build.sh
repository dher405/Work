#!/usr/bin/env bash

echo "Installing Chromium and matching ChromeDriver..."

# Define installation directories
CHROMIUM_DIR="$HOME/chromium"
CHROMEDRIVER_DIR="$HOME/chromedriver"

mkdir -p $CHROMIUM_DIR
mkdir -p $CHROMEDRIVER_DIR
cd $CHROMIUM_DIR

# Get the latest Chromium revision number
LASTCHANGE_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2FLAST_CHANGE?alt=media"
REVISION=$(curl -s -S $LASTCHANGE_URL)

echo "Latest Chromium revision is $REVISION"

# Download Chromium
ZIP_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F$REVISION%2Fchrome-linux.zip?alt=media"
ZIP_FILE="chromium-$REVISION.zip"

echo "Fetching Chromium from: $ZIP_URL"

rm -rf $REVISION
mkdir $REVISION
pushd $REVISION

curl -# -o $ZIP_FILE $ZIP_URL
unzip $ZIP_FILE
popd

rm -f ./latest
ln -s $REVISION/chrome-linux/ ./latest

export CHROME_BIN="$CHROMIUM_DIR/latest/chrome"

# Validate Chromium installation
if [ -f "$CHROME_BIN" ]; then
    echo "Chromium installed successfully at $CHROME_BIN"
else
    echo "ERROR: Chromium installation failed!"
    exit 1
fi

# --- Install ChromeDriver Matching Chromium Version ---
cd $CHROMEDRIVER_DIR

# Fetch ChromeDriver matching the Chromium version
CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/$REVISION/linux64/chromedriver-linux64.zip"
CHROMEDRIVER_ZIP="chromedriver-$REVISION.zip"

echo "Downloading ChromeDriver from: $CHROMEDRIVER_URL"

curl -# -o $CHROMEDRIVER_ZIP $CHROMEDRIVER_URL
unzip $CHROMEDRIVER_ZIP

export CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

# Validate ChromeDriver installation
if [ -f "$CHROMEDRIVER_BIN" ]; then
    echo "ChromeDriver installed successfully at $CHROMEDRIVER_BIN"
else
    echo "ERROR: ChromeDriver installation failed!"
    exit 1
fi


