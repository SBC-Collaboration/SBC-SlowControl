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

10.BKG settings
The reason why we made this so complicated is that our background code(PLC.py or PLC_init.sh) depends on the Qt package. Because the PICO's code, which is our mother code, didn't seperate bkg and GUI code.
So the method they used to communicated between classes was QT thread and QT signal, which is a very easy tool. However, both of them depends on the DISPLAY settings. When we firstly
seperate the BKG and GUI, I didn't know that the BKG code cannot be run in crontab/systemctl with QT thread. And for now, it is much easy to change the way how to run the code instead of chaning the code itself(because the bkg
also communicates with the GUI.) But we definitely will fix this one day...Because Gnome might be not so reliable.
But don't forget one thing: When you add it into crontab/system service, the order launching mysql and the bkg code matters.
Here is how to set BKG codes autorun after the machine reboot
1.You need to put a desktop executive file into ~/.local/share/applications, which I have put it there already, also you can find it in current directory. It is slowcontrol.desktop
This code will be executated by the Gnome after you log into the desktop
2.To enable it is been executated, Menu-> Applications->Accessories->Tweak-> Startup Applications-> add SBCslowcontrol. The purpose of step 1 is to let SBCslowcontrol appear in the application list.
3.TO run the bkg automatically, you also need the pc to auto log in. You can log in via root and grant hep auto login privilige.
4. If you want the background run without terminal, edit the desktop file with setting Terminal=False
5. If you don't want to it run when PC reboot just delete it from the Tweak startup application.

11.Alarm Settings
The alarm csv is saved in /home/hep/.config/sbcconfig/sbc_alarm_config.csv
Everyone can directly edit it in order to change the configuration of alarms. And background code will load it automatically everytime it reruns.
I didn't put it in the same directory as code because I still frequenty push and pull from github on both my pc and slowcontrol machine. I want to avoid
branch conflict as much as possible.





