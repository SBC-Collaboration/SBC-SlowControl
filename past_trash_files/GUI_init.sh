#!/bin/bash
PATH=/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/hep/.local/bin:/home/hep/bin
source ~/conda_init.sh 
source /home/hep/anaconda3/bin/activate sbcslowcontrol 
which python
python /home/hep/Downloads/sbc_slowcontrol/SBC-SlowControl/SlowDAQ_SBC_v2.py
echo "quit the loop" > ~/echo.txt
