#!/bin/bash
#xterm -hold -e "source ~/Downloads/sbc_slowcontrol/SBC-SlowControl/loop.sh > /dev/null 2>&1 &"
#xterm -hold -e "source ~/Downloads/sbc_slowcontrol/SBC-SlowControl/loop.sh ; echo 'h'"
#while true; do
PATH=/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/hep/.local/bin:/home/hep/bin

xterm -hold -e "source ~/conda_init.sh ; conda activate sbcslowcontrol; source PLC_init.sh & disown"


