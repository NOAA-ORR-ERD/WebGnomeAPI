#!/bin/bash

# !!!! Requires aws cli to be installed and available in $PATH
# !!!! https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

# Acquire a Redis distributed lock before proceeding. Releases on exit (including signals).
LOCK_KEY="aws-mirror-to-efs:lock"
LOCK_TTL=14400  # 4 hours in seconds
export LOCK_KEY LOCK_TTL
python3 "$(dirname "$0")/acquire_redis_lock.py"

LOCK_EXIT=$?
if [ $LOCK_EXIT -eq 2 ]; then
    exit 0
elif [ $LOCK_EXIT -ne 0 ]; then
    echo "ERROR: Failed to acquire Redis lock (exit $LOCK_EXIT)" >&2
    exit 1
fi

LOCK_FILE="/tmp/.redis_lock_$$"
export LOCK_VALUE=$(cat "$LOCK_FILE")
rm -f "$LOCK_FILE"

release_lock() {
    python3 "$(dirname "$0")/release_redis_lock.py"
}

trap 'release_lock' EXIT



set -e
set -x

curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d "Sync operation starting..."

# Matrix of models to sync. Format: "MODEL PATTERN CAST"
# PATTERN defaults to "fields"; CAST ".n" = nowcast, ".f" = forecast
SYNC_MATRIX=(
    # --- Nowcasts ---
    "wcofs   2ds    .n"
    "sscofs  fields .n"
    "ngofs2  2ds    .n"
    "cbofs   fields .n"
    "tbofs   fields .n"
    "dbofs   fields .n"
    "gomofs  2ds    .n"
    "ciofs   fields .n"
    "sfbofs  fields .n"
    "leofs   fields .n"
    "lmhofs  fields .n"
    "loofs   fields .n"
    "lsofs   fields .n"
    # --- Forecasts ---
    "wcofs   2ds    .f"
    "sscofs  fields .f"
    "ngofs2  2ds    .f"
    "cbofs   fields .f"
    "tbofs   fields .f"
    "dbofs   fields .f"
    "gomofs  2ds    .f"
    "ciofs   fields .f"
    "sfbofs  fields .f"
    "leofs   fields .f"
    "lmhofs  fields .f"
    "loofs   fields .f"
    "lsofs   fields .f"
)

SCRIPT_DIR="$(dirname "$0")"

for entry in "${SYNC_MATRIX[@]}"; do
    (
        read -r MODEL PATTERN CAST <<< "$entry"
        echo "=========================================================="
        echo "Syncing MODEL=$MODEL PATTERN=$PATTERN CAST=$CAST"
        echo "=========================================================="
        curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d "`hostname` Syncing MODEL=$MODEL PATTERN=$PATTERN CAST=$CAST"
        MODEL="$MODEL" PATTERN="$PATTERN" CAST="$CAST" bash "$SCRIPT_DIR/aws-mirror-matrix.sh" "/archive"
    ) &
done

wait

bash "$SCRIPT_DIR/aws-purge-old-forcasts.sh"
bash "$SCRIPT_DIR/aws-purge-old-nowcasts.sh"