#!/bin/bash
PATH=/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/hep/.local/bin:/home/hep/bin
source ~/conda_init.sh 
source /home/hep/anaconda3/bin/activate sbcslowcontrol 
which python
while true; do
source /home/hep/Downloads/sbc_slowcontrol/SBC-SlowControl/clear_tcp.sh
python /home/hep/Downloads/sbc_slowcontrol/SBC-SlowControl/PLC.py
sleep 2
done
echo "quit the loop"
