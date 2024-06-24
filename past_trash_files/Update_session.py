import os
import sys
import time
import platform
import datetime
from queue import Queue, Empty

from PySide2 import QtWidgets, QtCore, QtGui


from Update_session import *

from PPLC_v1 import PPLC
from TPLC_v1 import TPLC
from PICOPW import VerifyPW

from SlowDAQWidgets_SBC_v1 import *
# from SlowDAQ.SlowDAQ.SlowDAQWidgets import SingleButton

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.resize(2400, 1400)  # Open at center using resized
        self.setMinimumSize(2400, 1400)
        App.aboutToQuit.connect(self.StopUpdater)
        # Start display updater;
        self.StartUpdater()

    def StartUpdater(self):
        # Open connection to both PLCs
        self.P = PPLC()
        self.T = TPLC()


        # Read TPLC value on another thread
        self.TUpdateThread = None
        self.TUpdateThread = QtCore.QThread()
        self.pTPLC = UpdateTPLC(self.T)
        self.pTPLC.moveToThread(self.TUpdateThread)
        self.TUpdateThread.started.connect(self.pTPLC.run)
        self.TUpdateThread.start()

        # Read PPLC value on another thread
        self.PUpdateThread = None
        self.PUpdateThread = QtCore.QThread()
        self.UpPPLC = UpdatePPLC(self.P)
        self.UpPPLC.moveToThread(self.PUpdateThread)
        self.PUpdateThread.started.connect(self.UpPPLC.run)
        self.PUpdateThread.start()

    # Stop all updater threads
    @QtCore.Slot()
    def StopUpdater(self):
        self.UpPPLC.stop()
        self.UpTPLC.stop()
        self.TUpdateThread.quit()
        self.TUpdateThread.wait()

        self.PUpdateThread.quit()
        self.PUpdateThread.wait()


# Class to read PPLC value every 2 sec
class UpdatePPLC(QtCore.QObject):
    def __init__(self, PPLC, parent=None):
        super().__init__(parent)

        self.PPLC = PPLC
        self.Running = False

    @QtCore.Slot()
    def run(self):
        self.Running = True

        while self.Running:
            try:
                print("PPLC updating", datetime.datetime.now())
                self.PPLC.ReadAll()
                time.sleep(2)
            except Empty:
                continue

    @QtCore.Slot()
    def stop(self):
        self.Running = False


# Class to read TPLC value every 2 sec
class UpdateTPLC(QtCore.QObject):
    def __init__(self, TPLC, parent=None):
        super().__init__(parent)

        self.TPLC = TPLC
        self.Running = False

    @QtCore.Slot()
    def run(self):
        self.Running = True

        while self.Running:
            try:
                print("TPLC updating", datetime.datetime.now())
                self.TPLC.ReadAll()
                time.sleep(2)
            except Empty:
                continue

    @QtCore.Slot()
    def stop(self):
        self.Running = False


if __name__ == "__main__":
    App = QtWidgets.QApplication(sys.argv)

    MW = MainWindow()

    if platform.system() == "Linux":
        MW.show()
        MW.showMinimized()
    else:
        MW.show()
    MW.activateWindow()
    sys.exit(App.exec_())
