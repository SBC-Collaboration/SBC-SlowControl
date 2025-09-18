"""
This is the main SlowDAQ code used to read/setproperties of the TPLC and PPLC

By: Mathieu Laurin

v0.1.0 Initial code 29/11/19 ML
v0.1.1 Read and write implemented 08/12/19 ML
v0.1.2 Alarm implemented 07/01/20 ML
v0.1.3 PLC online detection, poll PLCs only when values are updated, fix Centos window size bug 04/03/20 ML
"""

import os, sys, time, platform, datetime, random, pickle, cgitb, traceback, signal,copy, json, socket, threading, struct


from PySide2 import QtWidgets, QtCore, QtGui

# from SlowDAQ_SBC_v2 import *

from SBC_GUI_Widgets import *
import zmq
import SBC_env as env

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


# Settings adapted to sbc slowcontrol machine
SMALL_LABEL_STYLE = "background-color: rgb(204,204,204); border-radius: 3px; font-family: \"Calibri\";" \
                    " font-size: 10px;" \
                    " font-weight: bold;"
LABEL_STYLE = "background-color: rgb(204,204,204); border-radius: 3px; font-family: \"Calibri\"; " \
              "font-size: 12px; font-weight: bold;"
TITLE_STYLE = "background-color: rgb(204,204,204); border-radius: 3px; font-family: \"Calibri\";" \
              " font-size: 14px; font-weight: bold;"

BORDER_STYLE = " border-radius: 2px; border-color: black;"





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



def sendKillSignal(etype, value, tb):
    print('KILL ALL')
    traceback.print_exception(etype, value, tb)
    os.kill(os.getpid(), signal.SIGKILL)


original_init = QtCore.QThread.__init__
def patched_init(self, *args, **kwargs):
    print("thread init'ed")
    original_init(self, *args, **kwargs)
    original_run = self.run
    def patched_run(*args, **kwargs):
        try:
            original_run(*args, **kwargs)
        except:
            sys.excepthook(*sys.exc_info())
    self.run = patched_run
QtCore.QThread.__init__ = patched_init

def install():
    sys._excepthook = sys.excepthook
    sys.excepthook = sendKillSignal
    QtCore.QThread.__init__ = patched_init
    

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
        self.GUI_design()
        self.Alarm_system()

        App.aboutToQuit.connect(self.StopUpdater)
        # Start display updater; comment out to show GUI only
        print("start updater...")
        self.StartUpdater()
        self.signal_connection()

    def GUI_design(self):
        # Get background image path
        if '__file__' in globals():
            self.Path = os.path.dirname(os.path.realpath(__file__))
        else:
            self.Path = os.getcwd()
        self.ImagePath = os.path.join(self.Path, "images")

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.resize(2400*R, 1450*R)  # Open at center using resized
        self.setMinimumSize(2400*R, 1450*R)
        self.setWindowTitle("SlowDAQ " + VERSION)
        self.setWindowIcon(QtGui.QIcon(os.path.join(self.ImagePath, "Logo white_resized.png")))

        # Tabs, backgrounds & labels

        self.Tab = QtWidgets.QTabWidget(self)
        self.Tab.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.Tab.setStyleSheet("font-weight: bold; font-size: 20px; font-family: Calibri;")
        self.Tab.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.Tab.setGeometry(QtCore.QRect(0*R, 0*R, 2400*R, 1450*R))

        self.ThermosyphonTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.ThermosyphonTab, "Thermosyphon Main Panel")

        self.ThermosyphonTab.Background = QtWidgets.QLabel(self.ThermosyphonTab)
        self.ThermosyphonTab.Background.setScaledContents(True)
        self.ThermosyphonTab.Background.setStyleSheet('background-color:black;')
        pixmap_thermalsyphon = QtGui.QPixmap(os.path.join(self.ImagePath, "Thermosyphon_v3.png"))
        pixmap_thermalsyphon = pixmap_thermalsyphon.scaledToWidth(2400*R)
        self.ThermosyphonTab.Background.setPixmap(QtGui.QPixmap(pixmap_thermalsyphon))
        self.ThermosyphonTab.Background.move(0*R, 0*R)
        self.ThermosyphonTab.Background.setAlignment(QtCore.Qt.AlignCenter)

        self.ChamberTab = QtWidgets.QWidget()
        self.Tab.addTab(self.ChamberTab, "Inner Chamber Components")

        self.ChamberTab.Background = QtWidgets.QLabel(self.ChamberTab)
        self.ChamberTab.Background.setScaledContents(True)
        self.ChamberTab.Background.setStyleSheet('background-color:black;')
        pixmap_chamber = QtGui.QPixmap(os.path.join(self.ImagePath, "PV_v2.png"))
        self.ChamberTab.Background.setPixmap(pixmap_chamber)
        self.ChamberTab.Background.resize(2400 * R, 1390 * R)
        self.ChamberTab.Background.move(0*R, 0*R)
        self.ChamberTab.Background.setObjectName("ChamberBkg")

        self.IVTab = QtWidgets.QWidget()
        self.Tab.addTab(self.IVTab, "IV 2D layout")

        self.IVTab.Background = QtWidgets.QLabel(self.IVTab)
        self.IVTab.Background.setScaledContents(True)
        self.IVTab.Background.setStyleSheet('background-color:black;')
        pixmap_IV = QtGui.QPixmap(os.path.join(self.ImagePath, "IV_2d.png"))
        self.IVTab.Background.setPixmap(pixmap_IV)
        self.IVTab.Background.resize(2400 * R, 1390 * R)
        self.IVTab.Background.move(0 * R, 0 * R)
        self.IVTab.Background.setObjectName("IVBkg")

        self.FluidTab = QtWidgets.QWidget()
        self.Tab.addTab(self.FluidTab, "Fluid System")

        self.FluidTab.Background = QtWidgets.QLabel(self.FluidTab)
        self.FluidTab.Background.setScaledContents(True)
        self.FluidTab.Background.setStyleSheet('background-color:black;')
        pixmap_Fluid = QtGui.QPixmap(os.path.join(self.ImagePath, "CF4_XeAr_Panel_cryogenic_v2.png"))
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
        pixmap_Hydraulic = QtGui.QPixmap(os.path.join(self.ImagePath, "Hydraulic_apparatus_v2.png"))
        pixmap_Hydraulic = pixmap_Hydraulic.scaledToWidth(2400*R)
        self.HydraulicTab.Background.setPixmap(QtGui.QPixmap(pixmap_Hydraulic))
        self.HydraulicTab.Background.move(0*R, 0*R)
        self.HydraulicTab.Background.setAlignment(QtCore.Qt.AlignCenter)
        self.HydraulicTab.Background.setObjectName("HydraulicBkg")

        self.RackTab = QtWidgets.QWidget()
        self.Tab.addTab(self.RackTab, "Rack Electronics")

        self.RackTab.Background = QtWidgets.QLabel(self.RackTab)
        self.RackTab.Background.setScaledContents(True)
        self.RackTab.Background.setStyleSheet('background-color:black;')
        pixmap_Rack = QtGui.QPixmap(os.path.join(self.ImagePath, "Default_Background.png"))
        pixmap_Rack = pixmap_Rack.scaledToWidth(2400 * R)
        self.RackTab.Background.setPixmap(QtGui.QPixmap(pixmap_Rack))
        self.RackTab.Background.move(0 * R, 0 * R)
        self.RackTab.Background.setAlignment(QtCore.Qt.AlignCenter)
        self.RackTab.Background.setObjectName("RackBkg")


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
        self.PT4306.SetUnit(" bar")

        self.PV4307 = Valve_v2(self.ThermosyphonTab)
        self.PV4307.Label.setText("PV4307")
        self.PV4307.move(1020*R, 202*R)

        self.PV4307_icon = Valve_image(self.ThermosyphonTab, mode="V")
        self.PV4307_icon.move(1188 * R, 202 * R)

        self.PV4308 = Valve_v2(self.ThermosyphonTab)
        self.PV4308.Label.setText("PV4308")
        self.PV4308.move(850*R, 320*R)

        self.PV4308_icon = Valve_image(self.ThermosyphonTab, mode="H")
        self.PV4308_icon.move(937 * R, 280 * R)
        self.PV4308_icon.stackUnder(self.PV4308)


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
        self.PT4315.SetUnit(" bar")

        self.PG4316 = PnID_Alone(self.ThermosyphonTab)
        self.PG4316.Label.setText("PG4316")
        self.PG4316.move(820*R, 470*R)

        self.PV4317 = Valve_v2(self.ThermosyphonTab)
        self.PV4317.Label.setText("PV4317")
        self.PV4317.move(520*R, 380*R)


        self.PV4317_icon = Valve_image(self.ThermosyphonTab, mode="V")
        self.PV4317_icon.move(495 * R, 380 * R)

        self.PV4318 = Valve_v2(self.ThermosyphonTab)
        self.PV4318.Label.setText("PV4318")
        self.PV4318.move(319*R, 600*R)

        self.PV4318_icon = Valve_image(self.ThermosyphonTab, mode="V")
        self.PV4318_icon.move(492 * R, 600 * R)

        self.PT4319 = Indicator(self.ThermosyphonTab)
        self.PT4319.Label.setText("PT4319")
        self.PT4319.move(570*R, 760*R)
        self.PT4319.SetUnit(" bar")

        self.PRV4320 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4320.Label.setText("PRV4320")
        self.PRV4320.move(570*R, 860*R)

        self.PV4321 = Valve_v2(self.ThermosyphonTab)
        self.PV4321.Label.setText("PV4321")
        self.PV4321.move(590*R, 600*R)

        self.PV4321_icon = Valve_image(self.ThermosyphonTab, mode="V")
        self.PV4321_icon.move(760 * R, 600 * R)

        self.PT4322 = Indicator(self.ThermosyphonTab)
        self.PT4322.Label.setText("PT4322")
        self.PT4322.move(850*R, 760*R)
        self.PT4322.SetUnit(" bar")

        self.PRV4323 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4323.Label.setText("PRV4323")
        self.PRV4323.move(850*R, 860*R)

        self.PV4324 = Valve_v2(self.ThermosyphonTab)
        self.PV4324.Label.setText("PV4324")
        self.PV4324.move(1100*R, 600*R)

        self.PV4324_icon = Valve_image(self.ThermosyphonTab, mode="V")
        self.PV4324_icon.move(1070 * R, 600 * R)

        self.PT4325 = Indicator(self.ThermosyphonTab)
        self.PT4325.Label.setText("PT4325")
        self.PT4325.move(1150*R, 760*R)
        self.PT4325.SetUnit(" bar")

        self.PRV4326 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4326.Label.setText("PRV4326")
        self.PRV4326.move(1150*R, 860*R)

        self.SV4327 = Valve_v2(self.ThermosyphonTab)
        self.SV4327.Label.setText("SV4327")
        self.SV4327.move(280 * R, 400 * R)

        self.SV4327_icon = Valve_image(self.ThermosyphonTab, mode="V")
        self.SV4327_icon.move(335 * R, 330 * R)

        self.SV4328 = Valve_v2(self.ThermosyphonTab)
        self.SV4328.Label.setText("SV4328")
        self.SV4328.move(1360*R, 190*R)

        self.SV4328_icon = Valve_image(self.ThermosyphonTab, mode="H")
        self.SV4328_icon.move(1410 * R, 145 * R)

        self.SV4329 = Valve_v2(self.ThermosyphonTab)
        self.SV4329.Label.setText("SV4329")
        self.SV4329.move(1865*R, 195*R)

        self.SV4329_icon = Valve_image(self.ThermosyphonTab, mode="H")
        self.SV4329_icon.move(1866 * R, 145 * R)

        self.TT4330 = Indicator(self.ThermosyphonTab)
        self.TT4330.Label.setText("TT4330")
        self.TT4330.move(1915*R, 55*R)

        self.SV4331 = Valve_v2(self.ThermosyphonTab)
        self.SV4331.Label.setText("SV4331")
        self.SV4331.move(1522*R, 290*R)

        self.SV4331_icon = Valve_image(self.ThermosyphonTab, mode="H")
        self.SV4331_icon.move(1564 * R, 232 * R)

        self.SV4332 = Valve_v2(self.ThermosyphonTab)
        self.SV4332.Label.setText("SV4332")
        self.SV4332.move(1680*R, 380*R)

        self.SV4332_icon = Valve_image(self.ThermosyphonTab, mode="H")
        self.SV4332_icon.move(1673 * R, 322 * R)

        self.SV4337 = Valve_v2(self.ThermosyphonTab)
        self.SV4337.Label.setText("SV4337")
        self.SV4337.move(115 * R, 320 * R)

        self.SV4337_icon = Valve_image(self.ThermosyphonTab, mode="H")
        self.SV4337_icon.move(170 * R, 280 * R)


        self.PRV4333 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4333.Label.setText("PRV4333")
        self.PRV4333.move(900*R, 650*R)

        self.PT6302 = Indicator(self.ThermosyphonTab)
        self.PT6302.Label.setText("PT6302")
        self.PT6302.move(2030*R, 690*R)
        self.PT6302.SetUnit(" tr")

        self.PRV6303 = PnID_Alone(self.ThermosyphonTab)
        self.PRV6303.Label.setText("PRV6303")
        self.PRV6303.move(1700*R, 700*R)

        self.MV6304 = PnID_Alone(self.ThermosyphonTab)
        self.MV6304.Label.setText("MV6304")
        self.MV6304.move(1810*R, 650*R)

        self.HE6201 = PnID_Alone(self.ThermosyphonTab)
        self.HE6201.Label.setText("HE6201")
        self.HE6201.move(1410*R, 1100*R)

        self.PT6306 = Indicator(self.ThermosyphonTab)
        self.PT6306.Label.setText("PT6306")
        self.PT6306.move(1410*R, 1200*R)
        self.PT6306.SetUnit(" tr")

        self.EV6204 = PnID_Alone(self.ThermosyphonTab)
        self.EV6204.Label.setText("EV6204")
        self.EV6204.move(930*R, 1100*R)

        self.PLCOnline = State(self.ThermosyphonTab)
        self.PLCOnline.move(200*R, 1200*R)
        self.PLCOnline.Label.setText("PLC link")
        self.PLCOnline.Field.setText("Offline")
        self.PLCOnline.SetAlarm()

        self.CC9313_CONT = Valve_v2(self.ThermosyphonTab)
        self.CC9313_CONT.Label.setText("CC9313_CONT")
        self.CC9313_CONT.move(1150 * R, 50 * R)

        self.CC9313_POWER = ColoredStatus(self.ThermosyphonTab, mode=2)
        self.CC9313_POWER.move(1350 * R, 50 * R)
        self.CC9313_POWER.Label.setText("CC9313_POW")



        self.PV4345 = Valve_v2(self.ThermosyphonTab)
        self.PV4345.Label.setText("PV4345")
        self.PV4345.move(2100 * R, 300 * R)




        # Chamber tab buttons



        self.PT1101 = Indicator_v2(self.ChamberTab, colorcode=0, bkg_c=1)
        self.PT1101.move(1500 * R, 990 * R)
        self.PT1101.Label.setText("PT1101")
        self.PT1101.SetUnit(" bar")

        self.PT2121 = Indicator_v2(self.ChamberTab, colorcode=0, bkg_c=1)
        self.PT2121.move(2110 * R, 990 * R)
        self.PT2121.Label.setText("PT2121")
        self.PT2121.SetUnit(" bar")

        self.LED1_OUT = Indicator_v2(self.ChamberTab, colorcode=0, bkg_c=1)
        self.LED1_OUT.move(763 * R, 426 * R)
        self.LED1_OUT.Label.setText("LED1_OUT")
        self.LED1_OUT.SetUnit("")

        self.LED2_OUT = Indicator_v2(self.ChamberTab, colorcode=0, bkg_c=1)
        self.LED2_OUT.move(463 * R, 426 * R)
        self.LED2_OUT.Label.setText("LED2_OUT")
        self.LED2_OUT.SetUnit("")

        self.LED3_OUT = Indicator_v2(self.ChamberTab, colorcode=0, bkg_c=1)
        self.LED3_OUT.move(363 * R, 426 * R)
        self.LED3_OUT.Label.setText("LED3_OUT")
        self.LED3_OUT.SetUnit("")

        self.LED_MAX = Indicator_v2(self.ChamberTab, colorcode=0, bkg_c=1)
        self.LED_MAX.move(263 * R, 426 * R)
        self.LED_MAX.Label.setText("LED_MAX")
        self.LED_MAX.SetUnit("")

        self.TT2118 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2118.move(483* R, 970 * R)
        self.TT2118.Label.setText("TT2118")
        self.TT2118.SetUnit(" K")

        self.TT2119 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1,dotted= True)
        self.TT2119.move(268 * R, 780 * R)
        self.TT2119.Label.setText("TT2119")
        self.TT2119.SetUnit(" K")

        self.TT2401 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2401.move(2047 * R, 850 * R)
        self.TT2401.Label.setText("TT2401")
        self.TT2401.SetUnit(" K")

        self.TT2402 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=2)
        self.TT2402.move(1830 * R, 1300 * R)
        self.TT2402.Label.setText("TT2402")
        self.TT2402.SetUnit(" K")

        self.TT2403 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2403.move(1832 * R, 516 * R)
        self.TT2403.Label.setText("TT2403")
        self.TT2403.SetUnit(" K")

        self.TT2404 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2404.move(495 * R, 1295 * R)
        self.TT2404.Label.setText("TT2404")
        self.TT2404.SetUnit(" K")

        self.TT2405 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1, dotted = True)
        self.TT2405.move(1552 * R, 850 * R)
        self.TT2405.Label.setText("TT2405")
        self.TT2405.SetUnit(" K")

        self.TT2406 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2406.move(1580 * R, 636 * R)
        self.TT2406.Label.setText("TT2406")
        self.TT2406.SetUnit(" K")

        self.TT2407 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2407.move(1776 * R, 636 * R)
        self.TT2407.Label.setText("TT2407")
        self.TT2407.SetUnit(" K")

        self.TT2408 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2408.move(1966 * R, 636 * R)
        self.TT2408.Label.setText("TT2408")
        self.TT2408.SetUnit(" K")

        self.TT2409 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2409.move(1863 * R, 850 * R)
        self.TT2409.Label.setText("TT2409")
        self.TT2409.SetUnit(" K")

        self.TT2410 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2410.move(1647 * R, 850 * R)
        self.TT2410.Label.setText("TT2410")
        self.TT2410.SetUnit(" K")

        self.TT2411 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2411.move(1958 * R, 850 * R)
        self.TT2411.Label.setText("TT2411")
        self.TT2411.SetUnit(" K")

        self.TT2412 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2412.move(780 * R, 1200 * R)
        self.TT2412.Label.setText("TT2412")
        self.TT2412.SetUnit(" K")

        self.TT2413 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2413.move(800 * R, 1300 * R)
        self.TT2413.Label.setText("TT2413")
        self.TT2413.SetUnit(" K")

        self.TT2414 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2414.move(1940 * R, 452 * R)
        self.TT2414.Label.setText("TT2414")
        self.TT2414.SetUnit(" K")

        self.TT2415 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2415.move(690 * R, 1200 * R)
        self.TT2415.Label.setText("TT2415")
        self.TT2415.SetUnit(" K")

        self.TT2416 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1,dotted= True)
        self.TT2416.move(400 * R, 1295 * R)
        self.TT2416.Label.setText("TT2416")
        self.TT2416.SetUnit(" K")

        self.TT2417 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2417.move(615 * R, 1092 * R)
        self.TT2417.Label.setText("TT2417")
        self.TT2417.SetUnit(" K")

        self.TT2418 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2418.move(570 * R, 1003 * R)
        self.TT2418.Label.setText("TT2418")
        self.TT2418.SetUnit(" K")

        self.TT2419 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1,dotted= True)
        self.TT2419.move(930 * R, 987 * R)
        self.TT2419.Label.setText("TT2419")
        self.TT2419.SetUnit(" K")

        self.TT2420 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2420.move(483 * R, 894 * R)
        self.TT2420.Label.setText("TT2420")
        self.TT2420.SetUnit(" K")

        self.TT2421 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1,dotted= True)
        self.TT2421.move(268 * R, 920 * R)
        self.TT2421.Label.setText("TT2421")
        self.TT2421.SetUnit(" K")

        self.TT2422 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2422.move(483 * R, 820 * R)
        self.TT2422.Label.setText("TT2422")
        self.TT2422.SetUnit(" K")

        self.TT2423 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1,dotted= True)
        self.TT2423.move(930 * R, 784 * R)
        self.TT2423.Label.setText("TT2423")
        self.TT2423.SetUnit(" K")

        self.TT2424 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2424.move(483 * R, 742 * R)
        self.TT2424.Label.setText("TT2424")
        self.TT2424.SetUnit(" K")

        self.TT2425 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2425.move(483 * R, 670 * R)
        self.TT2425.Label.setText("TT2425")
        self.TT2425.SetUnit(" K")

        self.TT2426 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=2,dotted= True)
        self.TT2426.move(930 * R, 667 * R)
        self.TT2426.Label.setText("TT2426")
        self.TT2426.SetUnit(" K")

        self.TT2427 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=2)
        self.TT2427.move(612 * R, 934 * R)
        self.TT2427.Label.setText("TT2427")
        self.TT2427.SetUnit(" K")

        self.TT2428 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=2,dotted= True)
        self.TT2428.move(268 * R, 975 * R)
        self.TT2428.Label.setText("TT2428")
        self.TT2428.SetUnit(" K")

        self.TT2429 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=2)
        self.TT2429.move(612 * R, 844 * R)
        self.TT2429.Label.setText("TT2429")
        self.TT2429.SetUnit(" K")

        self.TT2430 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=2,dotted= True)
        self.TT2430.move(930 * R, 858 * R)
        self.TT2430.Label.setText("TT2430")
        self.TT2430.SetUnit(" K")

        self.TT2431 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=2)
        self.TT2431.move(612 * R, 770 * R)
        self.TT2431.Label.setText("TT2431")
        self.TT2431.SetUnit(" K")

        self.TT2432 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=2,dotted= True)
        self.TT2432.move(268 * R, 717 * R)
        self.TT2432.Label.setText("TT2432")
        self.TT2432.SetUnit(" K")


        self.TT2435 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=2, dotted = True)
        self.TT2435.move(835 * R, 1020 * R)
        self.TT2435.Label.setText("TT2435")
        self.TT2435.SetUnit(" K")

        self.TT2436 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1)
        self.TT2436.move(875 * R, 1144 * R)
        self.TT2436.Label.setText("TT2436")
        self.TT2436.SetUnit(" K")

        self.TT2437 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1,dotted= True)
        self.TT2437.move(705 * R, 1092 * R)
        self.TT2437.Label.setText("TT2437")
        self.TT2437.SetUnit(" K")

        self.TT2438 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1)
        self.TT2438.move(875 * R, 920 * R)
        self.TT2438.Label.setText("TT2438")
        self.TT2438.SetUnit(" K")

        self.TT2439 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1,dotted= True)
        self.TT2439.move(145 * R, 966 * R)
        self.TT2439.Label.setText("TT2439")
        self.TT2439.SetUnit(" K")

        self.TT2440 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1)
        self.TT2440.move(875 * R, 730 * R)
        self.TT2440.Label.setText("TT2440")
        self.TT2440.SetUnit(" K")

        self.TT2441 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1)
        self.TT2441.move(145 * R, 770 * R)
        self.TT2441.Label.setText("TT2441")
        self.TT2441.SetUnit(" K")

        self.TT2442 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1)
        self.TT2442.move(360 * R, 646* R)
        self.TT2442.Label.setText("TT2442")
        self.TT2442.SetUnit(" K")

        self.TT2443 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1)
        self.TT2443.move(658 * R, 646 * R)
        self.TT2443.Label.setText("TT2443")
        self.TT2443.SetUnit(" K")

        self.TT2444 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1,dotted= True)
        self.TT2444.move(753* R, 646 * R)
        self.TT2444.Label.setText("TT2444")
        self.TT2444.SetUnit(" K")

        self.TT2445 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1,dotted= True)
        self.TT2445.move(468 * R, 566 * R)
        self.TT2445.Label.setText("TT2445")
        self.TT2445.SetUnit(" K")

        self.TT2446 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1,dotted= True)
        self.TT2446.move(752 * R, 564 * R)
        self.TT2446.Label.setText("TT2446")
        self.TT2446.SetUnit(" K")

        self.TT2447 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2447.move(637 * R, 564 * R)
        self.TT2447.Label.setText("TT2447")
        self.TT2447.SetUnit(" K")

        self.TT2448 = Indicator_v2(self.ChamberTab, colorcode=2, bkg_c=1)
        self.TT2448.move(352 * R, 564 * R)
        self.TT2448.Label.setText("TT2448")
        self.TT2448.SetUnit(" K")

        self.TT2449 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=2)
        self.TT2449.move(563 * R, 426 * R)
        self.TT2449.Label.setText("TT2449")
        self.TT2449.SetUnit(" K")

        self.TT2450 = Indicator_v2(self.ChamberTab, colorcode=1, bkg_c=1,dotted= True)
        self.TT2450.move(600 * R, 1180 * R)
        self.TT2450.Label.setText("TT2450")
        self.TT2450.SetUnit(" K")

        self.HTR6219 = LOOPPID_v3(self.ChamberTab, bkg_c = 1)
        self.HTR6219.move(180*R, 150*R)
        self.HTR6219.Label.setText("HTR6219")
        self.HTR6219.LOOPPIDWindow.setWindowTitle("HTR6219")
        self.HTR6219.LOOPPIDWindow.Label.setText("HTR6219")
        self.HTR6219.LOOPPIDWindow.RTD1.Label.setText("TT6222")
        self.HTR6219.LOOPPIDWindow.RTD2.Label.setText("TT6220")
        self.HTR6219.RTD1.Label.setText("TT6222")

        self.HTR6221 = LOOPPID_v3(self.ChamberTab, bkg_c = 1)
        self.HTR6221.move(684*R, 150*R)
        self.HTR6221.Label.setText("HTR6221")
        self.HTR6221.LOOPPIDWindow.setWindowTitle("HTR6221")
        self.HTR6221.LOOPPIDWindow.Label.setText("HTR6221")
        self.HTR6221.LOOPPIDWindow.RTD1.Label.setText("TT6222")
        self.HTR6221.LOOPPIDWindow.RTD2.Label.setText("EMPTY")
        self.HTR6221.RTD1.Label.setText("TT6222")

        self.HTR6214 = LOOPPID_v3(self.ChamberTab, bkg_c = 1)
        self.HTR6214.move(671*R, 335*R)
        self.HTR6214.Label.setText("HTR6214")
        self.HTR6214.LOOPPIDWindow.setWindowTitle("HTR6214")
        self.HTR6214.LOOPPIDWindow.Label.setText("HTR6214")
        self.HTR6214.LOOPPIDWindow.RTD1.Label.setText("TT6213")
        self.HTR6214.LOOPPIDWindow.RTD2.Label.setText("TT6401")
        self.HTR6214.RTD1.Label.setText("TT6213")

        self.HTR6202 = LOOPPID_v3(self.ChamberTab, bkg_c = 1)
        self.HTR6202.move(1298*R, 180*R)
        self.HTR6202.Label.setText("HTR6202")
        self.HTR6202.LOOPPIDWindow.setWindowTitle("HTR6202")
        self.HTR6202.LOOPPIDWindow.Label.setText("HTR6202")
        self.HTR6202.LOOPPIDWindow.RTD1.Label.setText("TT6203")
        self.HTR6202.LOOPPIDWindow.RTD2.Label.setText("TT6404")
        self.HTR6202.RTD1.Label.setText("TT6203")

        self.HTR6206 = LOOPPID_v3(self.ChamberTab, bkg_c = 1,dotted= True)
        self.HTR6206.move(1665*R, 180*R)
        self.HTR6206.Label.setText("HTR6206")
        self.HTR6206.LOOPPIDWindow.setWindowTitle("HTR6206")
        self.HTR6206.LOOPPIDWindow.Label.setText("HTR6206")
        self.HTR6206.LOOPPIDWindow.RTD1.Label.setText("TT6207")
        self.HTR6206.LOOPPIDWindow.RTD2.Label.setText("TT6405")
        self.HTR6206.RTD1.Label.setText("TT6207")

        self.HTR6210 = LOOPPID_v3(self.ChamberTab, bkg_c = 1)
        self.HTR6210.move(2020*R, 180*R)
        self.HTR6210.Label.setText("HTR6210")
        self.HTR6210.LOOPPIDWindow.setWindowTitle("HTR6210")
        self.HTR6210.LOOPPIDWindow.Label.setText("HTR6210")
        self.HTR6210.LOOPPIDWindow.RTD1.Label.setText("TT6211")
        self.HTR6210.LOOPPIDWindow.RTD2.Label.setText("TT6406")
        self.HTR6210.RTD1.Label.setText("TT6211")

        self.HTR6223 = LOOPPID_v3(self.ChamberTab, bkg_c = 1)
        self.HTR6223.move(1278*R, 350*R)
        self.HTR6223.Label.setText("HTR6223")
        self.HTR6223.LOOPPIDWindow.setWindowTitle("HTR6223")
        self.HTR6223.LOOPPIDWindow.Label.setText("HTR6223")
        self.HTR6223.LOOPPIDWindow.RTD1.Label.setText("TT6407")
        self.HTR6223.LOOPPIDWindow.RTD2.Label.setText("TT6410")
        self.HTR6223.RTD1.Label.setText("TT6407")

        self.HTR6224 = LOOPPID_v3(self.ChamberTab, bkg_c = 1,dotted= True)
        self.HTR6224.move(1645*R, 350*R)
        self.HTR6224.Label.setText("HTR6224")
        self.HTR6224.LOOPPIDWindow.setWindowTitle("HTR6224")
        self.HTR6224.LOOPPIDWindow.Label.setText("HTR6224")
        self.HTR6224.LOOPPIDWindow.RTD1.Label.setText("TT6408")
        self.HTR6224.LOOPPIDWindow.RTD2.Label.setText("TT6411")
        self.HTR6224.RTD1.Label.setText("TT6408")

        self.HTR6225 = LOOPPID_v3(self.ChamberTab, bkg_c = 1)
        self.HTR6225.move(2000*R, 350*R)
        self.HTR6225.Label.setText("HTR6225")
        self.HTR6225.LOOPPIDWindow.setWindowTitle("HTR6225")
        self.HTR6225.LOOPPIDWindow.Label.setText("HTR6225")
        self.HTR6225.LOOPPIDWindow.RTD1.Label.setText("TT6409")
        self.HTR6225.LOOPPIDWindow.RTD2.Label.setText("TT6412")
        self.HTR6225.RTD1.Label.setText("TT6409")

        self.HTR2123 = LOOPPID_v3(self.ChamberTab, colorcode=2,bkg_c = 1)
        self.HTR2123.move(1220*R, 755*R)
        self.HTR2123.Label.setText("HTR2123")
        self.HTR2123.LOOPPIDWindow.setWindowTitle("HTR2123")
        self.HTR2123.LOOPPIDWindow.Label.setText("HTR2123")
        self.HTR2123.LOOPPIDWindow.RTD1.Label.setText("TT2101")
        self.HTR2123.LOOPPIDWindow.RTD2.Label.setText("EMPTY")
        self.HTR2123.RTD1.Label.setText("TT2101")

        self.HTR2124 = LOOPPID_v3(self.ChamberTab, colorcode=2,bkg_c = 1)
        self.HTR2124.move(950*R, 1047*R)
        self.HTR2124.Label.setText("HTR2124")
        self.HTR2124.LOOPPIDWindow.setWindowTitle("HTR2124")
        self.HTR2124.LOOPPIDWindow.Label.setText("HTR2124")
        self.HTR2124.LOOPPIDWindow.RTD1.Label.setText("TT2113")
        self.HTR2124.LOOPPIDWindow.RTD2.Label.setText("TT2113")
        self.HTR2124.RTD1.Label.setText("TT2113")

        self.HTR2125 = LOOPPID_v3(self.ChamberTab, colorcode=2,bkg_c = 1)
        self.HTR2125.move(250*R, 1090*R)
        self.HTR2125.Label.setText("HTR2125")
        self.HTR2125.LOOPPIDWindow.setWindowTitle("HTR2125")
        self.HTR2125.LOOPPIDWindow.Label.setText("HTR2125")
        self.HTR2125.LOOPPIDWindow.RTD1.Label.setText("TT2111")
        self.HTR2125.LOOPPIDWindow.RTD2.Label.setText("TT2111")
        self.HTR2125.RTD1.Label.setText("TT2111")


        self.HTR1202 = LOOPPID_v3(self.ChamberTab, bkg_c = 1)
        self.HTR1202.move(1339*R, 1210*R)
        self.HTR1202.Label.setText("HTR1202")
        self.HTR1202.LOOPPIDWindow.setWindowTitle("HTR1202")
        self.HTR1202.LOOPPIDWindow.Label.setText("HTR1202")
        self.HTR1202.LOOPPIDWindow.RTD1.Label.setText("TT6415")
        self.HTR1202.LOOPPIDWindow.RTD2.Label.setText("TT6413")
        self.HTR1202.RTD1.Label.setText("TT6415")

        self.HTR2203 = LOOPPID_v3(self.ChamberTab, bkg_c = 1)
        self.HTR2203.move(1916*R, 1210*R)
        self.HTR2203.Label.setText("HTR2203")
        self.HTR2203.LOOPPIDWindow.setWindowTitle("HTR2203")
        self.HTR2203.LOOPPIDWindow.Label.setText("HTR2203")
        self.HTR2203.LOOPPIDWindow.RTD1.Label.setText("TT6416")
        self.HTR2203.LOOPPIDWindow.RTD2.Label.setText("TT6414")
        self.HTR2203.RTD1.Label.setText("TT6416")
        # 1st is whether the groups are expanded, 2nd is if visible

        self.PV_group = [False, True, self.HTR6214,self.HTR6219, self.HTR6221, self.HTR2203, self.HTR1202,
                              self.HTR6202, self.HTR6206, self.HTR6210,
                              self.HTR6223,self.HTR6224,self.HTR6225,self.PT1101,self.PT2121, self.LED1_OUT, self.LED2_OUT, self.LED3_OUT,
                         self.LED_MAX]

        self.HDPE_group = [False, True,self.TT2416,self.TT2435,self.TT2436,self.TT2437,self.TT2438,self.TT2439,self.TT2440,self.TT2441,
                           self.TT2442,self.TT2443,self.TT2444,self.TT2445,self.TT2450,self.TT2449]

        self.IV_group = [False, True,  self.HTR2123,self.HTR2124, self.HTR2125,self.TT2118,self.TT2119,
                         self.TT2401, self.TT2402,self.TT2403,self.TT2404,
                         self.TT2405,self.TT2406,self.TT2407,self.TT2408,self.TT2409,self.TT2410,self.TT2411,self.TT2412,
                         self.TT2413,self.TT2414,self.TT2415,self.TT2417,self.TT2418,self.TT2419,self.TT2420,self.TT2421,
                         self.TT2422,self.TT2423,self.TT2424,self.TT2425,self.TT2426,self.TT2427,self.TT2428,self.TT2429,
                         self.TT2430,self.TT2431,self.TT2432,self.TT2446,self.TT2447,
                         self.TT2448]

        self.PV_switch = TextButton(self.ChamberTab, colorcode=0, expanded= self.PV_group[0], visibility=self.PV_group[1])
        self.PV_switch.move(10 * R, 1040 * R)
        self.PV_switch.Button.setText("PV")
        self.PV_switch.Button.clicked.connect(lambda: self.set_background(0))
        self.PV_switch.Button.clicked.connect(lambda: self.set_visibility_true_only(layer="PV"))


        self.HDPE_switch = TextButton(self.ChamberTab, colorcode=1,expanded= self.HDPE_group[0], visibility=self.HDPE_group[1])
        self.HDPE_switch.move(10 * R, 1120 * R)
        self.HDPE_switch.Button.setText("HDPE")
        self.HDPE_switch.Button.clicked.connect(lambda: self.set_background(1))
        self.HDPE_switch.Button.clicked.connect(lambda: self.set_visibility_true_only(layer="HDPE"))


        self.IV_switch = TextButton(self.ChamberTab, colorcode=2,expanded= self.IV_group[0], visibility=self.IV_group[1])
        self.IV_switch.move(10 * R, 1200 * R)
        self.IV_switch.Button.setText("Jars")
        self.IV_switch.Button.clicked.connect(lambda: self.set_background(2))
        self.IV_switch.Button.clicked.connect(lambda: self.set_visibility_true_only(layer="IV"))




        # expansion button
        self.PV_switch.ExpButton.clicked.connect(lambda : self.set_expansion(layer="PV"))
        self.PV_switch.ExpButton.clicked.connect(lambda: self.PV_switch.update_expand(self.PV_group[0]))
        self.HDPE_switch.ExpButton.clicked.connect(lambda: self.set_expansion(layer="HDPE"))
        self.HDPE_switch.ExpButton.clicked.connect(lambda: self.HDPE_switch.update_expand(self.HDPE_group[0]))
        self.IV_switch.ExpButton.clicked.connect(lambda : self.set_expansion(layer="IV"))
        self.IV_switch.ExpButton.clicked.connect(lambda: self.IV_switch.update_expand(self.IV_group[0]))
        #visible button
        self.PV_switch.VisButton.clicked.connect(lambda: self.switch_visibility(layer="PV"))
        self.PV_switch.VisButton.clicked.connect(lambda: self.PV_switch.update_visible(self.PV_group[1]))
        self.HDPE_switch.VisButton.clicked.connect(lambda: self.switch_visibility(layer="HDPE"))
        self.HDPE_switch.VisButton.clicked.connect(lambda: self.HDPE_switch.update_visible(self.HDPE_group[1]))
        self.IV_switch.VisButton.clicked.connect(lambda: self.switch_visibility(layer="IV"))
        self.IV_switch.VisButton.clicked.connect(lambda: self.IV_switch.update_visible(self.IV_group[1]))


        # IV -2d
        self.TT2425_2d = Indicator(self.IVTab)
        self.TT2425_2d.move(875 * R, 250 * R)
        self.TT2425_2d.Label.setText("TT2425")
        self.TT2425_2d.SetUnit(" K")


        self.TT2424_2d = Indicator(self.IVTab)
        self.TT2424_2d.move(875 * R, 320 * R)
        self.TT2424_2d.Label.setText("TT2424")
        self.TT2424_2d.SetUnit(" K")

        self.TT2422_2d = Indicator(self.IVTab)
        self.TT2422_2d.move(875 * R, 390 * R)
        self.TT2422_2d.Label.setText("TT2422")
        self.TT2422_2d.SetUnit(" K")


        self.TT2420_2d = Indicator(self.IVTab)
        self.TT2420_2d.move(875 * R, 460 * R)
        self.TT2420_2d.Label.setText("TT2420")
        self.TT2420_2d.SetUnit(" K")


        self.TT2418_2d = Indicator(self.IVTab)
        self.TT2418_2d.move(875 * R, 530 * R)
        self.TT2418_2d.Label.setText("TT2418")
        self.TT2418_2d.SetUnit(" K")


        self.TT2442_2d = Indicator(self.IVTab)
        self.TT2442_2d.move(757 * R, 719 * R)
        self.TT2442_2d.Label.setText("TT2442")
        self.TT2442_2d.SetUnit(" K")


        self.TT2431_2d = Indicator(self.IVTab)
        self.TT2431_2d.move(1250 * R, 330 * R)
        self.TT2431_2d.Label.setText("TT2431")
        self.TT2431_2d.SetUnit(" K")


        self.TT2429_2d = Indicator(self.IVTab)
        self.TT2429_2d.move(1250 * R, 410 * R)
        self.TT2429_2d.Label.setText("TT2429")
        self.TT2429_2d.SetUnit(" K")

        self.TT2427_2d = Indicator(self.IVTab)
        self.TT2427_2d.move(1250 * R, 490 * R)
        self.TT2427_2d.Label.setText("TT2427")
        self.TT2427_2d.SetUnit(" K")

        self.TT2418_2d = Indicator(self.IVTab)
        self.TT2418_2d.move(1110 * R, 630 * R)
        self.TT2418_2d.Label.setText("TT2418")
        self.TT2418_2d.SetUnit(" K")


        self.TT2441_2d = Indicator(self.IVTab)
        self.TT2441_2d.move(1056 * R, 872 * R)
        self.TT2441_2d.Label.setText("TT2441")
        self.TT2441_2d.SetUnit(" K")


        self.TT2446_2d = Indicator(self.IVTab)
        self.TT2446_2d.move(1900 * R, 125 * R)
        self.TT2446_2d.Label.setText("TT2446")
        self.TT2446_2d.SetUnit(" K")


        self.TT2447_2d = Indicator(self.IVTab)
        self.TT2447_2d.move(1283 * R, 125 * R)
        self.TT2447_2d.Label.setText("TT2447")
        self.TT2447_2d.SetUnit(" K")


        self.TT2448_2d = Indicator(self.IVTab)
        self.TT2448_2d.move(845 * R, 125 * R)
        self.TT2448_2d.Label.setText("TT2448")
        self.TT2448_2d.SetUnit(" K")


        self.TT2440_2d = Indicator(self.IVTab)
        self.TT2440_2d.move(1450 * R, 876 * R)
        self.TT2440_2d.Label.setText("TT2440")
        self.TT2440_2d.SetUnit(" K")


        self.TT2438_2d = Indicator(self.IVTab)
        self.TT2438_2d.move(1450 * R, 1082 * R)
        self.TT2438_2d.Label.setText("TT2438")
        self.TT2438_2d.SetUnit(" K")


        self.TT2436_2d = Indicator(self.IVTab)
        self.TT2436_2d.move(1450 * R, 1247 * R)
        self.TT2436_2d.Label.setText("TT2436")
        self.TT2436_2d.SetUnit(" K")


        self.TT2443_2d = Indicator(self.IVTab)
        self.TT2443_2d.move(1203 * R, 716 * R)
        self.TT2443_2d.Label.setText("TT2443")
        self.TT2443_2d.SetUnit(" K")


        self.TT2419_2d = Indicator(self.IVTab)
        self.TT2419_2d.move(455 * R, 330 * R)
        self.TT2419_2d.Label.setText("TT2419")
        self.TT2419_2d.SetUnit(" K")


        self.TT2421_2d = Indicator(self.IVTab)
        self.TT2421_2d.move(455 * R, 490 * R)
        self.TT2421_2d.Label.setText("TT2421")
        self.TT2421_2d.SetUnit(" K")


        self.TT2432_2d = Indicator(self.IVTab)
        self.TT2432_2d.move(750 * R, 382 * R)
        self.TT2432_2d.Label.setText("TT2432")
        self.TT2432_2d.SetUnit(" K")

        self.TT2428_2d = Indicator(self.IVTab)
        self.TT2428_2d.move(750 * R, 605 * R)
        self.TT2428_2d.Label.setText("TT2428")
        self.TT2428_2d.SetUnit(" K")

        self.TT2416_2d = Indicator(self.IVTab)
        self.TT2416_2d.move(640 * R, 1320 * R)
        self.TT2416_2d.Label.setText("TT2416")
        self.TT2416_2d.SetUnit(" K")

        self.TT2439_2d = Indicator(self.IVTab)
        self.TT2439_2d.move(840 * R, 1081 * R)
        self.TT2439_2d.Label.setText("TT2439")
        self.TT2439_2d.SetUnit(" K")

        self.TT2423_2d = Indicator(self.IVTab)
        self.TT2423_2d.move(1721 * R, 356 * R)
        self.TT2423_2d.Label.setText("TT2423")
        self.TT2423_2d.SetUnit(" K")

        self.TT2419_2d = Indicator(self.IVTab)
        self.TT2419_2d.move(1721 * R, 523 * R)
        self.TT2419_2d.Label.setText("TT2419")
        self.TT2419_2d.SetUnit(" K")

        self.TT2426_2d = Indicator(self.IVTab)
        self.TT2426_2d.move(2076 * R, 240 * R)
        self.TT2426_2d.Label.setText("TT2426")
        self.TT2426_2d.SetUnit(" K")

        self.TT2430_2d = Indicator(self.IVTab)
        self.TT2430_2d.move(2076 * R, 410 * R)
        self.TT2430_2d.Label.setText("TT2430")
        self.TT2430_2d.SetUnit(" K")

        self.TT2113_2d = Indicator(self.IVTab)
        self.TT2113_2d.move(224 * R, 634 * R)
        self.TT2113_2d.Label.setText("TT2113")
        self.TT2113_2d.SetUnit(" K")

        self.TT2450_2d = Indicator(self.IVTab)
        self.TT2450_2d.move(223 * R, 1250 * R)
        self.TT2450_2d.Label.setText("TT2450")
        self.TT2450_2d.SetUnit(" K")

        self.TT2444_2d = Indicator(self.IVTab)
        self.TT2444_2d.move(1836 * R, 739 * R)
        self.TT2444_2d.Label.setText("TT2444")
        self.TT2444_2d.SetUnit(" K")

        self.TT2445_2d = Indicator(self.IVTab)
        self.TT2445_2d.move(304 * R, 719 * R)
        self.TT2445_2d.Label.setText("TT2445")
        self.TT2445_2d.SetUnit(" K")

        self.TT2437_2d = Indicator(self.IVTab)
        self.TT2437_2d.move(124 * R, 1228 * R)
        self.TT2437_2d.Label.setText("TT2437")
        self.TT2437_2d.SetUnit(" K")

        self.TT2435_2d = Indicator(self.IVTab)
        self.TT2435_2d.move(2164 * R, 559 * R)
        self.TT2435_2d.Label.setText("TT2435")
        self.TT2435_2d.SetUnit(" K")

        self.TT2449_2d = Indicator(self.IVTab)
        self.TT2449_2d.move(2109 * R, 129 * R)
        self.TT2449_2d.Label.setText("TT2449")
        self.TT2449_2d.SetUnit(" K")

        self.LED1_OUT_2d = Indicator(self.IVTab)
        self.LED1_OUT_2d.move(1750 * R, 90 * R)
        self.LED1_OUT_2d.Label.setText("LED1_OUT")
        self.LED1_OUT_2d.SetUnit("")

        self.LED2_OUT_2d = Indicator(self.IVTab)
        self.LED2_OUT_2d.move(1130 * R, 90 * R)
        self.LED2_OUT_2d.Label.setText("LED2_OUT")
        self.LED2_OUT_2d.SetUnit("")

        self.LED3_OUT_2d = Indicator(self.IVTab)
        self.LED3_OUT_2d.move(700 * R, 90 * R)
        self.LED3_OUT_2d.Label.setText("LED3_OUT")
        self.LED3_OUT_2d.SetUnit("")

        self.LED_MAX_2d = Indicator(self.IVTab)
        self.LED_MAX_2d.move(550 * R, 90 * R)
        self.LED_MAX_2d.Label.setText("LED_MAX")
        self.LED_MAX_2d.SetUnit("")

        # Fluid tab buttons

        self.PT2316 = Indicator(self.FluidTab)
        self.PT2316.move(1900*R, 360*R)
        self.PT2316.Label.setText("PT2316")
        self.PT2316.SetUnit(" bar")

        self.PT2330 = Indicator(self.FluidTab)
        self.PT2330.move(1780*R, 360*R)
        self.PT2330.Label.setText("PT2330")
        self.PT2330.SetUnit(" bar")

        self.PT2335 = Indicator(self.FluidTab)
        self.PT2335.move(1590*R, 420*R)
        self.PT2335.Label.setText("PT2335")
        self.PT2335.SetUnit(" bar")


        self.PS8302 = ColoredStatus(self.FluidTab, mode=2)
        self.PS8302.move(1300 * R, 300 * R)
        self.PS8302.Label.setText("PS8302")

        self.PS2352 = ColoredStatus(self.FluidTab, mode=2)
        self.PS2352.move(950 * R, 240 * R)
        self.PS2352.Label.setText("PS2352")

        self.LI2340 = Indicator(self.FluidTab)
        self.LI2340.move(2250*R, 880*R)
        self.LI2340.Label.setText("LI2340 ")

        self.PT1101Fluid = Indicator(self.FluidTab)
        self.PT1101Fluid.move(1030*R, 1300*R)
        self.PT1101Fluid.Label.setText("PT1101")
        self.PT1101Fluid.SetUnit(" bar")

        self.PT2121Fluid = Indicator(self.FluidTab)
        self.PT2121Fluid.move(1260*R, 1300*R)
        self.PT2121Fluid.Label.setText("PT2121")
        self.PT2121Fluid.SetUnit(" bar")

        self.MFC1316 = LOOPPID_v2(self.FluidTab)
        self.MFC1316.move(400*R, 800*R)
        self.MFC1316.Label.setText("MFC1316")
        self.MFC1316.LOOPPIDWindow.setWindowTitle("MFC1316")
        self.MFC1316.LOOPPIDWindow.Label.setText("MFC1316")
        self.MFC1316.LOOPPIDWindow.RTD1.Label.setText("TT1332")
        self.MFC1316.LOOPPIDWindow.RTD2.Label.setText("EMPTY")
        self.MFC1316.LOOPPIDWindow.SetGroupUnit(" ")


        self.PT1361 = Indicator(self.FluidTab)
        self.PT1361.move(810 * R, 870 * R)
        self.PT1361.Label.setText("PT1361")
        self.PT1361.SetUnit(" bar")

        self.PT1325 = Indicator(self.FluidTab)
        self.PT1325.move(630*R, 900*R)
        self.PT1325.Label.setText("PT1325")
        self.PT1325.SetUnit(" bar")

        self.PV1344=Valve_v2(self.FluidTab)
        self.PV1344.Label.setText("PV1344")
        self.PV1344.move(1460*R,870*R)

        self.PV1344_icon = Valve_image(self.FluidTab, mode="H")
        self.PV1344_icon.move(1520 * R, 815 * R)

        self.PV5305 = Valve_v2(self.FluidTab)
        self.PV5305.Label.setText("PV5305")
        self.PV5305.move(1200*R, 530*R)

        self.PV5305_icon = Valve_image(self.FluidTab, mode="H")
        self.PV5305_icon.move(1266 * R, 490 * R)

        self.PV5306 = Valve_v2(self.FluidTab)
        self.PV5306.Label.setText("PV5306")
        self.PV5306.move(1211*R, 808*R)

        self.PV5306_icon = Valve_image(self.FluidTab, mode="V")
        self.PV5306_icon.move(1384 * R, 813 * R)

        self.PV5307 = Valve_v2(self.FluidTab)
        self.PV5307.Label.setText("PV5307")
        self.PV5307.move(988*R, 768*R)

        self.PV5307_icon = Valve_image(self.FluidTab, mode="H")
        self.PV5307_icon.move(1013 * R, 720 * R)

        self.PV5309 = Valve_v2(self.FluidTab)
        self.PV5309.Label.setText("PV5309")
        self.PV5309.move(1420*R, 344*R)

        self.PV5309_icon = Valve_image(self.FluidTab, mode="V")
        self.PV5309_icon.move(1360 * R, 350 * R)

        self.PT5304= Indicator(self.FluidTab)
        self.PT5304.move(1420*R, 250*R)
        self.PT5304.Label.setText("PT5304")
        self.PT5304.SetUnit(" bar")

        self.PT_EN6306 = Valve_v2(self.FluidTab)
        self.PT_EN6306.Label.setText("PG6306")
        self.PT_EN6306.move(60 * R, 60 * R)

        self.PV1201_STATE = Indicator(self.FluidTab)
        self.PV1201_STATE.move(1030*R, 1090*R)
        self.PV1201_STATE.Label.setText("PV1201_STAT")
        self.PV1201_STATE.SetUnit("")

        self.PV2201_STATE = Indicator(self.FluidTab)
        self.PV2201_STATE.move(1260*R, 1090*R)
        self.PV2201_STATE.Label.setText("PV2201_STAT")
        self.PV2201_STATE.SetUnit("")

        self.PT1101_AVG = Indicator(self.FluidTab)
        self.PT1101_AVG.move(1030 * R, 1150 * R)
        self.PT1101_AVG.Label.setText("PT1101_AVG")
        self.PT1101_AVG.SetUnit("")

        self.PT2121_AVG = Indicator(self.FluidTab)
        self.PT2121_AVG.move(1260 * R, 1150 * R)
        self.PT2121_AVG.Label.setText("PT2121_AVG")
        self.PT2121_AVG.SetUnit("")

        self.PDIFF_PT2121PT1101 = Indicator(self.FluidTab)
        self.PDIFF_PT2121PT1101.move(1400 * R, 1300 * R)
        self.PDIFF_PT2121PT1101.Label.setText('\u0394'+"P_2121/1101")
        self.PDIFF_PT2121PT1101.SetUnit(" bar")

        self.PDIFF_PT2121PT1325 = Indicator(self.FluidTab)
        self.PDIFF_PT2121PT1325.move(1520 * R, 1300 * R)
        self.PDIFF_PT2121PT1325.Label.setText('\u0394'+"P_2121/1325")
        self.PDIFF_PT2121PT1325.SetUnit(" bar")








        # Hydraulic buttons

        self.PUMP3305 = LOOP2PT_v2(self.HydraulicTab)
        self.PUMP3305.move(365*R, 380*R)
        self.PUMP3305.Label.setText("PUMP3305")
        self.PUMP3305.State.LButton.setText("ON")
        self.PUMP3305.State.RButton.setText("OFF")
        self.PUMP3305.LOOP2PTWindow.setWindowTitle("PUMP3305")
        self.PUMP3305.LOOP2PTWindow.Label.setText("PUMP3305")

        self.PUMP3305_icon = Pump_image(self.HydraulicTab)
        self.PUMP3305_icon.move(285*R, 390*R)


        self.PUMP3305_CON = ColoredStatus(self.HydraulicTab, mode = 2)
        self.PUMP3305_CON.Label.setText("CON")
        self.PUMP3305_CON.move(365*R,330*R)

        self.PUMP3305_OL = ColoredStatus(self.HydraulicTab, mode=2)
        self.PUMP3305_OL.Label.setText("OL")
        self.PUMP3305_OL.move(435 * R, 330 * R)

        self.ES3347 = ColoredStatus(self.HydraulicTab, mode=3)
        self.ES3347.move(505 * R, 330 * R)
        self.ES3347.Label.setText("ES3347")



        self.TT3401 = Indicator(self.HydraulicTab)
        self.TT3401.move(385*R, 500*R)
        self.TT3401.Label.setText("TT3401")

        self.TT3402 = Indicator(self.HydraulicTab)
        self.TT3402.move(90*R, 53)
        self.TT3402.Label.setText("TT3402")

        self.PT3314 = Indicator(self.HydraulicTab)
        self.PT3314.move(700*R, 450*R)
        self.PT3314.Label.setText("PT3314")
        self.PT3314.SetUnit(" bar")

        self.PT3320 = Indicator(self.HydraulicTab)
        self.PT3320.move(880*R, 530*R)
        self.PT3320.Label.setText("PT3320")
        self.PT3320.SetUnit(" bar")

        self.PT3308 = Indicator(self.HydraulicTab)
        self.PT3308.move(440*R, 1080*R)
        self.PT3308.Label.setText("PT3308")
        self.PT3308.SetUnit(" bar")

        self.PT3309 = Indicator(self.HydraulicTab)
        self.PT3309.move(665*R, 1245*R)
        self.PT3309.Label.setText("PT3309")
        self.PT3309.SetUnit(" bar")

        self.PT3311 = Indicator(self.HydraulicTab)
        self.PT3311.move(910*R, 1110*R)
        self.PT3311.Label.setText("PT3311")
        self.PT3311.SetUnit(" bar")

        self.HFSV3312 = Valve_v2(self.HydraulicTab)
        self.HFSV3312.Label.setText("HFSV3312")
        self.HFSV3312.move(670*R, 1040*R)

        self.HFSV3312_icon = Valve_image(self.HydraulicTab, mode="H")
        self.HFSV3312_icon.move(731 * R, 990* R)

        self.HFSV3323 = Valve_v2(self.HydraulicTab)
        self.HFSV3323.Label.setText("HFSV3323")
        self.HFSV3323.move(1050*R, 1210*R)

        self.HFSV3323_icon = Valve_image(self.HydraulicTab, mode="H")
        self.HFSV3323_icon.move(1112 * R, 1152 * R)

        self.HFSV3331 = Valve_v2(self.HydraulicTab)
        self.HFSV3331.Label.setText("HFSV3331")
        self.HFSV3331.move(1100*R, 320*R)

        self.HFSV3331_icon = Valve_image(self.HydraulicTab, mode="H")
        self.HFSV3331_icon.move(1172 * R, 280 * R)
        self.HFSV3331_icon.stackUnder(self.HFSV3331)

        self.PT3332 = Indicator(self.HydraulicTab)
        self.PT3332.move(1570*R, 1125*R)
        self.PT3332.Label.setText("PT3332")
        self.PT3332.SetUnit(" bar")

        self.PT3333 = Indicator(self.HydraulicTab)
        self.PT3333.move(1570*R, 1250*R)
        self.PT3333.Label.setText("PT3333")
        self.PT3333.SetUnit(" bar")


        self.SV3329 = Valve_v2(self.HydraulicTab)
        self.SV3329.Label.setText("SV3329")
        self.SV3329.move(1580*R, 470*R)

        self.SV3329_icon = Valve_image(self.HydraulicTab, mode="V")
        self.SV3329_icon.move(1547 * R, 470 * R)

        self.SV3322 = Valve_v2(self.HydraulicTab)
        self.SV3322.Label.setText("SV3322")
        self.SV3322.move(1000*R, 780*R)

        self.SV3322_icon = Valve_image(self.HydraulicTab, mode="H")
        self.SV3322_icon.move(1076 * R, 740 * R)


        self.SERVO3321 = LOOPPID_v2(self.HydraulicTab)
        self.SERVO3321.move(1200*R, 550*R)
        self.SERVO3321.Label.setText("SERVO3321")
        self.SERVO3321.LOOPPIDWindow.setWindowTitle("SERVO3321")
        self.SERVO3321.LOOPPIDWindow.Label.setText("SERVO3321")
        self.SERVO3321.LOOPPIDWindow.RTD1.Label.setText("EMPTY")
        self.SERVO3321.LOOPPIDWindow.RTD2.Label.setText("EMPTY")
        self.SERVO3321.LOOPPIDWindow.LOSP.Field.setText('-100')
        self.SERVO3321.LOOPPIDWindow.HISP.Field.setText('100')


        self.SV3325 = Valve_v2(self.HydraulicTab)
        self.SV3325.Label.setText("SV3325")
        self.SV3325.move(1270*R, 950*R)

        self.SV3325_icon = Valve_image(self.HydraulicTab, mode="V")
        self.SV3325_icon.move(1436 * R, 990 * R)

        self.SV3307 = Valve_v2(self.HydraulicTab)
        self.SV3307.Label.setText("SV3307")
        self.SV3307.move(200*R, 1030*R)

        self.SV3307_icon = Valve_image(self.HydraulicTab, mode="H")
        self.SV3307_icon.move(360 * R, 990 * R)

        self.SV3310 = Valve_v2(self.HydraulicTab)
        self.SV3310.Label.setText("SV3310")
        self.SV3310.move(800*R, 1245*R)

        self.SV3310_icon = Valve_image(self.HydraulicTab, mode="V")
        self.SV3310_icon.move(876 * R, 1160 * R)

        self.TT7403 = Indicator(self.HydraulicTab)
        self.TT7403.move(1880*R, 950*R)
        self.TT7403.Label.setText("TT7403")

        self.LT3335 = Indicator(self.HydraulicTab)
        self.LT3335.move(2100*R, 950*R)
        self.LT3335.Label.setText("LT3335")
        self.LT3335.SetUnit(" in")

        self.LT3338 = Indicator(self.HydraulicTab)
        self.LT3338.move(2100*R, 1010*R)
        self.LT3338.Label.setText("LT3338")
        self.LT3338.SetUnit(" in")

        self.LT3339 = Indicator(self.HydraulicTab)
        self.LT3339.move(2100*R, 1070*R)
        self.LT3339.Label.setText("LT3339")
        self.LT3339.SetUnit(" in")

        self.LT2122 = Indicator(self.HydraulicTab)
        self.LT2122.move(2200 * R, 1160 * R)
        self.LT2122.Label.setText("LT2122")
        self.LT2122.SetUnit(" %")

        self.LT2130 = Indicator(self.HydraulicTab)
        self.LT2130.move(2300 * R, 1160 * R)
        self.LT2130.Label.setText("LT2130")
        self.LT2130.SetUnit(" %")

        self.LS2126= ColoredStatus(self.HydraulicTab, mode= 2)
        self.LS2126.move(1900*R, 650*R)
        self.LS2126.Label.setText("LS2126")

        self.LS2127 = ColoredStatus(self.HydraulicTab, mode=2)
        self.LS2127.move(1900 * R, 700 * R)
        self.LS2127.Label.setText("LS2127")

        self.LS2128 = ColoredStatus(self.HydraulicTab, mode=2)
        self.LS2128.move(2100 * R, 650 * R)
        self.LS2128.Label.setText("LS2128")

        self.LS2129 = ColoredStatus(self.HydraulicTab, mode=2)
        self.LS2129.move(2100 * R, 700 * R)
        self.LS2129.Label.setText("LS2129")

        self.LS3338 = ColoredStatus(self.HydraulicTab, mode= 2)
        self.LS3338.move(2200*R, 1010*R)
        self.LS3338.Label.setText("LS3338")

        self.LS3339 = ColoredStatus(self.HydraulicTab, mode=2)
        self.LS3339.move(2200 * R, 1070 * R)
        self.LS3339.Label.setText("LS3339")


        self.CYL3334 = Indicator_ds(self.HydraulicTab)
        self.CYL3334.move(2100 * R, 1160 * R)
        self.CYL3334.Label.setText("CYL3334")
        self.CYL3334.SetUnit(" lbs")

        self.PT1101Hy = Indicator(self.HydraulicTab)
        self.PT1101Hy.move(1900*R, 800*R)
        self.PT1101Hy.Label.setText("PT1101")
        self.PT1101Hy.SetUnit(" bar")

        self.PT2121Hy = Indicator(self.HydraulicTab)
        self.PT2121Hy.move(2100*R, 800*R)
        self.PT2121Hy.Label.setText("PT2121")
        self.PT2121Hy.SetUnit(" bar")

        self.CYL3334_LT3335_CF4PRESSCALC = Indicator(self.HydraulicTab)
        self.CYL3334_LT3335_CF4PRESSCALC.move(2100 * R, 1300 * R)
        self.CYL3334_LT3335_CF4PRESSCALC.Label.setText('\u0394'+"P_CYL/LT/CF4")
        self.CYL3334_LT3335_CF4PRESSCALC.SetUnit(" bar")

        # Rack
        self.TT7401 = Indicator(self.RackTab)
        self.TT7401.move(100 * R, 50 * R)
        self.TT7401.Label.setText("TT7401")

        self.TT7402 = Indicator(self.RackTab)
        self.TT7402.move(200 * R, 50 * R)
        self.TT7402.Label.setText("TT7402")

        self.TT7403 = Indicator(self.RackTab)
        self.TT7403.move(300 * R, 50 * R)
        self.TT7403.Label.setText("TT7403")

        self.TT7404 = Indicator(self.RackTab)
        self.TT7404.move(400 * R, 50 * R)
        self.TT7404.Label.setText("TT7404")

        self.VLUPS = QtWidgets.QHBoxLayout(self.RackTab)
        self.VLUPS.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.VLUPS.setSpacing(20 * R)
        self.VLUPS.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupUPS = QtWidgets.QGroupBox(self.RackTab)
        self.GroupUPS.setTitle("UPS")
        self.GroupUPS.setLayout(self.VLUPS)
        self.GroupUPS.move(100 * R, 150 * R)

        self.UPS_UTILITY_OK = ColoredStatus(self.RackTab, mode=2)
        # self.UPS_UTILITY_OK.move(100 * R, 150 * R)
        self.VLUPS.addWidget(self.UPS_UTILITY_OK)
        self.UPS_UTILITY_OK.Label.setText("UTI_OK")

        self.UPS_BATTERY_OK = ColoredStatus(self.RackTab, mode=2)
        # self.UPS_UTILITY_OK.move(200 * R, 150 * R)
        self.VLUPS.addWidget(self.UPS_BATTERY_OK)
        self.UPS_BATTERY_OK.Label.setText("BATT_OK")

        # self.UPS_ON_BATT = ColoredStatus(self.RackTab, mode=2)
        # # self.UPS_ON_BATT.move(1900 * R, 470 * R)
        # self.VLUPS.addWidget(self.UPS_ON_BATT)
        # self.UPS_ON_BATT.Label.setText("ON_BATT")

        # self.UPS_LOW_BATT = ColoredStatus(self.RackTab, mode=1)
        # # self.UPS_LOW_BATT.move(1900 * R, 470 * R)
        # self.VLUPS.addWidget(self.UPS_LOW_BATT)
        # self.UPS_LOW_BATT.Label.setText("LOW_BATT")

        # Data and Signal Tab
        self.ReadSettings = Loadfile(self.DatanSignalTab)
        self.ReadSettings.move(50*R, 50*R)
        # self.ReadSettings.LoadFileButton.clicked.connect(
        #     lambda x: self.Recover(address=self.ReadSettings.FilePath.text()))

        self.SaveSettings = CustomSave(self.DatanSignalTab)
        self.SaveSettings.move(700*R, 50*R)
        # self.SaveSettings.SaveFileButton.clicked.connect(
        #     lambda x: self.Save(directory=self.SaveSettings.Head, project=self.SaveSettings.Tail))

        self.TS_PRO = ProcedureTS_v2(self.DatanSignalTab)
        self.TS_PRO.move(50 * R, 950 * R)

        # self.TS_ADDREM = ProcedureWidget_TS(self.DatanSignalTab)
        # self.TS_ADDREM.move(1800*R, 150*R)
        # self.TS_ADDREM.Group.setTitle("TS ADDREM")
        # self.TS_ADDREM.objectname = "TS_ADDREM"
        # self.TS_ADDREM.expandwindow.MAXTIME_RD.Unit=' s'
        # self.TS_ADDREM.expandwindow.FLOWET.Unit = ' s'

        # self.TS_EMPTY = ProcedureWidget(self.DatanSignalTab)
        # self.TS_EMPTY.move(1800 * R, 390 * R)
        # self.TS_EMPTY.Group.setTitle("TS EMPTY")
        # self.TS_EMPTY.objectname = "TS_EMPTY"
        #
        # self.TS_EMPTYALL = ProcedureWidget(self.DatanSignalTab)
        # self.TS_EMPTYALL.move(1800 * R, 630 * R)
        # self.TS_EMPTYALL.Group.setTitle("TS EMPTY ALL")
        # self.TS_EMPTYALL.objectname = "TS_EMPTYALL"

        self.PU_PRIME = ProcedureWidget(self.DatanSignalTab)
        self.PU_PRIME.move(700 * R, 390 * R)
        self.PU_PRIME.Group.setTitle("PU PRIME")
        self.PU_PRIME.objectname = "PU_PRIME"

        self.WRITE_SLOWDAQ = ProcedureWidget(self.DatanSignalTab)
        self.WRITE_SLOWDAQ.move(700 * R, 650 * R)
        self.WRITE_SLOWDAQ.Group.setTitle("WRITE SLOWDAQ")
        self.WRITE_SLOWDAQ.objectname = "WRITE_SLOWDAQ"

        self.PRESSURE_CYCLE = ProcedureWidget_PC(self.DatanSignalTab)
        self.PRESSURE_CYCLE.move(700 * R, 150 * R)
        self.PRESSURE_CYCLE.Group.setTitle("PRESSURE_CYCLE")
        self.PRESSURE_CYCLE.objectname = "PRESSURE_CYCLE"
        self.PRESSURE_CYCLE.expandwindow.EXPTIME_RD.Unit = " s"
        self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_RD.Unit = " s"
        self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_RD.Unit = " s"
        self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_RD.Unit = " s"
        self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_RD.Unit = " s"

        self.CRYOVALVE_CONTROL = ProcedureWidget(self.DatanSignalTab)
        self.CRYOVALVE_CONTROL.move(1300 * R, 150 * R)
        self.CRYOVALVE_CONTROL.Group.setTitle("CRYOVALVE_CONTROL")
        self.CRYOVALVE_CONTROL.objectname = "CRYOVALVE_CONTROL"
        

        self.MAN_TS = Flag(self.DatanSignalTab)
        self.MAN_TS.move(1900 * R, 150 * R)
        self.MAN_TS.Label.setText("MAN_TS")

        self.MAN_HYD = Flag(self.DatanSignalTab)
        self.MAN_HYD.move(1900 * R, 260 * R)
        self.MAN_HYD.Label.setText("MAN_HYD")

        self.PCYCLE_AUTOCYCLE = Flag(self.DatanSignalTab)
        self.PCYCLE_AUTOCYCLE.move(1900 * R, 370 * R)
        self.PCYCLE_AUTOCYCLE.Label.setText("PCYCLE_AUTO")

        self.CRYOVALVE_OPENCLOSE = Flag(self.DatanSignalTab)
        self.CRYOVALVE_OPENCLOSE.move(1900 * R, 480 * R)
        self.CRYOVALVE_OPENCLOSE.Label.setText("CRYO_OP/CLS")

        self.CRYOVALVE_PV1201ACT = Flag(self.DatanSignalTab)
        self.CRYOVALVE_PV1201ACT.move(1900 * R, 590 * R)
        self.CRYOVALVE_PV1201ACT.Label.setText("CRYO_PV1201")

        self.CRYOVALVE_PV2201ACT = Flag(self.DatanSignalTab)
        self.CRYOVALVE_PV2201ACT.move(1900 * R, 700 * R)
        self.CRYOVALVE_PV2201ACT.Label.setText("CRYO_PV2201")

        # INTLCK button
        self.INTLCKWindow = INTLCK_Win_v2()
        self.INTLCKButton = INTLCKButton(self.INTLCKWindow, self)
        self.INTLCKButton.SubWindow.resize(1000 * R, 500 * R)
        # self.AlarmButton.StatusWindow.AlarmWindow()

        self.INTLCKButton.move(90 * R, 1350 * R)
        # self.INTLCKButton.Button.setText("INTLCK Button")

    def Alarm_system(self):
        # Alarm button
        self.AlarmWindow = AlarmWin()
        self.AlarmButton = AlarmButton(self.AlarmWindow, self)
        self.AlarmButton.SubWindow.resize(1000*R, 500*R)

        # self.AlarmButton.StatusWindow.AlarmWindow()

        self.AlarmButton.move(10*R, 1350*R)
        # self.AlarmButton.move(10 * R, 1200 * R)
        # self.AlarmButton.Button.setText("Alarm Button")


        #commands stack
        self.address =env.merge_dic(env.TT_FP_ADDRESS,env.TT_BO_ADDRESS,env.PT_ADDRESS,env.LEFT_REAL_ADDRESS,
                                                     env.DIN_ADDRESS,env.VALVE_ADDRESS,env.LOOPPID_ADR_BASE,env.LOOP2PT_ADR_BASE,env.PROCEDURE_ADDRESS, env.INTLK_A_ADDRESS,
                                    env.INTLK_D_ADDRESS,env.FLAG_ADDRESS, env.AD_ADDRESS)
        self.commands = {}
        self.command_buffer_waiting= 1
        # self.statustransition={}

        self.Valve_buffer = copy.copy(env.VALVE_OUT)
        self.CHECKED = False

        self.Switch_buffer = copy.copy(env.SWITCH_OUT)
        self.LOOPPID_EN_buffer = copy.copy(env.LOOPPID_EN)
        self.LOOP2PT_OUT_buffer =copy.copy(env.LOOP2PT_OUT)
        self.INTLK_D_DIC_buffer = copy.copy(env.INTLK_D_DIC)
        self.INTLK_A_DIC_buffer = copy.copy(env.INTLK_A_DIC)
        self.FLAG_buffer = copy.copy(env.FLAG_DIC)

        self.BORTDAlarmMatrix = [self.AlarmButton.SubWindow.TT2101, self.AlarmButton.SubWindow.TT2111,
                                 self.AlarmButton.SubWindow.TT2113, self.AlarmButton.SubWindow.TT2118,
                                 self.AlarmButton.SubWindow.TT2119, self.AlarmButton.SubWindow.TT4330,
                                 self.AlarmButton.SubWindow.TT6203, self.AlarmButton.SubWindow.TT6207,
                                 self.AlarmButton.SubWindow.TT6211, self.AlarmButton.SubWindow.TT6213,
                                 self.AlarmButton.SubWindow.TT6222, self.AlarmButton.SubWindow.TT6407,
                                 self.AlarmButton.SubWindow.TT6408, self.AlarmButton.SubWindow.TT6409,
                                 self.AlarmButton.SubWindow.TT6415, self.AlarmButton.SubWindow.TT6416]

        self.FPRTDAlarmMatrix = [self.AlarmButton.SubWindow.TT2420, self.AlarmButton.SubWindow.TT2422,
                                 self.AlarmButton.SubWindow.TT2424, self.AlarmButton.SubWindow.TT2425,
                                 self.AlarmButton.SubWindow.TT2442, self.AlarmButton.SubWindow.TT2403,
                                 self.AlarmButton.SubWindow.TT2418, self.AlarmButton.SubWindow.TT2427,
                                 self.AlarmButton.SubWindow.TT2429, self.AlarmButton.SubWindow.TT2431,
                                 self.AlarmButton.SubWindow.TT2441, self.AlarmButton.SubWindow.TT2414,
                                 self.AlarmButton.SubWindow.TT2413, self.AlarmButton.SubWindow.TT2412,
                                 self.AlarmButton.SubWindow.TT2415, self.AlarmButton.SubWindow.TT2409,
                                 self.AlarmButton.SubWindow.TT2436, self.AlarmButton.SubWindow.TT2438,
                                 self.AlarmButton.SubWindow.TT2440, self.AlarmButton.SubWindow.TT2402,
                                 self.AlarmButton.SubWindow.TT2411, self.AlarmButton.SubWindow.TT2443,
                                 self.AlarmButton.SubWindow.TT2417, self.AlarmButton.SubWindow.TT2404,
                                 self.AlarmButton.SubWindow.TT2408, self.AlarmButton.SubWindow.TT2407,
                                 self.AlarmButton.SubWindow.TT2406, self.AlarmButton.SubWindow.TT2428,
                                 self.AlarmButton.SubWindow.TT2432, self.AlarmButton.SubWindow.TT2421,
                                 self.AlarmButton.SubWindow.TT2416, self.AlarmButton.SubWindow.TT2439,
                                 self.AlarmButton.SubWindow.TT2419, self.AlarmButton.SubWindow.TT2423,
                                 self.AlarmButton.SubWindow.TT2426, self.AlarmButton.SubWindow.TT2430,
                                 self.AlarmButton.SubWindow.TT2450, self.AlarmButton.SubWindow.TT2401,
                                 self.AlarmButton.SubWindow.TT2449, self.AlarmButton.SubWindow.TT2445,
                                 self.AlarmButton.SubWindow.TT2444, self.AlarmButton.SubWindow.TT2435,
                                 self.AlarmButton.SubWindow.TT2437, self.AlarmButton.SubWindow.TT2446,
                                 self.AlarmButton.SubWindow.TT2447, self.AlarmButton.SubWindow.TT2448,
                                 self.AlarmButton.SubWindow.TT2410, self.AlarmButton.SubWindow.TT2405,
                                 self.AlarmButton.SubWindow.TT6220, self.AlarmButton.SubWindow.TT6401,
                                 self.AlarmButton.SubWindow.TT6404, self.AlarmButton.SubWindow.TT6405,
                                 self.AlarmButton.SubWindow.TT6406, self.AlarmButton.SubWindow.TT6410,
                                 self.AlarmButton.SubWindow.TT6411, self.AlarmButton.SubWindow.TT6412,
                                 self.AlarmButton.SubWindow.TT6413, self.AlarmButton.SubWindow.TT6414,
                                 self.AlarmButton.SubWindow.TT7401, self.AlarmButton.SubWindow.TT7402,
                                 self.AlarmButton.SubWindow.TT7403, self.AlarmButton.SubWindow.TT7404,
                                 self.AlarmButton.SubWindow.TT3401]


        self.PTAlarmMatrix = [self.AlarmButton.SubWindow.PT1101, self.AlarmButton.SubWindow.PT1325,
                              self.AlarmButton.SubWindow.PT1361,
                              self.AlarmButton.SubWindow.PT2316, self.AlarmButton.SubWindow.PT2121,
                              self.AlarmButton.SubWindow.PT2330, self.AlarmButton.SubWindow.PT2335,
                              self.AlarmButton.SubWindow.PT3308, self.AlarmButton.SubWindow.PT3309,
                              self.AlarmButton.SubWindow.PT3311,self.AlarmButton.SubWindow.PT3314,
                              self.AlarmButton.SubWindow.PT3320, self.AlarmButton.SubWindow.PT3332,
                              self.AlarmButton.SubWindow.PT3333, self.AlarmButton.SubWindow.PT4306,
                              self.AlarmButton.SubWindow.PT4315, self.AlarmButton.SubWindow.PT4319,
                              self.AlarmButton.SubWindow.PT4322, self.AlarmButton.SubWindow.PT4325,
                              self.AlarmButton.SubWindow.PT5304,self.AlarmButton.SubWindow.PT6302,
                              self.AlarmButton.SubWindow.PT6306,self.AlarmButton.SubWindow.PT1101_AVG,
                              self.AlarmButton.SubWindow.PT2121_AVG]

        self.PTDIFFAlarmMatrix =[self.AlarmButton.SubWindow.PDIFF_PT2121PT1101,
                              self.AlarmButton.SubWindow.PDIFF_PT2121PT1325,self.AlarmButton.SubWindow.CYL3334_LT3335_CF4PRESSCALC]

        self.expPTAlarmMatrix = [self.AlarmButton.SubWindow.PT6302,
                              self.AlarmButton.SubWindow.PT6306]

        self.LEFTVariableMatrix = [self.AlarmButton.SubWindow.BFM4313, self.AlarmButton.SubWindow.LT3335,
                                   self.AlarmButton.SubWindow.MFC1316_IN, self.AlarmButton.SubWindow.CYL3334_FCALC,
                                   self.AlarmButton.SubWindow.SERVO3321_IN_REAL, self.AlarmButton.SubWindow.TS1_MASS,
                                   self.AlarmButton.SubWindow.TS2_MASS, self.AlarmButton.SubWindow.TS3_MASS,self.AlarmButton.SubWindow.PV1201_STATE, self.AlarmButton.SubWindow.PV2201_STATE,
                                   self.AlarmButton.SubWindow.LED1_OUT,self.AlarmButton.SubWindow.LED2_OUT,self.AlarmButton.SubWindow.LED3_OUT,
                                   self.AlarmButton.SubWindow.LED_MAX]

        self.ADVariableMatrix = [ self.AlarmButton.SubWindow.LT2122,
                                   self.AlarmButton.SubWindow.LT2130]

        self.DinAlarmMatrix = [self.AlarmButton.SubWindow.LS3338, self.AlarmButton.SubWindow.LS3339,
                                   self.AlarmButton.SubWindow.ES3347, self.AlarmButton.SubWindow.PUMP3305_CON,
                                   self.AlarmButton.SubWindow.PUMP3305_OL, self.AlarmButton.SubWindow.PS2352,
                               self.AlarmButton.SubWindow.PS8302,

                               self.AlarmButton.SubWindow.LS2126, self.AlarmButton.SubWindow.LS2127,
                               self.AlarmButton.SubWindow.LS2128, self.AlarmButton.SubWindow.LS2129,
                               self.AlarmButton.SubWindow.CC9313_POWER, self.AlarmButton.SubWindow.UPS_UTILITY_OK,
                               self.AlarmButton.SubWindow.UPS_BATTERY_OK]



        self.LOOPPIDAlarmMatrix = [self.AlarmButton.SubWindow.SERVO3321, self.AlarmButton.SubWindow.HTR6225,
                                   self.AlarmButton.SubWindow.HTR2123, self.AlarmButton.SubWindow.HTR2124,
                                   self.AlarmButton.SubWindow.HTR2125, self.AlarmButton.SubWindow.HTR1202,
                                   self.AlarmButton.SubWindow.HTR2203, self.AlarmButton.SubWindow.HTR6202,
                                      self.AlarmButton.SubWindow.HTR6206,self.AlarmButton.SubWindow.HTR6210,
                                      self.AlarmButton.SubWindow.HTR6223,self.AlarmButton.SubWindow.HTR6224,
                                      self.AlarmButton.SubWindow.HTR6219,self.AlarmButton.SubWindow.HTR6221,
                                      self.AlarmButton.SubWindow.HTR6214, self.AlarmButton.SubWindow.MFC1316]

        self.AlarmMatrix = self.BORTDAlarmMatrix + self.FPRTDAlarmMatrix + self.PTAlarmMatrix + self.PTDIFFAlarmMatrix +self.LEFTVariableMatrix + self.ADVariableMatrix +self.LOOPPIDAlarmMatrix



    def StartUpdater(self):
        self.command_lock = threading.Lock()
        install()
        self.clientthread = UpdateClient(commands=self.commands, command_lock=self.command_lock)
        # when new data comes, update the display
        self.clientthread.client_data_transport.connect(self.updatedisplay)
        self.clientthread.start()

   # Stop all updater threads
    @QtCore.Slot()
    def StopUpdater(self):
        self.clientthread.join()

    @QtCore.Slot()
    def set_background(self, num = 0):
        list = ["PV_v2.png","HDPE_v2.png","IV_v2.png"]
        pixmap_chamber = QtGui.QPixmap(os.path.join(self.ImagePath, list[num]))
        pixmap_chamber = pixmap_chamber.scaledToWidth(2400 * R)
        self.ChamberTab.Background.setPixmap(QtGui.QPixmap(pixmap_chamber))

    @QtCore.Slot()
    def set_expansion(self, layer=None):
        if layer == "PV":
            # if PV is set all expanded or all collapsed
            if self.PV_group[0]:
                # loop over all widgets
                for i in self.PV_group[2:]:
                    # identify which type of widgets, heaters or RTDs/PTs
                    if isinstance(i,LOOPPID_v3):
                        #check itis checked or not. Checked -> right arrow-> collapsed
                        if not i.Tool.isChecked():
                            i.Tool.animateClick()
                        else:
                            pass
                    elif isinstance(i,Indicator_v2):
                        if not i.Field.isVisible():
                            i.toggle_value_visibility()
                        else:
                            pass
                self.PV_group[0] = False
            else:
                for i in self.PV_group[2:]:
                    # identify which type of widgets, heaters or RTDs/PTs
                    if isinstance(i,LOOPPID_v3):
                        # check itis checked or not. Checked -> right arrow-> collapsed
                        if i.Tool.isChecked():
                            i.Tool.animateClick()
                        else:
                            pass
                    elif isinstance(i, Indicator_v2):
                        if i.Field.isVisible():
                            i.toggle_value_visibility()
                        else:
                            pass
                self.PV_group[0] = True
        elif layer == "IV":
            if self.IV_group[0]:
                # loop over all widgets
                for i in self.IV_group[2:]:
                    # identify which type of widgets, heaters or RTDs/PTs
                    if isinstance(i, LOOPPID_v3):
                        # check itis checked or not. Checked -> right arrow-> collapsed
                        if not i.Tool.isChecked():
                            i.Tool.animateClick()
                        else:
                            pass
                    elif isinstance(i, Indicator_v2):
                        if not i.Field.isVisible():
                            i.toggle_value_visibility()
                        else:
                            pass
                self.IV_group[0] = False
            else:
                for i in self.IV_group[2:]:
                    # identify which type of widgets, heaters or RTDs/PTs
                    if isinstance(i, LOOPPID_v3):
                        # check itis checked or not. Checked -> right arrow-> collapsed
                        if i.Tool.isChecked():
                            i.Tool.animateClick()
                        else:
                            pass
                    elif isinstance(i, Indicator_v2):
                        if i.Field.isVisible():
                            i.toggle_value_visibility()
                        else:
                            pass
                self.IV_group[0] = True
        elif layer == "HDPE":
            if self.HDPE_group[0]:
                # loop over all widgets
                for i in self.HDPE_group[2:]:
                    # identify which type of widgets, heaters or RTDs/PTs
                    if isinstance(i, LOOPPID_v3):
                        # check itis checked or not. Checked -> right arrow-> collapsed
                        if not i.Tool.isChecked():
                            i.Tool.animateClick()
                        else:
                            pass
                    elif isinstance(i, Indicator_v2):
                        if not i.Field.isVisible():
                            i.toggle_value_visibility()
                        else:
                            pass
                self.HDPE_group[0] = False
            else:
                for i in self.HDPE_group[2:]:
                    # identify which type of widgets, heaters or RTDs/PTs
                    if isinstance(i, LOOPPID_v3):
                        # check itis checked or not. Checked -> right arrow-> collapsed
                        if i.Tool.isChecked():
                            i.Tool.animateClick()
                        else:
                            pass
                    elif isinstance(i, Indicator_v2):
                        if i.Field.isVisible():
                            i.toggle_value_visibility()
                        else:
                            pass
                self.HDPE_group[0] = True

    @QtCore.Slot()
    def switch_visibility(self, layer=None):
        if layer == "PV":
            if self.PV_group[1]:
                for i in self.PV_group[2:]:
                    i.setVisible(False)
                self.PV_group[1]=False
            else:
                for i in self.PV_group[2:]:
                    i.setVisible(True)
                self.PV_group[1] = True
        elif layer == "IV":
            if self.IV_group[1]:
                for i in self.IV_group[2:]:
                    i.setVisible(False)
                self.IV_group[1]=False
            else:
                for i in self.IV_group[2:]:
                    i.setVisible(True)
                self.IV_group[1] = True
        elif layer == "HDPE":
            if self.HDPE_group[1]:
                for i in self.HDPE_group[2:]:
                    i.setVisible(False)
                self.HDPE_group[1] = False
            else:
                for i in self.HDPE_group[2:]:
                    i.setVisible(True)
                self.HDPE_group[1] = True
        else:
            pass

    @QtCore.Slot()
    def set_visibility_true_only(self, layer=None):
        if layer=="PV":
            if not self.PV_group[1]:
                self.switch_visibility(layer="PV")
                self.PV_switch.update_visible(self.PV_group[1])
            if self.HDPE_group[1]:
                self.switch_visibility(layer="HDPE")
                self.HDPE_switch.update_visible(self.HDPE_group[1])
            if self.IV_group[1]:
                self.switch_visibility(layer="IV")
                self.IV_switch.update_visible(self.IV_group[1])
        if layer == "HDPE":
            if not self.HDPE_group[1]:
                self.switch_visibility(layer="HDPE")
                self.HDPE_switch.update_visible(self.HDPE_group[1])
            if self.PV_group[1]:
                self.switch_visibility(layer="PV")
                self.PV_switch.update_visible(self.PV_group[1])
            if self.IV_group[1]:
                self.switch_visibility(layer="IV")
                self.IV_switch.update_visible(self.IV_group[1])
        if layer == "IV":
            if not self.IV_group[1]:
                self.switch_visibility(layer="IV")
                self.IV_switch.update_visible(self.IV_group[1])
            if self.HDPE_group[1]:
                self.switch_visibility(layer="HDPE")
                self.HDPE_switch.update_visible(self.HDPE_group[1])
            if self.PV_group[1]:
                self.switch_visibility(layer="PV")
                self.PV_switch.update_visible(self.PV_group[1])


    # signal connections to write settings to PLC codes

    def signal_connection(self):

        # Data signal saving and writing
        self.SaveSettings.SaveFileButton.clicked.connect(lambda : self.SaveSettings.SavecsvConfig(self.clientthread.receive_dic))
        # man_set update the low/high/active status to bkg code
        self.ReadSettings.LoadFileButton.clicked.connect(lambda : self.man_set(self.ReadSettings.default_dict))
        # man_activate set the check status in current GUI widgets
        self.ReadSettings.LoadFileButton.clicked.connect(lambda : self.man_activated(self.ReadSettings.default_dict))

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

        self.CC9313_CONT.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.CC9313_CONT.Label.text()))
        self.CC9313_CONT.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.CC9313_CONT.Label.text()))
        self.PT_EN6306.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PT_EN6306.Label.text()))
        self.PT_EN6306.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PT_EN6306.Label.text()))
        self.PV4345.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4345.Label.text()))
        self.PV4345.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4345.Label.text()))
        #

        self.SERVO3321.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.SERVO3321.LOOPPIDWindow.Label.text()))
        self.SERVO3321.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.SERVO3321.LOOPPIDWindow.Label.text()))
        self.SERVO3321.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.SERVO3321.LOOPPIDWindow.Label.text()))
        self.SERVO3321.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.SERVO3321.LOOPPIDWindow.Label.text()))
        self.SERVO3321.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.SERVO3321.LOOPPIDWindow.Label.text(), 0))
        self.SERVO3321.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.SERVO3321.LOOPPIDWindow.Label.text(), 1))
        self.SERVO3321.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.SERVO3321.LOOPPIDWindow.Label.text(), 2))
        self.SERVO3321.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.SERVO3321.LOOPPIDWindow.Label.text(), 3))

        self.SERVO3321.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.SERVO3321.LOOPPIDWindow.Label.text(),
                                     self.SERVO3321.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.SERVO3321.LOOPPIDWindow.SP.Field.text()),
                                     float(self.SERVO3321.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.SERVO3321.LOOPPIDWindow.LOSP.Field.text())))

        self.MFC1316.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.MFC1316.LOOPPIDWindow.Label.text()))
        self.MFC1316.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.MFC1316.LOOPPIDWindow.Label.text()))
        self.MFC1316.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.MFC1316.LOOPPIDWindow.Label.text()))
        self.MFC1316.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.MFC1316.LOOPPIDWindow.Label.text()))
        self.MFC1316.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.MFC1316.LOOPPIDWindow.Label.text(), 0))
        self.MFC1316.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.MFC1316.LOOPPIDWindow.Label.text(), 1))
        self.MFC1316.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.MFC1316.LOOPPIDWindow.Label.text(), 2))
        self.MFC1316.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.MFC1316.LOOPPIDWindow.Label.text(), 3))

        self.MFC1316.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.MFC1316.LOOPPIDWindow.Label.text(),
                                     self.MFC1316.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.MFC1316.LOOPPIDWindow.SP.Field.text()),
                                     float(self.MFC1316.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.MFC1316.LOOPPIDWindow.LOSP.Field.text())))



        self.HTR6225.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6225.LOOPPIDWindow.Label.text()))
        self.HTR6225.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6225.LOOPPIDWindow.Label.text()))
        self.HTR6225.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6225.LOOPPIDWindow.Label.text()))
        self.HTR6225.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6225.LOOPPIDWindow.Label.text()))
        self.HTR6225.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6225.LOOPPIDWindow.Label.text(), 0))
        self.HTR6225.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6225.LOOPPIDWindow.Label.text(), 1))
        self.HTR6225.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6225.LOOPPIDWindow.Label.text(), 2))
        self.HTR6225.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6225.LOOPPIDWindow.Label.text(), 3))

        self.HTR6225.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR6225.LOOPPIDWindow.Label.text(),
                                     self.HTR6225.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR6225.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR6225.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR6225.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR2123.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR2123.LOOPPIDWindow.Label.text()))
        self.HTR2123.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR2123.LOOPPIDWindow.Label.text()))
        self.HTR2123.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR2123.LOOPPIDWindow.Label.text()))
        self.HTR2123.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR2123.LOOPPIDWindow.Label.text()))
        self.HTR2123.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2123.LOOPPIDWindow.Label.text(), 0))
        self.HTR2123.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2123.LOOPPIDWindow.Label.text(), 1))
        self.HTR2123.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2123.LOOPPIDWindow.Label.text(), 2))
        self.HTR2123.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2123.LOOPPIDWindow.Label.text(), 3))

        self.HTR2123.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR2123.LOOPPIDWindow.Label.text(),
                                     self.HTR2123.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR2123.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR2123.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR2123.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR2124.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR2124.LOOPPIDWindow.Label.text()))
        self.HTR2124.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR2124.LOOPPIDWindow.Label.text()))
        self.HTR2124.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR2124.LOOPPIDWindow.Label.text()))
        self.HTR2124.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR2124.LOOPPIDWindow.Label.text()))
        self.HTR2124.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2124.LOOPPIDWindow.Label.text(), 0))
        self.HTR2124.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2124.LOOPPIDWindow.Label.text(), 1))
        self.HTR2124.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2124.LOOPPIDWindow.Label.text(), 2))
        self.HTR2124.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2124.LOOPPIDWindow.Label.text(), 3))

        self.HTR2124.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR2124.LOOPPIDWindow.Label.text(),
                                     self.HTR2124.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR2124.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR2124.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR2124.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR2125.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR2125.LOOPPIDWindow.Label.text()))
        self.HTR2125.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR2125.LOOPPIDWindow.Label.text()))
        self.HTR2125.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR2125.LOOPPIDWindow.Label.text()))
        self.HTR2125.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR2125.LOOPPIDWindow.Label.text()))
        self.HTR2125.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2125.LOOPPIDWindow.Label.text(), 0))
        self.HTR2125.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2125.LOOPPIDWindow.Label.text(), 1))
        self.HTR2125.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2125.LOOPPIDWindow.Label.text(), 2))
        self.HTR2125.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2125.LOOPPIDWindow.Label.text(), 3))

        self.HTR2125.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR2125.LOOPPIDWindow.Label.text(),
                                     self.HTR2125.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR2125.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR2125.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR2125.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR1202.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR1202.LOOPPIDWindow.Label.text()))
        self.HTR1202.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR1202.LOOPPIDWindow.Label.text()))
        self.HTR1202.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR1202.LOOPPIDWindow.Label.text()))
        self.HTR1202.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR1202.LOOPPIDWindow.Label.text()))
        self.HTR1202.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR1202.LOOPPIDWindow.Label.text(), 0))
        self.HTR1202.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR1202.LOOPPIDWindow.Label.text(), 1))
        self.HTR1202.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR1202.LOOPPIDWindow.Label.text(), 2))
        self.HTR1202.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR1202.LOOPPIDWindow.Label.text(), 3))

        self.HTR1202.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR1202.LOOPPIDWindow.Label.text(),
                                     self.HTR1202.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR1202.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR1202.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR1202.LOOPPIDWindow.LOSP.Field.text())))



        self.HTR2203.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR2203.LOOPPIDWindow.Label.text()))
        self.HTR2203.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR2203.LOOPPIDWindow.Label.text()))
        self.HTR2203.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR2203.LOOPPIDWindow.Label.text()))
        self.HTR2203.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR2203.LOOPPIDWindow.Label.text()))
        self.HTR2203.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2203.LOOPPIDWindow.Label.text(), 0))
        self.HTR2203.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2203.LOOPPIDWindow.Label.text(), 1))
        self.HTR2203.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2203.LOOPPIDWindow.Label.text(), 2))
        self.HTR2203.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR2203.LOOPPIDWindow.Label.text(), 3))

        self.HTR2203.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR2203.LOOPPIDWindow.Label.text(),
                                     self.HTR2203.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR2203.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR2203.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR2203.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR6202.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6202.LOOPPIDWindow.Label.text()))
        self.HTR6202.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6202.LOOPPIDWindow.Label.text()))
        self.HTR6202.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6202.LOOPPIDWindow.Label.text()))
        self.HTR6202.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6202.LOOPPIDWindow.Label.text()))
        self.HTR6202.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6202.LOOPPIDWindow.Label.text(), 0))
        self.HTR6202.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6202.LOOPPIDWindow.Label.text(), 1))
        self.HTR6202.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6202.LOOPPIDWindow.Label.text(), 2))
        self.HTR6202.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6202.LOOPPIDWindow.Label.text(), 3))

        self.HTR6202.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR6202.LOOPPIDWindow.Label.text(),
                                     self.HTR6202.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR6202.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR6202.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR6202.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR6206.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6206.LOOPPIDWindow.Label.text()))
        self.HTR6206.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6206.LOOPPIDWindow.Label.text()))
        self.HTR6206.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6206.LOOPPIDWindow.Label.text()))
        self.HTR6206.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6206.LOOPPIDWindow.Label.text()))
        self.HTR6206.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6206.LOOPPIDWindow.Label.text(), 0))
        self.HTR6206.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6206.LOOPPIDWindow.Label.text(), 1))
        self.HTR6206.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6206.LOOPPIDWindow.Label.text(), 2))
        self.HTR6206.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6206.LOOPPIDWindow.Label.text(), 3))

        self.HTR6206.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR6206.LOOPPIDWindow.Label.text(),
                                     self.HTR6206.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR6206.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR6206.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR6206.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR6210.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6210.LOOPPIDWindow.Label.text()))
        self.HTR6210.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6210.LOOPPIDWindow.Label.text()))
        self.HTR6210.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6210.LOOPPIDWindow.Label.text()))
        self.HTR6210.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6210.LOOPPIDWindow.Label.text()))
        self.HTR6210.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6210.LOOPPIDWindow.Label.text(), 0))
        self.HTR6210.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6210.LOOPPIDWindow.Label.text(), 1))
        self.HTR6210.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6210.LOOPPIDWindow.Label.text(), 2))
        self.HTR6210.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6210.LOOPPIDWindow.Label.text(), 3))

        self.HTR6210.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR6210.LOOPPIDWindow.Label.text(),
                                     self.HTR6210.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR6210.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR6210.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR6210.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR6223.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6223.LOOPPIDWindow.Label.text()))
        self.HTR6223.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6223.LOOPPIDWindow.Label.text()))
        self.HTR6223.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6223.LOOPPIDWindow.Label.text()))
        self.HTR6223.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6223.LOOPPIDWindow.Label.text()))
        self.HTR6223.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6223.LOOPPIDWindow.Label.text(), 0))
        self.HTR6223.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6223.LOOPPIDWindow.Label.text(), 1))
        self.HTR6223.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6223.LOOPPIDWindow.Label.text(), 2))
        self.HTR6223.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6223.LOOPPIDWindow.Label.text(), 3))

        self.HTR6223.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR6223.LOOPPIDWindow.Label.text(),
                                     self.HTR6223.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR6223.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR6223.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR6223.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR6224.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6224.LOOPPIDWindow.Label.text()))
        self.HTR6224.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6224.LOOPPIDWindow.Label.text()))
        self.HTR6224.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6224.LOOPPIDWindow.Label.text()))
        self.HTR6224.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6224.LOOPPIDWindow.Label.text()))
        self.HTR6224.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6224.LOOPPIDWindow.Label.text(), 0))
        self.HTR6224.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6224.LOOPPIDWindow.Label.text(), 1))
        self.HTR6224.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6224.LOOPPIDWindow.Label.text(), 2))
        self.HTR6224.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6224.LOOPPIDWindow.Label.text(), 3))

        self.HTR6224.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR6224.LOOPPIDWindow.Label.text(),
                                     self.HTR6224.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR6224.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR6224.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR6224.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR6219.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6219.LOOPPIDWindow.Label.text()))
        self.HTR6219.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6219.LOOPPIDWindow.Label.text()))
        self.HTR6219.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6219.LOOPPIDWindow.Label.text()))
        self.HTR6219.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6219.LOOPPIDWindow.Label.text()))
        self.HTR6219.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6219.LOOPPIDWindow.Label.text(), 0))
        self.HTR6219.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6219.LOOPPIDWindow.Label.text(), 1))
        self.HTR6219.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6219.LOOPPIDWindow.Label.text(), 2))
        self.HTR6219.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6219.LOOPPIDWindow.Label.text(), 3))

        self.HTR6219.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR6219.LOOPPIDWindow.Label.text(),
                                     self.HTR6219.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR6219.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR6219.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR6219.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR6221.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6221.LOOPPIDWindow.Label.text()))
        self.HTR6221.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6221.LOOPPIDWindow.Label.text()))
        self.HTR6221.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6221.LOOPPIDWindow.Label.text()))
        self.HTR6221.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6221.LOOPPIDWindow.Label.text()))
        self.HTR6221.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6221.LOOPPIDWindow.Label.text(), 0))
        self.HTR6221.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6221.LOOPPIDWindow.Label.text(), 1))
        self.HTR6221.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6221.LOOPPIDWindow.Label.text(), 2))
        self.HTR6221.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6221.LOOPPIDWindow.Label.text(), 3))

        self.HTR6221.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR6221.LOOPPIDWindow.Label.text(),
                                     self.HTR6221.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR6221.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR6221.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR6221.LOOPPIDWindow.LOSP.Field.text())))


        self.HTR6214.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6214.LOOPPIDWindow.Label.text()))
        self.HTR6214.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6214.LOOPPIDWindow.Label.text()))
        self.HTR6214.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6214.LOOPPIDWindow.Label.text()))
        self.HTR6214.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6214.LOOPPIDWindow.Label.text()))
        self.HTR6214.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6214.LOOPPIDWindow.Label.text(), 0))
        self.HTR6214.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6214.LOOPPIDWindow.Label.text(), 1))
        self.HTR6214.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6214.LOOPPIDWindow.Label.text(), 2))
        self.HTR6214.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6214.LOOPPIDWindow.Label.text(), 3))

        self.HTR6214.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR6214.LOOPPIDWindow.Label.text(),
                                     self.HTR6214.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR6214.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR6214.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR6214.LOOPPIDWindow.LOSP.Field.text())))




        #LOOP2PT


        self.PUMP3305.LOOP2PTWindow.Mode.LButton.clicked.connect(
            lambda x: self.LOOP2PTLButtonClicked(self.PUMP3305.LOOP2PTWindow.Label.text()))
        self.PUMP3305.LOOP2PTWindow.Mode.RButton.clicked.connect(
            lambda x: self.LOOP2PTRButtonClicked(self.PUMP3305.LOOP2PTWindow.Label.text()))
        self.PUMP3305.State.LButton.clicked.connect(
            lambda x: self.LOOP2PTLButtonClicked(self.PUMP3305.LOOP2PTWindow.Label.text()))
        self.PUMP3305.State.RButton.clicked.connect(
            lambda x: self.LOOP2PTRButtonClicked(self.PUMP3305.LOOP2PTWindow.Label.text()))

        self.PUMP3305.LOOP2PTWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.LOOP2PTGroupButtonClicked(self.PUMP3305.LOOP2PTWindow.Label.text(), 0))
        self.PUMP3305.LOOP2PTWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.LOOP2PTGroupButtonClicked(self.PUMP3305.LOOP2PTWindow.Label.text(), 1))
        self.PUMP3305.LOOP2PTWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.LOOP2PTGroupButtonClicked(self.PUMP3305.LOOP2PTWindow.Label.text(), 2))
        self.PUMP3305.LOOP2PTWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.LOOP2PTGroupButtonClicked(self.PUMP3305.LOOP2PTWindow.Label.text(), 3))

        self.PUMP3305.LOOP2PTWindow.updatebutton.clicked.connect(
            lambda x: self.LOOP2PTupdate(self.PUMP3305.LOOP2PTWindow.Label.text(),
                                         self.PUMP3305.LOOP2PTWindow.ModeREAD.Field.text(),
                                         float(self.PUMP3305.LOOP2PTWindow.SP.Field.text())))

        # Beckoff RTDs

        self.AlarmButton.SubWindow.TT2101.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2101.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2101.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2101.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2101.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2101.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2101.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2101.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2101.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2101.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2111.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2111.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2111.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2111.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2111.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2111.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2111.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2111.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2111.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2111.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2113.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2113.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2113.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2113.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2113.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2113.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2113.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2113.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2113.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2113.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2118.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2118.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2118.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2118.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2118.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2118.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2118.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2118.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2118.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2118.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2119.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2119.Label.text(),Act=self.AlarmButton.SubWindow.TT2119.AlarmMode.isChecked(),
                                         LowLimit=self.AlarmButton.SubWindow.TT2119.Low_Set.Field.text(), HighLimit=self.AlarmButton.SubWindow.TT2119.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2119.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2119.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2119.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2119.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2119.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT4330.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT4330.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT4330.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT4330.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT4330.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT4330.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT4330.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT4330.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT4330.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT4330.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6203.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6203.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6203.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6203.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6203.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6203.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6203.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6203.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6203.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6203.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6207.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6207.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6207.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6207.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6207.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6207.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6207.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6207.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6207.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6207.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6211.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6211.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6211.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6211.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6211.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6211.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6211.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6211.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6211.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6211.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6213.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6213.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6213.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6213.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6213.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6213.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6213.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6213.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6213.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6213.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6222.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6222.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6222.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6222.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6222.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6222.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6222.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6222.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6222.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6222.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6407.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6407.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6407.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6407.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6407.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6407.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6407.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6407.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6407.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6407.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6408.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6408.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6408.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6408.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6408.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6408.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6408.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6408.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6408.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6408.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6409.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6409.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6409.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6409.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6409.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6409.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6409.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6409.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6409.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6409.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6415.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6415.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6415.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6415.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6415.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6415.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6415.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6415.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6415.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6415.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6416.AlarmMode.stateChanged.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6416.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6416.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6416.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6416.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6416.updatebutton.clicked.connect(
            lambda: self.BOTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6416.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6416.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6416.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6416.High_Set.Field.text()))

        # Field Point RTDs
        self.AlarmButton.SubWindow.TT2420.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2420.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2420.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2420.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2420.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2422.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2422.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2422.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2422.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2422.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2424.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2424.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2424.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2424.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2424.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2425.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2425.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2425.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2425.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2425.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2442.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2442.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2442.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2442.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2442.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2403.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2403.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2403.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2403.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2403.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2418.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2418.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2418.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2418.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2418.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2427.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2427.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2427.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2427.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2427.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2429.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2429.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2429.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2429.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2429.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2431.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2431.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2431.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2431.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2431.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2441.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2441.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2441.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2441.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2441.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2414.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2414.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2414.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2414.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2414.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2413.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2413.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2413.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2413.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2413.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2412.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2412.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2412.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2412.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2412.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2415.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2415.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2415.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2415.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2415.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2409.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2409.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2409.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2409.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2409.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2436.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2436.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2436.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2436.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2436.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2438.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2438.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2438.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2438.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2438.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2440.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2440.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2440.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2440.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2440.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2402.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2402.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2402.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2402.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2402.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2411.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2411.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2411.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2411.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2411.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2443.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2443.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2443.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2443.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2443.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2417.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2417.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2417.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2417.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2417.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2404.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2404.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2404.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2404.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2404.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2408.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2408.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2408.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2408.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2408.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2407.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2407.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2407.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2407.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2407.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2406.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2406.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2406.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2406.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2406.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2428.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2428.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2428.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2428.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2428.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2432.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2432.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2432.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2432.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2432.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2421.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2421.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2421.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2421.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2421.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2416.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2416.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2416.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2416.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2416.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2439.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2439.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2439.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2439.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2439.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2419.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2419.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2419.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2419.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2419.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2423.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2423.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2423.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2423.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2423.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2426.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2426.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2426.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2426.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2426.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2430.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2430.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2430.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2430.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2430.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2450.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2450.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2450.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2450.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2450.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2401.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2401.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2401.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2449.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2449.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2449.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2449.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2449.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2445.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2445.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2445.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2445.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2445.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2444.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2444.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2444.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2444.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2444.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2435.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2435.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2435.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2435.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2435.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2437.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2437.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2437.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2437.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2437.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2446.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2446.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2446.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2446.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2446.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2447.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2447.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2447.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2447.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2447.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2448.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2448.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2448.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2448.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2448.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2410.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2410.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2410.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2410.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2410.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT2405.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2405.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2405.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2405.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2405.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6220.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6220.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6220.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6220.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6401.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6401.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6401.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6404.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6404.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6404.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6404.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6404.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6405.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6405.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6405.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6405.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6405.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6406.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6406.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6406.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6406.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6406.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6410.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6410.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6410.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6410.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6410.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6411.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6411.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6411.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6411.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6411.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6412.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6412.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6412.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6412.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6412.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6413.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6413.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6413.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6413.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6413.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.TT6414.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6414.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6414.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6414.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6414.High_Set.Field.text(),update = False))


        #FP rtd updatebutton

        self.AlarmButton.SubWindow.TT7401.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT7401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT7401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT7401.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT7401.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.TT7402.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT7402.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT7402.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT7402.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT7402.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.TT7403.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT7403.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT7403.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT7403.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT7403.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.TT7404.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT7404.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT7404.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT7404.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT7404.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.TT3401.AlarmMode.stateChanged.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT3401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT3401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT3401.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT3401.High_Set.Field.text(), update=False))
        self.AlarmButton.SubWindow.TT2420.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2420.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2420.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2420.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2420.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2422.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2422.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2422.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2422.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2422.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2424.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2424.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2424.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2424.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2424.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2425.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2425.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2425.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2425.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2425.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2442.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2442.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2442.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2442.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2442.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2403.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2403.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2403.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2403.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2403.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2418.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2418.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2418.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2418.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2418.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2427.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2427.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2427.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2427.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2427.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2429.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2429.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2429.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2429.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2429.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2431.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2431.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2431.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2431.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2431.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2441.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2441.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2441.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2441.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2441.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2414.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2414.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2414.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2414.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2414.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2413.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2413.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2413.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2413.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2413.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2412.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2412.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2412.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2412.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2412.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2415.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2415.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2415.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2415.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2415.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2409.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2409.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2409.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2409.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2409.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2436.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2436.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2436.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2436.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2436.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2438.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2438.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2438.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2438.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2438.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2440.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2440.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2440.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2440.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2440.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2402.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2402.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2402.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2402.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2402.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2411.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2411.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2411.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2411.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2411.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2443.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2443.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2443.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2443.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2443.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2417.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2417.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2417.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2417.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2417.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2404.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2404.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2404.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2404.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2404.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2408.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2408.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2408.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2408.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2408.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2407.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2407.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2407.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2407.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2407.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2406.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2406.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2406.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2406.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2406.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2428.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2428.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2428.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2428.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2428.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2432.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2432.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2432.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2432.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2432.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2421.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2421.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2421.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2421.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2421.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2416.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2416.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2416.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2416.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2416.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2439.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2439.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2439.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2439.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2439.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2419.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2419.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2419.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2419.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2419.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2423.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2423.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2423.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2423.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2423.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2426.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2426.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2426.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2426.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2426.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2430.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2430.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2430.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2430.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2430.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2450.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2450.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2450.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2450.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2450.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2401.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2401.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2401.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2449.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2449.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2449.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2449.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2449.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2445.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2445.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2445.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2445.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2445.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2444.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2444.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2444.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2444.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2444.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2435.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2435.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2435.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2435.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2435.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2437.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2437.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2437.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2437.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2437.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2446.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2446.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2446.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2446.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2446.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2447.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2447.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2447.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2447.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2447.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2448.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2448.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2448.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2448.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2448.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2410.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2410.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2410.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2410.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2410.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT2405.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT2405.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT2405.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT2405.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT2405.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6220.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6220.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6220.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6220.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6401.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6401.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6401.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6404.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6404.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6404.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6404.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6404.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6405.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6405.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6405.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6405.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6405.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6406.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6406.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6406.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6406.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6406.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6410.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6410.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6410.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6410.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6410.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6411.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6411.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6411.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6411.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6411.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6412.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6412.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6412.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6412.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6412.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6413.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6413.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6413.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6413.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6413.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT6414.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT6414.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT6414.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT6414.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT6414.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT7401.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT7401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT7401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT7401.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT7401.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT7402.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT7402.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT7402.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT7402.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT7402.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT7403.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT7403.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT7403.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT7403.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT7403.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT7404.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT7404.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT7404.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT7404.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT7404.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TT3401.updatebutton.clicked.connect(
            lambda: self.FPTTBoxUpdate(pid=self.AlarmButton.SubWindow.TT3401.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TT3401.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TT3401.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TT3401.High_Set.Field.text()))


        #BO PT updatebutton and activate button

        self.AlarmButton.SubWindow.PT1361.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT1361.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT1361.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT1361.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT1361.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PT1361.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT1361.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT1361.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT1361.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT1361.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT2316.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT2316.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT2316.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT2316.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT2316.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT2316.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT2316.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT2316.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT2316.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT2316.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT2330.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT2330.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT2330.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT2330.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT2330.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT2330.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT2330.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT2330.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT2330.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT2330.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT2335.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT2335.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT2335.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT2335.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT2335.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT2335.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT2335.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT2335.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT2335.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT2335.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT3308.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3308.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3308.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3308.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3308.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT3308.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3308.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3308.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3308.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3308.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT3309.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3309.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3309.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3309.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3309.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT3309.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3309.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3309.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3309.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3309.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT3311.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3311.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3311.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3311.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3311.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT3311.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3311.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3311.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3311.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3311.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT3314.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3314.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3314.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3314.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3314.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT3314.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3314.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3314.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3314.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3314.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT3320.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3320.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3320.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3320.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3320.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT3320.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3320.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3320.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3320.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3320.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT3332.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3332.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT3332.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT3332.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT3332.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PT3332.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3332.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT3332.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT3332.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT3332.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT3333.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3333.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3333.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3333.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3333.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT3333.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT3333.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT3333.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT3333.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT3333.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT4306.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT4306.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT4306.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT4306.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT4306.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT4306.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT4306.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT4306.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT4306.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT4306.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT4315.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT4315.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT4315.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT4315.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT4315.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT4315.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT4315.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT4315.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT4315.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT4315.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT4319.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT4319.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT4319.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT4319.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT4319.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT4319.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT4319.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT4319.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT4319.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT4319.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT4322.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT4322.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT4322.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT4322.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT4322.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT4322.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT4322.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT4322.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT4322.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT4322.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT4325.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT4325.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT4325.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT4325.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT4325.High_Set.Field.text(),update = False))

        self.AlarmButton.SubWindow.PT4325.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT4325.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PT4325.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PT4325.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PT4325.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT6302.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT6302.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT6302.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT6302.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT6302.High_Set.Field.text(), update=False))


        self.AlarmButton.SubWindow.PT6302.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT6302.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT6302.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT6302.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT6302.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT6306.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT6306.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT6306.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT6306.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT6306.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PT6306.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT6306.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT6306.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT6306.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT6306.High_Set.Field.text()))

        #
        self.AlarmButton.SubWindow.PT1101_AVG.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT1101_AVG.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT1101_AVG.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT1101_AVG.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT1101_AVG.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PT1101_AVG.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT1101_AVG.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT1101_AVG.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT1101_AVG.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT1101_AVG.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT2121_AVG.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT2121_AVG.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT2121_AVG.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT2121_AVG.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT2121_AVG.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PT2121_AVG.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT2121_AVG.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT2121_AVG.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT2121_AVG.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT2121_AVG.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PDIFF_PT2121PT1101.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid="PDIFF_PT2121PT1101",
                                     Act=self.AlarmButton.SubWindow.PDIFF_PT2121PT1101.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PDIFF_PT2121PT1101.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PDIFF_PT2121PT1101.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PDIFF_PT2121PT1101.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid="PDIFF_PT2121PT1101",
                                     Act=self.AlarmButton.SubWindow.PDIFF_PT2121PT1101.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PDIFF_PT2121PT1101.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PDIFF_PT2121PT1101.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PDIFF_PT2121PT1325.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid="PDIFF_PT2121PT1325",
                                     Act=self.AlarmButton.SubWindow.PDIFF_PT2121PT1325.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PDIFF_PT2121PT1325.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PDIFF_PT2121PT1325.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PDIFF_PT2121PT1325.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid="PDIFF_PT2121PT1325",
                                     Act=self.AlarmButton.SubWindow.PDIFF_PT2121PT1325.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PDIFF_PT2121PT1325.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PDIFF_PT2121PT1325.High_Set.Field.text()))

        self.AlarmButton.SubWindow.CYL3334_LT3335_CF4PRESSCALC.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid="CYL3334_LT3335_CF4PRESSCALC",
                                     Act=self.AlarmButton.SubWindow.CYL3334_LT3335_CF4PRESSCALC.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.CYL3334_LT3335_CF4PRESSCALC.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.CYL3334_LT3335_CF4PRESSCALC.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.CYL3334_LT3335_CF4PRESSCALC.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate("CYL3334_LT3335_CF4PRESSCALC",
                                     Act=self.AlarmButton.SubWindow.CYL3334_LT3335_CF4PRESSCALC.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.CYL3334_LT3335_CF4PRESSCALC.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.CYL3334_LT3335_CF4PRESSCALC.High_Set.Field.text()))
        #

        self.AlarmButton.SubWindow.PT1101.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT1101.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT1101.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT1101.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT1101.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PT1101.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT1101.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT1101.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT1101.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT1101.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT1325.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT1325.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT1325.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT1325.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT1325.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PT1325.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT1325.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT1325.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT1325.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT1325.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT5304.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT5304.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT5304.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT5304.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT5304.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PT5304.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT5304.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT5304.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT5304.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT5304.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PT2121.AlarmMode.stateChanged.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT2121.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT2121.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT2121.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT2121.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.PT2121.updatebutton.clicked.connect(
            lambda: self.PTBoxUpdate(pid=self.AlarmButton.SubWindow.PT2121.Label.text(),
                                     Act=self.AlarmButton.SubWindow.PT2121.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.PT2121.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.PT2121.High_Set.Field.text()))


        #LEFT Variables
        self.AlarmButton.SubWindow.LT3335.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.LT3335.Label.text(),
                                     Act=self.AlarmButton.SubWindow.LT3335.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.LT3335.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.LT3335.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.LT3335.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.LT3335.Label.text(),
                                     Act=self.AlarmButton.SubWindow.LT3335.AlarmMode.isChecked(),
                                     LowLimit=self.AlarmButton.SubWindow.LT3335.Low_Set.Field.text(),
                                     HighLimit=self.AlarmButton.SubWindow.LT3335.High_Set.Field.text()))

        self.AlarmButton.SubWindow.BFM4313.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.BFM4313.Label.text(),
                                       Act=self.AlarmButton.SubWindow.BFM4313.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.BFM4313.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.BFM4313.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.BFM4313.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.BFM4313.Label.text(),
                                       Act=self.AlarmButton.SubWindow.BFM4313.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.BFM4313.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.BFM4313.High_Set.Field.text()))

        self.AlarmButton.SubWindow.MFC1316_IN.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.MFC1316_IN.Label.text(),
                                       Act=self.AlarmButton.SubWindow.MFC1316_IN.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.MFC1316_IN.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.MFC1316_IN.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.MFC1316_IN.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.MFC1316_IN.Label.text(),
                                       Act=self.AlarmButton.SubWindow.MFC1316_IN.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.MFC1316_IN.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.MFC1316_IN.High_Set.Field.text()))

        self.AlarmButton.SubWindow.CYL3334_FCALC.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.CYL3334_FCALC.Label.text(),
                                       Act=self.AlarmButton.SubWindow.CYL3334_FCALC.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.CYL3334_FCALC.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.CYL3334_FCALC.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.CYL3334_FCALC.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.CYL3334_FCALC.Label.text(),
                                       Act=self.AlarmButton.SubWindow.CYL3334_FCALC.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.CYL3334_FCALC.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.CYL3334_FCALC.High_Set.Field.text()))

        self.AlarmButton.SubWindow.SERVO3321_IN_REAL.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.SERVO3321_IN_REAL.Label.text(),
                                       Act=self.AlarmButton.SubWindow.SERVO3321_IN_REAL.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.SERVO3321_IN_REAL.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.SERVO3321_IN_REAL.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.SERVO3321_IN_REAL.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.SERVO3321_IN_REAL.Label.text(),
                                       Act=self.AlarmButton.SubWindow.SERVO3321_IN_REAL.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.SERVO3321_IN_REAL.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.SERVO3321_IN_REAL.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TS1_MASS.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.TS1_MASS.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TS1_MASS.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TS1_MASS.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TS1_MASS.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.TS1_MASS.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.TS1_MASS.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TS1_MASS.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TS1_MASS.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TS1_MASS.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TS2_MASS.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.TS2_MASS.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TS2_MASS.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TS2_MASS.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TS2_MASS.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.TS2_MASS.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.TS2_MASS.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TS2_MASS.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TS2_MASS.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TS2_MASS.High_Set.Field.text()))

        self.AlarmButton.SubWindow.TS3_MASS.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.TS3_MASS.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TS3_MASS.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TS3_MASS.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TS3_MASS.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.TS3_MASS.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.TS3_MASS.Label.text(),
                                       Act=self.AlarmButton.SubWindow.TS3_MASS.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.TS3_MASS.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.TS3_MASS.High_Set.Field.text()))

       #
        self.AlarmButton.SubWindow.PV1201_STATE.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.PV1201_STATE.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PV1201_STATE.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PV1201_STATE.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PV1201_STATE.High_Set.Field.text(),
                                       update=False))

        self.AlarmButton.SubWindow.PV1201_STATE.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.PV1201_STATE.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PV1201_STATE.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PV1201_STATE.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PV1201_STATE.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PV2201_STATE.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.PV2201_STATE.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PV2201_STATE.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PV2201_STATE.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PV2201_STATE.High_Set.Field.text(),
                                       update=False))

        self.AlarmButton.SubWindow.PV2201_STATE.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.PV2201_STATE.Label.text(),
                                       Act=self.AlarmButton.SubWindow.PV2201_STATE.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.PV2201_STATE.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.PV2201_STATE.High_Set.Field.text()))
        #

        self.AlarmButton.SubWindow.LED1_OUT.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.LED1_OUT.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LED1_OUT.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LED1_OUT.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LED1_OUT.High_Set.Field.text(),
                                       update=False))

        self.AlarmButton.SubWindow.LED1_OUT.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.LED1_OUT.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LED1_OUT.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LED1_OUT.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LED1_OUT.High_Set.Field.text()))

        self.AlarmButton.SubWindow.LED2_OUT.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.LED2_OUT.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LED2_OUT.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LED2_OUT.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LED2_OUT.High_Set.Field.text(),
                                       update=False))

        self.AlarmButton.SubWindow.LED2_OUT.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.LED2_OUT.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LED2_OUT.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LED2_OUT.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LED2_OUT.High_Set.Field.text()))

        self.AlarmButton.SubWindow.LED3_OUT.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.LED3_OUT.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LED3_OUT.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LED3_OUT.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LED3_OUT.High_Set.Field.text(),
                                       update=False))

        self.AlarmButton.SubWindow.LED3_OUT.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.LED3_OUT.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LED3_OUT.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LED3_OUT.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LED3_OUT.High_Set.Field.text()))

        self.AlarmButton.SubWindow.LED_MAX.AlarmMode.stateChanged.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.LED_MAX.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LED_MAX.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LED_MAX.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LED_MAX.High_Set.Field.text(),
                                       update=False))

        self.AlarmButton.SubWindow.LED_MAX.updatebutton.clicked.connect(
            lambda: self.LEFTBoxUpdate(pid=self.AlarmButton.SubWindow.LED_MAX.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LED_MAX.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LED_MAX.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LED_MAX.High_Set.Field.text()))




        # AD box
        self.AlarmButton.SubWindow.LT2122.AlarmMode.stateChanged.connect(
            lambda: self.ADBoxUpdate(pid=self.AlarmButton.SubWindow.LT2122.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LT2122.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LT2122.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LT2122.High_Set.Field.text(),
                                       update=False))

        self.AlarmButton.SubWindow.LT2122.updatebutton.clicked.connect(
            lambda: self.ADBoxUpdate(pid=self.AlarmButton.SubWindow.LT2122.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LT2122.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LT2122.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LT2122.High_Set.Field.text()))

        self.AlarmButton.SubWindow.LT2130.AlarmMode.stateChanged.connect(
            lambda: self.ADBoxUpdate(pid=self.AlarmButton.SubWindow.LT2130.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LT2130.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LT2130.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LT2130.High_Set.Field.text(),
                                       update=False))

        self.AlarmButton.SubWindow.LT2130.updatebutton.clicked.connect(
            lambda: self.ADBoxUpdate(pid=self.AlarmButton.SubWindow.LT2130.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LT2130.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LT2130.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LT2130.High_Set.Field.text()))

        # Din buttons
        self.AlarmButton.SubWindow.LS3338.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS3338.Label.text(),
                                       Act=self.AlarmButton.SubWindow.LS3338.AlarmMode.isChecked(),
                                       LowLimit=self.AlarmButton.SubWindow.LS3338.Low_Set.Field.text(),
                                       HighLimit=self.AlarmButton.SubWindow.LS3338.High_Set.Field.text()))

        self.AlarmButton.SubWindow.LS3339.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS3339.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS3339.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS3339.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS3339.High_Set.Field.text()))

        self.AlarmButton.SubWindow.ES3347.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.ES3347.Label.text(),
                                      Act=self.AlarmButton.SubWindow.ES3347.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.ES3347.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.ES3347.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PUMP3305_CON.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PUMP3305_CON.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PUMP3305_CON.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PUMP3305_CON.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PUMP3305_CON.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PUMP3305_OL.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PUMP3305_OL.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PUMP3305_OL.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PUMP3305_OL.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PUMP3305_OL.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PS2352.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PS2352.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PS2352.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PS2352.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PS2352.High_Set.Field.text()))


        self.AlarmButton.SubWindow.PS8302.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PS8302.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PS8302.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PS8302.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PS8302.High_Set.Field.text()))
        # self.AlarmButton.SubWindow.UPS_ON_BATT.updatebutton.clicked.connect(
        #     lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.UPS_ON_BATT.Label.text(),
        #                               Act=self.AlarmButton.SubWindow.UPS_ON_BATT.AlarmMode.isChecked(),
        #                               LowLimit=self.AlarmButton.SubWindow.UPS_ON_BATT.Low_Set.Field.text(),
        #                               HighLimit=self.AlarmButton.SubWindow.UPS_ON_BATT.High_Set.Field.text()))
        # self.AlarmButton.SubWindow.UPS_LOW_BATT.updatebutton.clicked.connect(
        #     lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.UPS_LOW_BATT.Label.text(),
        #                               Act=self.AlarmButton.SubWindow.UPS_LOW_BATT.AlarmMode.isChecked(),
        #                               LowLimit=self.AlarmButton.SubWindow.UPS_LOW_BATT.Low_Set.Field.text(),
        #                               HighLimit=self.AlarmButton.SubWindow.UPS_LOW_BATT.High_Set.Field.text()))

        self.AlarmButton.SubWindow.LS2126.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS2126.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS2126.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS2126.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS2126.High_Set.Field.text()))

        self.AlarmButton.SubWindow.LS2127.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS2127.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS2127.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS2127.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS2127.High_Set.Field.text()))

        self.AlarmButton.SubWindow.LS2128.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS2128.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS2128.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS2128.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS2128.High_Set.Field.text()))

        self.AlarmButton.SubWindow.LS2129.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS2129.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS2129.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS2129.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS2129.High_Set.Field.text()))

        self.AlarmButton.SubWindow.CC9313_POWER.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.CC9313_POWER.Label.text(),
                                      Act=self.AlarmButton.SubWindow.CC9313_POWER.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.CC9313_POWER.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.CC9313_POWER.High_Set.Field.text()))

        self.AlarmButton.SubWindow.UPS_UTILITY_OK.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid='UPS_UTI_OK',
                                      Act=self.AlarmButton.SubWindow.UPS_UTILITY_OK.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.UPS_UTILITY_OK.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.UPS_UTILITY_OK.High_Set.Field.text()))

        self.AlarmButton.SubWindow.UPS_BATTERY_OK.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid='UPS_BAT_OK',
                                      Act=self.AlarmButton.SubWindow.UPS_BATTERY_OK.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.UPS_BATTERY_OK.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.UPS_BATTERY_OK.High_Set.Field.text()))


        # checkbox
        self.AlarmButton.SubWindow.LS3338.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS3338.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS3338.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS3338.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS3338.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.LS3339.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS3339.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS3339.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS3339.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS3339.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.ES3347.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.ES3347.Label.text(),
                                      Act=self.AlarmButton.SubWindow.ES3347.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.ES3347.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.ES3347.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.PUMP3305_CON.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PUMP3305_CON.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PUMP3305_CON.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PUMP3305_CON.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PUMP3305_CON.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.PUMP3305_OL.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PUMP3305_OL.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PUMP3305_OL.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PUMP3305_OL.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PUMP3305_OL.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.PS2352.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PS2352.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PS2352.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PS2352.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PS2352.High_Set.Field.text(), update= False))


        self.AlarmButton.SubWindow.PS8302.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PS8302.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PS8302.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PS8302.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PS8302.High_Set.Field.text(), update= False))

        # self.AlarmButton.SubWindow.UPS_ON_BATT.AlarmMode.stateChanged.connect(
        #     lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.UPS_ON_BATT.Label.text(),
        #                               Act=self.AlarmButton.SubWindow.UPS_ON_BATT.AlarmMode.isChecked(),
        #                               LowLimit=self.AlarmButton.SubWindow.UPS_ON_BATT.Low_Set.Field.text(),
        #                               HighLimit=self.AlarmButton.SubWindow.UPS_ON_BATT.High_Set.Field.text(), update=False))
        #
        # self.AlarmButton.SubWindow.UPS_LOW_BATT.AlarmMode.stateChanged.connect(
        #     lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.UPS_LOW_BATT.Label.text(),
        #                               Act=self.AlarmButton.SubWindow.UPS_LOW_BATT.AlarmMode.isChecked(),
        #                               LowLimit=self.AlarmButton.SubWindow.UPS_LOW_BATT.Low_Set.Field.text(),
        #                               HighLimit=self.AlarmButton.SubWindow.UPS_LOW_BATT.High_Set.Field.text(), update=False))

        self.AlarmButton.SubWindow.LS2126.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS2126.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS2126.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS2126.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS2126.High_Set.Field.text(),
                                      update=False))

        self.AlarmButton.SubWindow.LS2127.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS2127.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS2127.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS2127.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS2127.High_Set.Field.text(),
                                      update=False))

        self.AlarmButton.SubWindow.LS2128.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS2128.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS2128.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS2128.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS2128.High_Set.Field.text(),
                                      update=False))

        self.AlarmButton.SubWindow.LS2129.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.LS2129.Label.text(),
                                      Act=self.AlarmButton.SubWindow.LS2129.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.LS2129.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.LS2129.High_Set.Field.text(),
                                      update=False))

        self.AlarmButton.SubWindow.CC9313_POWER.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.CC9313_POWER.Label.text(),
                                      Act=self.AlarmButton.SubWindow.CC9313_POWER.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.CC9313_POWER.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.CC9313_POWER.High_Set.Field.text(),
                                      update=False))

        self.AlarmButton.SubWindow.UPS_UTILITY_OK.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid='UPS_UTI_OK',
                                      Act=self.AlarmButton.SubWindow.UPS_UTILITY_OK.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.UPS_UTILITY_OK.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.UPS_UTILITY_OK.High_Set.Field.text(),
                                      update=False))

        self.AlarmButton.SubWindow.UPS_BATTERY_OK.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid='UPS_BAT_OK',
                                      Act=self.AlarmButton.SubWindow.UPS_BATTERY_OK.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.UPS_BATTERY_OK.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.UPS_BATTERY_OK.High_Set.Field.text(),
                                      update=False))

        #LOOPPID updatebutton
        self.AlarmButton.SubWindow.SERVO3321.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.SERVO3321.Label.text(),
                                      Act=self.AlarmButton.SubWindow.SERVO3321.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.SERVO3321.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.SERVO3321.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR6225.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6225.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6225.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6225.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6225.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR2123.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR2123.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR2123.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR2123.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR2123.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR2124.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR2124.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR2124.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR2124.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR2124.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR2125.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR2125.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR2125.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR2125.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR2125.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR1202.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR1202.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR1202.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR1202.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR1202.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR2203.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR2203.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR2203.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR2203.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR2203.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR6202.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6202.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6202.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6202.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6202.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR6206.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6206.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6206.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6206.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6206.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR6210.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6210.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6210.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6210.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6210.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR6223.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6223.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6223.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6223.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6223.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR6224.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6224.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6224.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6224.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6224.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR6219.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6219.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6219.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6219.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6219.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR6221.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6221.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6221.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6221.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6221.High_Set.Field.text()))

        self.AlarmButton.SubWindow.HTR6214.updatebutton.clicked.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6214.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6214.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6214.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6214.High_Set.Field.text()))

        #LOOPPID checkbox
        self.AlarmButton.SubWindow.SERVO3321.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.SERVO3321.Label.text(),
                                          Act=self.AlarmButton.SubWindow.SERVO3321.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.SERVO3321.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.SERVO3321.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR6225.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6225.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6225.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6225.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6225.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR2123.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR2123.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR2123.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR2123.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR2123.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR2124.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR2124.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR2124.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR2124.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR2124.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR2125.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR2125.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR2125.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR2125.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR2125.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR1202.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR1202.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR1202.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR1202.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR1202.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR2203.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR2203.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR2203.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR2203.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR2203.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR6202.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6202.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6202.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6202.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6202.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR6206.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6206.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6206.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6206.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6206.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR6210.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6210.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6210.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6210.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6210.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR6223.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6223.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6223.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6223.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6223.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR6224.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6224.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6224.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6224.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6224.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR6219.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6219.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6219.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6219.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6219.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR6221.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6221.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6221.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6221.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6221.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.HTR6214.AlarmMode.stateChanged.connect(
            lambda: self.LOOPPIDBoxUpdate(pid=self.AlarmButton.SubWindow.HTR6214.Label.text(),
                                          Act=self.AlarmButton.SubWindow.HTR6214.AlarmMode.isChecked(),
                                          LowLimit=self.AlarmButton.SubWindow.HTR6214.Low_Set.Field.text(),
                                          HighLimit=self.AlarmButton.SubWindow.HTR6214.High_Set.Field.text(), update= False))


        ##intlck A window
        self.INTLCKWindow.TT2118_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT2118_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT2118_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT2118_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT2118_HI_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_A_RESET(self.INTLCKWindow.TT2118_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT2118_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT2118_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT2118_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT2118_LO_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT2118_LO_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT2118_LO_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT2118_LO_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT2118_LO_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT2118_LO_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT2118_LO_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.PT4306_LO_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT4306_LO_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4306_LO_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT4306_LO_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4306_LO_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT4306_LO_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT4306_LO_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.PT5304_LO_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT5304_LO_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT5304_LO_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT5304_LO_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT5304_LO_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT5304_LO_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT5304_LO_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.PT4306_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT4306_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4306_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT4306_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4306_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT4306_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT4306_HI_INTLK.SET_W.Field.text()))


        #
        self.INTLCKWindow.PT6302_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT6302_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT6302_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT6302_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT6302_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT6302_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT6302_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.PT6306_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT6306_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT6306_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT6306_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT6306_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT6306_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT6306_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.PT2121_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT2121_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT2121_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT2121_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT2121_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT2121_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT2121_HI_INTLK.SET_W.Field.text()))
        #
        self.INTLCKWindow.PT4322_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT4322_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4322_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT4322_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4322_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT4322_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT4322_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.PT4322_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT4322_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4322_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT4322_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4322_HIHI_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_A_RESET(self.INTLCKWindow.PT4322_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4322_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT4322_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT4322_HIHI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.PT4319_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT4319_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4319_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT4319_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4319_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT4319_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT4319_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.PT4319_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT4319_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4319_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT4319_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4319_HIHI_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_A_RESET(self.INTLCKWindow.PT4319_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4319_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT4319_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT4319_HIHI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.PT4325_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT4325_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4325_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT4325_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4325_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT4325_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT4325_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.PT4325_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT4325_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4325_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT4325_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4325_HIHI_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_A_RESET(self.INTLCKWindow.PT4325_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4325_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT4325_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT4325_HIHI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6203_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6203_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6203_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6203_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6203_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6203_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6203_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6207_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6207_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6207_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6207_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6207_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6207_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6207_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6211_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6211_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6211_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6211_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6211_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6211_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6211_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6213_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6213_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6213_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6213_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6213_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6213_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6213_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6222_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6222_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6222_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6222_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6222_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6222_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6222_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6407_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6407_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6407_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6407_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6407_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6407_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6407_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6408_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6408_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6408_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6408_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6408_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6408_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6408_HI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6409_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6409_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6409_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6409_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6409_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6409_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6409_HI_INTLK.SET_W.Field.text()))


        self.INTLCKWindow.TT6203_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6203_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6203_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6203_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6203_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6203_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6203_HIHI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6207_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6207_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6207_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6207_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6207_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6207_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6207_HIHI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6211_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6211_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6211_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6211_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6211_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6211_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6211_HIHI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6213_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6213_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6213_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6213_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6213_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6213_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6213_HIHI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6222_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6222_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6222_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6222_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6222_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6222_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6222_HIHI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6407_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6407_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6407_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6407_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6407_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6407_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6407_HIHI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6408_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6408_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6408_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6408_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6408_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6408_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6408_HIHI_INTLK.SET_W.Field.text()))

        self.INTLCKWindow.TT6409_HIHI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.TT6409_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6409_HIHI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.TT6409_HIHI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TT6409_HIHI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.TT6409_HIHI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.TT6409_HIHI_INTLK.SET_W.Field.text()))





        ##intlkc window d

        self.INTLCKWindow.TS1_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_D_LButtonClicked(self.INTLCKWindow.TS1_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TS1_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_D_RButtonClicked(self.INTLCKWindow.TS1_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TS1_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_D_RESET(self.INTLCKWindow.TS1_INTLK.Label.text() + "_INTLK"))


        self.INTLCKWindow.ES3347_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_D_LButtonClicked(self.INTLCKWindow.ES3347_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.ES3347_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_D_RButtonClicked(self.INTLCKWindow.ES3347_INTLK.Label.text() + "_INTLK"))

        self.INTLCKWindow.PUMP3305_OL_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_D_LButtonClicked(self.INTLCKWindow.PUMP3305_OL_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PUMP3305_OL_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_D_RButtonClicked(self.INTLCKWindow.PUMP3305_OL_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PUMP3305_OL_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_D_RESET(self.INTLCKWindow.PUMP3305_OL_INTLK.Label.text() + "_INTLK"))

        self.INTLCKWindow.TS2_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_D_LButtonClicked(self.INTLCKWindow.TS2_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TS2_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_D_RButtonClicked(self.INTLCKWindow.TS2_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TS2_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_D_RESET(self.INTLCKWindow.TS2_INTLK.Label.text() + "_INTLK"))

        self.INTLCKWindow.TS3_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_D_LButtonClicked(self.INTLCKWindow.TS3_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TS3_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_D_RButtonClicked(self.INTLCKWindow.TS3_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.TS3_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_D_RESET(self.INTLCKWindow.TS3_INTLK.Label.text() + "_INTLK"))

        self.INTLCKWindow.PU_PRIME_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_D_LButtonClicked(self.INTLCKWindow.PU_PRIME_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PU_PRIME_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_D_RButtonClicked(self.INTLCKWindow.PU_PRIME_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PU_PRIME_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_D_RESET(self.INTLCKWindow.PU_PRIME_INTLK.Label.text() + "_INTLK"))


        #UPS_UTILITY_INTLK, UPS_BATTERY_INTLK, LS2126_INTLK, LS2127_INTLK
        self.INTLCKWindow.UPS_UTILITY_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_D_LButtonClicked(self.INTLCKWindow.UPS_UTILITY_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.UPS_UTILITY_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_D_RButtonClicked(self.INTLCKWindow.UPS_UTILITY_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.UPS_UTILITY_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_D_RESET(self.INTLCKWindow.UPS_UTILITY_INTLK.Label.text() + "_INTLK"))

        self.INTLCKWindow.UPS_BATTERY_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_D_LButtonClicked(self.INTLCKWindow.UPS_BATTERY_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.UPS_BATTERY_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_D_RButtonClicked(self.INTLCKWindow.UPS_BATTERY_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.UPS_BATTERY_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_D_RESET(self.INTLCKWindow.UPS_BATTERY_INTLK.Label.text() + "_INTLK"))

        self.INTLCKWindow.LS2126_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_D_LButtonClicked(self.INTLCKWindow.LS2126_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.LS2126_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_D_RButtonClicked(self.INTLCKWindow.LS2126_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.LS2126_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_D_RESET(self.INTLCKWindow.LS2126_INTLK.Label.text() + "_INTLK"))

        self.INTLCKWindow.LS2127_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_D_LButtonClicked(self.INTLCKWindow.LS2127_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.LS2127_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_D_RButtonClicked(self.INTLCKWindow.LS2127_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.LS2127_INTLK.RST.clicked.connect(
            lambda x: self.INTLK_D_RESET(self.INTLCKWindow.LS2127_INTLK.Label.text() + "_INTLK"))
        #

        #FLAG
        self.MAN_TS.Set.LButton.clicked.connect(
            lambda x: self.FLAGLButtonClicked(self.MAN_TS.Label.text()))
        self.MAN_TS.Set.RButton.clicked.connect(
            lambda x: self.FLAGRButtonClicked(self.MAN_TS.Label.text()))

        self.MAN_HYD.Set.LButton.clicked.connect(
            lambda x: self.FLAGLButtonClicked(self.MAN_HYD.Label.text()))
        self.MAN_HYD.Set.RButton.clicked.connect(
            lambda x: self.FLAGRButtonClicked(self.MAN_HYD.Label.text()))


        self.PCYCLE_AUTOCYCLE.Set.LButton.clicked.connect(
            lambda x: self.FLAGLButtonClicked(self.PCYCLE_AUTOCYCLE.Label.text()))
        self.PCYCLE_AUTOCYCLE.Set.RButton.clicked.connect(
            lambda x: self.FLAGRButtonClicked(self.PCYCLE_AUTOCYCLE.Label.text()))

        self.CRYOVALVE_OPENCLOSE.Set.LButton.clicked.connect(
            lambda x: self.FLAGLButtonClicked("CRYOVALVE_OPENCLOSE"))
        self.CRYOVALVE_OPENCLOSE.Set.RButton.clicked.connect(
            lambda x: self.FLAGRButtonClicked("CRYOVALVE_OPENCLOSE"))

        self.CRYOVALVE_PV1201ACT.Set.LButton.clicked.connect(
            lambda x: self.FLAGLButtonClicked('CRYOVALVE_PV1201ACT'))
        self.CRYOVALVE_PV1201ACT.Set.RButton.clicked.connect(
            lambda x: self.FLAGRButtonClicked('CRYOVALVE_PV1201ACT'))

        self.CRYOVALVE_PV2201ACT.Set.LButton.clicked.connect(
            lambda x: self.FLAGLButtonClicked("CRYOVALVE_PV2201ACT"))
        self.CRYOVALVE_PV2201ACT.Set.RButton.clicked.connect(
            lambda x: self.FLAGRButtonClicked("CRYOVALVE_PV2201ACT"))



        #Procedure widgets
        self.TS_PRO.START.clicked.connect(
            lambda: self.ProcedureClick_TSv2(pname=self.TS_PRO.Label.currentText(), start=True, stop=False, abort=False))
        self.TS_PRO.STOP.clicked.connect(
            lambda: self.ProcedureClick_TSv2(pname=self.TS_PRO.Label.currentText(), start=False, stop=True, abort=False))
        self.TS_PRO.ABORT.clicked.connect(
            lambda: self.ProcedureClick_TSv2(pname=self.TS_PRO.Label.currentText(), start=False, stop=False, abort=True))

        self.TS_PRO.RST_FF.clicked.connect(
            lambda: self.Procedure_TS_updatev2(pname=self.TS_PRO.Label.currentText(), RST=True,
                                               SEL=self.TS_PRO.SEL_WR.Field.currentText(),
                                               ADDREM_MASS=self.TS_PRO.ADDREM_MASS_WR.Field.text(),
                                               MAXTIME=self.TS_PRO.MAXTIME_WR.Field.text(),
                                               update=False))
        self.TS_PRO.updatebutton.clicked.connect(
            lambda: self.Procedure_TS_updatev2(pname=self.TS_PRO.Label.currentText(), RST=False,
                                               SEL=self.TS_PRO.SEL_WR.Field.currentText(),
                                               ADDREM_MASS=self.TS_PRO.ADDREM_MASS_WR.Field.text(),
                                               MAXTIME=self.TS_PRO.MAXTIME_WR.Field.text(),
                                               update=True))

        # self.TS_ADDREM.START.clicked.connect(lambda: self.ProcedureClick(pid = self.TS_ADDREM.objectname, start = True, stop = False, abort = False))
        # self.TS_ADDREM.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_ADDREM.objectname, start=False, stop=True, abort=False))
        # self.TS_ADDREM.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_ADDREM.objectname, start=False, stop=False, abort=True))
        #
        # self.TS_ADDREM.expandwindow.Start.clicked.connect(
        #     lambda: self.ProcedureClick(pid=self.TS_ADDREM.objectname, start=True, stop=False, abort=False))
        # self.TS_ADDREM.expandwindow.Stop.clicked.connect(
        #     lambda: self.ProcedureClick(pid=self.TS_ADDREM.objectname, start=False, stop=True, abort=False))
        # self.TS_ADDREM.expandwindow.Abort.clicked.connect(
        #     lambda: self.ProcedureClick(pid=self.TS_ADDREM.objectname, start=False, stop=False, abort=True))
        # self.TS_ADDREM.expandwindow.RST_FF.clicked.connect(
        #     lambda: self.Procedure_TS_update(pname=self.TS_ADDREM.objectname,  RST=True, SEL=self.TS_ADDREM.expandwindow.SEL_WR.Field.text(), ADDREM_MASS=self.TS_ADDREM.expandwindow.ADDREM_MASS_WR.Field.text(), MAXTIME=self.TS_ADDREM.expandwindow.MAXTIME_WR.Field.text(),update=False))
        # self.TS_ADDREM.expandwindow.updatebutton.clicked.connect(
        #     lambda: self.Procedure_TS_update(pname=self.TS_ADDREM.objectname,  RST=False, SEL=self.TS_ADDREM.expandwindow.SEL_WR.Field.text(), ADDREM_MASS=self.TS_ADDREM.expandwindow.ADDREM_MASS_WR.Field.text(), MAXTIME=self.TS_ADDREM.expandwindow.MAXTIME_WR.Field.text(),update=True))



        # self.TS_EMPTY.START.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTY.objectname, start=True, stop=False, abort=False))
        # self.TS_EMPTY.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTY.objectname, start=False, stop=True, abort=False))
        # self.TS_EMPTY.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTY.objectname, start=False, stop=False, abort=True))
        #
        # self.TS_EMPTYALL.START.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTYALL.objectname, start=True, stop=False, abort=False))
        # self.TS_EMPTYALL.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTYALL.objectname, start=False, stop=True, abort=False))
        # self.TS_EMPTYALL.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTYALL.objectname, start=False, stop=False, abort=True))

        self.PU_PRIME.START.clicked.connect(lambda: self.ProcedureClick(pid=self.PU_PRIME.objectname, start=True, stop=False, abort=False))
        self.PU_PRIME.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.PU_PRIME.objectname, start=False, stop=True, abort=False))
        self.PU_PRIME.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.PU_PRIME.objectname, start=False, stop=False, abort=True))

        self.WRITE_SLOWDAQ.START.clicked.connect(lambda: self.ProcedureClick(pid=self.WRITE_SLOWDAQ.objectname, start=True, stop=False, abort=False))
        self.WRITE_SLOWDAQ.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.WRITE_SLOWDAQ.objectname, start=False, stop=True, abort=False))
        self.WRITE_SLOWDAQ.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.WRITE_SLOWDAQ.objectname, start=False, stop=False, abort=True))

        self.PRESSURE_CYCLE.START.clicked.connect(lambda: self.ProcedureClick(pid=self.PRESSURE_CYCLE.objectname, start=True, stop=False, abort=False))
        self.PRESSURE_CYCLE.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=True, abort=False))
        self.PRESSURE_CYCLE.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=False, abort=True))

        self.CRYOVALVE_CONTROL.START.clicked.connect(
            lambda: self.ProcedureClick(pid=self.CRYOVALVE_CONTROL.objectname, start=True, stop=False, abort=False))
        self.CRYOVALVE_CONTROL.STOP.clicked.connect(
            lambda: self.ProcedureClick(pid=self.CRYOVALVE_CONTROL.objectname, start=False, stop=True, abort=False))
        self.CRYOVALVE_CONTROL.ABORT.clicked.connect(
            lambda: self.ProcedureClick(pid=self.CRYOVALVE_CONTROL.objectname, start=False, stop=False, abort=True))


        self.PRESSURE_CYCLE.expandwindow.Start.clicked.connect(
            lambda: self.ProcedureClick(pid=self.PRESSURE_CYCLE.objectname, start=True, stop=False, abort=False))
        self.PRESSURE_CYCLE.expandwindow.Stop.clicked.connect(
            lambda: self.ProcedureClick(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=True, abort=False))
        self.PRESSURE_CYCLE.expandwindow.Abort.clicked.connect(
            lambda: self.ProcedureClick(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=False, abort=True))

        self.PRESSURE_CYCLE.expandwindow.RST_ABORT_FF.clicked.connect(
            lambda: self.Procedure_PC_update(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=False, abort=False,ABORT_FF=True,FASTCOMP_FF=False,PCYCLE_SLOWCOMP_FF=False,PCYCLE_CYLEQ_FF=False,PCYCLE_ACCHARGE_FF=False,PCYCLE_CYLBLEED_FF=False,PSET=self.PRESSURE_CYCLE.expandwindow.PSET_WR.Field.text(),MAXEXPTIME=self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_WR.Field.text(),MAXEQTIME=self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_WR.Field.text(),MAXEQPDIFF=self.PRESSURE_CYCLE.expandwindow.MAXEQPDIFF_WR.Field.text(),MAXACCTIME=self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_WR.Field.text(),MAXACCDPDT=self.PRESSURE_CYCLE.expandwindow.MAXACCDPDT_WR.Field.text(),MAXBLEEDTIME=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_WR.Field.text(),MAXBLEEDDPDT=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDDPDT_WR.Field.text(),update=False))
        self.PRESSURE_CYCLE.expandwindow.RST_FASTCOMP_FF.clicked.connect(
            lambda: self.Procedure_PC_update(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=False, abort=False,
                                             ABORT_FF=False, FASTCOMP_FF=True, PCYCLE_SLOWCOMP_FF=False,
                                             PCYCLE_CYLEQ_FF=False, PCYCLE_ACCHARGE_FF=False, PCYCLE_CYLBLEED_FF=False,
                                             PSET=self.PRESSURE_CYCLE.expandwindow.PSET_WR.Field.text(),
                                             MAXEXPTIME=self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_WR.Field.text(),
                                             MAXEQTIME=self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_WR.Field.text(),
                                             MAXEQPDIFF=self.PRESSURE_CYCLE.expandwindow.MAXEQPDIFF_WR.Field.text(),
                                             MAXACCTIME=self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_WR.Field.text(),
                                             MAXACCDPDT=self.PRESSURE_CYCLE.expandwindow.MAXACCDPDT_WR.Field.text(),
                                             MAXBLEEDTIME=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_WR.Field.text(),
                                             MAXBLEEDDPDT=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDDPDT_WR.Field.text(),
                                             update=False))
        self.PRESSURE_CYCLE.expandwindow.RST_SLOWCOMP_FF.clicked.connect(
            lambda: self.Procedure_PC_update(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=False, abort=False,
                                             ABORT_FF=False, FASTCOMP_FF=False, PCYCLE_SLOWCOMP_FF=True,
                                             PCYCLE_CYLEQ_FF=False, PCYCLE_ACCHARGE_FF=False, PCYCLE_CYLBLEED_FF=False,
                                             PSET=self.PRESSURE_CYCLE.expandwindow.PSET_WR.Field.text(),
                                             MAXEXPTIME=self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_WR.Field.text(),
                                             MAXEQTIME=self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_WR.Field.text(),
                                             MAXEQPDIFF=self.PRESSURE_CYCLE.expandwindow.MAXEQPDIFF_WR.Field.text(),
                                             MAXACCTIME=self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_WR.Field.text(),
                                             MAXACCDPDT=self.PRESSURE_CYCLE.expandwindow.MAXACCDPDT_WR.Field.text(),
                                             MAXBLEEDTIME=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_WR.Field.text(),
                                             MAXBLEEDDPDT=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDDPDT_WR.Field.text(),
                                             update=False))
        self.PRESSURE_CYCLE.expandwindow.RST_CYLEQ_FF.clicked.connect(
            lambda: self.Procedure_PC_update(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=False, abort=False,
                                             ABORT_FF=False, FASTCOMP_FF=False, PCYCLE_SLOWCOMP_FF=False,
                                             PCYCLE_CYLEQ_FF=True, PCYCLE_ACCHARGE_FF=False, PCYCLE_CYLBLEED_FF=False,
                                             PSET=self.PRESSURE_CYCLE.expandwindow.PSET_WR.Field.text(),
                                             MAXEXPTIME=self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_WR.Field.text(),
                                             MAXEQTIME=self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_WR.Field.text(),
                                             MAXEQPDIFF=self.PRESSURE_CYCLE.expandwindow.MAXEQPDIFF_WR.Field.text(),
                                             MAXACCTIME=self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_WR.Field.text(),
                                             MAXACCDPDT=self.PRESSURE_CYCLE.expandwindow.MAXACCDPDT_WR.Field.text(),
                                             MAXBLEEDTIME=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_WR.Field.text(),
                                             MAXBLEEDDPDT=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDDPDT_WR.Field.text(),
                                             update=False))
        self.PRESSURE_CYCLE.expandwindow.RST_ACCHARGE_FF.clicked.connect(
            lambda: self.Procedure_PC_update(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=False, abort=False,
                                             ABORT_FF=False, FASTCOMP_FF=False, PCYCLE_SLOWCOMP_FF=False,
                                             PCYCLE_CYLEQ_FF=False, PCYCLE_ACCHARGE_FF=True, PCYCLE_CYLBLEED_FF=False,
                                             PSET=self.PRESSURE_CYCLE.expandwindow.PSET_WR.Field.text(),
                                             MAXEXPTIME=self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_WR.Field.text(),
                                             MAXEQTIME=self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_WR.Field.text(),
                                             MAXEQPDIFF=self.PRESSURE_CYCLE.expandwindow.MAXEQPDIFF_WR.Field.text(),
                                             MAXACCTIME=self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_WR.Field.text(),
                                             MAXACCDPDT=self.PRESSURE_CYCLE.expandwindow.MAXACCDPDT_WR.Field.text(),
                                             MAXBLEEDTIME=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_WR.Field.text(),
                                             MAXBLEEDDPDT=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDDPDT_WR.Field.text(),
                                             update=False))
        self.PRESSURE_CYCLE.expandwindow.RST_CYLBLEED_FF.clicked.connect(
            lambda: self.Procedure_PC_update(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=False, abort=False,
                                             ABORT_FF=False, FASTCOMP_FF=False, PCYCLE_SLOWCOMP_FF=False,
                                             PCYCLE_CYLEQ_FF=False, PCYCLE_ACCHARGE_FF=False, PCYCLE_CYLBLEED_FF=True,
                                             PSET=self.PRESSURE_CYCLE.expandwindow.PSET_WR.Field.text(),
                                             MAXEXPTIME=self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_WR.Field.text(),
                                             MAXEQTIME=self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_WR.Field.text(),
                                             MAXEQPDIFF=self.PRESSURE_CYCLE.expandwindow.MAXEQPDIFF_WR.Field.text(),
                                             MAXACCTIME=self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_WR.Field.text(),
                                             MAXACCDPDT=self.PRESSURE_CYCLE.expandwindow.MAXACCDPDT_WR.Field.text(),
                                             MAXBLEEDTIME=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_WR.Field.text(),
                                             MAXBLEEDDPDT=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDDPDT_WR.Field.text(),
                                             update=False))

        self.PRESSURE_CYCLE.expandwindow.updatebutton.clicked.connect(
            lambda: self.Procedure_PC_update(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=False, abort=False,
                                             ABORT_FF=False, FASTCOMP_FF=False, PCYCLE_SLOWCOMP_FF=False,
                                             PCYCLE_CYLEQ_FF=False, PCYCLE_ACCHARGE_FF=False, PCYCLE_CYLBLEED_FF=False,
                                             PSET=self.PRESSURE_CYCLE.expandwindow.PSET_WR.Field.text(),
                                             MAXEXPTIME=self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_WR.Field.text(),
                                             MAXEQTIME=self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_WR.Field.text(),
                                             MAXEQPDIFF=self.PRESSURE_CYCLE.expandwindow.MAXEQPDIFF_WR.Field.text(),
                                             MAXACCTIME=self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_WR.Field.text(),
                                             MAXACCDPDT=self.PRESSURE_CYCLE.expandwindow.MAXACCDPDT_WR.Field.text(),
                                             MAXBLEEDTIME=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_WR.Field.text(),
                                             MAXBLEEDDPDT=self.PRESSURE_CYCLE.expandwindow.MAXBLEEDDPDT_WR.Field.text(),
                                             update=True))


    @QtCore.Slot()
    def LButtonClicked(self,pid):
        try:
            #if there is alread a command to send to tcp server, wait the new command until last one has been sent
            # in case cannot find the pid's address
            address = self.address[pid]
            self.commands.update({pid:{"server":"BO","address": address, "type":"valve","operation":"OPEN", "value":1}})
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid,"LButton is clicked")
        except Exception as e:
            print(e)



    @QtCore.Slot()
    def RButtonClicked(self, pid):

        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "valve", "operation": "CLOSE",
                              "value": 1}})
            print(self.commands)
            print(pid, "R Button is clicked", datetime.datetime.now())
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def FLAGLButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "FLAG", "operation": "OPEN", "value": 1}})
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def FLAGRButtonClicked(self, pid):

        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "FLAG", "operation": "CLOSE",
                                  "value": 1}})
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def SwitchLButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "switch", "operation": "ON", "value": 1}})
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def SwitchRButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "switch", "operation": "OFF",
                              "value": 1}})
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_A_LButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "INTLK_A", "operation": "ON", "value": 1}})
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_A_RButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "INTLK_A", "operation": "OFF",
                              "value": 1}})
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_A_RESET(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "INTLK_A", "operation": "RESET",
                                  "value": 1}})
            print(self.commands)
            print(pid, "RESET")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_A_update(self, pid,value):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "INTLK_A", "operation": "update",
                                  "value": float(value)}})
            print(self.commands)
            print(pid, "update")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_D_LButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "INTLK_D", "operation": "ON", "value": 1}})
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_D_RButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "INTLK_D", "operation": "OFF",
                                  "value": 1}})
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_D_RESET(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "INTLK_D", "operation": "RESET",
                                  "value": 1}})
            print(self.commands)
            print(pid, "RESET")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LOOP2PTLButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT_power", "operation": "OPEN", "value": 1}})
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)


    @QtCore.Slot()
    def LOOP2PTRButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT_power", "operation": "CLOSE",
                                  "value": 1}})
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LOOP2PTSet(self, pid, value):
        try:
            address = self.address[pid]
            if value in [0, 1, 2, 3]:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT", "operation": "SETMODE", "value": value}})
            else:
                print("value should be 0, 1, 2, 3")
            print(self.commands)
        except Exception as e:
            print(e)


    @QtCore.Slot()
    def LOOP2PTSETPOINTSet(self, pid, value1, value2):
        try:
            address = self.address[pid]
            if value1 == 1:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT",
                                  "operation": "SET1", "value": value2}})
            elif value1 == 2:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT",
                                  "operation": "SET2", "value": value2}})
            elif value1 == 3:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT",
                                  "operation": "SET3", "value": value2}})
            else:
                print("MODE number should be in 1-3")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LOOP2PTGroupButtonClicked(self, pid, setN):
        try:
            address = self.address[pid]
            if setN == 0:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT_setmode",
                                  "operation": "SET0", "value": True}})
            elif setN == 1:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT_setmode",
                                  "operation": "SET1", "value": True}})
            elif setN == 2:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT_setmode",
                                  "operation": "SET2", "value": True}})
            elif setN == 3:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT_setmode",
                                  "operation": "SET3", "value": True}})
            else:
                print("not a valid address")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LOOP2PTupdate(self, pid, modeN, setpoint):
        try:
            address = self.address[pid]
            if modeN == 'MODE0':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT_para",
                                      "operation": "SET0", "value": {"SETPOINT": setpoint}}})
            elif modeN == 'MODE1':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT_para",
                                      "operation": "SET1", "value": {"SETPOINT": setpoint}}})
            elif modeN == 'MODE2':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT_para",
                                      "operation": "SET2", "value": {"SETPOINT": setpoint}}})
            elif modeN == 'MODE3':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOP2PT_para",
                                      "operation": "SET3", "value": {"SETPOINT": setpoint}}})
            else:
                print("MODE number should be in MODE0-3 and is a string")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTRupdate(self,pid, modeN, setpoint, HI, LO):
        try:
            address = self.address[pid]
            if modeN == 'MODE0':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_para",
                              "operation": "SET0", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}})
            elif modeN == 'MODE1':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET1", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}})
            elif modeN == 'MODE2':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET2", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}})
            elif modeN == 'MODE3':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET3", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}})
            else:
                print("MODE number should be in MODE0-3 and is a string")

            print(self.commands)
        except Exception as e:
            print(e)




    @QtCore.Slot()
    def HTLButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_power", "operation": "EN",
                              "value": 1}})
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTRButtonClicked(self, pid):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_power", "operation": "DISEN",
                              "value": 1}})
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTSwitchSet(self, pid, value):
        try:
            address = self.address[pid]
            if value in [0,1,2,3]:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater", "operation": "SETMODE", "value": value}})
            else:
                print("value should be 0, 1, 2, 3")
            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTHISet(self, pid, value):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "heater",
                                  "operation": "HI_LIM", "value": value}})

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTLOSet(self, pid, value):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "heater",
                              "operation": "LO_LIM", "value": value}})

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTSETPOINTSet(self, pid, value1, value2):
        try:
            address = self.address[pid]
            if value1 == 0:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater",
                                  "operation": "SET0", "value": value2}})
            elif value1 == 1:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater",
                                  "operation": "SET1", "value": value2}})
            elif value1 == 2:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater",
                                  "operation": "SET2", "value": value2}})
            elif value1 == 3:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater",
                                  "operation": "SET3", "value": value2}})
            else:
                print("MODE number should be in 0-3")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTRGroupButtonClicked(self, pid, setN):
        try:
            address = self.address[pid]
            if setN == 0:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_setmode",
                                  "operation": "SET0", "value": True}})
            elif setN == 1:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_setmode",
                                  "operation": "SET1", "value": True}})
            elif setN == 2:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_setmode",
                                  "operation": "SET2", "value": True}})
            elif setN == 3:
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_setmode",
                                  "operation": "SET3", "value": True}})
            else:
                print("not a valid address")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTRupdate(self,pid, modeN, setpoint, HI, LO):
        try:
            address = self.address[pid]
            if modeN == 'MODE0':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_para",
                              "operation": "SET0", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}})
            elif modeN == 'MODE1':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET1", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}})
            elif modeN == 'MODE2':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET2", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}})
            elif modeN == 'MODE3':
                self.commands.update({pid:{"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET3", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}})
            else:
                print("MODE number should be in MODE0-3 and is a string")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def BOTTBoxUpdate(self,pid, Act,LowLimit, HighLimit,update=True):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "TT", "operation": {"Act":Act,
                                "LowLimit":float(LowLimit),"HighLimit":float(HighLimit),"Update":update}}})
            print(pid,Act,LowLimit,HighLimit,"ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def FPTTBoxUpdate(self,pid, Act,LowLimit, HighLimit,update=True):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "FP", "address": address, "type": "TT", "operation": {"Act":Act,
                                "LowLimit":float(LowLimit),"HighLimit":float(HighLimit),"Update":update}}})
            print(pid,Act,LowLimit,HighLimit,"ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def PTBoxUpdate(self, pid, Act, LowLimit, HighLimit,update=True):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "PT", "operation": {"Act": Act,
                                                                                                        "LowLimit": float(LowLimit), "HighLimit": float(HighLimit),"Update":update}}})
            print(pid, Act, LowLimit, HighLimit, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LEFTBoxUpdate(self, pid, Act, LowLimit, HighLimit, update=True):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "LEFT", "operation": {"Act": Act,
                                                                                                  "LowLimit": float(LowLimit), "HighLimit": float(HighLimit), "Update": update}}})
            print(pid, Act, LowLimit, HighLimit, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def ADBoxUpdate(self, pid, Act, LowLimit, HighLimit, update=True):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "AD", "address": address, "type": "AD", "operation": {"Act": Act,
                                                                                                    "LowLimit": float(
                                                                                                        LowLimit),
                                                                                                    "HighLimit": float(
                                                                                                        HighLimit),
                                                                                                    "Update": update}}})
            print(pid, Act, LowLimit, HighLimit, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def DinBoxUpdate(self, pid, Act, LowLimit, HighLimit, update=True):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "Din", "operation": {"Act": Act,
                                                                                                    "LowLimit": float(
                                                                                                        LowLimit),
                                                                                                    "HighLimit": float(
                                                                                                        HighLimit),
                                                                                                    "Update": update}}})
            print(pid, Act, LowLimit, HighLimit, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LOOPPIDBoxUpdate(self, pid, Act, LowLimit, HighLimit, update=True):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "LOOPPID_alarm", "operation": {"Act": Act,
                                                                                                   "LowLimit": float(
                                                                                                       LowLimit),
                                                                                                   "HighLimit": float(
                                                                                                       HighLimit),
                                                                                                   "Update": update}}})
            print(pid, Act, LowLimit, HighLimit, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def ProcedureClick(self, pid, start, stop, abort):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "Procedure", "operation": {"Start": start, "Stop": stop, "Abort": abort}}})
            print(pid, start, stop, abort, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def ProcedureClick_TSv2(self, pname, start, stop, abort):
        try:
            if pname=="ADDREM":
                pid = "TS_ADDREM"
            elif pname=="EMPTY":
                pid = "TS_EMPTY"
            elif pname=="EMPTY_ALL":
                pid = "TS_EMPTYALL"
            else:
                raise Exception("Procedure no correct name!")
            address = self.address[pid]
            self.commands.update({pid: {"server": "BO", "address": address, "type": "Procedure",
                                        "operation": {"Start": start, "Stop": stop, "Abort": abort}}})
            print(pid, start, stop, abort, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def Procedure_TS_update(self, pid, RST, SEL, ADDREM_MASS, MAXTIME,update):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "Procedure_TS",
                                  "operation": {"RST_FF":RST, "SEL": SEL, "ADDREM_MASS": ADDREM_MASS, "MAXTIME": MAXTIME,"update":update}}})
            print(pid, RST, SEL, ADDREM_MASS, MAXTIME,update, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def Procedure_TS_updatev2(self, pname, RST, SEL, ADDREM_MASS, MAXTIME, update):
        try:
            if pname=="ADDREM":
                pid = "TS_ADDREM"
            elif pname == "EMPTY":
                pid = "TS_EMPTY"
            elif pname == "EMPTY_ALL":
                pid = "TS_EMPTYALL"
            else:
                raise Exception("Procedure no correct name!")

            address = self.address[pid]
            self.commands.update({pid: {"server": "BO", "address": address, "type": "Procedure_TS",
                                        "operation": {"RST_FF": RST, "SEL": SEL, "ADDREM_MASS": ADDREM_MASS,
                                                      "MAXTIME": MAXTIME, "update": update}}})
            print(pid, RST, SEL, ADDREM_MASS, MAXTIME, update, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def Procedure_PC_update(self, pid, start, stop, abort,ABORT_FF,FASTCOMP_FF,PCYCLE_SLOWCOMP_FF,PCYCLE_CYLEQ_FF,PCYCLE_ACCHARGE_FF,PCYCLE_CYLBLEED_FF,PSET,MAXEXPTIME,MAXEQTIME,MAXEQPDIFF,MAXACCTIME,MAXACCDPDT,MAXBLEEDTIME,MAXBLEEDDPDT,update):
        try:
            address = self.address[pid]
            self.commands.update({pid:{"server": "BO", "address": address, "type": "Procedure_PC",
                                  "operation": {"ABORT_FF":ABORT_FF,"FASTCOMP_FF":FASTCOMP_FF,"PCYCLE_SLOWCOMP_FF":PCYCLE_SLOWCOMP_FF,
                                                "PCYCLE_CYLEQ_FF":PCYCLE_CYLEQ_FF,"PCYCLE_ACCHARGE_FF":PCYCLE_ACCHARGE_FF,"PCYCLE_CYLBLEED_FF":PCYCLE_CYLBLEED_FF,
                                                "PSET":PSET,"MAXEXPTIME":MAXEXPTIME,"MAXEQTIME":MAXEQTIME,"MAXEQPDIFF":MAXEQPDIFF,
                                                "MAXACCTIME":MAXACCTIME,"MAXACCDPDT":MAXACCDPDT,"MAXBLEEDTIME":MAXBLEEDTIME,"MAXBLEEDDPDT":MAXBLEEDDPDT,"update":update}}})
            print(pid, start, stop, abort, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def sendcommands(self):
        self.send_command_signal_MW.emit()
        print(self.commands)
        # print("signal received")

    
    def FindDistinctTrue(self, v0, v1, v2, v3):
        if v0 == True:
            if True in [v1, v2, v3]:
                print("Multiple True values")
                return "False"
            else:
                return "MODE0"
        elif v1 == True:
            if True in [v2, v3]:
                print("Multiple True values")
                return "False"
            else:
                return "MODE1"
        elif v2 == True:
            if True in [v3]:
                print("Multiple True values")
                return "False"
            else:
                return "MODE2"
        else:
            if v3:
                return "MODE3"
            else:
                print("No True Value")
                return "False"

    def FetchSetPoint(self, v0, v1, v2, v3, w0, w1, w2, w3):
        # v0-3 must corresponds to w0-3 in order
        if v0 == True:
            if True in [v1, v2, v3]:
                print("Multiple True values")
                return "False"
            else:
                return w0
        elif v1 == True:
            if True in [v2, v3]:
                print("Multiple True values")
                return "False"
            else:
                return w1
        elif v2 == True:
            if True in [v3]:
                print("Multiple True values")
                return "False"
            else:
                return w2
        else:
            if v3:
                return w3
            else:
                print("No True Value")
                return "False"

    @QtCore.Slot(object)
    def man_set(self, dic_c):
        self.commands['MAN_SET'] = dic_c
        # check the checkboxes

    @QtCore.Slot(object)
    def man_activated(self, dic_c):
        print("Acitve",dic_c["Active"])
        for element in self.BORTDAlarmMatrix:
            element.AlarmMode.setChecked(bool(dic_c["Active"]["TT"]["BO"][element.Label.text()]))

        # FP TTs
        # update alarmwindow widgets' <alarm> value

        for element in self.FPRTDAlarmMatrix:
            # print(element.Label.text())
            element.AlarmMode.setChecked(bool(dic_c["Active"]["TT"]["FP"][element.Label.text()]))

        for element in self.PTAlarmMatrix:
            element.AlarmMode.setChecked(bool(dic_c["Active"]["PT"][element.Label.text()]))


        for element in self.PTDIFFAlarmMatrix:
            temp_text = element.Label.text()
            temp_text= temp_text.replace("\u0394P_2121/1101", "PDIFF_PT2121PT1101")
            temp_text = temp_text.replace("\u0394P_2121/1325", "PDIFF_PT2121PT1325")
            temp_text = temp_text.replace("\u0394P_CYL/LT/CF4", "CYL3334_LT3335_CF4PRESSCALC")

            element.AlarmMode.setChecked(bool(dic_c["Active"]["PT"][temp_text]))
            del temp_text


        for element in self.LEFTVariableMatrix:
            element.AlarmMode.setChecked(bool(dic_c["Active"]["LEFT_REAL"][element.Label.text()]))

        for element in self.ADVariableMatrix:
            element.AlarmMode.setChecked(bool(dic_c["Active"]["AD"][element.Label.text()]))

        for element in self.DinAlarmMatrix:
            element.AlarmMode.setChecked(bool(dic_c["Active"]["Din"][element.Label.text()]))


        for element in self.LOOPPIDAlarmMatrix:
            element.AlarmMode.setChecked(bool(dic_c["Active"]["LOOPPID"][element.Label.text()]))


    @QtCore.Slot(object)
    def updatedisplay(self, received_dic_c):
        print("Display updating", datetime.datetime.now())
        # update the check states in initilazation
        if received_dic_c["Active"]["INI_CHECK"]==True and self.CHECKED == False:
            self.man_activated(received_dic_c)
            self.CHECKED = True






        if self.TS_PRO.Label.currentText()=="ADDREM":
            self.TS_PRO.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"]["TS_ADDREM"])
            self.TS_PRO.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"]["TS_ADDREM"])
            self.TS_PRO.EXIT.SetValue(
            received_dic_c["data"]["Procedure"]["EXIT"]["TS_ADDREM"])
        elif self.TS_PRO.Label.currentText()=="EMPTY":
            self.TS_PRO.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"]["TS_EMPTY"])
            self.TS_PRO.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"]["TS_EMPTY"])
            self.TS_PRO.EXIT.SetValue(
                received_dic_c["data"]["Procedure"]["EXIT"]["TS_EMPTY"])
        elif self.TS_PRO.Label.currentText()=="EMPTY_ALL":
            self.TS_PRO.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"]["TS_EMPTYALL"])
            self.TS_PRO.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"]["TS_EMPTYALL"])
            self.TS_PRO.EXIT.SetValue(
                received_dic_c["data"]["Procedure"]["EXIT"]["TS_EMPTYALL"])
        self.TS_PRO.FF_RD.Field.setText(bin(received_dic_c["data"]["FF"]["TS_ADDREM_FF"]))
        self.TS_PRO.SEL_RD.SetIntValue(received_dic_c["data"]["PARA_I"]["TS_SEL"])
        self.TS_PRO.ADDREM_MASS_RD.SetValue(received_dic_c["data"]["PARA_F"]["TS_ADDREM_MASS"])
        self.TS_PRO.MAXTIME_RD.SetIntValue(received_dic_c["data"]["PARA_T"]["TS_ADDREM_MAXTIME"] / 1000)
        self.TS_PRO.N2MASSTX.SetValue(
            received_dic_c["data"]["LEFT_REAL"]["value"]["TS_ADDREM_N2MASSTX"])
        self.TS_PRO.FLOWET.SetIntValue(received_dic_c["data"]["PARA_T"]["TS_ADDREM_FLOWET"] / 1000)
        self.TS_PRO.TS1_MASS.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS1_MASS"])
        self.TS_PRO.TS2_MASS.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS2_MASS"])
        self.TS_PRO.TS3_MASS.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS3_MASS"])

        # self.TS_PRO.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.TS_PRO.objectname])
        # self.TS_PRO.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.TS_PRO.objectname])
        # self.TS_PRO.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.TS_PRO.objectname])
        #
        # self.TS_PRO.Running.UpdateColor(
        #     received_dic_c["data"]["Procedure"]["Running"][self.TS_PRO.objectname])
        # self.TS_PRO.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.TS_PRO.objectname])
        # self.TS_PRO.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.TS_PRO.objectname])
        #

        # self.TS_ADDREM.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.TS_ADDREM.objectname])
        # self.TS_ADDREM.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.TS_ADDREM.objectname])
        # self.TS_ADDREM.expandwindow.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.TS_ADDREM.objectname])
        #
        # self.TS_ADDREM.expandwindow.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.TS_ADDREM.objectname])
        # self.TS_ADDREM.expandwindow.FF_RD.Field.setText(bin(received_dic_c["data"]["FF"]["TS_ADDREM_FF"]))
        # self.TS_ADDREM.expandwindow.SEL_RD.SetIntValue(received_dic_c["data"]["PARA_I"]["TS_SEL"])
        # self.TS_ADDREM.expandwindow.ADDREM_MASS_RD.SetValue(received_dic_c["data"]["PARA_F"]["TS_ADDREM_MASS"])
        # self.TS_ADDREM.expandwindow.MAXTIME_RD.SetIntValue(received_dic_c["data"]["PARA_T"]["TS_ADDREM_MAXTIME"]/1000)
        # self.TS_ADDREM.expandwindow.N2MASSTX.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS_ADDREM_N2MASSTX"])
        # self.TS_ADDREM.expandwindow.FLOWET.SetIntValue(received_dic_c["data"]["PARA_T"]["TS_ADDREM_FLOWET"]/1000)
        # self.TS_ADDREM.expandwindow.TS1_MASS.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS1_MASS"])
        # self.TS_ADDREM.expandwindow.TS2_MASS.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS2_MASS"])
        # self.TS_ADDREM.expandwindow.TS3_MASS.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS3_MASS"])
        # self.TS_ADDREM.expandwindow.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.TS_ADDREM.objectname])
        #
        # self.TS_EMPTY.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.TS_EMPTY.objectname])
        # self.TS_EMPTY.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.TS_EMPTY.objectname])
        # self.TS_EMPTY.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.TS_EMPTY.objectname])
        #
        # self.TS_EMPTYALL.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.TS_EMPTYALL.objectname])
        # self.TS_EMPTYALL.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.TS_EMPTYALL.objectname])
        # self.TS_EMPTYALL.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.TS_EMPTYALL.objectname])

        self.PU_PRIME.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.PU_PRIME.objectname])
        self.PU_PRIME.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.PU_PRIME.objectname])
        self.PU_PRIME.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.PU_PRIME.objectname])

        self.WRITE_SLOWDAQ.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.WRITE_SLOWDAQ.objectname])
        self.WRITE_SLOWDAQ.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.WRITE_SLOWDAQ.objectname])
        self.WRITE_SLOWDAQ.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.WRITE_SLOWDAQ.objectname])

        self.CRYOVALVE_CONTROL.Running.UpdateColor(
            received_dic_c["data"]["Procedure"]["Running"][self.CRYOVALVE_CONTROL.objectname])
        self.CRYOVALVE_CONTROL.INTLKD.UpdateColor(
            received_dic_c["data"]["Procedure"]["INTLKD"][self.CRYOVALVE_CONTROL.objectname])
        self.CRYOVALVE_CONTROL.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.CRYOVALVE_CONTROL.objectname])

        self.PRESSURE_CYCLE.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.PRESSURE_CYCLE.objectname])
        self.PRESSURE_CYCLE.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.PRESSURE_CYCLE.objectname])

        self.PRESSURE_CYCLE.expandwindow.Running.UpdateColor(
            received_dic_c["data"]["Procedure"]["Running"][self.PRESSURE_CYCLE.objectname])
        self.PRESSURE_CYCLE.expandwindow.INTLKD.UpdateColor(
            received_dic_c["data"]["Procedure"]["INTLKD"][self.PRESSURE_CYCLE.objectname])
        self.PRESSURE_CYCLE.expandwindow.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.PRESSURE_CYCLE.objectname])
        self.PRESSURE_CYCLE.expandwindow.ABORT_FF_RD.Field.setText(bin(
            received_dic_c["data"]["FF"]["PCYCLE_ABORT_FF"]))
        self.PRESSURE_CYCLE.expandwindow.FASTCOMP_FF_RD.Field.setText(bin(
            received_dic_c["data"]["FF"]["PCYCLE_FASTCOMP_FF"]))
        self.PRESSURE_CYCLE.expandwindow.SLOWCOMP_FF_RD.Field.setText(bin(
            received_dic_c["data"]["FF"]["PCYCLE_SLOWCOMP_FF"]))
        self.PRESSURE_CYCLE.expandwindow.CYLEQ_FF_RD.Field.setText(bin(
            received_dic_c["data"]["FF"]["PCYCLE_CYLEQ_FF"]))
        self.PRESSURE_CYCLE.expandwindow.ACCHARGE_FF_RD.Field.setText(bin(
            received_dic_c["data"]["FF"]["PCYCLE_ACCHARGE_FF"]))
        self.PRESSURE_CYCLE.expandwindow.CYLBLEED_FF_RD.Field.setText(bin(
            received_dic_c["data"]["FF"]["PCYCLE_CYLBLEED_FF"]))
        self.PRESSURE_CYCLE.expandwindow.PSET_RD.SetValue(
            received_dic_c["data"]["PARA_F"]["PCYCLE_PSET"])
        self.PRESSURE_CYCLE.expandwindow.EXPTIME_RD.SetValue(
            round(received_dic_c["data"]["TIME"]["PCYCLE_EXPTIME"]))
        self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_RD.SetIntValue(
            round(received_dic_c["data"]["PARA_T"]["PCYCLE_MAXEXPTIME"]/1000))
        self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_RD.SetIntValue(
            round(received_dic_c["data"]["PARA_T"]["PCYCLE_MAXEQTIME"]/1000))
        self.PRESSURE_CYCLE.expandwindow.MAXEQPDIFF_RD.SetValue(
            received_dic_c["data"]["PARA_F"]["PCYCLE_MAXEQPDIFF"])
        self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_RD.SetIntValue(
            round(received_dic_c["data"]["PARA_T"]["PCYCLE_MAXACCTIME"]/1000))
        self.PRESSURE_CYCLE.expandwindow.MAXACCDPDT_RD.SetValue(
            received_dic_c["data"]["PARA_F"]["PCYCLE_MAXACCDPDT"])
        self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_RD.SetIntValue(
            round(received_dic_c["data"]["PARA_T"]["PCYCLE_MAXBLEEDTIME"]/1000))
        self.PRESSURE_CYCLE.expandwindow.MAXBLEEDDPDT_RD.SetValue(
            received_dic_c["data"]["PARA_F"]["PCYCLE_MAXBLEEDDPDT"])
        self.PRESSURE_CYCLE.expandwindow.SLOWCOMP_SET_RD.SetValue(
            received_dic_c["data"]["PARA_F"]["PCYCLE_SLOWCOMP_SET"])



        #Update alarmwindow's widgets' value





        for element in self.BORTDAlarmMatrix:
            # print(element.Label.text())

            element.UpdateAlarm(

                received_dic_c["Alarm"]["TT"]["BO"][element.Label.text()])
            element.Indicator.SetValue(
                received_dic_c["data"]["TT"]["BO"]["value"][element.Label.text()])
            element.Low_Read.SetValue(
                received_dic_c["data"]["TT"]["BO"]["low"][element.Label.text()])
            element.High_Read.SetValue(
                received_dic_c["data"]["TT"]["BO"]["high"][element.Label.text()])



        # FP TTs
        # update alarmwindow widgets' <alarm> value


        for element in self.FPRTDAlarmMatrix:
            # print(element.Label.text())

            element.UpdateAlarm(

                received_dic_c["Alarm"]["TT"]["FP"][element.Label.text()])
            element.Indicator.SetValue(
                received_dic_c["data"]["TT"]["FP"]["value"][element.Label.text()])
            element.Low_Read.SetValue(
                received_dic_c["data"]["TT"]["FP"]["low"][element.Label.text()])
            element.High_Read.SetValue(
                received_dic_c["data"]["TT"]["FP"]["high"][element.Label.text()])

        for element in self.PTAlarmMatrix:
            # print(element.Label.text())

            element.UpdateAlarm(
                received_dic_c["Alarm"]["PT"][element.Label.text()])
            element.Indicator.SetValue(
                received_dic_c["data"]["PT"]["value"][element.Label.text()])
            element.Low_Read.SetValue(
                received_dic_c["data"]["PT"]["low"][element.Label.text()])
            element.High_Read.SetValue(
                received_dic_c["data"]["PT"]["high"][element.Label.text()])

        # 2PTs that should be displayed at expotentially
        for element in self.expPTAlarmMatrix:
            # print(element.Label.text())

            element.UpdateAlarm(
                received_dic_c["Alarm"]["PT"][element.Label.text()])
            element.Indicator.SetExpValue(
                received_dic_c["data"]["PT"]["value"][element.Label.text()])
            element.Low_Read.SetExpValue(
                received_dic_c["data"]["PT"]["low"][element.Label.text()])
            element.High_Read.SetExpValue(
                received_dic_c["data"]["PT"]["high"][element.Label.text()])


        #LEFT Variables: because the receive_dic's dimension is different from the dimension in self.GLLEFT, I have to set widgets' value in self.GLLEFT mannually

        for element in self.LEFTVariableMatrix:
            element.UpdateAlarm(
                received_dic_c["Alarm"]["LEFT_REAL"][element.Label.text()])
            element.Indicator.SetValue(
                received_dic_c["data"]["LEFT_REAL"]["value"][element.Label.text()])
            element.Low_Read.SetValue(
                received_dic_c["data"]["LEFT_REAL"]["low"][element.Label.text()])
            element.High_Read.SetValue(
                received_dic_c["data"]["LEFT_REAL"]["high"][element.Label.text()])

        for element in self.ADVariableMatrix:
            element.UpdateAlarm(
                received_dic_c["Alarm"]["AD"][element.Label.text()])
            element.Indicator.SetValue(
                received_dic_c["data"]["AD"]["value"][element.Label.text()])
            element.Low_Read.SetValue(
                received_dic_c["data"]["AD"]["low"][element.Label.text()])
            element.High_Read.SetValue(
                received_dic_c["data"]["AD"]["high"][element.Label.text()])


        for element in self.DinAlarmMatrix:
            # print(element.Label.text())

            element.UpdateAlarm(
                received_dic_c["Alarm"]["Din"][element.Label.text()])
            element.Indicator.SetValue(
                received_dic_c["data"]["Din"]["value"][element.Label.text()])
            element.Low_Read.SetValue(
                received_dic_c["data"]["Din"]["low"][element.Label.text()])
            element.High_Read.SetValue(
                received_dic_c["data"]["Din"]["high"][element.Label.text()])


        for element in self.LOOPPIDAlarmMatrix:
            # print(element.Label.text())

            element.UpdateAlarm(
                received_dic_c["Alarm"]["LOOPPID"][element.Label.text()])
            element.Indicator.SetValue(
                received_dic_c["data"]["LOOPPID"]["OUT"][element.Label.text()])
            element.Low_Read.SetValue(
                received_dic_c["data"]["LOOPPID"]["Alarm_LowLimit"][element.Label.text()])
            element.High_Read.SetValue(
                received_dic_c["data"]["LOOPPID"]["Alarm_HighLimit"][element.Label.text()])


        AlarmMatrix= []
        for element in self.AlarmMatrix:
            AlarmMatrix.append(element.Alarm)
        self.update_alarmwindow(AlarmMatrix)

        self.PV1344.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV1344"])
        self.PV4307.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV4307"])
        self.PV4308.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV4308"])
        self.PV4317.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV4317"])
        self.PV4318.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV4318"])
        self.PV4321.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV4321"])
        self.PV4324.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV4324"])
        self.PV5305.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV5305"])
        self.PV5306.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV5306"])
        self.PV5307.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV5307"])
        self.PV5309.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV5309"])
        self.SV3307.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV3307"])
        self.SV3310.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV3310"])
        self.SV3322.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV3322"])
        self.SV3325.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV3325"])
        self.SV3329.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV3329"])
        self.SV4327.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV4327"])
        self.SV4328.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV4328"])
        self.SV4329.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV4329"])
        self.SV4331.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV4331"])
        self.SV4332.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV4332"])
        self.SV4337.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["SV4337"])
        self.HFSV3312.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"])
        self.HFSV3323.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"])
        self.HFSV3331.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"])
        self.CC9313_CONT.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["CC9313_CONT"])
        self.PT_EN6306.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PT_EN6306"])
        self.PV4345.ColorLabel(received_dic_c["data"]["Valve"]["OUT"]["PV4345"])





        #update Din widget
        self.PUMP3305_CON.UpdateColor(received_dic_c["data"]["Din"]["value"]["PUMP3305_CON"])
        self.PUMP3305_OL.UpdateColor(received_dic_c["data"]["Din"]["value"]["PUMP3305_OL"])
        self.ES3347.UpdateColor(received_dic_c["data"]["Din"]["value"]["ES3347"])
        self.LS3338.UpdateColor(received_dic_c["data"]["Din"]["value"]["LS3338"])
        self.LS3339.UpdateColor(received_dic_c["data"]["Din"]["value"]["LS3339"])
        self.PS2352.UpdateColor(received_dic_c["data"]["Din"]["value"]["PS2352"])
        self.PS8302.UpdateColor(received_dic_c["data"]["Din"]["value"]["PS8302"])
        # self.UPS_ON_BATT.UpdateColor(received_dic_c["data"]["Din"]["value"]["UPS_ON_BATT"])
        # self.UPS_LOW_BATT.UpdateColor(received_dic_c["data"]["Din"]["value"]["UPS_LOW_BATT"])
        self.LS2126.UpdateColor(received_dic_c["data"]["Din"]["value"]["LS2126"])
        self.LS2127.UpdateColor(received_dic_c["data"]["Din"]["value"]["LS2127"])
        self.LS2128.UpdateColor(received_dic_c["data"]["Din"]["value"]["LS2128"])
        self.LS2129.UpdateColor(received_dic_c["data"]["Din"]["value"]["LS2129"])
        self.CC9313_POWER.UpdateColor(received_dic_c["data"]["Din"]["value"]["CC9313_POW"])
        self.UPS_UTILITY_OK.UpdateColor(received_dic_c["data"]["Din"]["value"]["UPS_UTI_OK"])
        self.UPS_BATTERY_OK.UpdateColor(received_dic_c["data"]["Din"]["value"]["UPS_BAT_OK"])

        # show whether the widgets status are normal: manully controlled and no error signal


        if received_dic_c["data"]["Valve"]["MAN"]["PV1344"] and not received_dic_c["data"]["Valve"]["ERR"]["PV1344"]:

            self.PV1344.ActiveState.UpdateColor(True)
        else:
            self.PV1344.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["PV4307"] and not received_dic_c["data"]["Valve"]["ERR"]["PV4307"]:

            self.PV4307.ActiveState.UpdateColor(True)
        else:
            self.PV4307.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["PV4308"] and not received_dic_c["data"]["Valve"]["ERR"]["PV4308"]:

            self.PV4308.ActiveState.UpdateColor(True)
        else:
            self.PV4308.ActiveState.UpdateColor(False)


        if received_dic_c["data"]["Valve"]["MAN"]["PV4317"] and not received_dic_c["data"]["Valve"]["ERR"]["PV4317"]:

            self.PV4317.ActiveState.UpdateColor(True)
        else:
            self.PV4317.ActiveState.UpdateColor(False)



        if received_dic_c["data"]["Valve"]["MAN"]["PV4318"] and not received_dic_c["data"]["Valve"]["ERR"]["PV4318"]:

            self.PV4318.ActiveState.UpdateColor(True)
        else:
            self.PV4318.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["PV4321"] and not received_dic_c["data"]["Valve"]["ERR"]["PV4321"]:

            self.PV4321.ActiveState.UpdateColor(True)
        else:
            self.PV4321.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["PV4324"] and not received_dic_c["data"]["Valve"]["ERR"]["PV4324"]:

            self.PV4324.ActiveState.UpdateColor(True)
        else:
            self.PV4324.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["PV5305"] and not received_dic_c["data"]["Valve"]["ERR"]["PV5305"]:

            self.PV5305.ActiveState.UpdateColor(True)
        else:
            self.PV5305.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["PV5306"] and not received_dic_c["data"]["Valve"]["ERR"]["PV5306"]:

            self.PV5306.ActiveState.UpdateColor(True)
        else:
            self.PV5306.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["PV5307"] and not received_dic_c["data"]["Valve"]["ERR"]["PV5307"]:

            self.PV5307.ActiveState.UpdateColor(True)
        else:
            self.PV5307.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["PV5309"] and not received_dic_c["data"]["Valve"]["ERR"]["PV5309"]:

            self.PV5309.ActiveState.UpdateColor(True)
        else:
            self.PV5309.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV3307"] and not received_dic_c["data"]["Valve"]["ERR"]["SV3307"]:

            self.SV3307.ActiveState.UpdateColor(True)
        else:
            self.SV3307.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV3310"] and not received_dic_c["data"]["Valve"]["ERR"]["SV3310"]:

            self.SV3310.ActiveState.UpdateColor(True)
        else:
            self.SV3310.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV3322"] and not received_dic_c["data"]["Valve"]["ERR"]["SV3322"]:

            self.SV3322.ActiveState.UpdateColor(True)
        else:
            self.SV3322.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV3325"] and not received_dic_c["data"]["Valve"]["ERR"]["SV3325"]:

            self.SV3325.ActiveState.UpdateColor(True)
        else:
            self.SV3325.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV3329"] and not received_dic_c["data"]["Valve"]["ERR"]["SV3329"]:

            self.SV3329.ActiveState.UpdateColor(True)
        else:
            self.SV3329.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV4327"] and not received_dic_c["data"]["Valve"]["ERR"]["SV4327"]:

            self.SV4327.ActiveState.UpdateColor(True)
        else:
            self.SV4327.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV4328"] and not received_dic_c["data"]["Valve"]["ERR"]["SV4328"]:

            self.SV4328.ActiveState.UpdateColor(True)
        else:
            self.SV4328.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV4329"] and not received_dic_c["data"]["Valve"]["ERR"]["SV4329"]:

            self.SV4329.ActiveState.UpdateColor(True)
        else:
            self.SV4329.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV4331"] and not received_dic_c["data"]["Valve"]["ERR"]["SV4331"]:

            self.SV4331.ActiveState.UpdateColor(True)
        else:
            self.SV4331.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV4332"] and not received_dic_c["data"]["Valve"]["ERR"]["SV4332"]:

            self.SV4332.ActiveState.UpdateColor(True)
        else:
            self.SV4332.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["SV4337"] and not received_dic_c["data"]["Valve"]["ERR"]["SV4337"]:

            self.SV4337.ActiveState.UpdateColor(True)
        else:
            self.SV4337.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["HFSV3312"] and not received_dic_c["data"]["Valve"]["ERR"]["HFSV3312"]:

            self.HFSV3312.ActiveState.UpdateColor(True)
        else:
            self.HFSV3312.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["HFSV3323"] and not received_dic_c["data"]["Valve"]["ERR"]["HFSV3323"]:

            self.HFSV3323.ActiveState.UpdateColor(True)
        else:
            self.HFSV3323.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["HFSV3331"] and not received_dic_c["data"]["Valve"]["ERR"]["HFSV3331"]:

            self.HFSV3331.ActiveState.UpdateColor(True)
        else:
            self.HFSV3331.ActiveState.UpdateColor(False)


        if received_dic_c["data"]["Valve"]["MAN"]["CC9313_CONT"] and not received_dic_c["data"]["Valve"]["ERR"]["CC9313_CONT"]:

            self.CC9313_CONT.ActiveState.UpdateColor(True)
        else:
            self.CC9313_CONT.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["PT_EN6306"] and not received_dic_c["data"]["Valve"]["ERR"]["PT_EN6306"]:

            self.PT_EN6306.ActiveState.UpdateColor(True)
        else:
            self.PT_EN6306.ActiveState.UpdateColor(False)

        if received_dic_c["data"]["Valve"]["MAN"]["PV4345"] and not received_dic_c["data"]["Valve"]["ERR"]["PV4345"]:

            self.PV4345.ActiveState.UpdateColor(True)
        else:
            self.PV4345.ActiveState.UpdateColor(False)




        if received_dic_c["data"]["Valve"]["Busy"]["PV1344"] ==True:
            self.PV1344.ButtonTransitionState(False)
            # self.Valve_buffer["PV1344"] = received_dic_c["data"]["Valve"]["OUT"]["PV1344"]

        else:
            #if not rejected, and new value is different from the previous one(the valve status changed), then set busy back
            self.PV1344.ButtonTransitionState(True)



        if received_dic_c["data"]["Valve"]["Busy"]["PV4307"] == True:
            self.PV4307.ButtonTransitionState(False)
        else:
            self.PV4307.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["PV4308"] == True:
            self.PV4308.ButtonTransitionState(False)
        else:
            self.PV4308.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["PV4317"] == True:
            self.PV4317.ButtonTransitionState(True)
        elif not received_dic_c["data"]["Valve"]["Busy"]["PV4317"]:
            self.PV4317.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["Valve"]["Busy"]["PV4318"] == True:
            self.PV4318.ButtonTransitionState(False)

        else:
            self.PV4318.ButtonTransitionState(False)


        if received_dic_c["data"]["Valve"]["Busy"]["PV4321"] == True:
            self.PV4321.ButtonTransitionState(False)
        else:
             self.PV4321.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["PV4324"] == True:
            self.PV4324.ButtonTransitionState(False)

        else:
             self.PV4324.ButtonTransitionState(False)


        if received_dic_c["data"]["Valve"]["Busy"]["PV5305"] == True:
            self.PV5305.ButtonTransitionState(False)

        else:
            self.PV5305.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["PV5306"] == True:
            self.PV5306.ButtonTransitionState(False)

        else:
            self.PV5306.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["PV5307"] == True:
            self.PV5307.ButtonTransitionState(False)

        else:
            self.PV5307.ButtonTransitionState(False)


        if received_dic_c["data"]["Valve"]["Busy"]["PV5309"] == True:
            self.PV5309.ButtonTransitionState(False)

        else:
            self.PV5309.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["SV3307"] == True:
            self.SV3307.ButtonTransitionState(False)

        else:
            self.SV3307.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["SV3310"] == True:
            self.SV3310.ButtonTransitionState(False)

        else:
            self.SV3310.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["SV3322"] == True:
            self.SV3322.ButtonTransitionState(False)

        else:
            self.SV3322.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["SV3325"] == True:
            self.SV3325.ButtonTransitionState(False)

        else:
            self.SV3325.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["SV3329"] == True:
            self.SV3329.ButtonTransitionState(False)

        else:
            self.SV3329.ButtonTransitionState(False)

        if received_dic_c["data"]["Valve"]["Busy"]["SV4327"] == True:
            self.SV4327.ButtonTransitionState(False)

        else:
            self.SV4327.ButtonTransitionState(False)

        if received_dic_c["data"]["Valve"]["Busy"]["SV4328"] == True:
            self.SV4328.ButtonTransitionState(False)

        else:
            self.SV4328.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["SV4329"] == True:
            self.SV4329.ButtonTransitionState(False)

        else:
            self.SV4329.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["SV4331"] == True:
            self.SV4331.ButtonTransitionState(False)

        else:
            self.SV4331.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["SV4332"] == True:
            self.SV4332.ButtonTransitionState(False)

        else:
            self.SV4332.ButtonTransitionState(False)

        if received_dic_c["data"]["Valve"]["Busy"]["SV4337"] == True:
            self.SV4337.ButtonTransitionState(False)

        else:
            self.SV4337.ButtonTransitionState(False)

        if received_dic_c["data"]["Valve"]["Busy"]["HFSV3312"] == True:
            self.HFSV3312.ButtonTransitionState(False)

        else:
            self.HFSV3312.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["HFSV3323"] == True:
            self.HFSV3323.ButtonTransitionState(False)

        else:
            self.HFSV3323.ButtonTransitionState(False)



        if received_dic_c["data"]["Valve"]["Busy"]["HFSV3331"] == True:
            self.HFSV3331.ButtonTransitionState(False)

        else:
            self.HFSV3331.ButtonTransitionState(False)


        if received_dic_c["data"]["Valve"]["Busy"]["CC9313_CONT"] == True:
            self.CC9313_CONT.ButtonTransitionState(False)

        else:
            self.CC9313_CONT.ButtonTransitionState(False)

        if received_dic_c["data"]["Valve"]["Busy"]["PT_EN6306"] == True:
            self.PT_EN6306.ButtonTransitionState(False)

        else:
            self.PT_EN6306.ButtonTransitionState(False)

        if received_dic_c["data"]["Valve"]["Busy"]["PV4345"] == True:
            self.PV4345.ButtonTransitionState(False)

        else:
            self.PV4345.ButtonTransitionState(False)




        # FLAG
        if received_dic_c["data"]["FLAG"]["INTLKD"]["MAN_TS"]:

            self.MAN_TS.INTLK.UpdateColor(True)
        else:
            self.MAN_TS.INTLK.UpdateColor(False)

        # if received_dic_c["data"]["FLAG"]["value"]["MAN_TS"] != self.FLAG_buffer["MAN_TS"]:
        #     self.MAN_TS.Set.ButtonTransitionState(False)
        #     self.FLAG_buffer["MAN_TS"] = received_dic_c["data"]["FLAG"]["value"]["MAN_TS"]
        # else:
        #     pass
        if received_dic_c["data"]["FLAG"]["Busy"]["MAN_TS"] == True:
            self.MAN_TS.Set.ButtonTransitionState(False)

        elif received_dic_c["data"]["FLAG"]["Busy"]["MAN_TS"] == False:
            self.MAN_TS.Set.ButtonTransitionState(False)
        else:
            pass



        if received_dic_c["data"]["FLAG"]["INTLKD"]["MAN_HYD"]:

            self.MAN_HYD.INTLK.UpdateColor(True)
        else:
            self.MAN_HYD.INTLK.UpdateColor(False)

        # if received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"] != self.FLAG_buffer["MAN_HYD"]:
        #     self.MAN_HYD.Set.ButtonTransitionState(False)
        #     self.FLAG_buffer["MAN_HYD"] = received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"]
        # else:
        #     pass
        if received_dic_c["data"]["FLAG"]["Busy"]["MAN_HYD"] == True:
            self.MAN_HYD.Set.ButtonTransitionState(False)

        elif received_dic_c["data"]["FLAG"]["Busy"]["MAN_HYD"] == False:
            self.MAN_HYD.Set.ButtonTransitionState(False)
        else:
            pass


        if received_dic_c["data"]["FLAG"]["INTLKD"]["PCYCLE_AUTOCYCLE"]:

            self.PCYCLE_AUTOCYCLE.INTLK.UpdateColor(True)
        else:
            self.PCYCLE_AUTOCYCLE.INTLK.UpdateColor(False)

        # if received_dic_c["data"]["FLAG"]["value"]["PCYCLE_AUTOCYCLE"] != self.FLAG_buffer["PCYCLE_AUTOCYCLE"]:
        #     self.PCYCLE_AUTOCYCLE.Set.ButtonTransitionState(False)
        #     self.FLAG_buffer["PCYCLE_AUTOCYCLE"] = received_dic_c["data"]["FLAG"]["value"]["PCYCLE_AUTOCYCLE"]
        # else:
        #     pass
        if received_dic_c["data"]["FLAG"]["Busy"]["PCYCLE_AUTOCYCLE"] == True:
            self.PCYCLE_AUTOCYCLE.Set.ButtonTransitionState(False)

        elif received_dic_c["data"]["FLAG"]["Busy"]["PCYCLE_AUTOCYCLE"] == False:
            self.PCYCLE_AUTOCYCLE.Set.ButtonTransitionState(False)
        else:
            pass

        #
        if received_dic_c["data"]["FLAG"]["INTLKD"]["CRYOVALVE_OPENCLOSE"]:

            self.CRYOVALVE_OPENCLOSE.INTLK.UpdateColor(True)
        else:
            self.CRYOVALVE_OPENCLOSE.INTLK.UpdateColor(False)

        # if received_dic_c["data"]["FLAG"]["value"]["CRYOVALVE_OPENCLOSE"] != self.FLAG_buffer["CRYOVALVE_OPENCLOSE"]:
        #     self.CRYOVALVE_OPENCLOSE.Set.ButtonTransitionState(False)
        #     self.FLAG_buffer["CRYOVALVE_OPENCLOSE"] = received_dic_c["data"]["FLAG"]["value"]["CRYOVALVE_OPENCLOSE"]
        # else:
        #     pass
        if received_dic_c["data"]["FLAG"]["Busy"]["CRYOVALVE_OPENCLOSE"] == True:
            self.CRYOVALVE_OPENCLOSE.Set.ButtonTransitionState(False)

        elif received_dic_c["data"]["FLAG"]["Busy"]["CRYOVALVE_OPENCLOSE"] == False:
            self.CRYOVALVE_OPENCLOSE.Set.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["FLAG"]["INTLKD"]["CRYOVALVE_PV1201ACT"]:

            self.CRYOVALVE_PV1201ACT.INTLK.UpdateColor(True)
        else:
            self.CRYOVALVE_PV1201ACT.INTLK.UpdateColor(False)

        # if received_dic_c["data"]["FLAG"]["value"]["CRYOVALVE_PV1201ACT"] != self.FLAG_buffer["CRYOVALVE_PV1201ACT"]:
        #     self.CRYOVALVE_PV1201ACT.Set.ButtonTransitionState(False)
        #     self.FLAG_buffer["CRYOVALVE_PV1201ACT"] = received_dic_c["data"]["FLAG"]["value"]["CRYOVALVE_PV1201ACT"]
        # else:
        #     pass
        if received_dic_c["data"]["FLAG"]["Busy"]["CRYOVALVE_PV1201ACT"] == True:
            self.CRYOVALVE_PV1201ACT.Set.ButtonTransitionState(False)

        elif received_dic_c["data"]["FLAG"]["Busy"]["CRYOVALVE_PV1201ACT"] == False:
            self.CRYOVALVE_PV1201ACT.Set.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["FLAG"]["INTLKD"]["CRYOVALVE_PV2201ACT"]:

            self.CRYOVALVE_PV2201ACT.INTLK.UpdateColor(True)
        else:
            self.CRYOVALVE_PV2201ACT.INTLK.UpdateColor(False)

        # if received_dic_c["data"]["FLAG"]["value"]["CRYOVALVE_PV2201ACT"] != self.FLAG_buffer["CRYOVALVE_PV2201ACT"]:
        #     self.CRYOVALVE_PV2201ACT.Set.ButtonTransitionState(False)
        #     self.FLAG_buffer["CRYOVALVE_PV2201ACT"] = received_dic_c["data"]["FLAG"]["value"]["CRYOVALVE_PV2201ACT"]
        # else:
        #     pass
        if received_dic_c["data"]["FLAG"]["Busy"]["CRYOVALVE_PV2201ACT"] == True:
            self.CRYOVALVE_PV2201ACT.Set.ButtonTransitionState(False)

        elif received_dic_c["data"]["FLAG"]["Busy"]["CRYOVALVE_PV2201ACT"] == False:
            self.CRYOVALVE_PV2201ACT.Set.ButtonTransitionState(False)
        else:
            pass

        # if received_dic_c["data"]["Switch"]["OUT"]["PUMP3305"] != self.Switch_buffer["PUMP3305"]:
        #     self.PUMP3305.ButtonTransitionState(False)
        #     self.Switch_buffer["PUMP3305"] = received_dic_c["data"]["Switch"]["OUT"]["PUMP3305"]
        # else:
        #     pass

        #PIDLOOP part

        if received_dic_c["data"]["LOOPPID"]["Busy"]["SERVO3321"]:
            self.SERVO3321.ButtonTransitionState(True)
            self.SERVO3321.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["SERVO3321"]:
            self.SERVO3321.ButtonTransitionState(False)
            self.SERVO3321.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["SERVO3321"]:
            self.MFC1316.ButtonTransitionState(True)
            self.MFC1316.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["SERVO3321"]:
            self.MFC1316.ButtonTransitionState(False)
            self.MFC1316.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6225"]:
            self.HTR6225.ButtonTransitionState(True)
            self.HTR6225.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6225"]:
            self.HTR6225.ButtonTransitionState(False)
            self.HTR6225.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2123"]:
            self.HTR2123.ButtonTransitionState(True)
            self.HTR2123.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2123"]:
            self.HTR2123.ButtonTransitionState(False)
            self.HTR2123.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2124"]:
            self.HTR2124.ButtonTransitionState(True)
            self.HTR2124.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2124"]:
            self.HTR2124.ButtonTransitionState(False)
            self.HTR2124.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2125"]:
            self.HTR2125.ButtonTransitionState(True)
            self.HTR2125.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2125"]:
            self.HTR2125.ButtonTransitionState(False)
            self.HTR2125.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR1202"]:
            self.HTR1202.ButtonTransitionState(True)
            self.HTR1202.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR1202"]:
            self.HTR1202.ButtonTransitionState(False)
            self.HTR1202.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2203"]:
            self.HTR2203.ButtonTransitionState(True)
            self.HTR2203.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2203"]:
            self.HTR2203.ButtonTransitionState(False)
            self.HTR2203.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6202"]:
            self.HTR6202.ButtonTransitionState(True)
            self.HTR6202.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6202"]:
            self.HTR6202.ButtonTransitionState(False)
            self.HTR6202.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6206"]:
            self.HTR6206.ButtonTransitionState(True)
            self.HTR6206.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6206"]:
            self.HTR6206.ButtonTransitionState(False)
            self.HTR6206.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6210"]:
            self.HTR6210.ButtonTransitionState(True)
            self.HTR6210.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6210"]:
            self.HTR6210.ButtonTransitionState(False)
            self.HTR6210.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6223"]:
            self.HTR6223.ButtonTransitionState(True)
            self.HTR6223.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6223"]:
            self.HTR6223.ButtonTransitionState(False)
            self.HTR6223.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6224"]:
            self.HTR6224.ButtonTransitionState(True)
            self.HTR6224.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6224"]:
            self.HTR6224.ButtonTransitionState(False)
            self.HTR6224.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6219"]:
            self.HTR6219.ButtonTransitionState(True)
            self.HTR6219.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6219"]:
            self.HTR6219.ButtonTransitionState(False)
            self.HTR6219.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6221"]:
            self.HTR6221.ButtonTransitionState(True)
            self.HTR6221.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6221"]:
            self.HTR6221.ButtonTransitionState(False)
            self.HTR6221.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6214"]:
            self.HTR6214.ButtonTransitionState(True)
            self.HTR6214.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6214"]:
            self.HTR6214.ButtonTransitionState(False)
            self.HTR6214.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass










        # intlck window A button

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT2118_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_HI_INTLK"]:
                self.INTLCKWindow.TT2118_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT2118_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT2118_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT2118_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_HI_INTLK"] != self.INTLK_A_DIC_buffer["TT2118_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_HI_INTLK"]:
                    self.INTLCKWindow.TT2118_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT2118_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT2118_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_HI_INTLK"]
            else:
                pass


        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT2118_LO_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_LO_INTLK"]:
                self.INTLCKWindow.TT2118_LO_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT2118_LO_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT2118_LO_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_LO_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT2118_LO_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_LO_INTLK"] != self.INTLK_A_DIC_buffer["TT2118_LO_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_LO_INTLK"]:
                    self.INTLCKWindow.TT2118_LO_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT2118_LO_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT2118_LO_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_LO_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT4306_LO_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_LO_INTLK"]:
                self.INTLCKWindow.PT4306_LO_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT4306_LO_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT4306_LO_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_LO_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT4306_LO_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_LO_INTLK"] != self.INTLK_A_DIC_buffer["PT4306_LO_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_LO_INTLK"]:
                    self.INTLCKWindow.PT4306_LO_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT4306_LO_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT4306_LO_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_LO_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT5304_LO_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT5304_LO_INTLK"]:
                self.INTLCKWindow.PT5304_LO_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT5304_LO_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT5304_LO_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT5304_LO_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT5304_LO_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT5304_LO_INTLK"] != self.INTLK_A_DIC_buffer["PT5304_LO_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT5304_LO_INTLK"]:
                    self.INTLCKWindow.PT5304_LO_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT5304_LO_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT5304_LO_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT5304_LO_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT4306_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_HI_INTLK"]:
                self.INTLCKWindow.PT4306_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT4306_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT4306_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT4306_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_HI_INTLK"] != self.INTLK_A_DIC_buffer["PT4306_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_HI_INTLK"]:
                    self.INTLCKWindow.PT4306_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT4306_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT4306_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_HI_INTLK"]
            else:
                pass

        #

        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT6302_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT6302_HI_INTLK"]:
                self.INTLCKWindow.PT6302_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT6302_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT6302_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT6302_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT6302_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT6302_HI_INTLK"] != self.INTLK_A_DIC_buffer["PT6302_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT6302_HI_INTLK"]:
                    self.INTLCKWindow.PT6302_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT6302_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT6302_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT6302_HI_INTLK"]
            else:
                pass


        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT6306_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT6306_HI_INTLK"]:
                self.INTLCKWindow.PT6306_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT6306_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT6306_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT6306_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT6306_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT6306_HI_INTLK"] != self.INTLK_A_DIC_buffer["PT6306_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT6306_HI_INTLK"]:
                    self.INTLCKWindow.PT6306_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT6306_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT6306_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT6306_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT2121_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT2121_HI_INTLK"]:
                self.INTLCKWindow.PT2121_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT2121_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT2121_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT2121_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT2121_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT2121_HI_INTLK"] != self.INTLK_A_DIC_buffer["PT2121_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT2121_HI_INTLK"]:
                    self.INTLCKWindow.PT2121_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT2121_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT2121_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT2121_HI_INTLK"]
            else:
                pass
        #


        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT4322_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HI_INTLK"]:
                self.INTLCKWindow.PT4322_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT4322_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT4322_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT4322_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HI_INTLK"] != self.INTLK_A_DIC_buffer["PT4322_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HI_INTLK"]:
                    self.INTLCKWindow.PT4322_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT4322_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT4322_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT4322_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HIHI_INTLK"]:
                self.INTLCKWindow.PT4322_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT4322_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT4322_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT4322_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["PT4322_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HIHI_INTLK"]:
                    self.INTLCKWindow.PT4322_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT4322_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT4322_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HIHI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT4319_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HI_INTLK"]:
                self.INTLCKWindow.PT4319_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT4319_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT4319_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT4319_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HI_INTLK"] != self.INTLK_A_DIC_buffer["PT4319_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HI_INTLK"]:
                    self.INTLCKWindow.PT4319_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT4319_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT4319_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT4319_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HIHI_INTLK"]:
                self.INTLCKWindow.PT4319_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT4319_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT4319_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT4319_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["PT4319_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HIHI_INTLK"]:
                    self.INTLCKWindow.PT4319_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT4319_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT4319_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HIHI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT4325_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HI_INTLK"]:
                self.INTLCKWindow.PT4325_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT4325_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT4325_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT4325_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HI_INTLK"] != self.INTLK_A_DIC_buffer["PT4325_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HI_INTLK"]:
                    self.INTLCKWindow.PT4325_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT4325_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT4325_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["PT4325_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HIHI_INTLK"]:
                self.INTLCKWindow.PT4325_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PT4325_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["PT4325_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["PT4325_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["PT4325_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HIHI_INTLK"]:
                    self.INTLCKWindow.PT4325_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PT4325_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["PT4325_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HIHI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6203_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HI_INTLK"]:
                self.INTLCKWindow.TT6203_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6203_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6203_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6203_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HI_INTLK"] != self.INTLK_A_DIC_buffer["TT6203_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HI_INTLK"]:
                    self.INTLCKWindow.TT6203_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6203_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6203_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6207_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HI_INTLK"]:
                self.INTLCKWindow.TT6207_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6207_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6207_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6207_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HI_INTLK"] != self.INTLK_A_DIC_buffer["TT6207_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HI_INTLK"]:
                    self.INTLCKWindow.TT6207_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6207_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6207_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6211_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HI_INTLK"]:
                self.INTLCKWindow.TT6211_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6211_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6211_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6211_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HI_INTLK"] != self.INTLK_A_DIC_buffer["TT6211_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HI_INTLK"]:
                    self.INTLCKWindow.TT6211_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6211_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6211_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6213_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HI_INTLK"]:
                self.INTLCKWindow.TT6213_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6213_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6213_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6213_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HI_INTLK"] != self.INTLK_A_DIC_buffer["TT6213_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HI_INTLK"]:
                    self.INTLCKWindow.TT6213_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6213_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6213_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6222_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HI_INTLK"]:
                self.INTLCKWindow.TT6222_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6222_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6222_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6222_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HI_INTLK"] != self.INTLK_A_DIC_buffer["TT6222_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HI_INTLK"]:
                    self.INTLCKWindow.TT6222_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6222_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6222_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6407_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HI_INTLK"]:
                self.INTLCKWindow.TT6407_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6407_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6407_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6407_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HI_INTLK"] != self.INTLK_A_DIC_buffer["TT6407_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HI_INTLK"]:
                    self.INTLCKWindow.TT6407_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6407_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6407_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6408_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HI_INTLK"]:
                self.INTLCKWindow.TT6408_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6408_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6408_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6408_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HI_INTLK"] != self.INTLK_A_DIC_buffer["TT6408_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HI_INTLK"]:
                    self.INTLCKWindow.TT6408_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6408_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6408_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6409_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HI_INTLK"]:
                self.INTLCKWindow.TT6409_HI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6409_HI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6409_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6409_HI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HI_INTLK"] != self.INTLK_A_DIC_buffer["TT6409_HI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HI_INTLK"]:
                    self.INTLCKWindow.TT6409_HI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6409_HI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6409_HI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6203_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HIHI_INTLK"]:
                self.INTLCKWindow.TT6203_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6203_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6203_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6203_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["TT6203_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HIHI_INTLK"]:
                    self.INTLCKWindow.TT6203_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6203_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6203_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HIHI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6207_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HIHI_INTLK"]:
                self.INTLCKWindow.TT6207_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6207_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6207_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6207_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["TT6207_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HIHI_INTLK"]:
                    self.INTLCKWindow.TT6207_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6207_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6207_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HIHI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6211_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HIHI_INTLK"]:
                self.INTLCKWindow.TT6211_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6211_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6211_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6211_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["TT6211_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HIHI_INTLK"]:
                    self.INTLCKWindow.TT6211_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6211_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6211_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HIHI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6213_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HIHI_INTLK"]:
                self.INTLCKWindow.TT6213_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6213_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6213_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6213_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["TT6213_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HIHI_INTLK"]:
                    self.INTLCKWindow.TT6213_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6213_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6213_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HIHI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6222_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HIHI_INTLK"]:
                self.INTLCKWindow.TT6222_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6222_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6222_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6222_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["TT6222_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HIHI_INTLK"]:
                    self.INTLCKWindow.TT6222_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6222_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6222_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HIHI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6407_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HIHI_INTLK"]:
                self.INTLCKWindow.TT6407_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6407_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6407_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6407_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["TT6407_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HIHI_INTLK"]:
                    self.INTLCKWindow.TT6407_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6407_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6407_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HIHI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6408_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HIHI_INTLK"]:
                self.INTLCKWindow.TT6408_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6408_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6408_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6408_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["TT6408_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HIHI_INTLK"]:
                    self.INTLCKWindow.TT6408_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6408_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6408_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HIHI_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["TT6409_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HIHI_INTLK"]:
                self.INTLCKWindow.TT6409_HIHI_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TT6409_HIHI_INTLK.EN.ButtonRClicked()
            self.INTLK_A_DIC_buffer["TT6409_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HIHI_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["TT6409_HIHI_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HIHI_INTLK"] != self.INTLK_A_DIC_buffer["TT6409_HIHI_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HIHI_INTLK"]:
                    self.INTLCKWindow.TT6409_HIHI_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TT6409_HIHI_INTLK.EN.ButtonRClicked()
                self.INTLK_A_DIC_buffer["TT6409_HIHI_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HIHI_INTLK"]
            else:
                pass

        ## intlck window d

        if received_dic_c["data"]["INTLK_D"]["Busy"]["TS1_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["TS1_INTLK"]:
                self.INTLCKWindow.TS1_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TS1_INTLK.EN.ButtonRClicked()
            self.INTLK_D_DIC_buffer["TS1_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["TS1_INTLK"]
        elif not received_dic_c["data"]["INTLK_D"]["Busy"]["TS1_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["TS1_INTLK"] != self.INTLK_D_DIC_buffer["TS1_INTLK"]:
                if received_dic_c["data"]["INTLK_D"]["EN"]["TS1_INTLK"]:
                    self.INTLCKWindow.TS1_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TS1_INTLK.EN.ButtonRClicked()
                self.INTLK_D_DIC_buffer["TS1_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["TS1_INTLK"]
            else:
                pass


        if received_dic_c["data"]["INTLK_D"]["Busy"]["TS2_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["TS2_INTLK"]:
                self.INTLCKWindow.TS2_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TS2_INTLK.EN.ButtonRClicked()
            self.INTLK_D_DIC_buffer["TS2_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["TS2_INTLK"]
        elif not received_dic_c["data"]["INTLK_D"]["Busy"]["TS2_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["TS2_INTLK"] != self.INTLK_D_DIC_buffer["TS2_INTLK"]:
                if received_dic_c["data"]["INTLK_D"]["EN"]["TS2_INTLK"]:
                    self.INTLCKWindow.TS2_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TS2_INTLK.EN.ButtonRClicked()
                self.INTLK_D_DIC_buffer["TS2_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["TS2_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_D"]["Busy"]["TS3_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["TS3_INTLK"]:
                self.INTLCKWindow.TS3_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.TS3_INTLK.EN.ButtonRClicked()
            self.INTLK_D_DIC_buffer["TS3_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["TS3_INTLK"]
        elif not received_dic_c["data"]["INTLK_D"]["Busy"]["TS3_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["TS3_INTLK"] != self.INTLK_D_DIC_buffer["TS3_INTLK"]:
                if received_dic_c["data"]["INTLK_D"]["EN"]["TS3_INTLK"]:
                    self.INTLCKWindow.TS3_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.TS3_INTLK.EN.ButtonRClicked()
                self.INTLK_D_DIC_buffer["TS3_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["TS3_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_D"]["Busy"]["ES3347_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["ES3347_INTLK"]:
                self.INTLCKWindow.ES3347_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.ES3347_INTLK.EN.ButtonRClicked()
            self.INTLK_D_DIC_buffer["ES3347_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["ES3347_INTLK"]
        elif not received_dic_c["data"]["INTLK_D"]["Busy"]["ES3347_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["ES3347_INTLK"] != self.INTLK_D_DIC_buffer["ES3347_INTLK"]:
                if received_dic_c["data"]["INTLK_D"]["EN"]["ES3347_INTLK"]:
                    self.INTLCKWindow.ES3347_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.ES3347_INTLK.EN.ButtonRClicked()
                self.INTLK_D_DIC_buffer["ES3347_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["ES3347_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_D"]["Busy"]["PUMP3305_OL_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["PUMP3305_OL_INTLK"]:
                self.INTLCKWindow.PUMP3305_OL_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PUMP3305_OL_INTLK.EN.ButtonRClicked()
            self.INTLK_D_DIC_buffer["PUMP3305_OL_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["PUMP3305_OL_INTLK"]
        elif not received_dic_c["data"]["INTLK_D"]["Busy"]["PUMP3305_OL_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["PUMP3305_OL_INTLK"] != self.INTLK_D_DIC_buffer["PUMP3305_OL_INTLK"]:
                if received_dic_c["data"]["INTLK_D"]["EN"]["PUMP3305_OL_INTLK"]:
                    self.INTLCKWindow.PUMP3305_OL_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PUMP3305_OL_INTLK.EN.ButtonRClicked()
                self.INTLK_D_DIC_buffer["PUMP3305_OL_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["PUMP3305_OL_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_D"]["Busy"]["PU_PRIME_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["PU_PRIME_INTLK"]:
                self.INTLCKWindow.PU_PRIME_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.PU_PRIME_INTLK.EN.ButtonRClicked()
            self.INTLK_D_DIC_buffer["PU_PRIME_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["PU_PRIME_INTLK"]
        elif not received_dic_c["data"]["INTLK_D"]["Busy"]["PU_PRIME_INTLK"]:
            if received_dic_c["data"]["INTLK_D"]["EN"]["PU_PRIME_INTLK"] != self.INTLK_D_DIC_buffer["PU_PRIME_INTLK"]:
                if received_dic_c["data"]["INTLK_D"]["EN"]["PU_PRIME_INTLK"]:
                    self.INTLCKWindow.PU_PRIME_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.PU_PRIME_INTLK.EN.ButtonRClicked()
                self.INTLK_D_DIC_buffer["PU_PRIME_INTLK"] = received_dic_c["data"]["INTLK_D"]["EN"]["PU_PRIME_INTLK"]
            else:
                pass

        #UPS_UTILITY_INTLK, UPS_BATTERY_INTLK, LS2126_INTLK, LS2127_INTLK
        if received_dic_c["data"]["INTLK_A"]["Busy"]["UPS_UTILITY_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["UPS_UTILITY_INTLK"]:
                self.INTLCKWindow.UPS_UTILITY_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.UPS_UTILITY_INTLK.EN.ButtonRClicked()
            self.INTLK_D_DIC_buffer["UPS_UTILITY_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["UPS_UTILITY_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["UPS_UTILITY_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["UPS_UTILITY_INTLK"] != self.INTLK_D_DIC_buffer["UPS_UTILITY_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["UPS_UTILITY_INTLK"]:
                    self.INTLCKWindow.UPS_UTILITY_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.UPS_UTILITY_INTLK.EN.ButtonRClicked()
                self.INTLK_D_DIC_buffer["UPS_UTILITY_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["UPS_UTILITY_INTLK"]
            else:
                pass


        if received_dic_c["data"]["INTLK_A"]["Busy"]["UPS_BATTERY_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["UPS_BATTERY_INTLK"]:
                self.INTLCKWindow.UPS_BATTERY_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.UPS_BATTERY_INTLK.EN.ButtonRClicked()
            self.INTLK_D_DIC_buffer["UPS_BATTERY_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["UPS_BATTERY_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["UPS_BATTERY_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["UPS_BATTERY_INTLK"] != self.INTLK_D_DIC_buffer["UPS_BATTERY_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["UPS_BATTERY_INTLK"]:
                    self.INTLCKWindow.UPS_BATTERY_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.UPS_BATTERY_INTLK.EN.ButtonRClicked()
                self.INTLK_D_DIC_buffer["UPS_BATTERY_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["UPS_BATTERY_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["LS2126_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["LS2126_INTLK"]:
                self.INTLCKWindow.LS2126_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.LS2126_INTLK.EN.ButtonRClicked()
            self.INTLK_D_DIC_buffer["LS2126_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["LS2126_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["LS2126_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["LS2126_INTLK"] != self.INTLK_D_DIC_buffer["LS2126_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["LS2126_INTLK"]:
                    self.INTLCKWindow.LS2126_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.LS2126_INTLK.EN.ButtonRClicked()
                self.INTLK_D_DIC_buffer["LS2126_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["LS2126_INTLK"]
            else:
                pass

        if received_dic_c["data"]["INTLK_A"]["Busy"]["LS2127_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["LS2127_INTLK"]:
                self.INTLCKWindow.LS2127_INTLK.EN.ButtonLClicked()
            else:
                self.INTLCKWindow.LS2127_INTLK.EN.ButtonRClicked()
            self.INTLK_D_DIC_buffer["LS2127_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["LS2127_INTLK"]
        elif not received_dic_c["data"]["INTLK_A"]["Busy"]["LS2127_INTLK"]:
            if received_dic_c["data"]["INTLK_A"]["EN"]["LS2127_INTLK"] != self.INTLK_D_DIC_buffer["LS2127_INTLK"]:
                if received_dic_c["data"]["INTLK_A"]["EN"]["LS2127_INTLK"]:
                    self.INTLCKWindow.LS2127_INTLK.EN.ButtonLClicked()
                else:
                    self.INTLCKWindow.LS2127_INTLK.EN.ButtonRClicked()
                self.INTLK_D_DIC_buffer["LS2127_INTLK"] = received_dic_c["data"]["INTLK_A"]["EN"]["LS2127_INTLK"]
            else:
                pass
        #




        # set Valves' widget status



        if not received_dic_c["data"]["Valve"]["MAN"]["PV1344"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV1344"]:
                self.PV1344.Set.ButtonLClicked()
            else:
                self.PV1344.Set.ButtonRClicked()
            self.Valve_buffer["PV1344"] = received_dic_c["data"]["Valve"]["OUT"]["PV1344"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV1344"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV1344"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV1344"]:
                    self.PV1344.Set.ButtonLClicked()
                else:
                    self.PV1344.Set.ButtonRClicked()
                self.Valve_buffer["PV1344"] = received_dic_c["data"]["Valve"]["OUT"]["PV1344"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV1344"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV1344"] != self.Valve_buffer["PV1344"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV1344"]:
                        self.PV1344.Set.ButtonLClicked()
                    else:
                        self.PV1344.Set.ButtonRClicked()
                    self.Valve_buffer["PV1344"] = received_dic_c["data"]["Valve"]["OUT"]["PV1344"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["PV4307"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV4307"]:
                self.PV4307.Set.ButtonLClicked()
            else:
                self.PV4307.Set.ButtonRClicked()
            self.Valve_buffer["PV4307"] = received_dic_c["data"]["Valve"]["OUT"]["PV4307"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV4307"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV4307"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4307"]:
                    self.PV4307.Set.ButtonLClicked()
                else:
                    self.PV4307.Set.ButtonRClicked()
                self.Valve_buffer["PV4307"] = received_dic_c["data"]["Valve"]["OUT"]["PV4307"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV4307"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4307"] != self.Valve_buffer["PV4307"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV4307"]:
                        self.PV4307.Set.ButtonLClicked()
                    else:
                        self.PV4307.Set.ButtonRClicked()
                    self.Valve_buffer["PV4307"] = received_dic_c["data"]["Valve"]["OUT"]["PV4307"]
                else:
                    pass


        if not received_dic_c["data"]["Valve"]["MAN"]["PV4308"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV4308"]:
                self.PV4308.Set.ButtonLClicked()
            else:
                self.PV4308.Set.ButtonRClicked()
            self.Valve_buffer["PV4308"] = received_dic_c["data"]["Valve"]["OUT"]["PV4308"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV4308"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV4308"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4308"]:
                    self.PV4308.Set.ButtonLClicked()
                else:
                    self.PV4308.Set.ButtonRClicked()
                self.Valve_buffer["PV4308"] = received_dic_c["data"]["Valve"]["OUT"]["PV4308"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV4308"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4308"] != self.Valve_buffer["PV4308"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV4308"]:
                        self.PV4308.Set.ButtonLClicked()
                    else:
                        self.PV4308.Set.ButtonRClicked()
                    self.Valve_buffer["PV4308"] = received_dic_c["data"]["Valve"]["OUT"]["PV4308"]
                else:
                    pass





        if not received_dic_c["data"]["Valve"]["MAN"]["PV4317"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV4317"]:
                self.PV4317.Set.ButtonLClicked()
            else:
                self.PV4317.Set.ButtonRClicked()
            self.Valve_buffer["PV4317"] = received_dic_c["data"]["Valve"]["OUT"]["PV4317"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV4317"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV4317"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4317"]:
                    self.PV4317.Set.ButtonLClicked()
                else:
                    self.PV4317.Set.ButtonRClicked()
                self.Valve_buffer["PV4317"] = received_dic_c["data"]["Valve"]["OUT"]["PV4317"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV4317"]:
            #     print("PV4317", received_dic_c["data"]["Valve"]["OUT"]["PV4317"] != self.Valve_buffer["PV4317"])
            #     print("OUT", received_dic_c["data"]["Valve"]["OUT"]["PV4317"])
            #     print("Buffer", self.Valve_buffer["PV4317"])
                if received_dic_c["data"]["Valve"]["OUT"]["PV4317"] != self.Valve_buffer["PV4317"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV4317"]:
                        self.PV4317.Set.ButtonLClicked()
                    else:
                        self.PV4317.Set.ButtonRClicked()
                    self.Valve_buffer["PV4317"] = received_dic_c["data"]["Valve"]["OUT"]["PV4317"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["PV4318"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV4318"]:
                self.PV4318.Set.ButtonLClicked()
            else:
                self.PV4318.Set.ButtonRClicked()
            self.Valve_buffer["PV4318"] = received_dic_c["data"]["Valve"]["OUT"]["PV4318"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV4318"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV4318"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4318"]:
                    self.PV4318.Set.ButtonLClicked()
                else:
                    self.PV4318.Set.ButtonRClicked()
                self.Valve_buffer["PV4318"] = received_dic_c["data"]["Valve"]["OUT"]["PV4318"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV4318"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4318"] != self.Valve_buffer["PV4318"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV4318"]:
                        self.PV4318.Set.ButtonLClicked()
                    else:
                        self.PV4318.Set.ButtonRClicked()
                    self.Valve_buffer["PV4318"] = received_dic_c["data"]["Valve"]["OUT"]["PV4318"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["PV4321"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV4321"]:
                self.PV4321.Set.ButtonLClicked()
            else:
                self.PV4321.Set.ButtonRClicked()
            self.Valve_buffer["PV4321"] = received_dic_c["data"]["Valve"]["OUT"]["PV4321"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV4321"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV4321"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4321"]:
                    self.PV4321.Set.ButtonLClicked()
                else:
                    self.PV4321.Set.ButtonRClicked()
                self.Valve_buffer["PV4321"] = received_dic_c["data"]["Valve"]["OUT"]["PV4321"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV4321"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4321"] != self.Valve_buffer["PV4321"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV4321"]:
                        self.PV4321.Set.ButtonLClicked()
                    else:
                        self.PV4321.Set.ButtonRClicked()
                    self.Valve_buffer["PV4321"] = received_dic_c["data"]["Valve"]["OUT"]["PV4321"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["PV4324"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV4324"]:
                self.PV4324.Set.ButtonLClicked()
            else:
                self.PV4324.Set.ButtonRClicked()
            self.Valve_buffer["PV4324"] = received_dic_c["data"]["Valve"]["OUT"]["PV4324"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV4324"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV4324"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4324"]:
                    self.PV4324.Set.ButtonLClicked()
                else:
                    self.PV4324.Set.ButtonRClicked()
                self.Valve_buffer["PV4324"] = received_dic_c["data"]["Valve"]["OUT"]["PV4324"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV4324"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4324"] != self.Valve_buffer["PV4324"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV4324"]:
                        self.PV4324.Set.ButtonLClicked()
                    else:
                        self.PV4324.Set.ButtonRClicked()
                    self.Valve_buffer["PV4324"] = received_dic_c["data"]["Valve"]["OUT"]["PV4324"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["PV5305"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV5305"]:
                self.PV5305.Set.ButtonLClicked()
            else:
                self.PV5305.Set.ButtonRClicked()
            self.Valve_buffer["PV5305"] = received_dic_c["data"]["Valve"]["OUT"]["PV5305"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV5305"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV5305"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV5305"]:
                    self.PV5305.Set.ButtonLClicked()
                else:
                    self.PV5305.Set.ButtonRClicked()
                self.Valve_buffer["PV5305"] = received_dic_c["data"]["Valve"]["OUT"]["PV5305"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV5305"]:

                if received_dic_c["data"]["Valve"]["OUT"]["PV5305"] != self.Valve_buffer["PV5305"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV5305"]:
                        self.PV5305.Set.ButtonLClicked()
                    else:
                        self.PV5305.Set.ButtonRClicked()
                    self.Valve_buffer["PV5305"] = received_dic_c["data"]["Valve"]["OUT"]["PV5305"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["PV5306"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV5306"]:
                self.PV5306.Set.ButtonLClicked()
            else:
                self.PV5306.Set.ButtonRClicked()
            self.Valve_buffer["PV5306"] = received_dic_c["data"]["Valve"]["OUT"]["PV5306"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV5306"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV5306"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV5306"]:
                    self.PV5306.Set.ButtonLClicked()
                else:
                    self.PV5306.Set.ButtonRClicked()
                self.Valve_buffer["PV5306"] = received_dic_c["data"]["Valve"]["OUT"]["PV5306"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV5306"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV5306"] != self.Valve_buffer["PV5306"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV5306"]:
                        self.PV5306.Set.ButtonLClicked()
                    else:
                        self.PV5306.Set.ButtonRClicked()
                    self.Valve_buffer["PV5306"] = received_dic_c["data"]["Valve"]["OUT"]["PV5306"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["PV5307"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV5307"]:
                self.PV5307.Set.ButtonLClicked()
            else:
                self.PV5307.Set.ButtonRClicked()
            self.Valve_buffer["PV5307"] = received_dic_c["data"]["Valve"]["OUT"]["PV5307"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV5307"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV5307"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV5307"]:
                    self.PV5307.Set.ButtonLClicked()
                else:
                    self.PV5307.Set.ButtonRClicked()
                self.Valve_buffer["PV5307"] = received_dic_c["data"]["Valve"]["OUT"]["PV5307"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV5307"]:

                if received_dic_c["data"]["Valve"]["OUT"]["PV5307"] != self.Valve_buffer["PV5307"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV5307"]:
                        self.PV5307.Set.ButtonLClicked()
                    else:
                        self.PV5307.Set.ButtonRClicked()
                    self.Valve_buffer["PV5307"] = received_dic_c["data"]["Valve"]["OUT"]["PV5307"]
                else:
                    pass


        if not received_dic_c["data"]["Valve"]["MAN"]["PV5309"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV5309"]:
                self.PV5309.Set.ButtonLClicked()
            else:
                self.PV5309.Set.ButtonRClicked()
            self.Valve_buffer["PV5309"] = received_dic_c["data"]["Valve"]["OUT"]["PV5309"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV5309"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV5309"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV5309"]:
                    self.PV5309.Set.ButtonLClicked()
                else:
                    self.PV5309.Set.ButtonRClicked()
                self.Valve_buffer["PV5309"] = received_dic_c["data"]["Valve"]["OUT"]["PV5309"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV5309"]:

                if received_dic_c["data"]["Valve"]["OUT"]["PV5309"] != self.Valve_buffer["PV5309"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV5309"]:
                        self.PV5309.Set.ButtonLClicked()
                    else:
                        self.PV5309.Set.ButtonRClicked()
                    self.Valve_buffer["PV5309"] = received_dic_c["data"]["Valve"]["OUT"]["PV5309"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["SV3307"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV3307"]:
                self.SV3307.Set.ButtonLClicked()
            else:
                self.SV3307.Set.ButtonRClicked()
            self.Valve_buffer["SV3307"] = received_dic_c["data"]["Valve"]["OUT"]["SV3307"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV3307"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV3307"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV3307"]:
                    self.SV3307.Set.ButtonLClicked()
                else:
                    self.SV3307.Set.ButtonRClicked()
                self.Valve_buffer["SV3307"] = received_dic_c["data"]["Valve"]["OUT"]["SV3307"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV3307"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV3307"] != self.Valve_buffer["SV3307"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV3307"]:
                        self.SV3307.Set.ButtonLClicked()
                    else:
                        self.SV3307.Set.ButtonRClicked()
                    self.Valve_buffer["SV3307"] = received_dic_c["data"]["Valve"]["OUT"]["SV3307"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["SV3310"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV3310"]:
                self.SV3310.Set.ButtonLClicked()
            else:
                self.SV3310.Set.ButtonRClicked()
            self.Valve_buffer["SV3310"] = received_dic_c["data"]["Valve"]["OUT"]["SV3310"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV3310"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV3310"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV3310"]:
                    self.SV3310.Set.ButtonLClicked()
                else:
                    self.SV3310.Set.ButtonRClicked()
                self.Valve_buffer["SV3310"] = received_dic_c["data"]["Valve"]["OUT"]["SV3310"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV3310"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV3310"] != self.Valve_buffer["SV3310"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV3310"]:
                        self.SV3310.Set.ButtonLClicked()
                    else:
                        self.SV3310.Set.ButtonRClicked()
                    self.Valve_buffer["SV3310"] = received_dic_c["data"]["Valve"]["OUT"]["SV3310"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["SV3322"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV3322"]:
                self.SV3322.Set.ButtonLClicked()
            else:
                self.SV3322.Set.ButtonRClicked()
            self.Valve_buffer["SV3322"] = received_dic_c["data"]["Valve"]["OUT"]["SV3322"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV3322"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV3322"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV3322"]:
                    self.SV3322.Set.ButtonLClicked()
                else:
                    self.SV3322.Set.ButtonRClicked()
                self.Valve_buffer["SV3322"] = received_dic_c["data"]["Valve"]["OUT"]["SV3322"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV3322"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV3322"] != self.Valve_buffer["SV3322"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV3322"]:
                        self.SV3322.Set.ButtonLClicked()
                    else:
                        self.SV3322.Set.ButtonRClicked()
                    self.Valve_buffer["SV3322"] = received_dic_c["data"]["Valve"]["OUT"]["SV3322"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["SV3325"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV3325"]:
                self.SV3325.Set.ButtonLClicked()
            else:
                self.SV3325.Set.ButtonRClicked()
            self.Valve_buffer["SV3325"] = received_dic_c["data"]["Valve"]["OUT"]["SV3325"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV3325"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV3325"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV3325"]:
                    self.SV3325.Set.ButtonLClicked()
                else:
                    self.SV3325.Set.ButtonRClicked()
                self.Valve_buffer["SV3325"] = received_dic_c["data"]["Valve"]["OUT"]["SV3325"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV3325"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV3325"] != self.Valve_buffer["SV3325"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV3325"]:
                        self.SV3325.Set.ButtonLClicked()
                    else:
                        self.SV3325.Set.ButtonRClicked()
                    self.Valve_buffer["SV3325"] = received_dic_c["data"]["Valve"]["OUT"]["SV3325"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["SV3329"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV3329"]:
                self.SV3329.Set.ButtonLClicked()
            else:
                self.SV3329.Set.ButtonRClicked()
            self.Valve_buffer["SV3329"] = received_dic_c["data"]["Valve"]["OUT"]["SV3329"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV3329"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV3329"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV3329"]:
                    self.SV3329.Set.ButtonLClicked()
                else:
                    self.SV3329.Set.ButtonRClicked()
                self.Valve_buffer["SV3329"] = received_dic_c["data"]["Valve"]["OUT"]["SV3329"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV3329"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV3329"] != self.Valve_buffer["SV3329"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV3329"]:
                        self.SV3329.Set.ButtonLClicked()
                    else:
                        self.SV3329.Set.ButtonRClicked()
                    self.Valve_buffer["SV3329"] = received_dic_c["data"]["Valve"]["OUT"]["SV3329"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["SV4327"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV4327"]:
                self.SV4327.Set.ButtonLClicked()
            else:
                self.SV4327.Set.ButtonRClicked()
            self.Valve_buffer["SV4327"] = received_dic_c["data"]["Valve"]["OUT"]["SV4327"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV4327"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV4327"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4327"]:
                    self.SV4327.Set.ButtonLClicked()
                else:
                    self.SV4327.Set.ButtonRClicked()
                self.Valve_buffer["SV4327"] = received_dic_c["data"]["Valve"]["OUT"]["SV4327"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV4327"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4327"] != self.Valve_buffer["SV4327"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV4327"]:
                        self.SV4327.Set.ButtonLClicked()
                    else:
                        self.SV4327.Set.ButtonRClicked()
                    self.Valve_buffer["SV4327"] = received_dic_c["data"]["Valve"]["OUT"]["SV4327"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["SV4328"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV4328"]:
                self.SV4328.Set.ButtonLClicked()
            else:
                self.SV4328.Set.ButtonRClicked()
            self.Valve_buffer["SV4328"] = received_dic_c["data"]["Valve"]["OUT"]["SV4328"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV4328"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV4328"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4328"]:
                    self.SV4328.Set.ButtonLClicked()
                else:
                    self.SV4328.Set.ButtonRClicked()
                self.Valve_buffer["SV4328"] = received_dic_c["data"]["Valve"]["OUT"]["SV4328"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV4328"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4328"] != self.Valve_buffer["SV4328"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV4328"]:
                        self.SV4328.Set.ButtonLClicked()
                    else:
                        self.SV4328.Set.ButtonRClicked()
                    self.Valve_buffer["SV4328"] = received_dic_c["data"]["Valve"]["OUT"]["SV4328"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["SV4329"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV4329"]:
                self.SV4329.Set.ButtonLClicked()
            else:
                self.SV4329.Set.ButtonRClicked()
            self.Valve_buffer["SV4329"] = received_dic_c["data"]["Valve"]["OUT"]["SV4329"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV4329"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV4329"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4329"]:
                    self.SV4329.Set.ButtonLClicked()
                else:
                    self.SV4329.Set.ButtonRClicked()
                self.Valve_buffer["SV4329"] = received_dic_c["data"]["Valve"]["OUT"]["SV4329"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV4329"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4329"] != self.Valve_buffer["SV4329"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV4329"]:
                        self.SV4329.Set.ButtonLClicked()
                    else:
                        self.SV4329.Set.ButtonRClicked()
                    self.Valve_buffer["SV4329"] = received_dic_c["data"]["Valve"]["OUT"]["SV4329"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["SV4331"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV4331"]:
                self.SV4331.Set.ButtonLClicked()
            else:
                self.SV4331.Set.ButtonRClicked()
            self.Valve_buffer["SV4331"] = received_dic_c["data"]["Valve"]["OUT"]["SV4331"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV4331"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV4331"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4331"]:
                    self.SV4331.Set.ButtonLClicked()
                else:
                    self.SV4331.Set.ButtonRClicked()
                self.Valve_buffer["SV4331"] = received_dic_c["data"]["Valve"]["OUT"]["SV4331"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV4331"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4331"] != self.Valve_buffer["SV4331"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV4331"]:
                        self.SV4331.Set.ButtonLClicked()
                    else:
                        self.SV4331.Set.ButtonRClicked()
                    self.Valve_buffer["SV4331"] = received_dic_c["data"]["Valve"]["OUT"]["SV4331"]
                else:
                    pass


        if not received_dic_c["data"]["Valve"]["MAN"]["SV4332"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV4332"]:
                self.SV4332.Set.ButtonLClicked()
            else:
                self.SV4332.Set.ButtonRClicked()
            self.Valve_buffer["SV4332"] = received_dic_c["data"]["Valve"]["OUT"]["SV4332"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV4332"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV4332"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4332"]:
                    self.SV4332.Set.ButtonLClicked()
                else:
                    self.SV4332.Set.ButtonRClicked()
                self.Valve_buffer["SV4332"] = received_dic_c["data"]["Valve"]["OUT"]["SV4332"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV4332"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4332"] != self.Valve_buffer["SV4332"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV4332"]:
                        self.SV4332.Set.ButtonLClicked()
                    else:
                        self.SV4332.Set.ButtonRClicked()
                    self.Valve_buffer["SV4332"] = received_dic_c["data"]["Valve"]["OUT"]["SV4332"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["SV4337"]:
            if received_dic_c["data"]["Valve"]["OUT"]["SV4337"]:
                self.SV4337.Set.ButtonLClicked()
            else:
                self.SV4337.Set.ButtonRClicked()
            self.Valve_buffer["SV4337"] = received_dic_c["data"]["Valve"]["OUT"]["SV4337"]
        elif received_dic_c["data"]["Valve"]["MAN"]["SV4337"]:
            if received_dic_c["data"]["Valve"]["Busy"]["SV4337"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4337"]:
                    self.SV4337.Set.ButtonLClicked()
                else:
                    self.SV4337.Set.ButtonRClicked()
                self.Valve_buffer["SV4337"] = received_dic_c["data"]["Valve"]["OUT"]["SV4337"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["SV4337"]:
                if received_dic_c["data"]["Valve"]["OUT"]["SV4337"] != self.Valve_buffer["SV4337"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["SV4337"]:
                        self.SV4337.Set.ButtonLClicked()
                    else:
                        self.SV4337.Set.ButtonRClicked()
                    self.Valve_buffer["SV4337"] = received_dic_c["data"]["Valve"]["OUT"]["SV4337"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["HFSV3312"]:
            if received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"]:
                self.HFSV3312.Set.ButtonLClicked()
            else:
                self.HFSV3312.Set.ButtonRClicked()
            self.Valve_buffer["HFSV3312"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"]
        elif received_dic_c["data"]["Valve"]["MAN"]["HFSV3312"]:
            if received_dic_c["data"]["Valve"]["Busy"]["HFSV3312"]:
                if received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"]:
                    self.HFSV3312.Set.ButtonLClicked()
                else:
                    self.HFSV3312.Set.ButtonRClicked()
                self.Valve_buffer["HFSV3312"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["HFSV3312"]:
                if received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"] != self.Valve_buffer["HFSV3312"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"]:
                        self.HFSV3312.Set.ButtonLClicked()
                    else:
                        self.HFSV3312.Set.ButtonRClicked()
                    self.Valve_buffer["HFSV3312"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"]
                else:
                    pass




        if not received_dic_c["data"]["Valve"]["MAN"]["HFSV3323"]:
            if received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"]:
                self.HFSV3323.Set.ButtonLClicked()
            else:
                self.HFSV3323.Set.ButtonRClicked()
            self.Valve_buffer["HFSV3323"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"]
        elif received_dic_c["data"]["Valve"]["MAN"]["HFSV3323"]:
            if received_dic_c["data"]["Valve"]["Busy"]["HFSV3323"]:
                if received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"]:
                    self.HFSV3323.Set.ButtonLClicked()
                else:
                    self.HFSV3323.Set.ButtonRClicked()
                self.Valve_buffer["HFSV3323"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["HFSV3323"]:
                if received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"] != self.Valve_buffer["HFSV3323"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"]:
                        self.HFSV3323.Set.ButtonLClicked()
                    else:
                        self.HFSV3323.Set.ButtonRClicked()
                    self.Valve_buffer["HFSV3323"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"]
                else:
                    pass


        if not received_dic_c["data"]["Valve"]["MAN"]["HFSV3331"]:
            if received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"]:
                self.HFSV3331.Set.ButtonLClicked()
            else:
                self.HFSV3331.Set.ButtonRClicked()
            self.Valve_buffer["HFSV3331"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"]
        elif received_dic_c["data"]["Valve"]["MAN"]["HFSV3331"]:
            if received_dic_c["data"]["Valve"]["Busy"]["HFSV3331"]:
                if received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"]:
                    self.HFSV3331.Set.ButtonLClicked()
                else:
                    self.HFSV3331.Set.ButtonRClicked()
                self.Valve_buffer["HFSV3331"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["HFSV3331"]:
                if received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"] != self.Valve_buffer["HFSV3331"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"]:
                        self.HFSV3331.Set.ButtonLClicked()
                    else:
                        self.HFSV3331.Set.ButtonRClicked()
                    self.Valve_buffer["HFSV3331"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"]
                else:
                    pass



        #
        if not received_dic_c["data"]["Valve"]["MAN"]["CC9313_CONT"]:
            if received_dic_c["data"]["Valve"]["OUT"]["CC9313_CONT"]:
                self.CC9313_CONT.Set.ButtonLClicked()
            else:
                self.CC9313_CONT.Set.ButtonRClicked()
            self.Valve_buffer["CC9313_CONT"] = received_dic_c["data"]["Valve"]["OUT"]["CC9313_CONT"]
        elif received_dic_c["data"]["Valve"]["MAN"]["CC9313_CONT"]:
            if received_dic_c["data"]["Valve"]["Busy"]["CC9313_CONT"]:
                if received_dic_c["data"]["Valve"]["OUT"]["CC9313_CONT"]:
                    self.CC9313_CONT.Set.ButtonLClicked()
                else:
                    self.CC9313_CONT.Set.ButtonRClicked()
                self.Valve_buffer["CC9313_CONT"] = received_dic_c["data"]["Valve"]["OUT"]["CC9313_CONT"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["CC9313_CONT"]:
                if received_dic_c["data"]["Valve"]["OUT"]["CC9313_CONT"] != self.Valve_buffer["CC9313_CONT"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["CC9313_CONT"]:
                        self.CC9313_CONT.Set.ButtonLClicked()
                    else:
                        self.CC9313_CONT.Set.ButtonRClicked()
                    self.Valve_buffer["CC9313_CONT"] = received_dic_c["data"]["Valve"]["OUT"]["CC9313_CONT"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["PT_EN6306"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PT_EN6306"]:
                self.PT_EN6306.Set.ButtonLClicked()
            else:
                self.PT_EN6306.Set.ButtonRClicked()
            self.Valve_buffer["PT_EN6306"] = received_dic_c["data"]["Valve"]["OUT"]["PT_EN6306"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PT_EN6306"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PT_EN6306"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PT_EN6306"]:
                    self.PT_EN6306.Set.ButtonLClicked()
                else:
                    self.PT_EN6306.Set.ButtonRClicked()
                self.Valve_buffer["PT_EN6306"] = received_dic_c["data"]["Valve"]["OUT"]["PT_EN6306"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PT_EN6306"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PT_EN6306"] != self.Valve_buffer["PT_EN6306"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PT_EN6306"]:
                        self.PT_EN6306.Set.ButtonLClicked()
                    else:
                        self.PT_EN6306.Set.ButtonRClicked()
                    self.Valve_buffer["PT_EN6306"] = received_dic_c["data"]["Valve"]["OUT"]["PT_EN6306"]
                else:
                    pass

        if not received_dic_c["data"]["Valve"]["MAN"]["PV4345"]:
            if received_dic_c["data"]["Valve"]["OUT"]["PV4345"]:
                self.PV4345.Set.ButtonLClicked()
            else:
                self.PV4345.Set.ButtonRClicked()
            self.Valve_buffer["PV4345"] = received_dic_c["data"]["Valve"]["OUT"]["PV4345"]
        elif received_dic_c["data"]["Valve"]["MAN"]["PV4345"]:
            if received_dic_c["data"]["Valve"]["Busy"]["PV4345"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4345"]:
                    self.PV4345.Set.ButtonLClicked()
                else:
                    self.PV4345.Set.ButtonRClicked()
                self.Valve_buffer["PV4345"] = received_dic_c["data"]["Valve"]["OUT"]["PV4345"]
            elif not received_dic_c["data"]["Valve"]["Busy"]["PV4345"]:
                if received_dic_c["data"]["Valve"]["OUT"]["PV4345"] != self.Valve_buffer["PV4345"]:
                    if received_dic_c["data"]["Valve"]["OUT"]["PV4345"]:
                        self.PV4345.Set.ButtonLClicked()
                    else:
                        self.PV4345.Set.ButtonRClicked()
                    self.Valve_buffer["PV4345"] = received_dic_c["data"]["Valve"]["OUT"]["PV4345"]
                else:
                    pass


        # Valve icons
        if received_dic_c["data"]["Valve"]["OUT"]["PV1344"]:
            self.PV1344_icon.Turnon()
        else:
            self.PV1344_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["PV4307"]:
            self.PV4307_icon.Turnon()
        else:
            self.PV4307_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["PV4308"]:
            self.PV4308_icon.Turnon()
        else:
            self.PV4308_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["PV4317"]:
            self.PV4317_icon.Turnon()
        else:
            self.PV4317_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["PV4318"]:
            self.PV4318_icon.Turnon()
        else:
            self.PV4318_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["PV4321"]:
            self.PV4321_icon.Turnon()
        else:
            self.PV4321_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["PV4324"]:
            self.PV4324_icon.Turnon()
        else:
            self.PV4324_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["PV5305"]:
            self.PV5305_icon.Turnon()
        else:
            self.PV5305_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["PV5306"]:
            self.PV5306_icon.Turnon()
        else:
            self.PV5306_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["PV5307"]:
            self.PV5307_icon.Turnon()
        else:
            self.PV5307_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["PV5309"]:
            self.PV5309_icon.Turnon()
        else:
            self.PV5309_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV3307"]:
            self.SV3307_icon.Turnon()
        else:
            self.SV3307_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV3310"]:
            self.SV3310_icon.Turnon()
        else:
            self.SV3310_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV3322"]:
            self.SV3322_icon.Turnon()
        else:
            self.SV3322_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV3325"]:
            self.SV3325_icon.Turnon()
        else:
            self.SV3325_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV3329"]:
            self.SV3329_icon.Turnon()
        else:
            self.SV3329_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV4327"]:
            self.SV4327_icon.Turnon()
        else:
            self.SV4327_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV4328"]:
            self.SV4328_icon.Turnon()
        else:
            self.SV4328_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV4329"]:
            self.SV4329_icon.Turnon()
        else:
            self.SV4329_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV4331"]:
            self.SV4331_icon.Turnon()
        else:
            self.SV4331_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV4332"]:
            self.SV4332_icon.Turnon()
        else:
            self.SV4332_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["SV4337"]:
            self.SV4337_icon.Turnon()
        else:
            self.SV4337_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"]:
            self.HFSV3312_icon.Turnon()
        else:
            self.HFSV3312_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"]:
            self.HFSV3323_icon.Turnon()
        else:
            self.HFSV3323_icon.Turnoff()

        if received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"]:
            self.HFSV3331_icon.Turnon()
        else:
            self.HFSV3331_icon.Turnoff()



        if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]:
            self.PUMP3305_icon.Turnon()
        else:
            self.PUMP3305_icon.Turnoff()



        #FLAGs
        if received_dic_c["data"]["FLAG"]["Busy"]["MAN_TS"]:
            if received_dic_c["data"]["FLAG"]["value"]["MAN_TS"]:
                self.MAN_TS.Set.ButtonLClicked()
            else:
                self.MAN_TS.Set.ButtonRClicked()
        elif not received_dic_c["data"]["FLAG"]["Busy"]["MAN_TS"]:
            if received_dic_c["data"]["FLAG"]["value"]["MAN_TS"] != self.FLAG_buffer["MAN_TS"]:
                if received_dic_c["data"]["FLAG"]["value"]["MAN_TS"]:
                    self.MAN_TS.Set.ButtonLClicked()
                else:
                    self.MAN_TS.Set.ButtonRClicked()
                self.FLAG_buffer["MAN_TS"] = received_dic_c["data"]["FLAG"]["value"]["MAN_TS"]
            else:
                pass
        # print("display",received_dic_c["data"]["FLAG"]["value"]["MAN_TS"],datetime.datetime.now())



        if received_dic_c["data"]["FLAG"]["Busy"]["MAN_HYD"]:
            if received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"]:
                self.MAN_HYD.Set.ButtonLClicked()
            else:
                self.MAN_HYD.Set.ButtonRClicked()
        elif not received_dic_c["data"]["FLAG"]["Busy"]["MAN_HYD"]:
            if received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"] != self.FLAG_buffer["MAN_HYD"]:
                if received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"]:
                    self.MAN_HYD.Set.ButtonLClicked()
                else:
                    self.MAN_HYD.Set.ButtonRClicked()
                self.FLAG_buffer["MAN_HYD"] = received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"]
            else:
                pass
        

                
            
        # if received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"]:
        #     self.MAN_HYD.Set.ButtonLClicked()
        # else:
        #     self.MAN_HYD.Set.ButtonRClicked()


        if received_dic_c["data"]["FLAG"]["value"]["PCYCLE_AUTOCYCLE"]:
            self.PCYCLE_AUTOCYCLE.Set.ButtonLClicked()
        else:
            self.PCYCLE_AUTOCYCLE.Set.ButtonRClicked()

        #
        if received_dic_c["data"]["FLAG"]["value"]["CRYOVALVE_OPENCLOSE"]:
            self.CRYOVALVE_OPENCLOSE.Set.ButtonLClicked()
        else:
            self.CRYOVALVE_OPENCLOSE.Set.ButtonRClicked()

        if received_dic_c["data"]["FLAG"]["value"]["CRYOVALVE_PV1201ACT"]:
            self.CRYOVALVE_PV1201ACT.Set.ButtonLClicked()
        else:
            self.CRYOVALVE_PV1201ACT.Set.ButtonRClicked()

        if received_dic_c["data"]["FLAG"]["value"]["CRYOVALVE_PV2201ACT"]:
            self.CRYOVALVE_PV2201ACT.Set.ButtonLClicked()
        else:
            self.CRYOVALVE_PV2201ACT.Set.ButtonRClicked()
        # set LOOPPID double button status ON/OFF also the status in the subwindow



        if not received_dic_c["data"]["LOOPPID"]["MAN"]["SERVO3321"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"]:
                self.SERVO3321.LOOPPIDWindow.Mode.ButtonLClicked()
                self.SERVO3321.State.ButtonLClicked()
            else:
                self.SERVO3321.LOOPPIDWindow.Mode.ButtonRClicked()
                self.SERVO3321.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["SERVO3321"] = received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["SERVO3321"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["SERVO3321"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"]:
                    self.SERVO3321.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.SERVO3321.State.ButtonLClicked()
                else:
                    self.SERVO3321.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.SERVO3321.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["SERVO3321"] = received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["SERVO3321"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"] != self.LOOPPID_EN_buffer["SERVO3321"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"]:
                        self.SERVO3321.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.SERVO3321.State.ButtonLClicked()
                    else:
                        self.SERVO3321.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.SERVO3321.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["SERVO3321"] = received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"]
                else:
                    pass

        self.SERVO3321.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"])
        self.SERVO3321.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["MFC1316"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["MFC1316"]:
                self.MFC1316.LOOPPIDWindow.Mode.ButtonLClicked()
                self.MFC1316.State.ButtonLClicked()
            else:
                self.MFC1316.LOOPPIDWindow.Mode.ButtonRClicked()
                self.MFC1316.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["MFC1316"] = received_dic_c["data"]["LOOPPID"]["EN"]["MFC1316"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["MFC1316"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["MFC1316"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["MFC1316"]:
                    self.MFC1316.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.MFC1316.State.ButtonLClicked()
                else:
                    self.MFC1316.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.MFC1316.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["MFC1316"] = received_dic_c["data"]["LOOPPID"]["EN"]["MFC1316"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["MFC1316"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["MFC1316"] != self.LOOPPID_EN_buffer["MFC1316"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["MFC1316"]:
                        self.MFC1316.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.MFC1316.State.ButtonLClicked()
                    else:
                        self.MFC1316.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.MFC1316.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["MFC1316"] = received_dic_c["data"]["LOOPPID"]["EN"]["MFC1316"]
                else:
                    pass

        self.MFC1316.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["MFC1316"])
        self.MFC1316.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["MFC1316"])



        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6225"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"]:
                self.HTR6225.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR6225.State.ButtonLClicked()
            else:
                self.HTR6225.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR6225.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR6225"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6225"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6225"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"]:
                    self.HTR6225.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR6225.State.ButtonLClicked()
                else:
                    self.HTR6225.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR6225.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR6225"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6225"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"] != self.LOOPPID_EN_buffer["HTR6225"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"]:
                        self.HTR6225.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR6225.State.ButtonLClicked()
                    else:
                        self.HTR6225.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR6225.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR6225"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"]
                else:
                    pass

        self.HTR6225.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"])
        self.HTR6225.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2123"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"]:
                self.HTR2123.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR2123.State.ButtonLClicked()
            else:
                self.HTR2123.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR2123.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR2123"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2123"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2123"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"]:
                    self.HTR2123.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR2123.State.ButtonLClicked()
                else:
                    self.HTR2123.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR2123.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR2123"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2123"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"] != self.LOOPPID_EN_buffer["HTR2123"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"]:
                        self.HTR2123.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR2123.State.ButtonLClicked()
                    else:
                        self.HTR2123.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR2123.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR2123"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"]
                else:
                    pass

        self.HTR2123.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"])
        self.HTR2123.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2124"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"]:
                self.HTR2124.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR2124.State.ButtonLClicked()
            else:
                self.HTR2124.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR2124.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR2124"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2124"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2124"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"]:
                    self.HTR2124.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR2124.State.ButtonLClicked()
                else:
                    self.HTR2124.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR2124.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR2124"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2124"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"] != self.LOOPPID_EN_buffer["HTR2124"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"]:
                        self.HTR2124.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR2124.State.ButtonLClicked()
                    else:
                        self.HTR2124.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR2124.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR2124"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"]
                else:
                    pass

        self.HTR2124.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"])
        self.HTR2124.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2125"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"]:
                self.HTR2125.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR2125.State.ButtonLClicked()
            else:
                self.HTR2125.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR2125.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR2125"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2125"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2125"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"]:
                    self.HTR2125.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR2125.State.ButtonLClicked()
                else:
                    self.HTR2125.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR2125.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR2125"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2125"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"] != self.LOOPPID_EN_buffer["HTR2125"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"]:
                        self.HTR2125.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR2125.State.ButtonLClicked()
                    else:
                        self.HTR2125.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR2125.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR2125"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"]
                else:
                    pass

        self.HTR2125.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"])
        self.HTR2125.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR1202"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"]:
                self.HTR1202.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR1202.State.ButtonLClicked()
            else:
                self.HTR1202.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR1202.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR1202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR1202"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR1202"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"]:
                    self.HTR1202.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR1202.State.ButtonLClicked()
                else:
                    self.HTR1202.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR1202.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR1202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR1202"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"] != self.LOOPPID_EN_buffer["HTR1202"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"]:
                        self.HTR1202.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR1202.State.ButtonLClicked()
                    else:
                        self.HTR1202.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR1202.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR1202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"]
                else:
                    pass

        self.HTR1202.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"])
        self.HTR1202.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2203"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"]:
                self.HTR2203.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR2203.State.ButtonLClicked()
            else:
                self.HTR2203.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR2203.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR2203"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2203"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2203"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"]:
                    self.HTR2203.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR2203.State.ButtonLClicked()
                else:
                    self.HTR2203.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR2203.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR2203"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2203"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"] != self.LOOPPID_EN_buffer["HTR2203"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"]:
                        self.HTR2203.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR2203.State.ButtonLClicked()
                    else:
                        self.HTR2203.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR2203.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR2203"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"]
                else:
                    pass

        self.HTR2203.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"])
        self.HTR2203.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6202"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]:
                self.HTR6202.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR6202.State.ButtonLClicked()
            else:
                self.HTR6202.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR6202.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR6202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6202"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6202"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]:
                    self.HTR6202.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR6202.State.ButtonLClicked()
                else:
                    self.HTR6202.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR6202.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR6202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6202"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"] != self.LOOPPID_EN_buffer["HTR6202"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]:
                        self.HTR6202.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR6202.State.ButtonLClicked()
                    else:
                        self.HTR6202.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR6202.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR6202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]
                else:
                    pass

        self.HTR6202.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"])
        self.HTR6202.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6206"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"]:
                self.HTR6206.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR6206.State.ButtonLClicked()
            else:
                self.HTR6206.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR6206.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR6206"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6206"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6206"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"]:
                    self.HTR6206.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR6206.State.ButtonLClicked()
                else:
                    self.HTR6206.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR6206.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR6206"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6206"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"] != self.LOOPPID_EN_buffer["HTR6206"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"]:
                        self.HTR6206.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR6206.State.ButtonLClicked()
                    else:
                        self.HTR6206.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR6206.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR6206"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"]
                else:
                    pass

        self.HTR6206.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"])
        self.HTR6206.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6210"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"]:
                self.HTR6210.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR6210.State.ButtonLClicked()
            else:
                self.HTR6210.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR6210.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR6210"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6210"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6210"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"]:
                    self.HTR6210.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR6210.State.ButtonLClicked()
                else:
                    self.HTR6210.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR6210.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR6210"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6210"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"] != self.LOOPPID_EN_buffer["HTR6210"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"]:
                        self.HTR6210.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR6210.State.ButtonLClicked()
                    else:
                        self.HTR6210.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR6210.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR6210"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"]
                else:
                    pass

        self.HTR6210.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"])
        self.HTR6210.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6223"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"]:
                self.HTR6223.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR6223.State.ButtonLClicked()
            else:
                self.HTR6223.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR6223.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR6223"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6223"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6223"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"]:
                    self.HTR6223.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR6223.State.ButtonLClicked()
                else:
                    self.HTR6223.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR6223.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR6223"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6223"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"] != self.LOOPPID_EN_buffer["HTR6223"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"]:
                        self.HTR6223.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR6223.State.ButtonLClicked()
                    else:
                        self.HTR6223.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR6223.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR6223"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"]
                else:
                    pass

        self.HTR6223.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"])
        self.HTR6223.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6224"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"]:
                self.HTR6224.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR6224.State.ButtonLClicked()
            else:
                self.HTR6224.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR6224.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR6224"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6224"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6224"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"]:
                    self.HTR6224.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR6224.State.ButtonLClicked()
                else:
                    self.HTR6224.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR6224.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR6224"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6224"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"] != self.LOOPPID_EN_buffer["HTR6224"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"]:
                        self.HTR6224.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR6224.State.ButtonLClicked()
                    else:
                        self.HTR6224.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR6224.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR6224"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"]
                else:
                    pass

        self.HTR6224.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"])
        self.HTR6224.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6219"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"]:
                self.HTR6219.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR6219.State.ButtonLClicked()
            else:
                self.HTR6219.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR6219.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR6219"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6219"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6219"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"]:
                    self.HTR6219.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR6219.State.ButtonLClicked()
                else:
                    self.HTR6219.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR6219.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR6219"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6219"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"] != self.LOOPPID_EN_buffer["HTR6219"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"]:
                        self.HTR6219.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR6219.State.ButtonLClicked()
                    else:
                        self.HTR6219.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR6219.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR6219"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"]
                else:
                    pass

        self.HTR6219.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"])
        self.HTR6219.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"])


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6221"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"]:
                self.HTR6221.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR6221.State.ButtonLClicked()
            else:
                self.HTR6221.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR6221.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR6221"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6221"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6221"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"]:
                    self.HTR6221.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR6221.State.ButtonLClicked()
                else:
                    self.HTR6221.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR6221.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR6221"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6221"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"] != self.LOOPPID_EN_buffer["HTR6221"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"]:
                        self.HTR6221.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR6221.State.ButtonLClicked()
                    else:
                        self.HTR6221.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR6221.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR6221"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"]
                else:
                    pass

        self.HTR6221.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"])
        self.HTR6221.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"])

        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6214"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"]:
                self.HTR6214.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR6214.State.ButtonLClicked()
            else:
                self.HTR6214.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR6214.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR6214"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6214"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6214"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"]:
                    self.HTR6214.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR6214.State.ButtonLClicked()
                else:
                    self.HTR6214.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR6214.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR6214"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6214"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"] != self.LOOPPID_EN_buffer["HTR6214"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"]:
                        self.HTR6214.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR6214.State.ButtonLClicked()
                    else:
                        self.HTR6214.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR6214.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR6214"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"]
                else:
                    pass

        self.HTR6214.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"])
        self.HTR6214.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"])





        if not received_dic_c["data"]["LOOP2PT"]["MAN"]["PUMP3305"]:
            if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]:
                self.PUMP3305.LOOP2PTWindow.Mode.ButtonLClicked()
                self.PUMP3305.State.ButtonLClicked()
            else:
                self.PUMP3305.LOOP2PTWindow.Mode.ButtonRClicked()
                self.PUMP3305.State.ButtonRClicked()
            self.LOOP2PT_OUT_buffer["PUMP3305"] = received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]
        elif received_dic_c["data"]["LOOP2PT"]["MAN"]["PUMP3305"]:
            if received_dic_c["data"]["LOOP2PT"]["Busy"]["PUMP3305"]:
                if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]:
                    self.PUMP3305.LOOP2PTWindow.Mode.ButtonLClicked()
                    self.PUMP3305.State.ButtonLClicked()
                else:
                    self.PUMP3305.LOOP2PTWindow.Mode.ButtonRClicked()
                    self.PUMP3305.State.ButtonRClicked()
                self.LOOP2PT_OUT_buffer["PUMP3305"] = received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]
            elif not received_dic_c["data"]["LOOP2PT"]["Busy"]["PUMP3305"]:
                if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"] != self.LOOP2PT_OUT_buffer["PUMP3305"]:
                    if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]:
                        self.PUMP3305.LOOP2PTWindow.Mode.ButtonLClicked()
                        self.PUMP3305.State.ButtonLClicked()
                    else:
                        self.PUMP3305.LOOP2PTWindow.Mode.ButtonRClicked()
                        self.PUMP3305.State.ButtonRClicked()
                    self.LOOP2PT_OUT_buffer["PUMP3305"] = received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]
                else:
                    pass

        self.PUMP3305.ColorLabel(received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"])


        # set indicators value
        self.TT2118.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2118"])
        self.TT2119.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2119"])
        self.TT2440.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2440"])
        self.TT2401.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2401"])
        self.TT2402.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2402"])
        self.TT2403.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2403"])
        self.TT2404.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2404"])
        self.TT2405.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2405"])
        self.TT2406.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2406"])
        self.TT2407.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2407"])
        self.TT2408.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2408"])
        self.TT2409.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2409"])
        self.TT2410.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2410"])
        self.TT2411.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2411"])
        self.TT2412.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2412"])
        self.TT2413.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2413"])
        self.TT2414.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2414"])
        self.TT2415.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2415"])
        self.TT2416.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2416"])
        self.TT2417.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2417"])
        self.TT2418.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2418"])
        self.TT2419.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2419"])
        self.TT2420.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2420"])
        self.TT2421.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2421"])
        self.TT2422.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2422"])
        self.TT2423.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2423"])
        self.TT2424.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2424"])
        self.TT2425.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2425"])
        self.TT2426.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2426"])
        self.TT2427.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2427"])
        self.TT2428.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2428"])
        self.TT2429.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2429"])
        self.TT2430.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2430"])
        self.TT2431.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2431"])
        self.TT2432.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2432"])

        self.TT2435.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2435"])
        self.TT2436.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2436"])
        self.TT2437.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2437"])
        self.TT2438.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2438"])
        self.TT2439.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2439"])
        self.TT2430.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2430"])
        self.TT2441.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2441"])
        self.TT2442.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2442"])
        self.TT2443.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2443"])
        self.TT2444.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2444"])
        self.TT2445.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2445"])
        self.TT2446.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2446"])
        self.TT2447.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2447"])
        self.TT2448.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2448"])
        self.TT2449.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2449"])
        self.TT2450.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2450"])

        self.TT7401.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT7401"])
        self.TT7402.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT7402"])
        self.TT7403.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT7403"])
        self.TT7404.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT7404"])
        self.TT3401.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT3401"])

        self.PT1325.SetValue(received_dic_c["data"]["PT"]["value"]["PT1325"])
        self.PT1361.SetValue(received_dic_c["data"]["PT"]["value"]["PT1361"])
        self.PT2121.SetValue(received_dic_c["data"]["PT"]["value"]["PT2121"])
        self.PT2121Fluid.SetValue(received_dic_c["data"]["PT"]["value"]["PT2121"])
        self.PT2121Hy.SetValue(received_dic_c["data"]["PT"]["value"]["PT2121"])
        self.PT2316.SetValue(received_dic_c["data"]["PT"]["value"]["PT2316"])
        self.PT2330.SetValue(received_dic_c["data"]["PT"]["value"]["PT2330"])
        self.PT2335.SetValue(received_dic_c["data"]["PT"]["value"]["PT2335"])
        self.PT3308.SetValue(received_dic_c["data"]["PT"]["value"]["PT3308"])
        self.PT3309.SetValue(received_dic_c["data"]["PT"]["value"]["PT3309"])
        self.PT3311.SetValue(received_dic_c["data"]["PT"]["value"]["PT3311"])
        self.PT3314.SetValue(received_dic_c["data"]["PT"]["value"]["PT3314"])
        self.PT3320.SetValue(received_dic_c["data"]["PT"]["value"]["PT3320"])
        self.PT3332.SetValue(received_dic_c["data"]["PT"]["value"]["PT3332"])
        self.PT3333.SetValue(received_dic_c["data"]["PT"]["value"]["PT3333"])
        self.PT4306.SetValue(received_dic_c["data"]["PT"]["value"]["PT4306"])
        self.PT4315.SetValue(received_dic_c["data"]["PT"]["value"]["PT4315"])
        self.PT4319.SetValue(received_dic_c["data"]["PT"]["value"]["PT4319"])
        self.PT4322.SetValue(received_dic_c["data"]["PT"]["value"]["PT4322"])
        self.PT4325.SetValue(received_dic_c["data"]["PT"]["value"]["PT4325"])
        self.PT6302.SetExpValue(received_dic_c["data"]["PT"]["value"]["PT6302"])
        self.PT6306.SetExpValue(received_dic_c["data"]["PT"]["value"]["PT6306"])
        #
        self.PT1101_AVG.SetValue(received_dic_c["data"]["PT"]["value"]["PT1101_AVG"])
        self.PT2121_AVG.SetValue(received_dic_c["data"]["PT"]["value"]["PT2121_AVG"])
        self.PDIFF_PT2121PT1101.SetValue(received_dic_c["data"]["PT"]["value"]["PDIFF_PT2121PT1101"])
        self.PDIFF_PT2121PT1325.SetValue(received_dic_c["data"]["PT"]["value"]["PDIFF_PT2121PT1325"])
        self.CYL3334_LT3335_CF4PRESSCALC.SetValue(received_dic_c["data"]["PT"]["value"]["CYL3334_LT3335_CF4PRESSCALC"])
        #
        self.PT1101.SetValue(received_dic_c["data"]["PT"]["value"]["PT1101"])
        self.PT1101Fluid.SetValue(received_dic_c["data"]["PT"]["value"]["PT1101"])
        self.PT1101Hy.SetValue(received_dic_c["data"]["PT"]["value"]["PT1101"])
        self.PT5304.SetValue(received_dic_c["data"]["PT"]["value"]["PT5304"])


        self.LT3335.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["LT3335"])

        self.BFM4313.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["BFM4313"])
        # self.MFC1316.SetValue not given value
        self.MFC1316.LOOPPIDWindow.IN.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["MFC1316_IN"])
        self.CYL3334.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["CYL3334_FCALC"])

        self.PV1201_STATE.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["PV1201_STATE"])
        self.PV2201_STATE.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["PV2201_STATE"])
        self.LED1_OUT.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["LED1_OUT"])
        self.LED2_OUT.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["LED2_OUT"])
        self.LED3_OUT.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["LED3_OUT"])
        self.LED_MAX.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["LED_MAX"])

        self.LED1_OUT_2d.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["LED1_OUT"])
        self.LED2_OUT_2d.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["LED2_OUT"])
        self.LED3_OUT_2d.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["LED3_OUT"])
        self.LED_MAX_2d.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["LED_MAX"])

        self.LT2122.SetValue(received_dic_c["data"]["AD"]["value"]["LT2122"])
        self.LT2130.SetValue(received_dic_c["data"]["AD"]["value"]["LT2130"])




        self.TT4330.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT4330"])

        self.HTR6219.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6222"])
        self.HTR6219.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6222"])

        self.HTR6202.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6203"])
        self.HTR6202.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6203"])

        self.HTR6206.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6207"])
        self.HTR6206.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6207"])

        self.HTR6210.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6211"])
        self.HTR6210.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6211"])

        self.HTR6214.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6213"])
        self.HTR6214.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6213"])

        self.HTR6221.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6222"])
        self.HTR6221.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6222"])

        self.HTR6223.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6407"])
        self.HTR6223.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6407"])

        self.HTR6224.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6408"])
        self.HTR6224.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6408"])

        self.HTR6225.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6409"])
        self.HTR6225.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6409"])

        self.HTR2123.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2101"])
        self.HTR2123.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2101"])

        self.HTR2124.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2113"])
        self.HTR2124.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2113"])
        self.HTR2124.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2113"])

        self.HTR2125.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2111"])
        self.HTR2125.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2111"])
        self.HTR2125.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2111"])

        self.HTR1202.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6415"])
        self.HTR1202.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6415"])

        self.HTR2203.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6416"])
        self.HTR2203.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6416"])

        self.HTR6219.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6220"])
        # self.MFC1316.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT1332"])
        self.HTR6214.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6401"])
        self.HTR6202.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6404"])
        self.HTR6206.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6405"])
        self.HTR6210.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6406"])
        self.HTR6223.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6410"])
        self.HTR6224.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6411"])
        self.HTR6225.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6412"])
        self.HTR1202.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6413"])
        self.HTR2203.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6414"])

        #set indicator's value in 2d_tab
        self.TT2425_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2425"])
        self.TT2424_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2424"])
        self.TT2422_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2422"])
        self.TT2420_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2420"])
        self.TT2418_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2418"])
        self.TT2442_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2442"])
        self.TT2431_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2431"])
        self.TT2429_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2429"])
        self.TT2427_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2427"])
        self.TT2418_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2418"])
        self.TT2441_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2441"])
        self.TT2446_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2446"])
        self.TT2447_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2447"])
        self.TT2448_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2448"])
        self.TT2440_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2440"])
        self.TT2438_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2438"])
        self.TT2436_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2436"])
        self.TT2443_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2443"])
        self.TT2419_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2419"])
        self.TT2421_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2421"])
        self.TT2432_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2432"])
        self.TT2428_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2428"])
        self.TT2416_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2416"])
        self.TT2439_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2439"])
        self.TT2423_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2423"])
        self.TT2419_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2419"])
        self.TT2426_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2426"])
        self.TT2430_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2430"])
        self.TT2113_2d.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2113"])
        self.TT2450_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2450"])
        self.TT2444_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2444"])
        self.TT2445_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2445"])
        self.TT2437_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2437"])
        self.TT2435_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2435"])
        self.TT2449_2d.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2449"])


        self.SERVO3321.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["SERVO3321"])
        self.SERVO3321.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["SERVO3321"])
        self.SERVO3321.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["SERVO3321"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["SERVO3321"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["SERVO3321"]]:

            self.SERVO3321.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.SERVO3321.LOOPPIDWindow.SAT.UpdateColor(False)
        self.SERVO3321.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["SERVO3321"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["SERVO3321"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["SERVO3321"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["SERVO3321"]))
        self.SERVO3321.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"])
        self.SERVO3321.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["SERVO3321"])
        self.SERVO3321.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["SERVO3321"])
        self.SERVO3321.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["SERVO3321"])
        self.SERVO3321.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["SERVO3321"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["SERVO3321"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["SERVO3321"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["SERVO3321"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["SERVO3321"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["SERVO3321"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["SERVO3321"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["SERVO3321"]))
        self.SERVO3321.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["SERVO3321"])

        #
        self.MFC1316.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["MFC1316"])
        self.MFC1316.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["MFC1316"])
        self.MFC1316.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["MFC1316"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["MFC1316"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["MFC1316"]]:

            self.MFC1316.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.MFC1316.LOOPPIDWindow.SAT.UpdateColor(False)
        self.MFC1316.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["MFC1316"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["MFC1316"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["MFC1316"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["MFC1316"]))
        self.MFC1316.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["MFC1316"])
        self.MFC1316.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["MFC1316"])
        self.MFC1316.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["MFC1316"])
        self.MFC1316.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["MFC1316"])
        self.MFC1316.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["MFC1316"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["MFC1316"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["MFC1316"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["MFC1316"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["MFC1316"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["MFC1316"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["MFC1316"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["MFC1316"]))
        self.MFC1316.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["MFC1316"])


        self.HTR6225.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6225"])
        self.HTR6225.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6225"])
        self.HTR6225.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6225"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6225"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6225"]]:

            self.HTR6225.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR6225.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR6225.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6225"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6225"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6225"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6225"]))
        self.HTR6225.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"])
        self.HTR6225.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6225"])
        self.HTR6225.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6225"])
        self.HTR6225.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6225"])
        self.HTR6225.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6225"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6225"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6225"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6225"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6225"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6225"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6225"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6225"]))
        self.HTR6225.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6225"])


        self.HTR2123.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR2123"])
        self.HTR2123.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR2123"])
        self.HTR2123.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2123"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR2123"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR2123"]]:

            self.HTR2123.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR2123.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR2123.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2123"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2123"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2123"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2123"]))
        self.HTR2123.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"])
        self.HTR2123.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2123"])
        self.HTR2123.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR2123"])
        self.HTR2123.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR2123"])
        self.HTR2123.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2123"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2123"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2123"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2123"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR2123"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR2123"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR2123"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR2123"]))
        self.HTR2123.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2123"])



        self.HTR2124.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR2124"])
        self.HTR2124.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR2124"])
        self.HTR2124.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2124"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR2124"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR2124"]]:

            self.HTR2124.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR2124.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR2124.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2124"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2124"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2124"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2124"]))
        self.HTR2124.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"])
        self.HTR2124.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2124"])
        self.HTR2124.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR2124"])
        self.HTR2124.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR2124"])
        self.HTR2124.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2124"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2124"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2124"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2124"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR2124"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR2124"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR2124"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR2124"]))
        self.HTR2124.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2124"])



        self.HTR2125.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR2125"])
        self.HTR2125.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR2125"])
        self.HTR2125.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2125"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR2125"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR2125"]]:

            self.HTR2125.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR2125.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR2125.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2125"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2125"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2125"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2125"]))
        self.HTR2125.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"])
        self.HTR2125.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2125"])
        self.HTR2125.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR2125"])
        self.HTR2125.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR2125"])
        self.HTR2125.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2125"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2125"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2125"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2125"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR2125"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR2125"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR2125"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR2125"]))
        self.HTR2125.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2125"])



        self.HTR1202.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR1202"])
        self.HTR1202.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR1202"])
        self.HTR1202.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR1202"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR1202"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR1202"]]:

            self.HTR1202.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR1202.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR1202.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR1202"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR1202"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR1202"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR1202"]))
        self.HTR1202.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"])
        self.HTR1202.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR1202"])
        self.HTR1202.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR1202"])
        self.HTR1202.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR1202"])
        self.HTR1202.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR1202"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR1202"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR1202"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR1202"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR1202"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR1202"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR1202"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR1202"]))
        self.HTR1202.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR1202"])



        self.HTR2203.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR2203"])
        self.HTR2203.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR2203"])
        self.HTR2203.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2203"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR2203"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR2203"]]:

            self.HTR2203.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR2203.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR2203.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2203"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2203"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2203"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2203"]))
        self.HTR2203.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"])
        self.HTR2203.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2203"])
        self.HTR2203.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR2203"])
        self.HTR2203.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR2203"])
        self.HTR2203.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2203"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2203"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2203"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2203"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR2203"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR2203"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR2203"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR2203"]))
        self.HTR2203.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2203"])



        self.HTR6202.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6202"])
        self.HTR6202.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6202"])
        self.HTR6202.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6202"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6202"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6202"]]:

            self.HTR6202.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR6202.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR6202.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6202"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6202"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6202"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6202"]))
        self.HTR6202.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"])
        self.HTR6202.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6202"])
        self.HTR6202.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6202"])
        self.HTR6202.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6202"])
        self.HTR6202.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6202"]))
        self.HTR6202.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6202"])



        self.HTR6206.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6206"])
        self.HTR6206.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6206"])
        self.HTR6206.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6206"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6206"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6206"]]:

            self.HTR6206.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR6206.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR6206.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6206"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6206"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6206"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6206"]))
        self.HTR6206.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"])
        self.HTR6206.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6206"])
        self.HTR6206.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6206"])
        self.HTR6206.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6206"])
        self.HTR6206.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6206"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6206"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6206"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6206"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6206"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6206"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6206"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6206"]))
        self.HTR6206.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6206"])



        self.HTR6210.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6210"])
        self.HTR6210.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6210"])
        self.HTR6210.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6210"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6210"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6210"]]:

            self.HTR6210.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR6210.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR6210.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6210"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6210"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6210"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6210"]))
        self.HTR6210.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"])
        self.HTR6210.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6210"])
        self.HTR6210.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6210"])
        self.HTR6210.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6210"])
        self.HTR6210.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6210"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6210"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6210"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6210"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6210"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6210"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6210"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6210"]))
        self.HTR6210.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6210"])



        self.HTR6223.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6223"])
        self.HTR6223.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6223"])
        self.HTR6223.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6223"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6223"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6223"]]:

            self.HTR6223.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR6223.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR6223.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6223"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6223"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6223"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6223"]))
        self.HTR6223.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"])
        self.HTR6223.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6223"])
        self.HTR6223.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6223"])
        self.HTR6223.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6223"])
        self.HTR6223.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6223"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6223"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6223"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6223"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6223"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6223"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6223"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6223"]))
        self.HTR6223.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6223"])



        self.HTR6224.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6224"])
        self.HTR6224.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6224"])
        self.HTR6224.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6224"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6224"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6224"]]:

            self.HTR6224.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR6224.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR6224.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6224"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6224"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6224"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6224"]))
        self.HTR6224.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"])
        self.HTR6224.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6224"])
        self.HTR6224.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6224"])
        self.HTR6224.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6224"])
        self.HTR6224.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6224"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6224"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6224"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6224"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6224"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6224"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6224"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6224"]))
        self.HTR6224.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6224"])



        self.HTR6219.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6219"])
        self.HTR6219.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6219"])
        self.HTR6219.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6219"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6219"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6219"]]:

            self.HTR6219.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR6219.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR6219.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6219"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6219"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6219"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6219"]))
        self.HTR6219.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"])
        self.HTR6219.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6219"])
        self.HTR6219.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6219"])
        self.HTR6219.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6219"])
        self.HTR6219.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6219"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6219"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6219"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6219"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6219"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6219"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6219"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6219"]))
        self.HTR6219.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6219"])



        self.HTR6221.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6221"])
        self.HTR6221.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6221"])
        self.HTR6221.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6221"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6221"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6221"]]:

            self.HTR6221.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR6221.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR6221.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6221"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6221"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6221"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6221"]))
        self.HTR6221.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"])
        self.HTR6221.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6221"])
        self.HTR6221.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6221"])
        self.HTR6221.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6221"])
        self.HTR6221.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6221"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6221"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6221"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6221"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6221"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6221"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6221"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6221"]))
        self.HTR6221.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6221"])



        self.HTR6214.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6214"])
        self.HTR6214.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6214"])
        self.HTR6214.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6214"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6214"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6214"]]:

            self.HTR6214.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR6214.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR6214.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6214"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6214"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6214"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6214"]))
        self.HTR6214.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"])
        self.HTR6214.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6214"])
        self.HTR6214.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6214"])
        self.HTR6214.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6214"])
        self.HTR6214.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6214"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6214"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6214"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6214"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6214"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6214"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6214"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6214"]))
        self.HTR6214.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6214"])




        #LOOP2PT
        self.PUMP3305.LOOP2PTWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOP2PT"]["INTLKD"]["PUMP3305"])
        self.PUMP3305.LOOP2PTWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOP2PT"]["ERR"]["PUMP3305"])
        self.PUMP3305.LOOP2PTWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOP2PT"]["MAN"]["PUMP3305"])

        self.PUMP3305.LOOP2PTWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOP2PT"]["MODE0"]["PUMP3305"],
                                  received_dic_c["data"]["LOOP2PT"]["MODE1"]["PUMP3305"],
                                  received_dic_c["data"]["LOOP2PT"]["MODE2"]["PUMP3305"],
                                  received_dic_c["data"]["LOOP2PT"]["MODE3"]["PUMP3305"]))

        self.PUMP3305.LOOP2PTWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOP2PT"]["MODE0"]["PUMP3305"],
                               received_dic_c["data"]["LOOP2PT"]["MODE1"]["PUMP3305"],
                               received_dic_c["data"]["LOOP2PT"]["MODE2"]["PUMP3305"],
                               received_dic_c["data"]["LOOP2PT"]["MODE3"]["PUMP3305"],
                               -999,
                               received_dic_c["data"]["LOOP2PT"]["SET1"]["PUMP3305"],
                               received_dic_c["data"]["LOOP2PT"]["SET2"]["PUMP3305"],
                               received_dic_c["data"]["LOOP2PT"]["SET3"]["PUMP3305"]))
        # self.PUMP3305.Power.SetValue(
        #     received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"])

        #INTLCK indicator

        # intlck window a indicators
        # INTLCK indicator
        self.INTLCKWindow.TT2118_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT2118_HI_INTLK"])
        self.INTLCKWindow.TT2118_HI_INTLK.Indicator.UpdateColor(received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_HI_INTLK"])
        self.INTLCKWindow.TT2118_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT2118_HI_INTLK"])
        self.INTLCKWindow.TT2118_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT2118_HI_INTLK"])

        self.INTLCKWindow.TT2118_LO_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT2118_LO_INTLK"])
        self.INTLCKWindow.TT2118_LO_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT2118_LO_INTLK"])
        self.INTLCKWindow.TT2118_LO_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT2118_LO_INTLK"])
        self.INTLCKWindow.TT2118_LO_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT2118_LO_INTLK"])

        self.INTLCKWindow.PT4306_LO_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT4306_LO_INTLK"])
        self.INTLCKWindow.PT4306_LO_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_LO_INTLK"])
        self.INTLCKWindow.PT4306_LO_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT4306_LO_INTLK"])
        self.INTLCKWindow.PT4306_LO_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT4306_LO_INTLK"])

        self.INTLCKWindow.PT5304_LO_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT5304_LO_INTLK"])
        self.INTLCKWindow.PT5304_LO_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT5304_LO_INTLK"])
        self.INTLCKWindow.PT5304_LO_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT5304_LO_INTLK"])
        self.INTLCKWindow.PT5304_LO_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT5304_LO_INTLK"])


        self.INTLCKWindow.PT4306_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT4306_HI_INTLK"])
        self.INTLCKWindow.PT4306_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_HI_INTLK"])
        self.INTLCKWindow.PT4306_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT4306_HI_INTLK"])
        self.INTLCKWindow.PT4306_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT4306_HI_INTLK"])

        #PT6302_HI_INTLK, PT6306_HI_INTLK, PT2121_HI_INTLK
        self.INTLCKWindow.PT6302_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT6302_HI_INTLK"])
        self.INTLCKWindow.PT6302_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT6302_HI_INTLK"])
        self.INTLCKWindow.PT6302_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT6302_HI_INTLK"])
        self.INTLCKWindow.PT6302_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT6302_HI_INTLK"])

        self.INTLCKWindow.PT6306_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT6306_HI_INTLK"])
        self.INTLCKWindow.PT6306_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT6306_HI_INTLK"])
        self.INTLCKWindow.PT6306_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT6306_HI_INTLK"])
        self.INTLCKWindow.PT6306_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT6306_HI_INTLK"])

        self.INTLCKWindow.PT2121_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT2121_HI_INTLK"])
        self.INTLCKWindow.PT2121_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT2121_HI_INTLK"])
        self.INTLCKWindow.PT2121_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT2121_HI_INTLK"])
        self.INTLCKWindow.PT2121_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT2121_HI_INTLK"])
        #

        self.INTLCKWindow.PT4322_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT4322_HI_INTLK"])
        self.INTLCKWindow.PT4322_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HI_INTLK"])
        self.INTLCKWindow.PT4322_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT4322_HI_INTLK"])
        self.INTLCKWindow.PT4322_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT4322_HI_INTLK"])


        self.INTLCKWindow.PT4322_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT4322_HIHI_INTLK"])
        self.INTLCKWindow.PT4322_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT4322_HIHI_INTLK"])
        self.INTLCKWindow.PT4322_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT4322_HIHI_INTLK"])
        self.INTLCKWindow.PT4322_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT4322_HIHI_INTLK"])

        self.INTLCKWindow.PT4319_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT4319_HI_INTLK"])
        self.INTLCKWindow.PT4319_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HI_INTLK"])
        self.INTLCKWindow.PT4319_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT4319_HI_INTLK"])
        self.INTLCKWindow.PT4319_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT4319_HI_INTLK"])

        self.INTLCKWindow.PT4319_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT4319_HIHI_INTLK"])
        self.INTLCKWindow.PT4319_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT4319_HIHI_INTLK"])
        self.INTLCKWindow.PT4319_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT4319_HIHI_INTLK"])
        self.INTLCKWindow.PT4319_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT4319_HIHI_INTLK"])

        self.INTLCKWindow.PT4325_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT4325_HI_INTLK"])
        self.INTLCKWindow.PT4325_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HI_INTLK"])
        self.INTLCKWindow.PT4325_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT4325_HI_INTLK"])
        self.INTLCKWindow.PT4325_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT4325_HI_INTLK"])

        self.INTLCKWindow.PT4325_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT4325_HIHI_INTLK"])
        self.INTLCKWindow.PT4325_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT4325_HIHI_INTLK"])
        self.INTLCKWindow.PT4325_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT4325_HIHI_INTLK"])
        self.INTLCKWindow.PT4325_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT4325_HIHI_INTLK"])

        self.INTLCKWindow.TT6203_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6203_HI_INTLK"])
        self.INTLCKWindow.TT6203_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HI_INTLK"])
        self.INTLCKWindow.TT6203_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6203_HI_INTLK"])
        self.INTLCKWindow.TT6203_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6203_HI_INTLK"])

        self.INTLCKWindow.TT6207_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6207_HI_INTLK"])
        self.INTLCKWindow.TT6207_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HI_INTLK"])
        self.INTLCKWindow.TT6207_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6207_HI_INTLK"])
        self.INTLCKWindow.TT6207_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6207_HI_INTLK"])

        self.INTLCKWindow.TT6211_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6211_HI_INTLK"])
        self.INTLCKWindow.TT6211_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HI_INTLK"])
        self.INTLCKWindow.TT6211_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6211_HI_INTLK"])
        self.INTLCKWindow.TT6211_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6211_HI_INTLK"])

        self.INTLCKWindow.TT6213_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6213_HI_INTLK"])
        self.INTLCKWindow.TT6213_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HI_INTLK"])
        self.INTLCKWindow.TT6213_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6213_HI_INTLK"])
        self.INTLCKWindow.TT6213_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6213_HI_INTLK"])

        self.INTLCKWindow.TT6222_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6222_HI_INTLK"])
        self.INTLCKWindow.TT6222_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HI_INTLK"])
        self.INTLCKWindow.TT6222_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6222_HI_INTLK"])
        self.INTLCKWindow.TT6222_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6222_HI_INTLK"])

        self.INTLCKWindow.TT6407_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6407_HI_INTLK"])
        self.INTLCKWindow.TT6407_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HI_INTLK"])
        self.INTLCKWindow.TT6407_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6407_HI_INTLK"])
        self.INTLCKWindow.TT6407_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6407_HI_INTLK"])

        self.INTLCKWindow.TT6408_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6408_HI_INTLK"])
        self.INTLCKWindow.TT6408_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HI_INTLK"])
        self.INTLCKWindow.TT6408_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6408_HI_INTLK"])
        self.INTLCKWindow.TT6408_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6408_HI_INTLK"])

        self.INTLCKWindow.TT6409_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6409_HI_INTLK"])
        self.INTLCKWindow.TT6409_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HI_INTLK"])
        self.INTLCKWindow.TT6409_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6409_HI_INTLK"])
        self.INTLCKWindow.TT6409_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6409_HI_INTLK"])

        self.INTLCKWindow.TT6203_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6203_HIHI_INTLK"])
        self.INTLCKWindow.TT6203_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6203_HIHI_INTLK"])
        self.INTLCKWindow.TT6203_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6203_HIHI_INTLK"])
        self.INTLCKWindow.TT6203_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6203_HIHI_INTLK"])

        self.INTLCKWindow.TT6207_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6207_HIHI_INTLK"])
        self.INTLCKWindow.TT6207_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6207_HIHI_INTLK"])
        self.INTLCKWindow.TT6207_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6207_HIHI_INTLK"])
        self.INTLCKWindow.TT6207_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6207_HIHI_INTLK"])


        self.INTLCKWindow.TT6211_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6211_HIHI_INTLK"])
        self.INTLCKWindow.TT6211_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6211_HIHI_INTLK"])
        self.INTLCKWindow.TT6211_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6211_HIHI_INTLK"])
        self.INTLCKWindow.TT6211_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6211_HIHI_INTLK"])

        self.INTLCKWindow.TT6213_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6213_HIHI_INTLK"])
        self.INTLCKWindow.TT6213_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6213_HIHI_INTLK"])
        self.INTLCKWindow.TT6213_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6213_HIHI_INTLK"])
        self.INTLCKWindow.TT6213_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6213_HIHI_INTLK"])

        self.INTLCKWindow.TT6222_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6222_HIHI_INTLK"])
        self.INTLCKWindow.TT6222_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6222_HIHI_INTLK"])
        self.INTLCKWindow.TT6222_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6222_HIHI_INTLK"])
        self.INTLCKWindow.TT6222_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6222_HIHI_INTLK"])

        self.INTLCKWindow.TT6407_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6407_HIHI_INTLK"])
        self.INTLCKWindow.TT6407_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6407_HIHI_INTLK"])
        self.INTLCKWindow.TT6407_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6407_HIHI_INTLK"])
        self.INTLCKWindow.TT6407_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6407_HIHI_INTLK"])

        self.INTLCKWindow.TT6408_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6408_HIHI_INTLK"])
        self.INTLCKWindow.TT6408_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6408_HIHI_INTLK"])
        self.INTLCKWindow.TT6408_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6408_HIHI_INTLK"])
        self.INTLCKWindow.TT6408_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6408_HIHI_INTLK"])

        self.INTLCKWindow.TT6409_HIHI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["TT6409_HIHI_INTLK"])
        self.INTLCKWindow.TT6409_HIHI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["TT6409_HIHI_INTLK"])
        self.INTLCKWindow.TT6409_HIHI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["TT6409_HIHI_INTLK"])
        self.INTLCKWindow.TT6409_HIHI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["TT6409_HIHI_INTLK"])

        #intlck d window
        self.INTLCKWindow.TS1_INTLK.ColorLabel(received_dic_c["data"]["INTLK_D"]["value"]["TS1_INTLK"])
        self.INTLCKWindow.TS1_INTLK.Indicator.UpdateColor(received_dic_c["data"]["INTLK_D"]["EN"]["TS1_INTLK"])
        self.INTLCKWindow.TS1_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_D"]["COND"]["TS1_INTLK"])

        self.INTLCKWindow.TS2_INTLK.ColorLabel(received_dic_c["data"]["INTLK_D"]["value"]["TS2_INTLK"])
        self.INTLCKWindow.TS2_INTLK.Indicator.UpdateColor(received_dic_c["data"]["INTLK_D"]["EN"]["TS2_INTLK"])
        self.INTLCKWindow.TS2_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_D"]["COND"]["TS2_INTLK"])

        self.INTLCKWindow.TS3_INTLK.ColorLabel(received_dic_c["data"]["INTLK_D"]["value"]["TS3_INTLK"])
        self.INTLCKWindow.TS3_INTLK.Indicator.UpdateColor(received_dic_c["data"]["INTLK_D"]["EN"]["TS3_INTLK"])
        self.INTLCKWindow.TS3_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_D"]["COND"]["TS3_INTLK"])

        self.INTLCKWindow.PUMP3305_OL_INTLK.ColorLabel(received_dic_c["data"]["INTLK_D"]["value"]["PUMP3305_OL_INTLK"])
        self.INTLCKWindow.PUMP3305_OL_INTLK.Indicator.UpdateColor(received_dic_c["data"]["INTLK_D"]["EN"]["PUMP3305_OL_INTLK"])
        self.INTLCKWindow.PUMP3305_OL_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_D"]["COND"]["PUMP3305_OL_INTLK"])

        self.INTLCKWindow.ES3347_INTLK.ColorLabel(received_dic_c["data"]["INTLK_D"]["value"]["ES3347_INTLK"])
        self.INTLCKWindow.ES3347_INTLK.Indicator.UpdateColor(received_dic_c["data"]["INTLK_D"]["EN"]["ES3347_INTLK"])
        self.INTLCKWindow.ES3347_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_D"]["COND"]["ES3347_INTLK"])

        self.INTLCKWindow.PU_PRIME_INTLK.ColorLabel(received_dic_c["data"]["INTLK_D"]["value"]["PU_PRIME_INTLK"])
        self.INTLCKWindow.PU_PRIME_INTLK.Indicator.UpdateColor(received_dic_c["data"]["INTLK_D"]["EN"]["PU_PRIME_INTLK"])
        self.INTLCKWindow.PU_PRIME_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_D"]["COND"]["PU_PRIME_INTLK"])

        #UPS_UTILITY_INTLK, UPS_BATTERY_INTLK, LS2126_INTLK, LS2127_INTLK
        self.INTLCKWindow.UPS_UTILITY_INTLK.ColorLabel(received_dic_c["data"]["INTLK_A"]["value"]["UPS_UTILITY_INTLK"])
        self.INTLCKWindow.UPS_UTILITY_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["UPS_UTILITY_INTLK"])
        self.INTLCKWindow.UPS_UTILITY_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["UPS_UTILITY_INTLK"])

        self.INTLCKWindow.UPS_BATTERY_INTLK.ColorLabel(received_dic_c["data"]["INTLK_A"]["value"]["UPS_BATTERY_INTLK"])
        self.INTLCKWindow.UPS_BATTERY_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["UPS_BATTERY_INTLK"])
        self.INTLCKWindow.UPS_BATTERY_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["UPS_BATTERY_INTLK"])

        self.INTLCKWindow.LS2126_INTLK.ColorLabel(received_dic_c["data"]["INTLK_A"]["value"]["LS2126_INTLK"])
        self.INTLCKWindow.LS2126_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["LS2126_INTLK"])
        self.INTLCKWindow.LS2126_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["LS2126_INTLK"])

        self.INTLCKWindow.LS2127_INTLK.ColorLabel(received_dic_c["data"]["INTLK_A"]["value"]["LS2127_INTLK"])
        self.INTLCKWindow.LS2127_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["LS2127_INTLK"])
        self.INTLCKWindow.LS2127_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["LS2127_INTLK"])
        #


    @QtCore.Slot(object)
    def update_alarmwindow(self,list):
        # if len(dic)>0:
        #     print(dic)
        print(list[0])
        if True in list:
            print('list',True)
        else:
            print('list',False)

        self.AlarmButton.CollectAlarm(list)
        # print("Alarm Status=", self.AlarmButton.Button.Alarm)
        if self.AlarmButton.Button.Alarm:
            self.AlarmButton.ButtonAlarmSetSignal()
        else:
            self.AlarmButton.ButtonAlarmResetSignal()
            self.AlarmButton.SubWindow.ResetOrder()

class UpdateClient(QtCore.QThread):
    client_data_transport = QtCore.Signal(object)
    def __init__(self, commands, command_lock):
        super().__init__()

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = '127.0.0.1'
        self.port = 6666
        self.Running=False
        self.period = 1
        self.commands = commands
        self.command_lock = command_lock

        print("client is connecting to the socket server")

        self.receive_dic = copy.deepcopy(env.DIC_PACK)
        self.commands_package = pickle.dumps({})

    @QtCore.Slot()
    def run(self):
        self.Running = True

        while True:
            try:
                self.client_socket.connect((self.host, self.port))

                # Set a timeout for socket operations to 10 seconds
                self.client_socket.settimeout(10)
                while True:
                    # send commands
                    self.send_commands()
                    print("client commands sent")
                    received_data = self.receive_packed_data()

                    # Deserialize pickle data to a dictionary
                    data_dict = pickle.loads(received_data)
                    self.update_data(data_dict)


            except socket.timeout:
                print("Connection timed out. Restarting client...")
                self.client_socket.close()
                break
        self.run()

    @QtCore.Slot()
    def stop(self):
        self.Running = False
        self.client_socket.close()



    def update_data(self,message):
        #message mush be a dictionary
        self.receive_dic = message
        self.client_data_transport.emit(self.receive_dic)
    def receive_packed_data(self):
        data_length_bytes = self.client_socket.recv(4)
        data_length = struct.unpack('!I', data_length_bytes)[0]

        # Receive the serialized data in chunks
        received_data = b''
        while len(received_data) < data_length:
            chunk = self.client_socket.recv(min(1024, data_length - len(received_data)))
            if not chunk:
                break
            received_data += chunk
        return received_data

    def pack_data(self, conn):
        data_transfer = pickle.dumps(self.commands)

        # Send JSON data to the client
        conn.sendall(len(data_transfer).to_bytes(4, byteorder='big'))

        # Send the serialized data in chunks
        for i in range(0, len(data_transfer), 1024):
            chunk = data_transfer[i:i + 1024]
            conn.sendall(chunk)


    def send_commands(self):
        # claim that whether MAN_SET is True or false
        print("Commands are here", self.commands,datetime.datetime.now())
        self.pack_data(self.client_socket)
        with self.command_lock:
            self.commands.clear()
        print("finished sending commands")






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
