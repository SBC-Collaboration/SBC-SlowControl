import daemon, os, sys, psutil
import time
PORT_N=5555
PROCESS_NAME = "TCP"
pid = None
from PLC import *

def PLC_loop():

    while True:
        try:
            clear_tcp()
            PLC_body()
        except:
            time.sleep(5)
        time.sleep(5)

def run():
    with daemon.DaemonContext():
        PLC_loop()
def clear_tcp():
    for proc in psutil.process_iter():
        for conns in proc.connections(kind='tcp'):
            if conns.laddr.port ==PORT_N:
        # if PROCESS_NAME in proc.name() &:
                pid = proc.pid
                p=psutil.Process(pid)
                p.terminate()
                print(pid, "KILLED")
def PLC_body():
    App = QtWidgets.QApplication(sys.argv)
    Update = Update()
    sys.exit(App.exec_())


if __name__ == "__main__":
    run()