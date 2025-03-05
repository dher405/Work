#!/bin/bash

set -e  # Exit on error
set -x  # Enable debug logging

# Define paths
CHROMIUM_DIR="/opt/render/chromium"
CHROMEDRIVER_DIR="/opt/render/chromedriver"
CHROME_BIN="$CHROMIUM_DIR/chrome-linux64/chrome"
CHROMEDRIVER_BIN="$CHROMEDRIVER_DIR/chromedriver-linux64/chromedriver"

# Fetch the latest stable Chrome version with fallback
get_latest_stable_version() {
    local version=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json | jq -r '.milestones | to_entries | max_by(.key | tonumber) | .value.chromeVersion')
    if [[ -z "$version" || "$version" == "null" ]]; then
        echo "WARNING: Failed to retrieve latest Chrome version from primary source. Trying fallback..."
        curl -s https://versionhistory.googleapis.com/v1/chrome/platforms/linux/channels/stable/versions | jq -r '.versions[0].version'
    else
        echo "$version"
    fi
}

LATEST_STABLE=$(get_latest_stable_version)

if [[ -z "$LATEST_STABLE" || "$LATEST_STABLE" == "null" ]]; then
    echo "ERROR: Failed to retrieve the latest Chromium version!"
    exit 1
fi

echo "Latest stable Chrome version: $LATEST_STABLE"

# Fetch Chromium download URL
CHROMIUM_URL=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/latest-versions-per-milestone-with-downloads.json | jq -r '.milestones | to_entries | max_by(.key | tonumber) | .value.downloads.chrome| select(.platform == "linux64") | .url')

if [[ -z "$CHROMIUM_URL" || "$CHROMIUM_URL" == "null" ]]; then
    echo "ERROR: Failed to retrieve Chromium download URL!"
    exit 1
fi

echo "Downloading Chromium from: $CHROMIUM_URL"
# ... rest of the script ...
