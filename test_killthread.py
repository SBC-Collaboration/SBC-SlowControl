

import struct, time, zmq, sys, pickle
import numpy as np
from PySide2 import QtWidgets, QtCore, QtGui

from email.mime.text import MIMEText
from email.header import Header
from smtplib import SMTP_SSL
import requests
import os

import threading
import sys
import traceback
import os
import signal
import time
from PySide2 import QtCore,QtWidgets

# delete random number package when you read real data from PLC
import random
from pymodbus.client.sync import ModbusTcpClient




# class PLC:
#     def __init__(self):
#         super().__init__()
#         print('class0')
#
#     def ReadAll(self):
#         print('PLC')


class myclass(QtCore.QObject):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.string = '(*&*^$(*)_)&^'
    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:
            print(self.string[0])
            self.string = self.string[1:]
            time.sleep(1)

    @QtCore.Slot()
    def stop(self):
        self.Running = False

# Class to update myseeq database
class myclass1(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.string = 'small'

    @QtCore.Slot()
    def run(self):

        self.Running = True
        while self.Running:
            print(self.string[0])
            self.string = self.string[1:]
            time.sleep(1)

    @QtCore.Slot()
    def stop(self):
        self.Running = False

# Class to read PLC value every 2 sec
class myclass2(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.string = 'LARGE'

    @QtCore.Slot()
    def run(self):

        self.Running = True

        while self.Running:
            print(self.string[0])
            self.string = self.string[1:]
            time.sleep(1)



    @QtCore.Slot()
    def stop(self):
        self.Running = False





class Update(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        App.aboutToQuit.connect(self.StopUpdater)
        self.StartUpdater()

    def StartUpdater(self):


        # Read PLC value on another thread


        time.sleep(2)

        self.Mythread = QtCore.QThread()
        self.Myclass = myclass()
        self.Myclass.moveToThread(self.Mythread)
        self.Mythread.started.connect(self.Myclass.run())
        self.Mythread.start()




        # Stop all updater threads
    @QtCore.Slot()
    def StopUpdater(self):
        self.UpPLC.stop()
        self.PLCUpdateThread.quit()
        self.PLCUpdateThread.wait()

        self.UpDatabase.stop()
        self.DataUpdateThread.quit()
        self.DataUpdateThread.wait()

        self.Myclass.stop()
        self.Mythread.quit()
        self.Mythread.wait()



def sendKillSignal(etype, value, tb):
    print('KILL ALL')
    traceback.print_exception(etype, value, tb)
    os.kill(os.getpid(), signal.SIGKILL)


original_init = QtCore.QThread.__init__
def patched_init(self, *args, **kwargs):
    print("thread init'ed")
    original_init(self, *args, **kwargs)
    original_run = self.run
    def patched_run(*args, **kw):
        try:
            original_run(*args, **kw)
        except:
            sys.excepthook(*sys.exc_info())
    self.run = patched_run



def install():
    sys.excepthook = sendKillSignal
    QtCore.QThread.__init__ = patched_init

install()





if __name__ == "__main__":
    # msg_mana=message_manager()
    # msg_mana.tencent_alarm("this is a test message")

    install()

    App = QtWidgets.QApplication(sys.argv)
    Update=Update()


    # PLC=PLC()
    # PLC.ReadAll()

    sys.exit(App.exec_())


