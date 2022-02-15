This is a help files to specify some detais on how to operate GUI on sbcslowcontrol machine
0. Tutorial:
   0.a open a terminal on sbcslowonctrol machine. Menu-> Applications -> System Tools -> Xfce Terminal
   0.b activate conda environment.
       "source ~/conda_init.sh"
       "conda activate sbcslowcontrol"
       if you want to see conda env list, run "conda env list"
   0.c cd ~/Downloads/sbc_slowcontrol/SBC_slowcontrol 
       this is is the code directory
   0.d run the backgroudn code "source PLD_init.sh"
   0.e add another tab or terminal, activate conda environment again and run "python SlowDAQ_SBC_v2.py"-this is GUI
   0.f if you quit the program or the program crashes by accident, you will find you can not rerun the code because some tcp error
       "source clear_tcp.sh"
	to clear corrupted files caused by tcp connection


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

9.PLC code:
If the Qthread error prompts when you run PLC.py: zmq.error.ZMQError: Address already in use
QThread: Destroyed while thread is still running
please destroy the thread by runnig the following commands:
sudo netstat -ltnp |grep python and find the pid for port 5555
then:
kill -9 <pid>

PS.now you could directly source clear_tcp.sh to clean the corrupted files.





