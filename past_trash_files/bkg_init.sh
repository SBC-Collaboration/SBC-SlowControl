#!/bin/bash
#xterm -hold -e "source ~/Downloads/sbc_slowcontrol/SBC-SlowControl/loop.sh > /dev/null 2>&1 &"
#xterm -hold -e "source ~/Downloads/sbc_slowcontrol/SBC-SlowControl/loop.sh ; echo 'h'"
#while true; do
PATH=/home/hep/anaconda3/envs/sbcslowcontrol/bin:/home/hep/anaconda3/condabin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/hep/.local/bin:/home/hep/bin
CONDA_EXE=/home/hep/anaconda3/bin/conda
CONDA_PREFIX_1=/home/hep/anaconda3
PATH=/home/hep/anaconda3/envs/sbcslowcontrol/bin:/home/hep/anaconda3/condabin:/usr/local/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/home/hep/.local/bin:/home/hep/bin
GSETTINGS_SCHEMA_DIR=/home/hep/anaconda3/envs/sbcslowcontrol/share/glib-2.0/schemas
CONDA_PREFIX=/home/hep/anaconda3/envs/sbcslowcontrol
CONDA_PYTHON_EXE=/home/hep/anaconda3/bin/python


#xterm -hold -e "conda init bash;source ~/conda_init.sh ; conda activate sbcslowcontrol; source BKG_init.sh & disown"
export DISPLAY=:0 
xterm -hold -e  "nohup sh PLC_init.sh > /dev/null 2>&1"
