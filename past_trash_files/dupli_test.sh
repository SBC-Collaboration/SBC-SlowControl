#!/bin/bash

# Check if a physical display is connected
if [ -n "$(xrandr --listactivemonitors | grep -i connected)" ]; then
    # Launch the application if a display is connected
    echo "Hello, World!"
fi