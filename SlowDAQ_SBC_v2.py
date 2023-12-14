"""
This is the main SlowDAQ code used to read/setproperties of the TPLC and PPLC

By: Mathieu Laurin

v0.1.0 Initial code 29/11/19 ML
v0.1.1 Read and write implemented 08/12/19 ML
v0.1.2 Alarm implemented 07/01/20 ML
v0.1.3 PLC online detection, poll PLCs only when values are updated, fix Centos window size bug 04/03/20 ML
"""

import os, sys, time, platform, datetime, random, pickle, cgitb, traceback, signal,copy


from PySide2 import QtWidgets, QtCore, QtGui

# from SlowDAQ_SBC_v2 import *
# from PLC import *
from PICOPW import VerifyPW
from SlowDAQWidgets_SBC_v2 import *
import zmq
import slowcontrol_env_cons as sec

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
        pixmap_thermalsyphon = QtGui.QPixmap(os.path.join(self.ImagePath, "Thermosyphon_v2.png"))
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
        self.SV4327.move(300*R, 450*R)

        self.SV4327_icon = Valve_image(self.ThermosyphonTab, mode="V")
        self.SV4327_icon.move(330 * R, 360 * R)

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
        self.SV4337.move(120*R, 330*R)

        self.SV4337_icon = Valve_image(self.ThermosyphonTab, mode="H")
        self.SV4337_icon.move(187 * R, 278 * R)

        self.PRV4333 = PnID_Alone(self.ThermosyphonTab)
        self.PRV4333.Label.setText("PRV4333")
        self.PRV4333.move(900*R, 650*R)

        self.PT6302 = Indicator(self.ThermosyphonTab)
        self.PT6302.Label.setText("PT6302")
        self.PT6302.move(2030*R, 690*R)
        self.PT6302.SetUnit(" bar")

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


        self.HTR6219 = LOOPPID_v2(self.ChamberTab)
        self.HTR6219.move(820*R, 120*R)
        self.HTR6219.Label.setText("HTR6219")
        self.HTR6219.LOOPPIDWindow.setWindowTitle("HTR6219")
        self.HTR6219.LOOPPIDWindow.Label.setText("HTR6219")
        self.HTR6219.LOOPPIDWindow.RTD1.Label.setText("TT6220")
        self.HTR6219.LOOPPIDWindow.RTD2.Label.setText("EMPTY")

        self.HTR6221 = LOOPPID_v2(self.ChamberTab)
        self.HTR6221.move(1250*R, 120*R)
        self.HTR6221.Label.setText("HTR6221")
        self.HTR6221.LOOPPIDWindow.setWindowTitle("HTR6221")
        self.HTR6221.LOOPPIDWindow.Label.setText("HTR6221")
        self.HTR6221.LOOPPIDWindow.RTD1.Label.setText("TT6222")
        self.HTR6221.LOOPPIDWindow.RTD2.Label.setText("EMPTY")



        self.HTR6214 = LOOPPID_v2(self.ChamberTab)
        self.HTR6214.move(1780*R, 145*R)
        self.HTR6214.Label.setText("HTR6214")
        self.HTR6214.LOOPPIDWindow.setWindowTitle("HTR6214")
        self.HTR6214.LOOPPIDWindow.Label.setText("HTR6214")
        self.HTR6214.LOOPPIDWindow.RTD1.Label.setText("TT6213")
        self.HTR6214.LOOPPIDWindow.RTD2.Label.setText("TT6401")

        self.HTR6202 = LOOPPID_v2(self.ChamberTab)
        self.HTR6202.move(1780*R, 485*R)
        self.HTR6202.Label.setText("HTR6202")
        self.HTR6202.LOOPPIDWindow.setWindowTitle("HTR6202")
        self.HTR6202.LOOPPIDWindow.Label.setText("HTR6202")
        self.HTR6202.LOOPPIDWindow.RTD1.Label.setText("TT6203")
        self.HTR6202.LOOPPIDWindow.RTD2.Label.setText("TT6404")

        self.HTR6206 = LOOPPID_v2(self.ChamberTab)
        self.HTR6206.move(1780*R, 585*R)
        self.HTR6206.Label.setText("HTR6206")
        self.HTR6206.LOOPPIDWindow.setWindowTitle("HTR6206")
        self.HTR6206.LOOPPIDWindow.Label.setText("HTR6206")
        self.HTR6206.LOOPPIDWindow.RTD1.Label.setText("TT6207")
        self.HTR6206.LOOPPIDWindow.RTD2.Label.setText("TT6405")

        self.HTR6210 = LOOPPID_v2(self.ChamberTab)
        self.HTR6210.move(1780*R, 685*R)
        self.HTR6210.Label.setText("HTR6210")
        self.HTR6210.LOOPPIDWindow.setWindowTitle("HTR6210")
        self.HTR6210.LOOPPIDWindow.Label.setText("HTR6210")
        self.HTR6210.LOOPPIDWindow.RTD1.Label.setText("TT6211")
        self.HTR6210.LOOPPIDWindow.RTD2.Label.setText("TT6406")

        self.HTR6223 = LOOPPID_v2(self.ChamberTab)
        self.HTR6223.move(1780*R, 785*R)
        self.HTR6223.Label.setText("HTR6223")
        self.HTR6223.LOOPPIDWindow.setWindowTitle("HTR6223")
        self.HTR6223.LOOPPIDWindow.Label.setText("HTR6223")
        self.HTR6223.LOOPPIDWindow.RTD1.Label.setText("TT6407")
        self.HTR6223.LOOPPIDWindow.RTD2.Label.setText("TT6410")

        self.HTR6224 = LOOPPID_v2(self.ChamberTab)
        self.HTR6224.move(1780*R, 885*R)
        self.HTR6224.Label.setText("HTR6224")
        self.HTR6224.LOOPPIDWindow.setWindowTitle("HTR6224")
        self.HTR6224.LOOPPIDWindow.Label.setText("HTR6224")
        self.HTR6224.LOOPPIDWindow.RTD1.Label.setText("TT6408")
        self.HTR6224.LOOPPIDWindow.RTD2.Label.setText("TT6411")

        self.HTR6225 = LOOPPID_v2(self.ChamberTab)

        self.HTR6225.move(1780*R, 985*R)
        self.HTR6225.Label.setText("HTR6225")
        self.HTR6225.LOOPPIDWindow.setWindowTitle("HTR6225")
        self.HTR6225.LOOPPIDWindow.Label.setText("HTR6225")
        self.HTR6225.LOOPPIDWindow.RTD1.Label.setText("TT6409")
        self.HTR6225.LOOPPIDWindow.RTD2.Label.setText("TT6412")

        self.HTR2123 = LOOPPID_v2(self.ChamberTab)
        self.HTR2123.move(670*R, 820*R)
        self.HTR2123.Label.setText("HTR2123")
        self.HTR2123.LOOPPIDWindow.setWindowTitle("HTR2123")
        self.HTR2123.LOOPPIDWindow.Label.setText("HTR2123")
        self.HTR2123.LOOPPIDWindow.RTD1.Label.setText("EMPTY")
        self.HTR2123.LOOPPIDWindow.RTD2.Label.setText("EMPTY")

        self.HTR2124 = LOOPPID_v2(self.ChamberTab)
        self.HTR2124.move(670*R, 820*R)
        self.HTR2124.Label.setText("HTR2124")
        self.HTR2124.LOOPPIDWindow.setWindowTitle("HTR2124")
        self.HTR2124.LOOPPIDWindow.Label.setText("HTR2124")
        self.HTR2124.LOOPPIDWindow.RTD1.Label.setText("EMPTY")
        self.HTR2124.LOOPPIDWindow.RTD2.Label.setText("EMPTY")

        self.HTR2125 = LOOPPID_v2(self.ChamberTab)
        self.HTR2125.move(1030*R, 730*R)
        self.HTR2125.Label.setText("HTR2125")
        self.HTR2125.LOOPPIDWindow.setWindowTitle("HTR2125")
        self.HTR2125.LOOPPIDWindow.Label.setText("HTR2125")
        self.HTR2125.LOOPPIDWindow.RTD1.Label.setText("EMPTY")
        self.HTR2125.LOOPPIDWindow.RTD2.Label.setText("EMPTY")

        self.PT1101 = Indicator(self.ChamberTab)
        self.PT1101.move(940*R, 990*R)
        self.PT1101.Label.setText("PT1101")
        self.PT1101.SetUnit(" bar")

        self.PT2121 = Indicator(self.ChamberTab)
        self.PT2121.move(1210*R, 990*R)
        self.PT2121.Label.setText("PT2121")
        self.PT2121.SetUnit(" bar")

        self.HTR1202 = LOOPPID_v2(self.ChamberTab)
        self.HTR1202.move(840*R, 1250*R)
        self.HTR1202.Label.setText("HTR1202")
        self.HTR1202.LOOPPIDWindow.setWindowTitle("HTR1202")
        self.HTR1202.LOOPPIDWindow.Label.setText("HTR1202")
        self.HTR1202.LOOPPIDWindow.RTD1.Label.setText("TT6413")
        self.HTR1202.LOOPPIDWindow.RTD2.Label.setText("TT6415")


        self.HTR2203 = LOOPPID_v2(self.ChamberTab)
        self.HTR2203.move(1260*R, 1215*R)
        self.HTR2203.Label.setText("HTR2203")
        self.HTR2203.LOOPPIDWindow.setWindowTitle("HTR2203")
        self.HTR2203.LOOPPIDWindow.Label.setText("HTR2203")
        self.HTR2203.LOOPPIDWindow.RTD1.Label.setText("TT6414")
        self.HTR2203.LOOPPIDWindow.RTD2.Label.setText("TT6416")

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

        self.TT7401 = Indicator(self.FluidTab)
        self.TT7401.move(1985*R, 250*R)
        self.TT7401.Label.setText("TT7401")

        self.TT7402 = Indicator(self.FluidTab)
        self.TT7402.move(910*R, 530*R)
        self.TT7402.Label.setText("TT7402")

        self.PS8302 = ColoredStatus(self.FluidTab, mode=2)
        self.PS8302.move(2300 * R, 100 * R)
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

        self.PS1361 = ColoredStatus(self.FluidTab, mode=2)
        self.PS1361.move(810 * R, 870* R)
        self.PS1361.Label.setText("PS1361")


        self.PT1332 = Indicator(self.FluidTab)
        self.PT1332.move(630*R, 900*R)
        self.PT1332.Label.setText("PT1332")
        self.PT1332.SetUnit(" bar")

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

        # Data and Signal Tab
        self.ReadSettings = Loadfile(self.DatanSignalTab)
        self.ReadSettings.move(50*R, 50*R)
        # self.ReadSettings.LoadFileButton.clicked.connect(
        #     lambda x: self.Recover(address=self.ReadSettings.FilePath.text()))

        self.SaveSettings = CustomSave(self.DatanSignalTab)
        self.SaveSettings.move(700*R, 50*R)
        # self.SaveSettings.SaveFileButton.clicked.connect(
        #     lambda x: self.Save(directory=self.SaveSettings.Head, project=self.SaveSettings.Tail))


        self.TS_ADDREM = ProcedureWidget_TS(self.DatanSignalTab)
        self.TS_ADDREM.move(700*R, 150*R)
        self.TS_ADDREM.Group.setTitle("TS ADDREM")
        self.TS_ADDREM.objectname = "TS_ADDREM"
        self.TS_ADDREM.expandwindow.MAXTIME_RD.Unit=' s'
        self.TS_ADDREM.expandwindow.FLOWET.Unit = ' s'

        self.TS_EMPTY = ProcedureWidget(self.DatanSignalTab)
        self.TS_EMPTY.move(700 * R, 390 * R)
        self.TS_EMPTY.Group.setTitle("TS EMPTY")
        self.TS_EMPTY.objectname = "TS_EMPTY"

        self.TS_EMPTYALL = ProcedureWidget(self.DatanSignalTab)
        self.TS_EMPTYALL.move(700 * R, 630 * R)
        self.TS_EMPTYALL.Group.setTitle("TS EMPTY ALL")
        self.TS_EMPTYALL.objectname = "TS_EMPTYALL"

        self.PU_PRIME = ProcedureWidget(self.DatanSignalTab)
        self.PU_PRIME.move(700 * R, 870 * R)
        self.PU_PRIME.Group.setTitle("PU PRIME")
        self.PU_PRIME.objectname = "PU_PRIME"

        self.WRITE_SLOWDAQ = ProcedureWidget(self.DatanSignalTab)
        self.WRITE_SLOWDAQ.move(700 * R, 1110 * R)
        self.WRITE_SLOWDAQ.Group.setTitle("WRITE SLOWDAQ")
        self.WRITE_SLOWDAQ.objectname = "WRITE_SLOWDAQ"

        self.PRESSURE_CYCLE = ProcedureWidget_PC(self.DatanSignalTab)
        self.PRESSURE_CYCLE.move(1300 * R, 150 * R)
        self.PRESSURE_CYCLE.Group.setTitle("PRESSURE_CYCLE")
        self.PRESSURE_CYCLE.objectname = "PRESSURE_CYCLE"
        self.PRESSURE_CYCLE.expandwindow.EXPTIME_RD.Unit = " s"
        self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_RD.Unit = " s"
        self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_RD.Unit = " s"
        self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_RD.Unit = " s"
        self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_RD.Unit = " s"

        self.MAN_TS = Flag(self.DatanSignalTab)
        self.MAN_TS.move(1300 * R, 390 * R)
        self.MAN_TS.Label.setText("MAN_TS")


        self.MAN_HYD = Flag(self.DatanSignalTab)
        self.MAN_HYD.move(1300 * R, 500 * R)
        self.MAN_HYD.Label.setText("MAN_HYD")

        self.HTR6202_v2 = LOOPPID_v2(self.DatanSignalTab)
        self.HTR6202_v2.move(1300 * R, 900 * R)
        self.HTR6202_v2.Label.setText("HTR6202")
        self.HTR6202_v2.LOOPPIDWindow.setWindowTitle("HTR6202")
        self.HTR6202_v2.LOOPPIDWindow.Label.setText("HTR6202")
        self.HTR6202_v2.LOOPPIDWindow.RTD1.Label.setText("TT6222")
        self.HTR6202_v2.LOOPPIDWindow.RTD2.Label.setText("EMPTY")

        self.PUMP3305_v2 = LOOP2PT_v2(self.DatanSignalTab)
        self.PUMP3305_v2.move(1300 * R, 1000 * R)
        self.PUMP3305_v2.Label.setText("PUMP3305")
        self.PUMP3305_v2.State.LButton.setText("ON")
        self.PUMP3305_v2.State.RButton.setText("OFF")
        self.PUMP3305_v2.LOOP2PTWindow.setWindowTitle("PUMP3305")
        self.PUMP3305_v2.LOOP2PTWindow.Label.setText("PUMP3305")

        self.PCYCLE_AUTOCYCLE = Flag(self.DatanSignalTab)
        self.PCYCLE_AUTOCYCLE.move(1300 * R, 600 * R)
        self.PCYCLE_AUTOCYCLE.Label.setText("PCYCLE_AUTOCYCLE")


        # INTLCK button
        self.INTLCKWindow = INTLCK_Win_v2()
        self.INTLCKButton = INTLCKButton(self.INTLCKWindow, self)
        self.INTLCKButton.SubWindow.resize(1000 * R, 500 * R)
        # self.AlarmButton.StatusWindow.AlarmWindow()

        self.INTLCKButton.move(90 * R, 1350 * R)
        # self.INTLCKButton.Button.setText("INTLCK Button")

        # Alarm button
        self.AlarmWindow = AlarmWin()
        self.AlarmButton = AlarmButton(self.AlarmWindow, self)
        self.AlarmButton.SubWindow.resize(1000*R, 500*R)

        # self.AlarmButton.StatusWindow.AlarmWindow()

        self.AlarmButton.move(10*R, 1350*R)
        # self.AlarmButton.move(10 * R, 1200 * R)
        # self.AlarmButton.Button.setText("Alarm Button")


        #commands stack
        self.address =sec.merge_dic(sec.TT_FP_ADDRESS,sec.TT_BO_ADDRESS,sec.PT_ADDRESS,sec.LEFT_REAL_ADDRESS,
                                                     sec.DIN_ADDRESS,sec.VALVE_ADDRESS,sec.LOOPPID_ADR_BASE,sec.LOOP2PT_ADR_BASE,sec.PROCEDURE_ADDRESS, sec.INTLK_A_ADDRESS,
                                    sec.INTLK_D_ADDRESS,sec.FLAG_ADDRESS)
        self.commands = {}
        self.command_buffer_waiting= 1
        # self.statustransition={}

        self.Valve_buffer = copy.copy(sec.VALVE_OUT)
        self.CHECKED = False

        self.Switch_buffer = copy.copy(sec.SWITCH_OUT)
        self.LOOPPID_EN_buffer = copy.copy(sec.LOOPPID_EN)
        self.LOOP2PT_OUT_buffer =copy.copy(sec.LOOP2PT_OUT)
        self.INTLK_D_DIC_buffer = copy.copy(sec.INTLK_D_DIC)
        self.INTLK_A_DIC_buffer = copy.copy(sec.INTLK_A_DIC)
        self.FLAG_buffer = copy.copy(sec.FLAG_DIC)


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
                                 self.AlarmButton.SubWindow.TT6413, self.AlarmButton.SubWindow.TT6414]

        self.PTAlarmMatrix = [self.AlarmButton.SubWindow.PT1101, self.AlarmButton.SubWindow.PT1325,
                              self.AlarmButton.SubWindow.PT2316, self.AlarmButton.SubWindow.PT2121,
                              self.AlarmButton.SubWindow.PT2330, self.AlarmButton.SubWindow.PT2335,
                              self.AlarmButton.SubWindow.PT3308, self.AlarmButton.SubWindow.PT3309,
                              self.AlarmButton.SubWindow.PT3311,self.AlarmButton.SubWindow.PT3314,
                              self.AlarmButton.SubWindow.PT3320, self.AlarmButton.SubWindow.PT3332,
                              self.AlarmButton.SubWindow.PT3333, self.AlarmButton.SubWindow.PT4306,
                              self.AlarmButton.SubWindow.PT4315, self.AlarmButton.SubWindow.PT4319,
                              self.AlarmButton.SubWindow.PT4322, self.AlarmButton.SubWindow.PT4325,
                              self.AlarmButton.SubWindow.PT5304,self.AlarmButton.SubWindow.PT6302]

        self.LEFTVariableMatrix = [self.AlarmButton.SubWindow.BFM4313, self.AlarmButton.SubWindow.LT3335,
                                   self.AlarmButton.SubWindow.MFC1316_IN, self.AlarmButton.SubWindow.CYL3334_FCALC,
                                   self.AlarmButton.SubWindow.SERVO3321_IN_REAL, self.AlarmButton.SubWindow.TS1_MASS,
                                   self.AlarmButton.SubWindow.TS2_MASS, self.AlarmButton.SubWindow.TS3_MASS]

        self.DinAlarmMatrix = [self.AlarmButton.SubWindow.LS3338, self.AlarmButton.SubWindow.LS3339,
                                   self.AlarmButton.SubWindow.ES3347, self.AlarmButton.SubWindow.PUMP3305_CON,
                                   self.AlarmButton.SubWindow.PUMP3305_OL, self.AlarmButton.SubWindow.PS2352,
                                   self.AlarmButton.SubWindow.PS1361, self.AlarmButton.SubWindow.PS8302]

        self.LOOPPIDAlarmMatrix = [self.AlarmButton.SubWindow.SERVO3321, self.AlarmButton.SubWindow.HTR6225,
                                   self.AlarmButton.SubWindow.HTR2123, self.AlarmButton.SubWindow.HTR2124,
                                   self.AlarmButton.SubWindow.HTR2125, self.AlarmButton.SubWindow.HTR1202,
                                   self.AlarmButton.SubWindow.HTR2203, self.AlarmButton.SubWindow.HTR6202,
                                      self.AlarmButton.SubWindow.HTR6206,self.AlarmButton.SubWindow.HTR6210,
                                      self.AlarmButton.SubWindow.HTR6223,self.AlarmButton.SubWindow.HTR6224,
                                      self.AlarmButton.SubWindow.HTR6219,self.AlarmButton.SubWindow.HTR6221,
                                      self.AlarmButton.SubWindow.HTR6214]

        self.AlarmMatrix = [self.AlarmButton.SubWindow.TT2101, self.AlarmButton.SubWindow.TT2111,
                            self.AlarmButton.SubWindow.TT2113, self.AlarmButton.SubWindow.TT2118,
                            self.AlarmButton.SubWindow.TT2119, self.AlarmButton.SubWindow.TT4330,
                            self.AlarmButton.SubWindow.TT6203, self.AlarmButton.SubWindow.TT6207,
                            self.AlarmButton.SubWindow.TT6211, self.AlarmButton.SubWindow.TT6213,
                            self.AlarmButton.SubWindow.TT6222, self.AlarmButton.SubWindow.TT6407,
                            self.AlarmButton.SubWindow.TT6408, self.AlarmButton.SubWindow.TT6409,
                            self.AlarmButton.SubWindow.TT6415,self.AlarmButton.SubWindow.TT6416,
                            self.AlarmButton.SubWindow.TT2420, self.AlarmButton.SubWindow.TT2422,
                            self.AlarmButton.SubWindow.TT2424, self.AlarmButton.SubWindow.TT2425,
                            self.AlarmButton.SubWindow.TT2442,self.AlarmButton.SubWindow.TT2403,
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
                            self.AlarmButton.SubWindow.PT1101, self.AlarmButton.SubWindow.PT1325,
                            self.AlarmButton.SubWindow.PT2316, self.AlarmButton.SubWindow.PT2121,
                            self.AlarmButton.SubWindow.PT2330, self.AlarmButton.SubWindow.PT2335,
                            self.AlarmButton.SubWindow.PT3308, self.AlarmButton.SubWindow.PT3309,
                            self.AlarmButton.SubWindow.PT3311, self.AlarmButton.SubWindow.PT3314,
                            self.AlarmButton.SubWindow.PT3320, self.AlarmButton.SubWindow.PT3332,
                            self.AlarmButton.SubWindow.PT3333, self.AlarmButton.SubWindow.PT4306,
                            self.AlarmButton.SubWindow.PT4315, self.AlarmButton.SubWindow.PT4319,
                            self.AlarmButton.SubWindow.PT4322, self.AlarmButton.SubWindow.PT4325,
                            self.AlarmButton.SubWindow.PT5304, self.AlarmButton.SubWindow.PT6302,
                            self.AlarmButton.SubWindow.BFM4313, self.AlarmButton.SubWindow.LT3335,
                            self.AlarmButton.SubWindow.MFC1316_IN, self.AlarmButton.SubWindow.CYL3334_FCALC,
                            self.AlarmButton.SubWindow.SERVO3321_IN_REAL, self.AlarmButton.SubWindow.TS1_MASS,
                            self.AlarmButton.SubWindow.TS2_MASS, self.AlarmButton.SubWindow.TS3_MASS,
                            self.AlarmButton.SubWindow.LS3338, self.AlarmButton.SubWindow.LS3339,
                            self.AlarmButton.SubWindow.ES3347, self.AlarmButton.SubWindow.PUMP3305_CON,
                            self.AlarmButton.SubWindow.PUMP3305_OL, self.AlarmButton.SubWindow.PS2352,
                            self.AlarmButton.SubWindow.PS1361, self.AlarmButton.SubWindow.PS8302,
                            self.AlarmButton.SubWindow.SERVO3321, self.AlarmButton.SubWindow.HTR6225,
                            self.AlarmButton.SubWindow.HTR2123, self.AlarmButton.SubWindow.HTR2124,
                            self.AlarmButton.SubWindow.HTR2125, self.AlarmButton.SubWindow.HTR1202,
                            self.AlarmButton.SubWindow.HTR2203, self.AlarmButton.SubWindow.HTR6202,
                            self.AlarmButton.SubWindow.HTR6206, self.AlarmButton.SubWindow.HTR6210,
                            self.AlarmButton.SubWindow.HTR6223, self.AlarmButton.SubWindow.HTR6224,
                            self.AlarmButton.SubWindow.HTR6219, self.AlarmButton.SubWindow.HTR6221,
                            self.AlarmButton.SubWindow.HTR6214]




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

        # self.SV3329.Signals.sSignal.connect(self.SetSVMode)
        # self.HFSV3331.Signals.sSignal.connect(self.SetSVMode)
        self.LoginT.Button.clicked.connect(self.ChangeUser)
        self.LoginP.Button.clicked.connect(self.ChangeUser)


        App.aboutToQuit.connect(self.StopUpdater)
        # Start display updater;
        self.StartUpdater()

        self.signal_connection()

    # send_command_signal_MW = QtCore.Signal(object)
    send_command_signal_MW = QtCore.Signal()

    def StartUpdater(self):


        install()




        self.ClientUpdateThread = QtCore.QThread()
        self.UpClient = UpdateClient()
        self.UpClient.moveToThread(self.ClientUpdateThread)
        self.ClientUpdateThread.started.connect(self.UpClient.run)

        # signal receive the signal and send command to client
        self.UpClient.client_command_fectch.connect(self.sendcommands)
        # self.send_command_signal_MW.connect(self.UpClient.commands)
        self.send_command_signal_MW.connect(lambda:self.UpClient.commands(self.commands))

        #signal clear the self.command

        self.UpClient.client_clear_commands.connect(self.clearcommands)
        # transport read client data into GUI, this makes sure that only when new directory comes, main thread will update the display

        self.UpClient.client_data_transport.connect(lambda: self.updatedisplay(self.UpClient.receive_dic))
        self.ClientUpdateThread.start()






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

        # Data signal saving and writing
        self.SaveSettings.SaveFileButton.clicked.connect(lambda : self.SaveSettings.SavecsvConfig(self.UpClient.receive_dic))
        # self.ReadSettings.LoadFileButton.clicked.connect(lambda : self.updatedisplay(self.ReadSettings.loaded_dict))
        self.ReadSettings.LoadFileButton.clicked.connect(lambda : self.man_set(self.ReadSettings.default_dict))
        self.ReadSettings.LoadFileButton.clicked.connect(lambda : self.man_activated(self.ReadSettings.default_dict))
        # self.AlarmButton.SubWindow.MAN_ACT.clicked.connect(lambda: self.man_activated(self.UpClient.receive_dic))


        # self.PV1344.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV1344.Label.text()))
        # self.PV1344.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV1344.Label.text()))
        # self.PV4307.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4307.Label.text()))
        # self.PV4307.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4307.Label.text()))
        # self.PV4308.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4308.Label.text()))
        # self.PV4308.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4308.Label.text()))
        # self.PV4317.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4317.Label.text()))
        # self.PV4317.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4317.Label.text()))
        # self.PV4318.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4318.Label.text()))
        # self.PV4318.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4318.Label.text()))
        # self.PV4321.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4321.Label.text()))
        # self.PV4321.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4321.Label.text()))
        # self.PV4324.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV4324.Label.text()))
        # self.PV4324.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV4324.Label.text()))
        # self.PV5305.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV5305.Label.text()))
        # self.PV5305.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV5305.Label.text()))
        # self.PV5306.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV5306.Label.text()))
        # self.PV5306.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV5306.Label.text()))
        # self.PV5307.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV5307.Label.text()))
        # self.PV5307.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV5307.Label.text()))
        # self.PV5309.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.PV5309.Label.text()))
        # self.PV5309.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.PV5309.Label.text()))
        # self.SV3307.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3307.Label.text()))
        # self.SV3307.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3307.Label.text()))
        # self.SV3310.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3310.Label.text()))
        # self.SV3310.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3310.Label.text()))
        # self.SV3322.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3322.Label.text()))
        # self.SV3322.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3322.Label.text()))
        # self.SV3325.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3325.Label.text()))
        # self.SV3325.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3325.Label.text()))
        # self.SV3329.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV3329.Label.text()))
        # self.SV3329.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV3329.Label.text()))
        # self.SV4327.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4327.Label.text()))
        # self.SV4327.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4327.Label.text()))
        # self.SV4328.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4328.Label.text()))
        # self.SV4328.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4328.Label.text()))
        # self.SV4329.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4329.Label.text()))
        # self.SV4329.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4329.Label.text()))
        # self.SV4331.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4331.Label.text()))
        # self.SV4331.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4331.Label.text()))
        # self.SV4332.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4332.Label.text()))
        # self.SV4332.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4332.Label.text()))
        # self.SV4337.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.SV4337.Label.text()))
        # self.SV4337.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.SV4337.Label.text()))
        # self.HFSV3312.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.HFSV3312.Label.text()))
        # self.HFSV3312.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.HFSV3312.Label.text()))
        # self.HFSV3323.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.HFSV3323.Label.text()))
        # self.HFSV3323.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.HFSV3323.Label.text()))
        # self.HFSV3331.Set.LButton.clicked.connect(lambda x: self.LButtonClicked(self.HFSV3331.Label.text()))
        # self.HFSV3331.Set.RButton.clicked.connect(lambda x: self.RButtonClicked(self.HFSV3331.Label.text()))

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
        #
        # self.PUMP3305_v2.Set.LButton.clicked.connect(lambda x: self.LOOP2PTLButtonClicked(self.PUMP3305.Label.text()))
        # self.PUMP3305_v2.Set.RButton.clicked.connect(lambda x: self.LOOP2PTRButtonClicked(self.PUMP3305.Label.text()))



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



        self.HTR6202_v2.LOOPPIDWindow.Mode.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6202_v2.LOOPPIDWindow.Label.text()))
        self.HTR6202_v2.LOOPPIDWindow.Mode.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6202_v2.LOOPPIDWindow.Label.text()))
        self.HTR6202_v2.State.LButton.clicked.connect(
            lambda x: self.HTLButtonClicked(self.HTR6202_v2.LOOPPIDWindow.Label.text()))
        self.HTR6202_v2.State.RButton.clicked.connect(
            lambda x: self.HTRButtonClicked(self.HTR6202_v2.LOOPPIDWindow.Label.text()))
        self.HTR6202_v2.LOOPPIDWindow.ButtonGroup.Button0.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6202_v2.LOOPPIDWindow.Label.text(), 0))
        self.HTR6202_v2.LOOPPIDWindow.ButtonGroup.Button1.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6202_v2.LOOPPIDWindow.Label.text(), 1))
        self.HTR6202_v2.LOOPPIDWindow.ButtonGroup.Button2.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6202_v2.LOOPPIDWindow.Label.text(), 2))
        self.HTR6202_v2.LOOPPIDWindow.ButtonGroup.Button3.clicked.connect(
            lambda x: self.HTRGroupButtonClicked(self.HTR6202_v2.LOOPPIDWindow.Label.text(), 3))

        self.HTR6202_v2.LOOPPIDWindow.updatebutton.clicked.connect(
            lambda x: self.HTRupdate(self.HTR6202_v2.LOOPPIDWindow.Label.text(),
                                     self.HTR6202_v2.LOOPPIDWindow.ModeREAD.Field.text(),
                                     float(self.HTR6202_v2.LOOPPIDWindow.SP.Field.text()),
                                     float(self.HTR6202_v2.LOOPPIDWindow.HISP.Field.text()),
                                     float(self.HTR6202_v2.LOOPPIDWindow.LOSP.Field.text())))

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


        #BO PT updatebutton and activate button

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

        self.AlarmButton.SubWindow.PS1361.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PS1361.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PS1361.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PS1361.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PS1361.High_Set.Field.text()))

        self.AlarmButton.SubWindow.PS8302.updatebutton.clicked.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PS8302.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PS8302.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PS8302.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PS8302.High_Set.Field.text()))
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

        self.AlarmButton.SubWindow.PS1361.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PS1361.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PS1361.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PS1361.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PS1361.High_Set.Field.text(), update= False))

        self.AlarmButton.SubWindow.PS8302.AlarmMode.stateChanged.connect(
            lambda: self.DinBoxUpdate(pid=self.AlarmButton.SubWindow.PS8302.Label.text(),
                                      Act=self.AlarmButton.SubWindow.PS8302.AlarmMode.isChecked(),
                                      LowLimit=self.AlarmButton.SubWindow.PS8302.Low_Set.Field.text(),
                                      HighLimit=self.AlarmButton.SubWindow.PS8302.High_Set.Field.text(), update= False))


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

        self.INTLCKWindow.PT4306_HI_INTLK.EN.LButton.clicked.connect(
            lambda x: self.INTLK_A_LButtonClicked(self.INTLCKWindow.PT4306_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4306_HI_INTLK.EN.RButton.clicked.connect(
            lambda x: self.INTLK_A_RButtonClicked(self.INTLCKWindow.PT4306_HI_INTLK.Label.text() + "_INTLK"))
        self.INTLCKWindow.PT4306_HI_INTLK.updatebutton.clicked.connect(
            lambda x: self.INTLK_A_update(self.INTLCKWindow.PT4306_HI_INTLK.Label.text() + "_INTLK",
                                          self.INTLCKWindow.PT4306_HI_INTLK.SET_W.Field.text()))

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



        #Procedure widgets
        self.TS_ADDREM.START.clicked.connect(lambda: self.ProcedureClick(pid = self.TS_ADDREM.objectname, start = True, stop = False, abort = False))
        self.TS_ADDREM.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_ADDREM.objectname, start=False, stop=True, abort=False))
        self.TS_ADDREM.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_ADDREM.objectname, start=False, stop=False, abort=True))

        self.TS_ADDREM.expandwindow.Start.clicked.connect(
            lambda: self.ProcedureClick(pid=self.TS_ADDREM.objectname, start=True, stop=False, abort=False))
        self.TS_ADDREM.expandwindow.Stop.clicked.connect(
            lambda: self.ProcedureClick(pid=self.TS_ADDREM.objectname, start=False, stop=True, abort=False))
        self.TS_ADDREM.expandwindow.Abort.clicked.connect(
            lambda: self.ProcedureClick(pid=self.TS_ADDREM.objectname, start=False, stop=False, abort=True))
        self.TS_ADDREM.expandwindow.RST_FF.clicked.connect(
            lambda: self.Procedure_TS_update(pid=self.TS_ADDREM.objectname,  RST=True, SEL=self.TS_ADDREM.expandwindow.SEL_WR.Field.text(), ADDREM_MASS=self.TS_ADDREM.expandwindow.ADDREM_MASS_WR.Field.text(), MAXTIME=self.TS_ADDREM.expandwindow.MAXTIME_WR.Field.text(),update=False))
        self.TS_ADDREM.expandwindow.updatebutton.clicked.connect(
            lambda: self.Procedure_TS_update(pid=self.TS_ADDREM.objectname,  RST=False, SEL=self.TS_ADDREM.expandwindow.SEL_WR.Field.text(), ADDREM_MASS=self.TS_ADDREM.expandwindow.ADDREM_MASS_WR.Field.text(), MAXTIME=self.TS_ADDREM.expandwindow.MAXTIME_WR.Field.text(),update=True))



        self.TS_EMPTY.START.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTY.objectname, start=True, stop=False, abort=False))
        self.TS_EMPTY.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTY.objectname, start=False, stop=True, abort=False))
        self.TS_EMPTY.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTY.objectname, start=False, stop=False, abort=True))

        self.TS_EMPTYALL.START.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTYALL.objectname, start=True, stop=False, abort=False))
        self.TS_EMPTYALL.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTYALL.objectname, start=False, stop=True, abort=False))
        self.TS_EMPTYALL.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.TS_EMPTYALL.objectname, start=False, stop=False, abort=True))

        self.PU_PRIME.START.clicked.connect(lambda: self.ProcedureClick(pid=self.PU_PRIME.objectname, start=True, stop=False, abort=False))
        self.PU_PRIME.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.PU_PRIME.objectname, start=False, stop=True, abort=False))
        self.PU_PRIME.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.PU_PRIME.objectname, start=False, stop=False, abort=True))

        self.WRITE_SLOWDAQ.START.clicked.connect(lambda: self.ProcedureClick(pid=self.WRITE_SLOWDAQ.objectname, start=True, stop=False, abort=False))
        self.WRITE_SLOWDAQ.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.WRITE_SLOWDAQ.objectname, start=False, stop=True, abort=False))
        self.WRITE_SLOWDAQ.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.WRITE_SLOWDAQ.objectname, start=False, stop=False, abort=True))

        self.PRESSURE_CYCLE.START.clicked.connect(lambda: self.ProcedureClick(pid=self.PRESSURE_CYCLE.objectname, start=True, stop=False, abort=False))
        self.PRESSURE_CYCLE.STOP.clicked.connect(lambda: self.ProcedureClick(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=True, abort=False))
        self.PRESSURE_CYCLE.ABORT.clicked.connect(lambda: self.ProcedureClick(pid=self.PRESSURE_CYCLE.objectname, start=False, stop=False, abort=True))

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
            # if not self.commands[pid]:
            #     time.sleep(self.command_buffer_waiting)
            # in case cannot find the pid's address
            address = self.address[pid]
            self.commands[pid]={"server":"BO","address": address, "type":"valve","operation":"OPEN", "value":1}
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid,"LButton is clicked")
        except Exception as e:
            print(e)



    @QtCore.Slot()
    def RButtonClicked(self, pid):

        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "CLOSE",
                              "value": 1}
            print(self.commands)
            print(pid, "R Button is clicked", datetime.datetime.now())
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def FLAGLButtonClicked(self, pid):
        try:
            # if there is alread a command to send to tcp server, wait the new command until last one has been sent
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            # in case cannot find the pid's address
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "FLAG", "operation": "OPEN", "value": 1}
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def FLAGRButtonClicked(self, pid):

        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "FLAG", "operation": "CLOSE",
                                  "value": 1}
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def SwitchLButtonClicked(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "switch", "operation": "ON", "value": 1}
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def SwitchRButtonClicked(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "switch", "operation": "OFF",
                              "value": 1}
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_A_LButtonClicked(self, pid):
        try:

            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "INTLK_A", "operation": "ON", "value": 1}
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_A_RButtonClicked(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "INTLK_A", "operation": "OFF",
                              "value": 1}
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_A_RESET(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "INTLK_A", "operation": "RESET",
                                  "value": 1}
            print(self.commands)
            print(pid, "RESET")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_A_update(self, pid,value):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "INTLK_A", "operation": "update",
                                  "value": float(value)}
            print(self.commands)
            print(pid, "update")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_D_LButtonClicked(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "INTLK_D", "operation": "ON", "value": 1}
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_D_RButtonClicked(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "INTLK_D", "operation": "OFF",
                                  "value": 1}
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def INTLK_D_RESET(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "INTLK_D", "operation": "RESET",
                                  "value": 1}
            print(self.commands)
            print(pid, "RESET")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LOOP2PTLButtonClicked(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT_power", "operation": "OPEN", "value": 1}
            # self.statustransition[pid] = {"server": "BO", "address": address, "type": "valve", "operation": "OPEN", "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)


    @QtCore.Slot()
    def LOOP2PTRButtonClicked(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT_power", "operation": "CLOSE",
                                  "value": 1}
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LOOP2PTSet(self, pid, value):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            if value in [0, 1, 2, 3]:
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT", "operation": "SETMODE", "value": value}
            else:
                print("value should be 0, 1, 2, 3")
            print(self.commands)
        except Exception as e:
            print(e)


    @QtCore.Slot()
    def LOOP2PTSETPOINTSet(self, pid, value1, value2):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            if value1 == 1:
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT",
                                  "operation": "SET1", "value": value2}
            elif value1 == 2:
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT",
                                  "operation": "SET2", "value": value2}
            elif value1 == 3:
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT",
                                  "operation": "SET3", "value": value2}
            else:
                print("MODE number should be in 1-3")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LOOP2PTGroupButtonClicked(self, pid, setN):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            if setN == 0:
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT_setmode",
                                  "operation": "SET0", "value": True}
            elif setN == 1:
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT_setmode",
                                  "operation": "SET1", "value": True}
            elif setN == 2:
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT_setmode",
                                  "operation": "SET2", "value": True}
            elif setN == 3:
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT_setmode",
                                  "operation": "SET3", "value": True}
            else:
                print("not a valid address")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LOOP2PTupdate(self, pid, modeN, setpoint):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            if modeN == 'MODE0':
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT_para",
                                      "operation": "SET0", "value": {"SETPOINT": setpoint}}
            elif modeN == 'MODE1':
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT_para",
                                      "operation": "SET1", "value": {"SETPOINT": setpoint}}
            elif modeN == 'MODE2':
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT_para",
                                      "operation": "SET2", "value": {"SETPOINT": setpoint}}
            elif modeN == 'MODE3':
                self.commands[pid] = {"server": "BO", "address": address, "type": "LOOP2PT_para",
                                      "operation": "SET3", "value": {"SETPOINT": setpoint}}
            else:
                print("MODE number should be in MODE0-3 and is a string")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTRupdate(self,pid, modeN, setpoint, HI, LO):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            if modeN == 'MODE0':
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_para",
                              "operation": "SET0", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}
            elif modeN == 'MODE1':
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET1", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}
            elif modeN == 'MODE2':
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET2", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}
            elif modeN == 'MODE3':
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET3", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}
            else:
                print("MODE number should be in MODE0-3 and is a string")

            print(self.commands)
        except Exception as e:
            print(e)




    @QtCore.Slot()
    def HTLButtonClicked(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "heater_power", "operation": "EN",
                              "value": 1}
            print(self.commands)
            print(pid, "LButton is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTRButtonClicked(self, pid):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "heater_power", "operation": "DISEN",
                              "value": 1}
            print(self.commands)
            print(pid, "R Button is clicked")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTSwitchSet(self, pid, value):
        try:

            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            if value in [0,1,2,3]:
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater", "operation": "SETMODE", "value": value}
            else:
                print("value should be 0, 1, 2, 3")
            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTHISet(self, pid, value):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "heater",
                                  "operation": "HI_LIM", "value": value}

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTLOSet(self, pid, value):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "heater",
                              "operation": "LO_LIM", "value": value}

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTSETPOINTSet(self, pid, value1, value2):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            if value1 == 0:
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater",
                                  "operation": "SET0", "value": value2}
            elif value1 == 1:
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater",
                                  "operation": "SET1", "value": value2}
            elif value1 == 2:
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater",
                                  "operation": "SET2", "value": value2}
            elif value1 == 3:
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater",
                                  "operation": "SET3", "value": value2}
            else:
                print("MODE number should be in 0-3")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTRGroupButtonClicked(self, pid, setN):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            if setN == 0:
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_setmode",
                                  "operation": "SET0", "value": True}
            elif setN == 1:
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_setmode",
                                  "operation": "SET1", "value": True}
            elif setN == 2:
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_setmode",
                                  "operation": "SET2", "value": True}
            elif setN == 3:
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_setmode",
                                  "operation": "SET3", "value": True}
            else:
                print("not a valid address")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def HTRupdate(self,pid, modeN, setpoint, HI, LO):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            if modeN == 'MODE0':
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_para",
                              "operation": "SET0", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}
            elif modeN == 'MODE1':
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET1", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}
            elif modeN == 'MODE2':
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET2", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}
            elif modeN == 'MODE3':
                self.commands[pid] = {"server": "BO", "address": address, "type": "heater_para",
                                  "operation": "SET3", "value": {"SETPOINT": setpoint, "HI_LIM": HI, "LO_LIM": LO}}
            else:
                print("MODE number should be in MODE0-3 and is a string")

            print(self.commands)
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def BOTTBoxUpdate(self,pid, Act,LowLimit, HighLimit,update=True):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid]={"server": "BO", "address": address, "type": "TT", "operation": {"Act":Act,
                                "LowLimit":float(LowLimit),"HighLimit":float(HighLimit),"Update":update}}
            print(pid,Act,LowLimit,HighLimit,"ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def FPTTBoxUpdate(self,pid, Act,LowLimit, HighLimit,update=True):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid]={"server": "FP", "address": address, "type": "TT", "operation": {"Act":Act,
                                "LowLimit":float(LowLimit),"HighLimit":float(HighLimit),"Update":update}}
            print(pid,Act,LowLimit,HighLimit,"ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def PTBoxUpdate(self, pid, Act, LowLimit, HighLimit,update=True):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "PT", "operation": {"Act": Act,
                                                                                                        "LowLimit": float(LowLimit), "HighLimit": float(HighLimit),"Update":update}}
            print(pid, Act, LowLimit, HighLimit, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LEFTBoxUpdate(self, pid, Act, LowLimit, HighLimit, update=True):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "LEFT", "operation": {"Act": Act,
                                                                                                  "LowLimit": float(LowLimit), "HighLimit": float(HighLimit), "Update": update}}
            print(pid, Act, LowLimit, HighLimit, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def DinBoxUpdate(self, pid, Act, LowLimit, HighLimit, update=True):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "Din", "operation": {"Act": Act,
                                                                                                    "LowLimit": float(
                                                                                                        LowLimit),
                                                                                                    "HighLimit": float(
                                                                                                        HighLimit),
                                                                                                    "Update": update}}
            print(pid, Act, LowLimit, HighLimit, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def LOOPPIDBoxUpdate(self, pid, Act, LowLimit, HighLimit, update=True):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "LOOPPID_alarm", "operation": {"Act": Act,
                                                                                                   "LowLimit": float(
                                                                                                       LowLimit),
                                                                                                   "HighLimit": float(
                                                                                                       HighLimit),
                                                                                                   "Update": update}}
            print(pid, Act, LowLimit, HighLimit, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def ProcedureClick(self, pid, start, stop, abort):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "Procedure", "operation": {"Start": start, "Stop": stop, "Abort": abort}}
            print(pid, start, stop, abort, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def Procedure_TS_update(self, pid, RST, SEL, ADDREM_MASS, MAXTIME,update):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "Procedure_TS",
                                  "operation": {"RST_FF":RST, "SEL": SEL, "ADDREM_MASS": ADDREM_MASS, "MAXTIME": MAXTIME,"update":update}}
            print(pid, RST, SEL, ADDREM_MASS, MAXTIME,update, "ARE OK?")
        except Exception as e:
            print(e)

    @QtCore.Slot()
    def Procedure_PC_update(self, pid, start, stop, abort,ABORT_FF,FASTCOMP_FF,PCYCLE_SLOWCOMP_FF,PCYCLE_CYLEQ_FF,PCYCLE_ACCHARGE_FF,PCYCLE_CYLBLEED_FF,PSET,MAXEXPTIME,MAXEQTIME,MAXEQPDIFF,MAXACCTIME,MAXACCDPDT,MAXBLEEDTIME,MAXBLEEDDPDT,update):
        try:
            # if self.commands[pid] is not None:
            #     time.sleep(self.command_buffer_waiting)
            address = self.address[pid]
            self.commands[pid] = {"server": "BO", "address": address, "type": "Procedure_PC",
                                  "operation": {"ABORT_FF":ABORT_FF,"FASTCOMP_FF":FASTCOMP_FF,"PCYCLE_SLOWCOMP_FF":PCYCLE_SLOWCOMP_FF,
                                                "PCYCLE_CYLEQ_FF":PCYCLE_CYLEQ_FF,"PCYCLE_ACCHARGE_FF":PCYCLE_ACCHARGE_FF,"PCYCLE_CYLBLEED_FF":PCYCLE_CYLBLEED_FF,
                                                "PSET":PSET,"MAXEXPTIME":MAXEXPTIME,"MAXEQTIME":MAXEQTIME,"MAXEQPDIFF":MAXEQPDIFF,
                                                "MAXACCTIME":MAXACCTIME,"MAXACCDPDT":MAXACCDPDT,"MAXBLEEDTIME":MAXBLEEDTIME,"MAXBLEEDDPDT":MAXBLEEDDPDT,"update":update}}
            print(pid, start, stop, abort, "ARE OK?")
        except Exception as e:
            print(e)

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
    def sendcommands(self):
        self.send_command_signal_MW.emit()
        print(self.commands)
        # print("signal received")

    @QtCore.Slot()
    def clearcommands(self):
        self.commands = {}

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

        for element in self.LEFTVariableMatrix:
            element.AlarmMode.setChecked(bool(dic_c["Active"]["LEFT_REAL"][element.Label.text()]))


        for element in self.DinAlarmMatrix:
            element.AlarmMode.setChecked(bool(dic_c["Active"]["Din"][element.Label.text()]))

        for element in self.LOOPPIDAlarmMatrix:
            element.AlarmMode.setChecked(bool(dic_c["Active"]["LOOPPID"][element.Label.text()]))



        # if dic_c["Active"]["TT"]["FP"]["fa"]:
        #     self.AlarmWindow.PT2316.AlarmMode.setChecked(True)
        # elif not dic_c["Active"]["TT"]["FP"]["fa"]:
        #     self.AlarmWindow.PT2316.AlarmMode.setChecked(False)
        # else:
        #     pass


    @QtCore.Slot(object)
    def updatedisplay(self, received_dic_c):
        print("Display updating", datetime.datetime.now())
        # print('Display update result for HFSV3331:', received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"])

        # print(received_dic_c["data"]["Procedure"])

        # initialization for all check box
        if received_dic_c["Active"]["INI_CHECK"]==True and self.CHECKED == False:
            self.man_activated(received_dic_c)
            self.CHECKED = True



        self.TS_ADDREM.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.TS_ADDREM.objectname])
        self.TS_ADDREM.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.TS_ADDREM.objectname])
        self.TS_ADDREM.expandwindow.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.TS_ADDREM.objectname])

        self.TS_ADDREM.expandwindow.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.TS_ADDREM.objectname])
        self.TS_ADDREM.expandwindow.FF_RD.Field.setText(bin(received_dic_c["data"]["FF"]["TS_ADDREM_FF"]))
        self.TS_ADDREM.expandwindow.SEL_RD.SetIntValue(received_dic_c["data"]["PARA_I"]["TS_SEL"])
        self.TS_ADDREM.expandwindow.ADDREM_MASS_RD.SetValue(received_dic_c["data"]["PARA_F"]["TS_ADDREM_MASS"])
        self.TS_ADDREM.expandwindow.MAXTIME_RD.SetIntValue(received_dic_c["data"]["PARA_T"]["TS_ADDREM_MAXTIME"]/1000)
        self.TS_ADDREM.expandwindow.N2MASSTX.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS_ADDREM_N2MASSTX"])
        self.TS_ADDREM.expandwindow.FLOWET.SetIntValue(received_dic_c["data"]["PARA_T"]["TS_ADDREM_FLOWET"]/1000)
        self.TS_ADDREM.expandwindow.TS1_MASS.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS1_MASS"])
        self.TS_ADDREM.expandwindow.TS2_MASS.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS2_MASS"])
        self.TS_ADDREM.expandwindow.TS3_MASS.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["TS3_MASS"])
        self.TS_ADDREM.expandwindow.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.TS_ADDREM.objectname])

        self.TS_EMPTY.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.TS_EMPTY.objectname])
        self.TS_EMPTY.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.TS_EMPTY.objectname])
        self.TS_EMPTY.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.TS_EMPTY.objectname])

        self.TS_EMPTYALL.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.TS_EMPTYALL.objectname])
        self.TS_EMPTYALL.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.TS_EMPTYALL.objectname])
        self.TS_EMPTYALL.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.TS_EMPTYALL.objectname])

        self.PU_PRIME.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.PU_PRIME.objectname])
        self.PU_PRIME.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.PU_PRIME.objectname])
        self.PU_PRIME.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.PU_PRIME.objectname])

        self.WRITE_SLOWDAQ.Running.UpdateColor(received_dic_c["data"]["Procedure"]["Running"][self.WRITE_SLOWDAQ.objectname])
        self.WRITE_SLOWDAQ.INTLKD.UpdateColor(received_dic_c["data"]["Procedure"]["INTLKD"][self.WRITE_SLOWDAQ.objectname])
        self.WRITE_SLOWDAQ.EXIT.SetValue(received_dic_c["data"]["Procedure"]["EXIT"][self.WRITE_SLOWDAQ.objectname])

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
            received_dic_c["data"]["TIME"]["PCYCLE_EXPTIME"])
        self.PRESSURE_CYCLE.expandwindow.MAXEXPTIME_RD.SetIntValue(
            received_dic_c["data"]["PARA_T"]["PCYCLE_MAXEXPTIME"]/1000)
        self.PRESSURE_CYCLE.expandwindow.MAXEQTIME_RD.SetIntValue(
            received_dic_c["data"]["PARA_T"]["PCYCLE_MAXEQTIME"]/1000)
        self.PRESSURE_CYCLE.expandwindow.MAXEQPDIFF_RD.SetValue(
            received_dic_c["data"]["PARA_F"]["PCYCLE_MAXEQPDIFF"])
        self.PRESSURE_CYCLE.expandwindow.MAXACCTIME_RD.SetIntValue(
            received_dic_c["data"]["PARA_T"]["PCYCLE_MAXACCTIME"]/1000)
        self.PRESSURE_CYCLE.expandwindow.MAXACCDPDT_RD.SetValue(
            received_dic_c["data"]["PARA_F"]["PCYCLE_MAXACCDPDT"])
        self.PRESSURE_CYCLE.expandwindow.MAXBLEEDTIME_RD.SetIntValue(
            received_dic_c["data"]["PARA_T"]["PCYCLE_MAXBLEEDTIME"]/1000)
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


        #
        #
        # self.AlarmButton.SubWindow.LT3335.UpdateAlarm(
        #     received_dic_c["Alarm"]["LEFT_REAL"][self.AlarmButton.SubWindow.LT3335.Label.text()])
        # self.AlarmButton.SubWindow.LT3335.Indicator.SetValue(
        #     received_dic_c["data"]["LEFT_REAL"]["value"][self.AlarmButton.SubWindow.LT3335.Label.text()])
        # self.AlarmButton.SubWindow.LT3335.Low_Read.SetValue(
        #     received_dic_c["data"]["LEFT_REAL"]["low"][self.AlarmButton.SubWindow.LT3335.Label.text()])
        # self.AlarmButton.SubWindow.LT3335.High_Read.SetValue(
        #     received_dic_c["data"]["LEFT_REAL"]["high"][self.AlarmButton.SubWindow.LT3335.Label.text()])




        # update value in a Matrix

        # AlarmMatrix = [self.AlarmButton.SubWindow.TT2101.Alarm, self.AlarmButton.SubWindow.TT2111.Alarm, self.AlarmButton.SubWindow.TT2113.Alarm, self.AlarmButton.SubWindow.TT2118.Alarm,
        #                          self.AlarmButton.SubWindow.TT2119.Alarm,
        #                          self.AlarmButton.SubWindow.TT4330.Alarm, self.AlarmButton.SubWindow.TT6203.Alarm, self.AlarmButton.SubWindow.TT6207.Alarm, self.AlarmButton.SubWindow.TT6211.Alarm,
        #                          self.AlarmButton.SubWindow.TT6213.Alarm,
        #                          self.AlarmButton.SubWindow.TT6222.Alarm, self.AlarmButton.SubWindow.TT6407.Alarm, self.AlarmButton.SubWindow.TT6408.Alarm, self.AlarmButton.SubWindow.TT6409.Alarm,
        #                          self.AlarmButton.SubWindow.TT6415.Alarm,
        #                          self.AlarmButton.SubWindow.TT6416.Alarm,
        #                          self.AlarmButton.SubWindow.TT2420.Alarm, self.AlarmButton.SubWindow.TT2422.Alarm, self.AlarmButton.SubWindow.TT2424.Alarm, self.AlarmButton.SubWindow.TT2425.Alarm,
        #                          self.AlarmButton.SubWindow.TT2442.Alarm,
        #                          self.AlarmButton.SubWindow.TT2403.Alarm, self.AlarmButton.SubWindow.TT2418.Alarm, self.AlarmButton.SubWindow.TT2427.Alarm, self.AlarmButton.SubWindow.TT2429.Alarm,
        #                          self.AlarmButton.SubWindow.TT2431.Alarm,
        #                          self.AlarmButton.SubWindow.TT2441.Alarm, self.AlarmButton.SubWindow.TT2414.Alarm, self.AlarmButton.SubWindow.TT2413.Alarm, self.AlarmButton.SubWindow.TT2412.Alarm,
        #                          self.AlarmButton.SubWindow.TT2415.Alarm,
        #                          self.AlarmButton.SubWindow.TT2409.Alarm, self.AlarmButton.SubWindow.TT2436.Alarm, self.AlarmButton.SubWindow.TT2438.Alarm, self.AlarmButton.SubWindow.TT2440.Alarm,
        #                          self.AlarmButton.SubWindow.TT2402.Alarm,
        #                          self.AlarmButton.SubWindow.TT2411.Alarm, self.AlarmButton.SubWindow.TT2443.Alarm, self.AlarmButton.SubWindow.TT2417.Alarm, self.AlarmButton.SubWindow.TT2404.Alarm,
        #                          self.AlarmButton.SubWindow.TT2408.Alarm,
        #                          self.AlarmButton.SubWindow.TT2407.Alarm, self.AlarmButton.SubWindow.TT2406.Alarm, self.AlarmButton.SubWindow.TT2428.Alarm, self.AlarmButton.SubWindow.TT2432.Alarm,
        #                          self.AlarmButton.SubWindow.TT2421.Alarm,
        #                          self.AlarmButton.SubWindow.TT2416.Alarm, self.AlarmButton.SubWindow.TT2439.Alarm, self.AlarmButton.SubWindow.TT2419.Alarm, self.AlarmButton.SubWindow.TT2423.Alarm,
        #                          self.AlarmButton.SubWindow.TT2426.Alarm,
        #                          self.AlarmButton.SubWindow.TT2430.Alarm, self.AlarmButton.SubWindow.TT2450.Alarm, self.AlarmButton.SubWindow.TT2401.Alarm, self.AlarmButton.SubWindow.TT2449.Alarm,
        #                          self.AlarmButton.SubWindow.TT2445.Alarm,
        #                          self.AlarmButton.SubWindow.TT2444.Alarm, self.AlarmButton.SubWindow.TT2435.Alarm, self.AlarmButton.SubWindow.TT2437.Alarm, self.AlarmButton.SubWindow.TT2446.Alarm,
        #                          self.AlarmButton.SubWindow.TT2447.Alarm,
        #                          self.AlarmButton.SubWindow.TT2448.Alarm, self.AlarmButton.SubWindow.TT2410.Alarm, self.AlarmButton.SubWindow.TT2405.Alarm, self.AlarmButton.SubWindow.TT6220.Alarm,
        #                          self.AlarmButton.SubWindow.TT6401.Alarm,
        #                          self.AlarmButton.SubWindow.TT6404.Alarm, self.AlarmButton.SubWindow.TT6405.Alarm, self.AlarmButton.SubWindow.TT6406.Alarm, self.AlarmButton.SubWindow.TT6410.Alarm,
        #                          self.AlarmButton.SubWindow.TT6411.Alarm,
        #                          self.AlarmButton.SubWindow.TT6412.Alarm, self.AlarmButton.SubWindow.TT6413.Alarm, self.AlarmButton.SubWindow.TT6414.Alarm,
        #                          self.AlarmButton.SubWindow.PT2316.Alarm, self.AlarmButton.SubWindow.PT2330.Alarm, self.AlarmButton.SubWindow.PT2335.Alarm,
        #                          self.AlarmButton.SubWindow.PT3308.Alarm, self.AlarmButton.SubWindow.PT3309.Alarm, self.AlarmButton.SubWindow.PT3311.Alarm, self.AlarmButton.SubWindow.PT3314.Alarm,
        #                          self.AlarmButton.SubWindow.PT3320.Alarm, self.AlarmButton.SubWindow.PT3332.Alarm, self.AlarmButton.SubWindow.PT3333.Alarm, self.AlarmButton.SubWindow.PT4306.Alarm, self.AlarmButton.SubWindow.PT4315.Alarm,
        #                          self.AlarmButton.SubWindow.PT4319.Alarm,
        #                          self.AlarmButton.SubWindow.PT4322.Alarm, self.AlarmButton.SubWindow.PT4325.Alarm, self.AlarmButton.SubWindow.LT3335.Alarm]

        AlarmMatrix= []
        for element in self.AlarmMatrix:
            AlarmMatrix.append(element.Alarm)
        self.update_alarmwindow(AlarmMatrix)



        # print("PV4307_OUT", received_dic_c["data"]["Valve"]["OUT"]["PV4307"])
        # print("PV4307_MAN", received_dic_c["data"]["Valve"]["MAN"]["PV4307"])
        # print("PV5305_OUT", received_dic_c["data"]["Valve"]["OUT"]["PV5305"])
        # print("PV5305_MAN", received_dic_c["data"]["Valve"]["MAN"]["PV5305"])
        # print("SV3307_OUT", received_dic_c["data"]["Valve"]["OUT"]["SV3307"])
        # print("SV3307_MAN", received_dic_c["data"]["Valve"]["MAN"]["SV3307"])
        # print(received_dic_c["data"]["Valve"]["MAN"]["PV1344"])

        # set whether Valves are manually active or not

        # self.PV1344.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV1344"])
        # self.PV4307.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV4307"])
        # self.PV4308.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV4308"])
        # self.PV4317.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV4317"])
        # self.PV4318.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV4318"])
        # self.PV4321.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV4321"])
        # self.PV4324.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV4324"])
        # self.PV5305.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV5305"])
        # self.PV5306.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV5306"])
        # self.PV5307.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV5307"])
        # self.PV5309.Activate(received_dic_c["data"]["Valve"]["MAN"]["PV5309"])
        # self.SV3307.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV3307"])
        # self.SV3310.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV3310"])
        # self.SV3322.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV3322"])
        # self.SV3325.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV3325"])
        # self.SV3329.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV3329"])
        # self.SV4327.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV4327"])
        # self.SV4328.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV4328"])
        # self.SV4329.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV4329"])
        # self.SV4331.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV4331"])
        # self.SV4332.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV4332"])
        # self.SV4337.Activate(received_dic_c["data"]["Valve"]["MAN"]["SV4337"])
        # self.HFSV3312.Activate(received_dic_c["data"]["Valve"]["MAN"]["HFSV3312"])
        # self.HFSV3323.Activate(received_dic_c["data"]["Valve"]["MAN"]["HFSV3323"])
        # self.HFSV3331.Activate(received_dic_c["data"]["Valve"]["MAN"]["HFSV3331"])

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


        # self.PUMP3305.LOOP2PTSubWindow.Mode.Activate(received_dic_c["data"]["LOOP2PT"]["MAN"]["PUMP3305"])
        # self.PUMP3305.State.Activate(received_dic_c["data"]["LOOP2PT"]["MAN"]["PUMP3305"])


        # need to be verified that this is not needed at all
        # self.SERVO3321.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["SERVO3321"])
        # self.SERVO3321.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["SERVO3321"])
        #
        # self.HTR6225.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6225"])
        # self.HTR6225.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6225"])
        #
        # self.HTR2123.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2123"])
        # self.HTR2123.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2123"])
        #
        # self.HTR2124.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2124"])
        # self.HTR2124.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2124"])
        #
        # self.HTR2125.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2125"])
        # self.HTR2125.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2125"])
        #
        # self.HTR1202.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR1202"])
        # self.HTR1202.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR1202"])
        #
        # self.HTR2203.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2203"])
        # self.HTR2203.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2203"])
        #
        # self.HTR6202.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6202"])
        # self.HTR6202.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6202"])
        #
        # self.HTR6206.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6206"])
        # self.HTR6206.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6206"])
        #
        # self.HTR6210.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6210"])
        # self.HTR6210.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6210"])
        #
        # self.HTR6223.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6223"])
        # self.HTR6223.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6223"])
        #
        # self.HTR6224.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6224"])
        # self.HTR6224.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6224"])
        #
        # self.HTR6219.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6219"])
        # self.HTR6219.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6219"])
        #
        # self.HTR6221.LOOPPIDWindow.Mode.Activate(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6221"])
        # self.HTR6221.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6221"])
        #
        # self.HTR6214.LOOPPIDWindow.Mode.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6214"])
        # self.HTR6214.State.Activate(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6214"])
        #


        #update Din widget
        self.PUMP3305_CON.UpdateColor(received_dic_c["data"]["Din"]["value"]["PUMP3305_CON"])
        self.PUMP3305_OL.UpdateColor(received_dic_c["data"]["Din"]["value"]["PUMP3305_OL"])
        self.ES3347.UpdateColor(received_dic_c["data"]["Din"]["value"]["ES3347"])
        self.LS3338.UpdateColor(received_dic_c["data"]["Din"]["value"]["LS3338"])
        self.LS3339.UpdateColor(received_dic_c["data"]["Din"]["value"]["LS3339"])
        self.PS1361.UpdateColor(received_dic_c["data"]["Din"]["value"]["PS1361"])
        self.PS2352.UpdateColor(received_dic_c["data"]["Din"]["value"]["PS2352"])
        self.PS8302.UpdateColor(received_dic_c["data"]["Din"]["value"]["PS8302"])

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




        # if received_dic_c["data"]["LOOP2PT"]["MAN"]["PUMP3305"] and not received_dic_c["data"]["LOOP2PT"]["ERR"]["PUMP3305"]:
        #
        #     self.PUMP3305.ActiveState.UpdateColor(True)
        # else:
        #     self.PUMP3305.ActiveState.UpdateColor(False)

        # reset Valves' widget busy status

        # if commands are rejected by PLC, set busy back
        # if received_dic_c["data"]["Valve"]["Busy"]["PV1344"] ==True:
        #     self.PV1344.ButtonTransitionState(False)
        #     # self.Valve_buffer["PV1344"] = received_dic_c["data"]["Valve"]["OUT"]["PV1344"]
        #
        # else:
        #     #if not rejected, and new value is different from the previous one(the valve status changed), then set busy back
        #     self.PV1344.ButtonTransitionState(True)
        #
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["PV4307"] == True:
        #     self.PV4307.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["PV4307"] != self.Valve_buffer["PV4307"]:
        #         self.PV4307.ButtonTransitionState(False)
        #         self.Valve_buffer["PV4307"] = received_dic_c["data"]["Valve"]["OUT"]["PV4307"]
        #     else:
        #         pass
        #
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["PV4308"] == True:
        #     self.PV4308.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["PV4308"] != self.Valve_buffer["PV4308"]:
        #         self.PV4308.ButtonTransitionState(False)
        #         self.Valve_buffer["PV4308"] = received_dic_c["data"]["Valve"]["OUT"]["PV4308"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["PV4317"] == True:
        #     self.PV4317.ButtonTransitionState(True)
        # elif not received_dic_c["data"]["Valve"]["Busy"]["PV4317"]:
        #     self.PV4317.ButtonTransitionState(False)
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["PV4318"] == True:
        #     self.PV4318.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["PV4318"] != self.Valve_buffer["PV4318"]:
        #         self.PV4318.ButtonTransitionState(False)
        #         self.Valve_buffer["PV4318"] = received_dic_c["data"]["Valve"]["OUT"]["PV4318"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["PV4321"] == True:
        #     self.PV4321.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["PV4321"] != self.Valve_buffer["PV4321"]:
        #         self.PV4321.ButtonTransitionState(False)
        #         self.Valve_buffer["PV4321"] = received_dic_c["data"]["Valve"]["OUT"]["PV4321"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["PV4324"] == True:
        #     self.PV4324.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["PV4324"] != self.Valve_buffer["PV4324"]:
        #         self.PV4324.ButtonTransitionState(False)
        #         self.Valve_buffer["PV4324"] = received_dic_c["data"]["Valve"]["OUT"]["PV4324"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["PV5305"] == True:
        #     self.PV5305.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["PV5305"] != self.Valve_buffer["PV5305"]:
        #         self.PV5305.ButtonTransitionState(False)
        #         self.Valve_buffer["PV5305"] = received_dic_c["data"]["Valve"]["OUT"]["PV5305"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["PV5306"] == True:
        #     self.PV5306.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["PV5306"] != self.Valve_buffer["PV5306"]:
        #         self.PV5306.ButtonTransitionState(False)
        #         self.Valve_buffer["PV5306"] = received_dic_c["data"]["Valve"]["OUT"]["PV5306"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["PV5307"] == True:
        #     self.PV5307.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["PV5307"] != self.Valve_buffer["PV5307"]:
        #         self.PV5307.ButtonTransitionState(False)
        #         self.Valve_buffer["PV5307"] = received_dic_c["data"]["Valve"]["OUT"]["PV5307"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["PV5309"] == True:
        #     self.PV5309.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["PV5309"] != self.Valve_buffer["PV5309"]:
        #         self.PV5309.ButtonTransitionState(False)
        #         self.Valve_buffer["PV5309"] = received_dic_c["data"]["Valve"]["OUT"]["PV5309"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["SV3307"] == True:
        #     self.SV3307.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV3307"] != self.Valve_buffer["SV3307"]:
        #         self.SV3307.ButtonTransitionState(False)
        #         self.Valve_buffer["SV3307"] = received_dic_c["data"]["Valve"]["OUT"]["SV3307"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["SV3310"] == True:
        #     self.SV3310.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV3310"] != self.Valve_buffer["SV3310"]:
        #         self.SV3310.ButtonTransitionState(False)
        #         self.Valve_buffer["SV3310"] = received_dic_c["data"]["Valve"]["OUT"]["SV3310"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["SV3322"] == True:
        #     self.SV3322.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV3322"] != self.Valve_buffer["SV3322"]:
        #         self.SV3322.ButtonTransitionState(False)
        #         self.Valve_buffer["SV3322"] = received_dic_c["data"]["Valve"]["OUT"]["SV3322"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["SV3325"] == True:
        #     self.SV3325.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV3325"] != self.Valve_buffer["SV3325"]:
        #         self.SV3325.ButtonTransitionState(False)
        #         self.Valve_buffer["SV3325"] = received_dic_c["data"]["Valve"]["OUT"]["SV3325"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["SV3329"] == True:
        #     self.SV3329.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV3329"] != self.Valve_buffer["SV3329"]:
        #         self.SV3329.ButtonTransitionState(False)
        #         self.Valve_buffer["SV3329"] = received_dic_c["data"]["Valve"]["OUT"]["SV3329"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["SV4327"] == True:
        #     self.SV4327.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV4327"] != self.Valve_buffer["SV4327"]:
        #         self.SV4327.ButtonTransitionState(False)
        #         self.Valve_buffer["SV4327"] = received_dic_c["data"]["Valve"]["OUT"]["SV4327"]
        #     else:
        #         pass
        # print("SV4328",received_dic_c["data"]["Valve"]["Busy"]["SV4328"])
        # if received_dic_c["data"]["Valve"]["Busy"]["SV4328"] == True:
        #     self.SV4328.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV4328"] != self.Valve_buffer["SV4328"]:
        #         self.SV4328.ButtonTransitionState(False)
        #         self.Valve_buffer["SV4328"] = received_dic_c["data"]["Valve"]["OUT"]["SV4328"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["SV4329"] == True:
        #     self.SV4329.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV4329"] != self.Valve_buffer["SV4329"]:
        #         self.SV4329.ButtonTransitionState(False)
        #         self.Valve_buffer["SV4329"] = received_dic_c["data"]["Valve"]["OUT"]["SV4329"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["SV4331"] == True:
        #     self.SV4331.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV4331"] != self.Valve_buffer["SV4331"]:
        #         self.SV4331.ButtonTransitionState(False)
        #         self.Valve_buffer["SV4331"] = received_dic_c["data"]["Valve"]["OUT"]["SV4331"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["SV4332"] == True:
        #     self.SV4332.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV4332"] != self.Valve_buffer["SV4332"]:
        #         self.SV4332.ButtonTransitionState(False)
        #         self.Valve_buffer["SV4332"] = received_dic_c["data"]["Valve"]["OUT"]["SV4332"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["SV4337"] == True:
        #     self.SV4337.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["SV4337"] != self.Valve_buffer["SV4337"]:
        #         self.SV4337.ButtonTransitionState(False)
        #         self.Valve_buffer["SV4337"] = received_dic_c["data"]["Valve"]["OUT"]["SV4337"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["HFSV3312"] == True:
        #     self.HFSV3312.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"] != self.Valve_buffer["HFSV3312"]:
        #         self.HFSV3312.ButtonTransitionState(False)
        #         self.Valve_buffer["HFSV3312"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["HFSV3323"] == True:
        #     self.HFSV3323.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"] != self.Valve_buffer["HFSV3323"]:
        #         self.HFSV3323.ButtonTransitionState(False)
        #         self.Valve_buffer["HFSV3323"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"]
        #     else:
        #         pass
        #
        #
        # if received_dic_c["data"]["Valve"]["Busy"]["HFSV3331"] == True:
        #     self.HFSV3331.ButtonTransitionState(False)
        #
        # else:
        #     if received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"] != self.Valve_buffer["HFSV3331"]:
        #         self.HFSV3331.ButtonTransitionState(False)
        #         self.Valve_buffer["HFSV3331"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"]
        #     else:
        #         pass


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


        # if received_dic_c["data"]["Valve"]["OUT"]["PV1344"] != self.Valve_buffer["PV1344"]:
        #     self.PV1344.ButtonTransitionState(False)
        #     self.Valve_buffer["PV1344"] = received_dic_c["data"]["Valve"]["OUT"]["PV1344"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4307"] != self.Valve_buffer["PV4307"]:
        #     self.PV4307.ButtonTransitionState(False)
        #     self.Valve_buffer["PV4307"] = received_dic_c["data"]["Valve"]["OUT"]["PV4307"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4308"] != self.Valve_buffer["PV4308"]:
        #     self.PV4308.ButtonTransitionState(False)
        #     self.Valve_buffer["PV4308"] = received_dic_c["data"]["Valve"]["OUT"]["PV4308"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4317"] != self.Valve_buffer["PV4317"]:
        #     self.PV4317.ButtonTransitionState(False)
        #     self.Valve_buffer["PV4317"] = received_dic_c["data"]["Valve"]["OUT"]["PV4317"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4318"] != self.Valve_buffer["PV4318"]:
        #     self.PV4318.ButtonTransitionState(False)
        #     self.Valve_buffer["PV4318"] = received_dic_c["data"]["Valve"]["OUT"]["PV4318"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4321"] != self.Valve_buffer["PV4321"]:
        #     self.PV4321.ButtonTransitionState(False)
        #     self.Valve_buffer["PV4321"] = received_dic_c["data"]["Valve"]["OUT"]["PV4321"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4324"] != self.Valve_buffer["PV4324"]:
        #     self.PV4324.ButtonTransitionState(False)
        #     self.Valve_buffer["PV4324"] = received_dic_c["data"]["Valve"]["OUT"]["PV4324"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV5305"] != self.Valve_buffer["PV5305"]:
        #     self.PV5305.ButtonTransitionState(False)
        #     self.Valve_buffer["PV5305"] = received_dic_c["data"]["Valve"]["OUT"]["PV5305"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV5306"] != self.Valve_buffer["PV5306"]:
        #     self.PV5306.ButtonTransitionState(False)
        #     self.Valve_buffer["PV5306"] = received_dic_c["data"]["Valve"]["OUT"]["PV5306"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV5307"] != self.Valve_buffer["PV5307"]:
        #     self.PV5307.ButtonTransitionState(False)
        #     self.Valve_buffer["PV5307"] = received_dic_c["data"]["Valve"]["OUT"]["PV5307"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV5309"] != self.Valve_buffer["PV5309"]:
        #     self.PV5309.ButtonTransitionState(False)
        #     self.Valve_buffer["PV5309"] = received_dic_c["data"]["Valve"]["OUT"]["PV5309"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV3307"] != self.Valve_buffer["SV3307"]:
        #     self.SV3307.ButtonTransitionState(False)
        #     self.Valve_buffer["SV3307"] = received_dic_c["data"]["Valve"]["OUT"]["SV3307"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV3310"] != self.Valve_buffer["SV3310"]:
        #     self.SV3310.ButtonTransitionState(False)
        #     self.Valve_buffer["SV3310"] = received_dic_c["data"]["Valve"]["OUT"]["SV3310"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV3322"] != self.Valve_buffer["SV3322"]:
        #     self.SV3322.ButtonTransitionState(False)
        #     self.Valve_buffer["SV3322"] = received_dic_c["data"]["Valve"]["OUT"]["SV3322"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV3325"] != self.Valve_buffer["SV3325"]:
        #     self.SV3325.ButtonTransitionState(False)
        #     self.Valve_buffer["SV3325"] = received_dic_c["data"]["Valve"]["OUT"]["SV3325"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV3329"] != self.Valve_buffer["SV3329"]:
        #     self.SV3329.ButtonTransitionState(False)
        #     self.Valve_buffer["SV3329"] = received_dic_c["data"]["Valve"]["OUT"]["SV3329"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4327"] != self.Valve_buffer["SV4327"]:
        #     self.SV4327.ButtonTransitionState(False)
        #     self.Valve_buffer["SV4327"] = received_dic_c["data"]["Valve"]["OUT"]["SV4327"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4328"] != self.Valve_buffer["SV4328"]:
        #     self.SV4328.ButtonTransitionState(False)
        #     self.Valve_buffer["SV4328"] = received_dic_c["data"]["Valve"]["OUT"]["SV4328"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4329"] != self.Valve_buffer["SV4329"]:
        #     self.SV4329.ButtonTransitionState(False)
        #     self.Valve_buffer["SV4329"] = received_dic_c["data"]["Valve"]["OUT"]["SV4329"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4331"] != self.Valve_buffer["SV4331"]:
        #     self.SV4331.ButtonTransitionState(False)
        #     self.Valve_buffer["SV4331"] = received_dic_c["data"]["Valve"]["OUT"]["SV4331"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4332"] != self.Valve_buffer["SV4332"]:
        #     self.SV4332.ButtonTransitionState(False)
        #     self.Valve_buffer["SV4332"] = received_dic_c["data"]["Valve"]["OUT"]["SV4332"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4337"] != self.Valve_buffer["SV4337"]:
        #     self.SV4337.ButtonTransitionState(False)
        #     self.Valve_buffer["SV4337"] = received_dic_c["data"]["Valve"]["OUT"]["SV4337"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"] != self.Valve_buffer["HFSV3312"]:
        #     self.HFSV3312.ButtonTransitionState(False)
        #     self.Valve_buffer["HFSV3312"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"] != self.Valve_buffer["HFSV3323"]:
        #     self.HFSV3323.ButtonTransitionState(False)
        #     self.Valve_buffer["HFSV3323"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"] != self.Valve_buffer["HFSV3331"]:
        #     self.HFSV3331.ButtonTransitionState(False)
        #     self.Valve_buffer["HFSV3331"] = received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"]
        # else:
        #     pass

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


        # if received_dic_c["data"]["LOOPPID"]["Busy"]["SERVO3321"] ==True:
        #     self.SERVO3321.State.ButtonTransitionState(False)
        #     self.SERVO3321.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"] != self.LOOPPID_EN_buffer["SERVO3321"]:
        #         self.SERVO3321.State.ButtonTransitionState(False)
        #         self.SERVO3321.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["SERVO3321"] = received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"]
        #     else:
        #         pass
        #
        #
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6225"] ==True:
        #     self.HTR6225.State.ButtonTransitionState(False)
        #     self.HTR6225.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"] != self.LOOPPID_EN_buffer["HTR6225"]:
        #         self.HTR6225.State.ButtonTransitionState(False)
        #         self.HTR6225.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR6225"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2123"] ==True:
        #     self.HTR2123.State.ButtonTransitionState(False)
        #     self.HTR2123.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"] != self.LOOPPID_EN_buffer["HTR2123"]:
        #         self.HTR2123.State.ButtonTransitionState(False)
        #         self.HTR2123.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR2123"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2124"] ==True:
        #     self.HTR2124.State.ButtonTransitionState(False)
        #     self.HTR2124.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"] != self.LOOPPID_EN_buffer["HTR2124"]:
        #         self.HTR2124.State.ButtonTransitionState(False)
        #         self.HTR2124.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR2124"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2125"] ==True:
        #     self.HTR2125.State.ButtonTransitionState(False)
        #     self.HTR2125.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"] != self.LOOPPID_EN_buffer["HTR2125"]:
        #         self.HTR2125.State.ButtonTransitionState(False)
        #         self.HTR2125.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR2125"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR1202"] ==True:
        #     self.HTR1202.State.ButtonTransitionState(False)
        #     self.HTR1202.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"] != self.LOOPPID_EN_buffer["HTR1202"]:
        #         self.HTR1202.State.ButtonTransitionState(False)
        #         self.HTR1202.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR1202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR2203"] ==True:
        #     self.HTR2203.State.ButtonTransitionState(False)
        #     self.HTR2203.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"] != self.LOOPPID_EN_buffer["HTR2203"]:
        #         self.HTR2203.State.ButtonTransitionState(False)
        #         self.HTR2203.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR2203"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6202"] ==True:
        #     self.HTR6202.State.ButtonTransitionState(False)
        #     self.HTR6202.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"] != self.LOOPPID_EN_buffer["HTR6202"]:
        #         self.HTR6202.State.ButtonTransitionState(False)
        #         self.HTR6202.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         # self.LOOPPID_EN_buffer["HTR6202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6206"] ==True:
        #     self.HTR6206.State.ButtonTransitionState(False)
        #     self.HTR6206.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"] != self.LOOPPID_EN_buffer["HTR6206"]:
        #         self.HTR6206.State.ButtonTransitionState(False)
        #         self.HTR6206.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR6206"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6210"] ==True:
        #     self.HTR6210.State.ButtonTransitionState(False)
        #     self.HTR6210.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"] != self.LOOPPID_EN_buffer["HTR6210"]:
        #         self.HTR6210.State.ButtonTransitionState(False)
        #         self.HTR6210.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR6210"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6223"] ==True:
        #     self.HTR6223.State.ButtonTransitionState(False)
        #     self.HTR6223.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"] != self.LOOPPID_EN_buffer["HTR6223"]:
        #         self.HTR6223.State.ButtonTransitionState(False)
        #         self.HTR6223.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR6223"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6224"] ==True:
        #     self.HTR6224.State.ButtonTransitionState(False)
        #     self.HTR6224.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"] != self.LOOPPID_EN_buffer["HTR6224"]:
        #         self.HTR6224.State.ButtonTransitionState(False)
        #         self.HTR6224.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR6224"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6219"] ==True:
        #     self.HTR6219.State.ButtonTransitionState(False)
        #     self.HTR6219.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"] != self.LOOPPID_EN_buffer["HTR6219"]:
        #         self.HTR6219.State.ButtonTransitionState(False)
        #         self.HTR6219.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR6219"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6221"] ==True:
        #     self.HTR6221.State.ButtonTransitionState(False)
        #     self.HTR6221.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"] != self.LOOPPID_EN_buffer["HTR6221"]:
        #         self.HTR6221.State.ButtonTransitionState(False)
        #         self.HTR6221.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR6221"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"]
        #     else:
        #         pass

        if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6202"]:
            self.HTR6202_v2.ButtonTransitionState(True)
            self.HTR6202_v2.LOOPPIDWindow.ButtonTransitionState(True)
        elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6202"]:
            self.HTR6202_v2.ButtonTransitionState(False)
            self.HTR6202_v2.LOOPPIDWindow.ButtonTransitionState(False)
        else:
            pass

        # if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6214"] ==True:
        #     self.HTR6214.State.ButtonTransitionState(False)
        #     self.HTR6214.HeaterSubWindow.Mode.ButtonTransitionState(False)
        # else:
        #     if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"] != self.LOOPPID_EN_buffer["HTR6214"]:
        #         self.HTR6214.State.ButtonTransitionState(False)
        #         self.HTR6214.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOPPID_EN_buffer["HTR6214"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"]
        #     else:
        #         pass


        # if received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"] != self.LOOPPID_EN_buffer["SERVO3321"]:
        #     self.SERVO3321.State.ButtonTransitionState(False)
        #     self.SERVO3321.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["SERVO3321"] = received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"]
        # else:
        #     pass
        #
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"] != self.LOOPPID_EN_buffer["HTR6225"]:
        #     self.HTR6225.State.ButtonTransitionState(False)
        #     self.HTR6225.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR6225"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"] != self.LOOPPID_EN_buffer["HTR2123"]:
        #     self.HTR2123.State.ButtonTransitionState(False)
        #     self.HTR2123.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR2123"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"] != self.LOOPPID_EN_buffer["HTR2124"]:
        #     self.HTR2124.State.ButtonTransitionState(False)
        #     self.HTR2124.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR2124"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"] != self.LOOPPID_EN_buffer["HTR2125"]:
        #     self.HTR2125.State.ButtonTransitionState(False)
        #     self.HTR2125.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR2125"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"] != self.LOOPPID_EN_buffer["HTR1202"]:
        #     self.HTR1202.State.ButtonTransitionState(False)
        #     self.HTR1202.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR1202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"] != self.LOOPPID_EN_buffer["HTR2203"]:
        #     self.HTR2203.State.ButtonTransitionState(False)
        #     self.HTR2203.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR2203"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"] != self.LOOPPID_EN_buffer["HTR6202"]:
        #     self.HTR6202.State.ButtonTransitionState(False)
        #     self.HTR6202.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR6202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"] != self.LOOPPID_EN_buffer["HTR6206"]:
        #     self.HTR6206.State.ButtonTransitionState(False)
        #     self.HTR6206.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR6206"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"] != self.LOOPPID_EN_buffer["HTR6210"]:
        #     self.HTR6210.State.ButtonTransitionState(False)
        #     self.HTR6210.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR6210"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"] != self.LOOPPID_EN_buffer["HTR6223"]:
        #     self.HTR6223.State.ButtonTransitionState(False)
        #     self.HTR6223.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR6223"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"] != self.LOOPPID_EN_buffer["HTR6224"]:
        #     self.HTR6224.State.ButtonTransitionState(False)
        #     self.HTR6224.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR6224"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"] != self.LOOPPID_EN_buffer["HTR6219"]:
        #     self.HTR6219.State.ButtonTransitionState(False)
        #     self.HTR6219.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR6219"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"] != self.LOOPPID_EN_buffer["HTR6221"]:
        #     self.HTR6221.State.ButtonTransitionState(False)
        #     self.HTR6221.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR6221"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"]
        # else:
        #     pass
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"] != self.LOOPPID_EN_buffer["HTR6214"]:
        #     self.HTR6214.State.ButtonTransitionState(False)
        #     self.HTR6214.HeaterSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOPPID_EN_buffer["HTR6214"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"]
        # else:
        #     pass
        #
        # #LOOP2PT part
        # if received_dic_c["data"]["LOOP2PT"]["Busy"]["PUMP3305"] == True:
        #     self.PUMP3305.State.ButtonTransitionState(False)
        #     self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonTransitionState(False)
        #     # self.LOOP2PT_OUT_buffer["PUMP3305"] = received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]
        # else:
        #     if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"] != self.LOOP2PT_OUT_buffer["PUMP3305"]:
        #         self.PUMP3305.State.ButtonTransitionState(False)
        #         self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonTransitionState(False)
        #         self.LOOP2PT_OUT_buffer["PUMP3305"] = received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]
        #     else:
        #         pass
        #
        # if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"] != self.LOOP2PT_OUT_buffer["PUMP3305"]:
        #     self.PUMP3305.State.ButtonTransitionState(False)
        #     self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonTransitionState(False)
        #     self.LOOP2PT_OUT_buffer["PUMP3305"] = received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]
        # else:
        #     pass



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

        # if received_dic_c["data"]["Valve"]["OUT"]["PV1344"]:
        #
        #     self.PV1344.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV1344.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4307"]:
        #
        #     self.PV4307.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV4307.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4308"]:
        #
        #     self.PV4308.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV4308.collapse.Set.ButtonRClicked()

        # if received_dic_c["data"]["Valve"]["OUT"]["PV4317"]:
        #
        #     self.PV4317.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV4317.collapse.Set.ButtonRClicked()

        # if not received_dic_c["data"]["Valve"]["MAN"]["PV4317"]:
        #     if received_dic_c["data"]["Valve"]["OUT"]["PV4317"]:
        #         self.PV4317.collapse.Set.ButtonLClicked()
        #     else:
        #         self.PV4317.collapse.Set.ButtonRClicked()
        #     self.Valve_buffer["PV4317"] = received_dic_c["data"]["Valve"]["OUT"]["PV4317"]
        # elif received_dic_c["data"]["Valve"]["MAN"]["PV4317"]:
        #     if received_dic_c["data"]["Valve"]["Busy"]["PV4317"]:
        #         if received_dic_c["data"]["Valve"]["OUT"]["PV4317"]:
        #             self.PV4317.collapse.Set.ButtonLClicked()
        #         else:
        #             self.PV4317.collapse.Set.ButtonRClicked()
        #         self.Valve_buffer["PV4317"] = received_dic_c["data"]["Valve"]["OUT"]["PV4317"]
        #     elif not received_dic_c["data"]["Valve"]["Busy"]["PV4317"]:
        #         print("PV4317", received_dic_c["data"]["Valve"]["OUT"]["PV4317"] != self.Valve_buffer["PV4317"])
        #         print("OUT", received_dic_c["data"]["Valve"]["OUT"]["PV4317"])
        #         print("Buffer", self.Valve_buffer["PV4317"])
        #         if received_dic_c["data"]["Valve"]["OUT"]["PV4317"] != self.Valve_buffer["PV4317"]:
        #             if received_dic_c["data"]["Valve"]["OUT"]["PV4317"]:
        #                 self.PV4317.collapse.Set.ButtonLClicked()
        #             else:
        #                 self.PV4317.collapse.Set.ButtonRClicked()
        #             self.Valve_buffer["PV4317"] = received_dic_c["data"]["Valve"]["OUT"]["PV4317"]
        #         else:
        #             pass



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

        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4318"]:
        #
        #     self.PV4318.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV4318.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4321"]:
        #
        #     self.PV4321.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV4321.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV4324"]:
        #
        #     self.PV4324.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV4324.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV5305"]:
        #
        #     self.PV5305.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV5305.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV5306"]:
        #
        #     self.PV5306.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV5306.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV5307"]:
        #
        #     self.PV5307.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV5307.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["PV5309"]:
        #
        #     self.PV5309.collapse.Set.ButtonLClicked()
        # else:
        #     self.PV5309.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV3307"]:
        #
        #     self.SV3307.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV3307.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV3310"]:
        #
        #     self.SV3310.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV3310.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV3322"]:
        #
        #     self.SV3322.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV3322.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV3325"]:
        #
        #     self.SV3325.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV3325.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV3329"]:
        #
        #     self.SV3329.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV3329.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4327"]:
        #
        #     self.SV4327.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV3307.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4328"]:
        #
        #     self.SV4328.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV4328.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4329"]:
        #
        #     self.SV4329.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV4329.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4331"]:
        #
        #     self.SV4331.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV4331.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4332"]:
        #
        #     self.SV4332.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV4332.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["SV4337"]:
        #
        #     self.SV4337.collapse.Set.ButtonLClicked()
        # else:
        #     self.SV4337.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["HFSV3312"]:
        #
        #     self.HFSV3312.collapse.Set.ButtonLClicked()
        # else:
        #     self.HFSV3312.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["HFSV3323"]:
        #
        #     self.HFSV3323.collapse.Set.ButtonLClicked()
        # else:
        #     self.HFSV3323.collapse.Set.ButtonRClicked()
        #
        # if received_dic_c["data"]["Valve"]["OUT"]["HFSV3331"]:
        #
        #     self.HFSV3331.collapse.Set.ButtonLClicked()
        # else:
        #     self.HFSV3331.collapse.Set.ButtonRClicked()


        # if received_dic_c["data"]["Switch"]["OUT"]["PUMP3305"]:
        #
        #     self.PUMP3305.collapse.Set.ButtonLClicked()
        # else:
        #     self.PUMP3305.collapse.Set.ButtonRClicked()

        if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]:
            self.PUMP3305_icon.Turnon()
        else:
            self.PUMP3305_icon.Turnoff()



#      FLAGs
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

        # if not received_dic_c["data"]["FLAG"]["MAN"]["MAN_HYD"]:
        #     if received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"]:
        #         self.MAN_HYD.Set.ButtonLClicked()
        #     else:
        #         self.MAN_HYD.Set.ButtonRClicked()
        # elif received_dic_c["data"]["FLAG"]["MAN"]["MAN_HYD"]:
        #     if received_dic_c["data"]["FLAG"]["Busy"]["MAN_HYD"]:
        #         if received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"]:
        #             self.MAN_HYD.Set.ButtonLClicked()
        #         else:
        #             self.MAN_HYD.Set.ButtonRClicked()
        #     elif not received_dic_c["data"]["FLAG"]["Busy"]["MAN_HYD"]:
        #         if received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"] != self.FLAG_buffer["MAN_HYD"]:
        #             if received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"]:
        #                 self.MAN_HYD.Set.ButtonLClicked()
        #             else:
        #                 self.MAN_HYD.Set.ButtonRClicked()
        #             self.FLAG__buffer["MAN_HYD"] = received_dic_c["data"]["FLAG"]["value"]["MAN_HYD"]
        #         else:
        #             pass

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

        # if received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"]:
        #
        #     self.SERVO3321.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.SERVO3321.State.ButtonLClicked()
        #
        # else:
        #     self.SERVO3321.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.SERVO3321.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"]:
        #
        #     self.HTR6225.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR6225.State.ButtonLClicked()
        #
        # else:
        #     self.HTR6225.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR6225.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"]:
        #
        #     self.HTR2123.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR2123.State.ButtonLClicked()
        #
        # else:
        #     self.HTR2123.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR2123.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"]:
        #
        #     self.HTR2124.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR2124.State.ButtonLClicked()
        #
        # else:
        #     self.HTR2124.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR2124.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"]:
        #
        #     self.HTR2125.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR2125.State.ButtonLClicked()
        #
        # else:
        #     self.HTR2125.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR2125.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"]:
        #
        #     self.HTR1202.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR1202.State.ButtonLClicked()
        #
        # else:
        #     self.HTR1202.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR1202.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"]:
        #
        #     self.HTR2203.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR2203.State.ButtonLClicked()
        #
        # else:
        #     self.HTR2203.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR2203.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]:
        #
        #     self.HTR6202.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR6202.State.ButtonLClicked()
        #
        # else:
        #     self.HTR6202.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR6202.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"]:
        #
        #     self.HTR6206.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR6206.State.ButtonLClicked()
        #
        # else:
        #     self.HTR6206.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR6206.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"]:
        #
        #     self.HTR6210.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR6210.State.ButtonLClicked()
        #
        # else:
        #     self.HTR6210.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR6210.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"]:
        #
        #     self.HTR6223.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR6223.State.ButtonLClicked()
        #
        # else:
        #     self.HTR6223.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR6223.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"]:
        #
        #     self.HTR6224.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR6224.State.ButtonLClicked()
        #
        # else:
        #     self.HTR6224.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR6224.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"]:
        #
        #     self.HTR6219.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR6219.State.ButtonLClicked()
        #
        # else:
        #     self.HTR6219.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR6219.State.ButtonRClicked()
        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"]:
        #
        #     self.HTR6221.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR6221.State.ButtonLClicked()
        #
        # else:
        #     self.HTR6221.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR6221.State.ButtonRClicked()
        #


        if not received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6202"]:
            if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]:
                self.HTR6202_v2.LOOPPIDWindow.Mode.ButtonLClicked()
                self.HTR6202_v2.State.ButtonLClicked()
            else:
                self.HTR6202_v2.LOOPPIDWindow.Mode.ButtonRClicked()
                self.HTR6202_v2.State.ButtonRClicked()
            self.LOOPPID_EN_buffer["HTR6202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]
        elif received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6202"]:
            if received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6202"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]:
                    self.HTR6202_v2.LOOPPIDWindow.Mode.ButtonLClicked()
                    self.HTR6202_v2.State.ButtonLClicked()
                else:
                    self.HTR6202_v2.LOOPPIDWindow.Mode.ButtonRClicked()
                    self.HTR6202_v2.State.ButtonRClicked()
                self.LOOPPID_EN_buffer["HTR6202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]
            elif not received_dic_c["data"]["LOOPPID"]["Busy"]["HTR6202"]:
                if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"] != self.LOOPPID_EN_buffer["HTR6202"]:
                    if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]:
                        self.HTR6202_v2.LOOPPIDWindow.Mode.ButtonLClicked()
                        self.HTR6202_v2.State.ButtonLClicked()
                    else:
                        self.HTR6202_v2.LOOPPIDWindow.Mode.ButtonRClicked()
                        self.HTR6202_v2.State.ButtonRClicked()
                    self.LOOPPID_EN_buffer["HTR6202"] = received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"]
                else:
                    pass

        self.HTR6202_v2.ColorLabel(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"])
        self.HTR6202_v2.Power.ColorButton(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"])



        #
        # if received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"]:
        #
        #     self.HTR6214.HeaterSubWindow.Mode.ButtonLClicked()
        #     self.HTR6214.State.ButtonLClicked()
        #
        # else:
        #     self.HTR6214.HeaterSubWindow.Mode.ButtonRClicked()
        #     self.HTR6214.State.ButtonRClicked()


        #LOOP2PT
        # if not received_dic_c["data"]["LOOP2PT"]["MAN"]["PUMP3305"]:
        #     print("MAN is false")
        #     print("PUMP3305_OUT",received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"])
        #     if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]:
        #
        #         self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonLClicked()
        #         self.PUMP3305.State.ButtonLClicked()
        #
        #     else:
        #         print("if out is false")
        #         self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonRClicked()
        #         self.PUMP3305.State.ButtonRClicked()
        # elif received_dic_c["data"]["LOOP2PT"]["MAN"]["PUMP3305"]:
        #     print("MAN is true")
        #     if received_dic_c["data"]["LOOP2PT"]["Busy"]["PUMP3305"]:
        #         if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]:
        #
        #             self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonLClicked()
        #             self.PUMP3305.State.ButtonLClicked()
        #
        #         else:
        #             self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonRClicked()
        #             self.PUMP3305.State.ButtonRClicked()
        #     elif not received_dic_c["data"]["LOOP2PT"]["Busy"]["PUMP3305"]:
        #         print("not busy")
        #         if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"] != self.LOOP2PT_OUT_buffer["PUMP3305"]:
        #             if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]:
        #
        #                 self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonLClicked()
        #                 self.PUMP3305.State.ButtonLClicked()
        #
        #             else:
        #                 self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonRClicked()
        #                 self.PUMP3305.State.ButtonRClicked()
        #             self.LOOP2PT_OUT_buffer["PUMP3305"] = received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]
        #         else:
        #             pass
        # if received_dic_c["data"]["LOOP2PT"]["OUT"]["PUMP3305"]:
        #
        #     self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonLClicked()
        #     self.PUMP3305.State.ButtonLClicked()
        #
        # else:
        #     self.PUMP3305.LOOP2PTSubWindow.Mode.ButtonRClicked()
        #     self.PUMP3305.State.ButtonRClicked()



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

        self.PT2121.SetValue(received_dic_c["data"]["PT"]["value"]["PT2121"])
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
        self.PT6302.SetValue(received_dic_c["data"]["PT"]["value"]["PT6302"])
        self.PT1101.SetValue(received_dic_c["data"]["PT"]["value"]["PT1101"])
        self.PT1101Fluid.SetValue(received_dic_c["data"]["PT"]["value"]["PT1101"])
        self.PT1101Hy.SetValue(received_dic_c["data"]["PT"]["value"]["PT1101"])
        self.PT5304.SetValue(received_dic_c["data"]["PT"]["value"]["PT5304"])

        self.LT3335.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["LT3335"])
        self.BFM4313.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["BFM4313"])
        # self.MFC1316.SetValue not given value
        self.CYL3334.SetValue(received_dic_c["data"]["LEFT_REAL"]["value"]["CYL3334_FCALC"])



        self.RTDset4Win.TT2101.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2101"])
        self.RTDset1Win.TT2111.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2111"])
        self.RTDset1Win.TT2113.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2113"])
        self.RTDset1Win.TT2118.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2118"])
        self.RTDset1Win.TT2119.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT2119"])
        self.TT4330.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT4330"])

        self.HTR6202.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6203"])
        self.HTR6206.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6207"])
        self.HTR6210.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6211"])
        self.HTR6214.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6213"])
        self.HTR6221.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6222"])
        self.HTR6202_v2.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6222"])
        self.HTR6223.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6407"])
        self.HTR6224.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6408"])
        self.HTR6225.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6409"])
        self.HTR1202.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6415"])
        self.HTR2203.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["BO"]["value"]["TT6416"])

        self.RTDset2Win.TT2420.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2420"])
        self.RTDset2Win.TT2422.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2422"])
        self.RTDset2Win.TT2424.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2424"])
        self.RTDset2Win.TT2425.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2425"])
        self.RTDset3Win.TT2442.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2442"])
        self.RTDset2Win.TT2403.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2403"])
        self.RTDset2Win.TT2418.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2418"])
        self.RTDset2Win.TT2427.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2427"])
        self.RTDset2Win.TT2429.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2429"])
        self.RTDset2Win.TT2431.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2431"])
        self.RTDset3Win.TT2441.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2441"])
        self.RTDset2Win.TT2414.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2414"])
        self.RTDset2Win.TT2413.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2413"])
        self.RTDset2Win.TT2412.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2412"])
        self.RTDset2Win.TT2415.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2415"])
        self.RTDset2Win.TT2409.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2409"])
        self.RTDset3Win.TT2436.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2436"])
        self.RTDset3Win.TT2438.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2438"])
        self.RTDset3Win.TT2440.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2440"])
        self.RTDset2Win.TT2402.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2402"])
        self.RTDset2Win.TT2411.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2411"])
        self.RTDset3Win.TT2443.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2443"])
        self.RTDset2Win.TT2417.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2417"])
        self.RTDset2Win.TT2404.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2404"])
        self.RTDset2Win.TT2408.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2408"])
        self.RTDset2Win.TT2407.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2407"])
        self.RTDset2Win.TT2406.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2406"])
        self.RTDset2Win.TT2428.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2428"])
        self.RTDset2Win.TT2432.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2432"])
        self.RTDset2Win.TT2421.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2421"])
        self.RTDset2Win.TT2416.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2416"])
        self.RTDset3Win.TT2439.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2439"])
        self.RTDset2Win.TT2419.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2419"])
        self.RTDset2Win.TT2423.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2423"])
        self.RTDset2Win.TT2426.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2426"])
        self.RTDset2Win.TT2430.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2430"])
        self.RTDset3Win.TT2450.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2450"])
        self.RTDset2Win.TT2401.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2401"])
        self.RTDset3Win.TT2449.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2449"])
        self.RTDset3Win.TT2445.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2445"])
        self.RTDset3Win.TT2444.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2444"])
        self.RTDset3Win.TT2435.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2435"])
        self.RTDset3Win.TT2437.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2437"])
        self.RTDset3Win.TT2446.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2446"])
        self.RTDset3Win.TT2447.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2447"])
        self.RTDset3Win.TT2448.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2448"])
        self.RTDset2Win.TT2410.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2410"])
        self.RTDset2Win.TT2405.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT2405"])

        self.HTR6219.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6220"])
        # self.MFC1316.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT1332"])
        self.HTR6214.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6401"])
        self.HTR6202.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6404"])
        self.HTR6206.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6405"])
        self.HTR6210.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6406"])
        self.HTR6223.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6410"])
        self.HTR6224.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6411"])
        self.HTR6225.LOOPPIDWindow.RTD2.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6412"])
        self.HTR1202.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6413"])
        self.HTR2203.LOOPPIDWindow.RTD1.SetValue(received_dic_c["data"]["TT"]["FP"]["value"]["TT6414"])




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



        # self.SERVO3321.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["SERVO3321"])
        # self.SERVO3321.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["SERVO3321"])
        # self.SERVO3321.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["SERVO3321"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["SERVO3321"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["SERVO3321"]]:
        #
        #     self.SERVO3321.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.SERVO3321.HeaterSubWindow.SAT.UpdateColor(False)
        # self.SERVO3321.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["SERVO3321"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["SERVO3321"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["SERVO3321"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["SERVO3321"]))
        # self.SERVO3321.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["SERVO3321"])
        # self.SERVO3321.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["SERVO3321"])
        # self.SERVO3321.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["SERVO3321"])
        # self.SERVO3321.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["SERVO3321"])
        # self.SERVO3321.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["SERVO3321"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["SERVO3321"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["SERVO3321"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["SERVO3321"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["SERVO3321"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["SERVO3321"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["SERVO3321"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["SERVO3321"]))
        # self.SERVO3321.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["SERVO3321"])
        #
        # self.HTR6225.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6225"])
        # self.HTR6225.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6225"])
        # self.HTR6225.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6225"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6225"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6225"]]:
        #
        #     self.HTR6225.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR6225.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR6225.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6225"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6225"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6225"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6225"]))
        # self.HTR6225.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR6225"])
        # self.HTR6225.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6225"])
        # self.HTR6225.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6225"])
        # self.HTR6225.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6225"])
        # self.HTR6225.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6225"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6225"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6225"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6225"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6225"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6225"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6225"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6225"]))
        # self.HTR6225.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6225"])
        #
        # self.HTR2123.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR2123"])
        # self.HTR2123.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR2123"])
        # self.HTR2123.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2123"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR2123"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR2123"]]:
        #
        #     self.HTR2123.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR2123.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR2123.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2123"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2123"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2123"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2123"]))
        # self.HTR2123.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR2123"])
        # self.HTR2123.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2123"])
        # self.HTR2123.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR2123"])
        # self.HTR2123.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR2123"])
        # self.HTR2123.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2123"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2123"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2123"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2123"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR2123"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR2123"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR2123"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR2123"]))
        # self.HTR2123.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2123"])
        #
        # self.HTR2124.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR2124"])
        # self.HTR2124.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR2124"])
        # self.HTR2124.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2124"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR2124"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR2124"]]:
        #
        #     self.HTR2124.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR2124.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR2124.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2124"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2124"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2124"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2124"]))
        # self.HTR2124.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR2124"])
        # self.HTR2124.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2124"])
        # self.HTR2124.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR2124"])
        # self.HTR2124.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR2124"])
        # self.HTR2124.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2124"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2124"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2124"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2124"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR2124"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR2124"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR2124"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR2124"]))
        # self.HTR2124.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2124"])
        #
        # self.HTR2125.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR2125"])
        # self.HTR2125.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR2125"])
        # self.HTR2125.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2125"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR2125"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR2125"]]:
        #
        #     self.HTR2125.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR2125.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR2125.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2125"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2125"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2125"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2125"]))
        # self.HTR2125.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR2125"])
        # self.HTR2125.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2125"])
        # self.HTR2125.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR2125"])
        # self.HTR2125.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR2125"])
        # self.HTR2125.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2125"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2125"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2125"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2125"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR2125"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR2125"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR2125"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR2125"]))
        # self.HTR2125.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2125"])
        #
        # self.HTR1202.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR1202"])
        # self.HTR1202.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR1202"])
        # self.HTR1202.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR1202"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR1202"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR1202"]]:
        #
        #     self.HTR1202.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR1202.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR1202.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR1202"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR1202"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR1202"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR1202"]))
        # self.HTR1202.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR1202"])
        # self.HTR1202.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR1202"])
        # self.HTR1202.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR1202"])
        # self.HTR1202.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR1202"])
        # self.HTR1202.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR1202"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR1202"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR1202"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR1202"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR1202"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR1202"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR1202"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR1202"]))
        # self.HTR1202.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR1202"])
        #
        # self.HTR2203.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR2203"])
        # self.HTR2203.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR2203"])
        # self.HTR2203.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR2203"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR2203"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR2203"]]:
        #
        #     self.HTR2203.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR2203.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR2203.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2203"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2203"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2203"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2203"]))
        # self.HTR2203.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR2203"])
        # self.HTR2203.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2203"])
        # self.HTR2203.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR2203"])
        # self.HTR2203.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR2203"])
        # self.HTR2203.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR2203"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR2203"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR2203"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR2203"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR2203"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR2203"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR2203"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR2203"]))
        # self.HTR2203.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR2203"])
        #
        # self.HTR6202.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6202"])
        # self.HTR6202.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6202"])
        # self.HTR6202.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6202"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6202"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6202"]]:
        #
        #     self.HTR6202.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR6202.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR6202.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6202"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6202"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6202"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6202"]))
        # self.HTR6202.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"])
        # self.HTR6202.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6202"])
        # self.HTR6202.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6202"])
        # self.HTR6202.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6202"])
        # self.HTR6202.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6202"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6202"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6202"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6202"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6202"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6202"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6202"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6202"]))
        # self.HTR6202.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6202"])
        #
        # self.HTR6206.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6206"])
        # self.HTR6206.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6206"])
        # self.HTR6206.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6206"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6206"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6206"]]:
        #
        #     self.HTR6206.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR6206.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR6206.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6206"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6206"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6206"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6206"]))
        # self.HTR6206.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR6206"])
        # self.HTR6206.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6206"])
        # self.HTR6206.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6206"])
        # self.HTR6206.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6206"])
        # self.HTR6206.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6206"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6206"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6206"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6206"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6206"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6206"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6206"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6206"]))
        # self.HTR6206.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6206"])
        #
        # self.HTR6210.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6210"])
        # self.HTR6210.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6210"])
        # self.HTR6210.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6210"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6210"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6210"]]:
        #
        #     self.HTR6210.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR6210.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR6210.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6210"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6210"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6210"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6210"]))
        # self.HTR6210.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR6210"])
        # self.HTR6210.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6210"])
        # self.HTR6210.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6210"])
        # self.HTR6210.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6210"])
        # self.HTR6210.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6210"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6210"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6210"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6210"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6210"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6210"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6210"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6210"]))
        # self.HTR6210.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6210"])
        #
        # self.HTR6223.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6223"])
        # self.HTR6223.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6223"])
        # self.HTR6223.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6223"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6223"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6223"]]:
        #
        #     self.HTR6223.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR6223.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR6223.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6223"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6223"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6223"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6223"]))
        # self.HTR6223.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR6223"])
        # self.HTR6223.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6223"])
        # self.HTR6223.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6223"])
        # self.HTR6223.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6223"])
        # self.HTR6223.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6223"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6223"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6223"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6223"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6223"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6223"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6223"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6223"]))
        # self.HTR6223.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6223"])
        #
        # self.HTR6224.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6224"])
        # self.HTR6224.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6224"])
        # self.HTR6224.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6224"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6224"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6224"]]:
        #
        #     self.HTR6224.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR6224.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR6224.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6224"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6224"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6224"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6224"]))
        # self.HTR6224.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR6224"])
        # self.HTR6224.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6224"])
        # self.HTR6224.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6224"])
        # self.HTR6224.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6224"])
        # self.HTR6224.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6224"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6224"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6224"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6224"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6224"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6224"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6224"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6224"]))
        # self.HTR6224.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6224"])
        #
        # self.HTR6219.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6219"])
        # self.HTR6219.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6219"])
        # self.HTR6219.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6219"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6219"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6219"]]:
        #
        #     self.HTR6219.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR6219.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR6219.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6219"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6219"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6219"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6219"]))
        # self.HTR6219.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR6219"])
        # self.HTR6219.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6219"])
        # self.HTR6219.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6219"])
        # self.HTR6219.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6219"])
        # self.HTR6219.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6219"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6219"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6219"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6219"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6219"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6219"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6219"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6219"]))
        # self.HTR6219.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6219"])
        #
        # self.HTR6221.HeaterSubWindow.Interlock.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6221"])
        # self.HTR6221.HeaterSubWindow.Error.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6221"])
        # self.HTR6221.HeaterSubWindow.MANSP.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6221"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6221"],
        #             received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6221"]]:
        #
        #     self.HTR6221.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR6221.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR6221.HeaterSubWindow.ModeREAD.Field.setText(
        #
        #     self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6221"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6221"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6221"],
        #                           received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6221"]))
        # self.HTR6221.HeaterSubWindow.EN.UpdateColor(
        #     received_dic_c["data"]["LOOPPID"]["EN"]["HTR6221"])
        # self.HTR6221.HeaterSubWindow.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6221"])
        # self.HTR6221.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6221"])
        # self.HTR6221.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6221"])
        # self.HTR6221.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6221"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6221"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6221"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6221"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6221"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6221"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6221"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6221"]))
        # self.HTR6221.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6221"])

        self.HTR6202_v2.LOOPPIDWindow.Interlock.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6202"])
        self.HTR6202_v2.LOOPPIDWindow.Error.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6202"])
        self.HTR6202_v2.LOOPPIDWindow.MANSP.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6202"])
        if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6202"],
                    received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6202"]]:

            self.HTR6202_v2.LOOPPIDWindow.SAT.UpdateColor(True)
        else:
            self.HTR6202_v2.LOOPPIDWindow.SAT.UpdateColor(False)
        self.HTR6202_v2.LOOPPIDWindow.ModeREAD.Field.setText(

            self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6202"],
                                  received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6202"],
                                  received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6202"],
                                  received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6202"]))
        self.HTR6202_v2.LOOPPIDWindow.EN.UpdateColor(
            received_dic_c["data"]["LOOPPID"]["EN"]["HTR6202"])
        self.HTR6202_v2.LOOPPIDWindow.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6202"])
        self.HTR6202_v2.LOOPPIDWindow.HIGH.SetValue(
            received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6202"])
        self.HTR6202_v2.LOOPPIDWindow.LOW.SetValue(
            received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6202"])
        self.HTR6202_v2.LOOPPIDWindow.SETSP.SetValue(
            self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6202"],
                               received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6202"]))
        self.HTR6202_v2.Power.SetValue(
            received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6202"])
        #
        # self.HTR6214.HeaterSubWindow.Interlock.UpdateColor(received_dic_c["data"]["LOOPPID"]["INTLKD"]["HTR6214"])
        # self.HTR6214.HeaterSubWindow.Error.UpdateColor(received_dic_c["data"]["LOOPPID"]["ERR"]["HTR6214"])
        # self.HTR6214.HeaterSubWindow.MANSP.UpdateColor(received_dic_c["data"]["LOOPPID"]["MAN"]["HTR6214"])
        # if True in [received_dic_c["data"]["LOOPPID"]["SATHI"]["HTR6214"], received_dic_c["data"]["LOOPPID"]["SATLO"]["HTR6214"]]:
        #     self.HTR6214.HeaterSubWindow.SAT.UpdateColor(True)
        # else:
        #     self.HTR6214.HeaterSubWindow.SAT.UpdateColor(False)
        # self.HTR6214.HeaterSubWindow.ModeREAD.Field.setText(self.FindDistinctTrue(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6214"], received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6214"],
        #                                                                              received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6214"], received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6214"]))
        # self.HTR6214.HeaterSubWindow.EN.UpdateColor(received_dic_c["data"]["LOOPPID"]["EN"]["HTR6214"])
        # self.HTR6214.HeaterSubWindow.Power.SetValue(received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6214"])
        # self.HTR6214.HeaterSubWindow.HIGH.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["HI_LIM"]["HTR6214"])
        # self.HTR6214.HeaterSubWindow.LOW.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["LO_LIM"]["HTR6214"])
        # self.HTR6214.HeaterSubWindow.SETSP.SetValue(
        #     self.FetchSetPoint(received_dic_c["data"]["LOOPPID"]["MODE0"]["HTR6214"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE1"]["HTR6214"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE2"]["HTR6214"],
        #                        received_dic_c["data"]["LOOPPID"]["MODE3"]["HTR6214"],
        #                        received_dic_c["data"]["LOOPPID"]["SET0"]["HTR6214"],
        #                        received_dic_c["data"]["LOOPPID"]["SET1"]["HTR6214"],
        #                        received_dic_c["data"]["LOOPPID"]["SET2"]["HTR6214"],
        #                        received_dic_c["data"]["LOOPPID"]["SET3"]["HTR6214"]))
        # self.HTR6214.Power.SetValue(
        #     received_dic_c["data"]["LOOPPID"]["OUT"]["HTR6214"])

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

        self.INTLCKWindow.PT4306_HI_INTLK.ColorLabel(
            received_dic_c["data"]["INTLK_A"]["value"]["PT4306_HI_INTLK"])
        self.INTLCKWindow.PT4306_HI_INTLK.Indicator.UpdateColor(
            received_dic_c["data"]["INTLK_A"]["EN"]["PT4306_HI_INTLK"])
        self.INTLCKWindow.PT4306_HI_INTLK.COND.UpdateColor(received_dic_c["data"]["INTLK_A"]["COND"]["PT4306_HI_INTLK"])
        self.INTLCKWindow.PT4306_HI_INTLK.SET_R.SetValue(
            received_dic_c["data"]["INTLK_A"]["SET"]["PT4306_HI_INTLK"])

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
            self.AlarmButton.SubWindow.ReassignRTD1Order()
            self.AlarmButton.SubWindow.ReassignRTD2Order()
            self.AlarmButton.SubWindow.ReassignRTD3Order()
            self.AlarmButton.SubWindow.ReassignRTD4Order()
            self.AlarmButton.SubWindow.ReassignRTDLEFTOrder()
            self.AlarmButton.SubWindow.ReassignPTOrder()
            self.AlarmButton.SubWindow.ReassignLEFTOrder()
            self.AlarmButton.SubWindow.ReassignDinOrder()
            self.AlarmButton.SubWindow.ReassignHTROrder()



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
    #
    # def closeEvent(self, event):
    #     self.CloseMessage = QtWidgets.QMessageBox()
    #     self.CloseMessage.setText("The program is to be closed")
    #     self.CloseMessage.setInformativeText("Do you want to save the settings?")
    #     self.CloseMessage.setStandardButtons(
    #         QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
    #     self.CloseMessage.setDefaultButton(QtWidgets.QMessageBox.Save)
    #     self.ret = self.CloseMessage.exec_()
    #     if self.ret == QtWidgets.QMessageBox.Save:
    #         # self.Save()
    #         sys.exit(0)
    #         event.accept()
    #     elif self.ret == QtWidgets.QMessageBox.Discard:
    #         sys.exit(0)
    #         event.accept()
    #     elif self.ret == QtWidgets.QMessageBox.Cancel:
    #         event.ignore()
    #     else:
    #         print("Some problems with closing windows...")
    #         pass
    #
    # def Save(self, directory=None, company="SBC", project="Slowcontrol"):
    #     # dir is the path storing the ini setting file
    #     if directory is None:
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/CheckBox",
    #                                self.AlarmButton.SubWindow.TT2111.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/CheckBox",
    #                                self.AlarmButton.SubWindow.TT2401.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/CheckBox",
    #                                self.AlarmButton.SubWindow.TT2406.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/CheckBox",
    #                                self.AlarmButton.SubWindow.TT2411.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/CheckBox",
    #                                self.AlarmButton.SubWindow.TT2416.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/CheckBox",
    #                                self.AlarmButton.SubWindow.TT2421.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/CheckBox",
    #                                self.AlarmButton.SubWindow.TT2426.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/CheckBox",
    #                                self.AlarmButton.SubWindow.TT2431.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/CheckBox",
    #                                self.AlarmButton.SubWindow.TT2435.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/CheckBox",
    #                                self.AlarmButton.SubWindow.TT2440.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/CheckBox",
    #                                self.AlarmButton.SubWindow.TT4330.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/CheckBox",
    #                                self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/CheckBox",
    #                                self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/CheckBox",
    #                                self.AlarmButton.SubWindow.TT6221.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/CheckBox",
    #                                self.AlarmButton.SubWindow.TT6222.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/CheckBox",
    #                                self.AlarmButton.SubWindow.TT6223.AlarmMode.isChecked())
    #         # set PT value
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/CheckBox",
    #                                self.AlarmButton.SubWindow.PT1101.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/CheckBox",
    #                                self.AlarmButton.SubWindow.PT2316.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/CheckBox",
    #                                self.AlarmButton.SubWindow.PT2321.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/CheckBox",
    #                                self.AlarmButton.SubWindow.PT2330.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/CheckBox",
    #                                self.AlarmButton.SubWindow.PT2335.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/CheckBox",
    #                                self.AlarmButton.SubWindow.PT3308.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/CheckBox",
    #                                self.AlarmButton.SubWindow.PT3309.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/CheckBox",
    #                                self.AlarmButton.SubWindow.PT3310.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/CheckBox",
    #                                self.AlarmButton.SubWindow.PT3311.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/CheckBox",
    #                                self.AlarmButton.SubWindow.PT3314.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/CheckBox",
    #                                self.AlarmButton.SubWindow.PT3320.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/CheckBox",
    #                                self.AlarmButton.SubWindow.PT3333.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/CheckBox",
    #                                self.AlarmButton.SubWindow.PT4306.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/CheckBox",
    #                                self.AlarmButton.SubWindow.PT4315.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/CheckBox",
    #                                self.AlarmButton.SubWindow.PT4319.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/CheckBox",
    #                                self.AlarmButton.SubWindow.PT4322.AlarmMode.isChecked())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/CheckBox",
    #                                self.AlarmButton.SubWindow.PT4325.AlarmMode.isChecked())
    #
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/LowLimit",
    #                                self.AlarmButton.SubWindow.TT2111.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/LowLimit",
    #                                self.AlarmButton.SubWindow.TT2401.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/LowLimit",
    #                                self.AlarmButton.SubWindow.TT2406.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/LowLimit",
    #                                self.AlarmButton.SubWindow.TT2411.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/LowLimit",
    #                                self.AlarmButton.SubWindow.TT2416.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/LowLimit",
    #                                self.AlarmButton.SubWindow.TT2421.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/LowLimit",
    #                                self.AlarmButton.SubWindow.TT2426.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/LowLimit",
    #                                self.AlarmButton.SubWindow.TT2431.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/LowLimit",
    #                                self.AlarmButton.SubWindow.TT2435.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/LowLimit",
    #                                self.AlarmButton.SubWindow.TT2440.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/LowLimit",
    #                                self.AlarmButton.SubWindow.TT4330.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/LowLimit",
    #                                self.AlarmButton.SubWindow.TT6220.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/LowLimit",
    #                                self.AlarmButton.SubWindow.TT6220.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/LowLimit",
    #                                self.AlarmButton.SubWindow.TT6221.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/LowLimit",
    #                                self.AlarmButton.SubWindow.TT6222.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/LowLimit",
    #                                self.AlarmButton.SubWindow.TT6223.Low_Limit.Field.text())
    #         # set PT value
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/LowLimit",
    #                                self.AlarmButton.SubWindow.PT1101.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/LowLimit",
    #                                self.AlarmButton.SubWindow.PT2316.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/LowLimit",
    #                                self.AlarmButton.SubWindow.PT2321.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/LowLimit",
    #                                self.AlarmButton.SubWindow.PT2330.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/LowLimit",
    #                                self.AlarmButton.SubWindow.PT2335.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/LowLimit",
    #                                self.AlarmButton.SubWindow.PT3308.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/LowLimit",
    #                                self.AlarmButton.SubWindow.PT3309.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/LowLimit",
    #                                self.AlarmButton.SubWindow.PT3310.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/LowLimit",
    #                                self.AlarmButton.SubWindow.PT3311.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/LowLimit",
    #                                self.AlarmButton.SubWindow.PT3314.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/LowLimit",
    #                                self.AlarmButton.SubWindow.PT3320.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/LowLimit",
    #                                self.AlarmButton.SubWindow.PT3333.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/LowLimit",
    #                                self.AlarmButton.SubWindow.PT4306.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/LowLimit",
    #                                self.AlarmButton.SubWindow.PT4315.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/LowLimit",
    #                                self.AlarmButton.SubWindow.PT4319.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/LowLimit",
    #                                self.AlarmButton.SubWindow.PT4322.Low_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/LowLimit",
    #                                self.AlarmButton.SubWindow.PT4325.Low_Limit.Field.text())
    #
    #         # high limit
    #
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/HighLimit",
    #                                self.AlarmButton.SubWindow.TT2111.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/HighLimit",
    #                                self.AlarmButton.SubWindow.TT2401.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/HighLimit",
    #                                self.AlarmButton.SubWindow.TT2406.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/HighLimit",
    #                                self.AlarmButton.SubWindow.TT2411.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/HighLimit",
    #                                self.AlarmButton.SubWindow.TT2416.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/HighLimit",
    #                                self.AlarmButton.SubWindow.TT2421.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/HighLimit",
    #                                self.AlarmButton.SubWindow.TT2426.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/HighLimit",
    #                                self.AlarmButton.SubWindow.TT2431.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/HighLimit",
    #                                self.AlarmButton.SubWindow.TT2435.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/HighLimit",
    #                                self.AlarmButton.SubWindow.TT2440.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/HighLimit",
    #                                self.AlarmButton.SubWindow.TT4330.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/HighLimit",
    #                                self.AlarmButton.SubWindow.TT6220.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/HighLimit",
    #                                self.AlarmButton.SubWindow.TT6220.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/HighLimit",
    #                                self.AlarmButton.SubWindow.TT6221.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/HighLimit",
    #                                self.AlarmButton.SubWindow.TT6222.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/HighLimit",
    #                                self.AlarmButton.SubWindow.TT6223.High_Limit.Field.text())
    #         # set PT value
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/HighLimit",
    #                                self.AlarmButton.SubWindow.PT1101.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/HighLimit",
    #                                self.AlarmButton.SubWindow.PT2316.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/HighLimit",
    #                                self.AlarmButton.SubWindow.PT2321.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/HighLimit",
    #                                self.AlarmButton.SubWindow.PT2330.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/HighLimit",
    #                                self.AlarmButton.SubWindow.PT2335.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/HighLimit",
    #                                self.AlarmButton.SubWindow.PT3308.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/HighLimit",
    #                                self.AlarmButton.SubWindow.PT3309.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/HighLimit",
    #                                self.AlarmButton.SubWindow.PT3310.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/HighLimit",
    #                                self.AlarmButton.SubWindow.PT3311.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/HighLimit",
    #                                self.AlarmButton.SubWindow.PT3314.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/HighLimit",
    #                                self.AlarmButton.SubWindow.PT3320.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/HighLimit",
    #                                self.AlarmButton.SubWindow.PT3333.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/HighLimit",
    #                                self.AlarmButton.SubWindow.PT4306.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/HighLimit",
    #                                self.AlarmButton.SubWindow.PT4315.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/HighLimit",
    #                                self.AlarmButton.SubWindow.PT4319.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/HighLimit",
    #                                self.AlarmButton.SubWindow.PT4322.High_Limit.Field.text())
    #         self.settings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/HighLimit",
    #                                self.AlarmButton.SubWindow.PT4325.High_Limit.Field.text())
    #
    #         print("saving data to Default path: $HOME/.config//SBC/SlowControl.ini")
    #     else:
    #         try:
    #             # modify the qtsetting default save settings. if the directory is inside a folder named sbc, then save
    #             # the file into the folder. If not, create a folder named sbc and save the file in it.
    #             (path_head, path_tail) = os.path.split(directory)
    #             if path_tail == company:
    #                 path = os.path.join(directory, project)
    #             else:
    #                 path = os.path.join(directory, company, project)
    #             print(path)
    #             self.customsettings = QtCore.QSettings(path, QtCore.QSettings.IniFormat)
    #
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT2111.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT2401.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT2406.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT2411.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT2416.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT2421.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT2426.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT2431.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT2435.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT2440.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT4330.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT6220.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT6221.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT6222.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/CheckBox",
    #                                          self.AlarmButton.SubWindow.TT6223.AlarmMode.isChecked())
    #             # set PT value
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT1101.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT2316.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT2321.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT2330.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT2335.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT3308.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT3309.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT3310.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT3311.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT3314.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT3320.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT3333.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT4306.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT4315.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT4319.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT4322.AlarmMode.isChecked())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/CheckBox",
    #                                          self.AlarmButton.SubWindow.PT4325.AlarmMode.isChecked())
    #
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT2111.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT2401.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT2406.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT2411.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT2416.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT2421.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT2426.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT2431.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT2435.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT2440.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT4330.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT6220.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT6220.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT6221.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT6222.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/LowLimit",
    #                                          self.AlarmButton.SubWindow.TT6223.Low_Limit.Field.text())
    #             # set PT value
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT1101.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT2316.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT2321.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT2330.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT2335.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT3308.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT3309.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT3310.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT3311.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT3314.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT3320.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT3333.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT4306.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT4315.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT4319.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT4322.Low_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/LowLimit",
    #                                          self.AlarmButton.SubWindow.PT4325.Low_Limit.Field.text())
    #
    #             # high limit
    #
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2111/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT2111.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2401/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT2401.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2406/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT2406.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2411/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT2411.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2416/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT2416.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2421/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT2421.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2426/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT2426.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2431/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT2431.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2435/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT2435.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT2440/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT2440.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT4330/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT4330.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT6220.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6220/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT6220.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6221/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT6221.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6222/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT6222.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/TT6223/HighLimit",
    #                                          self.AlarmButton.SubWindow.TT6223.High_Limit.Field.text())
    #             # set PT value
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT1101/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT1101.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2316/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT2316.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2321/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT2321.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2330/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT2330.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT2335/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT2335.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3308/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT3308.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3309/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT3309.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3310/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT3310.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3311/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT3311.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3314/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT3314.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3320/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT3320.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT3333/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT3333.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4306/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT4306.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4315/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT4315.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4319/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT4319.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4322/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT4322.High_Limit.Field.text())
    #             self.customsettings.setValue("MainWindow/AlarmButton/SubWindow/PT4325/HighLimit",
    #                                          self.AlarmButton.SubWindow.PT4325.High_Limit.Field.text())
    #             print("saving data to ", path)
    #         except:
    #             print("Failed to custom save the settings.")
    #
    # def Recover(self, address="$HOME/.config//SBC/SlowControl.ini"):
    #     # address is the ini file 's directory you want to recover
    #
    #     try:
    #         # default recover. If no other address is claimed, then recover settings from default directory
    #         if address == "$HOME/.config//SBC/SlowControl.ini":
    #             self.RecoverChecked(self.AlarmButton.SubWindow.TT4330,
    #                                 "MainWindow/AlarmButton/SubWindow/TT4330/CheckBox")
    #             self.RecoverChecked(self.AlarmButton.SubWindow.PT4306,
    #                                 "MainWindow/AlarmButton/SubWindow/PT4306/CheckBox")
    #             self.RecoverChecked(self.AlarmButton.SubWindow.PT4315,
    #                                 "MainWindow/AlarmButton/SubWindow/PT4315/CheckBox")
    #             self.RecoverChecked(self.AlarmButton.SubWindow.PT4319,
    #                                 "MainWindow/AlarmButton/SubWindow/PT4319/CheckBox")
    #             self.RecoverChecked(self.AlarmButton.SubWindow.PT4322,
    #                                 "MainWindow/AlarmButton/SubWindow/PT4322/CheckBox")
    #             self.RecoverChecked(self.AlarmButton.SubWindow.PT4325,
    #                                 "MainWindow/AlarmButton/SubWindow/PT4325/CheckBox")
    #
    #             self.AlarmButton.SubWindow.TT4330.Low_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/TT4330/LowLimit"))
    #             self.AlarmButton.SubWindow.TT4330.Low_Limit.UpdateValue()
    #             self.AlarmButton.SubWindow.PT4306.Low_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/PT4306/LowLimit"))
    #             self.AlarmButton.SubWindow.PT4306.Low_Limit.UpdateValue()
    #             self.AlarmButton.SubWindow.PT4315.Low_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/PT4315/LowLimit"))
    #             self.AlarmButton.SubWindow.PT4315.Low_Limit.UpdateValue()
    #             self.AlarmButton.SubWindow.PT4319.Low_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/PT4319/LowLimit"))
    #             self.AlarmButton.SubWindow.PT4319.Low_Limit.UpdateValue()
    #             self.AlarmButton.SubWindow.PT4322.Low_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/PT4322/LowLimit"))
    #             self.AlarmButton.SubWindow.PT4322.Low_Limit.UpdateValue()
    #             self.AlarmButton.SubWindow.PT4325.Low_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/PT4325/LowLimit"))
    #             self.AlarmButton.SubWindow.PT4325.Low_Limit.UpdateValue()
    #
    #             self.AlarmButton.SubWindow.TT4330.High_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/TT4330/HighLimit"))
    #             self.AlarmButton.SubWindow.TT4330.High_Limit.UpdateValue()
    #             self.AlarmButton.SubWindow.PT4306.High_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/PT4306/HighLimit"))
    #             self.AlarmButton.SubWindow.PT4306.High_Limit.UpdateValue()
    #             self.AlarmButton.SubWindow.PT4315.High_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/PT4315/HighLimit"))
    #             self.AlarmButton.SubWindow.PT4315.High_Limit.UpdateValue()
    #             self.AlarmButton.SubWindow.PT4319.High_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/PT4319/HighLimit"))
    #             self.AlarmButton.SubWindow.PT4319.High_Limit.UpdateValue()
    #             self.AlarmButton.SubWindow.PT4322.High_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/PT4322/HighLimit"))
    #             self.AlarmButton.SubWindow.PT4322.High_Limit.UpdateValue()
    #             self.AlarmButton.SubWindow.PT4325.High_Limit.Field.setText(self.settings.value(
    #                 "MainWindow/AlarmButton/SubWindow/PT4325/HighLimit"))
    #             self.AlarmButton.SubWindow.PT4325.High_Limit.UpdateValue()
    #         else:
    #             try:
    #                 # else, recover from the claimed directory
    #                 # address should be surfix with ini. Example:$HOME/.config//SBC/SlowControl.ini
    #                 directory = QtCore.QSettings(str(address), QtCore.QSettings.IniFormat)
    #                 print("Recovering from " + str(address))
    #                 self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.TT4330,
    #                                     subdir="MainWindow/AlarmButton/SubWindow/TT4330/CheckBox",
    #                                     loadedsettings=directory)
    #                 self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.PT4306,
    #                                     subdir="MainWindow/AlarmButton/SubWindow/PT4306/CheckBox",
    #                                     loadedsettings=directory)
    #                 self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.PT4315,
    #                                     subdir="MainWindow/AlarmButton/SubWindow/PT4315/CheckBox",
    #                                     loadedsettings=directory)
    #                 self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.PT4319,
    #                                     subdir="MainWindow/AlarmButton/SubWindow/PT4319/CheckBox",
    #                                     loadedsettings=directory)
    #                 self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.PT4322,
    #                                     subdir="MainWindow/AlarmButton/SubWindow/PT4322/CheckBox",
    #                                     loadedsettings=directory)
    #                 self.RecoverChecked(GUIid=self.AlarmButton.SubWindow.PT4325,
    #                                     subdir="MainWindow/AlarmButton/SubWindow/PT4325/CheckBox",
    #                                     loadedsettings=directory)
    #
    #                 self.AlarmButton.SubWindow.TT4330.Low_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/TT4330/LowLimit"))
    #                 self.AlarmButton.SubWindow.TT4330.Low_Limit.UpdateValue()
    #                 self.AlarmButton.SubWindow.PT4306.Low_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/PT4306/LowLimit"))
    #                 self.AlarmButton.SubWindow.PT4306.Low_Limit.UpdateValue()
    #                 self.AlarmButton.SubWindow.PT4315.Low_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/PT4315/LowLimit"))
    #                 self.AlarmButton.SubWindow.PT4315.Low_Limit.UpdateValue()
    #                 self.AlarmButton.SubWindow.PT4319.Low_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/PT4319/LowLimit"))
    #                 self.AlarmButton.SubWindow.PT4319.Low_Limit.UpdateValue()
    #                 self.AlarmButton.SubWindow.PT4322.Low_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/PT4322/LowLimit"))
    #                 self.AlarmButton.SubWindow.PT4322.Low_Limit.UpdateValue()
    #                 self.AlarmButton.SubWindow.PT4325.Low_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/PT4325/LowLimit"))
    #                 self.AlarmButton.SubWindow.PT4325.Low_Limit.UpdateValue()
    #
    #                 self.AlarmButton.SubWindow.TT4330.High_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/TT4330/HighLimit"))
    #                 self.AlarmButton.SubWindow.TT4330.High_Limit.UpdateValue()
    #                 self.AlarmButton.SubWindow.PT4306.High_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/PT4306/HighLimit"))
    #                 self.AlarmButton.SubWindow.PT4306.High_Limit.UpdateValue()
    #                 self.AlarmButton.SubWindow.PT4315.High_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/PT4315/HighLimit"))
    #                 self.AlarmButton.SubWindow.PT4315.High_Limit.UpdateValue()
    #                 self.AlarmButton.SubWindow.PT4319.High_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/PT4319/HighLimit"))
    #                 self.AlarmButton.SubWindow.PT4319.High_Limit.UpdateValue()
    #                 self.AlarmButton.SubWindow.PT4322.High_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/PT4322/HighLimit"))
    #                 self.AlarmButton.SubWindow.PT4322.High_Limit.UpdateValue()
    #                 self.AlarmButton.SubWindow.PT4325.High_Limit.Field.setText(directory.value(
    #                     "MainWindow/AlarmButton/SubWindow/PT4325/HighLimit"))
    #                 self.AlarmButton.SubWindow.PT4325.High_Limit.UpdateValue()
    #
    #             except:
    #                 print("Wrong Path to recover")
    #     except:
    #         print("1st time run the code in this environment. "
    #               "Nothing to recover the settings. Please save the configuration to a ini file")
    #         pass
    #
    # def RecoverChecked(self, GUIid, subdir, loadedsettings=None):
    #     # add a function because you can not directly set check status to checkbox
    #     # GUIid should be form of "self.AlarmButton.SubWindow.PT4315", is the variable name in the Main window
    #     # subdir like ""MainWindow/AlarmButton/SubWindow/PT4306/CheckBox"", is the path file stored in the ini file
    #     # loadedsettings is the Qtsettings file the program is to load
    #     if loadedsettings is None:
    #         # It is weired here, when I save the data and close the program, the setting value
    #         # in the address is string true
    #         # while if you maintain the program, the setting value in the address is bool True
    #         if self.settings.value(subdir) == "true" or self.settings.value(subdir) == True:
    #             GUIid.AlarmMode.setChecked(True)
    #         elif self.settings.value(subdir) == "false" or self.settings.value(subdir) == False:
    #             GUIid.AlarmMode.setChecked(False)
    #         else:
    #             print("Checkbox's value is neither true nor false")
    #     else:
    #         try:
    #             if loadedsettings.value(subdir) == "True" or loadedsettings.value(subdir) == True:
    #                 GUIid.AlarmMode.setChecked(True)
    #             elif self.settings.value(subdir) == "false" or loadedsettings.value(subdir) == False:
    #                 GUIid.AlarmMode.setChecked(False)
    #             else:
    #                 print("Checkbox's value is neither true nor false")
    #         except:
    #             print("Failed to load the status of checkboxs")
    #


class UpdateClient(QtCore.QObject):
    client_data_transport = QtCore.Signal()
    client_command_fectch = QtCore.Signal()
    client_clear_commands = QtCore.Signal()
    # def __init__(self, MW, parent=None):
    def __init__(self, parent=None):
        super().__init__(parent)


        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")
        self.Running=False
        self.readcommand = False
        self.period = 1
        self.socket.setsockopt(zmq.LINGER, 0)


        print("client is connecting to the ZMQ server")

        self.TT_FP_dic_ini = sec.TT_FP_DIC
        self.TT_BO_dic_ini = sec.TT_BO_DIC
        self.PT_dic_ini = sec.PT_DIC
        self.LEFT_REAL_ini = sec.LEFT_REAL_DIC
        self.TT_FP_LowLimit_ini = sec.TT_FP_LOWLIMIT
        self.TT_FP_HighLimit_ini = sec.TT_FP_HIGHLIMIT
        self.TT_BO_LowLimit_ini = sec.TT_BO_LOWLIMIT
        self.TT_BO_HighLimit_ini = sec.TT_BO_HIGHLIMIT
        self.PT_LowLimit_ini = sec.PT_LOWLIMIT
        self.PT_HighLimit_ini = sec.PT_HIGHLIMIT
        self.LEFT_REAL_LowLimit_ini = sec.LEFT_REAL_LOWLIMIT
        self.LEFT_REAL_HighLimit_ini = sec.LEFT_REAL_HIGHLIMIT
        self.TT_FP_Activated_ini = sec.TT_FP_ACTIVATED
        self.TT_BO_Activated_ini = sec.TT_BO_ACTIVATED
        self.PT_Activated_ini = sec.PT_ACTIVATED
        self.TT_FP_Alarm_ini = sec.TT_FP_ALARM
        self.TT_BO_Alarm_ini = sec.TT_BO_ALARM
        self.PT_Alarm_ini = sec.PT_ALARM
        self.LEFT_REAL_Activated_ini = sec.LEFT_REAL_ACTIVATED
        self.LEFT_REAL_Alarm_ini = sec.LEFT_REAL_ALARM
        self.MainAlarm_ini = sec.MAINALARM
        self.MAN_SET = sec.MAN_SET
        self.Valve_OUT_ini = sec.VALVE_OUT
        self.Valve_MAN_ini = sec.VALVE_MAN
        self.Valve_INTLKD_ini = sec.VALVE_INTLKD
        self.Valve_ERR_ini = sec.VALVE_ERR
        self.Valve_Busy_ini = sec.VALVE_BUSY
        self.Switch_OUT_ini = sec.SWITCH_OUT
        self.Switch_MAN_ini = sec.SWITCH_MAN
        self.Switch_INTLKD_ini = sec.SWITCH_INTLKD
        self.Switch_ERR_ini = sec.SWITCH_ERR
        self.Din_dic_ini = sec.DIN_DIC
        self.Din_HighLimit_ini = sec.DIN_HIGHLIMIT
        self.Din_LowLimit_ini = sec.DIN_LOWLIMIT
        self.Din_Activated_ini = sec.DIN_ACTIVATED
        self.Din_Alarm_ini = sec.DIN_ALARM

        self.LOOPPID_MODE0_ini = sec.LOOPPID_MODE0
        self.LOOPPID_MODE1_ini = sec.LOOPPID_MODE1
        self.LOOPPID_MODE2_ini = sec.LOOPPID_MODE2
        self.LOOPPID_MODE3_ini = sec.LOOPPID_MODE3
        self.LOOPPID_INTLKD_ini = sec.LOOPPID_INTLKD
        self.LOOPPID_MAN_ini = sec.LOOPPID_MAN
        self.LOOPPID_ERR_ini = sec.LOOPPID_ERR
        self.LOOPPID_SATHI_ini = sec.LOOPPID_SATHI
        self.LOOPPID_SATLO_ini = sec.LOOPPID_SATLO
        self.LOOPPID_EN_ini = sec.LOOPPID_EN
        self.LOOPPID_OUT_ini = sec.LOOPPID_OUT
        self.LOOPPID_IN_ini = sec.LOOPPID_IN
        self.LOOPPID_HI_LIM_ini = sec.LOOPPID_HI_LIM
        self.LOOPPID_LO_LIM_ini = sec.LOOPPID_LO_LIM
        self.LOOPPID_SET0_ini = sec.LOOPPID_SET0
        self.LOOPPID_SET1_ini = sec.LOOPPID_SET1
        self.LOOPPID_SET2_ini = sec.LOOPPID_SET2
        self.LOOPPID_SET3_ini = sec.LOOPPID_SET3
        self.LOOPPID_Busy_ini = sec.LOOPPID_BUSY
        self.LOOPPID_Alarm_ini = sec.LOOPPID_ALARM
        self.LOOPPID_Activated_ini = sec.LOOPPID_ACTIVATED
        self.LOOPPID_Alarm_HighLimit_ini = sec.LOOPPID_ALARM_HI_LIM
        self.LOOPPID_Alarm_LowLimit_ini = sec.LOOPPID_ALARM_LO_LIM

        self.LOOP2PT_MODE0_ini = sec.LOOP2PT_MODE0
        self.LOOP2PT_MODE1_ini = sec.LOOP2PT_MODE1
        self.LOOP2PT_MODE2_ini = sec.LOOP2PT_MODE2
        self.LOOP2PT_MODE3_ini = sec.LOOP2PT_MODE3
        self.LOOP2PT_INTLKD_ini = sec.LOOP2PT_INTLKD
        self.LOOP2PT_MAN_ini = sec.LOOP2PT_MAN
        self.LOOP2PT_ERR_ini = sec.LOOP2PT_ERR
        self.LOOP2PT_OUT_ini = sec.LOOP2PT_OUT
        self.LOOP2PT_SET1_ini = sec.LOOP2PT_SET1
        self.LOOP2PT_SET2_ini = sec.LOOP2PT_SET2
        self.LOOP2PT_SET3_ini = sec.LOOP2PT_SET3
        self.LOOP2PT_Busy_ini = sec.LOOP2PT_BUSY

        self.Procedure_running_ini = sec.PROCEDURE_RUNNING
        self.Procedure_INTLKD_ini = sec.PROCEDURE_INTLKD
        self.Procedure_EXIT_ini = sec.PROCEDURE_EXIT

        self.INTLK_D_ADDRESS_ini = sec.INTLK_D_ADDRESS
        self.INTLK_D_DIC_ini = sec.INTLK_D_DIC
        self.INTLK_D_EN_ini = sec.INTLK_D_EN
        self.INTLK_D_COND_ini = sec.INTLK_D_COND
        self.INTLK_D_Busy_ini = sec.INTLK_D_BUSY
        self.INTLK_A_ADDRESS_ini = sec.INTLK_A_ADDRESS
        self.INTLK_A_DIC_ini = sec.INTLK_A_DIC
        self.INTLK_A_EN_ini = sec.INTLK_A_EN
        self.INTLK_A_COND_ini = sec.INTLK_A_COND
        self.INTLK_A_SET_ini = sec.INTLK_A_SET
        self.INTLK_A_Busy_ini = sec.INTLK_A_BUSY

        self.FLAG_ADDRESS_ini = sec.FLAG_ADDRESS
        self.FLAG_DIC_ini = sec.FLAG_DIC
        self.FLAG_INTLKD_ini = sec.FLAG_INTLKD
        self.FLAG_Busy_ini = sec.FLAG_BUSY

        self.FF_DIC_ini = copy.copy(sec.FF_DIC)
        self.PARAM_F_DIC_ini = copy.copy(sec.PARAM_F_DIC)
        self.PARAM_I_DIC_ini = copy.copy(sec.PARAM_I_DIC)
        self.PARAM_B_DIC_ini = copy.copy(sec.PARAM_B_DIC)
        self.PARAM_T_DIC_ini = copy.copy(sec.PARAM_T_DIC)
        self.TIME_DIC_ini = copy.copy(sec.TIME_DIC)


        self.Ini_Check_ini = sec.INI_CHECK
        self.MAN_SET = copy.copy(sec.MAN_SET)

        self.receive_dic = {"data": {"TT": {"FP": {"value": self.TT_FP_dic_ini, "high": self.TT_FP_HighLimit_ini, "low": self.TT_FP_LowLimit_ini},
                                         "BO": {"value": self.TT_BO_dic_ini, "high": self.TT_BO_HighLimit_ini, "low": self.TT_BO_LowLimit_ini}},
                                  "PT": {"value": self.PT_dic_ini, "high": self.PT_HighLimit_ini, "low": self.PT_LowLimit_ini},
                                  "LEFT_REAL": {"value": self.LEFT_REAL_ini, "high": self.LEFT_REAL_HighLimit_ini, "low": self.LEFT_REAL_LowLimit_ini},
                                  "Valve": {"OUT": self.Valve_OUT_ini,
                                            "INTLKD": self.Valve_INTLKD_ini,
                                            "MAN": self.Valve_MAN_ini,
                                            "ERR": self.Valve_ERR_ini,
                                            "Busy":self.Valve_Busy_ini},
                                  "Switch": {"OUT": self.Switch_OUT_ini,
                                             "INTLKD": self.Switch_INTLKD_ini,
                                             "MAN": self.Switch_MAN_ini,
                                             "ERR": self.Switch_ERR_ini},
                                  "Din": {'value': self.Din_dic_ini,"high": self.Din_HighLimit_ini, "low": self.Din_LowLimit_ini},
                                  "LOOPPID": {"MODE0": self.LOOPPID_MODE0_ini,
                                              "MODE1": self.LOOPPID_MODE1_ini,
                                              "MODE2": self.LOOPPID_MODE2_ini,
                                              "MODE3": self.LOOPPID_MODE3_ini,
                                              "INTLKD": self.LOOPPID_INTLKD_ini,
                                              "MAN": self.LOOPPID_MAN_ini,
                                              "ERR": self.LOOPPID_ERR_ini,
                                              "SATHI": self.LOOPPID_SATHI_ini,
                                              "SATLO": self.LOOPPID_SATLO_ini,
                                              "EN": self.LOOPPID_EN_ini,
                                              "OUT": self.LOOPPID_OUT_ini,
                                              "IN": self.LOOPPID_IN_ini,
                                              "HI_LIM": self.LOOPPID_HI_LIM_ini,
                                              "LO_LIM": self.LOOPPID_LO_LIM_ini,
                                              "SET0": self.LOOPPID_SET0_ini,
                                              "SET1": self.LOOPPID_SET1_ini,
                                              "SET2": self.LOOPPID_SET2_ini,
                                              "SET3": self.LOOPPID_SET3_ini,
                                              "Busy":self.LOOPPID_Busy_ini,
                                              "Alarm":self.LOOPPID_Alarm_ini,
                                              "Alarm_HighLimit":self.LOOPPID_Alarm_HighLimit_ini,
                                              "Alarm_LowLimit":self.LOOPPID_Alarm_LowLimit_ini},
                                  "LOOP2PT": {"MODE0": self.LOOP2PT_MODE0_ini,
                                              "MODE1": self.LOOP2PT_MODE1_ini,
                                              "MODE2": self.LOOP2PT_MODE2_ini,
                                              "MODE3": self.LOOP2PT_MODE3_ini,
                                              "INTLKD": self.LOOP2PT_INTLKD_ini,
                                              "MAN": self.LOOP2PT_MAN_ini,
                                              "ERR": self.LOOP2PT_ERR_ini,
                                              "OUT": self.LOOP2PT_OUT_ini,
                                              "SET1": self.LOOP2PT_SET1_ini,
                                              "SET2": self.LOOP2PT_SET2_ini,
                                              "SET3": self.LOOP2PT_SET3_ini,
                                              "Busy":self.LOOP2PT_Busy_ini},
                                  "INTLK_D": {"value": self.INTLK_D_DIC_ini,
                                              "EN": self.INTLK_D_EN_ini,
                                              "COND": self.INTLK_D_COND_ini,
                                              "Busy":self.INTLK_D_Busy_ini},
                                  "INTLK_A": {"value":self.INTLK_A_DIC_ini,
                                              "EN":self.INTLK_A_EN_ini,
                                              "COND":self.INTLK_A_COND_ini,
                                              "SET":self.INTLK_A_SET_ini,
                                              "Busy":self.INTLK_A_Busy_ini},
                                  "FLAG": {"value":self.FLAG_DIC_ini,
                                           "INTLKD":self.FLAG_INTLKD_ini,
                                           "Busy":self.FLAG_Busy_ini},
                                  "Procedure": {"Running": self.Procedure_running_ini, "INTLKD": self.Procedure_INTLKD_ini, "EXIT": self.Procedure_EXIT_ini},
                                  "FF": self.FF_DIC_ini,
                                  "PARA_I":self.PARAM_I_DIC_ini,
                                  "PARA_F":self.PARAM_F_DIC_ini,
                                  "PARA_B":self.PARAM_B_DIC_ini,
                                  "PARA_T":self.PARAM_T_DIC_ini,
                                  "TIME":self.TIME_DIC_ini},
                         "Alarm": {"TT": {"FP": self.TT_FP_Alarm_ini,
                                          "BO": self.TT_BO_Alarm_ini},
                                   "PT": self.PT_Alarm_ini,
                                   "LEFT_REAL": self.LEFT_REAL_Alarm_ini,
                                   "Din": self.Din_Alarm_ini,
                                   "LOOPPID": self.LOOPPID_Alarm_ini},
                         "Active": {"TT": {"FP": self.TT_FP_Activated_ini,
                                          "BO": self.TT_BO_Activated_ini},
                                   "PT": self.PT_Activated_ini,
                                   "LEFT_REAL": self.LEFT_REAL_Activated_ini,
                                    "Din": self.Din_Activated_ini,
                                    "LOOPPID": self.LOOPPID_Activated_ini,
                                    "INI_CHECK": self.Ini_Check_ini},
                         "MainAlarm": self.MainAlarm_ini
                         }
        self.commands_package= pickle.dumps({})

    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:
            try:

                print(f"Sending request...")

                #  Send reply back to client
                # self.socket.send(b"Hello")

                self.client_command_fectch.emit()
                # # wait until command read from the main thread
                while not self.readcommand:
                    print("read command from GUI...")
                    time.sleep(0.1)
                self.readcommand = False

                # self.commands({})
                # print(self.receive_dic)
                message = pickle.loads(self.socket.recv())


                # print(f"Received reply [ {message} ]")
                self.update_data(message)
                time.sleep(self.period)
            except:
                (type, value, traceback) = sys.exc_info()
                exception_hook(type, value, traceback)

    @QtCore.Slot()
    def stop(self):
        self.Running = False
        try:
            self.socket.send('bye')
            self.socket.recv()
        except:
            print("Error disconnecting.")
        self.socket.close()

    def update_data(self,message):
        #message mush be a dictionary
        self.receive_dic = message
        self.client_data_transport.emit()

    @QtCore.Slot(object)
    def commands(self, MWcommands):
        # claim that whether MAN_SET is True or false
        print("Commands are here", datetime.datetime.now())
        print("commands", MWcommands)
        self.commands_package = pickle.dumps(MWcommands)
        print("commands len", len(MWcommands))
        if len(MWcommands) != 0:
            self.socket.send(self.commands_package)
            self.client_clear_commands.emit()
        else:
            self.socket.send(pickle.dumps({}))
        self.readcommand = True
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
