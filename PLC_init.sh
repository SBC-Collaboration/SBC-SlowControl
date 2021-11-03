#!/bin/bash
PATH=/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/hep/.local/bin:/home/hep/bin
while true; do
source ~/Downloads/sbc_slowcontrol/SBC_slowcontrol/clear_tcp.sh
python ~/Downloads/sbc_slowcontrol/SBC_slowcontrol/PLC.py
sleep 2
done
echo "quit the loop"
