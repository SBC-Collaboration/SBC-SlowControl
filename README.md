# SBC-SlowControl
SBC Slow Control server and related code 
This is a help files to specify some detais on how to operate GUI on sbcslowcontrol machine
0. Tutorial:
   0.a open a terminal on sbcslowonctrol machine. Menu-> Applications -> System Tools -> Xfce Terminal
   0.b activate conda environment.
       "source ~/conda_init.sh"
       "conda activate sbcslowcontrol"
       if you want to see conda env list, run "conda env list"
   0.c cd **_~/Downloads/sbc_slowcontrol/SBC_slowcontrol/slowcontrol_reconstruct
       this is  the code directory_**
   0.d run the background code "source BKG_init.sh"
   0.e add another tab or terminal, activate conda environment again and run "SBC_GUI.py"-this is GUI


1.Python 3.7 is istalled in /usr/src.

2.Python 3.6 as default of python 3, is installed in usr/bin
ANaconda3 is installed in /home/hep/Anaconda3 by default settings.
conda environment is called sbcslowcontrol, type"conda activate sbcslowcontrol"
you can run "conda env list" to list all conda environments. 

3.sudo tar xzf pycharm-*.tar.gz -C /opt/
pycharm directory is in /opt/ by default
/opt/pycharm/bin/sh pycharm.sh to run the pycahrm
or directly run pycharm

4.mysql 
usr: root pwd: SBCr0ck5!
usr:MyseeQ 
usr:slowcontrol 

5.git local directory sbc_slowcontrol\SBC-Slowcontrol
branch main

6.remote repository git@github.com:SBC-Collaboration/SBC-SlowControl.git
alias sbcslowcontrol

7.iptable settings:
INPUT accept localhost SEEQ(131.225.108.49 )and drop other connection
install iptables-services
service iptables save will save the updated settings permanantly.

8.SBC database structure
SBCslowcontrol
tables:
DataStorage
MetaDataStorage


9.BKG settings
background code:
go to $ SBC_reconstruct$
$chmod +x BKG_init.sh$
$crontab -e$ and uncomment the BKG_init.sh part

10.Alarm Settings
The alarm csv is saved in /home/hep/.config/sbcconfig/sbc_alarm_config.csv
Everyone can directly edit it in order to change the configuration of alarms. And background code will load it automatically everytime it reruns.
I didn't put it in the same directory as code because I still frequenty push and pull from github on both my pc and slowcontrol machine. I want to avoid
branch conflict as much as possible.





