#!/bin/bash

OLDERTHAN=${OLDERTHAN:-'1400'}

curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d "purging old forecasts"

unamestr=$(uname)
if [[ "$unamestr" == 'Darwin' ]]; then
	find="/usr/local/opt/findutils/libexec/gnubin/find"
else
	find=$(which find)
fi

FORECAST_SIZE=$($find /archive -regextype posix-extended -regex '.*.f[0-9]{3}.*' -exec stat -c "%s" {} + | awk '{s+=$1} END {print s}')
if [[ "$FORECAST_SIZE" ]]; then
  echo 'FORECAST SIZE BEFORE:' $(($FORECAST_SIZE / 1024 / 1024 / 1024))'gb'
  curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d "FORECAST SIZE BEFORE: $(($FORECAST_SIZE / 1024 / 1024 / 1024))gb"
else
  echo 'FORECAST TOTAL SIZE BEFORE CLEANUP: 0gb'
  curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d 'FORECAST TOTAL SIZE BEFORE CLEANUP: 0gb'
fi

# remove forecast files older than a day
$find /archive -regextype posix-extended -regex '.*.f[0-9]{3}.*' -mmin +$OLDERTHAN -exec rm {} \;

FORECAST_SIZE=$($find /archive -regextype posix-extended -regex '.*.f[0-9]{3}.*' -exec stat -c "%s" {} + | awk '{s+=$1} END {print s}')
if [[ "$FORECAST_SIZE" ]]; then
  echo 'FORECAST TOTAL SIZE AFTER CLEANUP:' $(($FORECAST_SIZE / 1024 / 1024 / 1024))'gb'
  curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d "FORECAST TOTAL SIZE AFTER CLEANUP: $(($FORECAST_SIZE / 1024 / 1024 / 1024))gb"
else
  echo 'FORECAST TOTAL SIZE AFTER CLEANUP: 0gb'
  curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d 'FORECAST TOTAL SIZE AFTER CLEANUP: 0gb'
fi
