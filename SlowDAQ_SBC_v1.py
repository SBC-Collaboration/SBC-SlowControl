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

def TwoD_into_OneD(Twod_array):
    Oned_array=[]
    i_max=len(Twod_array)
    j_max=len(Twod_array[0])
    i_last=len(Twod_array)-1
    j_last=len(Twod_array[i_last])-1
    for i in range(0,i_max ):
        for j in range(0,j_max):
            Oned_array.append(Twod_array[i][j])
            if (i,j) == (i_last, j_last):
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

        self.ThermosyphonWin=ThermosyphonWindow()
        self.Tstatus = FunctionButton(self.ThermosyphonWin,self.ThermosyphonTab)
        self.Tstatus.SubWindow.resize(1000, 1050)
        # self.Tstatus.StatusWindow.thermosyphon()
        self.Tstatus.move(0, 0)
        self.Tstatus.Button.setText("Thermosyphon status")

        self.LoginT = SingleButton(self.ThermosyphonTab)
        self.LoginT.move(340, 1200)
        self.LoginT.Label.setText("Login")
        self.LoginT.Button.setText("Guest")

        #PLC test window
        self.TT9998=Indicator(self.ThermosyphonTab)
        self.TT9998.Label.setText("TT9998")
        self.TT9998.move(300,1100)

        self.TT9999 = Indicator(self.ThermosyphonTab)
        self.TT9999.Label.setText("TT9998")
        self.TT9999.move(300, 1150)

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

        self.RTDset1Win=RTDset1()
        self.RTDSET1Button = FunctionButton(self.RTDset1Win,self.ChamberTab)
        # self.RTDSET1.StatusWindow.RTDset1()
        self.RTDSET1Button.move(300, 330)
        self.RTDSET1Button.Button.setText("RTDSET1")

        self.RTDset2Win=RTDset2()
        self.RTDSET2Button = FunctionButton(self.RTDset2Win,self.ChamberTab)
        # self.RTDSET2.StatusWindow.RTDset2()
        self.RTDSET2Button.move(300, 510)
        self.RTDSET2Button.Button.setText("RTDSET2")

        self.RTDset3Win = RTDset3()
        self.RTDSET3Button = FunctionButton(self.RTDset3Win,self.ChamberTab)
        # self.RTDSET3.StatusWindow.RTDset3()
        self.RTDSET3Button.move(300, 610)
        self.RTDSET3Button.Button.setText("RTDSET3")

        self.RTDset4Win=RTDset4()
        self.RTDSET4Button = FunctionButton(self.RTDset4Win,self.ChamberTab)
        # self.RTDSET4.StatusWindow.RTDset4()
        self.RTDSET4Button.move(1780, 1150)
        self.RTDSET4Button.Button.setText("RTDSET4")

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
        self.Datacheck.setStyleSheet("background-color:gray;")

        # Alarm button
        self.AlarmWindow=AlarmWin()
        self.AlarmButton = AlarmButton(self.AlarmWindow,self)
        self.AlarmButton.SubWindow.resize(1000, 500)
        # self.AlarmButton.StatusWindow.AlarmWindow()

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
        # self.DataUpdateThread = QtCore.QThread()
        # self.UpDatabase = UpdateDataBase(self)
        # self.UpDatabase.moveToThread(self.DataUpdateThread)
        # self.DataUpdateThread.started.connect(self.UpDatabase.run)
        # self.DataUpdateThread.start()

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
            #set PT value
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

            #high limit

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


class ThermosyphonWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(2000, 1000)
        self.setMinimumSize(2000, 1000)
        self.setWindowTitle("Thermosyphon")

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0, 0, 2000, 1000))

        # reset the size of the window
        self.setMinimumSize(2000, 500)
        self.resize(1000, 500)
        self.setWindowTitle("Thermosyphon Status Window")
        self.Widget.setGeometry(QtCore.QRect(0, 0, 2000, 500))

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

        self.resize(2000, 1000)
        self.setMinimumSize(2000, 1000)
        self.setWindowTitle("Status Window")

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0, 0, 2000, 1000))

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

class RTDset2(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0, 0, 2000, 1000))

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

class RTDset3(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(2000, 1000)
        self.setMinimumSize(2000, 1000)
        self.setWindowTitle("Status Window")

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0, 0, 2000, 1000))

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

class RTDset4(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(2000, 1000)
        self.setMinimumSize(2000, 1000)
        self.setWindowTitle("Status Window")

        # self.Widget = QtWidgets.QWidget()
        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0, 0, 2000, 1000))

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


class AlarmWin(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0, 0, 2000, 1000))

        # reset the size of the window
        self.setMinimumSize(2000, 1100)
        self.resize(2000, 1100)
        self.setWindowTitle("Alarm Window")
        self.Widget.setGeometry(QtCore.QRect(0, 0, 2000, 1100))

        self.Tab = QtWidgets.QTabWidget(self)
        self.Tab.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.Tab.setStyleSheet("font-weight: bold; font-size: 20px; font-family: Calibri;")
        self.Tab.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.Tab.setGeometry(QtCore.QRect(0, 0, 2400, 1400))

        self.PressureTab=QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.PressureTab,"Pressure Transducers")

        self.RTDSET12Tab=QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDSET12Tab, "RTD SET 1&2")

        self.RTDSET34Tab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDSET34Tab, "RTD SET 3&4")

        self.RTDLEFTTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDLEFTTab, "HEATER RTDs and ETC")


        # Groupboxs for alarm/PT/TT

        self.GLPT = QtWidgets.QGridLayout()
        # self.GLPT = QtWidgets.QGridLayout(self)
        self.GLPT.setContentsMargins(20, 20, 20, 20)
        self.GLPT.setSpacing(20)
        self.GLPT.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupPT = QtWidgets.QGroupBox(self.PressureTab)
        self.GroupPT.setTitle("Pressure Transducer")
        self.GroupPT.setLayout(self.GLPT)
        self.GroupPT.move(0, 0)

        self.GLRTD1 = QtWidgets.QGridLayout()
        # self.GLRTD1 = QtWidgets.QGridLayout(self)
        self.GLRTD1.setContentsMargins(20, 20, 20, 20)
        self.GLRTD1.setSpacing(20)
        self.GLRTD1.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTD1 = QtWidgets.QGroupBox(self.RTDSET12Tab)
        self.GroupRTD1.setTitle("RTD SET 1")
        self.GroupRTD1.setLayout(self.GLRTD1)
        self.GroupRTD1.move(0, 0)

        self.GLRTD2 = QtWidgets.QGridLayout()
        # self.GLRTD2 = QtWidgets.QGridLayout(self)
        self.GLRTD2.setContentsMargins(20, 20, 20, 20)
        self.GLRTD2.setSpacing(20)
        self.GLRTD2.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTD2 = QtWidgets.QGroupBox(self.RTDSET12Tab)
        self.GroupRTD2.setTitle("RTD SET 2")
        self.GroupRTD2.setLayout(self.GLRTD2)
        self.GroupRTD2.move(0, 300)

        self.GLRTD3 = QtWidgets.QGridLayout()
        # self.GLRTD3 = QtWidgets.QGridLayout(self)
        self.GLRTD3.setContentsMargins(20, 20, 20, 20)
        self.GLRTD3.setSpacing(20)
        self.GLRTD3.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTD3 = QtWidgets.QGroupBox(self.RTDSET34Tab)
        self.GroupRTD3.setTitle("RTD SET 3")
        self.GroupRTD3.setLayout(self.GLRTD3)
        self.GroupRTD3.move(0, 0)

        self.GLRTD4 = QtWidgets.QGridLayout()
        # self.GLRTD4 = QtWidgets.QGridLayout(self)
        self.GLRTD4.setContentsMargins(20, 20, 20, 20)
        self.GLRTD4.setSpacing(20)
        self.GLRTD4.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTD4 = QtWidgets.QGroupBox(self.RTDSET34Tab)
        self.GroupRTD4.setTitle("RTD SET 4")
        self.GroupRTD4.setLayout(self.GLRTD4)
        self.GroupRTD4.move(0, 500)

        self.GLRTDLEFT = QtWidgets.QGridLayout()
        # self.GLRTDLEFT = QtWidgets.QGridLayout(self)
        self.GLRTDLEFT.setContentsMargins(20, 20, 20, 20)
        self.GLRTDLEFT.setSpacing(20)
        self.GLRTDLEFT.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTDLEFT = QtWidgets.QGroupBox(self.RTDLEFTTab)
        self.GroupRTDLEFT.setTitle(" LEFT RTDs ")
        self.GroupRTDLEFT.setLayout(self.GLRTDLEFT)
        self.GroupRTDLEFT.move(0, 0)

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

        #RTDSET34
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


        #RTDLEFT part

        self.TT4330 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT4330.Label.setText("TT4330")

        self.TT6220 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6220.Label.setText("TT6220")

        self.TT6213 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6213.Label.setText("TT6213")

        self.TT6401 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6401.Label.setText("TT6401")

        self.TT6215 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6215.Label.setText("TT6215")

        self.TT6402 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6402.Label.setText("TT6402")

        self.TT6217 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6217.Label.setText("TT6217")

        self.TT6403 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6403.Label.setText("TT6403")

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

        self.TT6223 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6223.Label.setText("TT6223")

        self.TT6410 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6410.Label.setText("TT6410")

        self.TT6408 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6408.Label.setText("TT6408")

        self.TT6409 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6409.Label.setText("TT6409")

        self.TT6412 = AlarmStatusWidget(self.RTDLEFTTab)
        self.TT6412.Label.setText("TT6412")

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

        self.AlarmRTD2dir = {0: {0: self.TT2401, 1: self.TT2402, 2: self.TT2403, 3: self.TT2404, 4: self.TT2405},
                             1: {0: self.TT2406, 1: self.TT2407, 2: self.TT2408, 3: self.TT2409, 4: self.TT2410},
                             2: {0: self.TT2411, 1: self.TT2412, 2: self.TT2413, 3: self.TT2414, 4: self.TT2415},
                             3: {0: self.TT2416, 1: self.TT2417, 2: self.TT2418, 3: self.TT2419, 4: self.TT2420},
                             4: {0: self.TT2421, 1: self.TT2422, 2: self.TT2423, 3: self.TT2424, 4: self.TT2425},
                             5: {0: self.TT2426, 1: self.TT2427, 2: self.TT2428, 3: self.TT2429, 4: self.TT2430},
                             6: {0: self.TT2431, 1: self.TT2432}}

        self.AlarmRTD3dir = {0: {0: self.TT2435, 1: self.TT2436, 2: self.TT2437, 3: self.TT2438, 4: self.TT2439},
                             1: {0: self.TT2440, 1: self.TT2441, 2: self.TT2442, 3: self.TT2443, 4: self.TT2444},
                             2: {0: self.TT2445, 1: self.TT2446, 2: self.TT2447, 3: self.TT2448, 4: self.TT2449}}

        self.AlarmRTD4dir = {0: {0: self.TT2101, 1: self.TT2102, 2: self.TT2103, 3: self.TT2104, 4: self.TT2105},
                             1: {0: self.TT2106, 1: self.TT2107, 2: self.TT2108, 3: self.TT2109, 4: self.TT2110}}

        self.AlarmPTdir = {0: {0: self.PT1101, 1: self.PT2316, 2: self.PT2321, 3: self.PT2330, 4: self.PT2335},
                           1: {0: self.PT3308, 1: self.PT3309, 2: self.PT3310, 3: self.PT3311, 4: self.PT3314},
                           2: {0: self.PT3320, 1: self.PT3333, 2: self.PT4306, 3: self.PT4315, 4: self.PT4319},
                           3: {0: self.PT4322, 1: self.PT4325}}

        self.AlarmRTDLEFTdir = {0: {0: self.TT4330, 1: self.TT6220, 2: self.TT6213, 3: self.TT6401, 4: self.TT6215},
                                1: {0: self.TT6402, 1: self.TT6217, 2: self.TT6403, 3: self.TT6203, 4: self.TT6404},
                                2: {0: self.TT6207, 1: self.TT6405, 2: self.TT6211, 3: self.TT6406, 4: self.TT6223},
                                3: {0: self.TT6410, 1: self.TT6408, 2: self.TT6409, 3: self.TT6412, 4: self.TT7202},
                                4: {0: self.TT7401, 1: self.TT3402, 2: self.TT3401, 3: self.TT7403}}


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
        #which is 4
        self.j_PT_max = len(self.AlarmPTdir[0])
        #which is 5
        self.i_RTD1_last = len(self.AlarmRTD1dir)-1
        # which is 1
        self.j_RTD1_last = len(self.AlarmRTD1dir[self.i_RTD1_last])-1
        #which is 4
        self.i_RTD2_last = len(self.AlarmRTD2dir) - 1
        self.j_RTD2_last = len(self.AlarmRTD2dir[self.i_RTD2_last]) - 1
        self.i_RTD3_last = len(self.AlarmRTD3dir) - 1
        self.j_RTD3_last = len(self.AlarmRTD3dir[self.i_RTD3_last]) - 1
        self.i_RTD4_last = len(self.AlarmRTD4dir) - 1
        self.j_RTD4_last = len(self.AlarmRTD4dir[self.i_RTD4_last]) - 1
        self.i_RTDLEFT_last = len(self.AlarmRTDLEFTdir) - 1
        self.j_RTDLEFT_last = len(self.AlarmRTDLEFTdir[self.i_RTDLEFT_last]) - 1
        self.i_PT_last = len(self.AlarmPTdir)-1
        #which is 3
        self.j_PT_last = len(self.AlarmPTdir[self.i_PT_last])-1
        #which is 1

        for i in range(0, self.i_RTD1_max):
            for j in range(0, self.j_RTD1_max):
                self.GLRTD1.addWidget(self.AlarmRTD1dir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_RTD1_last, self.j_RTD1_last):
                    break
            if (i, j) == (self.i_RTD1_last, self.j_RTD1_last):
                break

        for i in range(0, self.i_RTD2_max):
            for j in range(0, self.j_RTD2_max):
                self.GLRTD2.addWidget(self.AlarmRTD2dir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_RTD2_last, self.j_RTD2_last):
                    break
            if (i, j) == (self.i_RTD2_last, self.j_RTD2_last):
                break

        for i in range(0, self.i_RTD3_max):
            for j in range(0, self.j_RTD3_max):
                self.GLRTD3.addWidget(self.AlarmRTD3dir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_RTD3_last, self.j_RTD3_last):
                    break
            if (i, j) == (self.i_RTD3_last, self.j_RTD3_last):
                break

        for i in range(0, self.i_RTD4_max):
            for j in range(0, self.j_RTD4_max):
                self.GLRTD4.addWidget(self.AlarmRTD4dir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_RTD4_last, self.j_RTD4_last):
                    break
            if (i, j) == (self.i_RTD4_last, self.j_RTD4_last):
                break

        for i in range(0, self.i_RTDLEFT_max):
            for j in range(0, self.j_RTDLEFT_max):
                self.GLRTDLEFT.addWidget(self.AlarmRTDLEFTdir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_RTDLEFT_last, self.j_RTDLEFT_last):
                    break
            if (i, j) == (self.i_RTDLEFT_last, self.j_RTDLEFT_last):
                break

        for i in range(0, self.i_PT_max):
            for j in range(0, self.j_PT_max):
                self.GLPT.addWidget(self.AlarmPTdir[i][j], i, j)
                # end the position generator when i= last element's row number -1, j= last element's column number
                if (i, j) == (self.i_PT_last, self.j_PT_last):
                    break
            if (i, j) == (self.i_PT_last, self.j_PT_last):
                break


    @QtCore.Slot()
    def ReassignOrder(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate
        TempRefRTD1dir = self.AlarmRTD1dir
        TempRefRTD2dir = self.AlarmRTD2dir
        TempRefRTD3dir = self.AlarmRTD3dir
        TempRefRTD4dir = self.AlarmRTD4dir
        TempRefRTDLEFTdir = self.AlarmRTDLEFTdir
        TempRefPTdir = self.AlarmPTdir
        
        TempRTD1dir = self.AlarmRTD1dir
        TempRTD2dir = self.AlarmRTD2dir
        TempRTD3dir = self.AlarmRTD3dir
        TempRTD4dir = self.AlarmRTD4dir
        TempRTDLEFTdir = self.AlarmRTDLEFTdir
        TempPTdir = self.AlarmPTdir
        # l_RTD1_max is max number of column
        l_RTD1 = 0
        k_RTD1 = 0
        l_RTD2 = 0
        k_RTD2 = 0
        l_RTD3 = 0
        k_RTD3 = 0
        l_RTD4 = 0
        k_RTD4 = 0
        l_RTDLEFT = 0
        k_RTDLEFT = 0
        
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
        i_RTD1_max = len(self.AlarmRTD1dir)
        # which is 3
        j_RTD1_max = len(self.AlarmRTD1dir[0])
        # which is 5
        i_RTD2_max = len(self.AlarmRTD2dir)
        j_RTD2_max = len(self.AlarmRTD2dir[0])
        i_RTD3_max = len(self.AlarmRTD3dir)
        j_RTD3_max = len(self.AlarmRTD3dir[0])
        i_RTD4_max = len(self.AlarmRTD4dir)
        j_RTD4_max = len(self.AlarmRTD4dir[0])
        i_RTDLEFT_max = len(self.AlarmRTDLEFTdir)
        j_RTDLEFT_max = len(self.AlarmRTDLEFTdir[0])
        i_PT_max = len(self.AlarmPTdir)
        # which is 4
        j_PT_max = len(self.AlarmPTdir[0])
        # which is 5
        i_RTD1_last = len(self.AlarmRTD1dir) - 1
        # which is 2
        j_RTD1_last = len(self.AlarmRTD1dir[i_RTD1_last]) - 1
        # which is 4
        i_RTD2_last = len(self.AlarmRTD2dir) - 1
        j_RTD2_last = len(self.AlarmRTD2dir[i_RTD2_last]) - 1
        i_RTD3_last = len(self.AlarmRTD3dir) - 1
        j_RTD3_last = len(self.AlarmRTD3dir[i_RTD3_last]) - 1
        i_RTD4_last = len(self.AlarmRTD4dir) - 1
        j_RTD4_last = len(self.AlarmRTD4dir[i_RTD4_last]) - 1
        i_RTDLEFT_last = len(self.AlarmRTDLEFTdir) - 1
        j_RTDLEFT_last = len(self.AlarmRTDLEFTdir[i_RTDLEFT_last]) - 1
        i_PT_last = len(self.AlarmPTdir) - 1
        # which is 3
        j_PT_last = len(self.AlarmPTdir[i_PT_last]) - 1
        # which is 1
        l_RTD1_max = j_RTD1_max-1
        l_RTD2_max = j_RTD2_max - 1
        l_RTD3_max = j_RTD3_max - 1
        l_RTD4_max = j_RTD4_max - 1
        l_RTDLEFT_max = j_RTDLEFT_max - 1
        l_PT_max = j_PT_max-1
        # RTD1 put alarm true widget to the begining of the diretory
        for i in range(0, i_RTD1_max):
            for j in range(0, j_RTD1_max):
                if TempRefRTD1dir[i][j].Alarm:
                    TempRTD1dir[k_RTD1][l_RTD1] = TempRefRTD1dir[i][j]
                    l_RTD1 = l_RTD1 + 1
                    if l_RTD1 == l_RTD1_max:
                        l_RTD1 = 0
                        k_RTD1 = k_RTD1 + 1
                if (i, j) == (i_RTD1_last, j_RTD1_last):
                    break
            if (i, j) == (i_RTD1_last, j_RTD1_last):
                break

        # RTD1 put alarm false widget after that
        for i in range(0, i_RTD1_max):
            for j in range(0, j_RTD1_max):
                if not TempRefRTD1dir[i][j].Alarm:
                    TempRTD1dir[k_RTD1][l_RTD1] = TempRefRTD1dir[i][j]
                    l_RTD1 = l_RTD1 + 1
                    if l_RTD1 == l_RTD1_max:
                        l_RTD1 = 0
                        k_RTD1 = k_RTD1 + 1
                if (i, j) == (i_RTD1_last, j_RTD1_last):
                    break
            if (i, j) == (i_RTD1_last, j_RTD1_last):
                break

        for i in range(0, i_RTD2_max):
            for j in range(0, j_RTD2_max):
                if TempRefRTD2dir[i][j].Alarm:
                    TempRTD2dir[k_RTD2][l_RTD2] = TempRefRTD2dir[i][j]
                    l_RTD2 = l_RTD2 + 1
                    if l_RTD2 == l_RTD2_max:
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
                    if l_RTD2 == l_RTD2_max:
                        l_RTD2 = 0
                        k_RTD2 = k_RTD2 + 1
                if (i, j) == (i_RTD2_last, j_RTD2_last):
                    break
            if (i, j) == (i_RTD2_last, j_RTD2_last):
                break

        for i in range(0, i_RTD3_max):
            for j in range(0, j_RTD3_max):
                if TempRefRTD3dir[i][j].Alarm:
                    TempRTD3dir[k_RTD3][l_RTD3] = TempRefRTD3dir[i][j]
                    l_RTD3 = l_RTD3 + 1
                    if l_RTD3 == l_RTD3_max:
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
                    if l_RTD3 == l_RTD3_max:
                        l_RTD3 = 0
                        k_RTD3 = k_RTD3 + 1
                if (i, j) == (i_RTD3_last, j_RTD3_last):
                    break
            if (i, j) == (i_RTD3_last, j_RTD3_last):
                break

        for i in range(0, i_RTD4_max):
            for j in range(0, j_RTD4_max):
                if TempRefRTD4dir[i][j].Alarm:
                    TempRTD4dir[k_RTD4][l_RTD4] = TempRefRTD4dir[i][j]
                    l_RTD4 = l_RTD4 + 1
                    if l_RTD4 == l_RTD4_max:
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
                    if l_RTD4 == l_RTD4_max:
                        l_RTD4 = 0
                        k_RTD4 = k_RTD4 + 1
                if (i, j) == (i_RTD4_last, j_RTD4_last):
                    break
            if (i, j) == (i_RTD4_last, j_RTD4_last):
                break

        for i in range(0, i_RTDLEFT_max):
            for j in range(0, j_RTDLEFT_max):
                if TempRefRTDLEFTdir[i][j].Alarm:
                    TempRTDLEFTdir[k_RTDLEFT][l_RTDLEFT] = TempRefRTDLEFTdir[i][j]
                    l_RTDLEFT = l_RTDLEFT + 1
                    if l_RTDLEFT == l_RTDLEFT_max:
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
                    if l_RTDLEFT == l_RTDLEFT_max:
                        l_RTDLEFT = 0
                        k_RTDLEFT = k_RTDLEFT + 1
                if (i, j) == (i_RTDLEFT_last, j_RTDLEFT_last):
                    break
            if (i, j) == (i_RTDLEFT_last, j_RTDLEFT_last):
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
        for i in range(0, i_RTD1_max):
            for j in range(0, j_RTD1_max):
                self.GLRTD1.addWidget(TempRTD1dir[i][j], i, j)
                if (i, j) == (i_RTD1_last, j_RTD1_last):
                    break
            if (i, j) == (i_RTD1_last, j_RTD1_last):
                break

        for i in range(0, i_RTD2_max):
            for j in range(0, j_RTD2_max):
                self.GLRTD2.addWidget(TempRTD2dir[i][j], i, j)
                if (i, j) == (i_RTD2_last, j_RTD2_last):
                    break
            if (i, j) == (i_RTD2_last, j_RTD2_last):
                break

        for i in range(0, i_RTD3_max):
            for j in range(0, j_RTD3_max):
                self.GLRTD3.addWidget(TempRTD3dir[i][j], i, j)
                if (i, j) == (i_RTD3_last, j_RTD3_last):
                    break
            if (i, j) == (i_RTD3_last, j_RTD3_last):
                break

        for i in range(0, i_RTD4_max):
            for j in range(0, j_RTD4_max):
                self.GLRTD4.addWidget(TempRTD4dir[i][j], i, j)
                if (i, j) == (i_RTD4_last, j_RTD4_last):
                    break
            if (i, j) == (i_RTD4_last, j_RTD4_last):
                break

        for i in range(0, i_RTDLEFT_max):
            for j in range(0, j_RTDLEFT_max):
                self.GLRTDLEFT.addWidget(TempRTDLEFTdir[i][j], i, j)
                if (i, j) == (i_RTDLEFT_last, j_RTDLEFT_last):
                    break
            if (i, j) == (i_RTDLEFT_last, j_RTDLEFT_last):
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
    def __init__(self, Window, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("AlarmButton")
        self.setGeometry(QtCore.QRect(5, 5, 250, 80))
        self.setMinimumSize(250, 80)
        self.setSizePolicy(sizePolicy)

        # link the button to a new window
        self.SubWindow = Window

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
        self.Collected = False

    @QtCore.Slot()
    def ButtonClicked(self):
        self.SubWindow.show()
        # self.Signals.sSignal.emit(self.Button.text())

    @QtCore.Slot()
    def ButtonAlarmSignal(self):
        self.Button.setProperty("Alarm", self.Button.Alarm)
        print(type(self.Button.Alarm))
        print(self.Button.Alarm)
        self.Button.setStyle(self.Button.style())

    @QtCore.Slot()
    def CollectAlarm(self, list):
        for i in range(len(list)):
            # calculate collected alarm status
            self.Collected = self.Collected or list[i].Alarm
        self.Button.Alarm = self.Collected


# Define a function tab that shows the status of the widgets
class FunctionButton(QtWidgets.QWidget):
    def __init__(self, Window, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("FunctionButton")
        self.setGeometry(QtCore.QRect(5, 5, 250, 80))
        self.setMinimumSize(250, 80)
        self.setSizePolicy(sizePolicy)

        # link the button to a new window
        self.SubWindow = Window

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setText("Button")
        self.Button.setGeometry(QtCore.QRect(5, 5, 250, 80))
        self.Button.clicked.connect(self.ButtonClicked)

    @QtCore.Slot()
    def ButtonClicked(self):
        self.SubWindow.show()
        # self.Signals.sSignal.emit(self.Button.text())


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
                    self.db.insert_data_into_datastorage("TT9998", self.dt, self.MW.T.RTD[6])
                    self.db.insert_data_into_datastorage("TT9999", self.dt, self.MW.T.RTD[7])
                    self.MW.T.NewData_Database = False

                if self.MW.P.NewData_Database:
                    print("Writing PPLC data to database...")
                    self.db.insert_data_into_datastorage("PT4325", self.dt, self.MW.P.PT[4])
                    self.MW.P.NewData_Database = False
            else:
                print("Database Updating stopps.")
                pass

            time.sleep(60)

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

        self.RTD1_array = TwoD_into_OneD(self.MW.AlarmButton.SubWindow.AlarmRTD1dir)
        self.RTD2_array = TwoD_into_OneD(self.MW.AlarmButton.SubWindow.AlarmRTD2dir)
        self.RTD3_array = TwoD_into_OneD(self.MW.AlarmButton.SubWindow.AlarmRTD3dir)
        self.RTD4_array = TwoD_into_OneD(self.MW.AlarmButton.SubWindow.AlarmRTD4dir)
        self.RTDLEFT_array = TwoD_into_OneD(self.MW.AlarmButton.SubWindow.AlarmRTDLEFTdir)
        self.PT_array = TwoD_into_OneD(self.MW.AlarmButton.SubWindow.AlarmPTdir)
        self.array = self.RTD1_array + self.RTD2_array + self.RTD3_array + self.RTD4_array + self.RTDLEFT_array + self.PT_array


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
                self.MW.TT9998.SetValue(self.MW.T.RTD[6])
                self.MW.TT9999.SetValue(self.MW.T.RTD[7])
                self.MW.RTDSET1Button.SubWindow.TT2111.SetValue(self.MW.T.RTD[0])
                self.MW.RTDSET1Button.SubWindow.TT2112.SetValue(self.MW.T.RTD[1])
                self.MW.RTDSET1Button.SubWindow.TT2113.SetValue(self.MW.T.RTD[2])
                self.MW.RTDSET1Button.SubWindow.TT2114.SetValue(self.MW.T.RTD[3])
                self.MW.RTDSET1Button.SubWindow.TT2115.SetValue(self.MW.T.RTD[4])
                self.MW.RTDSET1Button.SubWindow.TT2116.SetValue(self.MW.T.RTD[5])
                self.MW.RTDSET1Button.SubWindow.TT2117.SetValue(self.MW.T.RTD[6])

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
            # self.MW.AlarmButton.SubWindow.TT2111.CheckAlarm()
            # self.MW.AlarmButton.SubWindow.PT1101.CheckAlarm()
            # self.MW.AlarmButton.SubWindow.AlarmPTdir[0][0].CheckAlarm()
            # print(self.MW.AlarmButton.SubWindow.AlarmPTdir[0][0]==self.MW.AlarmButton.SubWindow.PT1101)
            for i in range(0,self.MW.AlarmButton.SubWindow.i_RTD1_max):
                for j in range(0,self.MW.AlarmButton.SubWindow.j_RTD1_max):
                    self.MW.AlarmButton.SubWindow.AlarmRTD1dir[i][j].CheckAlarm()
                    if (i,j) ==(self.MW.AlarmButton.SubWindow.i_RTD1_last,self.MW.AlarmButton.SubWindow.j_RTD1_last):
                        break
                if (i, j) == (self.MW.AlarmButton.SubWindow.i_RTD1_last, self.MW.AlarmButton.SubWindow.j_RTD1_last):
                    break

            for i in range(0,self.MW.AlarmButton.SubWindow.i_RTD2_max):
                for j in range(0,self.MW.AlarmButton.SubWindow.j_RTD2_max):
                    self.MW.AlarmButton.SubWindow.AlarmRTD2dir[i][j].CheckAlarm()
                    if (i,j) ==(self.MW.AlarmButton.SubWindow.i_RTD2_last,self.MW.AlarmButton.SubWindow.j_RTD2_last):
                        break
                if (i, j) == (self.MW.AlarmButton.SubWindow.i_RTD2_last, self.MW.AlarmButton.SubWindow.j_RTD2_last):
                    break

            for i in range(0,self.MW.AlarmButton.SubWindow.i_RTD3_max):
                for j in range(0,self.MW.AlarmButton.SubWindow.j_RTD3_max):
                    self.MW.AlarmButton.SubWindow.AlarmRTD3dir[i][j].CheckAlarm()
                    if (i,j) ==(self.MW.AlarmButton.SubWindow.i_RTD3_last,self.MW.AlarmButton.SubWindow.j_RTD3_last):
                        break
                if (i, j) == (self.MW.AlarmButton.SubWindow.i_RTD3_last, self.MW.AlarmButton.SubWindow.j_RTD3_last):
                    break

            for i in range(0,self.MW.AlarmButton.SubWindow.i_RTD4_max):
                for j in range(0,self.MW.AlarmButton.SubWindow.j_RTD4_max):
                    self.MW.AlarmButton.SubWindow.AlarmRTD4dir[i][j].CheckAlarm()
                    if (i,j) ==(self.MW.AlarmButton.SubWindow.i_RTD4_last,self.MW.AlarmButton.SubWindow.j_RTD4_last):
                        break
                if (i, j) == (self.MW.AlarmButton.SubWindow.i_RTD4_last, self.MW.AlarmButton.SubWindow.j_RTD4_last):
                    break

            for i in range(0,self.MW.AlarmButton.SubWindow.i_PT_max):
                for j in range(0,self.MW.AlarmButton.SubWindow.j_PT_max):
                    self.MW.AlarmButton.SubWindow.AlarmPTdir[i][j].CheckAlarm()
                    if (i, j) == (self.MW.AlarmButton.SubWindow.i_PT_last, self.MW.AlarmButton.SubWindow.j_PT_last):
                        break
                if (i, j) == (self.MW.AlarmButton.SubWindow.i_PT_last, self.MW.AlarmButton.SubWindow.j_PT_last):
                    break

            # # # rewrite collectalarm in updatedisplay

            # self.MW.AlarmButton.CollectAlarm(self.array)

            self.MW.AlarmButton.CollectAlarm([self.MW.AlarmButton.SubWindow.TT2111,self.MW.AlarmButton.SubWindow.TT2401])

            # self.MW.AlarmButton.CollectAlarm([self.MW.AlarmButton.SubWindow.TT2111,
            #                                  self.MW.AlarmButton.SubWindow.TT2401,
            #                                  self.MW.AlarmButton.SubWindow.TT2406,
            #                                  self.MW.AlarmButton.SubWindow.TT2411,
            #                                  self.MW.AlarmButton.SubWindow.TT2416,
            #                                  self.MW.AlarmButton.SubWindow.TT2421,
            #                                  self.MW.AlarmButton.SubWindow.TT2426,
            #                                  self.MW.AlarmButton.SubWindow.TT2431,
            #                                  self.MW.AlarmButton.SubWindow.TT2435,
            #                                  self.MW.AlarmButton.SubWindow.TT2440,
            #                                  self.MW.AlarmButton.SubWindow.PT1101,
            #                                  self.MW.AlarmButton.SubWindow.PT2316,
            #                                  self.MW.AlarmButton.SubWindow.PT2321,
            #                                  self.MW.AlarmButton.SubWindow.PT2330,
            #                                  self.MW.AlarmButton.SubWindow.PT2335,
            #                                  self.MW.AlarmButton.SubWindow.PT3308,
            #                                  self.MW.AlarmButton.SubWindow.PT3309,
            #                                  self.MW.AlarmButton.SubWindow.PT3310,
            #                                  self.MW.AlarmButton.SubWindow.PT3311,
            #                                  self.MW.AlarmButton.SubWindow.PT3314,
            #                                  self.MW.AlarmButton.SubWindow.PT3320,
            #                                  self.MW.AlarmButton.SubWindow.PT3333,
            #                                  self.MW.AlarmButton.SubWindow.PT4306,
            #                                  self.MW.AlarmButton.SubWindow.PT4315,
            #                                  self.MW.AlarmButton.SubWindow.PT4319,
            #                                  self.MW.AlarmButton.SubWindow.PT4322,
            #                                  self.MW.AlarmButton.SubWindow.PT4325])

            self.MW.AlarmButton.ButtonAlarmSignal()
            # # # generally checkbutton.clicked -> move to updatedisplay
            if self.MW.AlarmButton.Button.Alarm:
                self.MW.AlarmButton.SubWindow.ReassignOrder()

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
