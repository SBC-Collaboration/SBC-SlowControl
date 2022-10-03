#!/bin/bash
PATH=/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/hep/.local/bin:/home/hep/bin
source ~/conda_init.sh
source /home/hep/miniforge3/bin/activate sbcslowcontrol
which python
while true; do
cd /home/hep/PycharmProjects/SBC_slowcontrol_test/
#source /home/hep/PycharmProjects/SBC_slowcontrol_test/clear_tcp.sh
#/hep/home/miniforge3/envs/sbcslowcontrol/bin/python /home/hep/PycharmProjects/SBC_slowcontrol_test/PLC.py
source ./clear_tcp.sh
python ./PLC.py
sleep 2
done
echo "quit the loop" > ~/ECHO.txt
