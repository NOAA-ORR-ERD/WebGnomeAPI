#!/bin/bash -x
#
# Handle the startup using the environment variable that sets up the 
# deployment scenario

exec supervisord --configuration /config_files/supervisord.conf -n
