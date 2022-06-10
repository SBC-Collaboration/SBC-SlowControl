import daemon
import time

def do_something():
    i = 0
    while i<=2:
        with open("/home/hep/Downloads/current_time.txt", "w") as f:
        # with open("~/Downloads//current_time.txt", "w") as f:
            f.write("The time is now " + time.ctime())
        # print(1)
        time.sleep(5)
        i += 1

def run():
    # do_something()
    try:
        # with daemon.DaemonContext(working_directory="/home/hep/Downloads/"):
        with daemon.DaemonContext():
            do_something()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    run()