#!/bin/bash

dir='/Volumes/macOS Base System/usr/share/firmware/wifi'
find "$dir" -type f -print0 | xargs -P10 -0 -I{} -n1 ./searchb.py "{}" ~/Downloads/inflated | cut -c "$(echo "$dir" | wc -c | awk '{print $1+1}')-"
