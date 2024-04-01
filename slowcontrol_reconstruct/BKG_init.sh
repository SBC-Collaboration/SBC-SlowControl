#!/bin/bash

PATH=/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/hep/.local/bin:/home/hep/bin
if [ -n "$(xrandr --listactivemonitors | grep -i connected)" ]; then
    # Launch the application if a display is connected
    source ~/conda_init.sh
    source /home/hep/miniforge3/bin/activate sbcslowcontrol
    which python
    while true; do
    cd /home/hep/PycharmProjects/SBC_slowcontrol_test/slowcontrol_reconstruct
    python ./SBC_background.py
    sleep 2
    done
    echo "quit the loop" > ~/ECHO.txt
fi

