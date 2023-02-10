"""
Module SlowDAQWidgets contains the definition of all the custom widgets used in SlowDAQ

By: Mathieu Laurin														

v1.0 Initial code 29/11/19 ML
v1.1 Alarm on state widget 04/03/20 ML
"""

from PySide2 import QtCore, QtWidgets, QtGui
import time, platform, pickle
import os, copy
import pandas as pd
import slowcontrol_env_cons as sec

# FONT = "font-family: \"Calibri\"; font-size: 14px;"
FONT = "font-family: \"Calibri\"; font-size: 8px;"
LAG_FONT = "font-family: \"Calibri\"; font-size: 10px;"

# FONT = " "


# BORDER_RADIUS = "border-radius: 2px;"
BORDER_RADIUS = " "

C_LIGHT_GREY = "background-color: rgb(204,204,204);"
C_MEDIUM_GREY = "background-color: rgb(167,167,167);"
C_BKG_WHITE = "background-color: white;"
C_WHITE = "color: white;"
C_BLACK = "color: black;"
C_GREEN = "background-color: rgb(0,217,0);"
C_RED = "background-color: rgb(255,25,25);"
C_BLUE = "background-color: rgb(34,48,171);"
C_ORANGE = "background-color: rgb(255,132,27);"

# if platform.system() == "Linux":
#     QtGui.QFontDatabase.addApplicationFont("/usr/share/fonts/truetype/vista/calibrib.ttf")
#     FONT = "font-family: calibrib; font-size: 8px;"
#     TITLE_STYLE = "background-color: rgb(204,204,204);  font-family: calibrib;" \
#                   " font-size: 14px; "

# TITLE_STYLE = "background-color: rgb(204,204,204); border-radius: 10px; font-family: " \
#               "\"Calibri\"; font-size: 22px; font-weight: bold;"

#this title style is for SBC slowcontrol machine
TITLE_STYLE = "background-color: rgb(204,204,204); border-radius: 3px; font-family: " \
              "\"Calibri\"; font-size: 14px; font-weight: bold;"
BORDER_STYLE = "border-style: outset; border-width: 2px; border-radius: 4px;" \
               " border-color: black;"
LABEL_STYLE = "background-color: rgb(204,204,204); border-radius: 3px; font-family: \"Calibri\"; " \
              "font-size: 12px; font-weight: bold;"
TITLE_STYLE_1 = "background-color: white; border-radius: 3px; font-family: " \
              "\"Calibri\"; font-size: 14px; font-weight: bold;"
# TITLE_STYLE = "background-color: rgb(204,204,204); "
# BORDER_STYLE = " "
# FONT = " font-size: 14px;"
# TITLE_STYLE = "background-color: rgb(204,204,204);  " \
#                   " font-size: 14px; "




R=0.6 #Resolution rate


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
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2300*R, 1500*R))

        # reset the size of the window
        self.setMinimumSize(2300*R, 1500*R)
        self.resize(2300*R, 1500*R)
        self.setWindowTitle("Alarm Window")
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2300*R, 1500*R))



        self.Tab = QtWidgets.QTabWidget(self)
        self.Tab.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.Tab.setStyleSheet("font-weight: bold; font-size: 20px; font-family: Calibri;")
        self.Tab.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.Tab.setGeometry(QtCore.QRect(0*R, 0*R, 2300*R, 1500*R))

        self.PressureTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.PressureTab, "Pressure Transducers")

        self.RTDSET1Tab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDSET1Tab, "RTD SET 1")

        self.RTDSET2Tab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDSET2Tab, "RTD SET 2")

        self.RTDSET34Tab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDSET34Tab, "RTD SET 3&4")

        self.RTDLEFTTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDLEFTTab, "HEATER RTDs and ETC")

        self.LEFTVariableTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.LEFTVariableTab, "LEFT VARIABLEs")

        self.HTRTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.HTRTab, "HEATER VARIABLEs")

        self.MAN_ACT = QtWidgets.QPushButton(self)
        self.MAN_ACT.setObjectName("Label")
        self.MAN_ACT.setText("MAN_ACT")
        self.MAN_ACT.setGeometry(QtCore.QRect(0 * R, 0 * R, 150 * R, 50 * R))
        self.MAN_ACT.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.MAN_ACT.move(2100*R,1400*R)

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

        self.GroupRTD1 = QtWidgets.QGroupBox(self.RTDSET1Tab)
        self.GroupRTD1.setTitle("RTD SET 1")
        self.GroupRTD1.setLayout(self.GLRTD1)
        self.GroupRTD1.move(0*R, 0*R)

        self.GLRTD2 = QtWidgets.QGridLayout()
        # self.GLRTD2 = QtWidgets.QGridLayout(self)
        self.GLRTD2.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLRTD2.setSpacing(20*R)
        self.GLRTD2.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTD2 = QtWidgets.QGroupBox(self.RTDSET2Tab)
        self.GroupRTD2.setTitle("RTD SET 2")
        self.GroupRTD2.setLayout(self.GLRTD2)
        self.GroupRTD2.move(0*R, 0*R)

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
        self.GroupRTD4.move(0*R, 870*R)

        self.GLRTDLEFT = QtWidgets.QGridLayout()
        # self.GLRTDLEFT = QtWidgets.QGridLayout(self)
        self.GLRTDLEFT.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLRTDLEFT.setSpacing(20*R)
        self.GLRTDLEFT.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRTDLEFT = QtWidgets.QGroupBox(self.RTDLEFTTab)
        self.GroupRTDLEFT.setTitle(" LEFT RTDs ")
        self.GroupRTDLEFT.setLayout(self.GLRTDLEFT)
        self.GroupRTDLEFT.move(0*R, 0*R)

        self.GLLEFT = QtWidgets.QGridLayout()
        self.GLLEFT.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GLLEFT.setSpacing(20 * R)
        self.GLLEFT.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupLEFT = QtWidgets.QGroupBox(self.LEFTVariableTab)
        self.GroupLEFT.setTitle(" LEFT Variables ")
        self.GroupLEFT.setLayout(self.GLLEFT)
        self.GroupLEFT.move(0 * R, 0 * R)

        self.GLDIN = QtWidgets.QGridLayout()
        self.GLDIN.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GLDIN.setSpacing(20 * R)
        self.GLDIN.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupDIN = QtWidgets.QGroupBox(self.LEFTVariableTab)
        self.GroupDIN.setTitle(" DIN Variables ")
        self.GroupDIN.setLayout(self.GLDIN)
        self.GroupDIN.move(0 * R, 500 * R)

        self.GLHTR = QtWidgets.QGridLayout()
        self.GLHTR.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GLHTR.setSpacing(20 * R)
        self.GLHTR.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupHTR = QtWidgets.QGroupBox(self.HTRTab)
        self.GroupHTR.setTitle(" HTR Variables ")
        self.GroupHTR.setLayout(self.GLHTR)
        self.GroupHTR.move(0 * R, 0 * R)

        self.TT2111 = AlarmStatusWidget(self.RTDSET1Tab)
        self.TT2111.Label.setText("TT2111")

        self.TT2112 = AlarmStatusWidget(self.RTDSET1Tab)
        self.TT2112.Label.setText("TT2112")

        self.TT2113 = AlarmStatusWidget(self.RTDSET1Tab)
        self.TT2113.Label.setText("TT2113")

        self.TT2114 = AlarmStatusWidget(self.RTDSET1Tab)
        self.TT2114.Label.setText("TT2114")

        self.TT2115 = AlarmStatusWidget(self.RTDSET1Tab)
        self.TT2115.Label.setText("TT2115")

        self.TT2116 = AlarmStatusWidget(self.RTDSET1Tab)
        self.TT2116.Label.setText("TT2116")

        self.TT2117 = AlarmStatusWidget(self.RTDSET1Tab)
        self.TT2117.Label.setText("TT2117")

        self.TT2118 = AlarmStatusWidget(self.RTDSET1Tab)
        self.TT2118.Label.setText("TT2118")

        self.TT2119 = AlarmStatusWidget(self.RTDSET1Tab)
        self.TT2119.Label.setText("TT2119")

        self.TT2120 = AlarmStatusWidget(self.RTDSET1Tab)
        self.TT2120.Label.setText("TT2120")


        #RTD2

        self.TT2401 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2401.Label.setText("TT2401")

        self.TT2402 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2402.Label.setText("TT2402")

        self.TT2403 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2403.Label.setText("TT2403")

        self.TT2404 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2404.Label.setText("TT2404")

        self.TT2405 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2405.Label.setText("TT2405")

        self.TT2406 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2406.Label.setText("TT2406")

        self.TT2407 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2407.Label.setText("TT2407")

        self.TT2408 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2408.Label.setText("TT2408")

        self.TT2409 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2409.Label.setText("TT2409")

        self.TT2410 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2410.Label.setText("TT2410")

        self.TT2411 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2411.Label.setText("TT2411")

        self.TT2412 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2412.Label.setText("TT2412")

        self.TT2413 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2413.Label.setText("TT2413")

        self.TT2414 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2414.Label.setText("TT2414")

        self.TT2415 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2415.Label.setText("TT2415")

        self.TT2416 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2416.Label.setText("TT2416")

        self.TT2417 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2417.Label.setText("TT2417")

        self.TT2418 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2418.Label.setText("TT2418")

        self.TT2419 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2419.Label.setText("TT2419")

        self.TT2420 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2420.Label.setText("TT2420")

        self.TT2421 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2421.Label.setText("TT2421")

        self.TT2422 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2422.Label.setText("TT2422")

        self.TT2423 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2423.Label.setText("TT2423")

        self.TT2424 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2424.Label.setText("TT2424")

        self.TT2425 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2425.Label.setText("TT2425")

        self.TT2426 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2426.Label.setText("TT2426")

        self.TT2427 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2427.Label.setText("TT2427")

        self.TT2428 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2428.Label.setText("TT2428")

        self.TT2429 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2429.Label.setText("TT2429")

        self.TT2430 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2430.Label.setText("TT2430")

        self.TT2431 = AlarmStatusWidget(self.RTDSET2Tab)
        self.TT2431.Label.setText("TT2431")

        self.TT2432 = AlarmStatusWidget(self.RTDSET2Tab)
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
        self.PT1101.Indicator.SetUnit(" bar")
        self.PT1101.Low_Read.SetUnit(" bar")
        self.PT1101.High_Read.SetUnit(" bar")

        self.PT2316 = AlarmStatusWidget(self.PressureTab)
        self.PT2316.Label.setText("PT2316")
        self.PT2316.Indicator.SetUnit(" bar")
        self.PT2316.Low_Read.SetUnit(" bar")
        self.PT2316.High_Read.SetUnit(" bar")

        self.PT2121 = AlarmStatusWidget(self.PressureTab)
        self.PT2121.Label.setText("PT2121")
        self.PT2121.Indicator.SetUnit(" bar")
        self.PT2121.Low_Read.SetUnit(" bar")
        self.PT2121.High_Read.SetUnit(" bar")


        self.PT2330 = AlarmStatusWidget(self.PressureTab)
        self.PT2330.Label.setText("PT2330")
        self.PT2330.Indicator.SetUnit(" bar")
        self.PT2330.Low_Read.SetUnit(" bar")
        self.PT2330.High_Read.SetUnit(" bar")

        self.PT2335 = AlarmStatusWidget(self.PressureTab)
        self.PT2335.Label.setText("PT2335")
        self.PT2335.Indicator.SetUnit(" bar")
        self.PT2335.Low_Read.SetUnit(" bar")
        self.PT2335.High_Read.SetUnit(" bar")

        self.PT3308 = AlarmStatusWidget(self.PressureTab)
        self.PT3308.Label.setText("PT3308")
        self.PT3308.Indicator.SetUnit(" bar")
        self.PT3308.Low_Read.SetUnit(" bar")
        self.PT3308.High_Read.SetUnit(" bar")

        self.PT3309 = AlarmStatusWidget(self.PressureTab)
        self.PT3309.Label.setText("PT3309")
        self.PT3309.Indicator.SetUnit(" bar")
        self.PT3309.Low_Read.SetUnit(" bar")
        self.PT3309.High_Read.SetUnit(" bar")
        #!
        self.PT1325 = AlarmStatusWidget(self.PressureTab)
        self.PT1325.Label.setText("PT1325")
        self.PT1325.Indicator.SetUnit(" bar")
        self.PT1325.Low_Read.SetUnit(" bar")
        self.PT1325.High_Read.SetUnit(" bar")

        self.PT3311 = AlarmStatusWidget(self.PressureTab)
        self.PT3311.Label.setText("PT3311")
        self.PT3311.Indicator.SetUnit(" bar")
        self.PT3311.Low_Read.SetUnit(" bar")
        self.PT3311.High_Read.SetUnit(" bar")

        self.PT3314 = AlarmStatusWidget(self.PressureTab)
        self.PT3314.Label.setText("PT3314")
        self.PT3314.Indicator.SetUnit(" bar")
        self.PT3314.Low_Read.SetUnit(" bar")
        self.PT3314.High_Read.SetUnit(" bar")

        self.PT3320 = AlarmStatusWidget(self.PressureTab)
        self.PT3320.Label.setText("PT3320")
        self.PT3320.Indicator.SetUnit(" bar")
        self.PT3320.Low_Read.SetUnit(" bar")
        self.PT3320.High_Read.SetUnit(" bar")

        self.PT3332 = AlarmStatusWidget(self.PressureTab)
        self.PT3332.Label.setText("PT3332")
        self.PT3332.Indicator.SetUnit(" bar")
        self.PT3332.Low_Read.SetUnit(" bar")
        self.PT3332.High_Read.SetUnit(" bar")

        self.PT3333 = AlarmStatusWidget(self.PressureTab)
        self.PT3333.Label.setText("PT3333")
        self.PT3333.Indicator.SetUnit(" bar")
        self.PT3333.Low_Read.SetUnit(" bar")
        self.PT3333.High_Read.SetUnit(" bar")

        self.PT4306 = AlarmStatusWidget(self.PressureTab)
        self.PT4306.Label.setText("PT4306")
        self.PT4306.Indicator.SetUnit(" bar")
        self.PT4306.Low_Read.SetUnit(" bar")
        self.PT4306.High_Read.SetUnit(" bar")

        self.PT4315 = AlarmStatusWidget(self.PressureTab)
        self.PT4315.Label.setText("PT4315")
        self.PT4315.Indicator.SetUnit(" bar")
        self.PT4315.Low_Read.SetUnit(" bar")
        self.PT4315.High_Read.SetUnit(" bar")

        self.PT4319 = AlarmStatusWidget(self.PressureTab)
        self.PT4319.Label.setText("PT4319")
        self.PT4319.Indicator.SetUnit(" bar")
        self.PT4319.Low_Read.SetUnit(" bar")
        self.PT4319.High_Read.SetUnit(" bar")

        self.PT4322 = AlarmStatusWidget(self.PressureTab)
        self.PT4322.Label.setText("PT4322")
        self.PT4322.Indicator.SetUnit(" bar")
        self.PT4322.Low_Read.SetUnit(" bar")
        self.PT4322.High_Read.SetUnit(" bar")

        self.PT4325 = AlarmStatusWidget(self.PressureTab)
        self.PT4325.Label.setText("PT4325")
        self.PT4325.Indicator.SetUnit(" bar")
        self.PT4325.Low_Read.SetUnit(" bar")
        self.PT4325.High_Read.SetUnit(" bar")

        self.PT6302 = AlarmStatusWidget(self.PressureTab)
        self.PT6302.Label.setText("PT6302")
        self.PT6302.Indicator.SetUnit(" bar")
        self.PT6302.Low_Read.SetUnit(" bar")
        self.PT6302.High_Read.SetUnit(" bar")

        self.PT5304 = AlarmStatusWidget(self.PressureTab)
        self.PT5304.Label.setText("PT5304")
        self.PT5304.Indicator.SetUnit(" bar")
        self.PT5304.Low_Read.SetUnit(" bar")
        self.PT5304.High_Read.SetUnit(" bar")

        #left variable part
        self.LT3335 = AlarmStatusWidget(self.LEFTVariableTab)
        self.LT3335.Label.setText("LT3335")
        self.LT3335.Indicator.SetUnit(" in")
        self.LT3335.Low_Read.SetUnit(" in")
        self.LT3335.High_Read.SetUnit(" in")

        # 'BFM4313': 12788, 'LT3335': 12790, 'MFC1316_IN': 12792, "CYL3334_FCALC": 12832, "SERVO3321_IN_REAL": 12830, "TS1_MASS": 16288, "TS2_MASS": 16290, "TS3_MASS": 16292

        self.BFM4313 = AlarmStatusWidget(self.LEFTVariableTab)
        self.BFM4313.Label.setText("BFM4313")
        self.BFM4313.Indicator.SetUnit("")
        self.BFM4313.Low_Read.SetUnit("")
        self.BFM4313.High_Read.SetUnit("")

        self.MFC1316_IN = AlarmStatusWidget(self.LEFTVariableTab)
        self.MFC1316_IN.Label.setText("MFC1316_IN")
        self.MFC1316_IN.Indicator.SetUnit("")
        self.MFC1316_IN.Low_Read.SetUnit("")
        self.MFC1316_IN.High_Read.SetUnit("")

        self.CYL3334_FCALC = AlarmStatusWidget(self.LEFTVariableTab)
        self.CYL3334_FCALC.Label.setText("CYL3334_FCALC")
        self.CYL3334_FCALC.Indicator.SetUnit(" lbs")
        self.CYL3334_FCALC.Low_Read.SetUnit(" lbs")
        self.CYL3334_FCALC.High_Read.SetUnit(" lbs")

        self.SERVO3321_IN_REAL = AlarmStatusWidget(self.LEFTVariableTab)
        self.SERVO3321_IN_REAL.Label.setText("SERVO3321_IN_REAL")
        self.SERVO3321_IN_REAL.Indicator.SetUnit(" ")
        self.SERVO3321_IN_REAL.Low_Read.SetUnit(" ")
        self.SERVO3321_IN_REAL.High_Read.SetUnit(" ")

        self.TS1_MASS = AlarmStatusWidget(self.LEFTVariableTab)
        self.TS1_MASS.Label.setText("TS1_MASS")
        self.TS1_MASS.Indicator.SetUnit(" ")
        self.TS1_MASS.Low_Read.SetUnit(" ")
        self.TS1_MASS.High_Read.SetUnit(" ")

        self.TS2_MASS = AlarmStatusWidget(self.LEFTVariableTab)
        self.TS2_MASS.Label.setText("TS2_MASS")
        self.TS2_MASS.Indicator.SetUnit(" ")
        self.TS2_MASS.Low_Read.SetUnit(" ")
        self.TS2_MASS.High_Read.SetUnit(" ")

        self.TS3_MASS = AlarmStatusWidget(self.LEFTVariableTab)
        self.TS3_MASS.Label.setText("TS3_MASS")
        self.TS3_MASS.Indicator.SetUnit(" ")
        self.TS3_MASS.Low_Read.SetUnit(" ")
        self.TS3_MASS.High_Read.SetUnit(" ")

        self.PUMP3305_CON = AlarmStatusWidget(self.LEFTVariableTab)
        self.PUMP3305_CON.Label.setText("PUMP3305_CON")
        self.PUMP3305_CON.Indicator.SetUnit(" ")
        self.PUMP3305_CON.Low_Read.SetUnit(" ")
        self.PUMP3305_CON.High_Read.SetUnit(" ")



        self.LS3338 = AlarmStatusWidget(self.LEFTVariableTab)
        self.LS3338.Label.setText("LS3338")
        self.LS3338.Indicator.SetUnit(" ")
        self.LS3338.Low_Read.SetUnit(" ")
        self.LS3338.High_Read.SetUnit(" ")


        self.LS3339 = AlarmStatusWidget(self.LEFTVariableTab)
        self.LS3339.Label.setText("LS3339")
        self.LS3339.Indicator.SetUnit(" ")
        self.LS3339.Low_Read.SetUnit(" ")
        self.LS3339.High_Read.SetUnit(" ")


        self.ES3347 = AlarmStatusWidget(self.LEFTVariableTab)
        self.ES3347.Label.setText("ES3347")
        self.ES3347.Indicator.SetUnit(" ")
        self.ES3347.Low_Read.SetUnit(" ")
        self.ES3347.High_Read.SetUnit(" ")


        self.PUMP3305_OL = AlarmStatusWidget(self.LEFTVariableTab)
        self.PUMP3305_OL.Label.setText("PUMP3305_OL")
        self.PUMP3305_OL.Indicator.SetUnit(" ")
        self.PUMP3305_OL.Low_Read.SetUnit(" ")
        self.PUMP3305_OL.High_Read.SetUnit(" ")


        self.PS2352 = AlarmStatusWidget(self.LEFTVariableTab)
        self.PS2352.Label.setText("PS2352")
        self.PS2352.Indicator.SetUnit(" ")
        self.PS2352.Low_Read.SetUnit(" ")
        self.PS2352.High_Read.SetUnit(" ")


        self.PS1361 = AlarmStatusWidget(self.LEFTVariableTab)
        self.PS1361.Label.setText("PS1361")
        self.PS1361.Indicator.SetUnit(" ")
        self.PS1361.Low_Read.SetUnit(" ")
        self.PS1361.High_Read.SetUnit(" ")


        self.PS8302 = AlarmStatusWidget(self.LEFTVariableTab)
        self.PS8302.Label.setText("PS8302")
        self.PS8302.Indicator.SetUnit(" ")
        self.PS8302.Low_Read.SetUnit(" ")
        self.PS8302.High_Read.SetUnit(" ")


        self.SERVO3321 = AlarmStatusWidget(self.HTRTab)
        self.SERVO3321.Label.setText("SERVO3321")
        self.SERVO3321.Indicator.SetUnit(" ")
        self.SERVO3321.Low_Read.SetUnit(" ")
        self.SERVO3321.High_Read.SetUnit(" ")


        self.HTR6225 = AlarmStatusWidget(self.HTRTab)
        self.HTR6225.Label.setText("HTR6225")
        self.HTR6225.Indicator.SetUnit(" ")
        self.HTR6225.Low_Read.SetUnit(" ")
        self.HTR6225.High_Read.SetUnit(" ")


        self.HTR2123 = AlarmStatusWidget(self.HTRTab)
        self.HTR2123.Label.setText("HTR2123")
        self.HTR2123.Indicator.SetUnit(" ")
        self.HTR2123.Low_Read.SetUnit(" ")
        self.HTR2123.High_Read.SetUnit(" ")


        self.HTR2124 = AlarmStatusWidget(self.HTRTab)
        self.HTR2124.Label.setText("HTR2124")
        self.HTR2124.Indicator.SetUnit(" ")
        self.HTR2124.Low_Read.SetUnit(" ")
        self.HTR2124.High_Read.SetUnit(" ")

        self.HTR2125 = AlarmStatusWidget(self.HTRTab)
        self.HTR2125.Label.setText("HTR2125")
        self.HTR2125.Indicator.SetUnit(" ")
        self.HTR2125.Low_Read.SetUnit(" ")
        self.HTR2125.High_Read.SetUnit(" ")

        self.HTR1202 = AlarmStatusWidget(self.HTRTab)
        self.HTR1202.Label.setText("HTR1202")
        self.HTR1202.Indicator.SetUnit(" ")
        self.HTR1202.Low_Read.SetUnit(" ")
        self.HTR1202.High_Read.SetUnit(" ")

        self.HTR2203 = AlarmStatusWidget(self.HTRTab)
        self.HTR2203.Label.setText("HTR2203")
        self.HTR2203.Indicator.SetUnit(" ")
        self.HTR2203.Low_Read.SetUnit(" ")
        self.HTR2203.High_Read.SetUnit(" ")

        self.HTR6202 = AlarmStatusWidget(self.HTRTab)
        self.HTR6202.Label.setText("HTR6202")
        self.HTR6202.Indicator.SetUnit(" ")
        self.HTR6202.Low_Read.SetUnit(" ")
        self.HTR6202.High_Read.SetUnit(" ")

        self.HTR6206 = AlarmStatusWidget(self.HTRTab)
        self.HTR6206.Label.setText("HTR6206")
        self.HTR6206.Indicator.SetUnit(" ")
        self.HTR6206.Low_Read.SetUnit(" ")
        self.HTR6206.High_Read.SetUnit(" ")

        self.HTR6210 = AlarmStatusWidget(self.HTRTab)
        self.HTR6210.Label.setText("HTR6210")
        self.HTR6210.Indicator.SetUnit(" ")
        self.HTR6210.Low_Read.SetUnit(" ")
        self.HTR6210.High_Read.SetUnit(" ")

        self.HTR6223 = AlarmStatusWidget(self.HTRTab)
        self.HTR6223.Label.setText("HTR6223")
        self.HTR6223.Indicator.SetUnit(" ")
        self.HTR6223.Low_Read.SetUnit(" ")
        self.HTR6223.High_Read.SetUnit(" ")

        self.HTR6224 = AlarmStatusWidget(self.HTRTab)
        self.HTR6224.Label.setText("HTR6224")
        self.HTR6224.Indicator.SetUnit(" ")
        self.HTR6224.Low_Read.SetUnit(" ")
        self.HTR6224.High_Read.SetUnit(" ")

        self.HTR6219 = AlarmStatusWidget(self.HTRTab)
        self.HTR6219.Label.setText("HTR6219")
        self.HTR6219.Indicator.SetUnit(" ")
        self.HTR6219.Low_Read.SetUnit(" ")
        self.HTR6219.High_Read.SetUnit(" ")

        self.HTR6221 = AlarmStatusWidget(self.HTRTab)
        self.HTR6221.Label.setText("HTR6221")
        self.HTR6221.Indicator.SetUnit(" ")
        self.HTR6221.Low_Read.SetUnit(" ")
        self.HTR6221.High_Read.SetUnit(" ")

        self.HTR6214 = AlarmStatusWidget(self.HTRTab)
        self.HTR6214.Label.setText("HTR6214")
        self.HTR6214.Indicator.SetUnit(" ")
        self.HTR6214.Low_Read.SetUnit(" ")
        self.HTR6214.High_Read.SetUnit(" ")





        # "LS3338": False, "LS3339": False, "ES3347": False, "PUMP3305_CON": False, "PUMP3305_OL": False, "PS2352": False, "PS1361": False, "PS8302": False}
        # #

        # make a directory for the alarm instrument and assign instrument to certain position
        #IF you change the dimenstion of the following matrixes, don't forget to change TempMatrix in the Reassign function
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

        self.AlarmPTdir = {0: {0: self.PT1101, 1: self.PT1325, 2: self.PT2316, 3: self.PT2121, 4: self.PT2330},
                           1: {0: self.PT2335, 1: self.PT3308, 2: self.PT3309, 3: self.PT3311, 4: self.PT3314},
                           2: {0: self.PT3320, 1: self.PT3332, 2: self.PT3333, 3: self.PT4306, 4: self.PT4315},
                           3: {0: self.PT4319, 1: self.PT4322, 2: self.PT4325, 3: self.PT5304, 4: self.PT6302}}


        self.AlarmRTDLEFTdir = {0: {0: self.TT4330, 1: self.TT6220, 2: self.TT6213, 3: self.TT6401, 4: self.TT6203},
                                1: {0: self.TT6404, 1: self.TT6207, 2: self.TT6405, 3: self.TT6211, 4: self.TT6406},
                                2: {0: self.TT6223, 1: self.TT6410, 2: self.TT6408, 3: self.TT6409, 4: self.TT6412},
                                3: {0: self.TT3402, 1: self.TT3401, 2: self.TT7401, 3: self.TT7202, 4: self.TT7403},
                                4: {0: self.TT6222, 1: self.TT6407, 2: self.TT6415, 3: self.TT6416, 4: self.TT6411},
                                5: {0: self.TT6413, 1: self.TT6414}}

        self.AlarmLEFTdir = {0:{0: self.BFM4313, 1: self.LT3335, 2: self.MFC1316_IN, 3: self.CYL3334_FCALC, 4: self.SERVO3321_IN_REAL},
                             1:{0: self.TS1_MASS, 1: self.TS2_MASS, 2: self.TS3_MASS}}

        self.AlarmDindir = {0:{0: self.LS3338, 1: self.LS3339, 2: self.ES3347, 3: self.PUMP3305_CON, 4: self.PUMP3305_OL},
                             1:{0: self.PS2352, 1: self.PS1361, 2: self.PS8302}}

        self.AlarmHTRdir = {
            0: {0: self.SERVO3321, 1: self.HTR6225, 2: self.HTR2123, 3: self.HTR2124, 4: self.HTR2125},
            1: {0: self.HTR1202, 1: self.HTR2203, 2: self.HTR6202, 3: self.HTR6206, 4: self.HTR6210},
            2: {0: self.HTR6223, 1: self.HTR6224, 2: self.HTR6219, 3: self.HTR6221, 4: self.HTR6214}}

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
        # self.AlarmPTdir = {0: {0: "self.PT1101", 1: "self.PT2316", 2: "self.PT2121", 3: "self.PT2330", 4: "self.PT2335"},
        #                    1: {0: "self.PT3308", 1: "self.PT3309", 2: "self.PT1325", 3: "self.PT3311", 4: "self.PT3314"},
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
        self.i_LEFT_max = len(self.AlarmLEFTdir)
        # which is 4
        self.j_LEFT_max = len(self.AlarmLEFTdir[0])

        self.i_DIN_max = len(self.AlarmDindir)
        self.j_DIN_max = len(self.AlarmDindir[0])

        self.i_HTR_max = len(self.AlarmHTRdir)
        self.j_HTR_max = len(self.AlarmHTRdir[0])

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

        self.i_LEFT_last = len(self.AlarmLEFTdir) - 1
        self.j_LEFT_last = len(self.AlarmLEFTdir[self.i_LEFT_last]) - 1

        self.i_DIN_last = len(self.AlarmDindir) - 1
        self.j_DIN_last = len(self.AlarmDindir[self.i_DIN_last]) - 1

        self.i_HTR_last = len(self.AlarmHTRdir) - 1
        self.j_HTR_last = len(self.AlarmHTRdir[self.i_HTR_last]) - 1
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

        for i in range(0, self.i_LEFT_max):
            for j in range(0, self.j_LEFT_max):
                # self.GLPT.addWidget(eval(self.AlarmPTdir[i][j]), i, j)
                self.GLLEFT.addWidget(self.AlarmLEFTdir[i][j], i, j)
                # end the position generator when i= last element's row number -1, j= last element's column number
                if (i, j) == (self.i_LEFT_last, self.j_LEFT_last):
                    break
            if (i, j) == (self.i_LEFT_last, self.j_LEFT_last):
                break

        for i in range(0, self.i_DIN_max):
            for j in range(0, self.j_DIN_max):
                self.GLDIN.addWidget(self.AlarmDindir[i][j], i, j)
                if (i, j) == (self.i_DIN_last, self.j_DIN_last):
                    break
            if (i, j) == (self.i_DIN_last, self.j_DIN_last):
                break

        for i in range(0, self.i_HTR_max):
            for j in range(0, self.j_HTR_max):
                self.GLHTR.addWidget(self.AlarmHTRdir[i][j], i, j)
                if (i, j) == (self.i_HTR_last, self.j_HTR_last):
                    break
            if (i, j) == (self.i_HTR_last, self.j_HTR_last):
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

        TempRTD2dir = {0: {0: None, 1: None, 2: None, 3: None, 4: None},
                             1: {0: None, 1: None, 2: None, 3: None, 4: None},
                             2: {0: None, 1: None, 2: None, 3: None, 4: None},
                             3: {0: None, 1: None, 2: None, 3: None, 4: None},
                             4: {0: None, 1: None, 2: None, 3: None, 4: None},
                             5: {0: None, 1: None, 2: None, 3: None, 4: None},
                             6: {0: None, 1: None}}

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

        TempRTD3dir = {0: {0: None, 1: None, 2: None, 3: None, 4: None},
                       1: {0: None, 1: None, 2: None, 3: None, 4: None},
                       2: {0: None, 1: None, 2: None, 3: None, 4: None},
                       3: {0: None}}

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

        TempRTD4dir = {0: {0: None, 1: None, 2: None, 3: None, 4: None},
                       1: {0: None, 1: None, 2: None, 3: None, 4: None}}

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

        TempRTDLEFTdir = {0: {0: None, 1: None, 2: None, 3: None, 4: None},
                          1: {0: None, 1: None, 2: None, 3: None, 4: None},
                          2: {0: None, 1: None, 2: None, 3: None, 4: None},
                          3: {0: None, 1: None, 2: None, 3: None, 4: None},
                          4: {0: None, 1: None, 2: None, 3: None, 4: None},
                          5: {0: None, 1: None}}

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

        TempPTdir = {0: {0: None, 1: None, 2: None, 3: None, 4: None},
                           1: {0: None, 1: None, 2: None, 3: None, 4: None},
                           2: {0: None, 1: None, 2: None, 3: None, 4: None},
                           3: {0: None, 1: None, 2: None, 3: None, 4: None}}
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
                    if l_PT == l_PT_max + 1:
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
                    if l_PT == l_PT_max + 1:
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


    @QtCore.Slot()
    def ReassignLEFTOrder(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate


        TempRefLEFTdir = self.AlarmLEFTdir

        TempLEFTdir = {0:{0: None, 1: None, 2: None, 3: None, 4: None},
                       1:{0: None, 1: None, 2: None}}
        # l_RTD1_max is max number of column

        l_LEFT = 0
        k_LEFT = 0


        i_LEFT_max = len(self.AlarmLEFTdir)

        j_LEFT_max = len(self.AlarmLEFTdir[0])


        i_LEFT_last = len(self.AlarmLEFTdir) - 1

        j_LEFT_last = len(self.AlarmLEFTdir[i_LEFT_last]) - 1


        l_LEFT_max = j_LEFT_max - 1

        # LEFT
        for i in range(0, i_LEFT_max):
            for j in range(0, j_LEFT_max):
                if TempRefLEFTdir[i][j].Alarm:
                    TempLEFTdir[k_LEFT][l_LEFT] = TempRefLEFTdir[i][j]
                    l_LEFT = l_LEFT + 1
                    if l_LEFT == l_LEFT_max+1:
                        l_LEFT = 0
                        k_LEFT = k_LEFT + 1
                if (i, j) == (i_LEFT_last, j_LEFT_last):
                    break
            if (i, j) == (i_LEFT_last, j_LEFT_last):
                break

        for i in range(0, i_LEFT_max):
            for j in range(0, j_LEFT_max):
                if not TempRefLEFTdir[i][j].Alarm:
                    TempLEFTdir[k_LEFT][l_LEFT] = TempRefLEFTdir[i][j]
                    l_LEFT = l_LEFT + 1
                    if l_LEFT == l_LEFT_max+1:
                        l_LEFT = 0
                        k_LEFT = k_LEFT + 1
                    if (i, j) == (i_LEFT_last, j_LEFT_last):
                        break
                if (i, j) == (i_LEFT_last, j_LEFT_last):
                    break

        # Reassign position
        # end the position generator when i= last element's row number, j= last element's column number

        # end the position generator when i= last element's row number, j= last element's column number
        for i in range(0, i_LEFT_max):
            for j in range(0, j_LEFT_max):
                self.GLLEFT.addWidget(TempLEFTdir[i][j], i, j)
                if (i, j) == (i_LEFT_last, j_LEFT_last):
                    break
            if (i, j) == (i_LEFT_last, j_LEFT_last):
                break

    @QtCore.Slot()
    def ReassignDinOrder(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate

        TempRefDindir = self.AlarmDindir

        TempDindir = {0: {0: None, 1: None, 2: None, 3: None, 4: None},
                       1: {0: None, 1: None, 2: None}}
        # l_RTD1_max is max number of column

        l_DIN = 0
        k_DIN = 0

        i_DIN_max = len(self.AlarmDindir)

        j_DIN_max = len(self.AlarmDindir[0])

        i_DIN_last = len(self.AlarmDindir) - 1

        j_DIN_last = len(self.AlarmDindir[i_DIN_last]) - 1

        l_DIN_max = j_DIN_max - 1


        for i in range(0, i_DIN_max):
            for j in range(0, j_DIN_max):
                if TempRefDindir[i][j].Alarm:
                    TempDindir[k_DIN][l_DIN] = TempRefDindir[i][j]
                    l_DIN = l_DIN + 1
                    if l_DIN == l_DIN_max + 1:
                        l_DIN = 0
                        k_DIN = k_DIN + 1
                if (i, j) == (i_DIN_last, j_DIN_last):
                    break
            if (i, j) == (i_DIN_last, j_DIN_last):
                break

        for i in range(0, i_DIN_max):
            for j in range(0, j_DIN_max):
                if not TempRefDindir[i][j].Alarm:
                    TempDindir[k_DIN][l_DIN] = TempRefDindir[i][j]
                    l_DIN = l_DIN + 1
                    if l_DIN == l_DIN_max + 1:
                        l_DIN = 0
                        k_DIN = k_DIN + 1
                    if (i, j) == (i_DIN_last, j_DIN_last):
                        break
                if (i, j) == (i_DIN_last, j_DIN_last):
                    break

        # Reassign position
        # end the position generator when i= last element's row number, j= last element's column number

        # end the position generator when i= last element's row number, j= last element's column number
        for i in range(0, i_DIN_max):
            for j in range(0, j_DIN_max):
                self.GLDIN.addWidget(TempDindir[i][j], i, j)
                if (i, j) == (i_DIN_last, j_DIN_last):
                    break
            if (i, j) == (i_DIN_last, j_DIN_last):
                break

    @QtCore.Slot()
    def ReassignHTROrder(self):
        # check the status of the Widget and reassign the diretory
        # establish 2 diretory, reorder TempDic to reorder the widgets
        # k,l are pointers in the TempDic, ij are pointers in TempRefDic
        # i_max, j_max are max row and column number
        # l max are max column number+1
        # i_last,j_last are last elements's diretory coordinate

        TempRefHTRdir = self.AlarmHTRdir

        TempHTRdir = {
            0: {0: None, 1: None, 2: None, 3: None, 4: None},
            1: {0: None, 1: None, 2: None, 3: None, 4: None},
            2: {0: None, 1: None, 2: None, 3: None, 4: None}}
        # l_RTD1_max is max number of column

        l_HTR = 0
        k_HTR = 0

        i_HTR_max = len(self.AlarmHTRdir)

        j_HTR_max = len(self.AlarmHTRdir[0])

        i_HTR_last = len(self.AlarmHTRdir) - 1

        j_HTR_last = len(self.AlarmHTRdir[i_HTR_last]) - 1

        l_HTR_max = j_HTR_max - 1

        for i in range(0, i_HTR_max):
            for j in range(0, j_HTR_max):
                if TempRefHTRdir[i][j].Alarm:
                    TempHTRdir[k_HTR][l_HTR] = TempRefHTRdir[i][j]
                    l_HTR = l_HTR + 1
                    if l_HTR == l_HTR_max + 1:
                        l_HTR = 0
                        k_HTR = k_HTR + 1
                if (i, j) == (i_HTR_last, j_HTR_last):
                    break
            if (i, j) == (i_HTR_last, j_HTR_last):
                break

        for i in range(0, i_HTR_max):
            for j in range(0, j_HTR_max):
                if not TempRefHTRdir[i][j].Alarm:
                    TempHTRdir[k_HTR][l_HTR] = TempRefHTRdir[i][j]
                    l_HTR = l_HTR + 1
                    if l_HTR == l_HTR_max + 1:
                        l_HTR = 0
                        k_HTR = k_HTR + 1
                    if (i, j) == (i_HTR_last, j_HTR_last):
                        break
                if (i, j) == (i_HTR_last, j_HTR_last):
                    break

        # Reassign position
        # end the position generator when i= last element's row number, j= last element's column number

        # end the position generator when i= last element's row number, j= last element's column number
        for i in range(0, i_HTR_max):
            for j in range(0, j_HTR_max):
                self.GLHTR.addWidget(TempHTRdir[i][j], i, j)
                if (i, j) == (i_HTR_last, j_HTR_last):
                    break
            if (i, j) == (i_HTR_last, j_HTR_last):
                break

class INTLCK_Win_v2(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2300*R, 1500*R))

        # reset the size of the window
        self.setMinimumSize(2300*R, 1500*R)
        self.resize(2300*R, 1500*R)
        self.setWindowTitle("INTLCK Window")
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2300*R, 1500*R))

        self.Tab = QtWidgets.QTabWidget(self)
        self.Tab.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.Tab.setStyleSheet("font-weight: bold; font-size: 20px; font-family: Calibri;")
        self.Tab.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.Tab.setGeometry(QtCore.QRect(0*R, 0*R, 2300*R, 1500*R))

        self.PressureTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.PressureTab, "PT INTLCK")

        self.RTDSET1Tab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDSET1Tab, "RTD INTLCK")


        # self.GLPTLO = QtWidgets.QGridLayout()
        # # self.GLPT = QtWidgets.QGridLayout(self)
        # self.GLPTLO.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        # self.GLPTLO.setSpacing(20*R)
        # self.GLPTLO.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupPTLO = QtWidgets.QGroupBox(self.PressureTab)
        self.GroupPTLO.setTitle("PT LO INTLCK")
        # self.GroupPTLO.setLayout(self.GLPTLO)
        self.GroupPTLO.move(0*R, 0*R)
        self.GroupPTLO.setMinimumSize(2200*R,250*R)


        #
        # self.GLPTHI = QtWidgets.QGridLayout()
        # # self.GLPT = QtWidgets.QGridLayout(self)
        # self.GLPTHI.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        # self.GLPTHI.setSpacing(20*R)
        # self.GLPTHI.setAlignment(QtCore.Qt.AlignCenter)
        #
        self.GroupPTHI = QtWidgets.QGroupBox(self.PressureTab)
        self.GroupPTHI.setTitle("PT HI INTLCK")
        # self.GroupPTHI.setLayout(self.GLPTHI)
        self.GroupPTHI.move(0*R, 300*R)
        self.GroupPTHI.setMinimumSize(2200 * R, 250 * R)
        #
        #
        #
        # self.GLPTHIHI = QtWidgets.QGridLayout()
        # # self.GLPT = QtWidgets.QGridLayout(self)
        # self.GLPTHIHI.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        # self.GLPTHIHI.setSpacing(20*R)
        # self.GLPTHIHI.setAlignment(QtCore.Qt.AlignCenter)
        #
        self.GroupPTHIHI = QtWidgets.QGroupBox(self.PressureTab)
        self.GroupPTHIHI.setTitle("PT HIHI INTLCK")
        # self.GroupPTHIHI.setLayout(self.GLPTHIHI)
        self.GroupPTHIHI.move(0*R, 600*R)
        self.GroupPTHIHI.setMinimumSize(2200 * R, 250 * R)
        #
        #
        # self.GLOTHER = QtWidgets.QGridLayout()
        # self.GLOTHER.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        # self.GLOTHER.setSpacing(20 * R)
        # self.GLOTHER.setAlignment(QtCore.Qt.AlignCenter)
        #
        self.GroupOTHER = QtWidgets.QGroupBox(self.PressureTab)
        self.GroupOTHER.setTitle("OTHER")
        # self.GroupOTHER.setLayout(self.GLOTHER)
        self.GroupOTHER.move(0 * R, 900 * R)
        self.GroupOTHER.setMinimumSize(2200 * R, 500 * R)
        #
        # self.GLTTLO = QtWidgets.QGridLayout()
        # self.GLTTLO.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        # self.GLTTLO.setSpacing(20*R)
        # self.GLTTLO.setAlignment(QtCore.Qt.AlignCenter)
        #
        self.GroupTTLO = QtWidgets.QGroupBox(self.RTDSET1Tab)
        self.GroupTTLO.setTitle("RTD LO INTLCK")
        # self.GroupTTLO.setLayout(self.GLTTLO)
        self.GroupTTLO.move(0*R, 0*R)
        self.GroupTTLO.setMinimumSize(2200 * R, 250 * R)
        #
        # self.GLTTHI = QtWidgets.QGridLayout()
        # self.GLTTHI.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        # self.GLTTHI.setSpacing(20 * R)
        # self.GLTTHI.setAlignment(QtCore.Qt.AlignCenter)
        #
        self.GroupTTHI = QtWidgets.QGroupBox(self.RTDSET1Tab)
        self.GroupTTHI.setTitle("RTD HI INTLCK")
        # self.GroupTTHI.setLayout(self.GLTTHI)
        self.GroupTTHI.move(0 * R, 300 * R)
        self.GroupTTHI.setMinimumSize(2200 * R, 500 * R)
        #
        # self.GLTTHIHI = QtWidgets.QGridLayout()
        # self.GLTTHIHI.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        # self.GLTTHIHI.setSpacing(20 * R)
        # self.GLTTHIHI.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupTTHIHI = QtWidgets.QGroupBox(self.RTDSET1Tab)
        self.GroupTTHIHI.setTitle("RTD HIHI INTLCK")
        # self.GroupTTHIHI.setLayout(self.GLTTHIHI)
        self.GroupTTHIHI.move(0 * R, 900 * R)
        self.GroupTTHIHI.setMinimumSize(2200 * R, 500 * R)
        #
        #
        # #
        self.PT4306_LO_INTLK = INTLK_RA_Widget_v2(self.PressureTab)
        self.PT4306_LO_INTLK.Label.setText("PT4306_LO")
        self.PT4306_LO_INTLK.setObjectName("PT4306_LO_INTLK")
        self.PT4306_LO_INTLK.move(0*R,50*R)

        self.PT4306_HI_INTLK = INTLK_RA_Widget_v2(self.PressureTab)
        self.PT4306_HI_INTLK.Label.setText("PT4306_HI")
        self.PT4306_HI_INTLK.setObjectName("PT4306_HI_INTLK")
        self.PT4306_HI_INTLK.move(0*R,350*R)

        self.PT4322_HI_INTLK = INTLK_RA_Widget_v2(self.PressureTab)
        self.PT4322_HI_INTLK.Label.setText("PT4322_HI")
        self.PT4322_HI_INTLK.setObjectName("PT4322_HI_INTLK")
        self.PT4322_HI_INTLK.move(450*R, 350*R)

        self.PT4322_HIHI_INTLK = INTLK_LA_Widget_v2(self.PressureTab)
        self.PT4322_HIHI_INTLK.Label.setText("PT4322_HIHI")
        self.PT4322_HIHI_INTLK.setObjectName("PT4322_HIHI_INTLK")
        self.PT4322_HIHI_INTLK.move(0*R, 650*R)

        self.PT4319_HI_INTLK = INTLK_RA_Widget_v2(self.PressureTab)
        self.PT4319_HI_INTLK.Label.setText("PT4319_HI")
        self.PT4319_HI_INTLK.setObjectName("PT4319_HI_INTLK")
        self.PT4319_HI_INTLK.move(900*R, 350*R)

        self.PT4319_HIHI_INTLK = INTLK_LA_Widget_v2(self.PressureTab)
        self.PT4319_HIHI_INTLK.Label.setText("PT4319_HIHI")
        self.PT4319_HIHI_INTLK.setObjectName("PT4319_HIHI_INTLK")
        self.PT4319_HIHI_INTLK.move(450*R, 650*R)

        self.PT4325_HI_INTLK = INTLK_RA_Widget_v2(self.PressureTab)
        self.PT4325_HI_INTLK.Label.setText("PT4325_HI")
        self.PT4325_HI_INTLK.setObjectName("PT4325_HI_INTLK")
        self.PT4325_HI_INTLK.move(1350*R, 350*R)

        self.PT4325_HIHI_INTLK = INTLK_LA_Widget_v2(self.PressureTab)
        self.PT4325_HIHI_INTLK.Label.setText("PT4325_HIHI")
        self.PT4325_HIHI_INTLK.setObjectName("PT4325_HIHI_INTLK")
        self.PT4325_HIHI_INTLK.move(900*R,650*R)

        self.TS1_INTLK = INTLK_LD_Widget_v2(self.PressureTab)
        self.TS1_INTLK.Label.setText("TS1")
        self.TS1_INTLK.setObjectName("TS1")
        self.TS1_INTLK.move(0*R,950*R)

        self.ES3347_INTLK = INTLK_RD_Widget_v2(self.PressureTab)
        self.ES3347_INTLK.Label.setText("ES3347")
        self.ES3347_INTLK.setObjectName("ES3347")
        self.ES3347_INTLK.move(1350*R, 950*R)

        self.PUMP3305_OL_INTLK = INTLK_LD_Widget_v2(self.PressureTab)
        self.PUMP3305_OL_INTLK.Label.setText("PUMP3305_OL")
        self.PUMP3305_OL_INTLK.setObjectName("PUMP3305_OL")
        self.PUMP3305_OL_INTLK.move(1800*R, 950*R)

        self.TS2_INTLK = INTLK_LD_Widget_v2(self.PressureTab)
        self.TS2_INTLK.Label.setText("TS2")
        self.TS2_INTLK.setObjectName("TS2")
        self.TS2_INTLK.move(450*R, 950*R)

        self.TS3_INTLK = INTLK_LD_Widget_v2(self.PressureTab)
        self.TS3_INTLK.Label.setText("TS3")
        self.TS3_INTLK.setObjectName("TS3")
        self.TS3_INTLK.move(900*R, 950*R)

        self.PU_PRIME_INTLK = INTLK_LD_Widget_v2(self.PressureTab)
        self.PU_PRIME_INTLK.Label.setText("PU_PRIME")
        self.PU_PRIME_INTLK.setObjectName("PU_PRIME")
        self.PU_PRIME_INTLK.move(0*R, 1150*R)

        #

        self.TT2118_HI_INTLK = INTLK_LA_Widget_v2(self.RTDSET1Tab)
        self.TT2118_HI_INTLK.Label.setText("TT2118_HI")
        self.TT2118_HI_INTLK.move(0*R,350*R)

        self.TT2118_LO_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT2118_LO_INTLK.Label.setText("TT2118_LO")
        self.TT2118_LO_INTLK.move(0*R, 50*R)

        self.TT6203_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6203_HI_INTLK.Label.setText("TT6203_HI")
        self.TT6203_HI_INTLK.move(450*R, 350*R )

        self.TT6207_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6207_HI_INTLK.Label.setText("TT6207_HI")
        self.TT6207_HI_INTLK.move(900*R, 350*R)

        self.TT6211_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6211_HI_INTLK.Label.setText("TT6211_HI")
        self.TT6211_HI_INTLK.move(1350*R,350*R)

        self.TT6213_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6213_HI_INTLK.Label.setText("TT6213_HI")
        self.TT6213_HI_INTLK.move(1800*R, 350*R)

        self.TT6222_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6222_HI_INTLK.Label.setText("TT6222_HI")
        self.TT6222_HI_INTLK.move(0*R, 550*R)

        self.TT6407_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6407_HI_INTLK.Label.setText("TT6407_HI")
        self.TT6407_HI_INTLK.move(450*R, 550*R)

        self.TT6408_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6408_HI_INTLK.Label.setText("TT6408_HI")
        self.TT6408_HI_INTLK.move(900*R, 550*R)

        self.TT6409_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6409_HI_INTLK.Label.setText("TT6409_HI")
        self.TT6409_HI_INTLK.move(1350*R,550*R)

        self.TT6203_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6203_HIHI_INTLK.Label.setText("TT6203_HIHI")
        self.TT6203_HIHI_INTLK.move(0*R,950*R)

        self.TT6207_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6207_HIHI_INTLK.Label.setText("TT6207_HIHI")
        self.TT6207_HIHI_INTLK.move(450 * R, 950 * R)

        self.TT6211_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6211_HIHI_INTLK.Label.setText("TT6211_HIHI")
        self.TT6211_HIHI_INTLK.move(900 * R, 950 * R)

        self.TT6213_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6213_HIHI_INTLK.Label.setText("TT6213_HIHI")
        self.TT6213_HIHI_INTLK.move(1350 * R, 950 * R)

        self.TT6222_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6222_HIHI_INTLK.Label.setText("TT6222_HIHI")
        self.TT6222_HIHI_INTLK.move(1800 * R, 950 * R)

        self.TT6407_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6407_HIHI_INTLK.Label.setText("TT6407_HIHI")
        self.TT6407_HIHI_INTLK.move(0 * R, 1150 * R)

        self.TT6408_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6408_HIHI_INTLK.Label.setText("TT6408_HIHI")
        self.TT6408_HIHI_INTLK.move(0 * R, 1150 * R)

        self.TT6409_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6409_HIHI_INTLK.Label.setText("TT6409_HIHI")
        self.TT6409_HIHI_INTLK.move(0 * R, 1150 * R)



class INTLCK_Win(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2300*R, 1500*R))

        # reset the size of the window
        self.setMinimumSize(2300*R, 1500*R)
        self.resize(2300*R, 1500*R)
        self.setWindowTitle("INTLCK Window")
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 2300*R, 1500*R))

        self.Tab = QtWidgets.QTabWidget(self)
        self.Tab.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.Tab.setStyleSheet("font-weight: bold; font-size: 20px; font-family: Calibri;")
        self.Tab.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.Tab.setGeometry(QtCore.QRect(0*R, 0*R, 2300*R, 1500*R))

        self.PressureTab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.PressureTab, "PT INTLCK")

        self.RTDSET1Tab = QtWidgets.QTabWidget(self.Tab)
        self.Tab.addTab(self.RTDSET1Tab, "RTD INTLCK")


        self.GLPTLO = QtWidgets.QGridLayout()
        # self.GLPT = QtWidgets.QGridLayout(self)
        self.GLPTLO.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLPTLO.setSpacing(20*R)
        self.GLPTLO.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupPTLO = QtWidgets.QGroupBox(self.PressureTab)
        self.GroupPTLO.setTitle("PT LO INTLCK")
        self.GroupPTLO.setLayout(self.GLPTLO)
        self.GroupPTLO.move(0*R, 0*R)



        self.GLPTHI = QtWidgets.QGridLayout()
        # self.GLPT = QtWidgets.QGridLayout(self)
        self.GLPTHI.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLPTHI.setSpacing(20*R)
        self.GLPTHI.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupPTHI = QtWidgets.QGroupBox(self.PressureTab)
        self.GroupPTHI.setTitle("PT HI INTLCK")
        self.GroupPTHI.setLayout(self.GLPTHI)
        self.GroupPTHI.move(0*R, 200*R)



        self.GLPTHIHI = QtWidgets.QGridLayout()
        # self.GLPT = QtWidgets.QGridLayout(self)
        self.GLPTHIHI.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLPTHIHI.setSpacing(20*R)
        self.GLPTHIHI.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupPTHIHI = QtWidgets.QGroupBox(self.PressureTab)
        self.GroupPTHIHI.setTitle("PT HIHI INTLCK")
        self.GroupPTHIHI.setLayout(self.GLPTHIHI)
        self.GroupPTHIHI.move(0*R, 400*R)


        self.GLOTHER = QtWidgets.QGridLayout()
        self.GLOTHER.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GLOTHER.setSpacing(20 * R)
        self.GLOTHER.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupOTHER = QtWidgets.QGroupBox(self.PressureTab)
        self.GroupOTHER.setTitle("OTHER")
        self.GroupOTHER.setLayout(self.GLOTHER)
        self.GroupOTHER.move(0 * R, 600 * R)

        self.GLTTLO = QtWidgets.QGridLayout()
        self.GLTTLO.setContentsMargins(20*R, 20*R, 20*R, 20*R)
        self.GLTTLO.setSpacing(20*R)
        self.GLTTLO.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupTTLO = QtWidgets.QGroupBox(self.RTDSET1Tab)
        self.GroupTTLO.setTitle("RTD LO INTLCK")
        self.GroupTTLO.setLayout(self.GLTTLO)
        self.GroupTTLO.move(0*R, 0*R)

        self.GLTTHI = QtWidgets.QGridLayout()
        self.GLTTHI.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GLTTHI.setSpacing(20 * R)
        self.GLTTHI.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupTTHI = QtWidgets.QGroupBox(self.RTDSET1Tab)
        self.GroupTTHI.setTitle("RTD HI INTLCK")
        self.GroupTTHI.setLayout(self.GLTTHI)
        self.GroupTTHI.move(0 * R, 200 * R)

        self.GLTTHIHI = QtWidgets.QGridLayout()
        self.GLTTHIHI.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GLTTHIHI.setSpacing(20 * R)
        self.GLTTHIHI.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupTTHIHI = QtWidgets.QGroupBox(self.RTDSET1Tab)
        self.GroupTTHIHI.setTitle("RTD HIHI INTLCK")
        self.GroupTTHIHI.setLayout(self.GLTTHIHI)
        self.GroupTTHIHI.move(0 * R, 600 * R)


        #
        self.PT4306_LO_INTLK = INTLK_RA_Widget_v2(self.PressureTab)
        self.PT4306_LO_INTLK.Label.setText("PT4306_LO")
        self.PT4306_LO_INTLK.setObjectName("PT4306_LO_INTLK")

        self.PT4306_HI_INTLK = INTLK_RA_Widget_v2(self.PressureTab)
        self.PT4306_HI_INTLK.Label.setText("PT4306_HI")
        self.PT4306_HI_INTLK.setObjectName("PT4306_HI_INTLK")

        self.PT4322_HI_INTLK = INTLK_RA_Widget_v2(self.PressureTab)
        self.PT4322_HI_INTLK.Label.setText("PT4322_HI")
        self.PT4322_HI_INTLK.setObjectName("PT4322_HI_INTLK")

        self.PT4322_HIHI_INTLK = INTLK_LA_Widget_v2(self.PressureTab)
        self.PT4322_HIHI_INTLK.Label.setText("PT4322_HIHI")
        self.PT4322_HIHI_INTLK.setObjectName("PT4322_HIHI_INTLK")

        self.PT4319_HI_INTLK = INTLK_RA_Widget_v2(self.PressureTab)
        self.PT4319_HI_INTLK.Label.setText("PT4319_HI")
        self.PT4319_HI_INTLK.setObjectName("PT4319_HI_INTLK")

        self.PT4319_HIHI_INTLK = INTLK_LA_Widget_v2(self.PressureTab)
        self.PT4319_HIHI_INTLK.Label.setText("PT4319_HIHI")
        self.PT4319_HIHI_INTLK.setObjectName("PT4319_HIHI_INTLK")

        self.PT4325_HI_INTLK = INTLK_RA_Widget_v2(self.PressureTab)
        self.PT4325_HI_INTLK.Label.setText("PT4325_HI")
        self.PT4325_HI_INTLK.setObjectName("PT4325_HI_INTLK")

        self.PT4325_HIHI_INTLK = INTLK_LA_Widget_v2(self.PressureTab)
        self.PT4325_HIHI_INTLK.Label.setText("PT4325_HIHI")
        self.PT4325_HIHI_INTLK.setObjectName("PT4325_HIHI_INTLK")

        self.TS1_INTLK = INTLK_LD_Widget_v2(self.PressureTab)
        self.TS1_INTLK.Label.setText("TS1")
        self.TS1_INTLK.setObjectName("TS1")

        self.ES3347_INTLK = INTLK_RD_Widget_v2(self.PressureTab)
        self.ES3347_INTLK.Label.setText("ES3347")
        self.ES3347_INTLK.setObjectName("ES3347")

        self.PUMP3305_OL_INTLK = INTLK_LD_Widget_v2(self.PressureTab)
        self.PUMP3305_OL_INTLK.Label.setText("PUMP3305_OL")
        self.PUMP3305_OL_INTLK.setObjectName("PUMP3305_OL")

        self.TS2_INTLK = INTLK_LD_Widget_v2(self.PressureTab)
        self.TS2_INTLK.Label.setText("TS2")
        self.TS2_INTLK.setObjectName("TS2")

        self.TS3_INTLK = INTLK_LD_Widget_v2(self.PressureTab)
        self.TS3_INTLK.Label.setText("TS3")
        self.TS3_INTLK.setObjectName("TS3")

        self.PU_PRIME_INTLK = INTLK_LD_Widget_v2(self.PressureTab)
        self.PU_PRIME_INTLK.Label.setText("PU_PRIME")
        self.PU_PRIME_INTLK.setObjectName("PU_PRIME")

        #

        self.TT2118_HI_INTLK = INTLK_LA_Widget_v2(self.RTDSET1Tab)
        self.TT2118_HI_INTLK.Label.setText("TT2118_HI")

        self.TT2118_LO_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT2118_LO_INTLK.Label.setText("TT2118_LO")

        self.TT6203_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6203_HI_INTLK.Label.setText("TT6203_HI")

        self.TT6207_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6207_HI_INTLK.Label.setText("TT6207_HI")

        self.TT6211_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6211_HI_INTLK.Label.setText("TT6211_HI")

        self.TT6213_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6213_HI_INTLK.Label.setText("TT6213_HI")

        self.TT6222_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6222_HI_INTLK.Label.setText("TT6222_HI")

        self.TT6407_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6407_HI_INTLK.Label.setText("TT6407_HI")

        self.TT6408_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6408_HI_INTLK.Label.setText("TT6408_HI")

        self.TT6409_HI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6409_HI_INTLK.Label.setText("TT6409_HI")

        self.TT6203_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6203_HIHI_INTLK.Label.setText("TT6203_HIHI")

        self.TT6207_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6207_HIHI_INTLK.Label.setText("TT6207_HIHI")

        self.TT6211_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6211_HIHI_INTLK.Label.setText("TT6211_HIHI")

        self.TT6213_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6213_HIHI_INTLK.Label.setText("TT6213_HIHI")

        self.TT6222_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6222_HIHI_INTLK.Label.setText("TT6222_HIHI")

        self.TT6407_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6407_HIHI_INTLK.Label.setText("TT6407_HIHI")

        self.TT6408_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6408_HIHI_INTLK.Label.setText("TT6408_HIHI")

        self.TT6409_HIHI_INTLK = INTLK_RA_Widget_v2(self.RTDSET1Tab)
        self.TT6409_HIHI_INTLK.Label.setText("TT6409_HIHI")



        # make a directory for the alarm instrument and assign instrument to certain position
        #IF you change the dimenstion of the following matrixes, don't forget to change TempMatrix in the Reassign function
        self.PTLOdir = {0: {0: self.PT4306_LO_INTLK}}

        self.PTHIdir = {0: {0: self.PT4306_HI_INTLK, 1: self.PT4322_HI_INTLK, 2: self.PT4319_HI_INTLK, 3: self.PT4325_HI_INTLK}}

        self.PTHIHIdir = {
            0: {0: self.PT4322_HIHI_INTLK, 1: self.PT4319_HIHI_INTLK, 2: self.PT4325_HIHI_INTLK}}

        self.OTHERdir = {0: {0: self.TS1_INTLK, 1: self.TS2_INTLK, 2: self.TS3_INTLK, 3: self.ES3347_INTLK, 4: self.PUMP3305_OL_INTLK},
                           1: {0: self.PU_PRIME_INTLK}}

        self.TTLOdir = {0: {0: self.TT2118_LO_INTLK}}

        self.TTHIdir = {0: {0: self.TT2118_HI_INTLK, 1: self.TT6203_HI_INTLK, 2: self.TT6207_HI_INTLK, 3: self.TT6211_HI_INTLK, 4: self.TT6213_HI_INTLK},
                           1: {0: self.TT6222_HI_INTLK, 1: self.TT6407_HI_INTLK, 2: self.TT6408_HI_INTLK, 3: self.TT6409_HI_INTLK}}

        self.TTHIHIdir = {0: {0: self.TT6203_HIHI_INTLK, 1: self.TT6207_HIHI_INTLK, 2: self.TT6211_HIHI_INTLK, 3: self.TT6213_HIHI_INTLK, 4: self.TT6222_HIHI_INTLK},
                        1: { 0: self.TT6407_HIHI_INTLK, 1: self.TT6408_HIHI_INTLK, 2: self.TT6409_HIHI_INTLK}}



        # variables usable for building widgets
        # i is row number, j is column number
        # RTD1 is for temperature transducer while PT is for pressure transducer
        # max is max row and column number
        # last is the last widget's row and column index in gridbox
        self.i_PTLO_max = len(self.PTLOdir)
        # which is 2
        self.j_PTLO_max = len(self.PTLOdir[0])
        # which is 5

        self.i_PTHI_max = len(self.PTHIdir)
        # which is 4
        self.j_PTHI_max = len(self.PTHIdir[0])

        self.i_PTHIHI_max = len(self.PTHIHIdir)
        # which is 4
        self.j_PTHIHI_max = len(self.PTHIHIdir[0])

        self.i_OTHER_max = len(self.OTHERdir)
        # which is 4
        self.j_OTHER_max = len(self.OTHERdir[0])

        self.i_TTLO_max = len(self.TTLOdir)
        # which is 2
        self.j_TTLO_max = len(self.TTLOdir[0])
        # which is 5

        self.i_TTHI_max = len(self.TTHIdir)
        # which is 4
        self.j_TTHI_max = len(self.TTHIdir[0])

        self.i_TTHIHI_max = len(self.TTHIHIdir)
        # which is 4
        self.j_TTHIHI_max = len(self.TTHIHIdir[0])

        self.i_PTLO_last = len(self.PTLOdir) - 1
        # which is 1
        self.j_PTLO_last = len(self.PTLOdir[self.i_PTLO_last]) - 1
        # which is 4
        self.i_PTHI_last = len(self.PTHIdir) - 1
        self.j_PTHI_last = len(self.PTHIdir[self.i_PTHI_last]) - 1
        self.i_PTHIHI_last = len(self.PTHIHIdir) - 1
        self.j_PTHIHI_last = len(self.PTHIHIdir[self.i_PTHIHI_last]) - 1

        self.i_OTHER_last = len(self.OTHERdir) - 1
        self.j_OTHER_last = len(self.OTHERdir[self.i_OTHER_last]) - 1

        self.i_TTLO_last = len(self.TTLOdir) - 1
        # which is 1
        self.j_TTLO_last = len(self.TTLOdir[self.i_TTLO_last]) - 1
        # which is 4
        self.i_TTHI_last = len(self.TTHIdir) - 1
        self.j_TTHI_last = len(self.TTHIdir[self.i_TTHI_last]) - 1
        self.i_TTHIHI_last = len(self.TTHIHIdir) - 1
        self.j_TTHIHI_last = len(self.TTHIHIdir[self.i_TTHIHI_last]) - 1

        # which is 1
        self.ResetOrder()

    @QtCore.Slot()
    def ResetOrder(self):
        for i in range(0, self.i_PTLO_max):
            for j in range(0, self.j_PTLO_max):
                self.GLPTLO.addWidget(self.PTLOdir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_PTLO_last, self.j_PTLO_last):
                    break
            if (i, j) == (self.i_PTLO_last, self.j_PTLO_last):
                break

        for i in range(0, self.i_PTHI_max):
            for j in range(0, self.j_PTHI_max):
                self.GLPTHI.addWidget(self.PTHIdir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_PTHI_last, self.j_PTHI_last):
                    break
            if (i, j) == (self.i_PTHI_last, self.j_PTHI_last):
                break

        for i in range(0, self.i_PTHIHI_max):
            for j in range(0, self.j_PTHIHI_max):
                self.GLPTHIHI.addWidget(self.PTHIHIdir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_PTHIHI_last, self.j_PTHIHI_last):
                    break
            if (i, j) == (self.i_PTHIHI_last, self.j_PTHIHI_last):
                break

        for i in range(0, self.i_OTHER_max):
            for j in range(0, self.j_OTHER_max):
                self.GLOTHER.addWidget(self.OTHERdir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_OTHER_last, self.j_OTHER_last):
                    break
            if (i, j) == (self.i_OTHER_last, self.j_OTHER_last):
                break

        for i in range(0, self.i_TTLO_max):
            for j in range(0, self.j_TTLO_max):
                self.GLTTLO.addWidget(self.TTLOdir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_TTLO_last, self.j_TTLO_last):
                    break
            if (i, j) == (self.i_TTLO_last, self.j_TTLO_last):
                break

        for i in range(0, self.i_TTHI_max):
            for j in range(0, self.j_TTHI_max):
                self.GLTTHI.addWidget(self.TTHIdir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_TTHI_last, self.j_TTHI_last):
                    break
            if (i, j) == (self.i_TTHI_last, self.j_TTHI_last):
                break

        for i in range(0, self.i_TTHIHI_max):
            for j in range(0, self.j_TTHIHI_max):
                self.GLTTHIHI.addWidget(self.TTHIHIdir[i][j], i, j)
                # end the position generator when i= last element's row number, j= last element's column number
                if (i, j) == (self.i_TTHIHI_last, self.j_TTHIHI_last):
                    break
            if (i, j) == (self.i_TTHIHI_last, self.j_TTHIHI_last):
                break


# comment the change the widgets' order based on the INTLCK status
    #
    # @QtCore.Slot()
    # def ReassignRTD1Order(self):
    #     # check the status of the Widget and reassign the diretory
    #     # establish 2 diretory, reorder TempDic to reorder the widgets
    #     # k,l are pointers in the TempDic, ij are pointers in TempRefDic
    #     # i_max, j_max are max row and column number
    #     # l max are max column number+1
    #     # i_last,j_last are last elements's diretory coordinate
    #     TempRefRTD1dir = self.AlarmRTD1dir
    #     TempRTD1dir = {0: {0: None, 1: None, 2: None, 3: None, 4: None},
    #                    1: {0: None, 1: None, 2: None, 3: None, 4: None}}
    #
    #     # l_RTD1_max is max number of column
    #     l_RTD1 = 0
    #     k_RTD1 = 0
    #
    #     # i_RTD1_max = 3
    #     # j_RTD1_max = 5
    #     # i_PT_max = 4
    #     # j_PT_max = 5
    #     # l_RTD1_max = 4
    #     # l_PT_max = 4
    #     # i_RTD1_last = 2
    #     # j_RTD1_last = 4
    #     # i_PT_last = 3
    #     # j_PT_last = 1
    #     i_RTD1_max = len(self.AlarmRTD1dir)
    #     # which is 3
    #     j_RTD1_max = len(self.AlarmRTD1dir[0])
    #     # which is 5
    #
    #     i_RTD1_last = len(self.AlarmRTD1dir) - 1
    #     # which is 2
    #     j_RTD1_last = len(self.AlarmRTD1dir[i_RTD1_last]) - 1
    #     # which is 4
    #     # print(i_RTD1_max,j_RTD1_max,i_RTD1_last, j_RTD1_last)
    #
    #     l_RTD1_max = j_RTD1_max - 1
    #
    #     # RTD1 put alarm true widget to the begining of the diretory
    #     for i in range(0, i_RTD1_max):
    #         for j in range(0, j_RTD1_max):
    #             if TempRefRTD1dir[i][j].Alarm:
    #                 TempRTD1dir[k_RTD1][l_RTD1] = TempRefRTD1dir[i][j]
    #                 l_RTD1 = l_RTD1 + 1
    #                 if l_RTD1 == l_RTD1_max + 1:
    #                     l_RTD1 = 0
    #                     k_RTD1 = k_RTD1 + 1
    #             if (i, j) == (i_RTD1_last, j_RTD1_last):
    #                 break
    #         if (i, j) == (i_RTD1_last, j_RTD1_last):
    #             break
    #     # print("1st part")
    #     #
    #     #
    #     # # RTD1 put alarm false widget after that
    #     for i in range(0, i_RTD1_max):
    #         for j in range(0, j_RTD1_max):
    #             if not TempRefRTD1dir[i][j].Alarm:
    #                 TempRTD1dir[k_RTD1][l_RTD1] = TempRefRTD1dir[i][j]
    #                 l_RTD1 = l_RTD1 + 1
    #                 if l_RTD1 == l_RTD1_max + 1:
    #                     l_RTD1 = 0
    #                     k_RTD1 = k_RTD1 + 1
    #             if (i, j) == (i_RTD1_last, j_RTD1_last):
    #                 break
    #         if (i, j) == (i_RTD1_last, j_RTD1_last):
    #             break
    #     # print("2nd part")
    #     # Reassign position
    #     # end the position generator when i= last element's row number, j= last element's column number
    #     for i in range(0, i_RTD1_max):
    #         for j in range(0, j_RTD1_max):
    #             self.GLRTD1.addWidget(TempRTD1dir[i][j], i, j)
    #             if (i, j) == (i_RTD1_last, j_RTD1_last):
    #                 break
    #         if (i, j) == (i_RTD1_last, j_RTD1_last):
    #             break
    #     # print("3rd part")
    #
    #
    # @QtCore.Slot()
    # def ReassignPTOrder(self):
    #     # check the status of the Widget and reassign the diretory
    #     # establish 2 diretory, reorder TempDic to reorder the widgets
    #     # k,l are pointers in the TempDic, ij are pointers in TempRefDic
    #     # i_max, j_max are max row and column number
    #     # l max are max column number+1
    #     # i_last,j_last are last elements's diretory coordinate
    #
    #     TempRefPTdir = self.AlarmPTdir
    #
    #     TempPTdir = {0: {0: None, 1: None, 2: None, 3: None, 4: None},
    #                  1: {0: None, 1: None, 2: None, 3: None, 4: None},
    #                  2: {0: None, 1: None, 2: None, 3: None, 4: None},
    #                  3: {0: None, 1: None, 2: None}}
    #     # l_RTD1_max is max number of column
    #
    #     l_PT = 0
    #     k_PT = 0
    #     # i_RTD1_max = 3
    #     # j_RTD1_max = 5
    #     # i_PT_max = 4
    #     # j_PT_max = 5
    #     # l_RTD1_max = 4
    #     # l_PT_max = 4
    #     # i_RTD1_last = 2
    #     # j_RTD1_last = 4
    #     # i_PT_last = 3
    #     # j_PT_last = 1
    #
    #     i_PT_max = len(self.AlarmPTdir)
    #     # which is 4
    #     j_PT_max = len(self.AlarmPTdir[0])
    #     # which is 5
    #
    #     i_PT_last = len(self.AlarmPTdir) - 1
    #     # which is 3
    #     j_PT_last = len(self.AlarmPTdir[i_PT_last]) - 1
    #     # which is 1
    #
    #     l_PT_max = j_PT_max - 1
    #
    #     # PT
    #     for i in range(0, i_PT_max):
    #         for j in range(0, j_PT_max):
    #             if TempRefPTdir[i][j].Alarm:
    #                 TempPTdir[k_PT][l_PT] = TempRefPTdir[i][j]
    #                 l_PT = l_PT + 1
    #                 if l_PT == l_PT_max + 1:
    #                     l_PT = 0
    #                     k_PT = k_PT + 1
    #             if (i, j) == (i_PT_last, j_PT_last):
    #                 break
    #         if (i, j) == (i_PT_last, j_PT_last):
    #             break
    #
    #     for i in range(0, i_PT_max):
    #         for j in range(0, j_PT_max):
    #             if not TempRefPTdir[i][j].Alarm:
    #                 TempPTdir[k_PT][l_PT] = TempRefPTdir[i][j]
    #                 l_PT = l_PT + 1
    #                 if l_PT == l_PT_max + 1:
    #                     l_PT = 0
    #                     k_PT = k_PT + 1
    #                 if (i, j) == (i_PT_last, j_PT_last):
    #                     break
    #             if (i, j) == (i_PT_last, j_PT_last):
    #                 break
    #
    #     # Reassign position
    #     # end the position generator when i= last element's row number, j= last element's column number
    #
    #     # end the position generator when i= last element's row number, j= last element's column number
    #     for i in range(0, i_PT_max):
    #         for j in range(0, j_PT_max):
    #             self.GLPT.addWidget(TempPTdir[i][j], i, j)
    #             if (i, j) == (i_PT_last, j_PT_last):
    #                 break
    #         if (i, j) == (i_PT_last, j_PT_last):
    #             break
    #


class HeaterSubWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(1500*R, 600*R)
        self.setMinimumSize(1500*R, 600*R)
        self.setWindowTitle("Detailed Information")

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1500*R, 600*R))

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
        self.GroupRD.move(0 * R, 240 * R)

        self.Label = QtWidgets.QPushButton(self.GroupWR)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        # self.Label.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.GLWR.addWidget(self.Label)

        self.ButtonGroup = ButtonGroup(self.GroupWR)
        self.GLWR.addWidget(self.ButtonGroup)


        self.Mode = DoubleButton(self.GroupWR)
        self.Mode.Label.setText("Mode")
        self.GLWR.addWidget(self.Mode)


        self.LOSP = SetPoint(self.GroupWR)
        self.LOSP.Label.setText("LO SET")
        self.GLWR.addWidget(self.LOSP)

        self.HISP = SetPoint(self.GroupWR)
        self.HISP.Label.setText("HI SET")
        self.GLWR.addWidget(self.HISP)


        self.SP = SetPoint(self.GroupWR)
        self.SP.Label.setText("SetPoint")
        self.GLWR.addWidget(self.SP)

        self.updatebutton = QtWidgets.QPushButton(self.GroupWR)
        self.updatebutton.setText("Update")
        self.updatebutton.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.updatebutton)

        self.Interlock = ColoredStatus(self.GroupRD, mode = 1)
        self.Interlock.Label.setText("INTLCK")
        self.GLRD.addWidget(self.Interlock)

        self.Error = ColoredStatus(self.GroupRD, mode = 1)
        self.Error.Label.setText("ERR")
        self.GLRD.addWidget(self.Error)

        self.MANSP = ColoredStatus(self.GroupRD, mode = 2)
        self.MANSP.Label.setText("MAN")
        self.GLRD.addWidget(self.MANSP)

        self.SAT = ColoredStatus(self.GroupRD, mode = 1)
        self.SAT.Label.setText("SAT")
        self.GLRD.addWidget(self.SAT)

        self.ModeREAD = Indicator(self.GroupRD)
        self.ModeREAD.Label.setText("Mode")
        self.ModeREAD.Field.setText('MODE0')
        self.GLRD.addWidget(self.ModeREAD)

        self.EN = ColoredStatus(self.GroupRD, mode = 4)
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

        self.LOW = Indicator(self.GroupRD)
        self.LOW.Label.setText("LOW")
        self.GLRD.addWidget(self.LOW)

        self.HIGH = Indicator(self.GroupRD)
        self.HIGH.Label.setText("HIGH")
        self.GLRD.addWidget(self.HIGH)


        self.SETSP = Indicator(self.GroupRD)
        self.SETSP.Label.setText("SP")
        self.GLRD.addWidget(self.SETSP)

        self.RTD1 = Indicator(self.GroupRD)
        self.RTD1.Label.setText("RTD1")
        self.GLRD.addWidget(self.RTD1)

        self.RTD2 = Indicator(self.GroupRD)
        self.RTD2.Label.setText("RTD2")
        self.GLRD.addWidget(self.RTD2)



class LOOPPIDSubWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(1500*R, 600*R)
        self.setMinimumSize(1500*R, 600*R)
        self.setWindowTitle("Detailed Information")

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1500*R, 600*R))

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
        self.GroupRD.move(0 * R, 240 * R)

        self.Label = QtWidgets.QPushButton(self.GroupWR)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        # self.Label.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.GLWR.addWidget(self.Label)

        self.ButtonGroup = ButtonGroup(self.GroupWR)
        self.GLWR.addWidget(self.ButtonGroup)


        self.Mode = DoubleButton_s(self.GroupWR)
        self.Mode.Label.setText("Mode")
        self.GLWR.addWidget(self.Mode)


        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")
        self.GLWR.addWidget(self.StatusTransition)


        self.LOSP = SetPoint(self.GroupWR)
        self.LOSP.Label.setText("LO SET")
        self.GLWR.addWidget(self.LOSP)

        self.HISP = SetPoint(self.GroupWR)
        self.HISP.Label.setText("HI SET")
        self.GLWR.addWidget(self.HISP)


        self.SP = SetPoint(self.GroupWR)
        self.SP.Label.setText("SetPoint")
        self.GLWR.addWidget(self.SP)

        self.updatebutton = QtWidgets.QPushButton(self.GroupWR)
        self.updatebutton.setText("Update")
        self.updatebutton.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.updatebutton)

        self.Interlock = ColoredStatus(self.GroupRD, mode = 1)
        self.Interlock.Label.setText("INTLCK")
        self.GLRD.addWidget(self.Interlock)

        self.Error = ColoredStatus(self.GroupRD, mode = 1)
        self.Error.Label.setText("ERR")
        self.GLRD.addWidget(self.Error)

        self.MANSP = ColoredStatus(self.GroupRD, mode = 2)
        self.MANSP.Label.setText("MAN")
        self.GLRD.addWidget(self.MANSP)

        self.SAT = ColoredStatus(self.GroupRD, mode = 1)
        self.SAT.Label.setText("SAT")
        self.GLRD.addWidget(self.SAT)

        self.ModeREAD = Indicator(self.GroupRD)
        self.ModeREAD.Label.setText("Mode")
        self.ModeREAD.Field.setText('MODE0')
        self.GLRD.addWidget(self.ModeREAD)

        self.EN = ColoredStatus(self.GroupRD, mode = 4)
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

        self.LOW = Indicator(self.GroupRD)
        self.LOW.Label.setText("LOW")
        self.GLRD.addWidget(self.LOW)

        self.HIGH = Indicator(self.GroupRD)
        self.HIGH.Label.setText("HIGH")
        self.GLRD.addWidget(self.HIGH)


        self.SETSP = Indicator(self.GroupRD)
        self.SETSP.Label.setText("SP")
        self.GLRD.addWidget(self.SETSP)

        self.RTD1 = Indicator(self.GroupRD)
        self.RTD1.Label.setText("RTD1")
        self.GLRD.addWidget(self.RTD1)

        self.RTD2 = Indicator(self.GroupRD)
        self.RTD2.Label.setText("RTD2")
        self.GLRD.addWidget(self.RTD2)

    @QtCore.Slot()
    def ButtonTransitionState(self, bool):
        self.StatusTransition.UpdateColor(bool)


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
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 70*R))
        self.setMinimumSize(70*R, 70*R)
        self.setSizePolicy(sizePolicy)

        # link the button to a new window
        self.SubWindow = Window

        # set alarm icon
        if '__file__' in globals():
            self.Path = os.path.dirname(os.path.realpath(__file__))
        else:
            self.Path = os.getcwd()
        self.ImagePath = os.path.join(self.Path, "images")
        self.pixmap = QtGui.QPixmap(os.path.join(self.ImagePath, "alarm_button.png"))
        self.pixmap = self.pixmap.scaledToHeight(70 * R)

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        # self.Button.setText("Button")
        self.Button.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 70*R))
        self.Button.setStyleSheet(
            "QPushButton{" + LABEL_STYLE + BORDER_STYLE + BORDER_RADIUS+"} QWidget[Alarm = true]{ background-color: rgb(255,132,27);} "
                                       "QWidget[Alarm = false]{ background-color: rgb(204,204,204);}")
        self.Button.setIcon(self.pixmap)

        self.Button.setProperty("Alarm", False)
        self.Button.Alarm = False
        self.Button.clicked.connect(self.ButtonClicked)
        self.Collected = False


        # Green vertical



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



# Define an alarm button
class INTLCKButton(QtWidgets.QWidget):
    def __init__(self, Window, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("INTLCKButton")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 70*R))
        self.setMinimumSize(70*R, 70*R)
        self.setSizePolicy(sizePolicy)

        # link the button to a new window
        self.SubWindow = Window
        # set icon
        if '__file__' in globals():
            self.Path = os.path.dirname(os.path.realpath(__file__))
        else:
            self.Path = os.getcwd()
        self.ImagePath = os.path.join(self.Path, "images")
        self.pixmap = QtGui.QPixmap(os.path.join(self.ImagePath, "lock_button.png"))
        self.pixmap = self.pixmap.scaledToHeight(70 * R)



        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 70*R))
        self.Button.setStyleSheet(
            "QWidget{" + LABEL_STYLE +  BORDER_STYLE + BORDER_RADIUS+"} QWidget[Alarm = true]{ background-color: rgb(255,132,27);} "
                                       "QWidget[Alarm = false]{ background-color: rgb(204,204,204);}")
        self.Button.setIcon(self.pixmap)

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



# Defines a reusable layout containing widgets
class LOOPPID_v2(QtWidgets.QWidget):
    def __init__(self, parent=None, title=""):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 350 * R, 50 * R))
        self.setSizePolicy(sizePolicy)


        # self.HL1 = QtWidgets.QHBoxLayout()
        # self.HL1.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)

        self.Label = QtWidgets.QPushButton(self)
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 250 * R, 35 * R))
        self.Label.setMinimumSize(QtCore.QSize(150*R, 30*R))
        self.Label.setProperty("State", False)
        self.Label.setStyleSheet("QPushButton {" + TITLE_STYLE + BORDER_STYLE + "} QWidget[State = true]{" + C_GREEN
                                 + "} QWidget[State = false]{" + C_MEDIUM_GREY + "}")
        # self.HL1.addWidget(self.Label)

        self.Power = Control_v2(self)
        self.Power.Label.setText("Power")
        self.Power.SetUnit(" %")
        self.Power.Max = 100.
        self.Power.Min = 0.
        self.Power.Step = 0.1
        self.Power.Decimals = 1

        self.Tool = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.Tool.setGeometry(QtCore.QRect(0 * R, 0 * R, 30 * R, 30 * R))
        self.Tool.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.Tool.setArrowType(QtCore.Qt.RightArrow)


        self.Tool.setMinimumSize(QtCore.QSize(30 * R, 30 * R))
        self.Tool.setProperty("State", False)
        self.Tool.setStyleSheet("QToolButton { background: transparent}")
        self.Tool.setText("Label")

        self.Tool.setSizePolicy(sizePolicy)
        self.Tool.pressed.connect(self.on_pressed)
        # self.HL1.addWidget(self.Tool)

        # Add a Sub window popped out when click the name
        self.LOOPPIDWindow = LOOPPIDSubWindow(self)
        self.Label.clicked.connect(self.PushButton)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setGeometry(QtCore.QRect(0 * R, 0 * R, 350 * R, 40 * R))
        # self.content_area.setMinimumSize()
        # self.content_area.setSizePolicy(
        #     QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        # )
        self.content_area.setSizePolicy(sizePolicy)
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.content_area.setStyleSheet("QWidget { background: transparent; }")

        lay = QtWidgets.QGridLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.Label, 0,0,1,4)
        lay.addWidget(self.Power,0,4,1,1)
        lay.addWidget(self.Tool,0,5,1,1)
        # lay.addWidget(self.Tool)
        lay.addWidget(self.content_area,1,0,1,5)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

        self.lay = QtWidgets.QHBoxLayout()

        self.State = DoubleButton_s(self)
        self.State.Label.setText("State")
        self.State.LButton.setText("On")
        self.State.RButton.setText("Off")



        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")

        self.lay.addWidget(self.State)
        self.lay.addWidget(self.StatusTransition)

        self.setContentLayout(self.lay)

    @QtCore.Slot()
    def on_pressed(self):
        checked = self.Tool.isChecked()
        self.Tool.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        # But the -8 make the whole thing work
        collapsed_height = (
                self.sizeHint().height() - self.content_area.maximumHeight()
        )
        # print("height",collapsed_height, self.sizeHint().height(),self.content_area.maximumHeight())
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

    # Neutral means that the button shouldn't show any color

    @QtCore.Slot()
    def ButtonLTransitionState(self, bool):
        if self.StateLState == self.StateInactiveName and self.StateRState == self.StateActiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonRTransitionState(self, bool):
        if self.StateLState == self.StateActiveName and self.StateRState == self.StateInactiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonTransitionState(self, bool):
        self.StatusTransition.UpdateColor(bool)

    @QtCore.Slot()
    def ColorLabel(self, bool):
        self.Label.setProperty("State", bool)
        self.Label.setStyle(self.Tool.style())

    @QtCore.Slot()
    def PushButton(self):
        self.LOOPPIDWindow.show()
        self.InitWindow()

    @QtCore.Slot()
    def InitWindow(self):
        self.LOOPPIDWindow.SP.SetValue(self.LOOPPIDWindow.SETSP.value)
        self.LOOPPIDWindow.LOSP.SetValue(self.LOOPPIDWindow.LOW.value)
        self.LOOPPIDWindow.HISP.SetValue(self.LOOPPIDWindow.HIGH.value)



# Defines a reusable layout containing widgets
class LOOP2PT_v2(QtWidgets.QWidget):
    def __init__(self, parent=None, title=""):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 300 * R, 35 * R))
        self.setSizePolicy(sizePolicy)


        # self.HL1 = QtWidgets.QHBoxLayout()
        # self.HL1.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)

        self.Label = QtWidgets.QPushButton(self)
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 300 * R, 35 * R))
        self.Label.setMinimumSize(QtCore.QSize(150*R, 30*R))
        self.Label.setProperty("State", False)
        self.Label.setStyleSheet("QPushButton {" + TITLE_STYLE + BORDER_STYLE + "} QWidget[State = true]{" + C_GREEN
                                 + "} QWidget[State = false]{" + C_MEDIUM_GREY + "}")
        # self.HL1.addWidget(self.Label)

        self.Tool = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.Tool.setGeometry(QtCore.QRect(0 * R, 0 * R, 30 * R, 30 * R))
        self.Tool.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.Tool.setArrowType(QtCore.Qt.RightArrow)


        self.Tool.setMinimumSize(QtCore.QSize(30 * R, 30 * R))
        self.Tool.setProperty("State", False)
        self.Tool.setStyleSheet("QToolButton { background: transparent}")
        self.Tool.setText("Label")

        self.Tool.setSizePolicy(sizePolicy)
        self.Tool.pressed.connect(self.on_pressed)
        # self.HL1.addWidget(self.Tool)

        # Add a Sub window popped out when click the name
        self.LOOP2PTWindow = LOOP2PTSubWindow_v2(self)
        self.Label.clicked.connect(self.PushButton)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setGeometry(QtCore.QRect(0 * R, 0 * R, 300 * R, 40 * R))
        # self.content_area.setMinimumSize()
        # self.content_area.setSizePolicy(
        #     QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        # )
        self.content_area.setSizePolicy(sizePolicy)
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.content_area.setStyleSheet("QWidget { background: transparent; }")

        lay = QtWidgets.QGridLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.Label, 0,0,1,4)
        lay.addWidget(self.Tool,0,4,1,1)
        # lay.addWidget(self.Tool)
        lay.addWidget(self.content_area,1,0,1,5)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

        self.lay = QtWidgets.QHBoxLayout()

        self.State = DoubleButton_s(self)
        self.State.Label.setText("State")
        self.State.LButton.setText("On")
        self.State.RButton.setText("Off")
        #
        # self.Power = Control(self)
        # self.Power.Label.setText("Power")
        # self.Power.SetUnit(" %")
        # self.Power.Max = 100.
        # self.Power.Min = 0.
        # self.Power.Step = 0.1
        # self.Power.Decimals = 1

        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")

        self.lay.addWidget(self.State)
        self.lay.addWidget(self.StatusTransition)
        # self.lay.addWidget(self.Power)

        self.setContentLayout(self.lay)

    @QtCore.Slot()
    def on_pressed(self):
        checked = self.Tool.isChecked()
        self.Tool.setArrowType(
            QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        # But the -8 make the whole thing work
        collapsed_height = (
                self.sizeHint().height() - self.content_area.maximumHeight()
        )-10*R
        # print("height",collapsed_height, self.sizeHint().height(),self.content_area.maximumHeight())
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

    # Neutral means that the button shouldn't show any color

    @QtCore.Slot()
    def ButtonLTransitionState(self, bool):
        if self.StateLState == self.StateInactiveName and self.StateRState == self.StateActiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonRTransitionState(self, bool):
        if self.StateLState == self.StateActiveName and self.StateRState == self.StateInactiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonTransitionState(self, bool):
        self.StatusTransition.UpdateColor(bool)

    @QtCore.Slot()
    def ColorLabel(self, bool):
        self.Label.setProperty("State", bool)
        self.Label.setStyle(self.Tool.style())

    @QtCore.Slot()
    def PushButton(self):
        self.LOOP2PTWindow.show()
        self.InitWindow()

    @QtCore.Slot()
    def InitWindow(self):
        self.LOOP2PTWindow.SP.SetValue(self.LOOP2PTWindow.SETSP.value)


# Defines a reusable layout containing widgets
class LOOP2PTSubWindow_v2(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(1500*R, 600*R)
        self.setMinimumSize(1500*R, 600*R)
        self.setWindowTitle("Detailed Information")

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1500*R, 600*R))

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
        self.GroupRD.move(0 * R, 240 * R)

        self.Label = QtWidgets.QPushButton(self.GroupWR)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        # self.Label.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.GLWR.addWidget(self.Label)

        self.ButtonGroup = ButtonGroup(self.GroupWR)
        self.GLWR.addWidget(self.ButtonGroup)

        self.Mode = DoubleButton_s(self.GroupWR)
        self.Mode.Label.setText("Mode")
        self.GLWR.addWidget(self.Mode)

        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")
        self.GLWR.addWidget(self.StatusTransition)

        self.SP = SetPoint(self.GroupWR)
        self.SP.Label.setText("SetPoint")
        self.GLWR.addWidget(self.SP)

        self.updatebutton = QtWidgets.QPushButton(self.GroupWR)
        self.updatebutton.setText("Update")
        self.updatebutton.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.updatebutton)

        self.Interlock = ColoredStatus(self.GroupRD, mode = 1)
        self.Interlock.Label.setText("INTLCK")
        self.GLRD.addWidget(self.Interlock)

        self.Error = ColoredStatus(self.GroupRD, mode = 1)
        self.Error.Label.setText("ERR")
        self.GLRD.addWidget(self.Error)

        self.MANSP = ColoredStatus(self.GroupRD, mode = 2)
        self.MANSP.Label.setText("MAN")
        self.GLRD.addWidget(self.MANSP)

        self.ModeREAD = Indicator(self.GroupRD)
        self.ModeREAD.Label.setText("Mode")
        self.ModeREAD.Field.setText('MODE0')
        self.GLRD.addWidget(self.ModeREAD)

        self.SETSP = Indicator(self.GroupRD)
        self.SETSP.Label.setText("SP")
        self.GLRD.addWidget(self.SETSP)



# Defines a reusable layout containing widgets
class LOOP2PT(QtWidgets.QWidget):
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
        self.LOOP2PTSubWindow = LOOP2PTSubWindow(self)
        self.Label.clicked.connect(self.PushButton)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.addLayout(self.HL)

        self.State = DoubleButton(self)
        self.State.Label.setText("State")
        self.State.LButton.setText("OPEN")
        self.State.RButton.setText("CLOSE")
        self.HL.addWidget(self.State)

    def PushButton(self):
        self.LOOP2PTSubWindow.show()


# Defines a reusable layout containing widgets
class LOOP2PTSubWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(1500*R, 600*R)
        self.setMinimumSize(1500*R, 600*R)
        self.setWindowTitle("Detailed Information")

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1500*R, 600*R))

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
        self.GroupRD.move(0 * R, 240 * R)

        self.Label = QtWidgets.QPushButton(self.GroupWR)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        # self.Label.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.GLWR.addWidget(self.Label)

        self.ButtonGroup = ButtonGroup(self.GroupWR)
        self.GLWR.addWidget(self.ButtonGroup)

        self.Mode = DoubleButton(self.GroupWR)
        self.Mode.Label.setText("Mode")
        self.GLWR.addWidget(self.Mode)

        self.SP = SetPoint(self.GroupWR)
        self.SP.Label.setText("SetPoint")
        self.GLWR.addWidget(self.SP)

        self.updatebutton = QtWidgets.QPushButton(self.GroupWR)
        self.updatebutton.setText("Update")
        self.updatebutton.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.updatebutton)

        self.Interlock = ColoredStatus(self.GroupRD, mode = 1)
        self.Interlock.Label.setText("INTLCK")
        self.GLRD.addWidget(self.Interlock)

        self.Error = ColoredStatus(self.GroupRD, mode = 1)
        self.Error.Label.setText("ERR")
        self.GLRD.addWidget(self.Error)

        self.MANSP = ColoredStatus(self.GroupRD, mode = 2)
        self.MANSP.Label.setText("MAN")
        self.GLRD.addWidget(self.MANSP)

        self.ModeREAD = Indicator(self.GroupRD)
        self.ModeREAD.Label.setText("Mode")
        self.ModeREAD.Field.setText('MODE0')
        self.GLRD.addWidget(self.ModeREAD)

        self.SETSP = Indicator(self.GroupRD)
        self.SETSP.Label.setText("SP")
        self.GLRD.addWidget(self.SETSP)

# Defines a reusable layout containing widget
class Valve(QtWidgets.QWidget):
    def __init__(self, parent=None, mode=4):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.setSpacing(3)

        # self.Label = QtWidgets.QLabel(self)
        # # self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        # self.Label.setMinimumSize(QtCore.QSize(10*R, 10*R))
        # self.Label.setStyleSheet("QLabel {" +TITLE_STYLE + BORDER_STYLE+"}")
        # self.Label.setAlignment(QtCore.Qt.AlignCenter)
        # self.Label.setText("Label")
        # self.VL.addWidget(self.Label)
        #
        # self.HL = QtWidgets.QHBoxLayout()
        # self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        # self.VL.addLayout(self.HL)
        #
        # self.Set = DoubleButton(self)
        # self.Set.Label.setText("Set")
        # self.Set.LButton.setText("open")
        # self.Set.RButton.setText("close")
        # self.HL.addWidget(self.Set)
        #
        # self.ActiveState = ColoredStatus(self, mode)
        # # self.ActiveState = ColorIndicator(self) for test the function
        # self.ActiveState.Label.setText("Status")
        # self.HL.addWidget(self.ActiveState)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        self.VL.addLayout(self.HL)

        self.Label = QtWidgets.QLabel(self)
        # self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 200 * R, 40 * R))
        self.Label.setMinimumSize(QtCore.QSize(10 * R, 10 * R))
        self.Label.setStyleSheet("QLabel {" + TITLE_STYLE + BORDER_STYLE + "}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        # self.Label.setSizePolicy(sizePolicy)
        self.HL.addWidget(self.Label)


        self.Set = DoubleButton(self)
        self.Set.Label.setText("Set")
        self.Set.LButton.setText("open")
        self.Set.RButton.setText("close")
        self.VL.addWidget(self.Set)

        self.ActiveState = ColoredStatus(self, mode)
        # self.ActiveState = ColorIndicator(self) for test the function
        self.ActiveState.Label.setText("Status")
        self.HL.addWidget(self.ActiveState)


class Valve_s(QtWidgets.QWidget):
    def __init__(self, parent=None, mode=4):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 200 * R, 170 * R))
        self.setSizePolicy(sizePolicy)

        # self.VL = QtWidgets.QVBoxLayout(self)
        # self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        # self.VL.setSpacing(3)

        self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        self.GL.setSpacing(3)

        # self.Label = QtWidgets.QLabel(self)
        # # self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        # self.Label.setMinimumSize(QtCore.QSize(10*R, 10*R))
        # self.Label.setStyleSheet("QLabel {" +TITLE_STYLE + BORDER_STYLE+"}")
        # self.Label.setAlignment(QtCore.Qt.AlignCenter)
        # self.Label.setText("Label")
        # self.VL.addWidget(self.Label)
        #
        # self.HL = QtWidgets.QHBoxLayout()
        # self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        # self.VL.addLayout(self.HL)
        #
        # self.Set = DoubleButton(self)
        # self.Set.Label.setText("Set")
        # self.Set.LButton.setText("open")
        # self.Set.RButton.setText("close")
        # self.HL.addWidget(self.Set)
        #
        # self.ActiveState = ColoredStatus(self, mode)
        # # self.ActiveState = ColorIndicator(self) for test the function
        # self.ActiveState.Label.setText("Status")
        # self.HL.addWidget(self.ActiveState)

        # self.HL = QtWidgets.QHBoxLayout()
        # self.HL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        # self.VL.addLayout(self.HL)

        self.Label = QtWidgets.QLabel(self)
        # self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 200 * R, 40 * R))
        self.Label.setSizePolicy(sizePolicy)
        self.Label.setMinimumSize(QtCore.QSize(140 * R, 40 * R))
        self.Label.setProperty("State", False)
        self.Label.setStyleSheet("QLabel {" + TITLE_STYLE + BORDER_STYLE +"} QWidget[State = true]{" + C_GREEN
        + "} QWidget[State = false]{" + C_MEDIUM_GREY + "}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        # self.Label.setSizePolicy(sizePolicy)
        self.GL.addWidget(self.Label,0,0,1,2,QtCore.Qt.AlignRight)


        # self.Set = DoubleButton_s(self)
        # self.Set.Label.setText("Set")
        # self.Set.LButton.setText("open")
        # self.Set.RButton.setText("close")
        # self.VL.addWidget(self.Set)

        self.collapse = Valve_CollapsibleBox(self)
        self.GL.addWidget(self.collapse,1,0,1,2,QtCore.Qt.AlignLeft)

    #     self.Activate(True)
    # def Activate(self, Activate):
    #
    #     if Activate:
    #         try:
    #             # Don't need this because the button only read feedback from PLC
    #             # self.LButton.clicked.connect(self.ButtonLClicked)
    #             # self.RButton.clicked.connect(self.ButtonRClicked)
    #             # print(1)
    #             pass
    #             # self.Set.LButton.clicked.connect(lambda: self.ButtonLTransitionState(True))
    #             # self.Set.RButton.clicked.connect(lambda: self.ButtonRTransitionState(True))
    #         except:
    #
    #             print("Failed to Activate the Doublebutton")
    #             pass
    #     else:
    #         try:
    #             #Don't need this because the button only read feedback from PLC
    #             # self.LButton.clicked.connect(self.ButtonLClicked)
    #             # self.RButton.clicked.connect(self.ButtonRClicked)
    #
    #             # self.LButton.clicked.disconnect(self.ButtonLClicked)
    #             # self.RButton.clicked.disconnect(self.ButtonRClicked)
    #             pass
    #
    #         except:
    #             print("Failed to Deactivate the Doublebutton")
    #
    #             pass


    @QtCore.Slot()
    def ButtonTransitionState(self, bool):
        self.collapse.StatusTransition.UpdateColor(bool)

    @QtCore.Slot()
    def ColorLabel(self, bool):
        self.Label.setProperty("State", bool)
        self.Label.setStyle(self.Label.style())




class Valve_v2(QtWidgets.QWidget):
    def __init__(self,  parent=None, title=""):
        super(Valve_v2, self).__init__(parent)
        # super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 170 * R, 200* R))
        self.setSizePolicy(sizePolicy)
        # self.setSizePolicy(sizePolicy)

        self.Label = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 170 * R, 30 * R))
        self.Label.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)

        self.Label.setMinimumSize(QtCore.QSize(170 * R, 30 * R))
        self.Label.setProperty("State", False)
        self.Label.setStyleSheet("QToolButton {" + TITLE_STYLE + BORDER_STYLE + "} QWidget[State = true]{" + C_GREEN
                                 + "} QWidget[State = false]{" + C_MEDIUM_GREY + "}")
        self.Label.setText("Label")

        self.Label.setSizePolicy(sizePolicy)
        self.Label.pressed.connect(self.on_pressed)


        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setGeometry(QtCore.QRect(0 * R, 0 * R, 170 * R, 100* R))
        # self.content_area.setSizePolicy(
        #     QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        # )
        self.content_area.setSizePolicy(
            sizePolicy
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.content_area.setStyleSheet("QWidget { background: transparent; }")


        lay = QtWidgets.QGridLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.Label,0,0,1,3)
        lay.addWidget(self.content_area,1,0,3,3)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

        self.lay = QtWidgets.QGridLayout()


        self.Set = DoubleButton_s(self)
        self.Set.Label.setText("Set")
        self.Set.LButton.setText("open")
        self.Set.RButton.setText("close")

        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")

        self.ActiveState = ColoredStatus(self, mode=2)
        self.ActiveState.Label.setText("Status")

        self.lay.addWidget(self.Set, 0,0, 1,2, QtCore.Qt.AlignTop)
        self.lay.addWidget(self.StatusTransition, 1,0, QtCore.Qt.AlignRight)
        self.lay.addWidget(self.ActiveState,1,1)

        self.setContentLayout(self.lay)


    @QtCore.Slot()
    def on_pressed(self):
        checked = self.Label.isChecked()
        # self.Label.setArrowType(
        #     QtCore.Qt.RightArrow if not checked else QtCore.Qt.DownArrow
        # )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
            self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)
# Neutral means that the button shouldn't show any color

    @QtCore.Slot()
    def ButtonLTransitionState(self, bool):
        if self.Set.LState == self.Set.InactiveName and self.Set.RState == self.Set.ActiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonRTransitionState(self, bool):
        if self.Set.LState == self.Set.ActiveName and self.Set.RState == self.Set.InactiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonTransitionState(self, bool):
        self.StatusTransition.UpdateColor(bool)

    @QtCore.Slot()
    def ColorLabel(self, bool):
        self.Label.setProperty("State", bool)
        self.Label.setStyle(self.Label.style())




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

class ButtonGroup(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("ButtonGroup")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 150*R))
        self.setMinimumSize(70*R, 150*R)
        self.setSizePolicy(sizePolicy)

        self.Button0 = QtWidgets.QPushButton(self)
        self.Button0.setObjectName("Button0")
        self.Button0.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 30*R))
        self.Button0.setText("Mode0")
        self.Button0.setStyleSheet("QPushButton {" + FONT + "}")

        self.Button1 = QtWidgets.QPushButton(self)
        self.Button1.setObjectName("Button1")
        self.Button1.setGeometry(QtCore.QRect(0 * R, 35 * R, 70 * R, 30 * R))
        self.Button1.setText("Mode1")
        self.Button1.setStyleSheet("QPushButton {" + FONT + "}")

        self.Button2 = QtWidgets.QPushButton(self)
        self.Button2.setObjectName("Button2")
        self.Button2.setGeometry(QtCore.QRect(0 * R, 70 * R, 70 * R, 30 * R))
        self.Button2.setText("Mode2")
        self.Button2.setStyleSheet("QPushButton {" + FONT + "}")

        self.Button3 = QtWidgets.QPushButton(self)
        self.Button3.setObjectName("Button3")
        self.Button3.setGeometry(QtCore.QRect(0 * R, 105 * R, 70 * R, 30 * R))
        self.Button3.setText("Mode3")
        self.Button3.setStyleSheet("QPushButton {" + FONT + "}")

class PnID_Alone(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("PnID_Alone")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.setMinimumSize(70*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Background.setStyleSheet("QLabel {" + C_LIGHT_GREY + BORDER_RADIUS+ "}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("PnID_Alone")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")


class ColoredStatus(QtWidgets.QWidget):
    # Mode number should be set to 0, 1 and 2
    def __init__(self, parent=None, mode=0):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("ColoredStatus")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.setMinimumSize(70*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.Background.setStyleSheet("QLabel {" + C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Field = QtWidgets.QPushButton(self)
        self.Field.setObjectName("color status value")
        self.Field.setGeometry(QtCore.QRect(2.5*R, 20*R, 65*R, 15*R))


        self.Mode = mode
        if self.Mode == 0:
            # mode 0: color is green when active is false and red when active is true
            self.Field.setStyleSheet(
                "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Active = true]{" + C_RED +
                "} QWidget[Active = false]{" + C_GREEN + "}")
            # mode 1: color is grey when active is false and red when active is true
        elif self.Mode == 1:
            self.Field.setStyleSheet(
                "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Active = true]{" + C_RED +
                "} QWidget[Active = false]{" + C_MEDIUM_GREY + "}")
            # mode 2: color is grey when active is false and green when active is true
        elif self.Mode == 2:
            self.Field.setStyleSheet(
                "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Active = true]{" + C_GREEN +
                "} QWidget[Active = false]{" + C_MEDIUM_GREY + "}")
        elif self.Mode == 3:
            # mode 3: color is green when active is false and orange when active is true
            self.Field.setStyleSheet(
                "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Active = true]{" + C_ORANGE +
                "} QWidget[Active = false]{" + C_GREEN + "}")
        elif self.Mode == 4:
            # mode 4: color is green when active is true and red when active is false
            self.Field.setStyleSheet(
                "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Active = true]{" + C_GREEN +
                "} QWidget[Active = false]{" + C_RED + "}")
        elif self.Mode == 5:
            # mode 5: color is grey when active is true and red when active is false
            self.Field.setStyleSheet(
                "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Active = true]{" + C_MEDIUM_GREY +
                "} QWidget[Active = false]{" + C_RED + "}")

        else:
            print("Please set a mode number to class colorstatus widget!")
        self.Field.setProperty("Active", False)
    @QtCore.Slot()
    def UpdateColor(self, active):
        # active should true or false
        if active in [True, "true", 1]:
            self.Field.setProperty("Active", True)
        elif active in [False, "false", 0]:
            self.Field.setProperty("Active", False)
        else:
            print("variable'active' must be either True or False!")
        self.Field.setStyle(self.Field.style())


class ColorIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("ColorIndicator")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.setMinimumSize(70*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_RADIUS+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        # unfinished part of the function, should change color when the reading changes
        # self.Field = QtWidgets.QLineEdit(self)
        # self.Field.setObjectName("value")
        # self.Field.setGeometry(QtCore.QRect(0*R, 20*R, 70*R, 20*R))
        # self.Field.setAlignment(QtCore.Qt.AlignCenter)
        # self.Field.setStyleSheet(
        # "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Alarm = true]{" + C_ORANGE + "}
        # QWidget[Alarm = false]{" + C_MEDIUM_GREY + "}")
        # self.Field.setProperty("Alarm", False)

        # test part.
        self.ColorButton = QtWidgets.QPushButton(self)
        self.ColorButton.setObjectName("ColorButton")
        self.ColorButton.setGeometry(QtCore.QRect(0*R, 20*R, 65*R, 15*R))
        self.ColorButton.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[ColorStyle='0']{" + C_ORANGE +
            "} QWidget[ColorStyle = '1']{" + C_RED + "} QWidget[ColorStyle = '2']{" + C_BLUE + "}")
        self.ColorNumber = 0
        self.ColorButton.clicked.connect(self.ButtonClicked)

    @QtCore.Slot()
    def ButtonClicked(self):
        self.ColorNumber += 1
        self.ColorNumber = self.ColorNumber % 3
        self.ColorButton.setProperty("ColorStyle", str(self.ColorNumber))
        self.ColorButton.setStyle(self.ColorButton.style())

    def setColorNumber(self, number):
        self.ColorNumber = number

    def UpdateColor(self):
        self.ColorButton.setProperty("ColorStyle", str(self.ColorNumber))
        self.ColorButton.setStyle(self.ColorButton.style())


# unfinished part of change button color every 2 seconds
# def ColorNumberLoop(self, loopnumber=10):
#     while loopnumber>1:
#         self.ColorButton.setProperty("ColorStyle", str(self.ColorNumber))
#         self.ColorButton.setStyle(self.ColorButton.style())
#         self.ColorNumber += 1
#         loopnumber -= 1
#         time.sleep(2)
#         self.ColorNumber = self.ColorNumber%3


class SetPoint(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("SetPoint")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.setMinimumSize(70*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("SetPoint")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setValidator(QtGui.QDoubleValidator(-1000,1000,2))
        self.Field.setAlignment(QtCore.Qt.AlignCenter)
        self.Field.setObjectName("setpoint value")
        self.Field.setGeometry(QtCore.QRect(0*R, 20*R, 70*R, 20*R))
        self.Field.setStyleSheet("QLineEdit {"+BORDER_STYLE + C_BLACK + FONT+"}")
        self.Field.editingFinished.connect(self.UpdateValue)
        self.value = 0
        self.Field.setText(str(self.value))
        self.Unit = " "

    def SetValue(self, value):
        self.value = value
        self.Field.setText(format(value, '#.2f') + self.Unit)

    def SetIntValue(self, value):
        self.value = value
        self.Field.setText(str(int(value)) + self.Unit)

    def UpdateValue(self):
        self.value = self.Field.text()



class CheckButton(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("CheckButton")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 200*R, 100*R))
        self.setMinimumSize(200*R, 100*R)
        self.setSizePolicy(sizePolicy)

        self.CheckButton = QtWidgets.QPushButton(self)
        self.CheckButton.setText("Check!")
        self.CheckButton.Alarm = False

    @QtCore.Slot()
    def CollectAlarm(self, *args):
        self.Collected = False
        for i in range(len(args)):
            # calculate collected alarm status
            self.Collected = self.Collected or args[i].Alarm
        self.CheckButton.Alarm = self.Collected


class Loadfile(QtWidgets.QWidget):
    def __init__(self,  parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.loaded_dict ={}
        self.default_dict = copy.copy(sec.DIC_PACK)

        self.setObjectName("LoadFile")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 600*R, 1000*R))
        self.setMinimumSize(600*R, 1000*R)
        self.setSizePolicy(sizePolicy)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.setSpacing(3)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.addLayout(self.HL)

        self.FilePath = QtWidgets.QLineEdit(self)
        self.FilePath.setGeometry(QtCore.QRect(0*R, 0*R, 400*R, 50*R))
        self.HL.addWidget(self.FilePath)

        self.LoadPathButton = QtWidgets.QPushButton(self)
        self.LoadPathButton.clicked.connect(self.LoadcsvPath)
        self.LoadPathButton.setText("LoadPath")
        self.LoadPathButton.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.LoadPathButton.setFixedSize(100*R, 50*R)
        self.HL.addWidget(self.LoadPathButton)

        self.LoadFileButton = QtWidgets.QPushButton(self)
        self.LoadFileButton.setFixedSize(100*R, 50*R)
        self.LoadFileButton.setText("Read")
        self.LoadFileButton.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.HL.addWidget(self.LoadFileButton)

        self.FileContent = QtWidgets.QTextEdit(self)
        self.FileContent.setReadOnly(True)
        self.FileContent.setStyleSheet("QWidget {" + TITLE_STYLE_1 + "}")
        self.VL.addWidget(self.FileContent)

    def LoadPath(self):
        # set default path to read
        # based on linux
        defaultpath = "/home/hep/.config/sbcconfig/"
        filterset = "*.pkl;;*.*"
        name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', dir=defaultpath, filter=filterset)
        self.FilePath.setText(name[0])

        try:
            print("Read " + str(self.FilePath.text()))

            with open(str(self.FilePath.text()), 'rb') as f:
                self.loaded_dict = pickle.load(f)
                text_TT_FP_HI="TT_FP_HI: "+ str(self.loaded_dict["data"]["TT"]["FP"]["high"])+"\n \n"
                text_TT_BO_HI = "TT_BO_HI: " + str(self.loaded_dict["data"]["TT"]["BO"]["high"]) + "\n \n"
                text_PT_HI = "PT_HI: " + str(self.loaded_dict["data"]["PT"]["high"]) + "\n \n"
                text_REAL_HI = "REAL_HI: " + str(self.loaded_dict["data"]["LEFT_REAL"]["high"]) + "\n \n"

                text_TT_FP_LO = "TT_FP_LO: " + str(self.loaded_dict["data"]["TT"]["FP"]["low"]) + "\n \n"
                text_TT_BO_LO = "TT_BO_LO: " + str(self.loaded_dict["data"]["TT"]["BO"]["low"]) + "\n \n"
                text_PT_LO = "PT_LO: " + str(self.loaded_dict["data"]["PT"]["low"]) + "\n \n"
                text_REAL_LO = "REAL_LO: " + str(self.loaded_dict["data"]["LEFT_REAL"]["low"]) + "\n \n"

                text_TT_FP_Activated = "TT_FP_Activated: " + str(self.loaded_dict["Active"]["TT"]["FP"]) + "\n \n"
                text_TT_BO_Activated = "TT_BO_Activated: " + str(self.loaded_dict["Active"]["TT"]["BO"]) + "\n \n"
                text_PT_Activated_ = "PT_Activated: " + str(self.loaded_dict["Active"]["PT"]) + "\n \n"
                text_REAL_Activated = "REAL_Activated: " + str(self.loaded_dict["Active"]["LEFT_REAL"]) + "\n \n"
                text = text_TT_FP_HI+ text_TT_BO_HI+ text_PT_HI+ text_REAL_HI+ text_TT_FP_LO+ text_TT_BO_LO+ text_PT_LO+ \
                       text_REAL_LO+ text_TT_FP_Activated + text_TT_BO_Activated+ text_PT_Activated_ +text_REAL_Activated
                self.FileContent.setText(text)
        except:
            print("Error! Please type in a valid path")

    def LoadcsvPath(self):
        # set default path to read
        # based on linux
        defaultpath = "/home/hep/.config/sbcconfig/"
        filterset = "*.csv;;*.*"
        name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', dir=defaultpath, filter=filterset)
        self.FilePath.setText(name[0])

        try:
            print("Read " + str(self.FilePath.text()))
            self.fulladdress = str(self.FilePath.text())

            self.read_Info_n_save()
            text = self.df.to_string()

            # print(text)
            self.FileContent.setText(text)
        except:
            print("Error! Please type in a valid path")

    def read_Info_n_save(self):
        self.df = pd.read_csv(self.fulladdress)
        print(self.df.head(5))
        # print(self.df.iloc[0]["High_Limit"],type(self.df.iloc[0]["High_Limit"]))
        self.low_dic = self.translate_csv("Low_Limit")
        self.high_dic = self.translate_csv("High_Limit")
        self.active_dic = self.translate_csv("Active")

        # value low high they share the same key list
        for key in self.default_dict['data']['TT']['FP']['low']:
            self.default_dict['data']['TT']['FP']['low'][key] = self.low_dic[key]
            self.default_dict['data']['TT']['FP']['high'][key] = self.high_dic[key]
            self.default_dict['Active']['TT']['FP'][key] = self.active_dic[key]


        for key in self.default_dict['data']['TT']['BO']['low']:
            self.default_dict['data']['TT']['BO']['low'][key]= self.low_dic[key]
            self.default_dict['data']['TT']['BO']['high'][key] = self.high_dic[key]
            self.default_dict['Active']['TT']['BO'][key] = self.active_dic[key]

        for key in self.default_dict['data']['PT']['low']:
            self.default_dict['data']['PT']['low'][key]= self.low_dic[key]
            self.default_dict['data']['PT']['high'][key] = self.high_dic[key]
            self.default_dict['Active']['PT'][key] = self.active_dic[key]


        for key in self.default_dict['data']['LEFT_REAL']['low']:
            self.default_dict['data']['LEFT_REAL']['low'][key]= self.low_dic[key]
            self.default_dict['data']['LEFT_REAL']['high'][key] = self.high_dic[key]
            self.default_dict['Active']['LEFT_REAL'][key] = self.active_dic[key]


        for key in self.default_dict['data']['Din']['low']:
            self.default_dict['data']['Din']['low'][key]= self.low_dic[key]
            self.default_dict['data']['Din']['high'][key] = self.high_dic[key]
            self.default_dict['Active']['Din'][key] = self.active_dic[key]

        for key in self.default_dict['data']['LOOPPID']['Alarm_LowLimit']:
            self.default_dict['data']['LOOPPID']['Alarm_LowLimit'][key]= self.low_dic[key]
            self.default_dict['data']['LOOPPID']['Alarm_HighLimit'][key] = self.high_dic[key]
            self.default_dict['Active']['LOOPPID'][key] = self.active_dic[key]

        # print("Active",self.active_dic)
        # print(self.default_dict["Active"])


    # csv file will lose the data type of the record, we need to recover those properties
    def translate_csv(self, type="Low_Limit"):
        df = self.df[["Instrument",type]]
        dic = df.set_index('Instrument').T.to_dict('records')[0]

        # print("before",dic)
        for key in dic:
            try:
                dic[key] = float(dic[key])
            except:
                if dic[key] == "FALSE" or dic[key] == "False":
                    dic[key] = False
                elif dic[key] == "TRUE" or dic[key] == "True":
                    dic[key] = True
                else:
                    pass

        # print("after",dic)
        return dic



class CustomSave(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("CustomSave")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 600*R, 1000*R))
        self.setMinimumSize(600*R, 1000*R)
        self.setSizePolicy(sizePolicy)

        self.VL = QtWidgets.QHBoxLayout()
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.setSpacing(3)

        self.FilePath = QtWidgets.QLineEdit(self)
        self.FilePath.setGeometry(QtCore.QRect(0*R, 0*R, 400*R, 50*R))
        self.VL.addWidget(self.FilePath)

        self.LoadPathButton = QtWidgets.QPushButton(self)
        self.LoadPathButton.clicked.connect(self.LoadPath)
        self.LoadPathButton.setText("SetPath")
        self.LoadPathButton.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.LoadPathButton.setFixedSize(100*R, 50*R)
        self.LoadPathButton.move(400*R, 0*R)
        self.VL.addWidget(self.LoadPathButton)

        self.SaveFileButton = QtWidgets.QPushButton(self)
        self.SaveFileButton.setFixedSize(100*R, 50*R)
        self.SaveFileButton.move(500*R, 0*R)
        self.SaveFileButton.setText("Save")
        self.SaveFileButton.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.VL.addWidget(self.SaveFileButton)

        self.Head = None
        self.Tail = None

        self.instrument = []
        self.highlimit = []
        self.lowlimit = []
        self.active = []
        self.dtype = []

    def LoadPath(self):
        # set default path to save
        # based on linux
        defaultpath = "/home/hep/.config/sbcconfig/"
        filterset = "*.csv;;"
        name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', dir=defaultpath, filter=filterset)
        self.FilePath.setText(name[0])
        head_tail = os.path.split(name[0])
        # split path to a local path and the project name for future reference
        self.Head = head_tail[0]
        self.Tail = head_tail[1]
    def SaveConfig(self,config):
        print("config",config)
        try:
            with open(str(self.FilePath.text()), 'wb') as f:
                pickle.dump(config, f)

            print("Save Successfully!")
        except:
            print("Error in writing configuration files. Please check it!")

    def SavecsvConfig(self, dic_c):

        self.instrument = []
        self.highlimit = []
        self.lowlimit = []
        self.active = []
        self.dtype = []

        # lowlimit, high limit and activae share the same keys
        for key in dic_c['data']['TT']['FP']['low']:
            self.instrument.append(key)
            self.lowlimit.append(dic_c['data']['TT']['FP']['low'][key])
            self.highlimit.append(dic_c['data']['TT']['FP']['high'][key])
            self.active.append(dic_c['Active']['TT']['FP'][key])

        for key in dic_c['data']['TT']['BO']['low']:
            self.instrument.append(key)
            self.lowlimit.append(dic_c['data']['TT']['BO']['low'][key])
            self.highlimit.append(dic_c['data']['TT']['BO']['high'][key])
            self.active.append(dic_c['Active']['TT']['BO'][key])

        for key in dic_c['data']['PT']['low']:
            self.instrument.append(key)
            self.lowlimit.append(dic_c['data']['PT']['low'][key])
            self.highlimit.append(dic_c['data']['PT']['high'][key])
            self.active.append(dic_c['Active']['PT'][key])


        for key in dic_c['data']['LEFT_REAL']['low']:
            self.instrument.append(key)
            self.lowlimit.append(dic_c['data']['LEFT_REAL']['low'][key])
            self.highlimit.append(dic_c['data']['LEFT_REAL']['high'][key])
            self.active.append(dic_c['Active']['LEFT_REAL'][key])

        for key in dic_c['data']['LOOPPID']['Alarm_LowLimit']:
            self.instrument.append(key)
            self.lowlimit.append(dic_c['data']['LOOPPID']['Alarm_LowLimit'][key])
            self.highlimit.append(dic_c['data']['LOOPPID']['Alarm_HighLimit'][key])
            self.active.append(dic_c['Active']['LOOPPID'][key])

        for key in dic_c['data']['Din']['low']:
            self.instrument.append(key)
            self.lowlimit.append(dic_c['data']['Din']['low'][key])
            self.highlimit.append(dic_c['data']['Din']['high'][key])
            self.active.append(dic_c['Active']['Din'][key])

        self.init_dic = {"Instrument": self.instrument, "Low_Limit": self.lowlimit, "High_Limit": self.highlimit,
                         "Active": self.active}

        print(type(self.init_dic["Low_Limit"][0]))
        df = pd.DataFrame(self.init_dic)
        # df = pd.DataFrame(columns=["Instrument","LowLimit","HighLimit","Active"])

        df.to_csv(str(self.FilePath.text()), index=False)


class AlarmStatusWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("AlarmStatusWidget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 200 * R, 100 * R))
        self.setMinimumSize(200 * R, 100 * R)
        self.setSizePolicy(sizePolicy)

        self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        self.GL.setSpacing(3)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(10 * R, 10 * R))
        self.Label.setStyleSheet("QLabel {" + TITLE_STYLE + "}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        # self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 150 * R, 60 * R))
        self.Label.setText("Label")
        self.GL.addWidget(self.Label, 0, 0,1,2)


        self.Indicator = Indicator(self)
        self.Indicator.Label.setText("Indicator")

        self.GL.addWidget(self.Indicator,1,0,QtCore.Qt.AlignCenter)


        self.Low_Read = Indicator(self)
        self.Low_Read.Label.setText("Low")

        self.GL.addWidget(self.Low_Read,1,1,QtCore.Qt.AlignCenter)

        self.High_Read = Indicator(self)
        self.High_Read.Label.setText("High")

        self.GL.addWidget(self.High_Read, 1, 2,QtCore.Qt.AlignCenter)

        self.Low_Set = SetPoint(self)
        self.Low_Set.Label.setText("L SET")

        self.GL.addWidget(self.Low_Set,2,0,QtCore.Qt.AlignCenter)

        self.High_Set = SetPoint(self)
        self.High_Set.Label.setText("H SET")

        self.GL.addWidget(self.High_Set,2,1,QtCore.Qt.AlignCenter)

        # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        self.AlarmMode = QtWidgets.QCheckBox(self)
        self.AlarmMode.setText("Active")
        self.GL.addWidget(self.AlarmMode,0,2,QtCore.Qt.AlignCenter)
        self.Alarm = False

        self.updatebutton =  QtWidgets.QPushButton(self)
        self.updatebutton.setText("Update")
        self.GL.addWidget(self.updatebutton,2,2,QtCore.Qt.AlignCenter)



    @QtCore.Slot()
    def CheckAlarm(self):
        if self.AlarmMode.isChecked():
            if int(self.Low_Read.value) > int(self.High_Read.value):
                print("Low limit should be less than high limit!")
            else:
                if int(self.Indicator.value) < int(self.Low_Read.value):
                    self.Indicator.SetAlarm()
                    self.Alarm = True
                    print(str(self.Label.text()) + " reading is lower than the low limit")
                elif int(self.Indicator.value) > int(self.High_Read.value):
                    self.Indicator.SetAlarm()
                    self.Alarm = True
                    print(str(self.Label.text()) + " reading is higher than the high limit")
                else:
                    self.Indicator.ResetAlarm()
                    self.Alarm = False
        else:
            self.Indicator.ResetAlarm()
            self.Alarm = False

    @QtCore.Slot()
    def UpdateAlarm(self,Value):
        if self.AlarmMode.isChecked():
            if Value:
                self.Indicator.SetAlarm()
                self.Alarm = True
            elif not Value:
                self.Indicator.ResetAlarm()
                self.Alarm = False
            else:
                print("Alarm Info Error")

        else:
            self.Indicator.ResetAlarm()
            self.Alarm = False


class INTLK_RA_Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("INTLK_A_Widget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 450 * R, 200 * R))
        self.setMinimumSize(200 * R, 100 * R)
        self.setSizePolicy(sizePolicy)

        self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        self.GL.setSpacing(3)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(10 * R, 10 * R))
        self.Label.setStyleSheet("QLabel {" + TITLE_STYLE + "}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        # self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 150 * R, 60 * R))
        self.Label.setText("Label")
        self.GL.addWidget(self.Label, 0, 0,1,3)

        self.Indicator = ColoredStatus(self, mode= 4)
        self.Indicator.Label.setText("Indicator")
        self.GL.addWidget(self.Indicator,0,3,QtCore.Qt.AlignCenter)

        self.EN = DoubleButton(self)
        self.EN.Label.setText("Low")
        self.EN.Label.setText("Set")
        self.EN.LButton.setText("open")
        self.EN.RButton.setText("close")

        self.GL.addWidget(self.EN,1,0,QtCore.Qt.AlignCenter)

        self.COND = ColoredStatus(self, mode= 4)
        self.COND.Label.setText("COND")

        self.GL.addWidget(self.COND, 1, 2,QtCore.Qt.AlignCenter)

        self.SET_W = SetPoint(self)
        self.SET_W.Label.setText("SET_W")

        self.GL.addWidget(self.SET_W,2,0,QtCore.Qt.AlignCenter)


        self.SET_R = SetPoint(self)
        self.SET_R.Label.setText("SET_R")

        self.GL.addWidget(self.SET_R, 2, 1, QtCore.Qt.AlignCenter)


        # # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        # self.RST = QtWidgets.QPushButton(self)
        # self.RST.setText("Reset")
        # self.GL.addWidget(self.RST,1,3,QtCore.Qt.AlignCenter)


        self.updatebutton =  QtWidgets.QPushButton(self)
        self.updatebutton.setText("Update")
        self.GL.addWidget(self.updatebutton,2,3,QtCore.Qt.AlignCenter)



class INTLK_LA_Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("INTLK_A_Widget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 450 * R, 200 * R))
        self.setMinimumSize(200 * R, 100 * R)
        self.setSizePolicy(sizePolicy)

        self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        self.GL.setSpacing(3)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(10 * R, 10 * R))
        self.Label.setStyleSheet("QLabel {" + TITLE_STYLE + "}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        # self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 150 * R, 60 * R))
        self.Label.setText("Label")
        self.GL.addWidget(self.Label, 0, 0,1,3)

        self.Indicator = ColoredStatus(self, mode= 4)
        self.Indicator.Label.setText("Indicator")
        self.GL.addWidget(self.Indicator,0,3,QtCore.Qt.AlignCenter)

        self.EN = DoubleButton(self)
        self.EN.Label.setText("Low")
        self.EN.Label.setText("Set")
        self.EN.LButton.setText("open")
        self.EN.RButton.setText("close")

        self.GL.addWidget(self.EN,1,0,QtCore.Qt.AlignCenter)

        self.COND = ColoredStatus(self, mode= 4)
        self.COND.Label.setText("COND")

        self.GL.addWidget(self.COND, 1, 2,QtCore.Qt.AlignCenter)

        self.SET_W = SetPoint(self)
        self.SET_W.Label.setText("SET_W")

        self.GL.addWidget(self.SET_W,2,0,QtCore.Qt.AlignCenter)


        self.SET_R = SetPoint(self)
        self.SET_R.Label.setText("SET_R")

        self.GL.addWidget(self.SET_R, 2, 1, QtCore.Qt.AlignCenter)


        # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        self.RST = QtWidgets.QPushButton(self)
        self.RST.setText("Reset")
        self.GL.addWidget(self.RST,1,3,QtCore.Qt.AlignCenter)


        self.updatebutton =  QtWidgets.QPushButton(self)
        self.updatebutton.setText("Update")
        self.GL.addWidget(self.updatebutton,2,3,QtCore.Qt.AlignCenter)


class INTLK_RD_Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("INTLK_A_Widget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 450 * R, 200 * R))
        self.setMinimumSize(200 * R, 100 * R)
        self.setSizePolicy(sizePolicy)

        self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        self.GL.setSpacing(3)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(10 * R, 10 * R))
        self.Label.setStyleSheet("QLabel {" + TITLE_STYLE + "}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        # self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 150 * R, 60 * R))
        self.Label.setText("Label")
        self.GL.addWidget(self.Label, 0, 0,1,3)

        self.Indicator = ColoredStatus(self, mode= 4)
        self.Indicator.Label.setText("Indicator")
        self.GL.addWidget(self.Indicator,0,3,QtCore.Qt.AlignCenter)

        self.EN = DoubleButton(self)
        self.EN.Label.setText("Low")
        self.EN.Label.setText("Set")
        self.EN.LButton.setText("open")
        self.EN.RButton.setText("close")

        self.GL.addWidget(self.EN,1,0,QtCore.Qt.AlignCenter)

        self.COND = ColoredStatus(self, mode= 4)
        self.COND.Label.setText("COND")

        self.GL.addWidget(self.COND, 1, 2,QtCore.Qt.AlignCenter)

        # # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        # self.RST = QtWidgets.QPushButton(self)
        # self.RST.setText("Reset")
        # self.GL.addWidget(self.RST,1,3,QtCore.Qt.AlignCenter)



class INTLK_LD_Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("INTLK_A_Widget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 450 * R, 200 * R))
        self.setMinimumSize(200 * R, 100 * R)
        self.setSizePolicy(sizePolicy)

        self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        self.GL.setSpacing(3)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(10 * R, 10 * R))
        self.Label.setStyleSheet("QLabel {" + TITLE_STYLE + "}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        # self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 150 * R, 60 * R))
        self.Label.setText("Label")
        self.GL.addWidget(self.Label, 0, 0,1,3)

        self.Indicator = ColoredStatus(self, mode= 4)
        self.Indicator.Label.setText("Indicator")
        self.GL.addWidget(self.Indicator,0,3,QtCore.Qt.AlignCenter)

        self.EN = DoubleButton(self)
        self.EN.Label.setText("Low")
        self.EN.Label.setText("Set")
        self.EN.LButton.setText("open")
        self.EN.RButton.setText("close")

        self.GL.addWidget(self.EN,1,0,QtCore.Qt.AlignCenter)

        self.COND = ColoredStatus(self, mode= 4)
        self.COND.Label.setText("COND")

        self.GL.addWidget(self.COND, 1, 2,QtCore.Qt.AlignCenter)

        # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        self.RST = QtWidgets.QPushButton(self)
        self.RST.setText("Reset")
        self.GL.addWidget(self.RST, 1, 3, QtCore.Qt.AlignCenter)


## New version of INTLCK

class INTLK_RA_Widget_v2(QtWidgets.QWidget):
    def __init__(self, parent=None, title=''):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)


        self.setObjectName("INTLK_RA_Widget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 350 * R, 200 * R))
        self.setMinimumSize(200 * R, 100 * R)
        self.setSizePolicy(sizePolicy)

        self.Label = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 250 * R, 30 * R))
        self.Label.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)

        self.Label.setMinimumSize(QtCore.QSize(250 * R, 30 * R))
        self.Label.setProperty("State", False)
        self.Label.setStyleSheet("QToolButton {" + TITLE_STYLE + BORDER_STYLE + "} QWidget[State = true]{" + C_MEDIUM_GREY
                                 + "} QWidget[State = false]{" + C_ORANGE + "}")
        self.Label.setText("Label")

        self.Label.setSizePolicy(sizePolicy)
        self.Label.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setGeometry(QtCore.QRect(0 * R, 0 * R, 350 * R, 100 * R))
        # self.content_area.setSizePolicy(
        #     QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        # )
        self.content_area.setSizePolicy(
            sizePolicy
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.content_area.setStyleSheet("QWidget { background: transparent; }")


        self.Indicator = ColoredStatus(self, mode= 2)
        self.Indicator.Label.setText("ENABLE")

        lay = QtWidgets.QGridLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.Label, 0, 0, 1, 3)
        lay.addWidget(self.Indicator,0,4,1,1)
        lay.addWidget(self.content_area, 1, 0, 2, 5)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

        self.lay = QtWidgets.QGridLayout()

        self.EN = DoubleButton_s(self)
        self.EN.Label.setText("Low")
        self.EN.Label.setText("Set")
        self.EN.LButton.setText("open")
        self.EN.RButton.setText("close")

        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")

        self.COND = ColoredStatus(self, mode=4)
        self.COND.Label.setText("COND")


        self.SET_W = SetPoint(self)
        self.SET_W.Label.setText("SET_W")


        self.SET_R = SetPoint(self)
        self.SET_R.Label.setText("SET_R")


        # # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        # self.RST = QtWidgets.QPushButton(self)
        # self.RST.setText("Reset")
        # self.GL.addWidget(self.RST,1,3,QtCore.Qt.AlignCenter)

        self.updatebutton = QtWidgets.QPushButton(self)
        self.updatebutton.setText("Write")
        self.updatebutton.setStyleSheet("QPushButton {" + TITLE_STYLE + BORDER_STYLE +  "}")


        self.lay.addWidget(self.EN, 0, 0)
        self.lay.addWidget(self.StatusTransition, 0, 4)
        self.lay.addWidget(self.COND, 0,5)
        self.lay.addWidget(self.SET_R, 1, 0)
        self.lay.addWidget(self.SET_W,1,2)
        self.lay.addWidget(self.updatebutton,1,4,1,2)

        self.setContentLayout(self.lay)

    # Neutral means that the button shouldn't show any color



    @QtCore.Slot()
    def on_pressed(self):
        checked = self.Label.isChecked()
        # self.Label.setArrowType(
        #     QtCore.Qt.RightArrow if not checked else QtCore.Qt.DownArrow
        # )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
                self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


    @QtCore.Slot()
    def ButtonLTransitionState(self, bool):
        if self.EN.LState == self.EN.InactiveName and self.EN.RState == self.EN.ActiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonRTransitionState(self, bool):
        if self.EN.LState == self.EN.ActiveName and self.EN.RState == self.EN.InactiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonTransitionState(self, bool):
        self.StatusTransition.UpdateColor(bool)

    @QtCore.Slot()
    def ColorLabel(self, bool):
        self.Label.setProperty("State", bool)
        self.Label.setStyle(self.Label.style())



class INTLK_LA_Widget_v2(QtWidgets.QWidget):
    def __init__(self, parent=None, title=''):
        super().__init__(parent)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("INTLK_LA_Widget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 350 * R, 200 * R))
        self.setMinimumSize(200 * R, 100 * R)
        self.setSizePolicy(sizePolicy)

        self.Label = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 250 * R, 30 * R))
        self.Label.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)

        self.Label.setMinimumSize(QtCore.QSize(250 * R, 30 * R))
        self.Label.setProperty("State", False)
        self.Label.setStyleSheet("QToolButton {" + TITLE_STYLE + BORDER_STYLE + "} QWidget[State = true]{" + C_MEDIUM_GREY
                                 + "} QWidget[State = false]{" + C_ORANGE + "}")
        self.Label.setText("Label")

        self.Label.setSizePolicy(sizePolicy)
        self.Label.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setGeometry(QtCore.QRect(0 * R, 0 * R, 350 * R, 100 * R))
        # self.content_area.setSizePolicy(
        #     QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        # )
        self.content_area.setSizePolicy(
            sizePolicy
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.content_area.setStyleSheet("QWidget { background: transparent; }")

        self.Indicator = ColoredStatus(self, mode=2)
        self.Indicator.Label.setText("ENABLE")

        lay = QtWidgets.QGridLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.Label, 0, 0, 1, 3)
        lay.addWidget(self.Indicator, 0, 4, 1, 1)
        lay.addWidget(self.content_area, 1, 0, 2, 5)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

        self.lay = QtWidgets.QGridLayout()

        self.EN = DoubleButton_s(self)
        self.EN.Label.setText("Low")
        self.EN.Label.setText("Set")
        self.EN.LButton.setText("open")
        self.EN.RButton.setText("close")

        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")

        self.COND = ColoredStatus(self, mode=4)
        self.COND.Label.setText("COND")

        self.SET_W = SetPoint(self)
        self.SET_W.Label.setText("SET_W")

        self.SET_R = SetPoint(self)
        self.SET_R.Label.setText("SET_R")

        # # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        # self.RST = QtWidgets.QPushButton(self)
        # self.RST.setText("Reset")
        # self.GL.addWidget(self.RST,1,3,QtCore.Qt.AlignCenter)


        # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        self.RST = QtWidgets.QPushButton(self)
        self.RST.setText("Reset")
        self.RST.setStyleSheet("QPushButton {" + TITLE_STYLE + BORDER_STYLE + "}")


        self.updatebutton = QtWidgets.QPushButton(self)
        self.updatebutton.setText("Write")
        self.updatebutton.setStyleSheet("QPushButton {" + TITLE_STYLE + BORDER_STYLE + "}")

        self.lay.addWidget(self.EN, 0, 0)
        self.lay.addWidget(self.StatusTransition, 0, 4)
        self.lay.addWidget(self.COND, 0, 5)
        self.lay.addWidget(self.SET_R, 1, 0)
        self.lay.addWidget(self.SET_W, 1, 2)
        self.lay.addWidget(self.RST, 1, 4)
        self.lay.addWidget(self.updatebutton, 1, 5)

        self.setContentLayout(self.lay)

        # Neutral means that the button shouldn't show any color

    @QtCore.Slot()
    def on_pressed(self):
        checked = self.Label.isChecked()
        # self.Label.setArrowType(
        #     QtCore.Qt.RightArrow if not checked else QtCore.Qt.DownArrow
        # )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
                self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

    @QtCore.Slot()
    def ButtonLTransitionState(self, bool):
        if self.EN.LState == self.EN.InactiveName and self.EN.RState == self.EN.ActiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonRTransitionState(self, bool):
        if self.EN.LState == self.EN.ActiveName and self.EN.RState == self.EN.InactiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonTransitionState(self, bool):
        self.StatusTransition.UpdateColor(bool)

    @QtCore.Slot()
    def ColorLabel(self, bool):
        self.Label.setProperty("State", bool)
        self.Label.setStyle(self.Label.style())


class INTLK_RD_Widget_v2(QtWidgets.QWidget):

    def __init__(self, parent=None, title=''):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)


        self.setObjectName("INTLK_RD_Widget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 350 * R, 200 * R))
        self.setMinimumSize(200 * R, 100 * R)
        self.setSizePolicy(sizePolicy)

        self.Label = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 250 * R, 30 * R))
        self.Label.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)

        self.Label.setMinimumSize(QtCore.QSize(250 * R, 30 * R))
        self.Label.setProperty("State", False)
        self.Label.setStyleSheet("QToolButton {" + TITLE_STYLE + BORDER_STYLE + "} QWidget[State = true]{" + C_MEDIUM_GREY
                                 + "} QWidget[State = false]{" + C_ORANGE + "}")
        self.Label.setText("Label")

        self.Label.setSizePolicy(sizePolicy)
        self.Label.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setGeometry(QtCore.QRect(0 * R, 0 * R, 350 * R, 100 * R))
        # self.content_area.setSizePolicy(
        #     QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        # )
        self.content_area.setSizePolicy(
            sizePolicy
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.content_area.setStyleSheet("QWidget { background: transparent; }")


        self.Indicator = ColoredStatus(self, mode= 2)
        self.Indicator.Label.setText("ENABLE")

        lay = QtWidgets.QGridLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.Label, 0, 0, 1, 3)
        lay.addWidget(self.Indicator,0,4,1,1)
        lay.addWidget(self.content_area, 1, 0, 2, 5)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

        self.lay = QtWidgets.QGridLayout()

        self.EN = DoubleButton_s(self)
        self.EN.Label.setText("Low")
        self.EN.Label.setText("Set")
        self.EN.LButton.setText("open")
        self.EN.RButton.setText("close")

        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")

        self.COND = ColoredStatus(self, mode=4)
        self.COND.Label.setText("COND")



        # # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        # self.RST = QtWidgets.QPushButton(self)
        # self.RST.setText("Reset")
        # self.GL.addWidget(self.RST,1,3,QtCore.Qt.AlignCenter)



        self.lay.addWidget(self.EN, 0, 0)
        self.lay.addWidget(self.StatusTransition, 0, 4)
        self.lay.addWidget(self.COND, 0,5)


        self.setContentLayout(self.lay)

    # Neutral means that the button shouldn't show any color



    @QtCore.Slot()
    def on_pressed(self):
        checked = self.Label.isChecked()
        # self.Label.setArrowType(
        #     QtCore.Qt.RightArrow if not checked else QtCore.Qt.DownArrow
        # )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
                self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


    @QtCore.Slot()
    def ButtonLTransitionState(self, bool):
        if self.EN.LState == self.EN.InactiveName and self.EN.RState == self.EN.ActiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonRTransitionState(self, bool):
        if self.EN.LState == self.EN.ActiveName and self.EN.RState == self.EN.InactiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonTransitionState(self, bool):
        self.StatusTransition.UpdateColor(bool)

    @QtCore.Slot()
    def ColorLabel(self, bool):
        self.Label.setProperty("State", bool)
        self.Label.setStyle(self.Label.style())


class INTLK_LD_Widget_v2(QtWidgets.QWidget):
    def __init__(self, parent=None, title=''):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("INTLK_LD_Widget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 350 * R, 200 * R))
        self.setMinimumSize(200 * R, 100 * R)
        self.setSizePolicy(sizePolicy)

        self.Label = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 250 * R, 30 * R))
        self.Label.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)

        self.Label.setMinimumSize(QtCore.QSize(250 * R, 30 * R))
        self.Label.setProperty("State", False)
        self.Label.setStyleSheet(
            "QToolButton {" + TITLE_STYLE + BORDER_STYLE + "} QWidget[State = true]{" + C_MEDIUM_GREY
            + "} QWidget[State = false]{" + C_ORANGE + "}")
        self.Label.setText("Label")

        self.Label.setSizePolicy(sizePolicy)
        self.Label.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setGeometry(QtCore.QRect(0 * R, 0 * R, 350 * R, 100 * R))
        # self.content_area.setSizePolicy(
        #     QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        # )
        self.content_area.setSizePolicy(
            sizePolicy
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.content_area.setStyleSheet("QWidget { background: transparent; }")

        self.Indicator = ColoredStatus(self, mode=2)
        self.Indicator.Label.setText("ENABLE")

        lay = QtWidgets.QGridLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.Label, 0, 0, 1, 3)
        lay.addWidget(self.Indicator, 0, 4, 1, 1)
        lay.addWidget(self.content_area, 1, 0, 2, 5)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumHeight")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumHeight")
        )

        self.lay = QtWidgets.QGridLayout()

        self.EN = DoubleButton_s(self)
        self.EN.Label.setText("Low")
        self.EN.Label.setText("Set")
        self.EN.LButton.setText("open")
        self.EN.RButton.setText("close")

        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")

        self.COND = ColoredStatus(self, mode=4)
        self.COND.Label.setText("COND")

        # # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        # self.RST = QtWidgets.QPushButton(self)
        # self.RST.setText("Reset")
        # self.GL.addWidget(self.RST,1,3,QtCore.Qt.AlignCenter)

        self.RST = QtWidgets.QPushButton(self)
        self.RST.setText("Reset")
        self.RST.setStyleSheet("QPushButton {" + TITLE_STYLE + BORDER_STYLE + "}")

        self.lay.addWidget(self.EN, 0, 0)
        self.lay.addWidget(self.StatusTransition, 0, 4)
        self.lay.addWidget(self.COND, 0, 5)

        self.lay.addWidget(self.RST, 1, 0, 1, 6)

        self.setContentLayout(self.lay)

    # Neutral means that the button shouldn't show any color

    @QtCore.Slot()
    def on_pressed(self):
        checked = self.Label.isChecked()
        # self.Label.setArrowType(
        #     QtCore.Qt.RightArrow if not checked else QtCore.Qt.DownArrow
        # )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = (
                self.sizeHint().height() - self.content_area.maximumHeight()
        )
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)

    @QtCore.Slot()
    def ButtonLTransitionState(self, bool):
        if self.EN.LState == self.EN.InactiveName and self.EN.RState == self.EN.ActiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonRTransitionState(self, bool):
        if self.EN.LState == self.EN.ActiveName and self.EN.RState == self.EN.InactiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonTransitionState(self, bool):
        self.StatusTransition.UpdateColor(bool)

    @QtCore.Slot()
    def ColorLabel(self, bool):
        self.Label.setProperty("State", bool)
        self.Label.setStyle(self.Label.style())


# Defines a reusable layout containing widget
class Flag(QtWidgets.QWidget):
    def __init__(self, parent=None, mode=4):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0*R, 0*R, 0*R, 0*R)
        self.VL.setSpacing(3)


        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0 * R, 0 * R, 0 * R, 0 * R)
        self.VL.addLayout(self.HL)

        self.Label = QtWidgets.QLabel(self)
        # self.Label.setMinimumSize(QtCore.QSize(30*R, 30*R))
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 200 * R, 40 * R))
        self.Label.setMinimumSize(QtCore.QSize(10 * R, 10 * R))
        self.Label.setStyleSheet("QLabel {" + TITLE_STYLE + BORDER_STYLE + "}")
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        # self.Label.setSizePolicy(sizePolicy)
        self.HL.addWidget(self.Label)


        self.Set = DoubleButton(self)
        self.Set.Label.setText("Set")
        self.Set.LButton.setText("open")
        self.Set.RButton.setText("close")
        self.VL.addWidget(self.Set)

        self.INTLK = ColoredStatus(self, mode=mode)
        # self.ActiveState = ColorIndicator(self) for test the function
        self.INTLK.Label.setText("INTLK")
        self.HL.addWidget(self.INTLK)





class BoolIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("BoolIndicator")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.setMinimumSize(70*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_RADIUS+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setObjectName("value")
        self.Field.setGeometry(QtCore.QRect(0*R, 20*R, 70*R, 20*R))
        self.Field.setAlignment(QtCore.Qt.AlignCenter)
        self.Field.setReadOnly(True)
        self.Field.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Alarm = true]{" + C_ORANGE +
            "} QWidget[Alarm = false]{" + C_MEDIUM_GREY + "}")
        self.Field.setProperty("Alarm", False)
        self.SetValue("On")

    def SetValue(self, value):
        self.value = value
        self.Field.setText(str(value))

    def SetAlarm(self):
        self.Field.setProperty("Alarm", True)
        self.Field.setStyle(self.Field.style())

    def ResetAlarm(self):
        self.Field.setProperty("Alarm", False)
        self.Field.setStyle(self.Field.style())


class Indicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("Indicator")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 90*R, 60*R))
        self.setMinimumSize(90*R, 60*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 90*R, 60*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 90*R, 25*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setObjectName("indicator value")
        self.Field.setGeometry(QtCore.QRect(0*R, 25*R, 90*R, 35*R))
        self.Field.setAlignment(QtCore.Qt.AlignCenter)
        self.Field.setReadOnly(True)
        self.Field.setStyleSheet(
            "QLineEdit{" + BORDER_STYLE + C_WHITE + LAG_FONT + "} QLineEdit[Alarm = true]{" + C_ORANGE +
            "} QLineEdit[Alarm = false]{" + C_MEDIUM_GREY + "}")
        self.Field.Property = False
        self.Field.setProperty("Alarm", False)

        self.Unit = " K"
        self.SetValue(0.)

    def SetValue(self, value):
        self.value = value
        self.Field.setText(format(value, '#.2f') + self.Unit)

    def SetIntValue(self, value):
        self.value = value
        self.Field.setText(str(int(value)) + self.Unit)

    def SetAlarm(self):
        self.Field.Property = True
        self.Field.setProperty("Alarm", self.Field.Property)
        self.Field.setStyle(self.Field.style())

    def ResetAlarm(self):
        self.Field.Property = False
        self.Field.setProperty("Alarm", self.Field.Property)
        self.Field.setStyle(self.Field.style())

    def SetUnit(self, unit=" °C"):
        self.Unit = unit
        self.Field.setText(format(self.value, '#.2f') + self.Unit)

    # set alarm mode, if the mode is false, then the alarm will not be triggered despite of alarm value
    def SetAlarmMode(self, Mode):
        self.AlarmMode = Mode

#Indicator with different size
class Indicator_ds(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("Indicator")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 100*R, 60*R))
        self.setMinimumSize(100*R, 60*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 100*R, 60*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 100*R, 25*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setObjectName("indicator value")
        self.Field.setGeometry(QtCore.QRect(0*R, 25*R, 100*R, 35*R))
        self.Field.setAlignment(QtCore.Qt.AlignCenter)
        self.Field.setReadOnly(True)
        self.Field.setStyleSheet(
            "QLineEdit{" + BORDER_STYLE + C_WHITE + LAG_FONT + "} QLineEdit[Alarm = true]{" + C_ORANGE +
            "} QLineEdit[Alarm = false]{" + C_MEDIUM_GREY + "}")
        self.Field.Property = False
        self.Field.setProperty("Alarm", False)

        self.Unit = " K"
        self.SetValue(0.)

    def SetValue(self, value):
        self.value = value
        self.Field.setText(format(value, '#.2f') + self.Unit)

    def SetAlarm(self):
        self.Field.Property = True
        self.Field.setProperty("Alarm", self.Field.Property)
        self.Field.setStyle(self.Field.style())

    def ResetAlarm(self):
        self.Field.Property = False
        self.Field.setProperty("Alarm", self.Field.Property)
        self.Field.setStyle(self.Field.style())

    def SetUnit(self, unit=" °C"):
        self.Unit = unit
        self.Field.setText(format(self.value, '#.2f') + self.Unit)

    # set alarm mode, if the mode is false, then the alarm will not be triggered despite of alarm value
    def SetAlarmMode(self, Mode):
        self.AlarmMode = Mode


class Control(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("Control")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.setMinimumSize(70*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Control")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setGeometry(QtCore.QRect(0*R, 20*R, 70*R, 20*R))
        self.Button.setStyleSheet("QPushButton {" +C_BLUE + C_WHITE + FONT + BORDER_RADIUS+"}")

        self.Unit = " W"
        self.SetValue(0.)

        self.Max = 10.
        self.Min = -10.
        self.Step = 0.1
        self.Decimals = 1

    def SetValue(self, value):
        self.value = value
        self.Button.setText(str(value) + self.Unit)

    def SetUnit(self, unit=" °C"):
        self.Unit = unit
        self.Button.setText(format(self.value, '#.2f') + self.Unit)

    @QtCore.Slot()
    def Changevalue(self):
        Dialog = QtWidgets.QInputDialog()
        Dialog.setInputMode(QtWidgets.QInputDialog.DoubleInput)
        Dialog.setDoubleDecimals(self.Decimals)
        Dialog.setDoubleRange(self.Min, self.Max)
        Dialog.setDoubleStep(self.Step)
        Dialog.setDoublevalue(self.value)
        Dialog.setLabelText("Please entre a new value (min = " + str(self.Min) + ", max = " + str(self.Max) + ")")
        Dialog.setModal(True)
        Dialog.setWindowTitle("Modify value")
        Dialog.exec()
        if Dialog.result():
            self.SetValue(Dialog.doublevalue())
            self.Signals.fSignal.emit(self.value)

    def Activate(self, Activate):
        if Activate:
            try:
                self.Button.clicked.connect(self.Changevalue)
            except:
                pass
        else:
            try:
                self.Button.clicked.disconnect(self.Changevalue)
            except:
                pass



class Control_v2(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("Control")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.setMinimumSize(70*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Control")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setGeometry(QtCore.QRect(0*R, 20*R, 70*R, 20*R))
        self.Button.setProperty("State",True)
        self.Button.setStyleSheet("QPushButton {" +C_BLUE + C_WHITE + FONT + BORDER_RADIUS + "} QWidget[State = true]{" + C_BLUE
                                 + "} QWidget[State = false]{" + C_MEDIUM_GREY + "}")

        self.Unit = " W"
        self.SetValue(0.)

        self.Max = 10.
        self.Min = -10.
        self.Step = 0.1
        self.Decimals = 1

    def SetValue(self, value):
        self.value = value
        self.Button.setText(str(value) + self.Unit)

    def SetUnit(self, unit=" °C"):
        self.Unit = unit
        self.Button.setText(format(self.value, '#.2f') + self.Unit)

    @QtCore.Slot()
    def Changevalue(self):
        Dialog = QtWidgets.QInputDialog()
        Dialog.setInputMode(QtWidgets.QInputDialog.DoubleInput)
        Dialog.setDoubleDecimals(self.Decimals)
        Dialog.setDoubleRange(self.Min, self.Max)
        Dialog.setDoubleStep(self.Step)
        Dialog.setDoublevalue(self.value)
        Dialog.setLabelText("Please entre a new value (min = " + str(self.Min) + ", max = " + str(self.Max) + ")")
        Dialog.setModal(True)
        Dialog.setWindowTitle("Modify value")
        Dialog.exec()
        if Dialog.result():
            self.SetValue(Dialog.doublevalue())
            self.Signals.fSignal.emit(self.value)

    def Activate(self, Activate):
        if Activate:
            try:
                self.Button.clicked.connect(self.Changevalue)
            except:
                pass
        else:
            try:
                self.Button.clicked.disconnect(self.Changevalue)
            except:
                pass

    @QtCore.Slot()
    def ColorButton(self, bool):
        self.Button.setProperty("State", bool)
        self.Button.setStyle(self.Button.style())

class Menu(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("Menu")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 40*R))
        self.setMinimumSize(140*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Menu")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Combobox = QtWidgets.QComboBox(self)
        self.Combobox.setObjectName("Menu")
        self.Combobox.setGeometry(QtCore.QRect(0*R, 20*R, 140*R, 20*R))
        self.Combobox.addItem("0")
        self.Combobox.addItem("1")
        self.Combobox.addItem("2")
        self.Combobox.setStyleSheet("QWidget {" + FONT + "}")


class Toggle(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("Toggle")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.setMinimumSize(70*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Toggle")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setGeometry(QtCore.QRect(0*R, 20*R, 70*R, 20*R))
        self.Button.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[State = true]{" + C_GREEN
            + "} QWidget[State = false]{" + C_RED + "}")
        self.Button.setProperty("State", False)
        self.Button.clicked.connect(self.ButtonClicked)

        self.State = "On"
        self.SetToggleStateNames("On", "Off")
        self.SetState("Off")

    def SetToggleStateNames(self, On, Off):
        self.OnName = On
        self.OffName = Off

    def ToggleState(self):
        if self.State == self.OnName:
            self.Button.setText(self.OffName)
            self.Button.setProperty("State", False)
            self.Button.setStyle(self.Button.style())
            self.State = self.OffName
        else:
            self.Button.setText(self.OnName)
            self.Button.setProperty("State", True)
            self.Button.setStyle(self.Button.style())
            self.State = self.OnName

    def SetState(self, State):
        if self.State != self.OffName and State == self.OffName:
            self.ToggleState()
        elif self.State != self.OnName and State == self.OnName:
            self.ToggleState()

    @QtCore.Slot()
    def ButtonClicked(self):
        self.ToggleState()
        self.Signals.sSignal.emit(self.State)

    def Activate(self, Activate):
        if Activate:
            try:
                self.Button.clicked.connect(self.ButtonClicked)
            except:
                pass
        else:
            try:
                self.Button.clicked.disconnect(self.ButtonClicked)
            except:
                pass


class Position(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("Position")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 250*R))
        self.setMinimumSize(70*R, 250*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 250*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Position")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setObjectName("value")
        self.Field.setGeometry(QtCore.QRect(0*R, 20*R, 70*R, 20*R))
        self.Field.setAlignment(QtCore.Qt.AlignCenter)
        self.Field.setReadOnly(True)
        self.Field.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Alarm = true]{" + C_ORANGE
            + "} QWidget[Alarm = false]{" + C_MEDIUM_GREY + "}")
        self.Field.setProperty("Alarm", False)

        self.Max = QtWidgets.QLabel(self)
        self.Max.setObjectName("Max")
        self.Max.setGeometry(QtCore.QRect(0*R, 43, 40*R, 20*R))
        self.Max.setAlignment(QtCore.Qt.AlignRight)
        self.Max.setStyleSheet("QLabel {" +FONT+"}")

        self.Zero = QtWidgets.QLabel(self)
        self.Zero.setObjectName("Zero")
        self.Zero.setText("0\"")
        self.Zero.setAlignment(QtCore.Qt.AlignRight)
        self.Zero.setStyleSheet("QLabel {" +FONT+"}")

        self.Min = QtWidgets.QLabel(self)
        self.Min.setObjectName("Min")
        self.Min.setGeometry(QtCore.QRect(0*R, 230*R, 40*R, 20*R))
        self.Min.setAlignment(QtCore.Qt.AlignRight)
        self.Min.setStyleSheet("QLabel {" +FONT+"}")

        self.Slider = QtWidgets.QSlider(self)
        self.Slider.setObjectName("Slider")
        self.Slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.Slider.setGeometry(QtCore.QRect(40*R, 45*R, 25*R, 200*R))
        self.Slider.setStyleSheet("QSlider::handle:vertical{background: white; border-radius: 5px;}")
        self.Slider.setEnabled(False)

        self.SetLimits(-.88, 2.35)
        self.SetValue(0.)

    def SetValue(self, value):
        self.value = value
        self.Slider.setSliderPosition(value * 100*R)
        self.Field.setText(format(value, '#.2f') + "\"")

    def SetLimits(self, Min, Max):
        self.Slider.setMaximum(Max * 100*R)
        self.Slider.setMinimum(Min * 100*R)
        self.Max.setText(format(Max, '#.2f') + "\"")
        self.Min.setText(format(Min, '#.2f') + "\"")
        Offset = 43 - ((43 - 230) / (Max - Min)) * Max
        self.Zero.setGeometry(QtCore.QRect(0*R, Offset, 40*R, 20*R))

    def SetAlarm(self):
        self.Field.setProperty("Alarm", True)
        self.Field.setStyle(self.Field.style())

    def ResetAlarm(self):
        self.Field.setProperty("Alarm", False)
        self.Field.setStyle(self.Field.style())


class State(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("State")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 40*R))
        self.setMinimumSize(140*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("State")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setObjectName("state value")
        self.Field.setGeometry(QtCore.QRect(0*R, 20*R, 140*R, 20*R))
        self.Field.setAlignment(QtCore.Qt.AlignCenter)
        self.Field.setReadOnly(True)
        self.Field.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Alarm = true]{" + C_ORANGE
            + "} QWidget[Alarm = false]{" + C_MEDIUM_GREY + "}")
        self.Field.setProperty("Alarm", False)
        self.Field.setText("Emergency")

    def SetAlarm(self):
        self.Field.setProperty("Alarm", True)
        self.Field.setStyle(self.Field.style())

    def ResetAlarm(self):
        self.Field.setProperty("Alarm", False)
        self.Field.setStyle(self.Field.style())


class DoubleButton(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("DoubleButton")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 220*R, 40*R))
        self.setMinimumSize(220*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Double button")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.LButton = QtWidgets.QPushButton(self)
        self.LButton.setObjectName("LButton")
        self.LButton.setText("On")
        self.LButton.setGeometry(QtCore.QRect(2.5*R, 20*R, 65*R, 15*R))
        self.LButton.setProperty("State", True)
        self.LButton.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[State = true]{" + C_GREEN
            + "} QWidget[State = false]{" + C_MEDIUM_GREY + "}")


        self.RButton = QtWidgets.QPushButton(self)
        self.RButton.setObjectName("RButton")
        self.RButton.setText("Off")
        self.RButton.setGeometry(QtCore.QRect(72.5*R, 20*R, 65*R, 15*R))
        self.RButton.setProperty("State", False)
        self.RButton.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[State = true]{"
            + C_MEDIUM_GREY + "} QWidget[State = false]{" + C_RED + "}")

        #Button States transition Indicator
        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")
        self.StatusTransition.move(150*R,0*R)

        self.LState = "Active"
        self.RState = "Inactive"
        self.SetButtonStateNames("Active", "Inactive")
        self.ButtonRState()
        self.Activate(True)
        self.LButton.clicked.connect(self.ButtonLStateLocked)
        self.RButton.clicked.connect(self.ButtonRStateLocked)


    def SetButtonStateNames(self, Active, Inactive):
        self.ActiveName = Active
        self.InactiveName = Inactive

    # Neutral means that the button shouldn't show any color

    @QtCore.Slot()
    def ButtonTransitionState(self, bool):
        self.StatusTransition.UpdateColor(bool)
    # when you clicked the button, busy will change into orange
    @QtCore.Slot()
    def ButtonLTransitionState(self, bool):
        if self.LState == self.InactiveName and self.RState == self.ActiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonRTransitionState(self, bool):
        if self.LState == self.ActiveName and self.RState == self.InactiveName:
            self.StatusTransition.UpdateColor(bool)
        else:
            pass

    # Neutral means that the button shouldn't show any
    #if in R state and clicked L, then turn into R* (R lock/gray out) state
    @QtCore.Slot()
    def ButtonLStateLocked(self):
        if self.LState == self.InactiveName and self.RState == self.ActiveName:
            self.RButton.setProperty("State", True)
            self.RButton.setStyle(self.RButton.style())


    @QtCore.Slot()
    def ButtonRStateLocked(self):
        if self.LState == self.ActiveName and self.RState == self.InactiveName:
            self.LButton.setProperty("State", False)
            self.LButton.setStyle(self.LButton.style())


    # L->L/R->L state.
    # initial state is R active, then change into L
    # initial state is L*(L but grey), then change into L but L(green)
    def ButtonLState(self):
        #
        if self.LState == self.InactiveName and self.RState == self.ActiveName:
            self.LButton.setProperty("State", True)
            self.LButton.setStyle(self.LButton.style())
            self.LState = self.ActiveName
            self.RButton.setProperty("State", "Neutral")
            self.RButton.setStyle(self.RButton.style())
            self.RState = self.InactiveName
        elif self.LState == self.ActiveName and self.RState == self.InactiveName:

            self.LButton.setProperty("State", True)
            self.LButton.setStyle(self.LButton.style())
            self.LState = self.ActiveName
            self.RButton.setProperty("State", "Neutral")
            self.RButton.setStyle(self.RButton.style())
            self.RState = self.InactiveName
        else:
            pass

    # R->R/L->R state.
    # initial state is L active, then change into R
    # initial state is R*(R but grey), then change into R but R(red)
    def ButtonRState(self):
        if self.LState == self.ActiveName and self.RState == self.InactiveName:
            self.RButton.setProperty("State", False)
            self.RButton.setStyle(self.RButton.style())
            self.LState = self.InactiveName
            self.LButton.setProperty("State", "Neutral")
            self.LButton.setStyle(self.LButton.style())
            self.RState = self.ActiveName
        elif self.LState == self.InactiveName and self.RState == self.ActiveName:
            self.RButton.setProperty("State", False)
            self.RButton.setStyle(self.RButton.style())
            self.LState = self.InactiveName
            self.LButton.setProperty("State", "Neutral")
            self.LButton.setStyle(self.LButton.style())
            self.RState = self.ActiveName
        else:
            pass

    @QtCore.Slot()
    def ButtonLClicked(self):
        # time.sleep(1)
        self.ButtonLState()
        self.Signals.sSignal.emit(self.LButton.text())

    @QtCore.Slot()
    def ButtonRClicked(self):
        # time.sleep(1)
        self.ButtonRState()
        self.Signals.sSignal.emit(self.RButton.text())

    def Activate(self, Activate):

        if Activate:
            try:
                # Don't need this because the button only read feedback from PLC
                # self.LButton.clicked.connect(self.ButtonLClicked)
                # self.RButton.clicked.connect(self.ButtonRClicked)
                # print("busy?")
                pass
                # self.LButton.clicked.connect(lambda: self.ButtonLTransitionState(True))
                # self.RButton.clicked.connect(lambda: self.ButtonRTransitionState(True))
            except:

                print("Failed to Activate the Doublebutton")
                pass
        else:
            try:
                #Don't need this because the button only read feedback from PLC
                # self.LButton.clicked.connect(self.ButtonLClicked)
                # self.RButton.clicked.connect(self.ButtonRClicked)

                # self.LButton.clicked.disconnect(self.ButtonLClicked)
                # self.RButton.clicked.disconnect(self.ButtonRClicked)
                pass




            except:
                print("Failed to Deactivate the Doublebutton")

                pass



class DoubleButton_s(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("DoubleButton")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 40*R))
        self.setMinimumSize(140*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")


        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Double button")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 140*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.LButton = QtWidgets.QPushButton(self)
        self.LButton.setObjectName("LButton")
        self.LButton.setText("On")
        self.LButton.setGeometry(QtCore.QRect(2.5 * R, 20 * R, 65 * R, 15 * R))
        self.LButton.setProperty("State", True)
        self.LButton.setStyleSheet(
            "QWidget {" + BORDER_RADIUS + C_WHITE + FONT +C_BKG_WHITE+ "} QWidget[State = true]{" + C_GREEN
            + "} QWidget[State = false]{" + C_MEDIUM_GREY + "}")

        self.RButton = QtWidgets.QPushButton(self)
        self.RButton.setObjectName("RButton")
        self.RButton.setText("Off")
        self.RButton.setGeometry(QtCore.QRect(72.5 * R, 20 * R, 65 * R, 15 * R))
        self.RButton.setProperty("State", False)
        self.RButton.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + C_BKG_WHITE+"} QWidget[State = true]{"
            + C_MEDIUM_GREY + "} QWidget[State = false]{" + C_RED + "}")

        self.LState = "Active"
        self.RState = "Inactive"
        self.SetButtonStateNames("Active", "Inactive")
        self.ButtonRState()

        self.LButton.clicked.connect(self.ButtonLStateLocked)
        self.RButton.clicked.connect(self.ButtonRStateLocked)


    def SetButtonStateNames(self, Active, Inactive):
        self.ActiveName = Active
        self.InactiveName = Inactive


    # Neutral means that the button shouldn't show any color


    # def ButtonLState(self):
    #     if self.LState == self.InactiveName and self.RState == self.ActiveName:
    #         self.LButton.setProperty("State", True)
    #         self.LButton.setStyle(self.LButton.style())
    #         self.LState = self.ActiveName
    #         self.RButton.setProperty("State", "Neutral")
    #         self.RButton.setStyle(self.RButton.style())
    #         self.RState = self.InactiveName
    #     else:
    #         pass
    #
    # def ButtonRState(self):
    #     if self.LState == self.ActiveName and self.RState == self.InactiveName:
    #         self.RButton.setProperty("State", False)
    #         self.RButton.setStyle(self.RButton.style())
    #         self.LState = self.InactiveName
    #         self.LButton.setProperty("State", "Neutral")
    #         self.LButton.setStyle(self.LButton.style())
    #         self.RState = self.ActiveName
    #     else:
    #         pass

    # Neutral means that the button shouldn't show any
    # if in R state and clicked L, then turn into R* (R lock/gray out) state
    @QtCore.Slot()
    def ButtonLStateLocked(self):
        if self.LState == self.InactiveName and self.RState == self.ActiveName:
            self.RButton.setProperty("State", True)
            self.RButton.setStyle(self.RButton.style())

    @QtCore.Slot()
    def ButtonRStateLocked(self):
        if self.LState == self.ActiveName and self.RState == self.InactiveName:
            self.LButton.setProperty("State", False)
            self.LButton.setStyle(self.LButton.style())

    # L->L/R->L state.
    # initial state is R active, then change into L
    # initial state is L*(L but grey), then change into L but L(green)
    def ButtonLState(self):
        #
        if self.LState == self.InactiveName and self.RState == self.ActiveName:
            self.LButton.setProperty("State", True)
            self.LButton.setStyle(self.LButton.style())
            self.LState = self.ActiveName
            self.RButton.setProperty("State", "Neutral")
            self.RButton.setStyle(self.RButton.style())
            self.RState = self.InactiveName
        elif self.LState == self.ActiveName and self.RState == self.InactiveName:

            self.LButton.setProperty("State", True)
            self.LButton.setStyle(self.LButton.style())
            self.LState = self.ActiveName
            self.RButton.setProperty("State", "Neutral")
            self.RButton.setStyle(self.RButton.style())
            self.RState = self.InactiveName
        else:
            pass

    # R->R/L->R state.
    # initial state is L active, then change into R
    # initial state is R*(R but grey), then change into R but R(red)
    def ButtonRState(self):
        if self.LState == self.ActiveName and self.RState == self.InactiveName:
            self.RButton.setProperty("State", False)
            self.RButton.setStyle(self.RButton.style())
            self.LState = self.InactiveName
            self.LButton.setProperty("State", "Neutral")
            self.LButton.setStyle(self.LButton.style())
            self.RState = self.ActiveName
        elif self.LState == self.InactiveName and self.RState == self.ActiveName:
            self.RButton.setProperty("State", False)
            self.RButton.setStyle(self.RButton.style())
            self.LState = self.InactiveName
            self.LButton.setProperty("State", "Neutral")
            self.LButton.setStyle(self.LButton.style())
            self.RState = self.ActiveName
        else:
            pass

    @QtCore.Slot()
    def ButtonLClicked(self):
        # time.sleep(1)
        self.ButtonLState()
        self.Signals.sSignal.emit(self.LButton.text())

    @QtCore.Slot()
    def ButtonRClicked(self):
        # time.sleep(1)
        self.ButtonRState()
        self.Signals.sSignal.emit(self.RButton.text())





class SingleButton(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("SingleButton")
        self.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.setMinimumSize(70*R, 40*R)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 40*R))
        self.Background.setStyleSheet("QLabel {" +C_LIGHT_GREY + BORDER_STYLE+"}")

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Button")
        self.Label.setGeometry(QtCore.QRect(0*R, 0*R, 70*R, 20*R))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet("QLabel {" +FONT+"}")

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setText("Button")
        self.Button.setGeometry(QtCore.QRect(0*R, 20*R, 70*R, 20*R))
        self.Button.setStyleSheet("QPushButton {" +C_BLUE + C_WHITE + FONT + BORDER_RADIUS+"}")

    @QtCore.Slot()
    def ButtonClicked(self):
        self.Signals.sSignal.emit(self.Button.text())

    def Activate(self, Activate):
        if Activate:
            try:
                self.Button.clicked.connect(self.ButtonClicked)
            except:
                pass
        else:
            try:
                self.Button.clicked.disconnect(self.ButtonClicked)
            except:
                pass


class ProcedureWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("ProcedureWidget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 460 * R, 200 * R))

        self.setMinimumSize(460 * R, 20 * R)
        self.setSizePolicy(sizePolicy)
        self.objectname = "ProcedureWidget"
        # self.setStyleSheet("QWidget { background: transparent; }")


        self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GL.setSpacing(3)
        # self.GL.setColumnStretch(1, 2)
        # self.GL.setRowStretch(1, 4)

        self.Group = QtWidgets.QGroupBox(self)
        self.Group.setTitle("ProcedureWidget")
        self.Group.setLayout(self.GL)
        self.Group.move(0 * R, 0 * R)
        self.Group.setStyleSheet("QGroupbox { background: transparent; }")


        self.Running = ColoredStatus(self, mode= 4)
        self.Running.Label.setText("Running")
        self.GL.addWidget(self.Running,0,0,QtCore.Qt.AlignCenter)

        self.INTLKD = ColoredStatus(self, mode= 1)
        self.INTLKD.Label.setText("INTLKD")
        self.GL.addWidget(self.INTLKD,0,1,QtCore.Qt.AlignCenter)

        # self.Menu = QtWidgets.QPushButton(self)
        # self.Menu.setText("Menu")
        # self.Menu.setGeometry(QtCore.QRect(0 * R, 0 * R, 20 * R, 20 * R))
        # self.Menu.clicked.connect(self.expand_window)
        #
        # self.expandwindow = ProcedureSubWindow()


        self.EXIT = Indicator(self)
        self.EXIT.Label.setText("EXIT")
        self.EXIT.SetUnit(" ")
        self.GL.addWidget(self.EXIT, 0, 2, QtCore.Qt.AlignCenter)

        # self.GL.addWidget(self.Menu, 0, 2,QtCore.Qt.AlignCenter)

        self.START = QtWidgets.QPushButton(self)
        self.START.setText("Start")
        self.START.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 20 * R))


        self.STOP = QtWidgets.QPushButton(self)
        self.STOP.setText("Stop")
        self.STOP.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 20 * R))


        self.ABORT =  QtWidgets.QPushButton(self)
        self.ABORT.setText("Abort")
        self.ABORT.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 20 * R))
        self.GL.addWidget(self.START, 1, 0, QtCore.Qt.AlignCenter)
        self.GL.addWidget(self.STOP, 1, 1, QtCore.Qt.AlignCenter)
        self.GL.addWidget(self.ABORT,1,2,QtCore.Qt.AlignCenter)

    def expand_window(self):
        self.expandwindow.show()


class ProcedureSubWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(1500*R, 600*R)
        self.setMinimumSize(1500*R, 600*R)
        self.setWindowTitle("Detailed Information")

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1500*R, 600*R))

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
        self.GroupRD.move(0 * R, 240 * R)

        self.Label = QtWidgets.QPushButton(self.GroupWR)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        # self.Label.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.GLWR.addWidget(self.Label)


        self.Start = QtWidgets.QPushButton(self.GroupWR)
        self.Start.setText("Start")
        self.Start.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.Start)

        self.Stop = QtWidgets.QPushButton(self.GroupWR)
        self.Stop.setText("Stop")
        self.Stop.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.Stop)

        self.Abort = QtWidgets.QPushButton(self.GroupWR)
        self.Abort.setText("Abort")
        self.Abort.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.Abort)

        self.RST_FF = QtWidgets.QPushButton(self.GroupWR)
        self.RST_FF.setText("RST_FF")
        self.GLWR.addWidget(self.RST_FF)

        self.TS_SEL_WR = SetPoint(self.GroupWR)
        self.TS_SEL_WR.Label.setText("SEL")
        self.GLWR.addWidget(self.TS_SEL_WR)

        self.ADDREM_MASS_WR = SetPoint(self.GroupWR)
        self.ADDREM_MASS_WR.Label.setText("ADDREM_MASS")
        self.GLWR.addWidget(self.ADDREM_MASS_WR)

        self.MAXTIME_WR = SetPoint(self.GroupWR)
        self.MAXTIME_WR.Label.setText("MAXTIME")
        self.GLWR.addWidget(self.MAXTIME_WR)

        self.updatebutton = QtWidgets.QPushButton(self.GroupWR)
        self.updatebutton.setText("Update")
        self.updatebutton.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.updatebutton)

        self.Interlock = ColoredStatus(self.GroupRD, mode = 1)
        self.Interlock.Label.setText("INTLCK")
        self.GLRD.addWidget(self.Interlock)

        self.EXIT = Indicator(self.GroupRD)
        self.EXIT.Label.setText("EXIT")
        self.EXIT.SetUnit(" ")
        self.GLRD.addWidget(self.EXIT)

        self.SEL_RD = SetPoint(self.GroupWR)
        self.SEL_RD.Label.setText("SEL")
        self.GLRD.addWidget(self.SEL_RD)

        self.ADDREM_MASS_RD = SetPoint(self.GroupWR)
        self.ADDREM_MASS_RD.Label.setText("ADDREM_MASS")
        self.GLRD.addWidget(self.ADDREM_MASS_RD)

        self.MAXTIME_RD = SetPoint(self.GroupWR)
        self.MAXTIME_RD.Label.setText("MAXTIME")
        self.GLRD.addWidget(self.MAXTIME_RD)


        self.N2MASSTX = Indicator(self.GroupRD)
        self.N2MASSTX.Label.setText("N2MASSTX")
        self.N2MASSTX.SetUnit(" ")
        self.GLRD.addWidget(self.N2MASSTX)

        self.FLOWET = Indicator(self.GroupRD)
        self.FLOWET.Label.setText("FLOWET")
        self.FLOWET.SetUnit(" ")
        self.GLRD.addWidget(self.FLOWET)

        self.TS1_MASS = Indicator(self.GroupRD)
        self.TS1_MASS.Label.setText("TS1_MASS")
        self.TS1_MASS.SetUnit(" ")
        self.GLRD.addWidget(self.TS1_MASS)

        self.TS2_MASS = Indicator(self.GroupRD)
        self.TS2_MASS.Label.setText("TS2_MASS")
        self.TS2_MASS.SetUnit(" ")
        self.GLRD.addWidget(self.TS2_MASS)

        self.TS3_MASS = Indicator(self.GroupRD)
        self.TS3_MASS.Label.setText("TS3_MASS")
        self.TS3_MASS.SetUnit(" ")
        self.GLRD.addWidget(self.TS3_MASS)



class ProcedureWidget_TS(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("ProcedureWidget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 460 * R, 200 * R))

        self.setMinimumSize(460 * R, 20 * R)
        self.setSizePolicy(sizePolicy)
        self.objectname = "ProcedureWidget"
        # self.setStyleSheet("QWidget { background: transparent; }")


        self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GL.setSpacing(3)
        # self.GL.setColumnStretch(1, 2)
        # self.GL.setRowStretch(1, 4)

        self.Group = QtWidgets.QGroupBox(self)
        self.Group.setTitle("ProcedureWidget")
        self.Group.setLayout(self.GL)
        self.Group.move(0 * R, 0 * R)
        self.Group.setStyleSheet("QGroupbox { background: transparent; }")


        self.Running = ColoredStatus(self, mode= 4)
        self.Running.Label.setText("Running")
        self.GL.addWidget(self.Running,0,0,QtCore.Qt.AlignCenter)

        self.INTLKD = ColoredStatus(self, mode= 1)
        self.INTLKD.Label.setText("INTLKD")
        self.GL.addWidget(self.INTLKD,0,1,QtCore.Qt.AlignCenter)

        self.Menu = QtWidgets.QPushButton(self)
        self.Menu.setText("Menu")
        self.Menu.setGeometry(QtCore.QRect(0 * R, 0 * R, 20 * R, 20 * R))
        self.Menu.clicked.connect(self.expand_window)

        self.expandwindow = ProcedureSubWindow_TS()


        # self.EXIT = Indicator(self)
        # self.EXIT.Label.setText("EXIT")
        # self.EXIT.SetUnit(" ")

        self.GL.addWidget(self.Menu, 0, 2,QtCore.Qt.AlignCenter)

        self.START = QtWidgets.QPushButton(self)
        self.START.setText("Start")
        self.START.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 20 * R))


        self.STOP = QtWidgets.QPushButton(self)
        self.STOP.setText("Stop")
        self.STOP.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 20 * R))


        self.ABORT =  QtWidgets.QPushButton(self)
        self.ABORT.setText("Abort")
        self.ABORT.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 20 * R))
        self.GL.addWidget(self.START, 1, 0, QtCore.Qt.AlignCenter)
        self.GL.addWidget(self.STOP, 1, 1, QtCore.Qt.AlignCenter)
        self.GL.addWidget(self.ABORT,1,2,QtCore.Qt.AlignCenter)

    def expand_window(self):

        self.expandwindow.show()
        self.InitWindow()

    @QtCore.Slot()
    def InitWindow(self):
        self.expandwindow.SEL_WR.SetValue(self.expandwindow.SEL_RD.value)
        self.expandwindow.ADDREM_MASS_WR.SetValue(self.expandwindow.ADDREM_MASS_RD.value)
        self.expandwindow.MAXTIME_WR.SetValue(self.expandwindow.MAXTIME_RD.value)


class ProcedureSubWindow_TS(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(1500*R, 600*R)
        self.setMinimumSize(1500*R, 600*R)
        self.setWindowTitle("Detailed Information")

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1500*R, 600*R))

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
        self.GroupRD.move(0 * R, 240 * R)

        self.Label = QtWidgets.QPushButton(self.GroupWR)
        self.Label.setObjectName("Label")
        self.Label.setText("TS_ADDREM")
        self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        # self.Label.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        self.GLWR.addWidget(self.Label)


        self.Start = QtWidgets.QPushButton(self.GroupWR)
        self.Start.setText("Start")
        self.Start.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.Start)

        self.Stop = QtWidgets.QPushButton(self.GroupWR)
        self.Stop.setText("Stop")
        self.Stop.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.Stop)

        self.Abort = QtWidgets.QPushButton(self.GroupWR)
        self.Abort.setText("Abort")
        self.Abort.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.Abort)

        self.RST_FF = QtWidgets.QPushButton(self.GroupWR)
        self.RST_FF.setText("RST_FF")
        self.GLWR.addWidget(self.RST_FF)

        self.SEL_WR = SetPoint(self.GroupWR)
        self.SEL_WR.Label.setText("SEL")
        self.GLWR.addWidget(self.SEL_WR)

        self.ADDREM_MASS_WR = SetPoint(self.GroupWR)
        self.ADDREM_MASS_WR.Label.setText("ADDREM_MASS")
        self.GLWR.addWidget(self.ADDREM_MASS_WR)

        self.MAXTIME_WR = SetPoint(self.GroupWR)
        self.MAXTIME_WR.Label.setText("MAXTIME")
        self.GLWR.addWidget(self.MAXTIME_WR)

        self.updatebutton = QtWidgets.QPushButton(self.GroupWR)
        self.updatebutton.setText("Update")
        self.updatebutton.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.updatebutton)

        self.INTLKD = ColoredStatus(self.GroupRD, mode = 1)
        self.INTLKD.Label.setText("INTLCK")
        self.GLRD.addWidget(self.INTLKD)

        self.Running = ColoredStatus(self, mode=4)
        self.Running.Label.setText("Running")
        self.GLRD.addWidget(self.Running)

        self.EXIT = Indicator(self.GroupRD)
        self.EXIT.Label.setText("EXIT")
        self.EXIT.SetUnit(" ")
        self.GLRD.addWidget(self.EXIT)

        self.FF_RD = Indicator(self.GroupWR)
        self.FF_RD.Label.setText("FF")
        self.GLRD.addWidget(self.FF_RD)

        self.SEL_RD = Indicator(self.GroupWR)
        self.SEL_RD.Label.setText("SEL")
        self.GLRD.addWidget(self.SEL_RD)

        self.ADDREM_MASS_RD = Indicator(self.GroupWR)
        self.ADDREM_MASS_RD.Label.setText("ADDREM_MASS")
        self.GLRD.addWidget(self.ADDREM_MASS_RD)

        self.MAXTIME_RD = Indicator(self.GroupWR)
        self.MAXTIME_RD.Label.setText("MAXTIME")
        self.GLRD.addWidget(self.MAXTIME_RD)


        self.N2MASSTX = Indicator(self.GroupRD)
        self.N2MASSTX.Label.setText("N2MASSTX")
        self.N2MASSTX.SetUnit(" ")
        self.GLRD.addWidget(self.N2MASSTX)

        self.FLOWET = Indicator(self.GroupRD)
        self.FLOWET.Label.setText("FLOWET")
        self.FLOWET.SetUnit(" ")
        self.GLRD.addWidget(self.FLOWET)

        self.TS1_MASS = Indicator(self.GroupRD)
        self.TS1_MASS.Label.setText("TS1_MASS")
        self.TS1_MASS.SetUnit(" ")
        self.GLRD.addWidget(self.TS1_MASS)

        self.TS2_MASS = Indicator(self.GroupRD)
        self.TS2_MASS.Label.setText("TS2_MASS")
        self.TS2_MASS.SetUnit(" ")
        self.GLRD.addWidget(self.TS2_MASS)

        self.TS3_MASS = Indicator(self.GroupRD)
        self.TS3_MASS.Label.setText("TS3_MASS")
        self.TS3_MASS.SetUnit(" ")
        self.GLRD.addWidget(self.TS3_MASS)




class ProcedureWidget_PC(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("ProcedureWidget")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 460 * R, 200 * R))

        self.setMinimumSize(460 * R, 20 * R)
        self.setSizePolicy(sizePolicy)
        self.objectname = "ProcedureWidget"
        # self.setStyleSheet("QWidget { background: transparent; }")


        self.GL = QtWidgets.QGridLayout(self)
        self.GL.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GL.setSpacing(3)
        # self.GL.setColumnStretch(1, 2)
        # self.GL.setRowStretch(1, 4)

        self.Group = QtWidgets.QGroupBox(self)
        self.Group.setTitle("ProcedureWidget")
        self.Group.setLayout(self.GL)
        self.Group.move(0 * R, 0 * R)
        self.Group.setStyleSheet("QGroupbox { background: transparent; }")


        self.Running = ColoredStatus(self, mode= 4)
        self.Running.Label.setText("Running")
        self.GL.addWidget(self.Running,0,0,QtCore.Qt.AlignCenter)

        self.INTLKD = ColoredStatus(self, mode= 1)
        self.INTLKD.Label.setText("INTLKD")
        self.GL.addWidget(self.INTLKD,0,1,QtCore.Qt.AlignCenter)

        self.Menu = QtWidgets.QPushButton(self)
        self.Menu.setText("Menu")
        self.Menu.setGeometry(QtCore.QRect(0 * R, 0 * R, 20 * R, 20 * R))
        self.Menu.clicked.connect(self.expand_window)

        self.expandwindow = ProcedureSubWindow_PC()


        # self.EXIT = Indicator(self)
        # self.EXIT.Label.setText("EXIT")
        # self.EXIT.SetUnit(" ")

        self.GL.addWidget(self.Menu, 0, 2,QtCore.Qt.AlignCenter)

        self.START = QtWidgets.QPushButton(self)
        self.START.setText("Start")
        self.START.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 20 * R))


        self.STOP = QtWidgets.QPushButton(self)
        self.STOP.setText("Stop")
        self.STOP.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 20 * R))


        self.ABORT =  QtWidgets.QPushButton(self)
        self.ABORT.setText("Abort")
        self.ABORT.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 20 * R))
        self.GL.addWidget(self.START, 1, 0, QtCore.Qt.AlignCenter)
        self.GL.addWidget(self.STOP, 1, 1, QtCore.Qt.AlignCenter)
        self.GL.addWidget(self.ABORT,1,2,QtCore.Qt.AlignCenter)

    def expand_window(self):
        self.expandwindow.show()
        self.InitWindow()

    @QtCore.Slot()
    def InitWindow(self):
        self.expandwindow.PSET_WR.SetValue(self.expandwindow.PSET_RD.value)
        self.expandwindow.MAXEXPTIME_WR.SetValue(self.expandwindow.MAXEXPTIME_RD.value)
        self.expandwindow.MAXEQTIME_WR.SetValue(self.expandwindow.MAXEQTIME_RD.value)
        self.expandwindow.MAXEQPDIFF_WR.SetValue(self.expandwindow.MAXEQPDIFF_RD.value)
        self.expandwindow.MAXACCTIME_WR.SetValue(self.expandwindow.MAXACCTIME_RD.value)
        self.expandwindow.MAXACCDPDT_WR.SetValue(self.expandwindow.MAXACCDPDT_RD.value)
        self.expandwindow.MAXBLEEDTIME_WR.SetValue(self.expandwindow.MAXBLEEDTIME_RD.value)
        self.expandwindow.MAXBLEEDDPDT_WR.SetValue(self.expandwindow.MAXBLEEDDPDT_RD.value)
        self.expandwindow.SLOWCOMP_SET_WR.SetValue(self.expandwindow.SLOWCOMP_SET_RD.value)


class ProcedureSubWindow_PC(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(1500*R, 600*R)
        self.setMinimumSize(1500*R, 600*R)
        self.setWindowTitle("Detailed Information")

        self.Widget = QtWidgets.QWidget(self)
        self.Widget.setGeometry(QtCore.QRect(0*R, 0*R, 1500*R, 600*R))

        # Groupboxs for alarm/PT/TT

        self.GLWR = QtWidgets.QGridLayout()
        self.GLWR.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GLWR.setSpacing(20 * R)
        self.GLWR.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupWR = QtWidgets.QGroupBox(self.Widget)
        self.GroupWR.setTitle("Write")
        self.GroupWR.setLayout(self.GLWR)
        self.GroupWR.move(0 * R, 0 * R)

        self.GLRD = QtWidgets.QGridLayout()
        self.GLRD.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.GLRD.setSpacing(20 * R)
        self.GLRD.setAlignment(QtCore.Qt.AlignCenter)

        self.GroupRD = QtWidgets.QGroupBox(self.Widget)
        self.GroupRD.setTitle("Read")
        self.GroupRD.setLayout(self.GLRD)
        self.GroupRD.move(0 * R, 350 * R)
        #
        # self.Label = QtWidgets.QPushButton(self.GroupWR)
        # self.Label.setObjectName("Label")
        # self.Label.setText("PCYCLE")
        # self.Label.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        # # self.Label.setStyleSheet("QPushButton {" + TITLE_STYLE + "}")
        # self.GLWR.addWidget(self.Label)


        self.Start = QtWidgets.QPushButton(self.GroupWR)
        self.Start.setText("Start")
        self.Start.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.Start,0,0,QtCore.Qt.AlignCenter)

        self.Stop = QtWidgets.QPushButton(self.GroupWR)
        self.Stop.setText("Stop")
        self.Stop.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.Stop,0,1,QtCore.Qt.AlignCenter)

        self.Abort = QtWidgets.QPushButton(self.GroupWR)
        self.Abort.setText("Abort")
        self.Abort.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.Abort,0,2,QtCore.Qt.AlignCenter)

        self.RST_ABORT_FF = QtWidgets.QPushButton(self.GroupWR)
        self.RST_ABORT_FF.setText("RST_ABORT_FF")
        self.GLWR.addWidget(self.RST_ABORT_FF,0,3,QtCore.Qt.AlignCenter)

        self.RST_FASTCOMP_FF = QtWidgets.QPushButton(self.GroupWR)
        self.RST_FASTCOMP_FF.setText("RST_FASTCOMP_FF")
        self.GLWR.addWidget(self.RST_FASTCOMP_FF,0,4,QtCore.Qt.AlignCenter)

        self.RST_SLOWCOMP_FF = QtWidgets.QPushButton(self.GroupWR)
        self.RST_SLOWCOMP_FF.setText("RST_SLOWCOMP_FF")
        self.GLWR.addWidget(self.RST_SLOWCOMP_FF,1,0,QtCore.Qt.AlignCenter)

        self.RST_CYLEQ_FF = QtWidgets.QPushButton(self.GroupWR)
        self.RST_CYLEQ_FF.setText("RST_CYLEQ_FF")
        self.GLWR.addWidget(self.RST_CYLEQ_FF,1,1,QtCore.Qt.AlignCenter)

        self.RST_ACCHARGE_FF = QtWidgets.QPushButton(self.GroupWR)
        self.RST_ACCHARGE_FF.setText("RST_ACCHARGE_FF")
        self.GLWR.addWidget(self.RST_ACCHARGE_FF,1,2,QtCore.Qt.AlignCenter)

        self.RST_CYLBLEED_FF = QtWidgets.QPushButton(self.GroupWR)
        self.RST_CYLBLEED_FF.setText("RST_CYLBLEED_FF")
        self.GLWR.addWidget(self.RST_CYLBLEED_FF,1,3,QtCore.Qt.AlignCenter)

        self.PSET_WR = SetPoint(self.GroupWR)
        self.PSET_WR.Label.setText("PSET")
        self.GLWR.addWidget(self.PSET_WR,2,0,QtCore.Qt.AlignCenter)

        self.MAXEXPTIME_WR = SetPoint(self.GroupWR)
        self.MAXEXPTIME_WR.Label.setText("MAXEXPTIME")
        self.GLWR.addWidget(self.MAXEXPTIME_WR,2,1,QtCore.Qt.AlignCenter)

        self.MAXEQTIME_WR = SetPoint(self.GroupWR)
        self.MAXEQTIME_WR.Label.setText("MAXEQTIME")
        self.GLWR.addWidget(self.MAXEQTIME_WR,2,2,QtCore.Qt.AlignCenter)

        self.MAXEQPDIFF_WR = SetPoint(self.GroupWR)
        self.MAXEQPDIFF_WR.Label.setText("MAXEQPDIFF")
        self.GLWR.addWidget(self.MAXEQPDIFF_WR,2,3,QtCore.Qt.AlignCenter)

        self.MAXACCTIME_WR = SetPoint(self.GroupWR)
        self.MAXACCTIME_WR.Label.setText("MAXACCTIME")
        self.GLWR.addWidget(self.MAXACCTIME_WR,2,4,QtCore.Qt.AlignCenter)

        self.MAXACCDPDT_WR = SetPoint(self.GroupWR)
        self.MAXACCDPDT_WR.Label.setText("MAXACCDPDT")
        self.GLWR.addWidget(self.MAXACCDPDT_WR,3,0,QtCore.Qt.AlignCenter)

        self.MAXBLEEDTIME_WR = SetPoint(self.GroupWR)
        self.MAXBLEEDTIME_WR.Label.setText("MAXBLEEDTIME")
        self.GLWR.addWidget(self.MAXBLEEDTIME_WR,3,1,QtCore.Qt.AlignCenter)

        self.MAXBLEEDDPDT_WR = SetPoint(self.GroupWR)
        self.MAXBLEEDDPDT_WR.Label.setText("MAXBLEEDDPDT")
        self.GLWR.addWidget(self.MAXBLEEDDPDT_WR,3,2,QtCore.Qt.AlignCenter)

        self.SLOWCOMP_SET_WR = SetPoint(self.GroupWR)
        self.SLOWCOMP_SET_WR.Label.setText("SLOWCOMP_SET")
        self.GLWR.addWidget(self.SLOWCOMP_SET_WR,3,3,QtCore.Qt.AlignCenter)

        self.updatebutton = QtWidgets.QPushButton(self.GroupWR)
        self.updatebutton.setText("Update")
        self.updatebutton.setGeometry(QtCore.QRect(0 * R, 0 * R, 40 * R, 70 * R))
        self.GLWR.addWidget(self.updatebutton,3,4,QtCore.Qt.AlignCenter)

        self.Running = ColoredStatus(self.GroupRD, mode=4)
        self.Running.Label.setText("Running")
        self.GLRD.addWidget(self.Running, 0, 0)

        self.INTLKD = ColoredStatus(self.GroupRD, mode = 1)
        self.INTLKD.Label.setText("INTLCK")
        self.GLRD.addWidget(self.INTLKD,0,1)

        self.EXIT = Indicator(self.GroupRD)
        self.EXIT.Label.setText("EXIT")
        self.EXIT.SetUnit(" ")
        self.GLRD.addWidget(self.EXIT,0,2)

        self.ABORT_FF_RD = Indicator(self.GroupWR)
        self.ABORT_FF_RD.Label.setText("ABORT_FF")
        self.GLRD.addWidget(self.ABORT_FF_RD,0,3)

        self.FASTCOMP_FF_RD = Indicator(self.GroupWR)
        self.FASTCOMP_FF_RD.Label.setText("FASTCOMP_FF")
        self.GLRD.addWidget(self.FASTCOMP_FF_RD,0,4)

        self.SLOWCOMP_FF_RD = Indicator(self.GroupWR)
        self.SLOWCOMP_FF_RD.Label.setText("SLOWCOMP_FF")
        self.GLRD.addWidget(self.SLOWCOMP_FF_RD,0,5)

        self.CYLEQ_FF_RD = Indicator(self.GroupWR)
        self.CYLEQ_FF_RD.Label.setText("CYLEQ_FF")
        self.GLRD.addWidget(self.CYLEQ_FF_RD,0,6)

        self.ACCHARGE_FF_RD = Indicator(self.GroupWR)
        self.ACCHARGE_FF_RD.Label.setText("ACCHARGE_FF")
        self.GLRD.addWidget(self.ACCHARGE_FF_RD,0,7)

        self.CYLBLEED_FF_RD = Indicator(self.GroupWR)
        self.CYLBLEED_FF_RD.Label.setText("CYLBLEED_FF")
        self.GLRD.addWidget(self.CYLBLEED_FF_RD,0,8)

        self.PSET_RD = Indicator(self.GroupWR)
        self.PSET_RD.Label.setText("PSET")
        self.GLRD.addWidget(self.PSET_RD,0,9)

        self.EXPTIME_RD = Indicator(self.GroupWR)
        self.EXPTIME_RD.Label.setText("EXPTIME")
        self.GLRD.addWidget(self.EXPTIME_RD,1,0)

        self.MAXEXPTIME_RD = Indicator(self.GroupWR)
        self.MAXEXPTIME_RD.Label.setText("MAXEXPTIME")
        self.GLRD.addWidget(self.MAXEXPTIME_RD,1,1)

        self.MAXEQTIME_RD = Indicator(self.GroupWR)
        self.MAXEQTIME_RD.Label.setText("MAXEQTIME")
        self.GLRD.addWidget(self.MAXEQTIME_RD,1,2)

        self.MAXEQPDIFF_RD = Indicator(self.GroupWR)
        self.MAXEQPDIFF_RD.Label.setText("MAXEQPDIFF")
        self.GLRD.addWidget(self.MAXEQPDIFF_RD,1,3)

        self.MAXACCTIME_RD = Indicator(self.GroupWR)
        self.MAXACCTIME_RD.Label.setText("MAXACCTIME")
        self.GLRD.addWidget(self.MAXACCTIME_RD,1,4)

        self.MAXACCDPDT_RD = Indicator(self.GroupWR)
        self.MAXACCDPDT_RD.Label.setText("MAXACCDPDT")
        self.GLRD.addWidget(self.MAXACCDPDT_RD,1,5)

        self.MAXBLEEDTIME_RD = Indicator(self.GroupWR)
        self.MAXBLEEDTIME_RD.Label.setText("MAXBLEEDTIME")
        self.GLRD.addWidget(self.MAXBLEEDTIME_RD,1,6)

        self.MAXBLEEDDPDT_RD = Indicator(self.GroupWR)
        self.MAXBLEEDDPDT_RD.Label.setText("MAXBLEEDDPDT")
        self.GLRD.addWidget(self.MAXBLEEDDPDT_RD,1,7)

        self.SLOWCOMP_SET_RD = Indicator(self.GroupWR)
        self.SLOWCOMP_SET_RD.Label.setText("SLOWCOMP_SET")
        self.GLRD.addWidget(self.SLOWCOMP_SET_RD,1,8)




class Valve_CollapsibleBox(QtWidgets.QWidget):
    def __init__(self,  parent=None, title=""):
        super(Valve_CollapsibleBox, self).__init__(parent)
        # super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 140 * R, 100* R))
        self.setSizePolicy(sizePolicy)
        # self.setSizePolicy(sizePolicy)

        self.toggle_button = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggle_button.setStyleSheet("QToolButton { border: none; subcontrol-position: top;}")
        # self.toggle_button.setStyleSheet("QToolButton { background: white;}")

        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonIconOnly
        )
        self.toggle_button.setSizePolicy(sizePolicy)
        self.toggle_button.setArrowType(QtCore.Qt.DownArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumWidth=0, minimumWidth=0
        )
        self.content_area.setGeometry(QtCore.QRect(0 * R, 0 * R, 140 * R, 100* R))
        # self.content_area.setSizePolicy(
        #     QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        # )
        self.content_area.setSizePolicy(
            sizePolicy
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.content_area.setStyleSheet("QWidget { background: transparent; }")

        # lay = QtWidgets.QHBoxLayout(self)
        # lay.setSpacing(0)
        # lay.setContentsMargins(0, 0, 0, 0)
        # lay.addWidget(self.toggle_button,QtCore.Qt.AlignTop)
        # lay.addWidget(self.content_area)

        lay = QtWidgets.QGridLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button ,0,0)
        lay.addWidget(self.content_area,0,1,3,2, QtCore.Qt.AlignTop)

        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"minimumWidth")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self, b"maximumWidth")
        )
        self.toggle_animation.addAnimation(
            QtCore.QPropertyAnimation(self.content_area, b"maximumWidth")
        )

        # self.lay = QtWidgets.QVBoxLayout()
        # self.Hlay= QtWidgets.QHBoxLayout()
        #
        # self.Set = DoubleButton_s(self)
        # self.Set.Label.setText("Set")
        # self.Set.LButton.setText("open")
        # self.Set.RButton.setText("close")
        # # self.VL.addWidget(self.Set)
        #
        # self.StatusTransition = ColoredStatus(self, mode=3)
        # self.StatusTransition.setObjectName("StatusTransition")
        # self.StatusTransition.Label.setText("Busy")
        #
        # self.ActiveState = ColoredStatus(self, mode =2)
        # self.ActiveState.Label.setText("Status")
        #
        # self.lay.addWidget(self.Set)
        # self.lay.addLayout(self.Hlay)
        # self.Hlay.addWidget(self.StatusTransition)
        # self.Hlay.addWidget(self.ActiveState)

        self.lay = QtWidgets.QGridLayout()
        self.lay.setContentsMargins(20 * R, 20 * R, 20 * R, 20 * R)
        self.lay.setSpacing(3)


        self.Set = DoubleButton_s(self)
        self.Set.Label.setText("Set")
        self.Set.LButton.setText("open")
        self.Set.RButton.setText("close")
        # self.VL.addWidget(self.Set)

        self.StatusTransition = ColoredStatus(self, mode=3)
        self.StatusTransition.setObjectName("StatusTransition")
        self.StatusTransition.Label.setText("Busy")

        self.ActiveState = ColoredStatus(self, mode=2)
        self.ActiveState.Label.setText("Status")

        # self.GL.addWidget(self.Running, 0, 0, QtCore.Qt.AlignCenter)
        self.lay.addWidget(self.Set, 0,0, 1,3, QtCore.Qt.AlignTop)
        # self.lay.addLayout(self.Hlay)
        self.lay.addWidget(self.StatusTransition, 1,0, QtCore.Qt.AlignRight)
        self.lay.addWidget(self.ActiveState,1,1,QtCore.Qt.AlignRight)

        self.setContentLayout(self.lay)

    @QtCore.Slot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(
            QtCore.Qt.RightArrow if not checked else QtCore.Qt.DownArrow
        )
        self.toggle_animation.setDirection(
            QtCore.QAbstractAnimation.Forward
            if not checked
            else QtCore.QAbstractAnimation.Backward
        )
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_width = (
            self.sizeHint().width() - self.content_area.maximumWidth()
        )
        content_width = layout.sizeHint().width()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_width)
            animation.setEndValue(collapsed_width + content_width)

        content_animation = self.toggle_animation.animationAt(
            self.toggle_animation.animationCount() - 1
        )
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_width)
# Neutral means that the button shouldn't show any color

    @QtCore.Slot()
    def ButtonLTransitionState(self, bool):
        if self.Set.LState == self.Set.InactiveName and self.Set.RState == self.Set.ActiveName:
            self.collapse.StatusTransition.UpdateColor(bool)
        else:
            pass

    @QtCore.Slot()
    def ButtonRTransitionState(self, bool):
        if self.Set.LState == self.Set.ActiveName and self.Set.RState == self.Set.InactiveName:
            self.collapse.StatusTransition.UpdateColor(bool)
        else:
            pass





class Valve_image(QtWidgets.QWidget):
    def __init__(self, parent=None, mode="H"):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        if '__file__' in globals():
            self.Path = os.path.dirname(os.path.realpath(__file__))
        else:
            self.Path = os.getcwd()
        self.ImagePath = os.path.join(self.Path, "images")
        self.setObjectName("Valve_image")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 70 * R, 70 * R))
        self.setStyleSheet("QWidget { background: transparent; }")

        self.mode=mode

        self.setMinimumSize(70 * R, 70 * R)
        self.setSizePolicy(sizePolicy)
        self.objectname = "Valve_image"

        # self.button = QtWidgets.QToolButton(self)
        # # self.button.setStyleSheet("QToolButton { background: transparent; }")
        # self.button.setStyleSheet("QWidget { background: transparent; }")
        # self.button.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # # self.button.setStyleSheet("QPushButton {"+C_MEDIUM_GREY+"; }")
        # # Green vertical
        # self.pixmap_valve_GV = QtGui.QPixmap(os.path.join(self.ImagePath, "Valve_green_V.png"))
        # # self.pixmap_valve_GV =  self.pixmap_valve_GV.scaledToWidth(80*R)
        # self.icon_GV = QtGui.QIcon(self.pixmap_valve_GV)
        # #Green horizontal
        # self.pixmap_valve_GH = QtGui.QPixmap(os.path.join(self.ImagePath, "Valve_green_H.png"))
        # self.icon_GH = QtGui.QIcon(self.pixmap_valve_GH)
        # # Red vertical
        # self.pixmap_valve_RV = QtGui.QPixmap(os.path.join(self.ImagePath, "Valve_red_V.png"))
        # self.icon_RV = QtGui.QIcon(self.pixmap_valve_RV)
        # # Red horizontal
        # self.pixmap_valve_RH = QtGui.QPixmap(os.path.join(self.ImagePath, "Valve_red_H.png"))
        # self.icon_RH = QtGui.QIcon(self.pixmap_valve_RH)
        #
        # self.Turnon()
        # self.button.setIconSize(QtCore.QSize(60*R, 60*R))
        # # self.Turnoff(mode=mode)

        self.label = QtWidgets.QLabel(self)
        self.label.setStyleSheet("QLabel { background: transparent; }")
        self.label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # Green vertical
        self.pixmap_valve_GV = QtGui.QPixmap(os.path.join(self.ImagePath, "Valve_green_V.png"))
        self.pixmap_valve_GV =  self.pixmap_valve_GV.scaledToHeight(60*R)
        # Green horizontal
        self.pixmap_valve_GH = QtGui.QPixmap(os.path.join(self.ImagePath, "Valve_green_H.png"))
        self.pixmap_valve_GH = self.pixmap_valve_GH.scaledToWidth(60 * R)
        # self.icon_GH = QtGui.QIcon(self.pixmap_valve_GH)
        # Red vertical
        self.pixmap_valve_RV = QtGui.QPixmap(os.path.join(self.ImagePath, "Valve_red_V.png"))
        self.pixmap_valve_RV = self.pixmap_valve_RV.scaledToHeight(60 * R)
        # self.icon_RV = QtGui.QIcon(self.pixmap_valve_RV)
        # Red horizontal
        self.pixmap_valve_RH = QtGui.QPixmap(os.path.join(self.ImagePath, "Valve_red_H.png"))
        self.pixmap_valve_RH = self.pixmap_valve_RH.scaledToWidth(60 * R)
        # self.icon_RH = QtGui.QIcon(self.pixmap_valve_RH)

        self.Turnon()
        # self.label.setIconSize(QtCore.QSize(60 * R, 60 * R))
        # self.Turnoff(mode=mode)

    # def Turnon(self):
    #     if self.mode == "H":
    #         self.button.setIcon(self.icon_GH)
    #
    #     elif self.mode == "V":
    #         self.button.setIcon(self.icon_GV)
    #     else:
    #         pass
    #
    # def Turnoff(self):
    #     if self.mode == "H":
    #         self.button.setIcon(self.icon_RH)
    #     elif self.mode == "V":
    #         self.button.setIcon(self.icon_RV)
    #     else:
    #         pass

    def Turnon(self):
        if self.mode == "H":
            self.label.setPixmap(self.pixmap_valve_GH)

        elif self.mode == "V":
            self.label.setPixmap(self.pixmap_valve_GV)
        else:
            pass

    def Turnoff(self):
        if self.mode == "H":
            self.label.setPixmap(self.pixmap_valve_RH)
        elif self.mode == "V":
            self.label.setPixmap(self.pixmap_valve_RV)
        else:
            pass



class Pump_image(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        if '__file__' in globals():
            self.Path = os.path.dirname(os.path.realpath(__file__))
        else:
            self.Path = os.getcwd()
        self.ImagePath = os.path.join(self.Path, "images")
        self.setObjectName("Pump_image")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 70 * R, 70 * R))
        # self.setStyleSheet("QWidget { background: transparent; }")



        self.setMinimumSize(140 * R, 140 * R)
        self.setSizePolicy(sizePolicy)
        self.objectname = "Pump_image"


        self.label = QtWidgets.QLabel(self)
        self.label.setStyleSheet("QLabel { background: transparent; }")
        self.label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # Green vertical
        self.pixmap_pump_G = QtGui.QPixmap(os.path.join(self.ImagePath, "pump_green.png"))
        self.pixmap_pump_G =  self.pixmap_pump_G.scaledToHeight(60*R)

        # Red vertical
        self.pixmap_pump_R = QtGui.QPixmap(os.path.join(self.ImagePath, "pump_red.png"))
        self.pixmap_pump_R = self.pixmap_pump_R.scaledToHeight(60 * R)
        # self.icon_RV = QtGui.QIcon(self.pixmap_valve_RV)

        self.Turnon()
        # self.label.setIconSize(QtCore.QSize(60 * R, 60 * R))
        # self.Turnoff(mode=mode)


    def Turnon(self):
            self.label.setPixmap(self.pixmap_pump_G)

    def Turnoff(self):
            self.label.setPixmap(self.pixmap_pump_R)




class SERVO_image(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        if '__file__' in globals():
            self.Path = os.path.dirname(os.path.realpath(__file__))
        else:
            self.Path = os.getcwd()
        self.ImagePath = os.path.join(self.Path, "images")
        self.setObjectName("SERVO_image")
        self.setGeometry(QtCore.QRect(0 * R, 0 * R, 70 * R, 70 * R))
        self.setStyleSheet("QWidget { background: transparent; }")

        self.setMinimumSize(140 * R, 140 * R)
        self.setSizePolicy(sizePolicy)
        self.objectname = "SERVO_image"


        self.label = QtWidgets.QLabel(self)
        self.label.setStyleSheet("QLabel { background: transparent; }")
        self.label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # Green vertical
        self.pixmap_pump_G = QtGui.QPixmap(os.path.join(self.ImagePath, "Pump_green.png"))
        self.pixmap_pump_G =  self.pixmap_pump_G.scaledToHeight(60*R)

        # Red vertical
        self.pixmap_pump_R = QtGui.QPixmap(os.path.join(self.ImagePath, "Pump_red.png"))
        self.pixmap_pump_R = self.pixmap_pump_R.scaledToHeight(60 * R)
        # self.icon_RV = QtGui.QIcon(self.pixmap_valve_RV)

        self.Turnon()
        # self.label.setIconSize(QtCore.QSize(60 * R, 60 * R))
        # self.Turnoff(mode=mode)


    def Turnon(self):
            self.label.setPixmap(self.pixmap_pump_G)

    def Turnoff(self):
            self.label.setPixmap(self.pixmap_pump_R)


class ChangeValueSignal(QtCore.QObject):
    fSignal = QtCore.Signal(float)
    bSignal = QtCore.Signal(bool)
    sSignal = QtCore.Signal(str)
