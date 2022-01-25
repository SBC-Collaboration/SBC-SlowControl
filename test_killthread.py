"""
Class PLC is used to read/write via modbus to the temperature PLC

To read the variable, just call the ReadAll() method
To write to a variable, call the proper setXXX() method

By: Mathieu Laurin

v1.0 Initial code 25/11/19 ML
v1.1 Initialize values, flag when values are updated more modbus variables 04/03/20 ML
"""

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


#output address to attribute function in FP ()
def FPADS_OUT_AT(outaddress):
    # 1e5 digit
    e5 = outaddress // 10000
    e4 = (outaddress % 10000) // 1000
    e3 = (outaddress % 1000) // 100
    e2 = (outaddress % 100) // 10
    e1 = (outaddress % 10) // 1
    new_e5 = e5-2
    new_e4 = e4
    new_e321=(e3*100+e2*10+e1)*4
    new_address=new_e5*10000+new_e4*1000+new_e321
    print(e5,e4,e3,e2,e1)
    print(new_address)
    return new_address


class PLC:
    def __init__(self):
        super().__init__()
        print('class0')

    def ReadAll(self):
        print('PLC')

# Class to update myseeq database
class UpdateDataBase(QtCore.QObject):
    def __init__(self, PLC, parent=None):
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
class UpdatePLC(QtCore.QObject):
    def __init__(self, PLC, parent=None):
        super().__init__(parent)

        self.string = 'THISISALARGEMESSAGE'

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
        self.PLC = PLC()

        # Read PLC value on another thread
        self.PLCUpdateThread = QtCore.QThread()
        self.UpPLC = UpdatePLC(self.PLC)
        self.UpPLC.moveToThread(self.PLCUpdateThread)
        self.PLCUpdateThread.started.connect(self.UpPLC.run)
        self.PLCUpdateThread.start()

        # wait for PLC initialization finished
        time.sleep(2)

        # Update database on another thread
        self.DataUpdateThread = QtCore.QThread()
        self.UpDatabase = UpdateDataBase(self.PLC)
        self.UpDatabase.moveToThread(self.DataUpdateThread)
        self.DataUpdateThread.started.connect(self.UpDatabase.run)
        self.DataUpdateThread.start()




        # Stop all updater threads
    @QtCore.Slot()
    def StopUpdater(self):
        self.UpPLC.stop()
        self.PLCUpdateThread.quit()
        self.PLCUpdateThread.wait()

        self.UpDatabase.stop()
        self.DataUpdateThread.quit()
        self.DataUpdateThread.wait()





if __name__ == "__main__":
    # msg_mana=message_manager()
    # msg_mana.tencent_alarm("this is a test message")

    App = QtWidgets.QApplication(sys.argv)
    Update=Update()


    # PLC=PLC()
    # PLC.ReadAll()

    sys.exit(App.exec_())


