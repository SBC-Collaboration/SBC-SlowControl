#!/bin/bash
#PATH=/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/hep/.local/bin:/home/hep/bin
#source ~/conda_init.sh
#source /home/hep/miniconda3/bin/activate sbcslowcontrol
#which python
while true; do
source ./clear_tcp.sh
python /home/hep/Downloads/sbc_slowcontrol/SBC-SlowControl/PLC.py
python ./PLC.py
sleep 2
done
echo "quit the loop" > ~/ECHO.txt
