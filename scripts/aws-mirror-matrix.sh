#!/bin/bash

# !!!! Requires aws cli to be installed and available in $PATH
# !!!! https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html

set -e
set -x

MODEL=${MODEL:="cbofs"}
PATTERN=${PATTERN:="fields"}
CAST=${CAST:=".n"}

# YYYY/MM/DD
if [ -z "${DATEPATTERN+x}" ]; then
	DATEPATTERN="$(date +%Y/%m/%d)/"
else
	DATEPATTERN="$DATEPATTERN/"
fi

FILE_PATH="$DATEPATTERN*$PATTERN$CAST*"

aws s3 sync s3://noaa-nos-ofs-pds/$MODEL $GNOME_S3_BUCKET/$MODEL \
	--no-sign-request \
	--size-only \
	--exclude "*" \
	--include "*netcdf/$FILE_PATH"
