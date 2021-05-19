"""
This is the main SlowDAQ code used to read/setproperties of the TPLC and PPLC

By: Mathieu Laurin														

v0.1.0 Initial code 29/11/19 ML	
v0.1.1 Read and write implemented 08/12/19 ML
v0.1.2 Alarm implemented 07/01/20 ML
v0.1.3 PLC online detection, poll PLCs only when values are updated, fix Centos window size bug 04/03/20 ML 
"""

import os
import sys
import time
import platform
import datetime
import random

from PySide2 import QtWidgets, QtCore, QtGui

from SlowDAQ_SBC_v1 import *
from TPLC_v1 import TPLC
from PPLC_v1 import PPLC
from PICOPW import VerifyPW
from Database_SBC import *
from SlowDAQWidgets_SBC_v1 import *


VERSION = "v0.1.3"
SMALL_LABEL_STYLE = "background-color: rgb(204,204,204); border-radius: 10px; font-family: \"Calibri\";" \
                    " font-size: 14px;" \
                    " font-weight: bold;"
LABEL_STYLE = "background-color: rgb(204,204,204); border-radius: 10px; font-family: \"Calibri\"; " \
              "font-size: 18px; font-weight: bold;"
TITLE_STYLE = "background-color: rgb(204,204,204); border-radius: 10px; font-family: \"Calibri\";" \
              " font-size: 22px; font-weight: bold;"
ADMIN_TIMER = 30000
PLOTTING_SCALE = 0.66
ADMIN_PASSWORD = "60b6a2988e4ee1ad831ad567ad938adcc8e294825460bbcab26c1948b935bdf133e9e2c98ad4eafc622f4" \
                 "f5845cf006961abcc0a4007e3ac87d26c8981b792259f3f4db207dc14dbff315071c2f419122f1367668" \
                 "31c12bff0da3a2314ca2266"
BORDER_STYLE = "border-style: outset; border-width: 2px; border-radius: 6px; border-color: black;"


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

        self.resize(2400, 1400)  # Open at center using resized
        self.setMinimumSize(2400, 1400)
        self.setWindowTitle("SlowDAQ " + VERSION)
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.ImagePath, "Logo white_resized.png")))

        # Tabs, backgrounds & labels

        self.Tab = QtWidgets.QTabWidget(self)
        self.Tab.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.Tab.setStyleSheet("font-weight: bold; font-size: 20px; font-family: Calibri;")
        self.Tab.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.Tab.setGeometry(QtCore.QRect(0, 0, 2400, 1400))

        self.ThermosyphonTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.ThermosyphonTab, "Thermosyphon Main Panel")

        self.ThermosyphonTab.Background = QtWidgets.QLabel(self.ThermosyphonTab)
        self.ThermosyphonTab.Background.setScaledContents(True)
        self.ThermosyphonTab.Background.setStyleSheet('background-color:black;')
        pixmap_thermalsyphon = QtGui.QPixmap(os.path.join(self.ImagePath, "Thermosyphon.png"))
        pixmap_thermalsyphon = pixmap_thermalsyphon.scaledToWidth(2400)
        self.ThermosyphonTab.Background.setPixmap(QtGui.QPixmap(pixmap_thermalsyphon))
        self.ThermosyphonTab.Background.move(0, 0)
        self.ThermosyphonTab.Background.setAlignment(QtCore.Qt.AlignCenter)

        self.ChamberTab = QtWidgets.QWidget()
        self.Tab.addTab(self.ChamberTab, "Inner Chamber Components")

        self.ChamberTab.Background = QtWidgets.QLabel(self.ChamberTab)
        self.ChamberTab.Background.setScaledContents(True)
        self.ChamberTab.Background.setStyleSheet('background-color:black;')
        pixmap_chamber = QtGui.QPixmap(os.path.join(self.ImagePath, "Chamber_simplified.png"))
        pixmap_chamber = pixmap_chamber.scaledToWidth(2400)
        self.ChamberTab.Background.setPixmap(QtGui.QPixmap(pixmap_chamber))
        self.ChamberTab.Background.move(0, 0)
        self.ChamberTab.Background.setObjectName("ChamberBkg")

        self.FluidTab = QtWidgets.QWidget()
        self.Tab.addTab(self.FluidTab, "Fluid System")

        self.FluidTab.Background = QtWidgets.QLabel(self.FluidTab)
        self.FluidTab.Background.setScaledContents(True)
        self.FluidTab.Background.setStyleSheet('background-color:black;')
        pixmap_Fluid = QtGui.QPixmap(os.path.join(self.ImagePath, "CF4_XeAr_Panel_cryogenic.png"))
        pixmap_Fluid = pixmap_Fluid.scaledToWidth(2400)
        self.FluidTab.Background.setPixmap(QtGui.QPixmap(pixmap_Fluid))
        self.FluidTab.Background.move(0, 0)
        self.FluidTab.Background.setAlignment(QtCore.Qt.AlignCenter)
        self.FluidTab.Background.setObjectName("FluidBkg")

        self.HydraulicTab = QtWidgets.QWidget()
        self.Tab.addTab(self.HydraulicTab, "Hydraulic Apparatus")

        self.HydraulicTab.Background = QtWidgets.QLabel(self.HydraulicTab)
        self.HydraulicTab.Background.setScaledContents(True)
        self.HydraulicTab.Background.setStyleSheet('background-color:black;')
        pixmap_Hydraulic = QtGui.QPixmap(os.path.join(self.ImagePath, "Hydraulic_apparatus.png"))
        pixmap_Hydraulic = pixmap_Hydraulic.scaledToWidth(2400)
        self.HydraulicTab.Background.setPixmap(QtGui.QPixmap(pixmap_Hydraulic))
        self.HydraulicTab.Background.move(0, 0)
        self.HydraulicTab.Background.setAlignment(QtCore.Qt.AlignCenter)
        self.HydraulicTab.Background.setObjectName("HydraulicBkg")

        self.DatanSignalTab = QtWidgets.QWidget()
        self.Tab.addTab(self.DatanSignalTab, "Data and Signal Panel")

        self.DatanSignalTab.Background = QtWidgets.QLabel(self.DatanSignalTab)
        self.DatanSignalTab.Background.setScaledContents(True)
        self.DatanSignalTab.Background.setStyleSheet('background-color:black;')
        pixmap_DatanSignal = QtGui.QPixmap(os.path.join(self.ImagePath, "Default_Background.png"))
        pixmap_DatanSignal = pixmap_DatanSignal.scaledToWidth(2400)
        self.DatanSignalTab.Background.setPixmap(QtGui.QPixmap(pixmap_DatanSignal))
        self.DatanSignalTab.Background.move(0, 0)
        self.DatanSignalTab.Background.setAlignment(QtCore.Qt.AlignCenter)
        self.DatanSignalTab.Background.setObjectName("DatanSignalBkg")

        # Data saving and recovery
        # Data setting form is ended with .ini and directory is https://doc.qt.io/archives/qtforpython-5.12/PySide2/QtCore/QSettings.html depending on the System
        self.settings = QtCore.QSettings("$HOME/.config//SBC/SlowControl.ini", QtCore.QSettings.IniFormat)

        # Temperature tab buttons

        self.Tstatus = FunctionButton(self.ThermosyphonTab)
        self.Tstatus.StatusWindow.resize(1000, 1050)
        self.Tstatus.StatusWindow.thermosyphon()
        self.Tstatus.move(0, 0)
        self.Tstatus.Button.setText("Thermosyphon status")

        self.LoginT = SingleButton(self.ThermosyphonTab)
        self.LoginT.move(340, 1200)
        self.LoginT.Label.setText("Login")
        self.LoginT.Button.setText("Guest")

        self.GV4301 = PnID_Alone(self.ThermosyphonTab)
        self.GV4301.Label.setText("GV4301")
        self.GV4301.move(185, 110)

        self.PRV4302 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4302.Label.setText("PRV4302")
        self.PRV4302.move(300, 32)

        self.MCV4303 = PnID_Alone(self.ThermosyphonTab)
        self.MCV4303.Label.setText("MCV4303")
        self.MCV4303.move(500, 80)

        self.RG4304 = PnID_Alone(self.ThermosyphonTab)
        self.RG4304.Label.setText("RG4304")
        self.RG4304.move(700, 110)

        self.MV4305 = PnID_Alone(self.ThermosyphonTab)
        self.MV4305.Label.setText("MV4305")
        self.MV4305.move(864, 110)

        self.PT4306 = Indicator(self.ThermosyphonTab)
        self.PT4306.Label.setText("PT4306")
        self.PT4306.move(1020, 60)
        self.PT4306.SetUnit(" psi")

        self.PV4307 = Valve(self.ThermosyphonTab)
        self.PV4307.Label.setText("PV4307")
        self.PV4307.move(925, 190)

        self.PV4308 = Valve(self.ThermosyphonTab)
        self.PV4308.Label.setText("PV4308")
        self.PV4308.move(850, 320)

        self.MV4309 = PnID_Alone(self.ThermosyphonTab)
        self.MV4309.Label.setText("MV4309")
        self.MV4309.move(390, 260)

        self.PG4310 = PnID_Alone(self.ThermosyphonTab)
        self.PG4310.Label.setText("PG4310")
        self.PG4310.move(225, 220)

        self.PRV4311 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4311.Label.setText("PRV4311")
        self.PRV4311.move(305, 190)

        self.VP4312 = PnID_Alone(self.ThermosyphonTab)
        self.VP4312.Label.setText("VP4312")
        self.VP4312.move(75, 260)

        self.BFM4313 = Indicator(self.ThermosyphonTab)
        self.BFM4313.Label.setText("BFM4313")
        self.BFM4313.move(1250, 340)
        self.BFM4313.SetUnit(" bfm")

        self.MCV4314 = PnID_Alone(self.ThermosyphonTab)
        self.MCV4314.Label.setText("MCV4314")
        self.MCV4314.move(1230, 470)

        self.PT4315 = Indicator(self.ThermosyphonTab)
        self.PT4315.Label.setText("PT4315")
        self.PT4315.move(950, 440)
        self.PT4315.SetUnit(" psi")

        self.PG4316 = PnID_Alone(self.ThermosyphonTab)
        self.PG4316.Label.setText("PG4316")
        self.PG4316.move(820, 470)

        self.PV4317 = Valve(self.ThermosyphonTab)
        self.PV4317.Label.setText("PV4317")
        self.PV4317.move(520, 380)

        self.PV4318 = Valve(self.ThermosyphonTab)
        self.PV4318.Label.setText("PV4318")
        self.PV4318.move(250, 580)

        self.PT4319 = Indicator(self.ThermosyphonTab)
        self.PT4319.Label.setText("PT4319")
        self.PT4319.move(570, 720)
        self.PT4319.SetUnit(" psi")

        self.PRV4320 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4320.Label.setText("PRV4320")
        self.PRV4320.move(570, 860)

        self.PV4321 = Valve(self.ThermosyphonTab)
        self.PV4321.Label.setText("PV4321")
        self.PV4321.move(530, 580)

        self.PT4322 = Indicator(self.ThermosyphonTab)
        self.PT4322.Label.setText("PT4322")
        self.PT4322.move(850, 720)
        self.PT4322.SetUnit(" psi")

        self.PRV4323 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4323.Label.setText("PRV4323")
        self.PRV4323.move(850, 860)

        self.PV4324 = Valve(self.ThermosyphonTab)
        self.PV4324.Label.setText("PV4324")
        self.PV4324.move(1100, 580)

        self.PT4325 = Indicator(self.ThermosyphonTab)
        self.PT4325.Label.setText("PT4325")
        self.PT4325.move(1150, 720)
        self.PT4325.SetUnit(" psi")

        self.PRV4326 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4326.Label.setText("PRV4326")
        self.PRV4326.move(1150, 860)

        self.SV4327 = Valve(self.ThermosyphonTab)
        self.SV4327.Label.setText("SV4327")
        self.SV4327.move(120, 330)

        self.SV4328 = Valve(self.ThermosyphonTab)
        self.SV4328.Label.setText("SV4328")

        self.SV4328.move(1350, 60)

        self.SV4329 = Valve(self.ThermosyphonTab)
        self.SV4329.Label.setText("SV4329")
        self.SV4329.move(1700, 60)

        self.TT4330 = Indicator(self.ThermosyphonTab)
        self.TT4330.Label.setText("TT4330")
        self.TT4330.move(1915, 55)

        self.SV4331 = Valve(self.ThermosyphonTab)
        self.SV4331.Label.setText("SV4331")
        self.SV4331.move(1340, 200)

        self.SV4332 = Valve(self.ThermosyphonTab)
        self.SV4332.Label.setText("SV4332")
        self.SV4332.move(1450, 300)

        self.PRV4333 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4333.Label.setText("PRV4333")
        self.PRV4333.move(900, 650)

        self.PT6302 = Indicator(self.ThermosyphonTab)
        self.PT6302.Label.setText("PT6302")
        self.PT6302.move(2030, 690)
        self.PT6302.SetUnit(" psi")

        self.PRV6303 = PnID_Alone(self.ThermosyphonTab)
        self.PRV6303.Label.setText("PRV6303")
        self.PRV6303.move(1700, 700)

        self.MV6304 = PnID_Alone(self.ThermosyphonTab)
        self.MV6304.Label.setText("MV6304")
        self.MV6304.move(1810, 650)

        self.HE6201 = PnID_Alone(self.ThermosyphonTab)
        self.HE6201.Label.setText("HE6201")
        self.HE6201.move(1410, 1100)

        self.EV6204 = PnID_Alone(self.ThermosyphonTab)
        self.EV6204.Label.setText("EV6204")
        self.EV6204.move(930, 1100)

        self.TPLCOnline = State(self.ThermosyphonTab)
        self.TPLCOnline.move(200, 1200)
        self.TPLCOnline.Label.setText("TPLC link")
        self.TPLCOnline.Field.setText("Offline")
        self.TPLCOnline.SetAlarm()

        self.PPLCOnline = State(self.ThermosyphonTab)
        self.PPLCOnline.move(60, 1200)
        self.PPLCOnline.Label.setText("PPLC link")
        self.PPLCOnline.Field.setText("Offline")
        self.PPLCOnline.SetAlarm()

        # Chamber tab buttons

        self.LoginP = SingleButton(self.ChamberTab)
        self.LoginP.move(140, 1200)
        self.LoginP.Label.setText("Login")
        self.LoginP.Button.setText("Guest")

        self.RTDSET1 = FunctionButton(self.ChamberTab)
        self.RTDSET1.StatusWindow.RTDset1()
        self.RTDSET1.move(300, 330)
        self.RTDSET1.Button.setText("RTDSET1")

        self.RTDSET2 = FunctionButton(self.ChamberTab)
        self.RTDSET2.StatusWindow.RTDset2()
        self.RTDSET2.move(300, 510)
        self.RTDSET2.Button.setText("RTDSET2")

        self.RTDSET3 = FunctionButton(self.ChamberTab)
        self.RTDSET3.StatusWindow.RTDset3()
        self.RTDSET3.move(300, 610)
        self.RTDSET3.Button.setText("RTDSET3")

        self.RTDSET4 = FunctionButton(self.ChamberTab)
        self.RTDSET4.StatusWindow.RTDset4()
        self.RTDSET4.move(1780, 1150)
        self.RTDSET4.Button.setText("RTDSET4")

        self.HT6219 = Heater(self.ChamberTab)
        self.HT6219.move(820, 120)
        self.HT6219.Label.setText("HT6219")
        self.HT6219.HeaterSubWindow.setWindowTitle("HT6219")
        self.HT6219SUB = HeaterExpand(self.HT6219.HeaterSubWindow)
        self.HT6219SUB.Label.setText("HT6219")
        self.HT6219SUB.FBSwitch.Combobox.setItemText(0, "PT6220")
        self.HT6219SUB.FBSwitch.Combobox.setItemText(1, "EMPTY")
        self.HT6219.HeaterSubWindow.VL.addWidget(self.HT6219SUB)
        self.TT6220 = self.HT6219SUB.RTD1
        self.TT6220.Label.setText("TT6220")
        self.HT6219SUB.RTD2.Label.setText("EMPTY")

        self.HT6221 = Heater(self.ChamberTab)
        self.HT6221.move(1250, 120)
        self.HT6221.Label.setText("HT6221")
        self.HT6221.HeaterSubWindow.setWindowTitle("HT6221")
        self.HT6221SUB = HeaterExpand(self.HT6221.HeaterSubWindow)
        self.HT6221SUB.Label.setText("HT6221")
        self.HT6221.HeaterSubWindow.VL.addWidget(self.HT6221SUB)
        self.TT6222 = self.HT6221SUB.RTD1
        self.TT6222.Label.setText("TT6222")
        self.HT6221SUB.RTD2.Label.setText("EMPTY")

        self.HT6214 = Heater(self.ChamberTab)
        self.HT6214.move(1780, 145)
        self.HT6214.Label.setText("HT6214")
        self.HT6214.HeaterSubWindow.setWindowTitle("HT6214")
        self.HT6214SUB = HeaterExpand(self.HT6214.HeaterSubWindow)
        self.HT6214SUB.Label.setText("HT6214")
        self.HT6214.HeaterSubWindow.VL.addWidget(self.HT6214SUB)
        self.TT6213 = self.HT6214SUB.RTD1
        self.TT6213.Label.setText("TT6213")
        self.TT6401 = self.HT6214SUB.RTD2
        self.TT6401.Label.setText("TT6401")

        self.HT6216 = Heater(self.ChamberTab)
        self.HT6216.move(1780, 245)
        self.HT6216.Label.setText("HT6216")
        self.HT6216.HeaterSubWindow.setWindowTitle("HT6216")
        self.HT6216SUB = HeaterExpand(self.HT6216.HeaterSubWindow)
        self.HT6216SUB.Label.setText("HT6216")
        self.HT6216.HeaterSubWindow.VL.addWidget(self.HT6216SUB)
        self.TT6215 = self.HT6216SUB.RTD1
        self.TT6215.Label.setText("TT6215")
        self.TT6402 = self.HT6216SUB.RTD2
        self.TT6402.Label.setText("TT6402")

        self.HT6218 = Heater(self.ChamberTab)
        self.HT6218.move(1780, 345)
        self.HT6218.Label.setText("HT6218")
        self.HT6218.HeaterSubWindow.setWindowTitle("HT6218")
        self.HT6218SUB = HeaterExpand(self.HT6218.HeaterSubWindow)
        self.HT6218SUB.Label.setText("HT6218")
        self.HT6218.HeaterSubWindow.VL.addWidget(self.HT6218SUB)
        self.TT6217 = self.HT6218SUB.RTD1
        self.TT6217.Label.setText("TT6217")
        self.TT6403 = self.HT6218SUB.RTD2
        self.TT6403.Label.setText("TT6403")

        self.HT6202 = Heater(self.ChamberTab)
        self.HT6202.move(1780, 485)
        self.HT6202.Label.setText("HT6202")
        self.HT6202.HeaterSubWindow.setWindowTitle("HT6202")
        self.HT6202SUB = HeaterExpand(self.HT6202.HeaterSubWindow)
        self.HT6202SUB.Label.setText("HT6202")
        self.HT6202.HeaterSubWindow.VL.addWidget(self.HT6202SUB)
        self.TT6203 = self.HT6202SUB.RTD1
        self.TT6203.Label.setText("TT6203")
        self.TT6404 = self.HT6202SUB.RTD2
        self.TT6404.Label.setText("TT6404")

        self.HT6206 = Heater(self.ChamberTab)
        self.HT6206.move(1780, 585)
        self.HT6206.Label.setText("HT6206")
        self.HT6206.HeaterSubWindow.setWindowTitle("HT6206")
        self.HT6206SUB = HeaterExpand(self.HT6206.HeaterSubWindow)
        self.HT6206SUB.Label.setText("HT6206")
        self.HT6206.HeaterSubWindow.VL.addWidget(self.HT6206SUB)
        self.TT6207 = self.HT6206SUB.RTD1
        self.TT6207.Label.setText("TT6207")
        self.TT6405 = self.HT6206SUB.RTD2
        self.TT6405.Label.setText("TT6405")

        self.HT6210 = Heater(self.ChamberTab)
        self.HT6210.move(1780, 685)
        self.HT6210.Label.setText("HT6210")
        self.HT6210.HeaterSubWindow.setWindowTitle("HT6210")
        self.HT6210SUB = HeaterExpand(self.HT6210.HeaterSubWindow)
        self.HT6210SUB.Label.setText("HT6210")
        self.HT6210.HeaterSubWindow.VL.addWidget(self.HT6210SUB)
        self.TT6211 = self.HT6210SUB.RTD1
        self.TT6211.Label.setText("TT6211")
        self.TT6406 = self.HT6210SUB.RTD2
        self.TT6406.Label.setText("TT6406")

        self.HT6223 = Heater(self.ChamberTab)
        self.HT6223.move(1780, 785)
        self.HT6223.Label.setText("HT6223")
        self.HT6223.HeaterSubWindow.setWindowTitle("HT6223")
        self.HT6223SUB = HeaterExpand(self.HT6223.HeaterSubWindow)
        self.HT6223SUB.Label.setText("HT6223")
        self.HT6223.HeaterSubWindow.VL.addWidget(self.HT6223SUB)
        self.TT6407 = self.HT6223SUB.RTD1
        self.TT6407.Label.setText("TT6407")
        self.TT6410 = self.HT6223SUB.RTD2
        self.TT6410.Label.setText("TT6410")

        self.HT6224 = Heater(self.ChamberTab)
        self.HT6224.move(1780, 885)
        self.HT6224.Label.setText("HT6224")
        self.HT6224.HeaterSubWindow.setWindowTitle("HT6224")
        self.HT6224SUB = HeaterExpand(self.HT6224.HeaterSubWindow)
        self.HT6224SUB.Label.setText("HT6224")
        self.HT6224.HeaterSubWindow.VL.addWidget(self.HT6224SUB)
        self.TT6408 = self.HT6224SUB.RTD1
        self.TT6408.Label.setText("TT6408")
        self.TT6411 = self.HT6224SUB.RTD2
        self.TT6411.Label.setText("TT6411")

        self.HT6225 = Heater(self.ChamberTab)
        self.HT6225.move(1780, 985)
        self.HT6225.Label.setText("HT6225")
        self.HT6225.HeaterSubWindow.setWindowTitle("HT6225")
        self.HT6225SUB = HeaterExpand(self.HT6225.HeaterSubWindow)
        self.HT6225SUB.Label.setText("HT6225")
        self.HT6225.HeaterSubWindow.VL.addWidget(self.HT6225SUB)
        self.TT6409 = self.HT6225SUB.RTD1
        self.TT6409.Label.setText("TT6409")
        self.TT6412 = self.HT6225SUB.RTD2
        self.TT6412.Label.setText("TT6412")

        self.HT2123 = Heater(self.ChamberTab)
        self.HT2123.move(670, 820)
        self.HT2123.Label.setText("HT2123")
        self.HT2123.HeaterSubWindow.setWindowTitle("HT2123")
        self.HT2123SUB = HeaterExpand(self.HT2123.HeaterSubWindow)
        self.HT2123SUB.Label.setText("HT2123")
        self.HT2123.HeaterSubWindow.VL.addWidget(self.HT2123SUB)
        self.HT2123SUB.RTD1.Label.setText("EMPTY")
        self.HT2123SUB.RTD2.Label.setText("EMPTY")

        self.HT2124 = Heater(self.ChamberTab)
        self.HT2124.move(670, 820)
        self.HT2124.Label.setText("HT2124")
        self.HT2124.HeaterSubWindow.setWindowTitle("HT2124")
        self.HT2124SUB = HeaterExpand(self.HT2124.HeaterSubWindow)
        self.HT2124SUB.Label.setText("HT2124")
        self.HT2124.HeaterSubWindow.VL.addWidget(self.HT2124SUB)
        self.HT2124SUB.RTD1.Label.setText("EMPTY")
        self.HT2124SUB.RTD2.Label.setText("EMPTY")

        self.HT2125 = Heater(self.ChamberTab)
        self.HT2125.move(1030, 730)
        self.HT2125.Label.setText("HT2125")
        self.HT2125.HeaterSubWindow.setWindowTitle("HT2125")
        self.HT2125SUB = HeaterExpand(self.HT2125.HeaterSubWindow)
        self.HT2125SUB.Label.setText("HT2125")
        self.HT2125.HeaterSubWindow.VL.addWidget(self.HT2125SUB)
        self.HT2125SUB.RTD1.Label.setText("EMPTY")
        self.HT2125SUB.RTD2.Label.setText("EMPTY")

        self.PT1101 = Indicator(self.ChamberTab)
        self.PT1101.move(940, 990)
        self.PT1101.Label.setText("PT1101")
        self.PT1101.SetUnit(" psi")

        self.PT2121 = Indicator(self.ChamberTab)
        self.PT2121.move(1210, 990)
        self.PT2121.Label.setText("PT2121")
        self.PT2121.SetUnit(" psi")

        self.HT1202 = Heater(self.ChamberTab)
        self.HT1202.move(840, 1250)
        self.HT1202.Label.setText("HT1202")
        self.HT1202.HeaterSubWindow.setWindowTitle("HT1202")
        self.HT1202SUB = HeaterExpand(self.HT1202.HeaterSubWindow)
        self.HT1202SUB.Label.setText("HT1202")
        self.HT1202.HeaterSubWindow.VL.addWidget(self.HT1202SUB)
        self.TT6413 = self.HT1202SUB.RTD1
        self.TT6413.Label.setText("TT6413")
        self.TT6415 = self.HT1202SUB.RTD2
        self.TT6415.Label.setText("TT6415")

        self.HT2203 = Heater(self.ChamberTab)
        self.HT2203.move(1260, 1215)
        self.HT2203.Label.setText("HT2203")
        self.HT2203.HeaterSubWindow.setWindowTitle("HT2203")
        self.HT2203SUB = HeaterExpand(self.HT2203.HeaterSubWindow)
        self.HT2203SUB.Label.setText("HT2203")
        self.HT2203.HeaterSubWindow.VL.addWidget(self.HT2203SUB)
        self.TT6414 = self.HT2203SUB.RTD1
        self.TT6414.Label.setText("TT6414")
        self.TT6416 = self.HT2203SUB.RTD2
        self.TT6416.Label.setText("TT6416")

        # Fluid tab buttons

        self.PT2316 = Indicator(self.FluidTab)
        self.PT2316.move(1900, 360)
        self.PT2316.Label.setText("PT2316")
        self.PT2316.SetUnit(" psi")

        self.PT2330 = Indicator(self.FluidTab)
        self.PT2330.move(1780, 360)
        self.PT2330.Label.setText("PT2330")
        self.PT2330.SetUnit(" psi")

        self.PT2335 = Indicator(self.FluidTab)
        self.PT2335.move(1590, 420)
        self.PT2335.Label.setText("PT2335")
        self.PT2335.SetUnit(" psi")

        self.TT7401 = Indicator(self.FluidTab)
        self.TT7401.move(1985, 250)
        self.TT7401.Label.setText("TT7401")

        self.TT7202 = Indicator(self.FluidTab)
        self.TT7202.move(910, 530)
        self.TT7202.Label.setText("TT7202")

        self.LI2340 = Indicator(self.FluidTab)
        self.LI2340.move(2250, 880)
        self.LI2340.Label.setText("LI2340 ")

        self.PT1101Fluid = Indicator(self.FluidTab)
        self.PT1101Fluid.move(1030, 1300)
        self.PT1101Fluid.Label.setText("PT1101")
        self.PT1101Fluid.SetUnit(" psi")

        self.PT2121Fluid = Indicator(self.FluidTab)
        self.PT2121Fluid.move(1260, 1300)
        self.PT2121Fluid.Label.setText("PT2121")
        self.PT2121Fluid.SetUnit(" psi")

        self.MFC1316 = Heater(self.FluidTab)
        self.MFC1316.move(400, 800)
        self.MFC1316.Label.setText("MFC1316")
        self.MFC1316.HeaterSubWindow.setWindowTitle("MFC1316")
        self.MFC1316SUB = HeaterExpand(self.MFC1316.HeaterSubWindow)
        self.MFC1316SUB.Label.setText("MFC1316")
        self.MFC1316.HeaterSubWindow.VL.addWidget(self.MFC1316SUB)
        self.PT1332SUB = self.MFC1316SUB.RTD1
        self.PT1332SUB.Label.setText("TT6220")
        self.MFC1316SUB.RTD2.Label.setText("EMPTY")

        self.PT1332 = Indicator(self.FluidTab)
        self.PT1332.move(630, 900)
        self.PT1332.Label.setText("PT1332")
        self.PT1332.SetUnit(" psi")

        self.SV5305 = Valve(self.FluidTab)
        self.SV5305.Label.setText("SV5305")
        self.SV5305.move(1200, 530)

        self.SV5306 = Valve(self.FluidTab)
        self.SV5306.Label.setText("SV5306")
        self.SV5306.move(1150, 800)

        self.SV5307 = Valve(self.FluidTab)
        self.SV5307.Label.setText("SV5307")
        self.SV5307.move(1030, 620)

        self.SV5309 = Valve(self.FluidTab)
        self.SV5309.Label.setText("SV5309")
        self.SV5309.move(1130, 310)

        # Hydraulic buttons
        self.PU3305 = Valve(self.HydraulicTab)
        self.PU3305.Label.setText("PU3305")
        self.PU3305.move(365, 380)

        self.TT3401 = Indicator(self.HydraulicTab)
        self.TT3401.move(385, 500)
        self.TT3401.Label.setText("TT3401")

        self.TT3402 = Indicator(self.HydraulicTab)
        self.TT3402.move(90, 53)
        self.TT3402.Label.setText("TT3402")

        self.PT3314 = Indicator(self.HydraulicTab)
        self.PT3314.move(700, 450)
        self.PT3314.Label.setText("PT3314")
        self.PT3314.SetUnit(" psi")

        self.PT3320 = Indicator(self.HydraulicTab)
        self.PT3320.move(880, 530)
        self.PT3320.Label.setText("PT3320")
        self.PT3320.SetUnit(" psi")

        self.PT3308 = Indicator(self.HydraulicTab)
        self.PT3308.move(440, 1080)
        self.PT3308.Label.setText("PT3308")
        self.PT3308.SetUnit(" psi")

        self.PT3309 = Indicator(self.HydraulicTab)
        self.PT3309.move(665, 1140)
        self.PT3309.Label.setText("PT3309")
        self.PT3309.SetUnit(" psi")

        self.PT3311 = Indicator(self.HydraulicTab)
        self.PT3311.move(750, 1110)
        self.PT3311.Label.setText("PT3311")
        self.PT3311.SetUnit(" psi")

        self.HFSV3312 = Valve(self.HydraulicTab)
        self.HFSV3312.Label.setText("HFSV3312")
        self.HFSV3312.move(650, 1030)

        self.HFSV3323 = Valve(self.HydraulicTab)
        self.HFSV3323.Label.setText("HFSV3323")
        self.HFSV3323.move(1050, 1080)

        self.HFSV3331 = Valve(self.HydraulicTab)
        self.HFSV3331.Label.setText("HFSV3331")
        self.HFSV3331.move(1100, 320)

        self.PT3332 = Indicator(self.HydraulicTab)
        self.PT3332.move(1570, 1125)
        self.PT3332.Label.setText("PT3332")
        self.PT3332.SetUnit(" psi")

        self.PT3333 = Indicator(self.HydraulicTab)
        self.PT3333.move(1570, 1250)
        self.PT3333.Label.setText("PT3333")
        self.PT3333.SetUnit(" psi")

        self.SV3326 = Valve(self.HydraulicTab)
        self.SV3326.Label.setText("SV3326")
        self.SV3326.move(1200, 400)

        self.SV3329 = Valve(self.HydraulicTab)
        self.SV3329.Label.setText("SV3329")
        self.SV3329.move(1570, 470)

        self.SV3322 = Valve(self.HydraulicTab)
        self.SV3322.Label.setText("SV3322")
        self.SV3322.move(1000, 780)

        self.SERVO3321 = AOMultiLoop(self.HydraulicTab)
        self.SERVO3321.move(1200, 550)
        self.SERVO3321.Label.setText("SERVO3321")
        self.SERVO3321.HeaterSubWindow.setWindowTitle("SERVO3321")
        self.SERVO3321SUB = AOMutiLoopExpand(self.SERVO3321.HeaterSubWindow)
        self.SERVO3321SUB.Label.setText("SERVO3321")
        self.SERVO3321.HeaterSubWindow.VL.addWidget(self.SERVO3321SUB)
        self.SERVO3321SUB.RTD1.Label.setText("EMPTY")
        self.SERVO3321SUB.RTD2.Label.setText("EMPTY")

        self.SV3325 = Valve(self.HydraulicTab)
        self.SV3325.Label.setText("SV3325")
        self.SV3325.move(1200, 1000)

        self.SV3307 = Valve(self.HydraulicTab)
        self.SV3307.Label.setText("SV3307")
        self.SV3307.move(200, 1030)

        self.SV3310 = Valve(self.HydraulicTab)
        self.SV3310.Label.setText("SV3310")
        self.SV3310.move(800, 1240)

        self.TT7403 = Indicator(self.HydraulicTab)
        self.TT7403.move(1880, 950)
        self.TT7403.Label.setText("TT7403")

        self.LI3335 = Indicator(self.HydraulicTab)
        self.LI3335.move(2100, 950)
        self.LI3335.Label.setText("LI3335 ")

        self.LT3338 = Indicator(self.HydraulicTab)
        self.LT3338.move(2100, 990)
        self.LT3338.Label.setText("LT3338 ")

        self.LT3339 = Indicator(self.HydraulicTab)
        self.LT3339.move(2100, 1030)
        self.LT3339.Label.setText("LT3339 ")

        self.PT1101Hy = Indicator(self.HydraulicTab)
        self.PT1101Hy.move(1900, 800)
        self.PT1101Hy.Label.setText("PT1101")
        self.PT1101Hy.SetUnit(" psi")

        self.PT2121Hy = Indicator(self.HydraulicTab)
        self.PT2121Hy.move(2100, 800)
        self.PT2121Hy.Label.setText("PT2121")
        self.PT2121Hy.SetUnit(" psi")

        # Data and Signal Tab
        self.ReadSettings = Loadfile(self.DatanSignalTab)
        self.ReadSettings.move(50, 50)
        self.ReadSettings.LoadFileButton.clicked.connect(
            lambda x: self.Recover(address=self.ReadSettings.FilePath.text()))

        self.SaveSettings = CustomSave(self.DatanSignalTab)
        self.SaveSettings.move(700, 50)
        self.SaveSettings.SaveFileButton.clicked.connect(
            lambda x: self.Save(directory=self.SaveSettings.Head, project=self.SaveSettings.Tail))

        self.Datacheck = QtWidgets.QCheckBox(self.DatanSignalTab)
        self.Datacheck.move(800, 150)
        self.Datacheck.setText("Clone data into sbc slowcontrol database")
        self.Datacheck.setStyleSheet("color:white;")

        # Alarm button
        self.AlarmButton = AlarmButton(self)
        self.AlarmButton.StatusWindow.resize(1000, 500)
        self.AlarmButton.StatusWindow.AlarmWindow()

        self.AlarmButton.move(0, 1300)
        self.AlarmButton.Button.setText("Alarm Button")

        # Set user to guest by default
        self.User = "Guest"
        self.UserTimer = QtCore.QTimer(self)
        self.UserTimer.setSingleShot(True)
        self.UserTimer.timeout.connect(self.Timeout)
        self.ActivateControls(False)

        # Initialize PLC live counters
        self.PPLCLiveCounter = 0
        self.TPLCLiveCounter = 0

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
        self.P = PPLC()
        self.T = TPLC()

        # Read PPLC value on another thread
        self.PUpdateThread = QtCore.QThread()
        self.UpPPLC = UpdatePPLC(self.P)
        self.UpPPLC.moveToThread(self.PUpdateThread)
        self.PUpdateThread.started.connect(self.UpPPLC.run)
        self.PUpdateThread.start()

        # Read PPLC value on another thread
        # self.PUpdateThread = QtCore.QThread()
        # self.UpPPLC = UpdateTPLC(self.T)
        # self.UpPPLC.moveToThread(self.PUpdateThread)
        # self.PUpdateThread.started.connect(self.UpPPLC.run)
        # self.PUpdateThread.start()

        # Read TPLC value on another thread
        self.TUpdateThread = QtCore.QThread()
        self.UpTPLC = UpdateTPLC(self.T)
        self.UpTPLC.moveToThread(self.TUpdateThread)
        self.TUpdateThread.started.connect(self.UpTPLC.run)
        self.TUpdateThread.start()

        # Make sure PLCs values are initialized before trying to access them with update function
        time.sleep(2)

        # Update display values on another thread
        self.DUpdateThread = QtCore.QThread()
        self.UpDisplay = UpdateDisplay(self)
        self.UpDisplay.moveToThread(self.DUpdateThread)
        self.DUpdateThread.started.connect(self.UpDisplay.run)
        self.DUpdateThread.start()

        # Update database on another thread
        self.DataUpdateThread = QtCore.QThread()
        self.UpDatabase = UpdateDataBase(self)
        self.UpDatabase.moveToThread(self.DataUpdateThread)
        self.DataUpdateThread.started.connect(self.UpDatabase.run)
        self.DataUpdateThread.start()

    # Stop all updater threads
    @QtCore.Slot()
    def StopUpdater(self):
        self.UpPPLC.stop()
        self.PUpdateThread.quit()
        self.PUpdateThread.wait()
        self.UpTPLC.stop()
        self.TUpdateThread.quit()
        self.TUpdateThread.wait()

        self.UpDisplay.stop()
        self.DUpdateThread.quit()
        self.DUpdateThread.wait()

        self.UpDatabase.stop()
        self.DataUpdateThread.quit()
        self.DataUpdateThread.wait()

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
        self.T.SetHotRegionPIDMode(value)

    @QtCore.Slot(float)
    def SetHotRegionSetpoint(self, value):
        self.T.SetHotRegionSetpoint(value)

    @QtCore.Slot(float)
    def SetHotRegionP(self, value):
        self.T.SetHotRegionP(value)

    @QtCore.Slot(float)
    def SetHotRegionI(self, value):
        self.T.SetHotRegionI(value)

    @QtCore.Slot(float)
    def SetHotRegionD(self, value):
        self.T.SetHotRegionD(value)

    @QtCore.Slot(str)
    def SetColdRegionMode(self, value):
        self.T.SetColdRegionPIDMode(value)

    @QtCore.Slot(float)
    def SetColdRegionSetpoint(self, value):
        self.T.SetColdRegionSetpoint(value)

    @QtCore.Slot(float)
    def SetColdRegionP(self, value):
        self.T.SetColdRegionP(value)

    @QtCore.Slot(float)
    def SetColdRegionI(self, value):
        self.T.SetColdRegionI(value)

    @QtCore.Slot(float)
    def SetColdRegionD(self, value):
        self.T.SetColdRegionD(value)

    @QtCore.Slot(float)
    def SetBottomChillerSetpoint(self, value):
        self.T.SetColdRegionD(value)

    @QtCore.Slot(str)
    def SetBottomChillerState(self, value):
        self.T.SetBottomChillerState(value)

    @QtCore.Slot(float)
    def SetTopChillerSetpoint(self, value):
        self.T.SetTopChillerSetpoint(value)

    @QtCore.Slot(str)
    def SetTopChillerState(self, value):
        self.T.SetTopChillerState(value)

    @QtCore.Slot(float)
    def SetCameraChillerSetpoint(self, value):
        self.T.SetCameraChillerSetpoint(value)

    @QtCore.Slot(str)
    def SetCameraChillerState(self, value):
        self.T.SetCameraChillerState(value)

    @QtCore.Slot(str)
    def SetInnerHeaterState(self, value):
        self.T.SetInnerPowerState(value)

    @QtCore.Slot(float)
    def SetInnerHeaterPower(self, value):
        self.T.SetInnerPower(value)

    @QtCore.Slot(str)
    def SetFreonHeaterState(self, value):
        self.T.SetFreonPowerState(value)

    @QtCore.Slot(float)
    def SetFreonHeaterPower(self, value):
        self.T.SetFreonPower(value)

    @QtCore.Slot(str)
    def SetOuterCloseHeaterState(self, value):
        self.T.SetOuterClosePowerState(value)

    @QtCore.Slot(float)
    def SetOuterCloseHeaterPower(self, value):
        self.T.SetOuterClosePower(value)

    @QtCore.Slot(str)
    def SetOuterFarHeaterState(self, value):
        self.T.SetOuterFarPowerState(value)

    @QtCore.Slot(float)
    def SetOuterFarHeaterPower(self, value):
        self.T.SetOuterFarPower(value)

    @QtCore.Slot(float)
    def SetCoolingFlow(self, value):
        self.T.SetFlowValve(value)

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
        self.T.SetWaterChillerState(value)

    @QtCore.Slot(float)
    def SetWaterChillerSetpoint(self, value):
        self.T.SetWaterChillerSetpoint(value)

    @QtCore.Slot(str)
    def SetPrimingValve(self, value):
        if value == "Open":
            self.T.SetWaterPrimingPower("On")
        elif value == "Close":
            self.T.SetWaterPrimingPower("Off")

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

            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/TT4330/CheckBox",
                                   self.AlarmButton.StatusWindow.TT4330.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4306/CheckBox",
                                   self.AlarmButton.StatusWindow.PT4306.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4315/CheckBox",
                                   self.AlarmButton.StatusWindow.PT4315.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4319/CheckBox",
                                   self.AlarmButton.StatusWindow.PT4319.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4322/CheckBox",
                                   self.AlarmButton.StatusWindow.PT4322.AlarmMode.isChecked())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4325/CheckBox",
                                   self.AlarmButton.StatusWindow.PT4325.AlarmMode.isChecked())

            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/TT4330/LowLimit",
                                   self.AlarmButton.StatusWindow.TT4330.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4306/LowLimit",
                                   self.AlarmButton.StatusWindow.PT4306.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4315/LowLimit",
                                   self.AlarmButton.StatusWindow.PT4315.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4319/LowLimit",
                                   self.AlarmButton.StatusWindow.PT4319.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4322/LowLimit",
                                   self.AlarmButton.StatusWindow.PT4322.Low_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4325/LowLimit",
                                   self.AlarmButton.StatusWindow.PT4325.Low_Limit.Field.text())

            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/TT4330/HighLimit",
                                   self.AlarmButton.StatusWindow.TT4330.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4306/HighLimit",
                                   self.AlarmButton.StatusWindow.PT4306.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4315/HighLimit",
                                   self.AlarmButton.StatusWindow.PT4315.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4319/HighLimit",
                                   self.AlarmButton.StatusWindow.PT4319.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4322/HighLimit",
                                   self.AlarmButton.StatusWindow.PT4322.High_Limit.Field.text())
            self.settings.setValue("MainWindow/AlarmButton/StatusWindow/PT4325/HighLimit",
                                   self.AlarmButton.StatusWindow.PT4325.High_Limit.Field.text())
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

                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/TT4330/CheckBox",
                                             self.AlarmButton.StatusWindow.TT4330.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4306/CheckBox",
                                             self.AlarmButton.StatusWindow.PT4306.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4315/CheckBox",
                                             self.AlarmButton.StatusWindow.PT4315.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4319/CheckBox",
                                             self.AlarmButton.StatusWindow.PT4319.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4322/CheckBox",
                                             self.AlarmButton.StatusWindow.PT4322.AlarmMode.isChecked())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4325/CheckBox",
                                             self.AlarmButton.StatusWindow.PT4325.AlarmMode.isChecked())

                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/TT4330/LowLimit",
                                             self.AlarmButton.StatusWindow.TT4330.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4306/LowLimit",
                                             self.AlarmButton.StatusWindow.PT4306.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4315/LowLimit",
                                             self.AlarmButton.StatusWindow.PT4315.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4319/LowLimit",
                                             self.AlarmButton.StatusWindow.PT4319.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4322/LowLimit",
                                             self.AlarmButton.StatusWindow.PT4322.Low_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4325/LowLimit",
                                             self.AlarmButton.StatusWindow.PT4325.Low_Limit.Field.text())

                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/TT4330/HighLimit",
                                             self.AlarmButton.StatusWindow.TT4330.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4306/HighLimit",
                                             self.AlarmButton.StatusWindow.PT4306.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4315/HighLimit",
                                             self.AlarmButton.StatusWindow.PT4315.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4319/HighLimit",
                                             self.AlarmButton.StatusWindow.PT4319.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4322/HighLimit",
                                             self.AlarmButton.StatusWindow.PT4322.High_Limit.Field.text())
                self.customsettings.setValue("MainWindow/AlarmButton/StatusWindow/PT4325/HighLimit",
                                             self.AlarmButton.StatusWindow.PT4325.High_Limit.Field.text())
                print("saving data to ", path)
            except:
                print("Failed to custom save the settings.")

    def Recover(self, address="$HOME/.config//SBC/SlowControl.ini"):
        # address is the ini file 's directory you want to recover

        try:
            # default recover. If no other address is claimed, then recover settings from default directory
            if address == "$HOME/.config//SBC/SlowControl.ini":
                self.RecoverChecked(self.AlarmButton.StatusWindow.TT4330,
                                    "MainWindow/AlarmButton/StatusWindow/TT4330/CheckBox")
                self.RecoverChecked(self.AlarmButton.StatusWindow.PT4306,
                                    "MainWindow/AlarmButton/StatusWindow/PT4306/CheckBox")
                self.RecoverChecked(self.AlarmButton.StatusWindow.PT4315,
                                    "MainWindow/AlarmButton/StatusWindow/PT4315/CheckBox")
                self.RecoverChecked(self.AlarmButton.StatusWindow.PT4319,
                                    "MainWindow/AlarmButton/StatusWindow/PT4319/CheckBox")
                self.RecoverChecked(self.AlarmButton.StatusWindow.PT4322,
                                    "MainWindow/AlarmButton/StatusWindow/PT4322/CheckBox")
                self.RecoverChecked(self.AlarmButton.StatusWindow.PT4325,
                                    "MainWindow/AlarmButton/StatusWindow/PT4325/CheckBox")

                self.AlarmButton.StatusWindow.TT4330.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/TT4330/LowLimit"))
                self.AlarmButton.StatusWindow.TT4330.Low_Limit.UpdateValue()
                self.AlarmButton.StatusWindow.PT4306.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/PT4306/LowLimit"))
                self.AlarmButton.StatusWindow.PT4306.Low_Limit.UpdateValue()
                self.AlarmButton.StatusWindow.PT4315.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/PT4315/LowLimit"))
                self.AlarmButton.StatusWindow.PT4315.Low_Limit.UpdateValue()
                self.AlarmButton.StatusWindow.PT4319.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/PT4319/LowLimit"))
                self.AlarmButton.StatusWindow.PT4319.Low_Limit.UpdateValue()
                self.AlarmButton.StatusWindow.PT4322.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/PT4322/LowLimit"))
                self.AlarmButton.StatusWindow.PT4322.Low_Limit.UpdateValue()
                self.AlarmButton.StatusWindow.PT4325.Low_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/PT4325/LowLimit"))
                self.AlarmButton.StatusWindow.PT4325.Low_Limit.UpdateValue()

                self.AlarmButton.StatusWindow.TT4330.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/TT4330/HighLimit"))
                self.AlarmButton.StatusWindow.TT4330.High_Limit.UpdateValue()
                self.AlarmButton.StatusWindow.PT4306.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/PT4306/HighLimit"))
                self.AlarmButton.StatusWindow.PT4306.High_Limit.UpdateValue()
                self.AlarmButton.StatusWindow.PT4315.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/PT4315/HighLimit"))
                self.AlarmButton.StatusWindow.PT4315.High_Limit.UpdateValue()
                self.AlarmButton.StatusWindow.PT4319.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/PT4319/HighLimit"))
                self.AlarmButton.StatusWindow.PT4319.High_Limit.UpdateValue()
                self.AlarmButton.StatusWindow.PT4322.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/PT4322/HighLimit"))
                self.AlarmButton.StatusWindow.PT4322.High_Limit.UpdateValue()
                self.AlarmButton.StatusWindow.PT4325.High_Limit.Field.setText(self.settings.value(
                    "MainWindow/AlarmButton/StatusWindow/PT4325/HighLimit"))
                self.AlarmButton.StatusWindow.PT4325.High_Limit.UpdateValue()
            else:
                try:
                    # else, recover from the claimed directory
                    # address should be surfix with ini. Example:$HOME/.config//SBC/SlowControl.ini
                    directory = QtCore.QSettings(str(address), QtCore.QSettings.IniFormat)
                    print("Recovering from " + str(address))
                    self.RecoverChecked(GUIid=self.AlarmButton.StatusWindow.TT4330,
                                        subdir="MainWindow/AlarmButton/StatusWindow/TT4330/CheckBox",
                                        loadedsettings=directory)
                    self.RecoverChecked(GUIid=self.AlarmButton.StatusWindow.PT4306,
                                        subdir="MainWindow/AlarmButton/StatusWindow/PT4306/CheckBox",
                                        loadedsettings=directory)
                    self.RecoverChecked(GUIid=self.AlarmButton.StatusWindow.PT4315,
                                        subdir="MainWindow/AlarmButton/StatusWindow/PT4315/CheckBox",
                                        loadedsettings=directory)
                    self.RecoverChecked(GUIid=self.AlarmButton.StatusWindow.PT4319,
                                        subdir="MainWindow/AlarmButton/StatusWindow/PT4319/CheckBox",
                                        loadedsettings=directory)
                    self.RecoverChecked(GUIid=self.AlarmButton.StatusWindow.PT4322,
                                        subdir="MainWindow/AlarmButton/StatusWindow/PT4322/CheckBox",
                                        loadedsettings=directory)
                    self.RecoverChecked(GUIid=self.AlarmButton.StatusWindow.PT4325,
                                        subdir="MainWindow/AlarmButton/StatusWindow/PT4325/CheckBox",
                                        loadedsettings=directory)

                    self.AlarmButton.StatusWindow.TT4330.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/TT4330/LowLimit"))
                    self.AlarmButton.StatusWindow.TT4330.Low_Limit.UpdateValue()
                    self.AlarmButton.StatusWindow.PT4306.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/PT4306/LowLimit"))
                    self.AlarmButton.StatusWindow.PT4306.Low_Limit.UpdateValue()
                    self.AlarmButton.StatusWindow.PT4315.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/PT4315/LowLimit"))
                    self.AlarmButton.StatusWindow.PT4315.Low_Limit.UpdateValue()
                    self.AlarmButton.StatusWindow.PT4319.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/PT4319/LowLimit"))
                    self.AlarmButton.StatusWindow.PT4319.Low_Limit.UpdateValue()
                    self.AlarmButton.StatusWindow.PT4322.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/PT4322/LowLimit"))
                    self.AlarmButton.StatusWindow.PT4322.Low_Limit.UpdateValue()
                    self.AlarmButton.StatusWindow.PT4325.Low_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/PT4325/LowLimit"))
                    self.AlarmButton.StatusWindow.PT4325.Low_Limit.UpdateValue()

                    self.AlarmButton.StatusWindow.TT4330.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/TT4330/HighLimit"))
                    self.AlarmButton.StatusWindow.TT4330.High_Limit.UpdateValue()
                    self.AlarmButton.StatusWindow.PT4306.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/PT4306/HighLimit"))
                    self.AlarmButton.StatusWindow.PT4306.High_Limit.UpdateValue()
                    self.AlarmButton.StatusWindow.PT4315.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/PT4315/HighLimit"))
                    self.AlarmButton.StatusWindow.PT4315.High_Limit.UpdateValue()
                    self.AlarmButton.StatusWindow.PT4319.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/PT4319/HighLimit"))
                    self.AlarmButton.StatusWindow.PT4319.High_Limit.UpdateValue()
                    self.AlarmButton.StatusWindow.PT4322.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/PT4322/HighLimit"))
                    self.AlarmButton.StatusWindow.PT4322.High_Limit.UpdateValue()
                    self.AlarmButton.StatusWindow.PT4325.High_Limit.Field.setText(directory.value(
                        "MainWindow/AlarmButton/StatusWindow/PT4325/HighLimit"))
                    self.AlarmButton.StatusWindow.PT4325.High_Limit.UpdateValue()

                except:
                    print("Wrong Path to recover")
        except:
            print("1st time run the code in this environment. "
                  "Nothing to recover the settings. Please save the configuration to a ini file")
            pass

    def RecoverChecked(self, GUIid, subdir, loadedsettings=None):
        # add a function because you can not directly set check status to checkbox
        # GUIid should be form of "self.AlarmButton.StatusWindow.PT4315", is the variable name in the Main window
        # subdir like ""MainWindow/AlarmButton/StatusWindow/PT4306/CheckBox"", is the path file stored in the ini file
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
        self.VL.setContentsMargins(0, 0, 0, 0)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(30, 30))
        self.Label.setStyleSheet(TITLE_STYLE)
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
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


# Defines a status subwindow
class StatusWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(StatusWindow, self).__init__(parent)

        self.resize(2000, 1000)
        self.setMinimumSize(2000, 1000)
        self.setWindowTitle("Status Window")

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0, 0, 2000, 1000))

    def thermosyphon(self):
        # reset the size of the window
        self.setMinimumSize(1000, 500)
        self.resize(1000, 500)
        self.setWindowTitle("Thermosyphon Status Window")
        self.Widget.setGeometry(QtCore.QRect(0, 0, 1000, 500))

        # set gridlayout
        self.GL = QtWidgets.QGridLayout()
        # self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20, 20, 20, 20)
        self.GL.setSpacing(20)
        self.GL.setAlignment(QtCore.Qt.AlignCenter)

        self.Widget.setLayout(self.GL)

        self.PV4307 = MultiStatusIndicator(self)
        self.PV4307.Label.setText("PV4307")
        self.GL.addWidget(self.PV4307, 0, 0)

        self.PV4308 = MultiStatusIndicator(self)
        self.PV4308.Label.setText("PV4308")
        self.GL.addWidget(self.PV4308, 1, 0)

        self.PV4317 = MultiStatusIndicator(self)
        self.PV4317.Label.setText("PV4317")
        self.GL.addWidget(self.PV4317, 2, 0)

        self.PV4318 = MultiStatusIndicator(self)
        self.PV4318.Label.setText("PV4318")
        self.GL.addWidget(self.PV4318, 0, 1)

        self.PV4321 = MultiStatusIndicator(self)
        self.PV4321.Label.setText("PV4321")
        self.GL.addWidget(self.PV4321, 1, 1)

        self.PV4324 = MultiStatusIndicator(self)
        self.PV4324.Label.setText("PV4324")
        self.GL.addWidget(self.PV4324, 2, 1)

    def RTDset1(self):
        # reset the size of the window
        self.setMinimumSize(1000, 500)
        self.resize(1000, 500)
        self.setWindowTitle("RTD SET 1")
        self.Widget.setGeometry(QtCore.QRect(0, 0, 1000, 500))

        # set gridlayout
        self.GL = QtWidgets.QGridLayout()
        # self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20, 20, 20, 20)
        self.GL.setSpacing(20)
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

    def RTDset2(self):
        # reset the size of the window
        self.setMinimumSize(1000, 500)
        self.resize(1000, 500)
        self.setWindowTitle("RTD SET 2")
        self.Widget.setGeometry(QtCore.QRect(0, 0, 1000, 500))

        # set gridlayout
        self.GL = QtWidgets.QGridLayout()
        # self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20, 20, 20, 20)
        self.GL.setSpacing(20)
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

    def RTDset3(self):
        # reset the size of the window
        self.setMinimumSize(1000, 500)
        self.resize(1000, 500)
        self.setWindowTitle("RTD SET 3")
        self.Widget.setGeometry(QtCore.QRect(0, 0, 1000, 500))

        # set gridlayout
        self.GL = QtWidgets.QGridLayout()
        # self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20, 20, 20, 20)
        self.GL.setSpacing(20)
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

    def RTDset4(self):
        # reset the size of the window
        self.setMinimumSize(1000, 500)
        self.resize(1000, 500)
        self.setWindowTitle("RTD SET 4")
        self.Widget.setGeometry(QtCore.QRect(0, 0, 1000, 500))

        # set gridlayout
        self.GL = QtWidgets.QGridLayout()
        # self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20, 20, 20, 20)
        self.GL.setSpacing(20)
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

    def AlarmWindow(self):
        # reset the size of the window
        self.setMinimumSize(2000, 1000)
        self.resize(2000, 1000)
        self.setWindowTitle("Alarm Window")
        self.Widget.setGeometry(QtCore.QRect(0, 0, 2000, 1000))

        # variables usable for building widgets
        i_TT_max = 1
        j_TT_max = 1
        i_PT_max = 2
        j_PT_max = 3
        i_TT_last = 0
        j_TT_last = 0
        i_PT_last = 1
        j_PT_last = 1

        # Groupboxs for alarm/PT/TT
        self.GLTT = QtWidgets.QGridLayout()
        # self.GLTT = QtWidgets.QGridLayout(self)
        self.GLTT.setContentsMargins(20, 20, 20, 20)
        self.GLTT.setSpacing(20)
        self.GLTT.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupTT = QtWidgets.QGroupBox(self.Widget)
        self.GroupTT.setTitle("Temperature Transducer")
        self.GroupTT.setLayout(self.GLTT)
        self.GroupTT.move(0, 0)

        self.GLPT = QtWidgets.QGridLayout()
        # self.GLPT = QtWidgets.QGridLayout(self)
        self.GLPT.setContentsMargins(20, 20, 20, 20)
        self.GLPT.setSpacing(20)
        self.GLPT.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupPT = QtWidgets.QGroupBox(self.Widget)
        self.GroupPT.setTitle("Pressure Transducer")
        self.GroupPT.setLayout(self.GLPT)
        self.GroupPT.move(0, 500)

        self.TT4330 = AlarmStatusWidget(self)
        self.TT4330.Label.setText("TT4330")

        self.PT4306 = AlarmStatusWidget(self)
        self.PT4306.Label.setText("PT4306")

        self.PT4315 = AlarmStatusWidget(self)
        self.PT4315.Label.setText("PT4315")

        self.PT4319 = AlarmStatusWidget(self)
        self.PT4319.Label.setText("PT4319")

        self.PT4322 = AlarmStatusWidget(self)
        self.PT4322.Label.setText("PT4322")

        self.PT4325 = AlarmStatusWidget(self)
        self.PT4325.Label.setText("PT4325")

        # make a diretory for the alarm instrument and assign instrument to certain position
        self.AlarmTTdir = {0: {0: self.TT4330}}
        self.AlarmPTdir = {0: {0: self.PT4306, 1: self.PT4315, 2: self.PT4319},
                           1: {0: self.PT4322, 1: self.PT4325}}

        for i in range(0, i_TT_max):
            for j in range(0, j_TT_max):
                self.GLTT.addWidget(self.AlarmTTdir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (i_TT_last, j_TT_last):
                    break
            if (i, j) == (i_TT_last, j_TT_last):
                break

        for i in range(0, i_PT_max):
            for j in range(0, j_PT_max):
                self.GLPT.addWidget(self.AlarmPTdir[i][j], i, j)
                # end the position generator when i= last element's row number -1, j= last element's column number
                if (i, j) == (i_PT_last, j_PT_last):
                    break
            if (i, j) == (i_PT_last, j_PT_last):
                break

        # self.CheckButton = CheckButton(self)
        # self.CheckButton.move(1200, 100)
        # change it to self.TT.checkalarm
        # self.CheckButton.CheckButton.clicked.connect(self.TT4330.CheckAlarm)
        # self.CheckButton.CheckButton.clicked.connect(self.PT4306.CheckAlarm)
        # self.CheckButton.CheckButton.clicked.connect(self.PT4315.CheckAlarm)
        # self.CheckButton.CheckButton.clicked.connect(self.PT4319.CheckAlarm)
        # self.CheckButton.CheckButton.clicked.connect(self.PT4322.CheckAlarm)
        # self.CheckButton.CheckButton.clicked.connect(self.PT4325.CheckAlarm)
        # rewrite collectalarm in updatedisplay
        # self.CheckButton.CheckButton.clicked.connect(lambda x:
        # self.CheckButton.CollectAlarm(self.TT4330, self.PT4306, self.PT4315, self.PT4319, self.PT4322, self.PT4325))
        # generally checkbutton.clicked -> move to updatedisplay
        # self.CheckButton.CheckButton.clicked.connect(self.ReassignOrder)

    @QtCore.Slot()
    def ReassignOrder(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate
        TempRefTTdir = {0: {0: self.TT4330}}
        TempRefPTdir = {0: {0: self.PT4306, 1: self.PT4315, 2: self.PT4319}, 1: {0: self.PT4322, 1: self.PT4325}}
        TempTTdir = {0: {0: self.TT4330}}
        TempPTdir = {0: {0: self.PT4306, 1: self.PT4315, 2: self.PT4319}, 1: {0: self.PT4322, 1: self.PT4325}}
        l_TT = 0
        k_TT = 0
        l_PT = 0
        k_PT = 0
        i_TT_max = 1
        j_TT_max = 1
        i_PT_max = 2
        j_PT_max = 3
        l_TT_max = 3
        l_PT_max = 3
        i_TT_last = 0
        j_TT_last = 0
        i_PT_last = 1
        j_PT_last = 1
        # TT put alarm true widget to the begining of the diretory
        for i in range(0, i_TT_max):
            for j in range(0, j_TT_max):
                if TempRefTTdir[i][j].Alarm:
                    TempTTdir[k_TT][l_TT] = TempRefTTdir[i][j]
                    l_TT = l_TT + 1
                    if l_TT == l_TT_max:
                        l_TT = 0
                        k_TT = k_TT + 1
                if (i, j) == (i_TT_last, j_TT_last):
                    break
            if (i, j) == (i_TT_last, j_TT_last):
                break

        # TT put alarm false widget after that
        for i in range(0, i_TT_max):
            for j in range(0, j_TT_max):
                if not TempRefTTdir[i][j].Alarm:
                    TempTTdir[k_TT][l_TT] = TempRefTTdir[i][j]
                    l_TT = l_TT + 1
                    if l_TT == l_TT_max:
                        l_TT = 0
                        k_TT = k_TT + 1
                if (i, j) == (i_TT_last, j_TT_last):
                    break
            if (i, j) == (i_TT_last, j_TT_last):
                break

        # PT
        for i in range(0, i_PT_max):
            for j in range(0, j_PT_max):
                if TempRefPTdir[i][j].Alarm:
                    TempPTdir[k_PT][l_PT] = TempRefPTdir[i][j]
                    l_PT = l_PT + 1
                    if l_PT == l_PT_max:
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
                    if l_PT == l_PT_max:
                        l_PT = 0
                        k_PT = k_PT + 1
                    if (i, j) == (i_PT_last, j_PT_last):
                        break
                if (i, j) == (i_PT_last, j_PT_last):
                    break

        # Reassign position
        # end the position generator when i= last element's row number, j= last element's column number
        for i in range(0, i_TT_max):
            for j in range(0, j_TT_max):
                self.GLTT.addWidget(TempTTdir[i][j], i, j)
                if (i, j) == (i_TT_last, j_TT_last):
                    break
            if (i, j) == (i_TT_last, j_TT_last):
                break
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
        super(HeaterSubWindow, self).__init__(parent)

        self.resize(1100, 90)
        self.setMinimumSize(1100, 120)
        self.setWindowTitle("Detailed Information")

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0, 0, 1100, 120))

        self.VL = QtWidgets.QVBoxLayout()
        # self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0, 0, 0, 0)
        self.VL.setSpacing(3)
        self.VL.setAlignment(QtCore.Qt.AlignCenter)
        self.Widget.setLayout(self.VL)

        self.HL = QtWidgets.QHBoxLayout()
        # self.HL = QtWidgets.QHBoxLayout(self)
        self.HL.setContentsMargins(0, 0, 0, 0)
        self.HL.setSpacing(3)
        self.HL.setAlignment(QtCore.Qt.AlignCenter)
        self.VL.addLayout(self.HL)


# Define a function tab that shows the status of the widgets

class MultiStatusIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("MutiStatusIndicator")
        self.setGeometry(QtCore.QRect(0, 0, 200, 100))
        self.setMinimumSize(200, 100)
        self.setSizePolicy(sizePolicy)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0, 0, 0, 0)
        self.VL.setSpacing(3)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(10, 10))
        self.Label.setStyleSheet(TITLE_STYLE + BORDER_STYLE)
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
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
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("AlarmButton")
        self.setGeometry(QtCore.QRect(5, 5, 250, 80))
        self.setMinimumSize(250, 80)
        self.setSizePolicy(sizePolicy)

        # link the button to a new window
        self.StatusWindow = StatusWindow(self)

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setText("Button")
        self.Button.setGeometry(QtCore.QRect(5, 5, 250, 80))
        self.Button.setStyleSheet(
            "QWidget{" + LABEL_STYLE + "} QWidget[Alarm = true]{ background-color: rgb(255,132,27);} "
                                       "QWidget[Alarm = false]{ background-color: rgb(204,204,204);}")

        self.Button.setProperty("Alarm", False)
        self.Button.Alarm = False
        self.Button.clicked.connect(self.ButtonClicked)

    @QtCore.Slot()
    def ButtonClicked(self):
        self.StatusWindow.show()
        self.Signals.sSignal.emit(self.Button.text())

    @QtCore.Slot()
    def ButtonAlarmSignal(self):
        self.Button.setProperty("Alarm", self.Button.Alarm)
        self.Button.setStyle(self.Button.style())

    @QtCore.Slot()
    def CollectAlarm(self, *args):
        self.Collected = False
        for i in range(len(args)):
            # calculate collected alarm status
            self.Collected = self.Collected or args[i].Alarm
        self.Button.Alarm = self.Collected


# Define a function tab that shows the status of the widgets
class FunctionButton(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("FunctionButton")
        self.setGeometry(QtCore.QRect(5, 5, 250, 80))
        self.setMinimumSize(250, 80)
        self.setSizePolicy(sizePolicy)

        # link the button to a new window
        self.StatusWindow = StatusWindow(self)

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setText("Button")
        self.Button.setGeometry(QtCore.QRect(5, 5, 250, 80))
        self.Button.clicked.connect(self.ButtonClicked)

    @QtCore.Slot()
    def ButtonClicked(self):
        self.StatusWindow.show()
        self.Signals.sSignal.emit(self.Button.text())


# Defines a reusable layout containing widgets

class Chiller(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0, 0, 0, 0)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(30, 30))
        self.Label.setStyleSheet(TITLE_STYLE)
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
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
        self.VL.setContentsMargins(0, 0, 0, 0)

        self.Label = QtWidgets.QPushButton(self)
        self.Label.setMinimumSize(QtCore.QSize(30, 30))
        self.Label.setStyleSheet(TITLE_STYLE)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        # Add a Sub window popped out when click the name
        self.HeaterSubWindow = HeaterSubWindow(self)
        self.Label.clicked.connect(self.PushButton)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
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


# Defines a reusable layout containing widgets
class HeaterExpand(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("HeaterExpand")
        self.setGeometry(QtCore.QRect(0, 0, 1050, 80))
        self.setMinimumSize(1050, 80)
        self.setSizePolicy(sizePolicy)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0, 0, 0, 0)
        self.VL.setSpacing(5)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(30, 30))
        self.Label.setStyleSheet(TITLE_STYLE + BORDER_STYLE)
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
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


# Defines a reusable layout containing widgets
class AOMultiLoop(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0, 0, 0, 0)

        self.Label = QtWidgets.QPushButton(self)
        self.Label.setMinimumSize(QtCore.QSize(30, 30))
        self.Label.setStyleSheet(TITLE_STYLE + BORDER_STYLE)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        # Add a Sub window popped out when click the name
        self.HeaterSubWindow = HeaterSubWindow(self)
        self.Label.clicked.connect(self.PushButton)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
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
        self.setGeometry(QtCore.QRect(0, 0, 1050, 80))
        self.setMinimumSize(1050, 80)
        self.setSizePolicy(sizePolicy)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0, 0, 0, 0)
        self.VL.setSpacing(5)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(30, 30))
        self.Label.setStyleSheet(TITLE_STYLE + BORDER_STYLE)
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
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
        self.VL.setContentsMargins(0, 0, 0, 0)
        self.VL.setSpacing(3)

        self.Label = QtWidgets.QLabel(self)
        # self.Label.setMinimumSize(QtCore.QSize(30, 30))
        self.Label.setMinimumSize(QtCore.QSize(10, 10))
        self.Label.setStyleSheet(TITLE_STYLE + BORDER_STYLE)
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
        self.VL.addLayout(self.HL)

        self.Set = DoubleButton(self)
        self.Set.Label.setText("Set")
        self.Set.LButton.setText("open")
        self.Set.RButton.setText("close")
        self.HL.addWidget(self.Set)

        self.ActiveState = ColoredStatus(self, mode)
        # self.ActiveState = ColorIndicator(self) for test the function
        self.ActiveState.Label.setText("Active Status")
        self.HL.addWidget(self.ActiveState)


# Defines a reusable layout containing widgets
class Camera(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0, 0, 0, 0)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(30, 30))
        self.Label.setStyleSheet(TITLE_STYLE)
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
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
            print("PPLC updating", datetime.datetime.now())
            self.PPLC.ReadAll()
            time.sleep(2)

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
            print("TPLC updating", datetime.datetime.now())
            self.TPLC.ReadAll()
            time.sleep(2)

    @QtCore.Slot()
    def stop(self):
        self.Running = False


# Class to update myseeq database
class UpdateDataBase(QtCore.QObject):
    def __init__(self, MW, parent=None):
        super().__init__(parent)

        self.MW = MW
        self.db = mydatabase()
        self.Running = False
        print("begin updating Database")

    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:
            if self.MW.Datacheck.isChecked():
                self.dt = datetime_in_s()
                print("Database Updating", self.dt)

                if self.MW.T.NewData_Database:
                    print("Wrting TPLC data to database...")
                    self.db.insert_data_into_datastorage("TT2111", self.dt, self.MW.T.RTD[0])
                    self.MW.T.NewData_Database = False

                if self.MW.P.NewData_Database:
                    print("Writing PPLC data to database...")
                    self.db.insert_data_into_datastorage("PT4325", self.dt, self.MW.P.PT[4])
                    self.MW.P.NewData_Database = False
            else:
                print("Database Updating stopps.")
                pass

            time.sleep(4)

    @QtCore.Slot()
    def stop(self):
        self.Running = False


# Class to update display with PLC values every time PLC values ave been updated
# All commented lines are modbus variables not yet implemented on the PLCs           
class UpdateDisplay(QtCore.QObject):
    def __init__(self, MW, parent=None):
        super().__init__(parent)

        self.MW = MW
        self.Running = False

    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:

            print("Display updating", datetime.datetime.now())
            # print(self.MW.T.RTD)
            # print(3, self.MW.T.RTD[3])
            # for i in range(0,6):
            #     print(i, self.MW.T.RTD[i])

            if self.MW.T.NewData_Display:
                self.MW.RTDSET1.StatusWindow.TT2111.SetValue(self.MW.T.RTD[0])
                self.MW.RTDSET1.StatusWindow.TT2112.SetValue(self.MW.T.RTD[1])
                self.MW.RTDSET1.StatusWindow.TT2113.SetValue(self.MW.T.RTD[2])
                self.MW.RTDSET1.StatusWindow.TT2114.SetValue(self.MW.T.RTD[3])
                self.MW.RTDSET1.StatusWindow.TT2115.SetValue(self.MW.T.RTD[4])
                self.MW.RTDSET1.StatusWindow.TT2116.SetValue(self.MW.T.RTD[5])
                self.MW.RTDSET1.StatusWindow.TT2117.SetValue(self.MW.T.RTD[6])

                # self.MW.TT2118.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2119.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2120.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6220.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6222.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2401.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2402.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2403.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2404.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2405.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2406.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2407.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2408.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2409.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2410.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2411.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2412.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2413.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2414.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2415.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2416.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2417.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2418.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2419.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2420.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2421.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2422.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2423.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2424.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2425.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2426.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2427.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2428.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2429.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2430.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2431.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2432.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2435.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2436.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2437.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2438.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2439.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2440.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2441.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2442.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2443.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2444.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2445.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2446.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2447.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2448.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2449.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6313.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6315.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6213.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6401.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6315.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6402.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6217.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6403.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6204.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6207.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6405.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6211.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6406.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6207.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6410.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6208.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6411.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6209.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6412.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2101.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2102.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2103.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2104.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2105.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2106.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2107.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2108.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2109.SetValue(self.MW.T.RTD[0])
                # self.MW.TT2110.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6414.SetValue(self.MW.T.RTD[0])
                # self.MW.TT6416.SetValue(self.MW.T.RTD[0])
                # self.MW.TT7202.SetValue(self.MW.T.RTD[0])
                # self.MW.TT7401.SetValue(self.MW.T.RTD[0])
                # self.MW.TT3402.SetValue(self.MW.T.RTD[0])
                # self.MW.TT3401.SetValue(self.MW.T.RTD[0])

                # Make sure the PLC is online
                # if self.MW.TPLCLiveCounter == self.MW.T.LiveCounter
                # and not self.MW.TPLCOnline.Field.property("Alarm"):
                #     self.MW.TPLCOnline.Field.setText("Offline")
                #     self.MW.TPLCOnline.SetAlarm()
                #     self.MW.TPLCOnlineW.Field.setText("Offline")
                #     self.MW.TPLCOnlineW.SetAlarm()
                # elif self.MW.TPLCLiveCounter != self.MW.T.LiveCounter and self.MW.TPLCOnline.Field.property("Alarm"):
                #     self.MW.TPLCOnline.Field.setText("Online")
                #     self.MW.TPLCOnline.ResetAlarm()
                #     self.MW.TPLCOnlineW.Field.setText("Online")
                #     self.MW.TPLCOnlineW.ResetAlarm()
                #     self.MW.TPLCLiveCounter = self.MW.T.LiveCounter

                self.MW.T.NewData_Display = False

            if self.MW.P.NewData_Display:
                #     print("PPLC updating", datetime.datetime.now())

                # self.MW.PT4306.SetValue(self.MW.P.PT[0])
                # self.MW.PT4315.SetValue(self.MW.P.PT[1])
                # self.MW.PT4319.SetValue(self.MW.P.PT[2])
                # self.MW.PT4322.SetValue(self.MW.P.PT[3])
                self.MW.PT4325.SetValue(self.MW.P.PT[4])
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

                # Make sure the PLC is online
                # if self.MW.PPLCLiveCounter == self.MW.P.LiveCounter
                # and not self.MW.PPLCOnline.Field.property("Alarm"):
                #     self.MW.PPLCOnline.Field.setText("Offline")
                #     self.MW.PPLCOnline.SetAlarm()
                # elif self.MW.PPLCLiveCounter != self.MW.P.LiveCounter and self.MW.PPLCOnline.Field.property("Alarm"):
                #     self.MW.PPLCOnline.Field.setText("Online")
                #     self.MW.PPLCOnline.ResetAlarm()
                #     self.MW.PPLCLiveCounter = self.MW.P.LiveCounter

                self.MW.P.NewData_Display = False

            # Check if alarm values are met and set them
            self.MW.AlarmButton.StatusWindow.TT4330.CheckAlarm()
            self.MW.AlarmButton.StatusWindow.PT4306.CheckAlarm()
            self.MW.AlarmButton.StatusWindow.PT4315.CheckAlarm()
            self.MW.AlarmButton.StatusWindow.PT4319.CheckAlarm()
            self.MW.AlarmButton.StatusWindow.PT4322.CheckAlarm()
            self.MW.AlarmButton.StatusWindow.PT4325.CheckAlarm()
            # # rewrite collectalarm in updatedisplay
            self.MW.AlarmButton.CollectAlarm(self.MW.AlarmButton.StatusWindow.TT4330,
                                             self.MW.AlarmButton.StatusWindow.PT4306,
                                             self.MW.AlarmButton.StatusWindow.PT4315,
                                             self.MW.AlarmButton.StatusWindow.PT4319,
                                             self.MW.AlarmButton.StatusWindow.PT4322,
                                             self.MW.AlarmButton.StatusWindow.PT4325)
            self.MW.AlarmButton.ButtonAlarmSignal()
            # # generally checkbutton.clicked -> move to updatedisplay
            self.MW.AlarmButton.StatusWindow.ReassignOrder()

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

            time.sleep(1)

    @QtCore.Slot()
    def stop(self):
        self.Running = False


# Code entry point
# Code entry point
if __name__ == "__main__":
    App = QtWidgets.QApplication(sys.argv)

    MW = MainWindow()
    # recover data
    MW.Recover()
    if platform.system() == "Linux":
        MW.show()
        MW.showMinimized()
    else:
        MW.show()
    MW.activateWindow()
    # save data

    sys.exit(App.exec_())

"""
Note to run on VS on my computer...

import os
os.chdir("D:\\Pico\\SlowDAQ\\Qt\\SlowDAQ")
exec(open("SlowDAQ.py").read())
"""
