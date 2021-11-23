"""
This is the main SlowDAQ code used to read/setproperties of the TPLC and PPLC

By: Mathieu Laurin

v0.1.0 Initial code 29/11/19 ML
v0.1.1 Read and write implemented 08/12/19 ML
v0.1.2 Alarm implemented 07/01/20 ML
v0.1.3 PLC online detection, poll PLCs only when values are updated, fix Centos window size bug 04/03/20 ML
"""

import os, sys, time, platform, datetime, random, pickle, cgitb


from PySide2 import QtWidgets, QtCore, QtGui

from SlowDAQ_SBC_v2 import *
from PLC import *
from PICOPW import VerifyPW
from SlowDAQWidgets_SBC_v2 import *
import zmq

VERSION = "v2.1.3"
# if platform.system() == "Linux":
#     QtGui.QFontDatabase.addApplicationFont("/usr/share/fonts/truetype/vista/calibrib.ttf")
#     SMALL_LABEL_STYLE = "background-color: rgb(204,204,204);  font-family: calibrib;" \
#                         " font-size: 10px;" \
#                         " font-weight: bold;"
#     LABEL_STYLE = "background-color: rgb(204,204,204);  font-family: calibrib; " \
#                   "font-size: 12px; "
#     TITLE_STYLE = "background-color: rgb(204,204,204);  font-family: calibrib;" \
#                   " font-size: 14px; "

# SMALL_LABEL_STYLE = "background-color: rgb(204,204,204); border-radius: 10px; font-family: \"Calibri\";" \
#                     " font-size: 14px;" \
#                     " font-weight: bold;"

# LABEL_STYLE = "background-color: rgb(204,204,204); border-radius: 10px; font-family: \"Calibri\"; " \
#               "font-size: 18px; font-weight: bold;"
# TITLE_STYLE = "background-color: rgb(204,204,204); border-radius: 10px; font-family: \"Calibri\";" \
#               " font-size: 22px; font-weight: bold;"

# Settings adapted to sbc slowcontrol machine
# SMALL_LABEL_STYLE = "background-color: rgb(204,204,204); border-radius: 3px; font-family: \"Calibri\";" \
#                     " font-size: 10px;" \
#                     " font-weight: bold;"
# LABEL_STYLE = "background-color: rgb(204,204,204); border-radius: 3px; font-family: \"Calibri\"; " \
#               "font-size: 12px; font-weight: bold;"
# TITLE_STYLE = "background-color: rgb(204,204,204); border-radius: 3px; font-family: \"Calibri\";" \
#               " font-size: 14px; font-weight: bold;"

# BORDER_STYLE = " border-radius: 2px; border-color: black;"

# SMALL_LABEL_STYLE = " background-color: rgb(204,204,204); "
# #
# LABEL_STYLE = " background-color: rgb(204,204,204); "
# TITLE_STYLE = " background-color: rgb(204,204,204); "
BORDER_STYLE = "  "


SMALL_LABEL_STYLE = "background-color: rgb(204,204,204);  font-family: calibrib;" \
                        " font-size: 10px;" \
                        " font-weight: bold;"
LABEL_STYLE = "background-color: rgb(204,204,204);  font-family: calibrib; " \
                  "font-size: 12px; "
TITLE_STYLE = "background-color: rgb(204,204,204);  font-family: calibrib;" \
                  " font-size: 14px; "




ADMIN_TIMER = 30000
PLOTTING_SCALE = 0.66
ADMIN_PASSWORD = "60b6a2988e4ee1ad831ad567ad938adcc8e294825460bbcab26c1948b935bdf133e9e2c98ad4eafc622f4" \
                 "f5845cf006961abcc0a4007e3ac87d26c8981b792259f3f4db207dc14dbff315071c2f419122f1367668" \
                 "31c12bff0da3a2314ca2266"


R=0.6 # Resolution settings


sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    print("ExceptType: ", exctype, "Value: ", value, "Traceback: ", traceback)
    # sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook


def TwoD_into_OneD(Twod_array):
    Oned_array = []
    i_max = len(Twod_array)
    j_max = len(Twod_array[0])
    i_last = len(Twod_array) - 1
    j_last = len(Twod_array[i_last]) - 1
    for i in range(0, i_max):
        for j in range(0, j_max):
            Oned_array.append(Twod_array[i][j])
            if (i, j) == (i_last, j_last):
                break
        if (i, j) == (i_last, j_last):
            break
    return Oned_array


# Main class
# This is designed for linux system
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Get background image path
        if '__file__' in globals():
            self.Path = os.path.dirname(os.path.realpath(__file__))
        else:
            self.Path = os.getcwd()
        self.ImagePath = os.path.join(self.Path, "images")

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.resize(2400*R, 1400*R)  # Open at center using resized
        self.setMinimumSize(2400*R, 1400*R)
        self.setWindowTitle("SlowDAQ " + VERSION)
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.ImagePath, "Logo white_resized.png")))

        # Tabs, backgrounds & labels

        self.Tab = QtWidgets.QTabWidget(self)
        self.Tab.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.Tab.setStyleSheet("font-weight: bold; font-size: 20px; font-family: Calibri;")
        self.Tab.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.Tab.setGeometry(QtCore.QRect(0*R, 0*R, 2400*R, 1400*R))

        self.ThermosyphonTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.ThermosyphonTab, "Thermosyphon Main Panel")

        self.ThermosyphonTab.Background = QtWidgets.QLabel(self.ThermosyphonTab)
        self.ThermosyphonTab.Background.setScaledContents(True)
        self.ThermosyphonTab.Background.setStyleSheet('background-color:black;')
        pixmap_thermalsyphon = QtGui.QPixmap(os.path.join(self.ImagePath, "Thermosyphon.png"))
        pixmap_thermalsyphon = pixmap_thermalsyphon.scaledToWidth(2400*R)
        self.ThermosyphonTab.Background.setPixmap(QtGui.QPixmap(pixmap_thermalsyphon))
        self.ThermosyphonTab.Background.move(0*R, 0*R)
        self.ThermosyphonTab.Background.setAlignment(QtCore.Qt.AlignCenter)

        self.ChamberTab = QtWidgets.QWidget()
        self.Tab.addTab(self.ChamberTab, "Inner Chamber Components")

        self.ChamberTab.Background = QtWidgets.QLabel(self.ChamberTab)
        self.ChamberTab.Background.setScaledContents(True)
        self.ChamberTab.Background.setStyleSheet('background-color:black;')
        pixmap_chamber = QtGui.QPixmap(os.path.join(self.ImagePath, "Chamber_simplified.png"))
        pixmap_chamber = pixmap_chamber.scaledToWidth(2400*R)
        self.ChamberTab.Background.setPixmap(QtGui.QPixmap(pixmap_chamber))
        self.ChamberTab.Background.move(0*R, 0*R)
        self.ChamberTab.Background.setObjectName("ChamberBkg")

        self.FluidTab = QtWidgets.QWidget()
        self.Tab.addTab(self.FluidTab, "Fluid System")

        self.FluidTab.Background = QtWidgets.QLabel(self.FluidTab)
        self.FluidTab.Background.setScaledContents(True)
        self.FluidTab.Background.setStyleSheet('background-color:black;')
        pixmap_Fluid = QtGui.QPixmap(os.path.join(self.ImagePath, "CF4_XeAr_Panel_cryogenic.png"))
        pixmap_Fluid = pixmap_Fluid.scaledToWidth(2400*R)
        self.FluidTab.Background.setPixmap(QtGui.QPixmap(pixmap_Fluid))
        self.FluidTab.Background.move(0*R, 0*R)
        self.FluidTab.Background.setAlignment(QtCore.Qt.AlignCenter)
        self.FluidTab.Background.setObjectName("FluidBkg")

        self.HydraulicTab = QtWidgets.QWidget()
        self.Tab.addTab(self.HydraulicTab, "Hydraulic Apparatus")

        self.HydraulicTab.Background = QtWidgets.QLabel(self.HydraulicTab)
        self.HydraulicTab.Background.setScaledContents(True)
        self.HydraulicTab.Background.setStyleSheet('background-color:black;')
        pixmap_Hydraulic = QtGui.QPixmap(os.path.join(self.ImagePath, "Hydraulic_apparatus.png"))
        pixmap_Hydraulic = pixmap_Hydraulic.scaledToWidth(2400*R)
        self.HydraulicTab.Background.setPixmap(QtGui.QPixmap(pixmap_Hydraulic))
        self.HydraulicTab.Background.move(0*R, 0*R)
        self.HydraulicTab.Background.setAlignment(QtCore.Qt.AlignCenter)
        self.HydraulicTab.Background.setObjectName("HydraulicBkg")

        self.DatanSignalTab = QtWidgets.QWidget()
        self.Tab.addTab(self.DatanSignalTab, "Data and Signal Panel")

        self.DatanSignalTab.Background = QtWidgets.QLabel(self.DatanSignalTab)
        self.DatanSignalTab.Background.setScaledContents(True)
        self.DatanSignalTab.Background.setStyleSheet('background-color:black;')
        pixmap_DatanSignal = QtGui.QPixmap(os.path.join(self.ImagePath, "Default_Background.png"))
        pixmap_DatanSignal = pixmap_DatanSignal.scaledToWidth(2400*R)
        self.DatanSignalTab.Background.setPixmap(QtGui.QPixmap(pixmap_DatanSignal))
        self.DatanSignalTab.Background.move(0*R, 0*R)
        self.DatanSignalTab.Background.setAlignment(QtCore.Qt.AlignCenter)
        self.DatanSignalTab.Background.setObjectName("DatanSignalBkg")

        # Data saving and recovery
        # Data setting form is ended with .ini and directory is https://doc.qt.io/archives/qtforpython-5.12/PySide2/QtCore/QSettings.html depending on the System
        self.settings = QtCore.QSettings("$HOME/.config//SBC/SlowControl.ini", QtCore.QSettings.IniFormat)

        # Temperature tab buttons

        self.ThermosyphonWin = ThermosyphonWindow()
        self.Tstatus = FunctionButton(self.ThermosyphonWin, self.ThermosyphonTab)
        self.Tstatus.SubWindow.resize(1000*R, 1050*R)
        # self.Tstatus.StatusWindow.thermosyphon()
        self.Tstatus.move(0*R, 0*R)
        self.Tstatus.Button.setText("Thermosyphon status")

        self.LoginT = SingleButton(self.ThermosyphonTab)
        self.LoginT.move(340*R, 1200*R)
        self.LoginT.Label.setText("Login")
        self.LoginT.Button.setText("Guest")

        # PLC test window

        self.GV4301 = PnID_Alone(self.ThermosyphonTab)
        self.GV4301.Label.setText("GV4301")
        self.GV4301.move(185*R, 110*R)

        self.PRV4302 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4302.Label.setText("PRV4302")
        self.PRV4302.move(300*R, 32)

        self.MCV4303 = PnID_Alone(self.ThermosyphonTab)
        self.MCV4303.Label.setText("MCV4303")
        self.MCV4303.move(500*R, 80*R)

        self.RG4304 = PnID_Alone(self.ThermosyphonTab)
        self.RG4304.Label.setText("RG4304")
        self.RG4304.move(700*R, 110*R)

        self.MV4305 = PnID_Alone(self.ThermosyphonTab)
        self.MV4305.Label.setText("MV4305")
        self.MV4305.move(864*R, 110*R)

        self.PT4306 = Indicator(self.ThermosyphonTab)
        self.PT4306.Label.setText("PT4306")
        self.PT4306.move(1020*R, 60*R)
        self.PT4306.SetUnit(" psi")

        self.PV4307 = Valve(self.ThermosyphonTab)
        self.PV4307.Label.setText("PV4307")
        self.PV4307.move(925*R, 190*R)

        self.PV4308 = Valve(self.ThermosyphonTab)
        self.PV4308.Label.setText("PV4308")
        self.PV4308.move(850*R, 320*R)

        self.MV4309 = PnID_Alone(self.ThermosyphonTab)
        self.MV4309.Label.setText("MV4309")
        self.MV4309.move(390*R, 260*R)

        self.PG4310 = PnID_Alone(self.ThermosyphonTab)
        self.PG4310.Label.setText("PG4310")
        self.PG4310.move(225*R, 220*R)

        self.PRV4311 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4311.Label.setText("PRV4311")
        self.PRV4311.move(305*R, 190*R)

        self.VP4312 = PnID_Alone(self.ThermosyphonTab)
        self.VP4312.Label.setText("VP4312")
        self.VP4312.move(75*R, 260*R)

        self.BFM4313 = Indicator(self.ThermosyphonTab)
        self.BFM4313.Label.setText("BFM4313")
        self.BFM4313.move(1250*R, 340*R)
        self.BFM4313.SetUnit(" bfm")

        self.MCV4314 = PnID_Alone(self.ThermosyphonTab)
        self.MCV4314.Label.setText("MCV4314")
        self.MCV4314.move(1230*R, 470*R)

        self.PT4315 = Indicator(self.ThermosyphonTab)
        self.PT4315.Label.setText("PT4315")
        self.PT4315.move(950*R, 440*R)
        self.PT4315.SetUnit(" psi")

        self.PG4316 = PnID_Alone(self.ThermosyphonTab)
        self.PG4316.Label.setText("PG4316")
        self.PG4316.move(820*R, 470*R)

        self.PV4317 = Valve(self.ThermosyphonTab)
        self.PV4317.Label.setText("PV4317")
        self.PV4317.move(520*R, 380*R)

        self.PV4318 = Valve(self.ThermosyphonTab)
        self.PV4318.Label.setText("PV4318")
        self.PV4318.move(250*R, 580*R)

        self.PT4319 = Indicator(self.ThermosyphonTab)
        self.PT4319.Label.setText("PT4319")
        self.PT4319.move(570*R, 720*R)
        self.PT4319.SetUnit(" psi")

        self.PRV4320 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4320.Label.setText("PRV4320")
        self.PRV4320.move(570*R, 860*R)

        self.PV4321 = Valve(self.ThermosyphonTab)
        self.PV4321.Label.setText("PV4321")
        self.PV4321.move(530*R, 580*R)

        self.PT4322 = Indicator(self.ThermosyphonTab)
        self.PT4322.Label.setText("PT4322")
        self.PT4322.move(850*R, 720*R)
        self.PT4322.SetUnit(" psi")

        self.PRV4323 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4323.Label.setText("PRV4323")
        self.PRV4323.move(850*R, 860*R)

        self.PV4324 = Valve(self.ThermosyphonTab)
        self.PV4324.Label.setText("PV4324")
        self.PV4324.move(1100*R, 580*R)

        self.PT4325 = Indicator(self.ThermosyphonTab)
        self.PT4325.Label.setText("PT4325")
        self.PT4325.move(1150*R, 720*R)
        self.PT4325.SetUnit(" psi")

        self.PRV4326 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4326.Label.setText("PRV4326")
        self.PRV4326.move(1150*R, 860*R)

        self.SV4327 = Valve(self.ThermosyphonTab)
        self.SV4327.Label.setText("SV4327")
        self.SV4327.move(120*R, 330*R)

        self.SV4328 = Valve(self.ThermosyphonTab)
        self.SV4328.Label.setText("SV4328")

        self.SV4328.move(1350*R, 60*R)

        self.SV4329 = Valve(self.ThermosyphonTab)
        self.SV4329.Label.setText("SV4329")
        self.SV4329.move(1700*R, 60*R)

        self.TT4330 = Indicator(self.ThermosyphonTab)
        self.TT4330.Label.setText("TT4330")
        self.TT4330.move(1915*R, 55*R)

        self.SV4331 = Valve(self.ThermosyphonTab)
        self.SV4331.Label.setText("SV4331")
        self.SV4331.move(1340*R, 200*R)

        self.SV4332 = Valve(self.ThermosyphonTab)
        self.SV4332.Label.setText("SV4332")
        self.SV4332.move(1450*R, 300*R)

        self.SV4337 = Valve(self.ThermosyphonTab)
        self.SV4337.Label.setText("SV4337")
        self.SV4337.move(0*R,220*R)

        self.PRV4333 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4333.Label.setText("PRV4333")
        self.PRV4333.move(900*R, 650*R)

        self.PT6302 = Indicator(self.ThermosyphonTab)
        self.PT6302.Label.setText("PT6302")
        self.PT6302.move(2030*R, 690*R)
        self.PT6302.SetUnit(" psi")

        self.PRV6303 = PnID_Alone(self.ThermosyphonTab)
        self.PRV6303.Label.setText("PRV6303")
        self.PRV6303.move(1700*R, 700*R)

        self.MV6304 = PnID_Alone(self.ThermosyphonTab)
        self.MV6304.Label.setText("MV6304")
        self.MV6304.move(1810*R, 650*R)

        self.HE6201 = PnID_Alone(self.ThermosyphonTab)
        self.HE6201.Label.setText("HE6201")
        self.HE6201.move(1410*R, 1100*R)

        self.EV6204 = PnID_Alone(self.ThermosyphonTab)
        self.EV6204.Label.setText("EV6204")
        self.EV6204.move(930*R, 1100*R)

        self.PLCOnline = State(self.ThermosyphonTab)
        self.PLCOnline.move(200*R, 1200*R)
        self.PLCOnline.Label.setText("PLC link")
        self.PLCOnline.Field.setText("Offline")
        self.PLCOnline.SetAlarm()


        # Chamber tab buttons

        self.LoginP = SingleButton(self.ChamberTab)
        self.LoginP.move(140*R, 1200*R)
        self.LoginP.Label.setText("Login")
        self.LoginP.Button.setText("Guest")

        self.RTDset1Win = RTDset1()
        self.RTDSET1Button = FunctionButton(self.RTDset1Win, self.ChamberTab)
        # self.RTDSET1.StatusWindow.RTDset1()
        self.RTDSET1Button.move(300*R, 330*R)
        self.RTDSET1Button.Button.setText("RTDSET1")

        self.RTDset2Win = RTDset2()
        self.RTDSET2Button = FunctionButton(self.RTDset2Win, self.ChamberTab)
        # self.RTDSET2.StatusWindow.RTDset2()
        self.RTDSET2Button.move(300*R, 510*R)
        self.RTDSET2Button.Button.setText("RTDSET2")

        self.RTDset3Win = RTDset3()
        self.RTDSET3Button = FunctionButton(self.RTDset3Win, self.ChamberTab)
        # self.RTDSET3.StatusWindow.RTDset3()
        self.RTDSET3Button.move(300*R, 610*R)
        self.RTDSET3Button.Button.setText("RTDSET3")

        self.RTDset4Win = RTDset4()
        self.RTDSET4Button = FunctionButton(self.RTDset4Win, self.ChamberTab)
        # self.RTDSET4.StatusWindow.RTDset4()
        self.RTDSET4Button.move(1780*R, 1150*R)
        self.RTDSET4Button.Button.setText("RTDSET4")

        self.HT6219 = Heater(self.ChamberTab)
        # self.HT6219 = HeaterExpand(self.ChamberTab)
        self.HT6219.move(820*R, 120*R)
        self.HT6219.Label.setText("HT6219")
        self.HT6219.HeaterSubWindow.setWindowTitle("HT6219")
        # self.HT6219SUB = HeaterExpand(self.HT6219.HeaterSubWindow)
        # self.HT6219SUB.Label.setText("HT6219")
        # self.HT6219SUB.FBSwitch.Combobox.setItemText(0, "PT6220")
        # self.HT6219SUB.FBSwitch.Combobox.setItemText(1, "EMPTY")
        # self.HT6219SUB.RTD1.Label.setText("TT6220")
        # self.HT6219SUB.RTD2.Label.setText("EMPTY")

        self.HT6221 = Heater(self.ChamberTab)
        # self.HT6221 = HeaterExpand(self.ChamberTab)
        self.HT6221.move(1250*R, 120*R)
        self.HT6221.Label.setText("HT6221")
        self.HT6221.HeaterSubWindow.setWindowTitle("HT6221")
        # self.HT6221SUB = HeaterExpand(self.HT6221.HeaterSubWindow)
        # self.HT6221SUB.Label.setText("HT6221")
        # # self.HT6221.HeaterSubWindow.VL.addWidget(self.HT6221SUB)
        # self.HT6221SUB.RTD1.Label.setText("TT6222")
        # self.HT6221SUB.RTD2.Label.setText("EMPTY")

        self.HT6214 = Heater(self.ChamberTab)
        # self.HT6214 = HeaterExpand(self.ChamberTab)
        self.HT6214.move(1780*R, 145*R)
        self.HT6214.Label.setText("HT6214")
        self.HT6214.HeaterSubWindow.setWindowTitle("HT6214")
        # self.HT6214SUB = HeaterExpand(self.HT6214.HeaterSubWindow)
        # self.HT6214SUB.Label.setText("HT6214")
        # # self.HT6214.HeaterSubWindow.VL.addWidget(self.HT6214SUB)
        # self.HT6214SUB.RTD1.Label.setText("TT6213")
        # self.HT6214SUB.RTD2.Label.setText("TT6401")

        self.HT6202 = Heater(self.ChamberTab)
        # self.HT6202 = HeaterExpand(self.ChamberTab)
        self.HT6202.move(1780*R, 485*R)
        self.HT6202.Label.setText("HT6202")
        self.HT6202.HeaterSubWindow.setWindowTitle("HT6202")
        # self.HT6202SUB = HeaterExpand(self.HT6202.HeaterSubWindow)
        # self.HT6202SUB.Label.setText("HT6202")
        # # self.HT6202.HeaterSubWindow.VL.addWidget(self.HT6202SUB)
        # self.HT6202SUB.RTD1.Label.setText("TT6203")
        # self.HT6202SUB.RTD2.Label.setText("TT6404")

        self.HT6206 = Heater(self.ChamberTab)
        # self.HT6206 = HeaterExpand(self.ChamberTab)
        self.HT6206.move(1780*R, 585*R)
        self.HT6206.Label.setText("HT6206")
        self.HT6206.HeaterSubWindow.setWindowTitle("HT6206")
        # self.HT6206SUB = HeaterExpand(self.HT6206.HeaterSubWindow)
        # self.HT6206SUB.Label.setText("HT6206")
        # # self.HT6206.HeaterSubWindow.VL.addWidget(self.HT6206SUB)
        # self.HT6206SUB.RTD1.Label.setText("TT6207")
        # self.HT6206SUB.RTD2.Label.setText("TT6405")

        self.HT6210 = Heater(self.ChamberTab)
        # self.HT6210 = HeaterExpand(self.ChamberTab)
        self.HT6210.move(1780*R, 685*R)
        self.HT6210.Label.setText("HT6210")
        self.HT6210.HeaterSubWindow.setWindowTitle("HT6210")
        # self.HT6210SUB = HeaterExpand(self.HT6210.HeaterSubWindow)
        # self.HT6210SUB.Label.setText("HT6210")
        # # self.HT6210.HeaterSubWindow.VL.addWidget(self.HT6210SUB)
        # self.HT6210SUB.RTD1.Label.setText("TT6211")
        # self.HT6210SUB.RTD2.Label.setText("TT6406")

        self.HT6223 = Heater(self.ChamberTab)
        # self.HT6223 = HeaterExpand(self.ChamberTab)
        self.HT6223.move(1780*R, 785*R)
        self.HT6223.Label.setText("HT6223")
        self.HT6223.HeaterSubWindow.setWindowTitle("HT6223")
        # self.HT6223SUB = HeaterExpand(self.HT6223.HeaterSubWindow)
        # self.HT6223SUB.Label.setText("HT6223")
        # # self.HT6223.HeaterSubWindow.VL.addWidget(self.HT6223SUB)
        # self.HT6223SUB.RTD1.Label.setText("TT6407")
        # self.HT6223SUB.RTD2.Label.setText("TT6410")

        self.HT6224 = Heater(self.ChamberTab)
        # self.HT6224 = HeaterExpand(self.ChamberTab)
        self.HT6224.move(1780*R, 885*R)
        self.HT6224.Label.setText("HT6224")
        self.HT6224.HeaterSubWindow.setWindowTitle("HT6224")
        # self.HT6224SUB = HeaterExpand(self.HT6224.HeaterSubWindow)
        # self.HT6224SUB.Label.setText("HT6224")
        # # self.HT6224.HeaterSubWindow.VL.addWidget(self.HT6224SUB)
        # self.HT6224SUB.RTD1.Label.setText("TT6408")
        # self.HT6224SUB.RTD2.Label.setText("TT6411")

        self.HT6225 = Heater(self.ChamberTab)
        # self.HT6225 = HeaterExpand(self.ChamberTab)
        self.HT6225.move(1780*R, 985*R)
        self.HT6225.Label.setText("HT6225")
        self.HT6225.HeaterSubWindow.setWindowTitle("HT6225")
        # self.HT6225SUB = HeaterExpand(self.HT6225.HeaterSubWindow)
        # self.HT6225SUB.Label.setText("HT6225")
        # # self.HT6225.HeaterSubWindow.VL.addWidget(self.HT6225SUB)
        # self.HT6225SUB.RTD1.Label.setText("TT6409")
        # # self.TT6412 = self.HT6225SUB.RTD2
        # self.HT6225SUB.RTD2.Label.setText("TT6412")

        self.HT2123 = Heater(self.ChamberTab)
        # self.HT2123 = HeaterExpand(self.ChamberTab)
        self.HT2123.move(670*R, 820*R)
        self.HT2123.Label.setText("HT2123")
        self.HT2123.HeaterSubWindow.setWindowTitle("HT2123")
        # self.HT2123SUB = HeaterExpand(self.HT2123.HeaterSubWindow)
        # self.HT2123SUB.Label.setText("HT2123")
        # # self.HT2123.HeaterSubWindow.VL.addWidget(self.HT2123SUB)
        # self.HT2123SUB.RTD1.Label.setText("EMPTY")
        # self.HT2123SUB.RTD2.Label.setText("EMPTY")

        self.HT2124 = Heater(self.ChamberTab)
        # self.HT2124 = HeaterExpand(self.ChamberTab)
        self.HT2124.move(670*R, 820*R)
        self.HT2124.Label.setText("HT2124")
        self.HT2124.HeaterSubWindow.setWindowTitle("HT2124")
        # self.HT2124SUB = HeaterExpand(self.HT2124.HeaterSubWindow)
        # self.HT2124SUB.Label.setText("HT2124")
        # # self.HT2124.HeaterSubWindow.VL.addWidget(self.HT2124SUB)
        # self.HT2124SUB.RTD1.Label.setText("EMPTY")
        # self.HT2124SUB.RTD2.Label.setText("EMPTY")

        self.HT2125 = Heater(self.ChamberTab)
        # self.HT2125 = HeaterExpand(self.ChamberTab)
        self.HT2125.move(1030*R, 730*R)
        self.HT2125.Label.setText("HT2125")
        self.HT2125.HeaterSubWindow.setWindowTitle("HT2125")
        # self.HT2125SUB = HeaterExpand(self.HT2125.HeaterSubWindow)
        # self.HT2125SUB.Label.setText("HT2125")
        # # self.HT2125.HeaterSubWindow.VL.addWidget(self.HT2125SUB)
        # self.HT2125SUB.RTD1.Label.setText("EMPTY")
        # self.HT2125SUB.RTD2.Label.setText("EMPTY")

        self.PT1101 = Indicator(self.ChamberTab)
        self.PT1101.move(940*R, 990*R)
        self.PT1101.Label.setText("PT1101")
        self.PT1101.SetUnit(" psi")

        self.PT2121 = Indicator(self.ChamberTab)
        self.PT2121.move(1210*R, 990*R)
        self.PT2121.Label.setText("PT2121")
        self.PT2121.SetUnit(" psi")

        self.HT1202 = Heater(self.ChamberTab)
        self.HT1202.move(840*R, 1250*R)
        self.HT1202.Label.setText("HT1202")
        self.HT1202.HeaterSubWindow.setWindowTitle("HT1202")
        # self.HT1202SUB = HeaterExpand(self.HT1202.HeaterSubWindow)
        # self.HT1202SUB.Label.setText("HT1202")
        # self.HT1202.HeaterSubWindow.VL.addWidget(self.HT1202SUB)
        # self.TT6413 = self.HT1202SUB.RTD1
        # self.HT1202SUB.RTD1.Label.setText("TT6413")
        # self.TT6415 = self.HT1202SUB.RTD2
        # self.HT1202SUB.RTD2.Label.setText("TT6415")


        self.HT2203 = Heater(self.ChamberTab)
        self.HT2203.move(1260*R, 1215*R)
        self.HT2203.Label.setText("HT2203")
        self.HT2203.HeaterSubWindow.setWindowTitle("HT2203")
        # self.HT2203SUB = HeaterExpand(self.HT2203.HeaterSubWindow)
        # self.HT2203SUB.Label.setText("HT2203")
        # self.HT2203.HeaterSubWindow.VL.addWidget(self.HT2203SUB)
        # self.TT6414 = self.HT2203SUB.RTD1
        # self.HT2203SUB.RTD1.Label.setText("TT6414")
        # self.TT6416 = self.HT2203SUB.RTD2
        # self.HT2203SUB.RTD2.Label.setText("TT6416")

        # Fluid tab buttons

        self.PT2316 = Indicator(self.FluidTab)
        self.PT2316.move(1900*R, 360*R)
        self.PT2316.Label.setText("PT2316")
        self.PT2316.SetUnit(" psi")

        self.PT2330 = Indicator(self.FluidTab)
        self.PT2330.move(1780*R, 360*R)
        self.PT2330.Label.setText("PT2330")
        self.PT2330.SetUnit(" psi")

        self.PT2335 = Indicator(self.FluidTab)
        self.PT2335.move(1590*R, 420*R)
        self.PT2335.Label.setText("PT2335")
        self.PT2335.SetUnit(" psi")

        self.TT7401 = Indicator(self.FluidTab)
        self.TT7401.move(1985*R, 250*R)
        self.TT7401.Label.setText("TT7401")

        self.TT7202 = Indicator(self.FluidTab)
        self.TT7202.move(910*R, 530*R)
        self.TT7202.Label.setText("TT7202")

        self.LI2340 = Indicator(self.FluidTab)
        self.LI2340.move(2250*R, 880*R)
        self.LI2340.Label.setText("LI2340 ")

        self.PT1101Fluid = Indicator(self.FluidTab)
        self.PT1101Fluid.move(1030*R, 1300*R)
        self.PT1101Fluid.Label.setText("PT1101")
        self.PT1101Fluid.SetUnit(" psi")

        self.PT2121Fluid = Indicator(self.FluidTab)
        self.PT2121Fluid.move(1260*R, 1300*R)
        self.PT2121Fluid.Label.setText("PT2121")
        self.PT2121Fluid.SetUnit(" psi")

        self.MFC1316 = Heater(self.FluidTab)
        self.MFC1316.move(400*R, 800*R)
        self.MFC1316.Label.setText("MFC1316")
        self.MFC1316.HeaterSubWindow.setWindowTitle("MFC1316")
        # self.MFC1316SUB = HeaterExpand(self.MFC1316.HeaterSubWindow)
        # self.MFC1316SUB.Label.setText("MFC1316")
        # # self.MFC1316.HeaterSubWindow.VL.addWidget(self.MFC1316SUB)
        # # self.PT1332SUB = self.MFC1316SUB.RTD1
        self.MFC1316.HeaterSubWindow.RTD1.Label.setText("TT1332")
        self.MFC1316.HeaterSubWindow.RTD2.Label.setText("EMPTY")


        self.PT1332 = Indicator(self.FluidTab)
        self.PT1332.move(630*R, 900*R)
        self.PT1332.Label.setText("PT1332")
        self.PT1332.SetUnit(" psi")

        self.PV1344=Valve(self.FluidTab)
        self.PV1344.Label.setText("PV1344")
        self.PV1344.move(1400*R,600*R)

        self.PV5305 = Valve(self.FluidTab)
        self.PV5305.Label.setText("PV5305")
        self.PV5305.move(1200*R, 530*R)

        self.PV5306 = Valve(self.FluidTab)
        self.PV5306.Label.setText("PV5306")
        self.PV5306.move(1150*R, 800*R)

        self.PV5307 = Valve(self.FluidTab)
        self.PV5307.Label.setText("PV5307")
        self.PV5307.move(1030*R, 620*R)

        self.PV5309 = Valve(self.FluidTab)
        self.PV5309.Label.setText("PV5309")
        self.PV5309.move(1130*R, 310*R)

        # Hydraulic buttons
        self.PU3305 = Valve(self.HydraulicTab)
        self.PU3305.Label.setText("PU3305")
        self.PU3305.move(365*R, 380*R)

        self.TT3401 = Indicator(self.HydraulicTab)
        self.TT3401.move(385*R, 500*R)
        self.TT3401.Label.setText("TT3401")

        self.TT3402 = Indicator(self.HydraulicTab)
        self.TT3402.move(90*R, 53)
        self.TT3402.Label.setText("TT3402")

        self.PT3314 = Indicator(self.HydraulicTab)
        self.PT3314.move(700*R, 450*R)
        self.PT3314.Label.setText("PT3314")
        self.PT3314.SetUnit(" psi")

        self.PT3320 = Indicator(self.HydraulicTab)
        self.PT3320.move(880*R, 530*R)
        self.PT3320.Label.setText("PT3320")
        self.PT3320.SetUnit(" psi")

        self.PT3308 = Indicator(self.HydraulicTab)
        self.PT3308.move(440*R, 1080*R)
        self.PT3308.Label.setText("PT3308")
        self.PT3308.SetUnit(" psi")

        self.PT3309 = Indicator(self.HydraulicTab)
        self.PT3309.move(665*R, 1140*R)
        self.PT3309.Label.setText("PT3309")
        self.PT3309.SetUnit(" psi")

        self.PT3311 = Indicator(self.HydraulicTab)
        self.PT3311.move(750*R, 1110*R)
        self.PT3311.Label.setText("PT3311")
        self.PT3311.SetUnit(" psi")

        self.HFSV3312 = Valve(self.HydraulicTab)
        self.HFSV3312.Label.setText("HFSV3312")
        self.HFSV3312.move(650*R, 1030*R)

        self.HFSV3323 = Valve(self.HydraulicTab)
        self.HFSV3323.Label.setText("HFSV3323")
        self.HFSV3323.move(1050*R, 1080*R)

        self.HFSV3331 = Valve(self.HydraulicTab)
        self.HFSV3331.Label.setText("HFSV3331")
        self.HFSV3331.move(1100*R, 320*R)

        self.PT3332 = Indicator(self.HydraulicTab)
        self.PT3332.move(1570*R, 1125*R)
        self.PT3332.Label.setText("PT3332")
        self.PT3332.SetUnit(" psi")

        self.PT3333 = Indicator(self.HydraulicTab)
        self.PT3333.move(1570*R, 1250*R)
        self.PT3333.Label.setText("PT3333")
        self.PT3333.SetUnit(" psi")

        self.SV3326 = Valve(self.HydraulicTab)
        self.SV3326.Label.setText("SV3326")
        self.SV3326.move(1200*R, 400*R)

        self.SV3329 = Valve(self.HydraulicTab)
        self.SV3329.Label.setText("SV3329")
        self.SV3329.move(1570*R, 470*R)

        self.SV3322 = Valve(self.HydraulicTab)
        self.SV3322.Label.setText("SV3322")
        self.SV3322.move(1000*R, 780*R)

        # self.SERVO3321 = AOMultiLoop(self.HydraulicTab)
        # self.SERVO3321.move(1200*R, 550*R)
        # self.SERVO3321.Label.setText("SERVO3321")
        # self.SERVO3321.HeaterSubWindow.setWindowTitle("SERVO3321")
        # self.SERVO3321SUB = AOMutiLoopExpand(self.SERVO3321.HeaterSubWindow)
        # self.SERVO3321SUB.Label.setText("SERVO3321")
        # self.SERVO3321.HeaterSubWindow.VL.addWidget(self.SERVO3321SUB)
        # self.SERVO3321SUB.RTD1.Label.setText("EMPTY")
        # self.SERVO3321SUB.RTD2.Label.setText("EMPTY")

        self.SV3325 = Valve(self.HydraulicTab)
        self.SV3325.Label.setText("SV3325")
        self.SV3325.move(1200*R, 1000*R)

        self.SV3307 = Valve(self.HydraulicTab)
        self.SV3307.Label.setText("SV3307")
        self.SV3307.move(200*R, 1030*R)

        self.SV3310 = Valve(self.HydraulicTab)
        self.SV3310.Label.setText("SV3310")
        self.SV3310.move(800*R, 1240*R)

        self.TT7403 = Indicator(self.HydraulicTab)
        self.TT7403.move(1880*R, 950*R)
        self.TT7403.Label.setText("TT7403")

        self.LI3335 = Indicator(self.HydraulicTab)
        self.LI3335.move(2100*R, 950*R)
        self.LI3335.Label.setText("LI3335 ")

        self.LT3338 = Indicator(self.HydraulicTab)
        self.LT3338.move(2100*R, 990*R)
        self.LT3338.Label.setText("LT3338 ")

        self.LT3339 = Indicator(self.HydraulicTab)
        self.LT3339.move(2100*R, 1030*R)
        self.LT3339.Label.setText("LT3339 ")

        self.PT1101Hy = Indicator(self.HydraulicTab)
        self.PT1101Hy.move(1900*R, 800*R)
        self.PT1101Hy.Label.setText("PT1101")
        self.PT1101Hy.SetUnit(" psi")

        self.PT2121Hy = Indicator(self.HydraulicTab)
        self.PT2121Hy.move(2100*R, 800*R)
        self.PT2121Hy.Label.setText("PT2121")
        self.PT2121Hy.SetUnit(" psi")

        # Data and Signal Tab
        self.ReadSettings = Loadfile(self.DatanSignalTab)
        self.ReadSettings.move(50*R, 50*R)
        self.ReadSettings.LoadFileButton.clicked.connect(
            lambda x: self.Recover(address=self.ReadSettings.FilePath.text()))

        self.SaveSettings = CustomSave(self.DatanSignalTab)
        self.SaveSettings.move(700*R, 50*R)
        self.SaveSettings.SaveFileButton.clicked.connect(
            lambda x: self.Save(directory=self.SaveSettings.Head, project=self.SaveSettings.Tail))


        # Alarm button
        self.AlarmWindow = AlarmWin()
        self.AlarmButton = AlarmButton(self.AlarmWindow, self)
        self.AlarmButton.SubWindow.resize(1000*R, 500*R)
        # self.AlarmButton.StatusWindow.AlarmWindow()

        self.AlarmButton.move(0*R, 1300*R)
        self.AlarmButton.Button.setText("Alarm Button")


        #commands stack
        self.address ={"PV1344":12288, "PV4307":12289,"PV4308":12290,"PV4317":12291,"PV4318":12292,"PV4321":12293,"PV4324":12294,"PV5305":12295,"PV5306":12296,
                       "PV5307":12297,"PV5309":12298,"SV3307":12299,"SV3310":12300,"SV3322":12301,"SV3325":12302,"SV3326":12303,"SV3329":12304,
                       "SV4327":12305,"SV4328":12306,"SV4329":12307,"SV4331":12308,"SV4332":12309, "SV4337": 12310, "HFSV3312": 12311,
                       "HFSV3323":12312, "HFSV3331":12313,"TT2101": 12988, "TT2111": 12990, "TT2113": 12992, "TT2118": 12994, "TT2119": 12996,
                           "TT4330": 12998, "TT6203": 13000, "TT6207": 13002, "TT6211": 13004, "TT6213": 13006,
                           "TT6222": 13008, "TT6407": 13010, "TT6408": 13012, "TT6409": 13014, "TT6415": 13016,
                           "TT6416": 13018,"TT2420": 31000, "TT2422": 31002, "TT2424": 31004, "TT2425": 31006, "TT2442": 36000,
                              "TT2403": 31008, "TT2418": 31010, "TT2427": 31012, "TT2429": 31014, "TT2431": 32000,
                              "TT2441": 36002, "TT2414": 32002, "TT2413": 32004, "TT2412": 32006, "TT2415": 32008,
                              "TT2409": 36004, "TT2436": 32010, "TT2438": 32012, "TT2440": 32014, "TT2402": 33000,
                              "TT2411": 38004, "TT2443": 36006, "TT2417": 33004, "TT2404": 33006, "TT2408": 33008,
                              "TT2407": 33010, "TT2406": 36008, "TT2428": 33012, "TT2432": 33014, "TT2421": 34000,
                              "TT2416": 38006, "TT2439": 36010, "TT2419": 34004, "TT2423": 34006, "TT2426": 34008,
                              "TT2430": 34010, "TT2450": 36012, "TT2401": 34012, "TT2449": 34014, "TT2445": 35000,
                              "TT2444": 35002, "TT2435": 35004, "TT2437": 36014, "TT2446": 35006, "TT2447": 35008,
                              "TT2448": 35010, "TT2410": 35012, "TT2405": 35014, "TT6220": 37000, "TT6401": 37002,
                              "TT6404": 37004, "TT6405": 37006, "TT6406": 37008, "TT6410": 37010, "TT6411": 37012,
                              "TT6412": 37014, "TT6413": 38000, "TT6414": 38002}
        self.commands = {}

        self.signal_connection()

        # Set user to guest by default
        self.User = "Guest"
        self.UserTimer = QtCore.QTimer(self)
        self.UserTimer.setSingleShot(True)
        self.UserTimer.timeout.connect(self.Timeout)
        self.ActivateControls(False)

        # Initialize PLC live counters

        self.PLCLiveCounter = 0

        # Link signals to slots (toggle type)
        # self.SV4327.Button.clicked.connect(self.SV4327.ButtonClicked)
        # self.SV4327.Signals.sSignal.connect(self.SetSVMode)
        # self.SV4328.Signals.sSignal.connect(self.SetSVMode)
        # self.SV4329.Signals.sSignal.connect(self.SetSVMode)
        # self.SV4331.Signals.sSignal.connect(self.SetSVMode)
        # self.SV4332.Signals.sSignal.connect(self.SetSVMode)
        # self.SV3307.Signals.sSignal.connect(self.SetSVMode)
        # self.SV3310.Signals.sSignal.connect(self.SetSVMode)
        # self.HFSV3312.Signals.sSignal.connect(self.SetSVMode)
        # self.SV3322.Signals.sSignal.connect(self.SetSVMode)
        # self.HFSV3323.Signals.sSignal.connect(self.SetSVMode)
        # self.SV3325.Signals.sSignal.connect(self.SetSVMode)
        # self.SV3326.Signals.sSignal.connect(self.SetSVMode)
        # self.SV3329.Signals.sSignal.connect(self.SetSVMode)
        # self.HFSV3331.Signals.sSignal.connect(self.SetSVMode)
        self.LoginT.Button.clicked.connect(self.ChangeUser)
        self.LoginP.Button.clicked.connect(self.ChangeUser)


        App.aboutToQuit.connect(self.StopUpdater)
        # Start display updater;
        self.StartUpdater()

    def StartUpdater(self):
        # Open connection to both PLCs
        # self.PLC = PLC()

        # Read PLC value on another thread
        # self.PLCUpdateThread = QtCore.QThread()
        # self.UpPLC = UpdatePLC(self.PLC)
        # self.UpPLC.moveToThread(self.PLCUpdateThread)
        # self.PLCUpdateThread.started.connect(self.UpPLC.run)
        # self.PLCUpdateThread.start()

        self.ClientUpdateThread = QtCore.QThread()
        self.UpClient = UpdateClient(self)
        self.UpClient.moveToThread(self.ClientUpdateThread)
        self.ClientUpdateThread.started.connect(self.UpClient.run)
        self.ClientUpdateThread.start()


        # Make sure PLCs values are initialized before trying to access them with update function
        time.sleep(2)

        # Update display values on another thread
        self.DUpdateThread = QtCore.QThread()
        self.UpDisplay = UpdateDisplay(self,self.UpClient)
        self.UpDisplay.moveToThread(self.DUpdateThread)
        self.DUpdateThread.started.connect(self.UpDisplay.run)
        self.DUpdateThread.start()


    # Stop all updater threads
    @QtCore.Slot()
    def StopUpdater(self):
        # self.UpPLC.stop()
        # self.PLCUpdateThread.quit()
        # self.PLCUpdateThread.wait()
        self.UpClient.stop()
        self.ClientUpdateThread.quit()
        self.ClientUpdateThread.wait()


        self.UpDisplay.stop()
        self.DUpdateThread.quit()
        self.DUpdateThread.wait()
    # signal connections to write settings to PLC codes

    def signal_connection(self):
        self.PV1344.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV1344.Label.text()))
        self.PV1344.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV1344.Label.text()))
        self.PV4307.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4307.Label.text()))
        self.PV4307.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4307.Label.text()))
        self.PV4308.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4308.Label.text()))
        self.PV4308.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4308.Label.text()))
        self.PV4317.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4317.Label.text()))
        self.PV4317.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4317.Label.text()))
        self.PV4318.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4318.Label.text()))
        self.PV4318.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4318.Label.text()))
        self.PV4321.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4321.Label.text()))
        self.PV4321.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4321.Label.text()))
        self.PV4324.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4324.Label.text()))
        self.PV4324.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4324.Label.text()))
        self.PV5305.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV5305.Label.text()))
        self.PV5305.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV5305.Label.text()))
        self.PV5306.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV5306.Label.text()))
        self.PV5306.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV5306.Label.text()))
        self.PV5307.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV5307.Label.text()))
        self.PV5307.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV5307.Label.text()))
        self.PV5309.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV5309.Label.text()))
        self.PV5309.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV5309.Label.text()))
        self.SV3307.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3307.Label.text()))
        self.SV3307.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3307.Label.text()))
        self.SV3310.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3310.Label.text()))
        self.SV3310.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3310.Label.text()))
        self.SV3322.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3322.Label.text()))
        self.SV3322.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3322.Label.text()))
        self.SV3325.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3325.Label.text()))
        self.SV3325.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3325.Label.text()))
        self.SV3326.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3326.Label.text()))
        self.SV3326.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3326.Label.text()))
        self.SV3329.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3329.Label.text()))
        self.SV3329.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3329.Label.text()))
        self.SV4327.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4327.Label.text()))
        self.SV4327.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4327.Label.text()))
        self.SV4328.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4328.Label.text()))
        self.SV4328.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4328.Label.text()))
        self.SV4329.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4329.Label.text()))
        self.SV4329.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4329.Label.text()))
        self.SV4331.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4331.Label.text()))
        self.SV4331.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4331.Label.text()))
        self.SV4332.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4332.Label.text()))
        self.SV4332.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4332.Label.text()))
        self.SV4337.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4337.Label.text()))
        self.SV4337.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4337.Label.text()))
        self.HFSV3312.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.HFSV3312.Label.text()))
        self.HFSV3312.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.HFSV3312.Label.text()))
        self.HFSV3323.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.HFSV3323.Label.text()))
        self.HFSV3323.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.HFSV3323.Label.text()))
        self.HFSV3331.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.HFSV3331.Label.text()))
        self.HFSV3331.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.HFSV3331.Label.text()))

        # Beckoff RTDs

        self.AlarmButton.SubWindow.TT2101.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2101.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2101.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2101.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2101.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2101.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2101.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2101.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2101.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2101.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2111.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2111.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2111.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2111.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2111.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2111.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2111.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2111.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2111.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2111.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2113.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2113.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2113.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2113.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2113.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2113.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2113.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2113.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2113.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2113.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2118.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2118.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2118.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2118.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2118.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2118.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2118.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2118.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2118.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2118.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2119.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2119.Label.text(),Act=self.AlarmButton.SubWindow.TT2119.AlarmMode.isChecked(),
                                         LowLimit=self.AlarmButton.SubWindow.TT2119.Low_Limit.Field.text(), HighLimit=self.AlarmButton.SubWindow.TT2119.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2119.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2119.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2119.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2119.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2119.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT4330.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT4330.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT4330.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT4330.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT4330.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT4330.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT4330.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT4330.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT4330.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT4330.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6203.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6203.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6203.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6203.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6203.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6203.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6203.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6203.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6203.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6203.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6207.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6207.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6207.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6207.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6207.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6207.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6207.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6207.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6207.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6207.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6211.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6211.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6211.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6211.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6211.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6211.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6211.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6211.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6211.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6211.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6213.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6213.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6213.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6213.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6213.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6213.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6213.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6213.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6213.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6213.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6222.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6222.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6222.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6222.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6222.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6222.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6222.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6222.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6222.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6222.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6407.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6407.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6407.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6407.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6407.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6407.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6407.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6407.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6407.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6407.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6408.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6408.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6408.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6408.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6408.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6408.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6408.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6408.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6408.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6408.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6409.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6409.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6409.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6409.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6409.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6409.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6409.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6409.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6409.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6409.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6415.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6415.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6415.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6415.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6415.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6415.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6415.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6415.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6415.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6415.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6416.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6416.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6416.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6416.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6416.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6416.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6416.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6416.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6416.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6416.High_Limit.Field.text()))

        # Field Point RTDs
        self.AlarmButton.SubWindow.TT2420.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2420.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2420.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2420.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2420.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2422.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2422.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2422.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2422.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2422.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2424.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2424.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2424.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2424.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2424.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2425.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2425.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2425.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2425.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2425.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2442.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2442.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2442.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2442.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2442.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2403.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2403.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2403.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2403.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2403.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2418.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2418.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2418.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2418.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2418.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2427.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2427.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2427.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2427.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2427.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2429.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2429.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2429.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2429.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2429.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2431.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2431.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2431.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2431.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2431.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2441.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2441.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2441.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2441.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2441.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2414.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2414.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2414.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2414.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2414.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2413.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2413.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2413.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2413.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2413.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2412.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2412.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2412.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2412.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2412.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2415.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2415.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2415.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2415.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2415.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2409.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2409.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2409.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2409.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2409.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2436.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2436.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2436.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2436.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2436.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2438.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2438.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2438.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2438.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2438.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2440.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2440.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2440.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2440.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2440.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2402.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2402.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2402.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2402.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2402.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2411.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2411.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2411.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2411.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2411.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2443.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2443.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2443.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2443.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2443.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2417.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2417.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2417.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2417.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2417.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2404.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2404.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2404.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2404.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2404.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2408.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2408.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2408.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2408.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2408.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2407.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2407.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2407.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2407.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2407.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2406.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2406.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2406.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2406.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2406.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2428.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2428.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2428.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2428.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2428.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2432.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2432.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2432.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2432.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2432.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2421.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2421.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2421.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2421.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2421.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2416.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2416.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2416.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2416.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2416.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2439.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2439.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2439.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2439.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2439.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2419.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2419.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2419.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2419.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2419.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2423.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2423.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2423.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2423.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2423.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2426.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2426.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2426.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2426.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2426.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2430.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2430.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2430.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2430.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2430.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2450.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2450.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2450.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2450.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2450.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2401.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2401.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2401.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2449.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2449.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2449.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2449.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2449.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2445.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2445.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2445.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2445.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2445.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2444.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2444.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2444.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2444.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2444.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2435.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2435.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2435.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2435.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2435.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2437.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2437.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2437.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2437.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2437.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2446.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2446.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2446.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2446.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2446.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2447.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2447.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2447.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2447.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2447.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2448.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2448.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2448.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2448.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2448.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2410.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2410.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2410.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2410.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2410.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2405.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2405.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2405.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2405.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2405.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6220.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6220.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6220.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6220.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6401.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6401.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6401.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6404.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6404.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6404.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6404.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6404.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6405.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6405.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6405.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6405.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6405.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6406.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6406.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6406.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6406.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6406.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6410.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6410.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6410.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6410.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6410.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6411.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6411.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6411.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6411.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6411.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6412.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6412.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6412.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6412.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6412.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6413.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6413.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6413.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6413.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6413.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6414.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6414.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6414.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6414.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6414.High_Limit.Field.text()))


        #FP rtd updatebutton

        self.AlarmButton.SubWindow.TT2420.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2420.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2420.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2420.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2420.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2422.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2422.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2422.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2422.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2422.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2424.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2424.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2424.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2424.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2424.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2425.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2425.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2425.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2425.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2425.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2442.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2442.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2442.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2442.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2442.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2403.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2403.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2403.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2403.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2403.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2418.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2418.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2418.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2418.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2418.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2427.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2427.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2427.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2427.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2427.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2429.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2429.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2429.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2429.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2429.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2431.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2431.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2431.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2431.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2431.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2441.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2441.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2441.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2441.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2441.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2414.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2414.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2414.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2414.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2414.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2413.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2413.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2413.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2413.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2413.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2412.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2412.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2412.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2412.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2412.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2415.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2415.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2415.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2415.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2415.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2409.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2409.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2409.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2409.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2409.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2436.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2436.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2436.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2436.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2436.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2438.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2438.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2438.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2438.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2438.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2440.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2440.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2440.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2440.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2440.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2402.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2402.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2402.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2402.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2402.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2411.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2411.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2411.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2411.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2411.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2443.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2443.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2443.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2443.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2443.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2417.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2417.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2417.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2417.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2417.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2404.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2404.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2404.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2404.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2404.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2408.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2408.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2408.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2408.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2408.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2407.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2407.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2407.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2407.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2407.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2406.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2406.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2406.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2406.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2406.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2428.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2428.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2428.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2428.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2428.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2432.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2432.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2432.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2432.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2432.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2421.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2421.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2421.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2421.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2421.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2416.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2416.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2416.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2416.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2416.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2439.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2439.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2439.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2439.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2439.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2419.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2419.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2419.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2419.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2419.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2423.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2423.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2423.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2423.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2423.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2426.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2426.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2426.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2426.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2426.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2430.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2430.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2430.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2430.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2430.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2450.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2450.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2450.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2450.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2450.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2401.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2401.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2401.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2449.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2449.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2449.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2449.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2449.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2445.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2445.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2445.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2445.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2445.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2444.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2444.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2444.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2444.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2444.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2435.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2435.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2435.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2435.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2435.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2437.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2437.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2437.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2437.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2437.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2446.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2446.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2446.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2446.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2446.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2447.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2447.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2447.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2447.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2447.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2448.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2448.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2448.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2448.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2448.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2410.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2410.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2410.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2410.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2410.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT2405.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2405.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2405.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2405.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2405.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6220.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6220.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6220.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6220.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6401.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6401.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6401.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6404.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6404.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6404.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6404.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6404.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6405.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6405.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6405.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6405.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6405.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6406.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6406.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6406.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6406.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6406.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6410.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6410.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6410.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6410.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6410.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6411.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6411.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6411.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6411.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6411.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6412.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6412.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6412.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6412.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6412.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6413.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6413.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6413.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6413.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6413.High_Limit.Field.text()))

        self.AlarmButton.SubWindow.TT6414.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6414.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6414.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6414.Low_Limit.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6414.High_Limit.Field.text()))






    @QtCore.Slot()
    def LButtonClicked(self,pid):
        self.commands[pid]={"server":"BO","address": self.address[pid], "type":"valve","operation":"OPEN", "value":1}
        print(self.commands)
        print(pid,"LButton is clicked")

    @QtCore.Slot()
    def RButtonClicked(self, pid):
        self.commands[pid] = {"server": "BO", "address": self.address[pid], "type": "valve", "operation": "CLOSE",
                              "value": 1}
        print(self.commands)
        print(pid, "R Button is clicked")

    @QtCore.Slot()
    def BOTTBoxUpdate(self,pid, Act,LowLimit, HighLimit):
        self.commands[pid]={"server": "BO", "address": self.address[pid], "type": "TT", "operation": {"Act":Act,
                                "LowLimit":LowLimit,"HighLimit":HighLimit}}
        print(pid,Act,LowLimit,HighLimit,"ARE OK?")

    @QtCore.Slot()
    def FPTTBoxUpdate(self,pid, Act,LowLimit, HighLimit):
        self.commands[pid]={"server": "FP", "address": self.address[pid], "type": "TT", "operation": {"Act":Act,
                                "LowLimit":LowLimit,"HighLimit":HighLimit}}
        print(pid,Act,LowLimit,HighLimit,"ARE OK?")


    # Ask if staying in admin mode after timeout
    @QtCore.Slot()
    def Timeout(self):
        if QtWidgets.QMessageBox.question(self, "Login", "Stay logged in?") == QtWidgets.QMessageBox.StandardButton.Yes:
            self.UserTimer.start(ADMIN_TIMER)
        else:
            self.ChangeUser()

    # Change user and lock/unlock controls
    @QtCore.Slot()
    def ChangeUser(self):
        if self.User == "Guest":
            Dialog = QtWidgets.QInputDialog()
            Dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
            Dialog.setLabelText("Please entre password")
            Dialog.setModal(True)
            Dialog.setWindowTitle("Login")
            Dialog.exec()
            if Dialog.result():
                if VerifyPW(ADMIN_PASSWORD, Dialog.textValue()):
                    self.User = "Admin"
                    self.LoginT.Button.setText("Admin")
                    self.LoginP.Button.setText("Admin")
                    self.LoginW.Button.setText("Admin")

                    self.ActivateControls(True)

                    self.UserTimer.start(ADMIN_TIMER)
        else:
            self.User = "Guest"
            self.LoginT.Button.setText("Guest")
            self.LoginP.Button.setText("Guest")
            self.LoginW.Button.setText("Guest")

            self.ActivateControls(False)

    @QtCore.Slot()
    def update_alarmwindow(self,dic):

        self.AlarmButton.CollectAlarm([self.AlarmButton.SubWindow.TT2111.Alarm,
                                          self.AlarmButton.SubWindow.TT2112.Alarm,
                                          self.AlarmButton.SubWindow.TT2113.Alarm,
                                          self.AlarmButton.SubWindow.TT2114.Alarm,
                                          self.AlarmButton.SubWindow.TT2115.Alarm,
                                          self.AlarmButton.SubWindow.TT2116.Alarm,
                                          self.AlarmButton.SubWindow.TT2117.Alarm,
                                          self.AlarmButton.SubWindow.TT2118.Alarm,
                                          self.AlarmButton.SubWindow.TT2119.Alarm,
                                          self.AlarmButton.SubWindow.TT2120.Alarm])
        # print("Alarm Status=", self.AlarmButton.Button.Alarm)
        if self.AlarmButton.Button.Alarm:
            self.AlarmButton.ButtonAlarmSetSignal()
            self.AlarmButton.SubWindow.ReassignRTD1Order()

        else:
            self.AlarmButton.ButtonAlarmResetSignal()
            self.AlarmButton.SubWindow.ResetOrder()

    # Lock/unlock controls
    def ActivateControls(self, Activate):
        # self.SV4327.Activate(Activate)
        # self.SV4328.Activate(Activate)
        # self.SV4329.Activate(Activate)
        # self.SV4331.Activate(Activate)
        # self.SV4332.Activate(Activate)
        # self.SV3307.Activate(Activate)
        # self.SV3310.Activate(Activate)
        # self.HFSV3312.Activate(Activate)
        # self.SV3322.Activate(Activate)
        # self.HFSV3323.Activate(Activate)
        # self.SV3325.Activate(Activate)
        # self.SV3326.Activate(Activate)
        # self.SV3329.Activate(Activate)
        # self.HFSV3331.Activate(Activate)
        return

    # This section call the right PLC function when you change a value on the display
    @QtCore.Slot(str)
    def SetSVMode(self, value):
        self.P.SetSValveMode(value)

    @QtCore.Slot(str)
    def SetHotRegionMode(self, value):
        self.PLC.SetHotRegionPIDMode(value)

    @QtCore.Slot(float)
    def SetHotRegionSetpoint(self, value):
        self.PLC.SetHotRegionSetpoint(value)

    @QtCore.Slot(float)
    def SetHotRegionP(self, value):
        self.PLC.SetHotRegionP(value)

    @QtCore.Slot(float)
    def SetHotRegionI(self, value):
        self.PLC.SetHotRegionI(value)

    @QtCore.Slot(float)
    def SetHotRegionD(self, value):
        self.PLC.SetHotRegionD(value)

    @QtCore.Slot(str)
    def SetColdRegionMode(self, value):
        self.PLC.SetColdRegionPIDMode(value)

    @QtCore.Slot(float)
    def SetColdRegionSetpoint(self, value):
        self.PLC.SetColdRegionSetpoint(value)

    @QtCore.Slot(float)
    def SetColdRegionP(self, value):
        self.PLC.SetColdRegionP(value)

    @QtCore.Slot(float)
    def SetColdRegionI(self, value):
        self.PLC.SetColdRegionI(value)

    @QtCore.Slot(float)
    def SetColdRegionD(self, value):
        self.PLC.SetColdRegionD(value)

    @QtCore.Slot(float)
    def SetBottomChillerSetpoint(self, value):
        self.PLC.SetColdRegionD(value)

    @QtCore.Slot(str)
    def SetBottomChillerState(self, value):
        self.PLC.SetBottomChillerState(value)

    @QtCore.Slot(float)
    def SetTopChillerSetpoint(self, value):
        self.PLC.SetTopChillerSetpoint(value)

    @QtCore.Slot(str)
    def SetTopChillerState(self, value):
        self.PLC.SetTopChillerState(value)

    @QtCore.Slot(float)
    def SetCameraChillerSetpoint(self, value):
        self.PLC.SetCameraChillerSetpoint(value)

    @QtCore.Slot(str)
    def SetCameraChillerState(self, value):
        self.PLC.SetCameraChillerState(value)

    @QtCore.Slot(str)
    def SetInnerHeaterState(self, value):
        self.PLC.SetInnerPowerState(value)

    @QtCore.Slot(float)
    def SetInnerHeaterPower(self, value):
        self.PLC.SetInnerPower(value)

    @QtCore.Slot(str)
    def SetFreonHeaterState(self, value):
        self.PLC.SetFreonPowerState(value)

    @QtCore.Slot(float)
    def SetFreonHeaterPower(self, value):
        self.PLC.SetFreonPower(value)

    @QtCore.Slot(str)
    def SetOuterCloseHeaterState(self, value):
        self.PLC.SetOuterClosePowerState(value)

    @QtCore.Slot(float)
    def SetOuterCloseHeaterPower(self, value):
        self.PLC.SetOuterClosePower(value)

    @QtCore.Slot(str)
    def SetOuterFarHeaterState(self, value):
        self.PLC.SetOuterFarPowerState(value)

    @QtCore.Slot(float)
    def SetOuterFarHeaterPower(self, value):
        self.PLC.SetOuterFarPower(value)

    @QtCore.Slot(float)
    def SetCoolingFlow(self, value):
        self.PLC.SetFlowValve(value)

    @QtCore.Slot(str)
    def setCartMode(self, value):
        if value == "Auto":
            self.P.GoIdle()
        elif value == "Manual":
            self.P.GoManual()

    @QtCore.Slot(float)
    def SetCartSetpoint(self, value):
        self.P.SetPressureSetpoint(value)

    @QtCore.Slot(str)
    def SetCartState(self, value):
        if value == "Compress":
            self.P.Compress()
        elif value == "Expand":
            self.P.Expand()

    @QtCore.Slot(float)
    def SetRegSetpoint(self, value):
        self.P.SetAirRegulatorSetpoint(value)

    @QtCore.Slot(str)
    def SetFast1(self, value):
        self.P.SetFastCompressValve1(value)

    @QtCore.Slot(str)
    def SetFast2(self, value):
        self.P.SetFastCompressValve2(value)

    @QtCore.Slot(str)
    def SetFast3(self, value):
        self.P.SetFastCompressValve3(value)

    @QtCore.Slot(str)
    def SetFreonIn(self, value):
        self.P.SetFreonInValve(value)

    @QtCore.Slot(str)
    def SetFreonOut(self, value):
        self.P.SetFreonOutValve(value)

    @QtCore.Slot(str)
    def SetFast(self, value):
        self.P.SetFastCompressValveCart(value)

    @QtCore.Slot(str)
    def SetSlow(self, value):
        self.P.SetSlowCompressValve(value)

    @QtCore.Slot(str)
    def SetExpansion(self, value):
        self.P.SetExpansionValve(value)

    @QtCore.Slot(str)
    def SetOil(self, value):
        self.P.SetOilReliefValve(value)

    @QtCore.Slot(str)
    def SetPump(self, value):
        self.P.SetPumpState(value)

    @QtCore.Slot(str)
    def SetWaterChillerState(self, value):
        self.PLC.SetWaterChillerState(value)

    @QtCore.Slot(float)
    def SetWaterChillerSetpoint(self, value):
        self.PLC.SetWaterChillerSetpoint(value)

    @QtCore.Slot(str)
    def SetPrimingValve(self, value):
        if value == "Open":
            self.PLC.SetWaterPrimingPower("On")
        elif value == "Close":
            self.PLC.SetWaterPrimingPower("Off")

    def closeEvent(self, event):
        self.CloseMessage = QtWidgets.QMessageBox()
        self.CloseMessage.setText("The program is to be closed")
        self.CloseMessage.setInformativeText("Do you want to save the settings?")
        self.CloseMessage.setStandardButtons(
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
        self.CloseMessage.setDefaultButton(QtWidgets.QMessageBox.Save)
        self.ret = self.CloseMessage.exec_()
        if self.ret == QtWidgets.QMessageBox.Save:
            self.Save()
            event.accept()
        elif self.ret == QtWidgets.QMessageBox.Discard:
            event.accept()
        elif self.ret == QtWidgets.QMessageBox.Cancel:
            event.ignore()
        else:
            print("Some problems with closing windows...")
            pass

    def Save(self, directory=None, company="SBC", project="Slowcontrol"):
        # dir is the path storing the ini setting file
        if directory is None:
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/CheckBox",
                                   self.AlarmButton.SubWindow.TT2111.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/CheckBox",
                                   self.AlarmButton.SubWindow.TT2401.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/CheckBox",
                                   self.AlarmButton.SubWindow.TT2406.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/CheckBox",
                                   self.AlarmButton.SubWindow.TT2411.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/CheckBox",
                                   self.AlarmButton.SubWindow.TT2416.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/CheckBox",
                                   self.AlarmButton.SubWindow.TT2421.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/CheckBox",
                                   self.AlarmButton.SubWindow.TT2426.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/CheckBox",
                                   self.AlarmButton.SubWindow.TT2431.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/CheckBox",
                                   self.AlarmButton.SubWindow.TT2435.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/CheckBox",
                                   self.AlarmButton.SubWindow.TT2440.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/CheckBox",
                                   self.AlarmButton.SubWindow.TT4330.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/CheckBox",
                                   self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/CheckBox",
                                   self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/CheckBox",
                                   self.AlarmButton.SubWindow.TT6221.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/CheckBox",
                                   self.AlarmButton.SubWindow.TT6222.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/CheckBox",
                                   self.AlarmButton.SubWindow.TT6223.AlarmMode.isChecked())
            # set PT value
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/CheckBox",
                                   self.AlarmButton.SubWindow.PT1101.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/CheckBox",
                                   self.AlarmButton.SubWindow.PT2316.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/CheckBox",
                                   self.AlarmButton.SubWindow.PT2321.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/CheckBox",
                                   self.AlarmButton.SubWindow.PT2330.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/CheckBox",
                                   self.AlarmButton.SubWindow.PT2335.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/CheckBox",
                                   self.AlarmButton.SubWindow.PT3308.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/CheckBox",
                                   self.AlarmButton.SubWindow.PT3309.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/CheckBox",
                                   self.AlarmButton.SubWindow.PT3310.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/CheckBox",
                                   self.AlarmButton.SubWindow.PT3311.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/CheckBox",
                                   self.AlarmButton.SubWindow.PT3314.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/CheckBox",
                                   self.AlarmButton.SubWindow.PT3320.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/CheckBox",
                                   self.AlarmButton.SubWindow.PT3333.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/CheckBox",
                                   self.AlarmButton.SubWindow.PT4306.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/CheckBox",
                                   self.AlarmButton.SubWindow.PT4315.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/CheckBox",
                                   self.AlarmButton.SubWindow.PT4319.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/CheckBox",
                                   self.AlarmButton.SubWindow.PT4322.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/CheckBox",
                                   self.AlarmButton.SubWindow.PT4325.AlarmMode.isChecked())

            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/LowLimit",
                                   self.AlarmButton.SubWindow.TT2111.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/LowLimit",
                                   self.AlarmButton.SubWindow.TT2401.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/LowLimit",
                                   self.AlarmButton.SubWindow.TT2406.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/LowLimit",
                                   self.AlarmButton.SubWindow.TT2411.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/LowLimit",
                                   self.AlarmButton.SubWindow.TT2416.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/LowLimit",
                                   self.AlarmButton.SubWindow.TT2421.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/LowLimit",
                                   self.AlarmButton.SubWindow.TT2426.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/LowLimit",
                                   self.AlarmButton.SubWindow.TT2431.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/LowLimit",
                                   self.AlarmButton.SubWindow.TT2435.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/LowLimit",
                                   self.AlarmButton.SubWindow.TT2440.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/LowLimit",
                                   self.AlarmButton.SubWindow.TT4330.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/LowLimit",
                                   self.AlarmButton.SubWindow.TT6220.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/LowLimit",
                                   self.AlarmButton.SubWindow.TT6220.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/LowLimit",
                                   self.AlarmButton.SubWindow.TT6221.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/LowLimit",
                                   self.AlarmButton.SubWindow.TT6222.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/LowLimit",
                                   self.AlarmButton.SubWindow.TT6223.Low_Limit.Field.text())
            # set PT value
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/LowLimit",
                                   self.AlarmButton.SubWindow.PT1101.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/LowLimit",
                                   self.AlarmButton.SubWindow.PT2316.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/LowLimit",
                                   self.AlarmButton.SubWindow.PT2321.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/LowLimit",
                                   self.AlarmButton.SubWindow.PT2330.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/LowLimit",
                                   self.AlarmButton.SubWindow.PT2335.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/LowLimit",
                                   self.AlarmButton.SubWindow.PT3308.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/LowLimit",
                                   self.AlarmButton.SubWindow.PT3309.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/LowLimit",
                                   self.AlarmButton.SubWindow.PT3310.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/LowLimit",
                                   self.AlarmButton.SubWindow.PT3311.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/LowLimit",
                                   self.AlarmButton.SubWindow.PT3314.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/LowLimit",
                                   self.AlarmButton.SubWindow.PT3320.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/LowLimit",
                                   self.AlarmButton.SubWindow.PT3333.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/LowLimit",
                                   self.AlarmButton.SubWindow.PT4306.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/LowLimit",
                                   self.AlarmButton.SubWindow.PT4315.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/LowLimit",
                                   self.AlarmButton.SubWindow.PT4319.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/LowLimit",
                                   self.AlarmButton.SubWindow.PT4322.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/LowLimit",
                                   self.AlarmButton.SubWindow.PT4325.Low_Limit.Field.text())

            # high limit

            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/HighLimit",
                                   self.AlarmButton.SubWindow.TT2111.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/HighLimit",
                                   self.AlarmButton.SubWindow.TT2401.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/HighLimit",
                                   self.AlarmButton.SubWindow.TT2406.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/HighLimit",
                                   self.AlarmButton.SubWindow.TT2411.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/HighLimit",
                                   self.AlarmButton.SubWindow.TT2416.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/HighLimit",
                                   self.AlarmButton.SubWindow.TT2421.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/HighLimit",
                                   self.AlarmButton.SubWindow.TT2426.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/HighLimit",
                                   self.AlarmButton.SubWindow.TT2431.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/HighLimit",
                                   self.AlarmButton.SubWindow.TT2435.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/HighLimit",
                                   self.AlarmButton.SubWindow.TT2440.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/HighLimit",
                                   self.AlarmButton.SubWindow.TT4330.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/HighLimit",
                                   self.AlarmButton.SubWindow.TT6220.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/HighLimit",
                                   self.AlarmButton.SubWindow.TT6220.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/HighLimit",
                                   self.AlarmButton.SubWindow.TT6221.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/HighLimit",
                                   self.AlarmButton.SubWindow.TT6222.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/HighLimit",
                                   self.AlarmButton.SubWindow.TT6223.High_Limit.Field.text())
            # set PT value
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/HighLimit",
                                   self.AlarmButton.SubWindow.PT1101.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/HighLimit",
                                   self.AlarmButton.SubWindow.PT2316.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/HighLimit",
                                   self.AlarmButton.SubWindow.PT2321.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/HighLimit",
                                   self.AlarmButton.SubWindow.PT2330.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/HighLimit",
                                   self.AlarmButton.SubWindow.PT2335.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/HighLimit",
                                   self.AlarmButton.SubWindow.PT3308.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/HighLimit",
                                   self.AlarmButton.SubWindow.PT3309.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/HighLimit",
                                   self.AlarmButton.SubWindow.PT3310.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/HighLimit",
                                   self.AlarmButton.SubWindow.PT3311.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/HighLimit",
                                   self.AlarmButton.SubWindow.PT3314.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/HighLimit",
                                   self.AlarmButton.SubWindow.PT3320.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/HighLimit",
                                   self.AlarmButton.SubWindow.PT3333.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/HighLimit",
                                   self.AlarmButton.SubWindow.PT4306.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/HighLimit",
                                   self.AlarmButton.SubWindow.PT4315.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/HighLimit",
                                   self.AlarmButton.SubWindow.PT4319.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/HighLimit",
                                   self.AlarmButton.SubWindow.PT4322.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/HighLimit",
                                   self.AlarmButton.SubWindow.PT4325.High_Limit.Field.text())

            print("saving data to Default path: $HOME/.config//SBC/SlowControl.ini")
        else:
            try:
                # modify the qtsetting default save settings. if the directory is inside a folder named sbc, then save
                # the file into the folder. If not, create a folder named sbc and save the file in it.
                (path_head, path_tail) = os.path.split(directory)
                if path_tail == company:
                    path = os.path.join(directory, project)
                else:
                    path = os.path.join(directory, company, project)
                print(path)
                self.customsettings = QtCore.QSettings(path, QtCore.QSettings.IniFormat)

                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/CheckBox",
                                             self.AlarmButton.SubWindow.TT2111.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/CheckBox",
                                             self.AlarmButton.SubWindow.TT2401.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/CheckBox",
                                             self.AlarmButton.SubWindow.TT2406.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/CheckBox",
                                             self.AlarmButton.SubWindow.TT2411.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/CheckBox",
                                             self.AlarmButton.SubWindow.TT2416.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/CheckBox",
                                             self.AlarmButton.SubWindow.TT2421.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/CheckBox",
                                             self.AlarmButton.SubWindow.TT2426.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/CheckBox",
                                             self.AlarmButton.SubWindow.TT2431.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/CheckBox",
                                             self.AlarmButton.SubWindow.TT2435.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/CheckBox",
                                             self.AlarmButton.SubWindow.TT2440.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/CheckBox",
                                             self.AlarmButton.SubWindow.TT4330.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/CheckBox",
                                             self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/CheckBox",
                                             self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/CheckBox",
                                             self.AlarmButton.SubWindow.TT6221.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/CheckBox",
                                             self.AlarmButton.SubWindow.TT6222.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/CheckBox",
                                             self.AlarmButton.SubWindow.TT6223.AlarmMode.isChecked())
                # set PT value
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/CheckBox",
                                             self.AlarmButton.SubWindow.PT1101.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/CheckBox",
                                             self.AlarmButton.SubWindow.PT2316.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/CheckBox",
                                             self.AlarmButton.SubWindow.PT2321.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/CheckBox",
                                             self.AlarmButton.SubWindow.PT2330.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/CheckBox",
                                             self.AlarmButton.SubWindow.PT2335.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/CheckBox",
                                             self.AlarmButton.SubWindow.PT3308.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/CheckBox",
                                             self.AlarmButton.SubWindow.PT3309.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/CheckBox",
                                             self.AlarmButton.SubWindow.PT3310.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/CheckBox",
                                             self.AlarmButton.SubWindow.PT3311.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/CheckBox",
                                             self.AlarmButton.SubWindow.PT3314.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/CheckBox",
                                             self.AlarmButton.SubWindow.PT3320.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/CheckBox",
                                             self.AlarmButton.SubWindow.PT3333.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/CheckBox",
                                             self.AlarmButton.SubWindow.PT4306.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/CheckBox",
                                             self.AlarmButton.SubWindow.PT4315.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/CheckBox",
                                             self.AlarmButton.SubWindow.PT4319.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/CheckBox",
                                             self.AlarmButton.SubWindow.PT4322.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/CheckBox",
                                             self.AlarmButton.SubWindow.PT4325.AlarmMode.isChecked())

                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/LowLimit",
                                             self.AlarmButton.SubWindow.TT2111.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/LowLimit",
                                             self.AlarmButton.SubWindow.TT2401.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/LowLimit",
                                             self.AlarmButton.SubWindow.TT2406.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/LowLimit",
                                             self.AlarmButton.SubWindow.TT2411.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/LowLimit",
                                             self.AlarmButton.SubWindow.TT2416.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/LowLimit",
                                             self.AlarmButton.SubWindow.TT2421.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/LowLimit",
                                             self.AlarmButton.SubWindow.TT2426.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/LowLimit",
                                             self.AlarmButton.SubWindow.TT2431.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/LowLimit",
                                             self.AlarmButton.SubWindow.TT2435.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/LowLimit",
                                             self.AlarmButton.SubWindow.TT2440.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/LowLimit",
                                             self.AlarmButton.SubWindow.TT4330.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/LowLimit",
                                             self.AlarmButton.SubWindow.TT6220.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/LowLimit",
                                             self.AlarmButton.SubWindow.TT6220.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/LowLimit",
                                             self.AlarmButton.SubWindow.TT6221.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/LowLimit",
                                             self.AlarmButton.SubWindow.TT6222.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/LowLimit",
                                             self.AlarmButton.SubWindow.TT6223.Low_Limit.Field.text())
                # set PT value
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/LowLimit",
                                             self.AlarmButton.SubWindow.PT1101.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/LowLimit",
                                             self.AlarmButton.SubWindow.PT2316.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/LowLimit",
                                             self.AlarmButton.SubWindow.PT2321.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/LowLimit",
                                             self.AlarmButton.SubWindow.PT2330.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/LowLimit",
                                             self.AlarmButton.SubWindow.PT2335.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/LowLimit",
                                             self.AlarmButton.SubWindow.PT3308.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/LowLimit",
                                             self.AlarmButton.SubWindow.PT3309.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/LowLimit",
                                             self.AlarmButton.SubWindow.PT3310.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/LowLimit",
                                             self.AlarmButton.SubWindow.PT3311.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/LowLimit",
                                             self.AlarmButton.SubWindow.PT3314.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/LowLimit",
                                             self.AlarmButton.SubWindow.PT3320.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/LowLimit",
                                             self.AlarmButton.SubWindow.PT3333.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/LowLimit",
                                             self.AlarmButton.SubWindow.PT4306.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/LowLimit",
                                             self.AlarmButton.SubWindow.PT4315.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/LowLimit",
                                             self.AlarmButton.SubWindow.PT4319.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/LowLimit",
                                             self.AlarmButton.SubWindow.PT4322.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/LowLimit",
                                             self.AlarmButton.SubWindow.PT4325.Low_Limit.Field.text())

                # high limit

                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/HighLimit",
                                             self.AlarmButton.SubWindow.TT2111.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/HighLimit",
                                             self.AlarmButton.SubWindow.TT2401.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/HighLimit",
                                             self.AlarmButton.SubWindow.TT2406.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/HighLimit",
                                             self.AlarmButton.SubWindow.TT2411.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/HighLimit",
                                             self.AlarmButton.SubWindow.TT2416.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/HighLimit",
                                             self.AlarmButton.SubWindow.TT2421.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/HighLimit",
                                             self.AlarmButton.SubWindow.TT2426.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/HighLimit",
                                             self.AlarmButton.SubWindow.TT2431.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/HighLimit",
                                             self.AlarmButton.SubWindow.TT2435.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/HighLimit",
                                             self.AlarmButton.SubWindow.TT2440.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/HighLimit",
                                             self.AlarmButton.SubWindow.TT4330.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/HighLimit",
                                             self.AlarmButton.SubWindow.TT6220.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/HighLimit",
                                             self.AlarmButton.SubWindow.TT6220.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/HighLimit",
                                             self.AlarmButton.SubWindow.TT6221.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/HighLimit",
                                             self.AlarmButton.SubWindow.TT6222.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/HighLimit",
                                             self.AlarmButton.SubWindow.TT6223.High_Limit.Field.text())
                # set PT value
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/HighLimit",
                                             self.AlarmButton.SubWindow.PT1101.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/HighLimit",
                                             self.AlarmButton.SubWindow.PT2316.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/HighLimit",
                                             self.AlarmButton.SubWindow.PT2321.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/HighLimit",
                                             self.AlarmButton.SubWindow.PT2330.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/HighLimit",
                                             self.AlarmButton.SubWindow.PT2335.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/HighLimit",
                                             self.AlarmButton.SubWindow.PT3308.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/HighLimit",
                                             self.AlarmButton.SubWindow.PT3309.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/HighLimit",
                                             self.AlarmButton.SubWindow.PT3310.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/HighLimit",
                                             self.AlarmButton.SubWindow.PT3311.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/HighLimit",
                                             self.AlarmButton.SubWindow.PT3314.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/HighLimit",
                                             self.AlarmButton.SubWindow.PT3320.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/HighLimit",
                                             self.AlarmButton.SubWindow.PT3333.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/HighLimit",
                                             self.AlarmButton.SubWindow.PT4306.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/HighLimit",
                                             self.AlarmButton.SubWindow.PT4315.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/HighLimit",
                                             self.AlarmButton.SubWindow.PT4319.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/HighLimit",
                                             self.AlarmButton.SubWindow.PT4322.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/HighLimit",
                                             self.AlarmButton.SubWindow.PT4325.High_Limit.Field.text())
                print("saving data to ", path)
            except:
                print("Failed to custom save the settings.")

    def Recover(self, address="$HOME/.config//SBC/SlowControl.ini"):
        # address is the ini file 's directory you want to recover

        try:
            # default recover. If no other address is claimed, then recover settings from default directory
            if address == "$HOME/.config//SBC/SlowControl.ini":
                self.RecoverChecked(self.AlarmButton.SubWindow.TT4330,
                                    "MainWindow/AlarmButton/SubWindow/TT4330/CheckBox")
                self.RecoverChecked(self.AlarmButton.SubWindow.PT4306,
                                    "MainWindow/AlarmButton/SubWindow/PT4306/CheckBox")
                self.RecoverChecked(self.AlarmButton.SubWindow.PT4315,
                                    "MainWindow/AlarmButton/SubWindow/PT4315/CheckBox")
                self.RecoverChecked(self.AlarmButton.SubWindow.PT4319,
                                    "MainWindow/AlarmButton/SubWindow/PT4319/CheckBox")
                self.RecoverChecked(self.AlarmButton.SubWindow.PT4322,
                                    "MainWindow/AlarmButton/SubWindow/PT4322/CheckBox")
                self.RecoverChecked(self.AlarmButton.SubWindow.PT4325,
                                    "MainWindow/AlarmButton/SubWindow/PT4325/CheckBox")

                self.AlarmButton.SubWindow.TT4330.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/TT4330/LowLimit"))
                self.AlarmButton.SubWindow.TT4330.Low_Limit.UpdateValue()
                self.AlarmButton.SubWindow.PT4306.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/PT4306/LowLimit"))
                self.AlarmButton.SubWindow.PT4306.Low_Limit.UpdateValue()
                self.AlarmButton.SubWindow.PT4315.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/PT4315/LowLimit"))
                self.AlarmButton.SubWindow.PT4315.Low_Limit.UpdateValue()
                self.AlarmButton.SubWindow.PT4319.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/PT4319/LowLimit"))
                self.AlarmButton.SubWindow.PT4319.Low_Limit.UpdateValue()
                self.AlarmButton.SubWindow.PT4322.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/PT4322/LowLimit"))
                self.AlarmButton.SubWindow.PT4322.Low_Limit.UpdateValue()
                self.AlarmButton.SubWindow.PT4325.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/PT4325/LowLimit"))
                self.AlarmButton.SubWindow.PT4325.Low_Limit.UpdateValue()

                self.AlarmButton.SubWindow.TT4330.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/TT4330/HighLimit"))
                self.AlarmButton.SubWindow.TT4330.High_Limit.UpdateValue()
                self.AlarmButton.SubWindow.PT4306.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/PT4306/HighLimit"))
                self.AlarmButton.SubWindow.PT4306.High_Limit.UpdateValue()
                self.AlarmButton.SubWindow.PT4315.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/PT4315/HighLimit"))
                self.AlarmButton.SubWindow.PT4315.High_Limit.UpdateValue()
                self.AlarmButton.SubWindow.PT4319.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/PT4319/HighLimit"))
                self.AlarmButton.SubWindow.PT4319.High_Limit.UpdateValue()
                self.AlarmButton.SubWindow.PT4322.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/PT4322/HighLimit"))
                self.AlarmButton.SubWindow.PT4322.High_Limit.UpdateValue()
                self.AlarmButton.SubWindow.PT4325.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/SubWindow/PT4325/HighLimit"))
                self.AlarmButton.SubWindow.PT4325.High_Limit.UpdateValue()
            else:
                try:
                    # else, recover from the claimed directory
                    # address should be surfix with ini. Example:$HOME/.config//SBC/SlowControl.ini
                    directory = QtCore.QSettings(str(address), QtCore.QSettings.IniFormat)
                    print("Recovering from " + str(address))
                    self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.TT4330,
                                        subdir="MainWindow/AlarmButton/SubWindow/TT4330/CheckBox",
                                        loadedsettings=directory)
                    self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.PT4306,
                                        subdir="MainWindow/AlarmButton/SubWindow/PT4306/CheckBox",
                                        loadedsettings=directory)
                    self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.PT4315,
                                        subdir="MainWindow/AlarmButton/SubWindow/PT4315/CheckBox",
                                        loadedsettings=directory)
                    self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.PT4319,
                                        subdir="MainWindow/AlarmButton/SubWindow/PT4319/CheckBox",
                                        loadedsettings=directory)
                    self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.PT4322,
                                        subdir="MainWindow/AlarmButton/SubWindow/PT4322/CheckBox",
                                        loadedsettings=directory)
                    self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.PT4325,
                                        subdir="MainWindow/AlarmButton/SubWindow/PT4325/CheckBox",
                                        loadedsettings=directory)

                    self.AlarmButton.SubWindow.TT4330.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/TT4330/LowLimit"))
                    self.AlarmButton.SubWindow.TT4330.Low_Limit.UpdateValue()
                    self.AlarmButton.SubWindow.PT4306.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/PT4306/LowLimit"))
                    self.AlarmButton.SubWindow.PT4306.Low_Limit.UpdateValue()
                    self.AlarmButton.SubWindow.PT4315.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/PT4315/LowLimit"))
                    self.AlarmButton.SubWindow.PT4315.Low_Limit.UpdateValue()
                    self.AlarmButton.SubWindow.PT4319.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/PT4319/LowLimit"))
                    self.AlarmButton.SubWindow.PT4319.Low_Limit.UpdateValue()
                    self.AlarmButton.SubWindow.PT4322.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/PT4322/LowLimit"))
                    self.AlarmButton.SubWindow.PT4322.Low_Limit.UpdateValue()
                    self.AlarmButton.SubWindow.PT4325.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/PT4325/LowLimit"))
                    self.AlarmButton.SubWindow.PT4325.Low_Limit.UpdateValue()

                    self.AlarmButton.SubWindow.TT4330.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/TT4330/HighLimit"))
                    self.AlarmButton.SubWindow.TT4330.High_Limit.UpdateValue()
                    self.AlarmButton.SubWindow.PT4306.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/PT4306/HighLimit"))
                    self.AlarmButton.SubWindow.PT4306.High_Limit.UpdateValue()
                    self.AlarmButton.SubWindow.PT4315.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/PT4315/HighLimit"))
                    self.AlarmButton.SubWindow.PT4315.High_Limit.UpdateValue()
                    self.AlarmButton.SubWindow.PT4319.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/PT4319/HighLimit"))
                    self.AlarmButton.SubWindow.PT4319.High_Limit.UpdateValue()
                    self.AlarmButton.SubWindow.PT4322.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/PT4322/HighLimit"))
                    self.AlarmButton.SubWindow.PT4322.High_Limit.UpdateValue()
                    self.AlarmButton.SubWindow.PT4325.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/SubWindow/PT4325/HighLimit"))
                    self.AlarmButton.SubWindow.PT4325.High_Limit.UpdateValue()

                except:
                    print("Wrong Path to recover")
        except:
            print("1st time run the code in this environment. "
                  "Nothing to recover the settings. Please save the configuration to a ini file")
            pass

    def RecoverChecked(self, GUIid, subdir, loadedsettings=None):
        # add a function because you can not directly set check status to checkbox
        # GUIid should be form of "self.AlarmButton.SubWindow.PT4315", is the variable name in the Main window
        # subdir like ""MainWindow/AlarmButton/SubWindow/PT4306/CheckBox"", is the path file stored in the ini file
        # loadedsettings is the Qtsettings file the program is to load
        if loadedsettings is None:
            # It is weired here, when I save the data and close the program, the setting value
            # in the address is string true
            # while if you maintain the program, the setting value in the address is bool True
            if self.settings.value(subdir) == "true" or self.settings.value(subdir) == True:
                GUIid.AlarmMode.setChecked(True)
            elif self.settings.value(subdir) == "false" or self.settings.value(subdir) == False:
                GUIid.AlarmMode.setChecked(False)
            else:
                print("Checkbox's value is neither true nor false")
        else:
            try:
                if loadedsettings.value(subdir) == "True" or loadedsettings.value(subdir) == True:
                    GUIid.AlarmMode.setChecked(True)
                elif self.settings.value(subdir) == "false" or loadedsettings.value(subdir) == False:
                    GUIid.AlarmMode.setChecked(False)
                else:
                    print("Checkbox's value is neither true nor false")
            except:
                print("Failed to load the status of checkboxs")


# Defines a reusable layout containing widgets
class RegionPID(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        self.Label.setStyleSheet("QLabel {" +TITLE_STYLE+"}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.addLayout(self.HL)

        self.Mode = Toggle(self)
        self.Mode.Label.setText("Mode")
        self.Mode.SetToggleStateNames("Auto", "Manual")
        self.HL.addWidget(self.Mode)

        self.Setpoint = Control(self)
        self.Setpoint.Label.setText("Setpoint")
        self.HL.addWidget(self.Setpoint)

        self.P = Control(self)
        self.P.Label.setText("P")
        self.P.Unit = ""
        self.P.Max = 20.
        self.P.Min = 0.
        self.P.Step = 0.1
        self.P.Decimals = 1
        self.HL.addWidget(self.P)

        self.I = Control(self)
        self.I.Label.setText("I")
        self.I.Unit = ""
        self.I.Max = 20.
        self.I.Min = 0.
        self.I.Step = 0.1
        self.I.Decimals = 1
        self.HL.addWidget(self.I)

        self.D = Control(self)
        self.D.Label.setText("D")
        self.D.Unit = ""
        self.D.Max = 20.
        self.D.Min = 0.
        self.D.Step = 0.1
        self.D.Decimals = 1
        self.HL.addWidget(self.D)


class ThermosyphonWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(2000*R, 1000*R)
        self.setMinimumSize(2000*R, 1000*R)
        self.setWindowTitle("Thermosyphon")

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2000*R, 1000*R))

        # reset the size of the window
        self.setMinimumSize(2000*R, 500*R)
        self.resize(1000*R, 500*R)
        self.setWindowTitle("Thermosyphon Status Window")
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2000*R, 500*R))

        # set gridlayout
        self.GL = QtWidgets.QGridLayout()
        # self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GL.setSpacing(20*R)
        self.GL.setAlignment(QtCore.Qt.AlignCenter)

        self.Widget.setLayout(self.GL)

        self.PV4307 = MultiStatusIndicator(self)
        self.PV4307.Label.setText("PV4307")
        self.GL.addWidget(self.PV4307, 0, 0)

        self.PV4308 = MultiStatusIndicator(self)
        self.PV4308.Label.setText("PV4308")
        self.GL.addWidget(self.PV4308, 0, 1)

        self.PV4317 = MultiStatusIndicator(self)
        self.PV4317.Label.setText("PV4317")
        self.GL.addWidget(self.PV4317, 0, 2)

        self.PV4318 = MultiStatusIndicator(self)
        self.PV4318.Label.setText("PV4318")
        self.GL.addWidget(self.PV4318, 0, 3)

        self.PV4321 = MultiStatusIndicator(self)
        self.PV4321.Label.setText("PV4321")
        self.GL.addWidget(self.PV4321, 0, 4)

        self.PV4324 = MultiStatusIndicator(self)
        self.PV4324.Label.setText("PV4324")
        self.GL.addWidget(self.PV4324, 0, 5)

        self.SV4327 = MultiStatusIndicator(self)
        self.SV4327.Label.setText("SV4327")
        self.GL.addWidget(self.SV4327, 1, 0)

        self.SV4328 = MultiStatusIndicator(self)
        self.SV4328.Label.setText("SV4328.")
        self.GL.addWidget(self.SV4328, 1, 1)

        self.SV4329 = MultiStatusIndicator(self)
        self.SV4329.Label.setText("SV4329")
        self.GL.addWidget(self.SV4329, 1, 2)

        self.SV4331 = MultiStatusIndicator(self)
        self.SV4331.Label.setText("SV4331")
        self.GL.addWidget(self.SV4331, 1, 3)

        self.SV4332 = MultiStatusIndicator(self)
        self.SV4332.Label.setText("SV4332")
        self.GL.addWidget(self.SV4332, 1, 4)


class RTDset1(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(2000*R, 1000*R)
        self.setMinimumSize(2000*R, 1000*R)
        self.setWindowTitle("Status Window")

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2000*R, 1000*R))

        # reset the size of the window
        self.setMinimumSize(1000*R, 500*R)
        self.resize(1000*R, 500*R)
        self.setWindowTitle("RTD SET 1")
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1000*R, 500*R))

        # set gridlayout
        self.GL = QtWidgets.QGridLayout()
        # self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GL.setSpacing(20*R)
        self.GL.setAlignment(QtCore.Qt.AlignCenter)

        self.Widget.setLayout(self.GL)

        self.TT2111 = Indicator(self)
        self.TT2111.Label.setText("TT2111")
        self.GL.addWidget(self.TT2111, 0, 0)

        self.TT2112 = Indicator(self)
        self.TT2112.Label.setText("TT2112")
        self.GL.addWidget(self.TT2112, 0, 1)

        self.TT2113 = Indicator(self)
        self.TT2113.Label.setText("TT2113")
        self.GL.addWidget(self.TT2113, 0, 2)

        self.TT2114 = Indicator(self)
        self.TT2114.Label.setText("TT2114")
        self.GL.addWidget(self.TT2114, 0, 3)

        self.TT2115 = Indicator(self)
        self.TT2115.Label.setText("TT2115")
        self.GL.addWidget(self.TT2115, 0, 4)

        self.TT2116 = Indicator(self)
        self.TT2116.Label.setText("TT2116")
        self.GL.addWidget(self.TT2116, 1, 0)

        self.TT2117 = Indicator(self)
        self.TT2117.Label.setText("TT2117")
        self.GL.addWidget(self.TT2117, 1, 1)

        self.TT2118 = Indicator(self)
        self.TT2118.Label.setText("TT2118")
        self.GL.addWidget(self.TT2118, 1, 2)

        self.TT2119 = Indicator(self)
        self.TT2119.Label.setText("TT2119")
        self.GL.addWidget(self.TT2119, 1, 3)

        self.TT2120 = Indicator(self)
        self.TT2120.Label.setText("TT2120")
        self.GL.addWidget(self.TT2120, 1, 4)


class RTDset2(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2000*R, 1000*R))

        # reset the size of the window
        self.setMinimumSize(1000*R, 500*R)
        self.resize(1000*R, 500*R)
        self.setWindowTitle("RTD SET 2")
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1000*R, 500*R))

        # set gridlayout
        self.GL = QtWidgets.QGridLayout()
        # self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GL.setSpacing(20*R)
        self.GL.setAlignment(QtCore.Qt.AlignCenter)

        self.Widget.setLayout(self.GL)

        self.TT2401 = Indicator(self)
        self.TT2401.Label.setText("TT2401")
        self.GL.addWidget(self.TT2401, 0, 0)

        self.TT2402 = Indicator(self)
        self.TT2402.Label.setText("TT2402")
        self.GL.addWidget(self.TT2402, 0, 1)

        self.TT2403 = Indicator(self)
        self.TT2403.Label.setText("TT2403")
        self.GL.addWidget(self.TT2403, 0, 2)

        self.TT2404 = Indicator(self)
        self.TT2404.Label.setText("TT2404")
        self.GL.addWidget(self.TT2404, 0, 3)

        self.TT2405 = Indicator(self)
        self.TT2405.Label.setText("TT2405")
        self.GL.addWidget(self.TT2405, 0, 4)

        self.TT2406 = Indicator(self)
        self.TT2406.Label.setText("TT2406")
        self.GL.addWidget(self.TT2406, 1, 0)

        self.TT2407 = Indicator(self)
        self.TT2407.Label.setText("TT2407")
        self.GL.addWidget(self.TT2407, 1, 1)

        self.TT2408 = Indicator(self)
        self.TT2408.Label.setText("TT2408")
        self.GL.addWidget(self.TT2408, 1, 2)

        self.TT2409 = Indicator(self)
        self.TT2409.Label.setText("TT2409")
        self.GL.addWidget(self.TT2409, 1, 3)

        self.TT2410 = Indicator(self)
        self.TT2410.Label.setText("TT2410")
        self.GL.addWidget(self.TT2410, 1, 4)

        self.TT2411 = Indicator(self)
        self.TT2411.Label.setText("TT2411")
        self.GL.addWidget(self.TT2411, 2, 0)

        self.TT2412 = Indicator(self)
        self.TT2412.Label.setText("TT2412")
        self.GL.addWidget(self.TT2412, 2, 1)

        self.TT2413 = Indicator(self)
        self.TT2413.Label.setText("TT2413")
        self.GL.addWidget(self.TT2413, 2, 2)

        self.TT2414 = Indicator(self)
        self.TT2414.Label.setText("TT2414")
        self.GL.addWidget(self.TT2414, 2, 3)

        self.TT2415 = Indicator(self)
        self.TT2415.Label.setText("TT2415")
        self.GL.addWidget(self.TT2415, 2, 4)

        self.TT2416 = Indicator(self)
        self.TT2416.Label.setText("TT2416")
        self.GL.addWidget(self.TT2416, 3, 0)

        self.TT2417 = Indicator(self)
        self.TT2417.Label.setText("TT2417")
        self.GL.addWidget(self.TT2417, 3, 1)

        self.TT2418 = Indicator(self)
        self.TT2418.Label.setText("TT2418")
        self.GL.addWidget(self.TT2418, 3, 2)

        self.TT2419 = Indicator(self)
        self.TT2419.Label.setText("TT2419")
        self.GL.addWidget(self.TT2419, 3, 3)

        self.TT2420 = Indicator(self)
        self.TT2420.Label.setText("TT2420")
        self.GL.addWidget(self.TT2420, 3, 4)

        self.TT2421 = Indicator(self)
        self.TT2421.Label.setText("TT2421")
        self.GL.addWidget(self.TT2421, 4, 0)

        self.TT2422 = Indicator(self)
        self.TT2422.Label.setText("TT2422")
        self.GL.addWidget(self.TT2422, 4, 1)

        self.TT2423 = Indicator(self)
        self.TT2423.Label.setText("TT2423")
        self.GL.addWidget(self.TT2423, 4, 2)

        self.TT2424 = Indicator(self)
        self.TT2424.Label.setText("TT2424")
        self.GL.addWidget(self.TT2424, 4, 3)

        self.TT2425 = Indicator(self)
        self.TT2425.Label.setText("TT2425")
        self.GL.addWidget(self.TT2425, 4, 4)

        self.TT2426 = Indicator(self)
        self.TT2426.Label.setText("TT2426")
        self.GL.addWidget(self.TT2426, 5, 0)

        self.TT2427 = Indicator(self)
        self.TT2427.Label.setText("TT2427")
        self.GL.addWidget(self.TT2427, 5, 1)

        self.TT2428 = Indicator(self)
        self.TT2428.Label.setText("TT2428")
        self.GL.addWidget(self.TT2428, 5, 2)

        self.TT2429 = Indicator(self)
        self.TT2429.Label.setText("TT2429")
        self.GL.addWidget(self.TT2429, 5, 3)

        self.TT2430 = Indicator(self)
        self.TT2430.Label.setText("TT2430")
        self.GL.addWidget(self.TT2430, 5, 4)

        self.TT2431 = Indicator(self)
        self.TT2431.Label.setText("TT2431")
        self.GL.addWidget(self.TT2431, 6, 0)

        self.TT2432 = Indicator(self)
        self.TT2432.Label.setText("TT2432")
        self.GL.addWidget(self.TT2432, 6, 1)

        self.GroupBox = QtWidgets.QGroupBox(self.Widget)
        self.GroupBox.setTitle("RTD SET2")
        self.GroupBox.setLayout(self.GL)
        self.GroupBox.setStyleSheet("background-color:transparent;")


class RTDset3(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(2000*R, 1000*R)
        self.setMinimumSize(2000*R, 1000*R)
        self.setWindowTitle("Status Window")

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2000*R, 1000*R))

        # reset the size of the window
        self.setMinimumSize(1000*R, 500*R)
        self.resize(1000*R, 500*R)
        self.setWindowTitle("RTD SET 3")
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1000*R, 500*R))

        # set gridlayout
        self.GL = QtWidgets.QGridLayout()
        # self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GL.setSpacing(20*R)
        self.GL.setAlignment(QtCore.Qt.AlignCenter)

        self.Widget.setLayout(self.GL)

        self.TT2435 = Indicator(self)
        self.TT2435.Label.setText("TT2435")
        self.GL.addWidget(self.TT2435, 0, 0)

        self.TT2436 = Indicator(self)
        self.TT2436.Label.setText("TT2436")
        self.GL.addWidget(self.TT2436, 0, 1)

        self.TT2437 = Indicator(self)
        self.TT2437.Label.setText("TT2437")
        self.GL.addWidget(self.TT2437, 0, 2)

        self.TT2438 = Indicator(self)
        self.TT2438.Label.setText("TT2438")
        self.GL.addWidget(self.TT2438, 0, 3)

        self.TT2439 = Indicator(self)
        self.TT2439.Label.setText("TT2439")
        self.GL.addWidget(self.TT2439, 0, 4)

        self.TT2440 = Indicator(self)
        self.TT2440.Label.setText("TT2440")
        self.GL.addWidget(self.TT2440, 1, 0)

        self.TT2441 = Indicator(self)
        self.TT2441.Label.setText("TT2441")
        self.GL.addWidget(self.TT2441, 1, 1)

        self.TT2442 = Indicator(self)
        self.TT2442.Label.setText("TT2442")
        self.GL.addWidget(self.TT2442, 1, 2)

        self.TT2443 = Indicator(self)
        self.TT2443.Label.setText("TT2443")
        self.GL.addWidget(self.TT2443, 1, 3)

        self.TT2444 = Indicator(self)
        self.TT2444.Label.setText("TT2444")
        self.GL.addWidget(self.TT2444, 1, 4)

        self.TT2445 = Indicator(self)
        self.TT2445.Label.setText("TT2445")
        self.GL.addWidget(self.TT2445, 2, 0)

        self.TT2446 = Indicator(self)
        self.TT2446.Label.setText("TT2446")
        self.GL.addWidget(self.TT2446, 2, 1)

        self.TT2447 = Indicator(self)
        self.TT2447.Label.setText("TT2447")
        self.GL.addWidget(self.TT2447, 2, 2)

        self.TT2448 = Indicator(self)
        self.TT2448.Label.setText("TT2448")
        self.GL.addWidget(self.TT2448, 2, 3)

        self.TT2449 = Indicator(self)
        self.TT2449.Label.setText("TT2449")
        self.GL.addWidget(self.TT2449, 2, 4)

        self.TT2450 = Indicator(self)
        self.TT2450.Label.setText("TT2450")
        self.GL.addWidget(self.TT2450, 3, 0)


class RTDset4(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(2000*R, 1000*R)
        self.setMinimumSize(2000*R, 1000*R)
        self.setWindowTitle("Status Window")

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2000*R, 1000*R))

        # reset the size of the window
        self.setMinimumSize(1000*R, 500*R)
        self.resize(1000*R, 500*R)
        self.setWindowTitle("RTD SET 4")
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1000*R, 500*R))

        # set gridlayout
        self.GL = QtWidgets.QGridLayout()
        # self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GL.setSpacing(20*R)
        self.GL.setAlignment(QtCore.Qt.AlignCenter)

        self.Widget.setLayout(self.GL)

        self.TT2101 = Indicator(self)
        self.TT2101.Label.setText("TT2101")
        self.GL.addWidget(self.TT2101, 0, 0)

        self.TT2102 = Indicator(self)
        self.TT2102.Label.setText("TT2102")
        self.GL.addWidget(self.TT2102, 0, 1)

        self.TT2103 = Indicator(self)
        self.TT2103.Label.setText("TT2103")
        self.GL.addWidget(self.TT2103, 0, 2)

        self.TT2104 = Indicator(self)
        self.TT2104.Label.setText("TT2104")
        self.GL.addWidget(self.TT2104, 0, 3)

        self.TT2105 = Indicator(self)
        self.TT2105.Label.setText("TT2105")
        self.GL.addWidget(self.TT2105, 0, 4)

        self.TT2106 = Indicator(self)
        self.TT2106.Label.setText("TT2106")
        self.GL.addWidget(self.TT2106, 1, 0)

        self.TT2107 = Indicator(self)
        self.TT2107.Label.setText("TT2107")
        self.GL.addWidget(self.TT2107, 1, 1)

        self.TT2108 = Indicator(self)
        self.TT2108.Label.setText("TT2108")
        self.GL.addWidget(self.TT2108, 1, 2)

        self.TT2109 = Indicator(self)
        self.TT2109.Label.setText("TT2109")
        self.GL.addWidget(self.TT2109, 1, 3)

        self.TT2110 = Indicator(self)
        self.TT2110.Label.setText("TT2110")
        self.GL.addWidget(self.TT2110, 1, 4)


class AlarmWin(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2000*R, 1000*R))

        # reset the size of the window
        self.setMinimumSize(2000*R, 1100*R)
        self.resize(2000*R, 1100*R)
        self.setWindowTitle("Alarm Window")
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2000*R, 1100*R))

        self.Tab = QtWidgets.QTabWidget(self)
        self.Tab.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.Tab.setStyleSheet("font-weight: bold; font-size: 20px; font-family: Calibri;")
        self.Tab.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.Tab.setGeometry(QtCore.QRect(0*R, 0*R, 2400*R, 1400*R))

        self.PressureTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.PressureTab, "Pressure Transducers")

        self.RTDSET12Tab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDSET12Tab, "RTD SET 1&2")

        self.RTDSET34Tab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDSET34Tab, "RTD SET 3&4")

        self.RTDLEFTTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDLEFTTab, "HEATER RTDs and ETC")

        # Groupboxs for alarm/PT/TT

        self.GLPT = QtWidgets.QGridLayout()
        # self.GLPT = QtWidgets.QGridLayout(self)
        self.GLPT.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLPT.setSpacing(20*R)
        self.GLPT.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupPT = QtWidgets.QGroupBox(self.PressureTab)
        self.GroupPT.setTitle("Pressure Transducer")
        self.GroupPT.setLayout(self.GLPT)
        self.GroupPT.move(0*R, 0*R)

        self.GLRTD1 = QtWidgets.QGridLayout()
        # self.GLRTD1 = QtWidgets.QGridLayout(self)
        self.GLRTD1.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLRTD1.setSpacing(20*R)
        self.GLRTD1.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTD1 = QtWidgets.QGroupBox(self.RTDSET12Tab)
        self.GroupRTD1.setTitle("RTD SET 1")
        self.GroupRTD1.setLayout(self.GLRTD1)
        self.GroupRTD1.move(0*R, 0*R)

        self.GLRTD2 = QtWidgets.QGridLayout()
        # self.GLRTD2 = QtWidgets.QGridLayout(self)
        self.GLRTD2.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLRTD2.setSpacing(20*R)
        self.GLRTD2.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTD2 = QtWidgets.QGroupBox(self.RTDSET12Tab)
        self.GroupRTD2.setTitle("RTD SET 2")
        self.GroupRTD2.setLayout(self.GLRTD2)
        self.GroupRTD2.move(0*R, 300*R)

        self.GLRTD3 = QtWidgets.QGridLayout()
        # self.GLRTD3 = QtWidgets.QGridLayout(self)
        self.GLRTD3.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLRTD3.setSpacing(20*R)
        self.GLRTD3.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTD3 = QtWidgets.QGroupBox(self.RTDSET34Tab)
        self.GroupRTD3.setTitle("RTD SET 3")
        self.GroupRTD3.setLayout(self.GLRTD3)
        self.GroupRTD3.move(0*R, 0*R)

        self.GLRTD4 = QtWidgets.QGridLayout()
        # self.GLRTD4 = QtWidgets.QGridLayout(self)
        self.GLRTD4.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLRTD4.setSpacing(20*R)
        self.GLRTD4.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTD4 = QtWidgets.QGroupBox(self.RTDSET34Tab)
        self.GroupRTD4.setTitle("RTD SET 4")
        self.GroupRTD4.setLayout(self.GLRTD4)
        self.GroupRTD4.move(0*R, 500*R)

        self.GLRTDLEFT = QtWidgets.QGridLayout()
        # self.GLRTDLEFT = QtWidgets.QGridLayout(self)
        self.GLRTDLEFT.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLRTDLEFT.setSpacing(20*R)
        self.GLRTDLEFT.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTDLEFT = QtWidgets.QGroupBox(self.RTDLEFTTab)
        self.GroupRTDLEFT.setTitle(" LEFT RTDs ")
        self.GroupRTDLEFT.setLayout(self.GLRTDLEFT)
        self.GroupRTDLEFT.move(0*R, 0*R)

        self.TT2111 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2111.Label.setText("TT2111")

        self.TT2112 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2112.Label.setText("TT2112")

        self.TT2113 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2113.Label.setText("TT2113")

        self.TT2114 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2114.Label.setText("TT2114")

        self.TT2115 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2115.Label.setText("TT2115")

        self.TT2116 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2116.Label.setText("TT2116")

        self.TT2117 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2117.Label.setText("TT2117")

        self.TT2118 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2118.Label.setText("TT2118")

        self.TT2119 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2119.Label.setText("TT2119")

        self.TT2120 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2120.Label.setText("TT2120")

        self.TT2401 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2401.Label.setText("TT2401")

        self.TT2402 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2402.Label.setText("TT2402")

        self.TT2403 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2403.Label.setText("TT2403")

        self.TT2404 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2404.Label.setText("TT2404")

        self.TT2405 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2405.Label.setText("TT2405")

        self.TT2406 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2406.Label.setText("TT2406")

        self.TT2407 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2407.Label.setText("TT2407")

        self.TT2408 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2408.Label.setText("TT2408")

        self.TT2409 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2409.Label.setText("TT2409")

        self.TT2410 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2410.Label.setText("TT2410")

        self.TT2411 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2411.Label.setText("TT2411")

        self.TT2412 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2412.Label.setText("TT2412")

        self.TT2413 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2413.Label.setText("TT2413")

        self.TT2414 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2414.Label.setText("TT2414")

        self.TT2415 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2415.Label.setText("TT2415")

        self.TT2416 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2416.Label.setText("TT2416")

        self.TT2417 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2417.Label.setText("TT2417")

        self.TT2418 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2418.Label.setText("TT2418")

        self.TT2419 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2419.Label.setText("TT2419")

        self.TT2420 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2420.Label.setText("TT2420")

        self.TT2421 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2421.Label.setText("TT2421")

        self.TT2422 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2422.Label.setText("TT2422")

        self.TT2423 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2423.Label.setText("TT2423")

        self.TT2424 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2424.Label.setText("TT2424")

        self.TT2425 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2425.Label.setText("TT2425")

        self.TT2426 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2426.Label.setText("TT2426")

        self.TT2427 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2427.Label.setText("TT2427")

        self.TT2428 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2428.Label.setText("TT2428")

        self.TT2429 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2429.Label.setText("TT2429")

        self.TT2430 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2430.Label.setText("TT2430")

        self.TT2431 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2431.Label.setText("TT2431")

        self.TT2432 = AlarmStatusWidget(self.RTDSET12Tab)
        self.TT2432.Label.setText("TT2432")

        # RTDSET34
        self.TT2435 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2435.Label.setText("TT2435")

        self.TT2436 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2436.Label.setText("TT2436")

        self.TT2437 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2437.Label.setText("TT2437")

        self.TT2438 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2438.Label.setText("TT2438")

        self.TT2439 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2439.Label.setText("TT2439")

        self.TT2440 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2440.Label.setText("TT2440")

        self.TT2441 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2441.Label.setText("TT2441")

        self.TT2442 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2442.Label.setText("TT2442")

        self.TT2443 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2443.Label.setText("TT2443")

        self.TT2444 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2444.Label.setText("TT2444")

        self.TT2445 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2445.Label.setText("TT2445")

        self.TT2446 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2446.Label.setText("TT2446")

        self.TT2447 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2447.Label.setText("TT2447")

        self.TT2448 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2448.Label.setText("TT2448")

        self.TT2449 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2449.Label.setText("TT2449")

        self.TT2450 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2450.Label.setText("TT2450")

        self.TT2101 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2101.Label.setText("TT2101")

        self.TT2102 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2102.Label.setText("TT2102")

        self.TT2103 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2103.Label.setText("TT2103")

        self.TT2104 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2104.Label.setText("TT2104")

        self.TT2105 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2105.Label.setText("TT2105")

        self.TT2106 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2106.Label.setText("TT2106")

        self.TT2107 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2107.Label.setText("TT2107")

        self.TT2108 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2108.Label.setText("TT2108")

        self.TT2109 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2109.Label.setText("TT2109")

        self.TT2110 = AlarmStatusWidget(self.RTDSET34Tab)
        self.TT2110.Label.setText("TT2110")

        # RTDLEFT part

        self.TT4330 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT4330.Label.setText("TT4330")

        self.TT6220 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6220.Label.setText("TT6220")

        self.TT6213 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6213.Label.setText("TT6213")

        self.TT6401 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6401.Label.setText("TT6401")

        self.TT6203 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6203.Label.setText("TT6203")

        self.TT6404 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6404.Label.setText("TT6404")

        self.TT6207 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6207.Label.setText("TT6207")

        self.TT6405 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6405.Label.setText("TT6405")

        self.TT6211 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6211.Label.setText("TT6211")

        self.TT6406 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6406.Label.setText("TT6406")

        self.TT6222 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6222.Label.setText("TT6222")

        self.TT6223 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6223.Label.setText("TT6223")


        self.TT6410 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6410.Label.setText("TT6410")

        self.TT6407 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6407.Label.setText("TT6407")

        self.TT6408 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6408.Label.setText("TT6408")

        self.TT6409 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6409.Label.setText("TT6409")

        self.TT6411 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6411.Label.setText("TT6411")

        self.TT6412 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6412.Label.setText("TT6412")

        self.TT6413 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6413.Label.setText("TT6413")

        self.TT6414 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6414.Label.setText("TT6414")

        self.TT6415 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6415.Label.setText("TT6415")

        self.TT6416 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6416.Label.setText("TT6416")

        self.TT7202 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT7202.Label.setText("TT7202")

        self.TT7401 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT7401.Label.setText("TT7401")

        self.TT3402 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT3402.Label.setText("TT3402")

        self.TT3401 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT3401.Label.setText("TT3401")

        self.TT7403 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT7403.Label.setText("TT7403")

        # PT part
        self.PT1101 = AlarmStatusWidget(self.PressureTab)
        self.PT1101.Label.setText("PT1101")

        self.PT2316 = AlarmStatusWidget(self.PressureTab)
        self.PT2316.Label.setText("PT2316")

        self.PT2321 = AlarmStatusWidget(self.PressureTab)
        self.PT2321.Label.setText("PT2321")

        self.PT2330 = AlarmStatusWidget(self.PressureTab)
        self.PT2330.Label.setText("PT2330")

        self.PT2335 = AlarmStatusWidget(self.PressureTab)
        self.PT2335.Label.setText("PT2335")

        self.PT3308 = AlarmStatusWidget(self.PressureTab)
        self.PT3308.Label.setText("PT3308")

        self.PT3309 = AlarmStatusWidget(self.PressureTab)
        self.PT3309.Label.setText("PT3309")

        self.PT3310 = AlarmStatusWidget(self.PressureTab)
        self.PT3310.Label.setText("PT3310")

        self.PT3311 = AlarmStatusWidget(self.PressureTab)
        self.PT3311.Label.setText("PT3311")

        self.PT3314 = AlarmStatusWidget(self.PressureTab)
        self.PT3314.Label.setText("PT3314")

        self.PT3320 = AlarmStatusWidget(self.PressureTab)
        self.PT3320.Label.setText("PT3320")

        self.PT3333 = AlarmStatusWidget(self.PressureTab)
        self.PT3333.Label.setText("PT3333")

        self.PT4306 = AlarmStatusWidget(self.PressureTab)
        self.PT4306.Label.setText("PT4306")

        self.PT4315 = AlarmStatusWidget(self.PressureTab)
        self.PT4315.Label.setText("PT4315")

        self.PT4319 = AlarmStatusWidget(self.PressureTab)
        self.PT4319.Label.setText("PT4319")

        self.PT4322 = AlarmStatusWidget(self.PressureTab)
        self.PT4322.Label.setText("PT4322")

        self.PT4325 = AlarmStatusWidget(self.PressureTab)
        self.PT4325.Label.setText("PT4325")

        # make a directory for the alarm instrument and assign instrument to certain position
        self.AlarmRTD1dir = {0: {0: self.TT2111, 1: self.TT2112, 2: self.TT2113, 3: self.TT2114, 4: self.TT2115},
                             1: {0: self.TT2116, 1: self.TT2117, 2: self.TT2118, 3: self.TT2119, 4: self.TT2120}}

        self.AlarmRTD1list1D = [self.TT2111, self.TT2112, self.TT2113,  self.TT2114,  self.TT2115, self.TT2116,
                               self.TT2117, self.TT2118, self.TT2119,  self.TT2120]

        self.AlarmRTD2dir = {0: {0: self.TT2401, 1: self.TT2402, 2: self.TT2403, 3: self.TT2404, 4: self.TT2405},
                             1: {0: self.TT2406, 1: self.TT2407, 2: self.TT2408, 3: self.TT2409, 4: self.TT2410},
                             2: {0: self.TT2411, 1: self.TT2412, 2: self.TT2413, 3: self.TT2414, 4: self.TT2415},
                             3: {0: self.TT2416, 1: self.TT2417, 2: self.TT2418, 3: self.TT2419, 4: self.TT2420},
                             4: {0: self.TT2421, 1: self.TT2422, 2: self.TT2423, 3: self.TT2424, 4: self.TT2425},
                             5: {0: self.TT2426, 1: self.TT2427, 2: self.TT2428, 3: self.TT2429, 4: self.TT2430},
                             6: {0: self.TT2431, 1: self.TT2432}}


        self.AlarmRTD3dir = {0: {0: self.TT2435, 1: self.TT2436, 2: self.TT2437, 3: self.TT2438, 4: self.TT2439},
                             1: {0: self.TT2440, 1: self.TT2441, 2: self.TT2442, 3: self.TT2443, 4: self.TT2444},
                             2: {0: self.TT2445, 1: self.TT2446, 2: self.TT2447, 3: self.TT2448, 4: self.TT2449},
                             3: {0: self.TT2450}}

        self.AlarmRTD4dir = {0: {0: self.TT2101, 1: self.TT2102, 2: self.TT2103, 3: self.TT2104, 4: self.TT2105},
                             1: {0: self.TT2106, 1: self.TT2107, 2: self.TT2108, 3: self.TT2109, 4: self.TT2110}}

        self.AlarmPTdir = {0: {0: self.PT1101, 1: self.PT2316, 2: self.PT2321, 3: self.PT2330, 4: self.PT2335},
                           1: {0: self.PT3308, 1: self.PT3309, 2: self.PT3310, 3: self.PT3311, 4: self.PT3314},
                           2: {0: self.PT3320, 1: self.PT3333, 2: self.PT4306, 3: self.PT4315, 4: self.PT4319},
                           3: {0: self.PT4322, 1: self.PT4325}}

        self.AlarmRTDLEFTdir = {0: {0: self.TT4330, 1: self.TT6220, 2: self.TT6213, 3: self.TT6401, 4: self.TT6203},
                                1: {0: self.TT6404, 1: self.TT6207, 2: self.TT6405, 3: self.TT6211, 4: self.TT6406},
                                2: {0: self.TT6223, 1: self.TT6410, 2: self.TT6408, 3: self.TT6409, 4: self.TT6412},
                                3: {0: self.TT3402, 1: self.TT3401, 2: self.TT7401, 3: self.TT7202, 4: self.TT7403},
                                4: {0: self.TT6222, 1: self.TT6407, 2: self.TT6415, 3: self.TT6416, 4: self.TT6411},
                                5: {0: self.TT6413, 1: self.TT6414}}

        # self.AlarmRTD1dir = {0: {0: "self.TT2111", 1: "self.TT2112", 2: "self.TT2113", 3: "self.TT2114", 4: "self.TT2115"},
        #                      1: {0: "self.TT2116", 1: "self.TT2117", 2: "self.TT2118", 3: "self.TT2119", 4: "self.TT2120"}}

        # self.AlarmRTD2dir = {0: {0: "self.TT2401", 1: "self.TT2402", 2: "self.TT2403", 3: "self.TT2404", 4: "self.TT2405"},
        #                      1: {0: "self.TT2406", 1: "self.TT2407", 2: "self.TT2408", 3: "self.TT2409", 4: "self.TT2410"},
        #                      2: {0: "self.TT2411", 1: "self.TT2412", 2: "self.TT2413", 3: "self.TT2414", 4: "self.TT2415"},
        #                      3: {0: "self.TT2416", 1: "self.TT2417", 2: "self.TT2418", 3: "self.TT2419", 4: "self.TT2420"},
        #                      4: {0: "self.TT2421", 1: "self.TT2422", 2: "self.TT2423", 3: "self.TT2424", 4: "self.TT2425"},
        #                      5: {0: "self.TT2426", 1: "self.TT2427", 2: "self.TT2428", 3: "self.TT2429", 4: "self.TT2430"},
        #                      6: {0: "self.TT2431", 1: "self.TT2432"}}

        # self.AlarmRTD3dir = {0: {0: "self.TT2435", 1: "self.TT2436", 2: "self.TT2437", 3: "self.TT2438", 4: "self.TT2439"},
        #                      1: {0: "self.TT2440", 1: "self.TT2441", 2: "self.TT2442", 3: "self.TT2443", 4: "self.TT2444"},
        #                      2: {0: "self.TT2445", 1: "self.TT2446", 2: "self.TT2447", 3: "self.TT2448", 4: "self.TT2449"}}
        #
        # self.AlarmRTD4dir = {0: {0: "self.TT2101", 1: "self.TT2102", 2: "self.TT2103", 3: "self.TT2104", 4: "self.TT2105"},
        #                      1: {0: "self.TT2106", 1: "self.TT2107", 2: "self.TT2108", 3: "self.TT2109", 4: "self.TT2110"}}
        #
        # self.AlarmPTdir = {0: {0: "self.PT1101", 1: "self.PT2316", 2: "self.PT2321", 3: "self.PT2330", 4: "self.PT2335"},
        #                    1: {0: "self.PT3308", 1: "self.PT3309", 2: "self.PT3310", 3: "self.PT3311", 4: "self.PT3314"},
        #                    2: {0: "self.PT3320", 1: "self.PT3333", 2: "self.PT4306", 3: "self.PT4315", 4: "self.PT4319"},
        #                    3: {0: "self.PT4322", 1: "self.PT4325"}}
        #
        # self.AlarmRTDLEFTdir = {0: {0: "self.TT4330", 1: "self.TT6220", 2: "self.TT6213", 3: "self.TT6401", 4: "self.TT6215"},
        #                         1: {0: "self.TT6402", 1: "self.TT6217", 2: "self.TT6403", 3: "self.TT6203", 4: "self.TT6404"},
        #                         2: {0: "self.TT6207", 1: "self.TT6405", 2: "self.TT6211", 3: "self.TT6406", 4: "self.TT6223"},
        #                         3: {0: "self.TT6410", 1: "self.TT6408", 2: "self.TT6409", 3: "self.TT6412", 4: "self.TT7202"},
        #                         4: {0: "self.TT7401", 1: "self.TT3402", 2: "self.TT3401", 3: "self.TT7403"}}

        # variables usable for building widgets
        # i is row number, j is column number
        # RTD1 is for temperature transducer while PT is for pressure transducer
        # max is max row and column number
        # last is the last widget's row and column index in gridbox
        self.i_RTD1_max = len(self.AlarmRTD1dir)
        # which is 2
        self.j_RTD1_max = len(self.AlarmRTD1dir[0])
        # which is 5
        self.i_RTD2_max = len(self.AlarmRTD2dir)
        self.j_RTD2_max = len(self.AlarmRTD2dir[0])
        self.i_RTD3_max = len(self.AlarmRTD3dir)
        self.j_RTD3_max = len(self.AlarmRTD3dir[0])
        self.i_RTD4_max = len(self.AlarmRTD4dir)
        self.j_RTD4_max = len(self.AlarmRTD4dir[0])
        self.i_RTDLEFT_max = len(self.AlarmRTDLEFTdir)
        self.j_RTDLEFT_max = len(self.AlarmRTDLEFTdir[0])

        self.i_PT_max = len(self.AlarmPTdir)
        # which is 4
        self.j_PT_max = len(self.AlarmPTdir[0])
        # which is 5
        self.i_RTD1_last = len(self.AlarmRTD1dir) - 1
        # which is 1
        self.j_RTD1_last = len(self.AlarmRTD1dir[self.i_RTD1_last]) - 1
        # which is 4
        self.i_RTD2_last = len(self.AlarmRTD2dir) - 1
        self.j_RTD2_last = len(self.AlarmRTD2dir[self.i_RTD2_last]) - 1
        self.i_RTD3_last = len(self.AlarmRTD3dir) - 1
        self.j_RTD3_last = len(self.AlarmRTD3dir[self.i_RTD3_last]) - 1
        self.i_RTD4_last = len(self.AlarmRTD4dir) - 1
        self.j_RTD4_last = len(self.AlarmRTD4dir[self.i_RTD4_last]) - 1
        self.i_RTDLEFT_last = len(self.AlarmRTDLEFTdir) - 1
        self.j_RTDLEFT_last = len(self.AlarmRTDLEFTdir[self.i_RTDLEFT_last]) - 1
        self.i_PT_last = len(self.AlarmPTdir) - 1
        # which is 3
        self.j_PT_last = len(self.AlarmPTdir[self.i_PT_last]) - 1
        # which is 1
        self.ResetOrder()

    @QtCore.Slot()
    def ResetOrder(self):
        for i in range(0, self.i_RTD1_max):
            for j in range(0, self.j_RTD1_max):
                # self.GLRTD1.addWidget(eval(self.AlarmRTD1dir[i][j]), i, j)
                self.GLRTD1.addWidget(self.AlarmRTD1dir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_RTD1_last, self.j_RTD1_last):
                    break
            if (i, j) == (self.i_RTD1_last, self.j_RTD1_last):
                break

        for i in range(0, self.i_RTD2_max):
            for j in range(0, self.j_RTD2_max):
                # self.GLRTD2.addWidget(eval(self.AlarmRTD2dir[i][j]), i, j)
                self.GLRTD2.addWidget(self.AlarmRTD2dir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_RTD2_last, self.j_RTD2_last):
                    break
            if (i, j) == (self.i_RTD2_last, self.j_RTD2_last):
                break

        for i in range(0, self.i_RTD3_max):
            for j in range(0, self.j_RTD3_max):
                # self.GLRTD3.addWidget(eval(self.AlarmRTD3dir[i][j]), i, j)
                self.GLRTD3.addWidget(self.AlarmRTD3dir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_RTD3_last, self.j_RTD3_last):
                    break
            if (i, j) == (self.i_RTD3_last, self.j_RTD3_last):
                break

        for i in range(0, self.i_RTD4_max):
            for j in range(0, self.j_RTD4_max):
                # self.GLRTD4.addWidget(eval(self.AlarmRTD4dir[i][j]), i, j)
                self.GLRTD4.addWidget(self.AlarmRTD4dir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_RTD4_last, self.j_RTD4_last):
                    break
            if (i, j) == (self.i_RTD4_last, self.j_RTD4_last):
                break

        for i in range(0, self.i_RTDLEFT_max):
            for j in range(0, self.j_RTDLEFT_max):
                # self.GLRTDLEFT.addWidget(eval(self.AlarmRTDLEFTdir[i][j]), i, j)
                self.GLRTDLEFT.addWidget(self.AlarmRTDLEFTdir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_RTDLEFT_last, self.j_RTDLEFT_last):
                    break
            if (i, j) == (self.i_RTDLEFT_last, self.j_RTDLEFT_last):
                break

        for i in range(0, self.i_PT_max):
            for j in range(0, self.j_PT_max):
                # self.GLPT.addWidget(eval(self.AlarmPTdir[i][j]), i, j)
                self.GLPT.addWidget(self.AlarmPTdir[i][j], i, j)
                # end the position generator when i= last element's row number -1, j= last element's column number
                if (i, j) == (self.i_PT_last, self.j_PT_last):
                    break
            if (i, j) == (self.i_PT_last, self.j_PT_last):
                break

    @QtCore.Slot()
    def ReassignRTD1Order(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate
        TempRefRTD1dir = self.AlarmRTD1dir
        TempRTD1dir = {0: {0: None, 1: None, 2: None, 3: None, 4: None},
                       1: {0: None, 1: None, 2: None, 3: None, 4: None}}

        # l_RTD1_max is max number of column
        l_RTD1 = 0
        k_RTD1 = 0

        # i_RTD1_max = 3
        # j_RTD1_max = 5
        # i_PT_max = 4
        # j_PT_max = 5
        # l_RTD1_max = 4
        # l_PT_max = 4
        # i_RTD1_last = 2
        # j_RTD1_last = 4
        # i_PT_last = 3
        # j_PT_last = 1
        i_RTD1_max = len(self.AlarmRTD1dir)
        # which is 3
        j_RTD1_max = len(self.AlarmRTD1dir[0])
        # which is 5

        i_RTD1_last = len(self.AlarmRTD1dir) - 1
        # which is 2
        j_RTD1_last = len(self.AlarmRTD1dir[i_RTD1_last]) - 1
        # which is 4
        # print(i_RTD1_max,j_RTD1_max,i_RTD1_last, j_RTD1_last)

        l_RTD1_max = j_RTD1_max - 1

        # RTD1 put alarm true widget to the begining of the diretory
        for i in range(0, i_RTD1_max):
            for j in range(0, j_RTD1_max):
                if TempRefRTD1dir[i][j].Alarm:
                    TempRTD1dir[k_RTD1][l_RTD1] = TempRefRTD1dir[i][j]
                    l_RTD1 = l_RTD1 + 1
                    if l_RTD1 == l_RTD1_max + 1:
                        l_RTD1 = 0
                        k_RTD1 = k_RTD1 + 1
                if (i, j) == (i_RTD1_last, j_RTD1_last):
                    break
            if (i, j) == (i_RTD1_last, j_RTD1_last):
                break
        # print("1st part")
        #
        #
        # # RTD1 put alarm false widget after that
        for i in range(0, i_RTD1_max):
            for j in range(0, j_RTD1_max):
                if not TempRefRTD1dir[i][j].Alarm:
                    TempRTD1dir[k_RTD1][l_RTD1] = TempRefRTD1dir[i][j]
                    l_RTD1 = l_RTD1 + 1
                    if l_RTD1 == l_RTD1_max + 1:
                        l_RTD1 = 0
                        k_RTD1 = k_RTD1 + 1
                if (i, j) == (i_RTD1_last, j_RTD1_last):
                    break
            if (i, j) == (i_RTD1_last, j_RTD1_last):
                break
        # print("2nd part")
        # Reassign position
        # end the position generator when i= last element's row number, j= last element's column number
        for i in range(0, i_RTD1_max):
            for j in range(0, j_RTD1_max):
                self.GLRTD1.addWidget(TempRTD1dir[i][j], i, j)
                if (i, j) == (i_RTD1_last, j_RTD1_last):
                    break
            if (i, j) == (i_RTD1_last, j_RTD1_last):
                break
        # print("3rd part")

    @QtCore.Slot()
    def ReassignRTD2Order(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate

        TempRefRTD2dir = self.AlarmRTD2dir

        TempRTD2dir = self.AlarmRTD2dir

        # l_RTD1_max is max number of column

        l_RTD2 = 0
        k_RTD2 = 0

        # i_RTD1_max = 3
        # j_RTD1_max = 5
        # i_PT_max = 4
        # j_PT_max = 5
        # l_RTD1_max = 4
        # l_PT_max = 4
        # i_RTD1_last = 2
        # j_RTD1_last = 4
        # i_PT_last = 3
        # j_PT_last = 1

        i_RTD2_max = len(self.AlarmRTD2dir)
        j_RTD2_max = len(self.AlarmRTD2dir[0])

        i_RTD2_last = len(self.AlarmRTD2dir) - 1
        j_RTD2_last = len(self.AlarmRTD2dir[i_RTD2_last]) - 1


        l_RTD2_max = j_RTD2_max - 1

        # RTD1 put alarm true widget to the begining of the diretory

        for i in range(0, i_RTD2_max):
            for j in range(0, j_RTD2_max):
                if TempRefRTD2dir[i][j].Alarm:
                    TempRTD2dir[k_RTD2][l_RTD2] = TempRefRTD2dir[i][j]
                    l_RTD2 = l_RTD2 + 1
                    if l_RTD2 == l_RTD2_max+1:
                        l_RTD2 = 0
                        k_RTD2 = k_RTD2 + 1
                if (i, j) == (i_RTD2_last, j_RTD2_last):
                    break
            if (i, j) == (i_RTD2_last, j_RTD2_last):
                break

        # RTD2 put alarm false widget after that
        for i in range(0, i_RTD2_max):
            for j in range(0, j_RTD2_max):
                if not TempRefRTD2dir[i][j].Alarm:
                    TempRTD2dir[k_RTD2][l_RTD2] = TempRefRTD2dir[i][j]
                    l_RTD2 = l_RTD2 + 1
                    if l_RTD2 == l_RTD2_max+1:
                        l_RTD2 = 0
                        k_RTD2 = k_RTD2 + 1
                if (i, j) == (i_RTD2_last, j_RTD2_last):
                    break
            if (i, j) == (i_RTD2_last, j_RTD2_last):
                break


        # Reassign position
        # end the position generator when i= last element's row number, j= last element's column number

        for i in range(0, i_RTD2_max):
            for j in range(0, j_RTD2_max):
                self.GLRTD2.addWidget(TempRTD2dir[i][j], i, j)
                if (i, j) == (i_RTD2_last, j_RTD2_last):
                    break
            if (i, j) == (i_RTD2_last, j_RTD2_last):
                break


    @QtCore.Slot()
    def ReassignRTD3Order(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate

        TempRefRTD3dir = self.AlarmRTD3dir

        TempRTD3dir = self.AlarmRTD3dir

        # l_RTD1_max is max number of column

        l_RTD3 = 0
        k_RTD3 = 0

        # i_RTD1_max = 3
        # j_RTD1_max = 5
        # i_PT_max = 4
        # j_PT_max = 5
        # l_RTD1_max = 4
        # l_PT_max = 4
        # i_RTD1_last = 2
        # j_RTD1_last = 4
        # i_PT_last = 3
        # j_PT_last = 1
        i_RTD3_max = len(self.AlarmRTD3dir)
        j_RTD3_max = len(self.AlarmRTD3dir[0])

        i_RTD3_last = len(self.AlarmRTD3dir) - 1
        j_RTD3_last = len(self.AlarmRTD3dir[i_RTD3_last]) - 1

        l_RTD3_max = j_RTD3_max - 1

        for i in range(0, i_RTD3_max):
            for j in range(0, j_RTD3_max):
                if TempRefRTD3dir[i][j].Alarm:
                    TempRTD3dir[k_RTD3][l_RTD3] = TempRefRTD3dir[i][j]
                    l_RTD3 = l_RTD3 + 1
                    if l_RTD3 == l_RTD3_max+1:
                        l_RTD3 = 0
                        k_RTD3 = k_RTD3 + 1
                if (i, j) == (i_RTD3_last, j_RTD3_last):
                    break
            if (i, j) == (i_RTD3_last, j_RTD3_last):
                break

        # RTD3 put alarm false widget after that
        for i in range(0, i_RTD3_max):
            for j in range(0, j_RTD3_max):
                if not TempRefRTD3dir[i][j].Alarm:
                    TempRTD3dir[k_RTD3][l_RTD3] = TempRefRTD3dir[i][j]
                    l_RTD3 = l_RTD3 + 1
                    if l_RTD3 == l_RTD3_max+1:
                        l_RTD3 = 0
                        k_RTD3 = k_RTD3 + 1
                if (i, j) == (i_RTD3_last, j_RTD3_last):
                    break
            if (i, j) == (i_RTD3_last, j_RTD3_last):
                break


        # Reassign position
        # end the position generator when i= last element's row number, j= last element's column number


        for i in range(0, i_RTD3_max):
            for j in range(0, j_RTD3_max):
                self.GLRTD3.addWidget(TempRTD3dir[i][j], i, j)
                if (i, j) == (i_RTD3_last, j_RTD3_last):
                    break
            if (i, j) == (i_RTD3_last, j_RTD3_last):
                break

    @QtCore.Slot()
    def ReassignRTD4Order(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate

        TempRefRTD4dir = self.AlarmRTD4dir

        TempRTD4dir = self.AlarmRTD4dir

        # l_RTD1_max is max number of column

        l_RTD4 = 0
        k_RTD4 = 0

        # i_RTD1_max = 3
        # j_RTD1_max = 5
        # i_PT_max = 4
        # j_PT_max = 5
        # l_RTD1_max = 4
        # l_PT_max = 4
        # i_RTD1_last = 2
        # j_RTD1_last = 4
        # i_PT_last = 3
        # j_PT_last = 1

        i_RTD4_max = len(self.AlarmRTD4dir)
        j_RTD4_max = len(self.AlarmRTD4dir[0])

        i_RTD4_last = len(self.AlarmRTD4dir) - 1
        j_RTD4_last = len(self.AlarmRTD4dir[i_RTD4_last]) - 1

        l_RTD4_max = j_RTD4_max - 1

        for i in range(0, i_RTD4_max):
            for j in range(0, j_RTD4_max):
                if TempRefRTD4dir[i][j].Alarm:
                    TempRTD4dir[k_RTD4][l_RTD4] = TempRefRTD4dir[i][j]
                    l_RTD4 = l_RTD4 + 1
                    if l_RTD4 == l_RTD4_max+1:
                        l_RTD4 = 0
                        k_RTD4 = k_RTD4 + 1
                if (i, j) == (i_RTD4_last, j_RTD4_last):
                    break
            if (i, j) == (i_RTD4_last, j_RTD4_last):
                break

        # RTD4 put alarm false widget after that
        for i in range(0, i_RTD4_max):
            for j in range(0, j_RTD4_max):
                if not TempRefRTD4dir[i][j].Alarm:
                    TempRTD4dir[k_RTD4][l_RTD4] = TempRefRTD4dir[i][j]
                    l_RTD4 = l_RTD4 + 1
                    if l_RTD4 == l_RTD4_max+1:
                        l_RTD4 = 0
                        k_RTD4 = k_RTD4 + 1
                if (i, j) == (i_RTD4_last, j_RTD4_last):
                    break
            if (i, j) == (i_RTD4_last, j_RTD4_last):
                break


        # Reassign position
        # end the position generator when i= last element's row number, j= last element's column number

            # for i in range(0, i_RTD4_max):
            for j in range(0, j_RTD4_max):
                self.GLRTD4.addWidget(TempRTD4dir[i][j], i, j)
                if (i, j) == (i_RTD4_last, j_RTD4_last):
                    break
            if (i, j) == (i_RTD4_last, j_RTD4_last):
                break
        # end the position generator when i= last element's row number, j= last element's column number


    @QtCore.Slot()
    def ReassignRTDLEFTOrder(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate


        TempRefRTDLEFTdir = self.AlarmRTDLEFTdir


        TempRTDLEFTdir = self.AlarmRTDLEFTdir

        # l_RTD1_max is max number of column

        l_RTDLEFT = 0
        k_RTDLEFT = 0


        # i_RTD1_max = 3
        # j_RTD1_max = 5
        # i_PT_max = 4
        # j_PT_max = 5
        # l_RTD1_max = 4
        # l_PT_max = 4
        # i_RTD1_last = 2
        # j_RTD1_last = 4
        # i_PT_last = 3
        # j_PT_last = 1

        i_RTDLEFT_max = len(self.AlarmRTDLEFTdir)
        j_RTDLEFT_max = len(self.AlarmRTDLEFTdir[0])

        i_RTDLEFT_last = len(self.AlarmRTDLEFTdir) - 1
        j_RTDLEFT_last = len(self.AlarmRTDLEFTdir[i_RTDLEFT_last]) - 1

        l_RTDLEFT_max = j_RTDLEFT_max - 1

        for i in range(0, i_RTDLEFT_max):
            for j in range(0, j_RTDLEFT_max):
                if TempRefRTDLEFTdir[i][j].Alarm:
                    TempRTDLEFTdir[k_RTDLEFT][l_RTDLEFT] = TempRefRTDLEFTdir[i][j]
                    l_RTDLEFT = l_RTDLEFT + 1
                    if l_RTDLEFT == l_RTDLEFT_max+1:
                        l_RTDLEFT = 0
                        k_RTDLEFT = k_RTDLEFT + 1
                if (i, j) == (i_RTDLEFT_last, j_RTDLEFT_last):
                    break
            if (i, j) == (i_RTDLEFT_last, j_RTDLEFT_last):
                break

        # RTDLEFT put alarm false widget after that
        for i in range(0, i_RTDLEFT_max):
            for j in range(0, j_RTDLEFT_max):
                if not TempRefRTDLEFTdir[i][j].Alarm:
                    TempRTDLEFTdir[k_RTDLEFT][l_RTDLEFT] = TempRefRTDLEFTdir[i][j]
                    l_RTDLEFT = l_RTDLEFT + 1
                    if l_RTDLEFT == l_RTDLEFT_max+1:
                        l_RTDLEFT = 0
                        k_RTDLEFT = k_RTDLEFT + 1
                if (i, j) == (i_RTDLEFT_last, j_RTDLEFT_last):
                    break
            if (i, j) == (i_RTDLEFT_last, j_RTDLEFT_last):
                break

        # Reassign position
        # end the position generator when i= last element's row number, j= last element's column number
        for i in range(0, i_RTDLEFT_max):
            for j in range(0, j_RTDLEFT_max):
                self.GLRTDLEFT.addWidget(TempRTDLEFTdir[i][j], i, j)
                if (i, j) == (i_RTDLEFT_last, j_RTDLEFT_last):
                    break
            if (i, j) == (i_RTDLEFT_last, j_RTDLEFT_last):
                break

        # end the position generator when i= last element's row number, j= last element's column number

    @QtCore.Slot()
    def ReassignPTOrder(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate


        TempRefPTdir = self.AlarmPTdir

        TempPTdir = self.AlarmPTdir
        # l_RTD1_max is max number of column

        l_PT = 0
        k_PT = 0
        # i_RTD1_max = 3
        # j_RTD1_max = 5
        # i_PT_max = 4
        # j_PT_max = 5
        # l_RTD1_max = 4
        # l_PT_max = 4
        # i_RTD1_last = 2
        # j_RTD1_last = 4
        # i_PT_last = 3
        # j_PT_last = 1

        i_PT_max = len(self.AlarmPTdir)
        # which is 4
        j_PT_max = len(self.AlarmPTdir[0])
        # which is 5

        i_PT_last = len(self.AlarmPTdir) - 1
        # which is 3
        j_PT_last = len(self.AlarmPTdir[i_PT_last]) - 1
        # which is 1

        l_PT_max = j_PT_max - 1

        # PT
        for i in range(0, i_PT_max):
            for j in range(0, j_PT_max):
                if TempRefPTdir[i][j].Alarm:
                    TempPTdir[k_PT][l_PT] = TempRefPTdir[i][j]
                    l_PT = l_PT + 1
                    if l_PT == l_PT_max+1:
                        l_PT = 0
                        k_PT = k_PT + 1
                if (i, j) == (i_PT_last, j_PT_last):
                    break
            if (i, j) == (i_PT_last, j_PT_last):
                break

        for i in range(0, i_PT_max):
            for j in range(0, j_PT_max):
                if not TempRefPTdir[i][j].Alarm:
                    TempPTdir[k_PT][l_PT] = TempRefPTdir[i][j]
                    l_PT = l_PT + 1
                    if l_PT == l_PT_max+1:
                        l_PT = 0
                        k_PT = k_PT + 1
                    if (i, j) == (i_PT_last, j_PT_last):
                        break
                if (i, j) == (i_PT_last, j_PT_last):
                    break

        # Reassign position
        # end the position generator when i= last element's row number, j= last element's column number

        # end the position generator when i= last element's row number, j= last element's column number
        for i in range(0, i_PT_max):
            for j in range(0, j_PT_max):
                self.GLPT.addWidget(TempPTdir[i][j], i, j)
                if (i, j) == (i_PT_last, j_PT_last):
                    break
            if (i, j) == (i_PT_last, j_PT_last):
                break


class HeaterSubWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(1200*R, 600*R)
        self.setMinimumSize(1200*R, 600*R)
        self.setWindowTitle("Detailed Information")

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1200*R, 600*R))

        # Groupboxs for alarm/PT/TT

        self.GLWR = QtWidgets.QHBoxLayout()
        self.GLWR.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GLWR.setSpacing(20 * R)
        self.GLWR.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupWR = QtWidgets.QGroupBox(self.Widget)
        self.GroupWR.setTitle("Write")
        self.GroupWR.setLayout(self.GLWR)
        self.GroupWR.move(0 * R, 0 * R)

        self.GLRD = QtWidgets.QHBoxLayout()
        self.GLRD.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GLRD.setSpacing(20 * R)
        self.GLRD.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRD = QtWidgets.QGroupBox(self.Widget)
        self.GroupRD.setTitle("Read")
        self.GroupRD.setLayout(self.GLRD)
        self.GroupRD.move(0 * R, 150 * R)

        # self.Label = QtWidgets.QLabel(self.GroupWR)
        # self.Label.setObjectName("Label")
        # self.Label.setMinimumSize(QtCore.QSize(10 * R, 10 * R))
        # self.Label.setStyleSheet("QLabel {" + TITLE_STYLE + BORDER_STYLE + "}")
        # self.Label.setAlignment(QtCore.Qt.AlignCenter)
        # self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 140 * R))
        # self.Label.setText("Write")
        # self.GLWR.addWidget(self.Label)







        # self.resize(1200*R, 600*R)
        # self.setMinimumSize(1200*R, 600*R)
        # self.setWindowTitle("Detailed Information")
        #
        # # self.Widget = QtWidgets.QWidget(self)
        # # self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1200*R, 600*R))
        #
        # self.VL = QtWidgets.QVBoxLayout(self)
        # self.VL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        # self.VL.setAlignment(QtCore.Qt.AlignCenter)
        # self.VL.setSpacing(5 * R)
        # # self.Widget.setLayout(self.VL)
        #
        # self.HL1 = QtWidgets.QHBoxLayout()
        # self.HL1.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        # self.HL1.setAlignment(QtCore.Qt.AlignCenter)
        # self.HL1.setSpacing(5 * R)
        #
        # self.HL2 = QtWidgets.QHBoxLayout()
        # self.HL2.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        # self.HL2.setAlignment(QtCore.Qt.AlignCenter)
        # self.HL2.setSpacing(5 * R)
        #
        # self.HL3 = QtWidgets.QHBoxLayout()
        # self.HL3.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        # self.HL3.setAlignment(QtCore.Qt.AlignCenter)
        # self.HL3.setSpacing(5 * R)
        #
        # self.VL.addLayout(self.HL1)
        # self.VL.addLayout(self.HL2)
        # self.VL.addLayout(self.HL3)
        #
        # self.Label = QtWidgets.QLabel(self)
        # self.Label.setObjectName("Label")
        # self.Label.setMinimumSize(QtCore.QSize(10 * R, 10 * R))
        # self.Label.setStyleSheet("QLabel {" + TITLE_STYLE + BORDER_STYLE + "}")
        # self.Label.setAlignment(QtCore.Qt.AlignCenter)
        # self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 140 * R))
        # self.Label.setText("Write")
        # self.HL1.addWidget(self.Label)
        #
        self.FBSwitch = Menu(self.GroupWR)
        self.FBSwitch.Label.setText("FBSWITCH")
        self.GLWR.addWidget(self.FBSwitch)

        self.Mode = DoubleButton(self.GroupWR)
        self.Mode.Label.setText("Mode")
        self.GLWR.addWidget(self.Mode)

        self.HISP = SetPoint(self.GroupWR)
        self.HISP.Label.setText("HI SET")
        self.GLWR.addWidget(self.HISP)

        self.LOSP = SetPoint(self.GroupWR)
        self.LOSP.Label.setText("LO SET")
        self.GLWR.addWidget(self.LOSP)

        self.SP = SetPoint(self.GroupWR)
        self.SP.Label.setText("SetPoint")
        self.GLWR.addWidget(self.SP)

        self.updatebutton = QtWidgets.QPushButton(self.GroupWR)
        self.updatebutton.setText("Update")
        self.updatebutton.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.updatebutton)

        self.Interlock = ColorIndicator(self.GroupRD)
        self.Interlock.Label.setText("INTLCK")
        self.GLRD.addWidget(self.Interlock)

        self.Error = ColorIndicator(self.GroupRD)
        self.Error.Label.setText("ERR")
        self.GLRD.addWidget(self.Error)

        self.MANSP = ColorIndicator(self.GroupRD)
        self.MANSP.Label.setText("MAN")
        self.GLRD.addWidget(self.MANSP)

        self.SAT = ColorIndicator(self.GroupRD)
        self.SAT.Label.setText("SAT")
        self.GLRD.addWidget(self.SAT)

        self.ModeREAD = Indicator(self.GroupRD)
        self.ModeREAD.Label.setText("Mode")
        self.GLRD.addWidget(self.ModeREAD)

        self.EN = Indicator(self.GroupRD)
        self.EN.Label.setText("ENABLE")
        self.GLRD.addWidget(self.EN)

        self.Power = Control(self.GroupRD)
        self.Power.Label.setText("Power")
        self.Power.SetUnit(" %")
        self.Power.Max = 100.
        self.Power.Min = 0.
        self.Power.Step = 0.1
        self.Power.Decimals = 1
        self.GLRD.addWidget(self.Power)

        self.IN = Indicator(self.GroupRD)
        self.IN.Label.setText("IN")
        self.GLRD.addWidget(self.IN)

        self.HIGH = Indicator(self.GroupRD)
        self.HIGH.Label.setText("HIGH")
        self.GLRD.addWidget(self.HIGH)

        self.LOW = SetPoint(self.GroupRD)
        self.LOW.Label.setText("LOW")
        self.GLRD.addWidget(self.LOW)

        self.SETSP = Indicator(self.GroupRD)
        self.SETSP.Label.setText("SP")
        self.GLRD.addWidget(self.SETSP)

        self.RTD1 = Indicator(self.GroupRD)
        self.RTD1.Label.setText("RTD1")
        self.GLRD.addWidget(self.RTD1)

        self.RTD2 = Indicator(self.GroupRD)
        self.RTD2.Label.setText("RTD2")
        self.GLRD.addWidget(self.RTD2)


# Define a function tab that shows the status of the widgets

class MultiStatusIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("MutiStatusIndicator")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 200*R, 100*R))
        self.setMinimumSize(200*R, 100*R)
        self.setSizePolicy(sizePolicy)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.setSpacing(3)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(10*R, 10*R))
        self.Label.setStyleSheet("QLabel {" +TITLE_STYLE + BORDER_STYLE+"}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.addLayout(self.HL)

        self.Interlock = ColoredStatus(self, 2)
        self.Interlock.Label.setText("INTLKD")
        self.HL.addWidget(self.Interlock)

        self.Manual = ColoredStatus(self, 2)
        self.Manual.Label.setText("MAN")
        self.HL.addWidget(self.Manual)

        self.Error = ColoredStatus(self, 1)
        self.Error.Label.setText("ERR")
        self.HL.addWidget(self.Error)


# Define an alarm button
class AlarmButton(QtWidgets.QWidget):
    def __init__(self, Window, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("AlarmButton")
        self.setGeometry(QtCore.QRect(5*R, 5*R, 250*R, 80*R))
        self.setMinimumSize(250*R, 80*R)
        self.setSizePolicy(sizePolicy)

        # link the button to a new window
        self.SubWindow = Window

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setText("Button")
        self.Button.setGeometry(QtCore.QRect(5*R, 5*R, 245*R, 75*R))
        self.Button.setStyleSheet(
            "QWidget{" + LABEL_STYLE + "} QWidget[Alarm = true]{ background-color: rgb(255,132,27);} "
                                       "QWidget[Alarm = false]{ background-color: rgb(204,204,204);}")

        self.Button.setProperty("Alarm", False)
        self.Button.Alarm = False
        self.Button.clicked.connect(self.ButtonClicked)
        self.Collected = False

    @QtCore.Slot()
    def ButtonClicked(self):
        self.SubWindow.show()
        # self.Signals.sSignal.emit(self.Button.text())

    @QtCore.Slot()
    def ButtonAlarmSetSignal(self):
        self.Button.setProperty("Alarm", True)
        self.Button.setStyle(self.Button.style())

    @QtCore.Slot()
    def ButtonAlarmResetSignal(self):
        self.Button.setProperty("Alarm", False)
        self.Button.setStyle(self.Button.style())


    @QtCore.Slot()
    def CollectAlarm(self, list):
        # self.Collected=False
        # for i in range(len(list)):
        #     # calculate collected alarm status
        #     self.Collected = self.Collected or list[i].Alarm
        # self.Button.Alarm = self.Collected
        if True in list:
            self.Button.Alarm = True
        else:
            self.Button.Alarm = False



# Define a function tab that shows the status of the widgets
class FunctionButton(QtWidgets.QWidget):
    def __init__(self, Window, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("FunctionButton")
        self.setGeometry(QtCore.QRect(5*R, 5*R, 250*R, 80*R))
        self.setMinimumSize(250*R, 80*R)
        self.setSizePolicy(sizePolicy)

        # link the button to a new window
        self.SubWindow = Window

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setText("Button")
        self.Button.setGeometry(QtCore.QRect(5*R, 5*R, 245*R, 75*R))
        self.Button.clicked.connect(self.ButtonClicked)
        self.Button.setStyleSheet("QPushButton {" +LABEL_STYLE+"}")

    @QtCore.Slot()
    def ButtonClicked(self):
        self.SubWindow.show()
        # self.Signals.sSignal.emit(self.Button.text())


# Defines a reusable layout containing widgets

class Chiller(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        self.Label.setStyleSheet("QLabel {" +TITLE_STYLE+"}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.addLayout(self.HL)

        self.State = Toggle(self)
        self.State.Label.setText("State")
        self.HL.addWidget(self.State)

        self.Setpoint = Control(self)
        self.Setpoint.Label.setText("Setpoint")
        self.HL.addWidget(self.Setpoint)

        self.Temp = Indicator(self)
        self.Temp.Label.setText("Temp")
        self.HL.addWidget(self.Temp)


# Defines a reusable layout containing widgets
class Heater(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)

        self.Label = QtWidgets.QPushButton(self)
        self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        self.Label.setStyleSheet("QPushButton {" +TITLE_STYLE+BORDER_STYLE+"}")
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        # Add a Sub window popped out when click the name
        self.HeaterSubWindow = HeaterSubWindow(self)
        self.Label.clicked.connect(self.PushButton)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.addLayout(self.HL)

        self.State = DoubleButton(self)
        self.State.Label.setText("State")
        self.State.LButton.setText("On")
        self.State.RButton.setText("Off")
        self.HL.addWidget(self.State)

        self.Power = Control(self)
        self.Power.Label.setText("Power")
        self.Power.SetUnit(" %")
        self.Power.Max = 100.
        self.Power.Min = 0.
        self.Power.Step = 0.1
        self.Power.Decimals = 1
        self.HL.addWidget(self.Power)

    def PushButton(self):
        self.HeaterSubWindow.show()


class HeaterExpand(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("HeaterExpand")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 1000*R, 500*R))
        self.setMinimumSize(900*R, 500*R)
        self.setSizePolicy(sizePolicy)



        # self.GL = QtWidgets.QGridLayout(self)
        # self.GL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        # self.GL.setSpacing(3*R)
        #
        # self.Label = QtWidgets.QLabel(self)
        # self.Label.setObjectName("Label")
        # self.Label.setMinimumSize(QtCore.QSize(10*R, 10*R))
        # self.Label.setStyleSheet("QLabel {" +TITLE_STYLE + BORDER_STYLE+"}")
        # self.Label.setAlignment(QtCore.Qt.AlignCenter)
        # self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 40*R, 140*R))
        # self.Label.setText("Write")
        # self.GL.addWidget(self.Label,0,1)
        #
        # self.FBSwitch = Menu(self)
        # self.FBSwitch.Label.setText("FBSWITCH")
        # self.GL.addWidget(self.FBSwitch, 0, 3)
        #
        # self.Mode = DoubleButton(self)
        # self.Mode.Label.setText("Mode")
        # self.GL.addWidget(self.Mode, 0, 5)
        #
        # self.HISP= SetPoint(self)
        # self.HISP.Label.setText("HI SET")
        # self.GL.addWidget(self.HISP, 0,9)
        #
        # self.LOSP = SetPoint(self)
        # self.LOSP.Label.setText("LO SET")
        # self.GL.addWidget(self.LOSP, 0, 10)
        #
        # self.SP = SetPoint(self)
        # self.SP.Label.setText("SetPoint")
        # self.GL.addWidget(self.SP, 0, 11)
        #
        # self.updatebutton = QtWidgets.QPushButton(self)
        # self.updatebutton.setText("Update")
        # self.updatebutton.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        # self.GL.addWidget(self.updatebutton, 0, 12)
        #
        # self.Interlock = ColorIndicator(self)
        # self.Interlock.Label.setText("INTLCK")
        # self.GL.addWidget(self.Interlock, 1, 1)
        #
        # self.Error = ColorIndicator(self)
        # self.Error.Label.setText("ERR")
        # self.GL.addWidget(self.Error, 1, 2)
        #
        # self.MANSP = ColorIndicator(self)
        # self.MANSP.Label.setText("MAN")
        # self.GL.addWidget(self.MANSP, 1, 3)
        #
        # self.SAT = ColorIndicator(self)
        # self.SAT.Label.setText("SAT")
        # self.GL.addWidget(self.SAT,1,4)
        #
        # self.ModeREAD = Indicator(self)
        # self.ModeREAD.Label.setText("Mode")
        # self.GL.addWidget(self.ModeREAD, 1, 5)
        #
        # self.EN = Indicator(self)
        # self.EN.Label.setText("ENABLE")
        # self.GL.addWidget(self.EN, 1, 6)
        #
        # self.Power = Control(self)
        # self.Power.Label.setText("Power")
        # self.Power.SetUnit(" %")
        # self.Power.Max = 100.
        # self.Power.Min = 0.
        # self.Power.Step = 0.1
        # self.Power.Decimals = 1
        # self.GL.addWidget(self.Power, 1, 7)
        #
        # self.IN = Indicator(self)
        # self.IN.Label.setText("IN")
        # self.GL.addWidget(self.IN, 1, 8)
        #
        # self.HIGH = Indicator(self)
        # self.HIGH.Label.setText("HIGH")
        # self.GL.addWidget(self.HIGH, 1, 9)
        #
        # self.LOW = SetPoint(self)
        # self.LOW.Label.setText("LOW")
        # self.GL.addWidget(self.LOW, 1, 10)
        #
        # self.SETSP = Indicator(self)
        # self.SETSP.Label.setText("SP")
        # self.GL.addWidget(self.SETSP, 1, 11)
        #
        #
        # self.RTD1 = Indicator(self)
        # self.RTD1.Label.setText("RTD1")
        # self.GL.addWidget(self.RTD1, 2, 1)
        #
        # self.RTD2 = Indicator(self)
        # self.RTD2.Label.setText("RTD2")
        # self.GL.addWidget(self.RTD2, 2, 2)


# Defines a reusable layout containing widgets
# class HeaterExpand(QtWidgets.QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#
#         sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
#
#         self.setObjectName("HeaterExpand")
#         self.setGeometry(QtCore.QRect(0*R, 0*R, 1050*R, 80*R))
#         self.setMinimumSize(1050*R, 80*R)
#         self.setSizePolicy(sizePolicy)
#
#         self.VL = QtWidgets.QVBoxLayout(self)
#         self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
#         self.VL.setSpacing(5*R)
#
#         self.Label = QtWidgets.QLabel(self)
#         self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
#         self.Label.setStyleSheet(TITLE_STYLE + BORDER_STYLE)
#         # self.Label.setAlignment(QtCore.Qt.AlignCenter)
#         self.Label.setText("Label")
#         self.VL.addWidget(self.Label)
#
#         self.HL = QtWidgets.QHBoxLayout()
#         self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
#         self.VL.addLayout(self.HL)
#
#         self.Mode = DoubleButton(self)
#         self.Mode.Label.setText("Mode")
#         self.HL.addWidget(self.Mode)
#
#         self.FBSwitch = Menu(self)
#         self.FBSwitch.Label.setText("FBSWITCH")
#         self.HL.addWidget(self.FBSwitch)
#
#         self.SP = SetPoint(self)
#         self.SP.Label.setText("SetPoint")
#         self.HL.addWidget(self.SP)
#
#         self.MANSP = SetPoint(self)
#         self.MANSP.Label.setText("Manual SetPoint")
#         self.HL.addWidget(self.MANSP)
#
#         self.Power = Control(self)
#         self.Power.Label.setText("Power")
#         self.Power.SetUnit(" %")
#         self.Power.Max = 100.
#         self.Power.Min = 0.
#         self.Power.Step = 0.1
#         self.Power.Decimals = 1
#         self.HL.addWidget(self.Power)
#
#         self.RTD1 = Indicator(self)
#         self.RTD1.Label.setText("RTD1")
#         self.HL.addWidget(self.RTD1)
#
#         self.RTD2 = Indicator(self)
#         self.RTD2.Label.setText("RTD2")
#         self.HL.addWidget(self.RTD2)
#
#         self.Interlock = ColorIndicator(self)
#         self.Interlock.Label.setText("INTLCK")
#         self.HL.addWidget(self.Interlock)
#
#         self.Error = ColorIndicator(self)
#         self.Error.Label.setText("ERR")
#         self.HL.addWidget(self.Error)
#
#         self.HIGH = SetPoint(self)
#         self.HIGH.Label.setText("HIGH")
#         self.HL.addWidget(self.HIGH)
#
#         self.LOW = SetPoint(self)
#         self.LOW.Label.setText("LOW")
#         self.HL.addWidget(self.LOW)




# Defines a reusable layout containing widgets
class AOMultiLoop(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)

        self.Label = QtWidgets.QPushButton(self)
        self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        self.Label.setStyleSheet("QLabel {" +TITLE_STYLE + BORDER_STYLE+"}")
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        # Add a Sub window popped out when click the name
        self.HeaterSubWindow = HeaterSubWindow(self)
        self.Label.clicked.connect(self.PushButton)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.addLayout(self.HL)

        self.Mode = Menu(self)
        self.Mode.Label.setText("Mode")
        self.HL.addWidget(self.Mode)

        self.Power = Control(self)
        self.Power.Label.setText("Power")
        self.Power.SetUnit(" %")
        self.Power.Max = 100.
        self.Power.Min = 0.
        self.Power.Step = 0.1
        self.Power.Decimals = 1
        self.HL.addWidget(self.Power)

    def PushButton(self):
        self.HeaterSubWindow.show()


# Defines a reusable layout containing widgets
class AOMutiLoopExpand(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("AOMutiLoop")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 1050*R, 80*R))
        self.setMinimumSize(1050*R, 80*R)
        self.setSizePolicy(sizePolicy)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.setSpacing(5*R)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        self.Label.setStyleSheet("QLabel {" +TITLE_STYLE + BORDER_STYLE+"}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.addLayout(self.HL)

        self.Mode = DoubleButton(self)
        self.Mode.Label.setText("Mode")
        self.HL.addWidget(self.Mode)

        self.FBSwitch = Menu(self)
        self.FBSwitch.Label.setText("FBSWITCH")
        self.HL.addWidget(self.FBSwitch)

        self.SP = SetPoint(self)
        self.SP.Label.setText("SetPoint")
        self.HL.addWidget(self.SP)

        self.MANSP = SetPoint(self)
        self.MANSP.Label.setText("Manual SetPoint")
        self.HL.addWidget(self.MANSP)

        self.Power = Control(self)
        self.Power.Label.setText("Power")
        self.Power.SetUnit(" %")
        self.Power.Max = 100.
        self.Power.Min = 0.
        self.Power.Step = 0.1
        self.Power.Decimals = 1
        self.HL.addWidget(self.Power)

        self.RTD1 = Indicator(self)
        self.RTD1.Label.setText("RTD1")
        self.HL.addWidget(self.RTD1)

        self.RTD2 = Indicator(self)
        self.RTD2.Label.setText("RTD2")
        self.HL.addWidget(self.RTD2)

        self.Interlock = ColorIndicator(self)
        self.Interlock.Label.setText("INTLCK")
        self.HL.addWidget(self.Interlock)

        self.Error = ColorIndicator(self)
        self.Error.Label.setText("ERR")
        self.HL.addWidget(self.Error)

        self.HIGH = SetPoint(self)
        self.HIGH.Label.setText("HIGH")
        self.HL.addWidget(self.HIGH)

        self.LOW = SetPoint(self)
        self.LOW.Label.setText("LOW")
        self.HL.addWidget(self.LOW)


# Defines a reusable layout containing widget
class Valve(QtWidgets.QWidget):
    def __init__(self, parent=None, mode=0):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.setSpacing(3)

        self.Label = QtWidgets.QLabel(self)
        # self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        self.Label.setMinimumSize(QtCore.QSize(10*R, 10*R))
        self.Label.setStyleSheet("QLabel {" +TITLE_STYLE + BORDER_STYLE+"}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.addLayout(self.HL)

        self.Set = DoubleButton(self)
        self.Set.Label.setText("Set")
        self.Set.LButton.setText("open")
        self.Set.RButton.setText("close")
        self.HL.addWidget(self.Set)

        self.ActiveState = ColoredStatus(self, mode)
        # self.ActiveState = ColorIndicator(self) for test the function
        self.ActiveState.Label.setText("Status")
        self.HL.addWidget(self.ActiveState)


# Defines a reusable layout containing widgets
class Camera(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        self.Label.setStyleSheet("QLabel {" +TITLE_STYLE+"}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.addLayout(self.HL)

        self.Temp = Indicator(self)
        self.Temp.Label.setText("Temp")
        self.HL.addWidget(self.Temp)

        self.LED1 = Indicator(self)
        self.LED1.Label.setText("LED 1")
        self.HL.addWidget(self.LED1)

        self.LED2 = Indicator(self)
        self.LED2.Label.setText("LED 2")
        self.HL.addWidget(self.LED2)

        self.Humidity = Indicator(self)
        self.Humidity.Label.setText("Humidity")
        self.Humidity.Unit = " %"
        self.HL.addWidget(self.Humidity)

        self.Air = Indicator(self)
        self.Air.Label.setText("Air")
        self.HL.addWidget(self.Air)

# Class to read PLC value every 2 sec
class UpdatePLC(QtCore.QObject):
    def __init__(self, PLC, parent=None):
        super().__init__(parent)
        self.PLC = PLC

        self.Running = False

    @QtCore.Slot()
    def run(self):
        self.Running = True

        while self.Running:
            print("PLC updating", datetime.datetime.now())
            self.PLC.ReadAll()
            time.sleep(0.5)

    @QtCore.Slot()
    def stop(self):
        self.Running = False


class UpdateClient(QtCore.QObject):
    def __init__(self, MW, parent=None):
        super().__init__(parent)
        self.MW = MW
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")
        self.Running=False
        self.period=1
        print("client is connecting to the ZMQ server")
        self.receive_dic = {"data":{"TT":{"FP":{"TT2420": 0, "TT2422": 0, "TT2424": 0, "TT2425": 0, "TT2442": 0,
                                                "TT2403": 0, "TT2418": 0, "TT2427": 0, "TT2429": 0, "TT2431": 0,
                                                 "TT2441": 0, "TT2414": 0, "TT2413": 0, "TT2412": 0, "TT2415": 0,
                                                 "TT2409": 0, "TT2436": 0, "TT2438": 0, "TT2440": 0, "TT2402": 0,
                                                 "TT2411": 0, "TT2443": 0, "TT2417": 0, "TT2404": 0, "TT2408": 0,
                                                 "TT2407": 0, "TT2406": 0, "TT2428": 0, "TT2432": 0, "TT2421": 0,
                                                 "TT2416": 0, "TT2439": 0, "TT2419": 0, "TT2423": 0, "TT2426": 0,
                                                 "TT2430": 0, "TT2450": 0, "TT2401": 0, "TT2449": 0, "TT2445": 0,
                                                 "TT2444": 0, "TT2435": 0, "TT2437": 0, "TT2446": 0, "TT2447": 0,
                                                 "TT2448": 0, "TT2410": 0, "TT2405": 0, "TT6220": 0, "TT6401": 0,
                                                 "TT6404": 0, "TT6405": 0, "TT6406": 0, "TT6410": 0, "TT6411": 0,
                                                 "TT6412": 0, "TT6413": 0, "TT6414": 0},
                                          "BO":{"TT2101": 0, "TT2111": 0, "TT2113": 0, "TT2118": 0, "TT2119": 0, "TT4330": 0,
                                                "TT6203": 0, "TT6207": 0, "TT6211": 0, "TT6213": 0, "TT6222": 0,
                                                 "TT6407": 0, "TT6408": 0, "TT6409": 0, "TT6415": 0, "TT6416": 0}},
                               "PT":{"PT1325": 0, "PT2121": 0, "PT2316": 0, "PT2330": 0, "PT2335": 0,
                                     "PT3308": 0, "PT3309": 0, "PT3311": 0, "PT3314": 0, "PT3320": 0,
                                     "PT3332": 0, "PT3333": 0, "PT4306": 0, "PT4315": 0, "PT4319": 0,
                                     "PT4322": 0, "PT4325": 0, "PT6302": 0},
                               "Valve":{"OUT": {"PV1344": 0, "PV4307": 0, "PV4308": 0, "PV4317": 0, "PV4318": 0, "PV4321": 0,
                                               "PV4324": 0, "PV5305": 0, "PV5306": 0,
                                               "PV5307": 0, "PV5309": 0, "SV3307": 0, "SV3310": 0, "SV3322": 0,
                                               "SV3325": 0, "SV3326": 0, "SV3329": 0,
                                               "SV4327": 0, "SV4328": 0, "SV4329": 0, "SV4331": 0, "SV4332": 0,
                                               "SV4337": 0, "HFSV3312": 0, "HFSV3323": 0, "HFSV3331": 0},
                                        "INTLKD": {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                                                  "PV4324": False, "PV5305": False, "PV5306": False,
                                                  "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
                                                  "SV3325": False, "SV3326": False, "SV3329": False,
                                                  "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                                                  "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False},
                                        "MAN": {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                                               "PV4324": False, "PV5305": True, "PV5306": True,
                                               "PV5307": True, "PV5309": True, "SV3307": True, "SV3310": True, "SV3322": True,
                                               "SV3325": True, "SV3326": True, "SV3329": True,
                                               "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                                               "SV4337": False, "HFSV3312": True, "HFSV3323": True, "HFSV3331": True},
                                        "ERR": {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                                               "PV4324": False, "PV5305": False, "PV5306": False,
                                               "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
                                               "SV3325": False, "SV3326": False, "SV3329": False,
                                               "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                                               "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False}}},
                       "Alarm":{"TT":{"FP":{"TT2420": False, "TT2422": False, "TT2424": False, "TT2425": False, "TT2442": False,
                                            "TT2403": False, "TT2418": False, "TT2427": False, "TT2429": False, "TT2431": False,
                                            "TT2441": False, "TT2414": False, "TT2413": False, "TT2412": False, "TT2415": False,
                                            "TT2409": False, "TT2436": False, "TT2438": False, "TT2440": False, "TT2402": False,
                                            "TT2411": False, "TT2443": False, "TT2417": False, "TT2404": False, "TT2408": False,
                                            "TT2407": False, "TT2406": False, "TT2428": False, "TT2432": False, "TT2421": False,
                                            "TT2416": False, "TT2439": False, "TT2419": False, "TT2423": False, "TT2426": False,
                                            "TT2430": False, "TT2450": False, "TT2401": False, "TT2449": False, "TT2445": False,
                                            "TT2444": False, "TT2435": False, "TT2437": False, "TT2446": False, "TT2447": False,
                                            "TT2448": False, "TT2410": False, "TT2405": False, "TT6220": False, "TT6401": False,
                                            "TT6404": False, "TT6405": False, "TT6406": False, "TT6410": False, "TT6411": False,
                                            "TT6412": False, "TT6413": False, "TT6414": False},
                                      "BO":{"TT2101": False, "TT2111": False, "TT2113": False, "TT2118": False, "TT2119": False,
                                      "TT4330": False,
                                      "TT6203": False, "TT6207": False, "TT6211": False, "TT6213": False, "TT6222": False,
                                      "TT6407": False, "TT6408": False, "TT6409": False, "TT6415": False, "TT6416": False}},
                                "PT":{"PT1325": False, "PT2121": False, "PT2316": False, "PT2330": False, "PT2335": False,
                                      "PT3308": False, "PT3309": False, "PT3311": False, "PT3314": False, "PT3320": False,
                                      "PT3332": False, "PT3333": False, "PT4306": False, "PT4315": False, "PT4319": False,
                                      "PT4322": False, "PT4325": False, "PT6302": False}},
                       "MainAlarm":False}
        self.commands_package= pickle.dumps({})
    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:

            print(f"Sending request...")

            #  Send reply back to client
            # self.socket.send(b"Hello")
            self.commands()
            message = pickle.loads(self.socket.recv())

            # print(f"Received reply [ {message} ]")
            self.update_data(message)
            time.sleep(self.period)

    @QtCore.Slot()
    def stop(self):
        self.Running = False
    def update_data(self,message):
        #message mush be a dictionary
        self.receive_dic = message
    def commands(self):
        print("Commands are here",datetime.datetime.now())
        print("commands",self.MW.commands)
        self.commands_package= pickle.dumps(self.MW.commands)
        print("commands len",len(self.MW.commands))
        if len(self.MW.commands) != 0:
            self.socket.send(self.commands_package)
            self.MW.commands={}
        else:
            self.socket.send(pickle.dumps({}))


# Class to update display with PLC values every time PLC values ave been updated
# All commented lines are modbus variables not yet implemented on the PLCs
class UpdateDisplay(QtCore.QObject):
    display_update = QtCore.Signal(dict)
    def __init__(self, MW, Client,parent=None):
        super().__init__(parent)

        self.MW = MW
        self.Client = Client
        self.Running = False

        self.display_update.connect(self.MW.update_alarmwindow)
        self.button_refreshing_count = 0
        self.count = 0

    @QtCore.Slot()
    def run(self):
        try:
            self.Running = True
            while self.Running:
                print("Display updating", datetime.datetime.now())

                # print(self.MW.PLC.RTD)
                # print(3, self.MW.PLC.RTD[3])
                # for i in range(0,6):
                #     print(i, self.MW.PLC.RTD[i])

                # if self.MW.PLC.NewData_Display:

                dic=self.Client.receive_dic
                # print(dic)
                # print(type(dic))

                self.MW.AlarmButton.SubWindow.TT2101.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT2101"])
                self.MW.AlarmButton.SubWindow.TT2101.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT2101"])

                self.MW.AlarmButton.SubWindow.TT2111.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT2111"])
                self.MW.AlarmButton.SubWindow.TT2111.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT2111"])

                self.MW.AlarmButton.SubWindow.TT2113.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT2113"])
                self.MW.AlarmButton.SubWindow.TT2113.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT2113"])

                self.MW.AlarmButton.SubWindow.TT2118.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT2118"])
                self.MW.AlarmButton.SubWindow.TT2118.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT2118"])

                self.MW.AlarmButton.SubWindow.TT2119.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT2119"])
                self.MW.AlarmButton.SubWindow.TT2119.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT2119"])

                self.MW.AlarmButton.SubWindow.TT4330.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT4330"])
                self.MW.AlarmButton.SubWindow.TT4330.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT4330"])

                self.MW.AlarmButton.SubWindow.TT6203.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT6203"])
                self.MW.AlarmButton.SubWindow.TT6203.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT6203"])

                self.MW.AlarmButton.SubWindow.TT6207.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT6207"])
                self.MW.AlarmButton.SubWindow.TT6207.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT6207"])

                self.MW.AlarmButton.SubWindow.TT6211.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT6211"])
                self.MW.AlarmButton.SubWindow.TT6211.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT6211"])

                self.MW.AlarmButton.SubWindow.TT6213.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT6213"])
                self.MW.AlarmButton.SubWindow.TT6213.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT6213"])

                self.MW.AlarmButton.SubWindow.TT6222.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT6222"])
                self.MW.AlarmButton.SubWindow.TT6222.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT6222"])

                self.MW.AlarmButton.SubWindow.TT6407.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT6407"])
                self.MW.AlarmButton.SubWindow.TT6407.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT6407"])

                self.MW.AlarmButton.SubWindow.TT6408.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT6408"])
                self.MW.AlarmButton.SubWindow.TT6408.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT6408"])

                self.MW.AlarmButton.SubWindow.TT6409.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT6409"])
                self.MW.AlarmButton.SubWindow.TT6409.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT6409"])

                self.MW.AlarmButton.SubWindow.TT6415.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT6415"])
                self.MW.AlarmButton.SubWindow.TT6415.Indicator.SetValue(
                    self.Client.receive_dic["data"]["TT"]["BO"]["TT6415"])

                self.MW.AlarmButton.SubWindow.TT6416.UpdateAlarm(self.Client.receive_dic["Alarm"]["TT"]["BO"]["TT6416"])
                self.MW.AlarmButton.SubWindow.TT6416.Indicator.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6416"])


                # FP TTs

                FPRTDAlarmMatrix=[self.MW.AlarmButton.SubWindow.TT2420, self.MW.AlarmButton.SubWindow.TT2422, self.MW.AlarmButton.SubWindow.TT2424, self.MW.AlarmButton.SubWindow.TT2425, self.MW.AlarmButton.SubWindow.TT2442,
                              self.MW.AlarmButton.SubWindow.TT2403, self.MW.AlarmButton.SubWindow.TT2418, self.MW.AlarmButton.SubWindow.TT2427, self.MW.AlarmButton.SubWindow.TT2429, self.MW.AlarmButton.SubWindow.TT2431,
                              self.MW.AlarmButton.SubWindow.TT2441, self.MW.AlarmButton.SubWindow.TT2414, self.MW.AlarmButton.SubWindow.TT2413, self.MW.AlarmButton.SubWindow.TT2412, self.MW.AlarmButton.SubWindow.TT2415,
                              self.MW.AlarmButton.SubWindow.TT2409, self.MW.AlarmButton.SubWindow.TT2436, self.MW.AlarmButton.SubWindow.TT2438, self.MW.AlarmButton.SubWindow.TT2440, self.MW.AlarmButton.SubWindow.TT2402,
                              self.MW.AlarmButton.SubWindow.TT2411, self.MW.AlarmButton.SubWindow.TT2443, self.MW.AlarmButton.SubWindow.TT2417, self.MW.AlarmButton.SubWindow.TT2404, self.MW.AlarmButton.SubWindow.TT2408,
                              self.MW.AlarmButton.SubWindow.TT2407, self.MW.AlarmButton.SubWindow.TT2406, self.MW.AlarmButton.SubWindow.TT2428, self.MW.AlarmButton.SubWindow.TT2432, self.MW.AlarmButton.SubWindow.TT2421,
                              self.MW.AlarmButton.SubWindow.TT2416, self.MW.AlarmButton.SubWindow.TT2439, self.MW.AlarmButton.SubWindow.TT2419, self.MW.AlarmButton.SubWindow.TT2423, self.MW.AlarmButton.SubWindow.TT2426,
                              self.MW.AlarmButton.SubWindow.TT2430, self.MW.AlarmButton.SubWindow.TT2450, self.MW.AlarmButton.SubWindow.TT2401, self.MW.AlarmButton.SubWindow.TT2449, self.MW.AlarmButton.SubWindow.TT2445,
                              self.MW.AlarmButton.SubWindow.TT2444, self.MW.AlarmButton.SubWindow.TT2435, self.MW.AlarmButton.SubWindow.TT2437, self.MW.AlarmButton.SubWindow.TT2446, self.MW.AlarmButton.SubWindow.TT2447,
                              self.MW.AlarmButton.SubWindow.TT2448, self.MW.AlarmButton.SubWindow.TT2410, self.MW.AlarmButton.SubWindow.TT2405, self.MW.AlarmButton.SubWindow.TT6220, self.MW.AlarmButton.SubWindow.TT6401,
                              self.MW.AlarmButton.SubWindow.TT6404, self.MW.AlarmButton.SubWindow.TT6405, self.MW.AlarmButton.SubWindow.TT6406, self.MW.AlarmButton.SubWindow.TT6410, self.MW.AlarmButton.SubWindow.TT6411,
                              self.MW.AlarmButton.SubWindow.TT6412, self.MW.AlarmButton.SubWindow.TT6413, self.MW.AlarmButton.SubWindow.TT6414]

                for element in FPRTDAlarmMatrix:
                    print(element.Label.text())

                    element.UpdateAlarm(
                        self.Client.receive_dic["Alarm"]["TT"]["FP"][element.Label.text()])
                #     element.Indicator.SetValue(
                #         self.Client.receive_dic["data"]["TT"]["FP"][element.Label.text()])


                self.display_update.emit(dic)



                # print("PV4307_OUT", self.Client.receive_dic["data"]["Valve"]["OUT"]["PV4307"])
                # print("PV4307_MAN", self.Client.receive_dic["data"]["Valve"]["MAN"]["PV4307"])
                # print("PV5305_OUT", self.Client.receive_dic["data"]["Valve"]["OUT"]["PV5305"])
                # print("PV5305_MAN", self.Client.receive_dic["data"]["Valve"]["MAN"]["PV5305"])
                # print("SV3307_OUT", self.Client.receive_dic["data"]["Valve"]["OUT"]["SV3307"])
                # print("SV3307_MAN", self.Client.receive_dic["data"]["Valve"]["MAN"]["SV3307"])

                self.MW.PV1344.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV1344"])
                self.MW.PV4307.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV4307"])
                self.MW.PV4308.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV4308"])
                self.MW.PV4317.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV4317"])
                self.MW.PV4318.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV4318"])
                self.MW.PV4321.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV4321"])
                self.MW.PV4324.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV4324"])
                self.MW.PV5305.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV5305"])
                self.MW.PV5306.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV5306"])
                self.MW.PV5307.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV5307"])
                self.MW.PV5309.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["PV5309"])
                self.MW.SV3307.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV3307"])
                self.MW.SV3310.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV3310"])
                self.MW.SV3322.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV3322"])
                self.MW.SV3325.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV3325"])
                self.MW.SV3326.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV3326"])
                self.MW.SV3329.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV3329"])
                self.MW.SV4327.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV4327"])
                self.MW.SV4328.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV4328"])
                self.MW.SV4329.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV4329"])
                self.MW.SV4331.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV4331"])
                self.MW.SV4332.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV4332"])
                self.MW.SV4337.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["SV4337"])
                self.MW.HFSV3312.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["HFSV3312"])
                self.MW.HFSV3323.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["HFSV3323"])
                self.MW.HFSV3331.Set.Activate(self.Client.receive_dic["data"]["Valve"]["MAN"]["HFSV3331"])

                # refreshing the valve status from PLC every 30s
                if self.count >= self.button_refreshing_count:
                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV1344"]:
                        self.MW.PV1344.Set.ButtonLClicked()
                    else:
                        self.MW.PV1344.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV4307"]:
                        self.MW.PV4307.Set.ButtonLClicked()
                    else:
                        self.MW.PV4307.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV4308"]:
                        self.MW.PV4308.Set.ButtonLClicked()
                    else:
                        self.MW.PV4308.Set.ButtonRClicked()
                    self.count = 0

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV4317"]:
                        self.MW.PV4317.Set.ButtonLClicked()
                    else:
                        self.MW.PV4317.Set.ButtonRClicked()
                    self.count = 0

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV4318"]:
                        self.MW.PV4318.Set.ButtonLClicked()
                    else:
                        self.MW.PV4318.Set.ButtonRClicked()
                    self.count = 0

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV4321"]:
                        self.MW.PV4321.Set.ButtonLClicked()
                    else:
                        self.MW.PV4321.Set.ButtonRClicked()
                    self.count = 0

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV4324"]:
                        self.MW.PV4324.Set.ButtonLClicked()
                    else:
                        self.MW.PV4324.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV5305"]:
                        self.MW.PV5305.Set.ButtonLClicked()
                    else:
                        self.MW.PV5305.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV5306"]:
                        self.MW.PV5306.Set.ButtonLClicked()
                    else:
                        self.MW.PV5306.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV5307"]:
                        self.MW.PV5307.Set.ButtonLClicked()
                    else:
                        self.MW.PV5307.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["PV5309"]:
                        self.MW.PV5309.Set.ButtonLClicked()
                    else:
                        self.MW.PV5309.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV3307"]:
                        self.MW.SV3307.Set.ButtonLClicked()
                    else:
                        self.MW.SV3307.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV3310"]:
                        self.MW.SV3310.Set.ButtonLClicked()
                    else:
                        self.MW.SV3310.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV3322"]:
                        self.MW.SV3322.Set.ButtonLClicked()
                    else:
                        self.MW.SV3322.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV3325"]:
                        self.MW.SV3325.Set.ButtonLClicked()
                    else:
                        self.MW.SV3325.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV3326"]:
                        self.MW.SV3326.Set.ButtonLClicked()
                    else:
                        self.MW.SV3326.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV3329"]:
                        self.MW.SV3329.Set.ButtonLClicked()
                    else:
                        self.MW.SV3329.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV4327"]:
                        self.MW.SV4327.Set.ButtonLClicked()
                    else:
                        self.MW.SV3307.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV4328"]:
                        self.MW.SV4328.Set.ButtonLClicked()
                    else:
                        self.MW.SV4328.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV4329"]:
                        self.MW.SV4329.Set.ButtonLClicked()
                    else:
                        self.MW.SV4329.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV4331"]:
                        self.MW.SV4331.Set.ButtonLClicked()
                    else:
                        self.MW.SV4331.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV4332"]:
                        self.MW.SV4332.Set.ButtonLClicked()
                    else:
                        self.MW.SV4332.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["SV4337"]:
                        self.MW.SV4337.Set.ButtonLClicked()
                    else:
                        self.MW.SV4337.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["HFSV3312"]:
                        self.MW.HFSV3312.Set.ButtonLClicked()
                    else:
                        self.MW.HFSV3312.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["HFSV3323"]:
                        self.MW.HFSV3323.Set.ButtonLClicked()
                    else:
                        self.MW.HFSV3323.Set.ButtonRClicked()

                    if self.Client.receive_dic["data"]["Valve"]["OUT"]["HFSV3331"]:
                        self.MW.HFSV3331.Set.ButtonLClicked()
                    else:
                        self.MW.HFSV3331.Set.ButtonRClicked()

                    self.count = 0
                self.count += 1

                self.MW.PT2121.SetValue(self.Client.receive_dic["data"]["PT"]["PT2121"])
                self.MW.PT2316.SetValue(self.Client.receive_dic["data"]["PT"]["PT2316"])
                self.MW.PT2330.SetValue(self.Client.receive_dic["data"]["PT"]["PT2330"])
                self.MW.PT2335.SetValue(self.Client.receive_dic["data"]["PT"]["PT2335"])
                self.MW.PT3308.SetValue(self.Client.receive_dic["data"]["PT"]["PT3308"])
                self.MW.PT3309.SetValue(self.Client.receive_dic["data"]["PT"]["PT3309"])
                self.MW.PT3311.SetValue(self.Client.receive_dic["data"]["PT"]["PT3311"])
                self.MW.PT3314.SetValue(self.Client.receive_dic["data"]["PT"]["PT3314"])
                self.MW.PT3320.SetValue(self.Client.receive_dic["data"]["PT"]["PT3320"])
                self.MW.PT3332.SetValue(self.Client.receive_dic["data"]["PT"]["PT3332"])
                self.MW.PT3333.SetValue(self.Client.receive_dic["data"]["PT"]["PT3333"])
                self.MW.PT4306.SetValue(self.Client.receive_dic["data"]["PT"]["PT4306"])
                self.MW.PT4315.SetValue(self.Client.receive_dic["data"]["PT"]["PT4315"])
                self.MW.PT4319.SetValue(self.Client.receive_dic["data"]["PT"]["PT4319"])
                self.MW.PT4322.SetValue(self.Client.receive_dic["data"]["PT"]["PT4322"])
                self.MW.PT4325.SetValue(self.Client.receive_dic["data"]["PT"]["PT4325"])
                self.MW.PT6302.SetValue(self.Client.receive_dic["data"]["PT"]["PT6302"])

                self.MW.RTDset4Win.TT2101.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT2101"])
                self.MW.RTDset1Win.TT2111.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT2111"])
                self.MW.RTDset1Win.TT2113.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT2113"])
                self.MW.RTDset1Win.TT2118.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT2118"])
                self.MW.RTDset1Win.TT2119.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT2119"])
                self.MW.TT4330.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT4330"])
                # self.MW.HT6202SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6203"])
                #
                # self.MW.HT6206SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6207"])
                # self.MW.HT6210SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6211"])
                # self.MW.HT6214SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6213"])
                # self.MW.HT6221SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6222"])
                # self.MW.HT6223SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6407"])
                # self.MW.HT6224SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6408"])
                # self.MW.HT6225SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6409"])
                # self.MW.HT1202SUB.RTD2.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6415"])
                # self.MW.HT2203SUB.RTD2.SetValue(self.Client.receive_dic["data"]["TT"]["BO"]["TT6416"])

                self.MW.RTDset2Win.TT2420.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2420"])
                self.MW.RTDset2Win.TT2422.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2422"])
                self.MW.RTDset2Win.TT2424.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2424"])
                self.MW.RTDset2Win.TT2425.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2425"])
                self.MW.RTDset3Win.TT2442.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2442"])
                self.MW.RTDset2Win.TT2403.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2403"])
                self.MW.RTDset2Win.TT2418.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2418"])
                self.MW.RTDset2Win.TT2427.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2427"])
                self.MW.RTDset2Win.TT2429.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2429"])
                self.MW.RTDset2Win.TT2431.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2431"])
                self.MW.RTDset3Win.TT2441.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2441"])
                self.MW.RTDset2Win.TT2414.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2414"])
                self.MW.RTDset2Win.TT2413.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2413"])
                self.MW.RTDset2Win.TT2412.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2412"])
                self.MW.RTDset2Win.TT2415.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2415"])
                self.MW.RTDset2Win.TT2409.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2409"])
                self.MW.RTDset3Win.TT2436.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2436"])
                self.MW.RTDset3Win.TT2438.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2438"])
                self.MW.RTDset3Win.TT2440.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2440"])
                self.MW.RTDset2Win.TT2402.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2402"])
                self.MW.RTDset2Win.TT2411.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2411"])
                self.MW.RTDset3Win.TT2443.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2443"])
                self.MW.RTDset2Win.TT2417.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2417"])
                self.MW.RTDset2Win.TT2404.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2404"])
                self.MW.RTDset2Win.TT2408.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2408"])
                self.MW.RTDset2Win.TT2407.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2407"])
                self.MW.RTDset2Win.TT2406.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2406"])
                self.MW.RTDset2Win.TT2428.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2428"])
                self.MW.RTDset2Win.TT2432.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2432"])
                self.MW.RTDset2Win.TT2421.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2421"])
                self.MW.RTDset2Win.TT2416.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2416"])
                self.MW.RTDset3Win.TT2439.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2439"])
                self.MW.RTDset2Win.TT2419.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2419"])
                self.MW.RTDset2Win.TT2423.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2423"])
                self.MW.RTDset2Win.TT2426.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2426"])
                self.MW.RTDset2Win.TT2430.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2430"])
                self.MW.RTDset3Win.TT2450.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2450"])
                self.MW.RTDset2Win.TT2401.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2401"])
                self.MW.RTDset3Win.TT2449.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2449"])
                self.MW.RTDset3Win.TT2445.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2445"])
                self.MW.RTDset3Win.TT2444.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2444"])
                self.MW.RTDset3Win.TT2435.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2435"])
                self.MW.RTDset3Win.TT2437.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2437"])
                self.MW.RTDset3Win.TT2446.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2446"])
                self.MW.RTDset3Win.TT2447.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2447"])
                self.MW.RTDset3Win.TT2448.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2448"])
                self.MW.RTDset2Win.TT2410.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2410"])
                self.MW.RTDset2Win.TT2405.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT2405"])
                # self.MW.MFC1316SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT6220"])
                # self.MW.HT6214SUB.RTD2.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT6401"])
                # self.MW.HT6202SUB.RTD2.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT6404"])
                # self.MW.HT6206SUB.RTD2.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT6405"])
                # self.MW.HT6210SUB.RTD2.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT6406"])
                # self.MW.HT6223SUB.RTD2.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT6410"])
                # self.MW.HT6224SUB.RTD2.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT6411"])
                # self.MW.HT6225SUB.RTD2.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT6412"])
                # self.MW.HT1202SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT6413"])
                # self.MW.HT2203SUB.RTD1.SetValue(self.Client.receive_dic["data"]["TT"]["FP"]["TT6414"])


                # self.MW.subwindow.alarmbutton(self.Client.receive_dic)
                # reorfer
                #     self.MW.RTDSET1Button.SubWindow.TT2111.SetValue(self.MW.PLC.RTD[0])
                #     self.MW.RTDSET1Button.SubWindow.TT2112.SetValue(self.MW.PLC.RTD[1])
                #     self.MW.RTDSET1Button.SubWindow.TT2113.SetValue(self.MW.PLC.RTD[2])
                #     self.MW.RTDSET1Button.SubWindow.TT2114.SetValue(self.MW.PLC.RTD[3])
                #     self.MW.RTDSET1Button.SubWindow.TT2115.SetValue(self.MW.PLC.RTD[4])
                #     self.MW.RTDSET1Button.SubWindow.TT2116.SetValue(self.MW.PLC.RTD[5])
                #     self.MW.RTDSET1Button.SubWindow.TT2117.SetValue(self.MW.PLC.RTD[6])

                # self.MW.PLC.NewData_Display = False

                # self.MW.TT2118.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2119.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2120.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6220.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6222.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2401.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2402.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2403.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2404.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2405.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2406.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2407.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2408.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2409.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2410.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2411.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2412.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2413.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2414.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2415.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2416.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2417.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2418.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2419.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2420.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2421.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2422.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2423.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2424.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2425.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2426.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2427.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2428.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2429.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2430.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2431.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2432.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2435.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2436.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2437.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2438.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2439.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2440.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2441.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2442.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2443.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2444.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2445.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2446.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2447.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2448.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2449.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6313.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6315.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6213.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6401.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6315.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6402.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6217.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6403.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6204.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6207.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6405.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6211.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6406.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6207.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6410.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6208.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6411.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6209.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6412.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2101.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2102.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2103.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2104.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2105.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2106.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2107.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2108.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2109.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT2110.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6414.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT6416.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT7202.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT7401.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT3402.SetValue(self.MW.PLC.RTD[0])
                # self.MW.TT3401.SetValue(self.MW.PLC.RTD[0])

                # Make sure the PLC is online
                # if self.MW.PLCLiveCounter == self.MW.PLC.LiveCounter
                # and not self.MW.PLCOnline.Field.property("Alarm"):
                #     self.MW.PLCOnline.Field.setText("Offline")
                #     self.MW.PLCOnline.SetAlarm()
                #     self.MW.PLCOnlineW.Field.setText("Offline")
                #     self.MW.PLCOnlineW.SetAlarm()
                # elif self.MW.PLCLiveCounter != self.MW.PLC.LiveCounter and self.MW.PLCOnline.Field.property("Alarm"):
                #     self.MW.PLCOnline.Field.setText("Online")
                #     self.MW.PLCOnline.ResetAlarm()
                #     self.MW.PLCOnlineW.Field.setText("Online")
                #     self.MW.PLCOnlineW.ResetAlarm()
                #     self.MW.PLCLiveCounter = self.MW.PLC.LiveCounter

                #     print("PPLC updating", datetime.datetime.now())

                # self.MW.PT4306.SetValue(self.MW.P.PT[0])
                # self.MW.PT4315.SetValue(self.MW.P.PT[1])
                # self.MW.PT4319.SetValue(self.MW.P.PT[2])
                # self.MW.PT4322.SetValue(self.MW.P.PT[3])
                # self.MW.PT4325.SetValue(self.MW.P.PT[4])
                # self.MW.PT6302.SetValue(self.MW.P.PT[5])
                # self.MW.PT4330.SetValue(self.MW.P.PT1)
                # self.MW.PT2316.SetValue(self.MW.P.PT1)
                # self.MW.PT2330.SetValue(self.MW.P.PT1)
                # self.MW.PT2335.SetValue(self.MW.P.PT1)
                # self.MW.PT1332.SetValue(self.MW.P.PT1)
                # self.MW.PT3414.SetValue(self.MW.P.PT1)
                # self.MW.PT3420.SetValue(self.MW.P.PT1)
                # self.MW.PT3308.SetValue(self.MW.P.PT1)
                # self.MW.PT3309.SetValue(self.MW.P.PT1)
                # self.MW.PT3311.SetValue(self.MW.P.PT1)
                # self.MW.PT3332.SetValue(self.MW.P.PT1)
                # self.MW.PT3333.SetValue(self.MW.P.PT1)
                #
                # self.MW.BFM4313.SetValue(self.MW.P.PT1)

                # self.MW.P.NewData_Display = False

                # Check if alarm values are met and set them
                # self.MW.AlarmButton.SubWindow.PT3309.CheckAlarm()
                # print(self.MW.AlarmButton.SubWindow.PT3309.AlarmMode.isChecked())
                # print(self.MW.AlarmButton.SubWIndow.PT3309.Alarm)
                # self.MW.AlarmButton.SubWindow.TT2111.CheckAlarm()
                # self.MW.AlarmButton.SubWindow.PT1101.CheckAlarm()
                # self.MW.AlarmButton.SubWindow.AlarmPTdir[0][0].CheckAlarm()
                # print(self.MW.AlarmButton.SubWindow.AlarmPTdir[0][0]==self.MW.AlarmButton.SubWindow.PT1101)



                # for i in range(0, len(self.MW.AlarmButton.SubWindow.AlarmRTD1list1D)):
                #     self.MW.AlarmButton.SubWindow.AlarmRTD1list1D[i].CheckAlarm()
                #
                # for i in range(0, self.MW.AlarmButton.SubWindow.i_RTD2_max):
                #     for j in range(0, self.MW.AlarmButton.SubWindow.j_RTD2_max):
                #         self.MW.AlarmButton.SubWindow.AlarmRTD2dir[i][j].CheckAlarm()
                #         if (i, j) == (self.MW.AlarmButton.SubWindow.i_RTD2_last, self.MW.AlarmButton.SubWindow.j_RTD2_last):
                #             break
                #     if (i, j) == (self.MW.AlarmButton.SubWindow.i_RTD2_last, self.MW.AlarmButton.SubWindow.j_RTD2_last):
                #         break
                #
                # for i in range(0, self.MW.AlarmButton.SubWindow.i_RTD3_max):
                #     for j in range(0, self.MW.AlarmButton.SubWindow.j_RTD3_max):
                #         self.MW.AlarmButton.SubWindow.AlarmRTD3dir[i][j].CheckAlarm()
                #         if (i, j) == (self.MW.AlarmButton.SubWindow.i_RTD3_last, self.MW.AlarmButton.SubWindow.j_RTD3_last):
                #             break
                #     if (i, j) == (self.MW.AlarmButton.SubWindow.i_RTD3_last, self.MW.AlarmButton.SubWindow.j_RTD3_last):
                #         break
                #
                # for i in range(0, self.MW.AlarmButton.SubWindow.i_RTD4_max):
                #     for j in range(0, self.MW.AlarmButton.SubWindow.j_RTD4_max):
                #         self.MW.AlarmButton.SubWindow.AlarmRTD4dir[i][j].CheckAlarm()
                #         if (i, j) == (self.MW.AlarmButton.SubWindow.i_RTD4_last, self.MW.AlarmButton.SubWindow.j_RTD4_last):
                #             break
                #     if (i, j) == (self.MW.AlarmButton.SubWindow.i_RTD4_last, self.MW.AlarmButton.SubWindow.j_RTD4_last):
                #         break
                #
                # for i in range(0, self.MW.AlarmButton.SubWindow.i_PT_max):
                #     for j in range(0, self.MW.AlarmButton.SubWindow.j_PT_max):
                #         self.MW.AlarmButton.SubWindow.AlarmPTdir[i][j].CheckAlarm()
                #         if (i, j) == (self.MW.AlarmButton.SubWindow.i_PT_last, self.MW.AlarmButton.SubWindow.j_PT_last):
                #             break
                #     if (i, j) == (self.MW.AlarmButton.SubWindow.i_PT_last, self.MW.AlarmButton.SubWindow.j_PT_last):
                #         break

                # # # rewrite collectalarm in updatedisplay

                # self.MW.AlarmButton.CollectAlarm(self.array)
                # self.MW.AlarmButton.CollectAlarm(
                # [self.MW.AlarmButton.SubWindow.PT3309])
                # self.MW.AlarmButton.CollectAlarm(
                #     [self.MW.AlarmButton.SubWindow.TT2111.Alarm, self.MW.AlarmButton.SubWindow.TT2115.Alarm])

                # self.MW.AlarmButton.CollectAlarm([self.MW.AlarmButton.SubWindow.TT2111.Alarm,
                #                                   self.MW.AlarmButton.SubWindow.TT2112.Alarm,
                #                                   self.MW.AlarmButton.SubWindow.TT2113.Alarm,
                #                                   self.MW.AlarmButton.SubWindow.TT2114.Alarm,
                #                                   self.MW.AlarmButton.SubWindow.TT2115.Alarm,
                #                                   self.MW.AlarmButton.SubWindow.TT2116.Alarm,
                #                                   self.MW.AlarmButton.SubWindow.TT2117.Alarm,
                #                                   self.MW.AlarmButton.SubWindow.TT2118.Alarm,
                #                                   self.MW.AlarmButton.SubWindow.TT2119.Alarm,
                #                                   self.MW.AlarmButton.SubWindow.TT2120.Alarm])
                # print("Alarm Status=", self.MW.AlarmButton.Button.Alarm)


                # try:
                #     raise RuntimeError("Test unhandlesd")
                # except:
                #     (type, value, traceback) = sys.exc_info()
                #     exception_hook(type, value, traceback)

                # if self.Client.receive_dic["MainAlarm"]:
                #     self.MW.AlarmButton.ButtonAlarmSetSignal()
                # else:
                #     self.MW.AlarmButton.ButtonAlarmResetSignal()
                # # # generally checkbutton.clicked -> move to updatedisplay

                # if self.MW.AlarmButton.Button.Alarm:
                #     self.MW.AlarmButton.ButtonAlarmSetSignal()
                #     # self.MW.AlarmButton.SubWindow.ReassignRTD1Order()
                #     # self.MW.AlarmButton.SubWindow.ResetOrder()
                #
                # else:
                #     self.MW.AlarmButton.ButtonAlarmResetSignal()
                #     self.MW.AlarmButton.SubWindow.ResetOrder()

                # if (self.MW.PT1.Value > 220 or self.MW.PT1.Value < 0) and not self.MW.PT1.Field.property("Alarm"):
                #     self.MW.PT1.SetAlarm()
                # elif self.MW.PT1.Value <= 220 and self.MW.PT1.Value >= 0 and self.MW.PT1.Field.property("Alarm"):
                #     self.MW.PT1.ResetAlarm()
                #
                # if (self.MW.PT2.Value > 220 or self.MW.PT2.Value < 120) and not self.MW.PT2.Field.property("Alarm"):
                #     self.MW.PT2.SetAlarm()
                # elif self.MW.PT2.Value <= 220 and self.MW.PT2.Value >= 120 and self.MW.PT2.Field.property("Alarm"):
                #     self.MW.PT2.ResetAlarm()
                #
                # if (self.MW.PT4.Value > 220 or self.MW.PT4.Value < 0) and not self.MW.PT4.Field.property("Alarm"):
                #     self.MW.PT4.SetAlarm()
                # elif self.MW.PT4.Value <= 220 and self.MW.PT4.Value >= 0 and self.MW.PT4.Field.property("Alarm"):
                #     self.MW.PT4.ResetAlarm()
                #
                # if (self.MW.PT8.Value > 220 or self.MW.PT8.Value < 0) and not self.MW.PT8.Field.property("Alarm"):
                #     self.MW.PT8.SetAlarm()
                # elif self.MW.PT8.Value <= 220 and self.MW.PT8.Value >= 0 and self.MW.PT8.Field.property("Alarm"):
                #     self.MW.PT8.ResetAlarm()
                #
                # if (self.MW.PT10.Value > 220 or self.MW.PT10.Value < 0) and not self.MW.PT10.Field.property("Alarm"):
                #     self.MW.PT10.SetAlarm()
                # elif self.MW.PT10.Value <= 220 and self.MW.PT10.Value >= 0 and self.MW.PT10.Field.property("Alarm"):
                #     self.MW.PT10.ResetAlarm()
                #
                # if (self.MW.Bellows.Value > 2 or self.MW.Bellows.Value < -.5) and not self.MW.Bellows.Field.property("Alarm"):
                #     self.MW.Bellows.SetAlarm()
                # elif self.MW.Bellows.Value <= 2 and self.MW.Bellows.Value >= -.5 and self.MW.Bellows.Field.property("Alarm"):
                #     self.MW.Bellows.ResetAlarm()
                #
                # if (self.MW.IV.Value > .1 or self.MW.IV.Value < -.1) and not self.MW.IV.Field.property("Alarm"):
                #     self.MW.IV.SetAlarm()
                # elif self.MW.IV.Value <= .1 and self.MW.IV.Value >= -.1 and self.MW.IV.Field.property("Alarm"):
                #     self.MW.IV.ResetAlarm()
                #
                # if (self.MW.PDiff.Value > 10 or self.MW.PDiff.Value < -10) and not self.MW.PDiff.Field.property("Alarm"):
                #     self.MW.PDiff.SetAlarm()
                # elif self.MW.PDiff.Value <= 10 and self.MW.PDiff.Value >= -10 and self.MW.PDiff.Field.property("Alarm"):
                #     self.MW.PDiff.ResetAlarm()
                #
                # if (self.MW.RTD37.Value > -5 or self.MW.RTD37.Value < -50) and not self.MW.RTD37.Field.property("Alarm"):
                #     self.MW.RTD37.SetAlarm()
                # elif self.MW.RTD37.Value <= -5 and self.MW.RTD37.Value >= -50 and self.MW.RTD37.Field.property("Alarm"):
                #     self.MW.RTD37.ResetAlarm()
                #
                # if (self.MW.RTD38.Value > -5 or self.MW.RTD38.Value < -50) and not self.MW.RTD38.Field.property("Alarm"):
                #     self.MW.RTD38.SetAlarm()
                # elif self.MW.RTD38.Value <= -5 and self.MW.RTD38.Value >= -50 and self.MW.RTD38.Field.property("Alarm"):
                #     self.MW.RTD38.ResetAlarm()
                #
                # if (self.MW.RTD42.Value > 0 or self.MW.RTD42.Value < -100) and not self.MW.RTD42.Field.property("Alarm"):
                #     self.MW.RTD42.SetAlarm()
                # elif self.MW.RTD42.Value <= 0 and self.MW.RTD42.Value >= -100 and self.MW.RTD42.Field.property("Alarm"):
                #     self.MW.RTD42.ResetAlarm()
                #
                # if (self.MW.RTD43.Value > -5 or self.MW.RTD43.Value < -50) and not self.MW.RTD43.Field.property("Alarm"):
                #     self.MW.RTD43.SetAlarm()
                # elif self.MW.RTD43.Value <= -5 and self.MW.RTD43.Value >= -50 and self.MW.RTD43.Field.property("Alarm"):
                #     self.MW.RTD43.ResetAlarm()
                #
                # if (self.MW.RTD45.Value > -5 or self.MW.RTD45.Value < -50) and not self.MW.RTD45.Field.property("Alarm"):
                #     self.MW.RTD45.SetAlarm()
                # elif self.MW.RTD45.Value <= -5 and self.MW.RTD45.Value >= -50 and self.MW.RTD45.Field.property("Alarm"):
                #     self.MW.RTD45.ResetAlarm()

                time.sleep(0.5)
        except:
            (type, value, traceback) = sys.exc_info()
            exception_hook(type, value, traceback)

    @QtCore.Slot()
    def stop(self):
        self.Running = False





# Code entry point

if __name__ == "__main__":



    App = QtWidgets.QApplication(sys.argv)

    MW = MainWindow()

    # MW = HeaterSubWindow()
    # recover data
    # MW.Recover()
    if platform.system() == "Linux":
        MW.show()
        MW.showMinimized()
    else:
        MW.show()
    MW.activateWindow()
    # save data

    sys.exit(App.exec_())

    # AW = AlarmWin()
    # if platform.system() == "Linux":
    #     AW.show()
    #     AW.showMinimized()
    # else:
    #     AW.show()
    # AW.activateWindow()
    # sys.exit(App.exec_())



"""
Note to run on VS on my computer...

import os
os.chdir("D:\\Pico\\SlowDAQ\\Qt\\SlowDAQ")
exec(open("SlowDAQ.py").read())
"""
