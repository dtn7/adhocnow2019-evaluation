#!/usr/bin/env bash

core-daemon &
sleep 1
core-gui

# Crashes the container
ps x | awk {'{print $1}'} | awk 'NR > 1' | xargs kill
