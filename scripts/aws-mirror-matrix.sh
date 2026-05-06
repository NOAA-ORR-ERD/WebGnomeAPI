#!/bin/bash

# !!!! Requires aws cli to be installed and available in $PATH
# !!!! https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

set -e
set -x

LOCAL_DIR="${1:?Usage: aws-mirror-matrix.sh <local-destination-dir>}"

MODEL=${MODEL:="cbofs"}
PATTERN=${PATTERN:="fields"}
CAST=${CAST:=".n"}

# NEW: Configure how many days back to sync if a specific date isn't provided.
DAYS_BACK=${DAYS_BACK:=1}

# Helper function to calculate past dates.
# This checks which version of `date` is installed to support both Linux (GNU) and macOS (BSD).
get_past_date() {
    local days_ago=$1
    if date -d "today" >/dev/null 2>&1; then
        # GNU/Linux standard
        date -d "$days_ago days ago" +%Y/%m/%d
    else
        # BSD/macOS standard
        date -v-"${days_ago}"d +%Y/%m/%d
    fi
}

# Determine which dates to process
if [ -n "${DATEPATTERN+x}" ]; then
    # If the user provides a specific DATEPATTERN, we only run it for that exact pattern.
    DATE_LIST=("$DATEPATTERN")
else
    # Otherwise, populate an array with the last $DAYS_BACK days.
    DATE_LIST=()
    for (( i=0; i<$DAYS_BACK; i++ )); do
        DATE_LIST+=("$(get_past_date $i)")
    done
fi

INCLUDE_PARAMS=()
for CURRENT_DATE in "${DATE_LIST[@]}"; do
    DATE_PREFIX="$CURRENT_DATE/"
    FILE_PATH="$DATE_PREFIX*$PATTERN$CAST*"
    INCLUDE_PARAMS+=(--include "*netcdf/$FILE_PATH")
done

aws s3 sync s3://noaa-nos-ofs-pds/$MODEL "$LOCAL_DIR/$MODEL" \
    --no-sign-request \
    --size-only \
    --exclude "*" \
    "${INCLUDE_PARAMS[@]}"