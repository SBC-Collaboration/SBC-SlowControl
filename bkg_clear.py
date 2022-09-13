import daemon, os, sys, psutil
PORT_N=5555
PROCESS_NAME = "TCP"
pid = None


def clear_tcp():
    for proc in psutil.process_iter():
        for conns in proc.connections(kind='tcp'):
            if conns.laddr.port ==PORT_N:
        # if PROCESS_NAME in proc.name() &:
                pid = proc.pid
                p=psutil.Process(pid)
                p.terminate()
                print("\n",pid, "KILLED")


def clear_tcp_scripts():
    os.system("source /home/hep/PycharmProjects/pythonProject/SBC-SlowControl/clear_tcp.sh")

if __nammysqle__ == "__main__":
    clear_tcp_scripts()
    # clear_tcp()