#!/usr/bin/env bash

echo "Installing Chromium and matching ChromeDriver..."

# Define installation directories
CHROMIUM_DIR="$HOME/chromium"
CHROMEDRIVER_DIR="$HOME/chromedriver"

mkdir -p $CHROMIUM_DIR
mkdir -p $CHROMEDRIVER_DIR
cd $CHROMIUM_DIR

# Fetch the latest Chromium revision from Google's API
LASTCHANGE_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2FLAST_CHANGE?alt=media"
REVISION=$(curl -s -S $LASTCHANGE_URL)

echo "Latest Chromium revision is: $REVISION"

# Ensure we got a valid revision number
if [[ -z "$REVISION" || "$REVISION" == "null" ]]; then
    echo "ERROR: Failed to retrieve the latest Chromium revision!"
    exit 1
fi

# Define Chromium download URL
ZIP_URL="https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F$REVISION%2Fchrome-linux.zip?alt=media"
ZIP_FILE="${REVISION}-chrome-linux.zip"

echo "Fetching Chromium from: $ZIP_URL"

rm -rf $REVISION
mkdir $REVISION
pushd $REVISION

curl -# -o $ZIP_FILE "$ZIP_URL"

# Verify if the download was successful
if [ ! -s "$ZIP_FILE" ]; then
    echo "ERROR: Chromium download failed or is empty!"
    exit 1
fi

echo "Unzipping Chromium..."
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

# --- Install the Correct ChromeDriver ---
cd $CHROMEDRIVER_DIR

# Fetch the matching ChromeDriver version
CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/$REVISION/linux64/chromedriver-linux64.zip"
CHROMEDRIVER_ZIP="chromedriver-$REVISION.zip"

echo "Downloading ChromeDriver from: $CHROMEDRIVER_URL"

curl -# -o $CHROMEDRIVER_ZIP "$CHROMEDRIVER_URL"

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




