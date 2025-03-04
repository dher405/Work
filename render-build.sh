#!/usr/bin/env bash

echo "Installing Chromium and matching ChromeDriver..."

# Define installation directories
CHROMIUM_DIR="$HOME/chromium"
CHROMEDRIVER_DIR="$HOME/chromedriver"

mkdir -p $CHROMIUM_DIR
mkdir -p $CHROMEDRIVER_DIR
cd $CHROMIUM_DIR

# Fetch the latest stable Chrome version
LATEST_STABLE=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json | jq -r '.milestones | to_entries | max_by(.key | tonumber) | .value.chromeVersion')

echo "Latest stable Chrome version: $LATEST_STABLE"

# Download Chromium
ZIP_URL="https://storage.googleapis.com/chrome-for-testing-public/$LATEST_STABLE/linux64/chrome-linux.zip"
ZIP_FILE="chromium-$LATEST_STABLE.zip"

echo "Fetching Chromium from: $ZIP_URL"

rm -rf $LATEST_STABLE
mkdir $LATEST_STABLE
pushd $LATEST_STABLE

curl -# -o $ZIP_FILE $ZIP_URL
unzip $ZIP_FILE
popd

rm -f ./latest
ln -s $LATEST_STABLE/chrome-linux/ ./latest

export CHROME_BIN="$CHROMIUM_DIR/latest/chrome"

# Validate Chromium installation
if [ -f "$CHROME_BIN" ]; then
    echo "Chromium installed successfully at $CHROME_BIN"
else
    echo "ERROR: Chromium installation failed!"
    exit 1
fi

# --- Install the Correct ChromeDriver ---
cd $CHROMEDRIVER_DIR

# Fetch the matching ChromeDriver version
CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/$LATEST_STABLE/linux64/chromedriver-linux64.zip"
CHROMEDRIVER_ZIP="chromedriver-$LATEST_STABLE.zip"

echo "Downloading ChromeDriver from: $CHROMEDRIVER_URL"

curl -# -o $CHROMEDRIVER_ZIP $CHROMEDRIVER_URL

# Verify the download was successful
if [ ! -s "$CHROMEDRIVER_ZIP" ]; then
    echo "ERROR: ChromeDriver download failed or is empty!"
    exit 1
fi

# Extract ChromeDriver
unzip $CHROMEDRIVER_ZIP -d $CHROMEDRIVER_DIR

export CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

# Validate ChromeDriver installation
if [ -f "$CHROMEDRIVER_BIN" ]; then
    echo "ChromeDriver installed successfully at $CHROMEDRIVER_BIN"
else
    echo "ERROR: ChromeDriver installation failed!"
    exit 1
fi



