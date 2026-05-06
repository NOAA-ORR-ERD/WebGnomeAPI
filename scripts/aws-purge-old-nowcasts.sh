#!/bin/bash

OLDERTHAN=${OLDERTHAN:-'14'}

curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d "purging old nowcasts"

unamestr=$(uname)
if [[ "$unamestr" == 'Darwin' ]]; then
	find="/usr/local/opt/findutils/libexec/gnubin/find"
else
	find=$(which find)
fi

NOWCAST_SIZE=$($find /archive -regextype posix-extended -regex '.*.n[0-9]{3}.*' -exec stat -c "%s" {} + | awk '{s+=$1} END {print s}')
if [[ "$NOWCAST_SIZE" ]]; then
  echo 'NOWCAST SIZE BEFORE:' $(($NOWCAST_SIZE / 1024 / 1024 / 1024))'gb'
  curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d "NOWCAST SIZE BEFORE: $(($NOWCAST_SIZE / 1024 / 1024 / 1024))gb"
else
  echo 'NOWCAST SIZE BEFORE: 0gb'
  curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d 'NOWCAST SIZE BEFORE: 0gb'
fi

# remove forecast files older than 14 days
$find /archive -regextype posix-extended -regex '.*.n[0-9]{3}.*' -mtime +$OLDERTHAN -exec rm {} \;

NOWCAST_SIZE=$($find / -regextype posix-extended -regex '.*.n[0-9]{3}.*' -exec stat -c "%s" {} + | awk '{s+=$1} END {print s}')

if [[ "$NOWCAST_SIZE" ]]; then
  echo 'NOWCAST SIZE AFTER:' $(($NOWCAST_SIZE / 1024 / 1024 / 1024))'gb'
  curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d "NOWCAST SIZE AFTER: $(($NOWCAST_SIZE / 1024 / 1024 / 1024))gb"
else
  echo 'NOWCAST SIZE AFTER: 0gb'
  curl -X PUT https://ntfy.naomiconnolly.dev/ocean-archive -d 'NOWCAST SIZE AFTER: 0gb'
fi
