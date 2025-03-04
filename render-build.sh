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

# If API request failed, retry with fallback URL
if [[ -z "$LATEST_STABLE" || "$LATEST_STABLE" == "null" ]]; then
    echo "WARNING: Failed to retrieve latest Chrome version from primary source. Trying fallback..."
    LATEST_STABLE=$(curl -s https://versionhistory.googleapis.com/v1/chrome/platforms/linux/channels/stable/versions | jq -r '.versions[0].version')
fi

# Final validation
if [[ -z "$LATEST_STABLE" || "$LATEST_STABLE" == "null" ]]; then
    echo "ERROR: Failed to retrieve the latest Chromium version!"
    exit 1
fi

echo "Latest stable Chrome version: $LATEST_STABLE"

# Fetch Chromium download URL
CHROMIUM_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json | jq -r ".milestones | to_entries | max_by(.key | tonumber) | .value.downloads.chrome[] | select(.platform == \"linux64\") | .url")

# Ensure URL is valid
if [[ -z "$CHROMIUM_URL" || "$CHROMIUM_URL" == "null" ]]; then
    echo "ERROR: Failed to retrieve Chromium download URL!"
    exit 1
fi

echo "Downloading Chromium from: $CHROMIUM_URL"
curl -# -o chromium.zip "$CHROMIUM_URL"
unzip chromium.zip
export CHROME_BIN="$CHROMIUM_DIR/chrome-linux64/chrome"

# Validate Chromium installation
if [ -f "$CHROME_BIN" ]; then
    echo "Chromium installed successfully at $CHROME_BIN"
else
    echo "ERROR: Chromium installation failed!"
    exit 1
fi

# --- Install the Correct ChromeDriver ---
cd $CHROMEDRIVER_DIR

# Fetch ChromeDriver download URL
CHROMEDRIVER_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json | jq -r ".milestones | to_entries | max_by(.key | tonumber) | .value.downloads.chromedriver[] | select(.platform == \"linux64\") | .url")

# Ensure URL is valid
if [[ -z "$CHROMEDRIVER_URL" || "$CHROMEDRIVER_URL" == "null" ]]; then
    echo "ERROR: Failed to retrieve ChromeDriver download URL!"
    exit 1
fi

echo "Downloading ChromeDriver from: $CHROMEDRIVER_URL"
curl -# -o chromedriver.zip "$CHROMEDRIVER_URL"

# Verify the download was successful
if [ ! -s "chromedriver.zip" ]; then
    echo "ERROR: ChromeDriver download failed or is empty!"
    exit 1
fi

unzip chromedriver.zip -d $CHROMEDRIVER_DIR
export CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

# Validate ChromeDriver installation
if [ -f "$CHROMEDRIVER_BIN" ]; then
    echo "ChromeDriver installed successfully at $CHROMEDRIVER_BIN"
else
    echo "ERROR: ChromeDriver installation failed!"
    exit 1
fi

