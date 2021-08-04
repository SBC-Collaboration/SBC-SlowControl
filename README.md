# SBC-SlowControl
SBC Slow Control server and related code
1.TCP conection:
if you force the PLC.py code to stop i.e. ctrl+Z, the tcp connection won't be closed and the port is still be occupied. Please source the clear_tcp.sh before you rerun the PLC.py
