#!/bin/bash
# This is a script for pruning the old session folders that are sometimes
# left behind by the WebGnomeAPI server.
# We expect to run this from the base project folder

echo "Begin pruning the webgnomeapi session folders..."

days=14  # number of days since the file/folder was modified
base_folder=models/session

num_folders=$(find $base_folder -maxdepth 1 -type d -mtime +$days |wc -l)

if [[ $num_folders -gt 0 ]]
then
    files=$(find $base_folder -maxdepth 1 -type d -mtime +$days)

    for f in $files
    do
        echo "pruning: $f"
        rm -rf $f
    done
else
    echo "no files to prune."
fi
