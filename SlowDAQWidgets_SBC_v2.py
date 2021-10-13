"""
Module SlowDAQWidgets contains the definition of all the custom widgets used in SlowDAQ

By: Mathieu Laurin														

v1.0 Initial code 29/11/19 ML
v1.1 Alarm on state widget 04/03/20 ML
"""

from PySide2 import QtCore, QtWidgets, QtGui
import time
import os

FONT = "font-family: \"Calibri\"; font-size: 14px;"
BORDER_RADIUS = "border-radius: 6px;"
C_LIGHT_GREY = "background-color: rgb(204,204,204);"
C_MEDIUM_GREY = "background-color: rgb(167,167,167);"
C_WHITE = "color: white;"
C_BLACK = "color: black;"
C_GREEN = "background-color: rgb(0,217,0);"
C_RED = "background-color: rgb(255,25,25);"
C_BLUE = "background-color: rgb(34,48,171);"
C_ORANGE = "background-color: rgb(255,132,27);"
TITLE_STYLE = "background-color: rgb(204,204,204); border-radius: 10px; font-family: " \
              "\"Calibri\"; font-size: 22px; font-weight: bold;"
BORDER_STYLE = "border-style: outset; border-width: 2px; border-radius: 6px;" \
               " border-color: black;"


class PnID_Alone(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("PnID_Alone")
        self.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.setMinimumSize(70, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_RADIUS)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("PnID_Alone")
        self.Label.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)


class ColoredStatus(QtWidgets.QWidget):
    # Mode number should be set to 1, 2 and 3
    def __init__(self, parent=None, mode=0):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("ColoredStatus")
        self.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.setMinimumSize(70, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_STYLE)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.Field = QtWidgets.QPushButton(self)
        self.Field.setObjectName("value")
        self.Field.setGeometry(QtCore.QRect(0, 20, 70, 20))
        # self.Field.setAlignment(QtCore.Qt.AlignCenter)

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
            # mode 1: color is grey when active is false and green when active is true
        elif self.Mode == 2:
            self.Field.setStyleSheet(
                "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Active = true]{" + C_GREEN +
                "} QWidget[Active = false]{" + C_MEDIUM_GREY + "}")
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
        self.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.setMinimumSize(70, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_RADIUS)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        # unfinished part of the function, should change color when the reading changes
        # self.Field = QtWidgets.QLineEdit(self)
        # self.Field.setObjectName("value")
        # self.Field.setGeometry(QtCore.QRect(0, 20, 70, 20))
        # self.Field.setAlignment(QtCore.Qt.AlignCenter)
        # self.Field.setStyleSheet(
        # "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Alarm = true]{" + C_ORANGE + "}
        # QWidget[Alarm = false]{" + C_MEDIUM_GREY + "}")
        # self.Field.setProperty("Alarm", False)

        # test part.
        self.ColorButton = QtWidgets.QPushButton(self)
        self.ColorButton.setObjectName("ColorButton")
        self.ColorButton.setGeometry(QtCore.QRect(0, 20, 70, 20))
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
        self.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.setMinimumSize(70, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_STYLE)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("SetPoint")
        self.Label.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setValidator(QtGui.QIntValidator(0, 1000, self))
        self.Field.setAlignment(QtCore.Qt.AlignCenter)
        self.Field.setObjectName("value")
        self.Field.setGeometry(QtCore.QRect(0, 20, 70, 20))
        self.Field.setStyleSheet(BORDER_STYLE + C_BLACK + FONT)
        self.Field.editingFinished.connect(self.UpdateValue)
        self.value = 0
        self.Field.setText(str(self.value))

    def SetValue(self, value):
        self.value = value
        self.Field.setText(format(value, '#.2f') + self.Unit)

    def UpdateValue(self):
        self.value = self.Field.text()


class CheckButton(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("CheckButton")
        self.setGeometry(QtCore.QRect(0, 0, 200, 100))
        self.setMinimumSize(200, 100)
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
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("LoadFile")
        self.setGeometry(QtCore.QRect(0, 0, 600, 1000))
        self.setMinimumSize(600, 1000)
        self.setSizePolicy(sizePolicy)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0, 0, 0, 0)
        self.VL.setSpacing(3)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
        self.VL.addLayout(self.HL)

        self.FilePath = QtWidgets.QLineEdit(self)
        self.FilePath.setGeometry(QtCore.QRect(0, 0, 400, 50))
        self.HL.addWidget(self.FilePath)

        self.LoadPathButton = QtWidgets.QPushButton(self)
        self.LoadPathButton.clicked.connect(self.LoadPath)
        self.LoadPathButton.setText("LoadPath")
        self.LoadPathButton.setFixedSize(100, 50)
        self.HL.addWidget(self.LoadPathButton)

        self.LoadFileButton = QtWidgets.QPushButton(self)
        self.LoadFileButton.setFixedSize(100, 50)
        self.LoadFileButton.setText("ReadFile")
        self.HL.addWidget(self.LoadFileButton)

        self.FileContent = QtWidgets.QTextEdit(self)
        self.FileContent.setReadOnly(True)
        self.VL.addWidget(self.FileContent)

    def LoadPath(self):
        # set default path to read
        defaultpath = "$HOME/.config//SBC/SlowControl.ini"
        filterset = "*.ini;;*.py;;*.*"
        name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', dir=defaultpath, filter=filterset)
        self.FilePath.setText(name[0])

        try:
            print("Read " + str(self.FilePath.text()))
            file = open(self.FilePath.text(), 'r')

            with file:
                text = file.read()
                self.FileContent.setText(text)
        except:
            print("Error! Please type in a valid path")


class CustomSave(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("CustomSave")
        self.setGeometry(QtCore.QRect(0, 0, 600, 1000))
        self.setMinimumSize(600, 1000)
        self.setSizePolicy(sizePolicy)

        self.VL = QtWidgets.QHBoxLayout()
        self.VL.setContentsMargins(0, 0, 0, 0)
        self.VL.setSpacing(3)

        self.FilePath = QtWidgets.QLineEdit(self)
        self.FilePath.setGeometry(QtCore.QRect(0, 0, 400, 50))
        self.VL.addWidget(self.FilePath)

        self.LoadPathButton = QtWidgets.QPushButton(self)
        self.LoadPathButton.clicked.connect(self.LoadPath)
        self.LoadPathButton.setText("ChoosePath")
        self.LoadPathButton.setFixedSize(100, 50)
        self.LoadPathButton.move(400, 0)
        self.VL.addWidget(self.LoadPathButton)

        self.SaveFileButton = QtWidgets.QPushButton(self)
        self.SaveFileButton.setFixedSize(100, 50)
        self.SaveFileButton.move(500, 0)
        self.SaveFileButton.setText("SaveFile")
        self.VL.addWidget(self.SaveFileButton)

        self.Head = None
        self.Tail = None

    def LoadPath(self):
        # set default path to save
        defaultpath = "$HOME/.config//SBC/"
        filterset = "*.ini"
        name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', dir=defaultpath, filter=filterset)
        self.FilePath.setText(name[0])
        head_tail = os.path.split(name[0])
        # split path to a local path and the project name for future reference
        self.Head = head_tail[0]
        self.Tail = head_tail[1]


class AlarmStatusWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("AlarmStatusWidget")
        self.setGeometry(QtCore.QRect(0, 0, 200, 100))
        self.setMinimumSize(200, 100)
        self.setSizePolicy(sizePolicy)

        self.VL = QtWidgets.QVBoxLayout(self)
        self.VL.setContentsMargins(0, 0, 0, 0)
        self.VL.setSpacing(3)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setMinimumSize(QtCore.QSize(10, 10))
        self.Label.setStyleSheet(TITLE_STYLE)
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setText("Label")
        self.VL.addWidget(self.Label)

        self.HL = QtWidgets.QHBoxLayout()
        self.HL.setContentsMargins(0, 0, 0, 0)
        self.VL.addLayout(self.HL)

        self.Indicator = Indicator(self)
        self.Indicator.Label.setText("Indicator")
        self.HL.addWidget(self.Indicator)

        self.Low_Limit = SetPoint(self)
        self.Low_Limit.Label.setText("LOW")
        self.HL.addWidget(self.Low_Limit)

        self.High_Limit = SetPoint(self)
        self.High_Limit.Label.setText("HIGH")
        self.HL.addWidget(self.High_Limit)

        # When mode is off, the alarm won't be sent out in spite of the value of the indicator value
        self.AlarmMode = QtWidgets.QCheckBox(self)
        self.AlarmMode.setText("Active")
        self.HL.addWidget(self.AlarmMode)

        self.Alarm = False
    @QtCore.Slot()
    def CheckAlarm(self):
        if self.AlarmMode.isChecked():
            if int(self.Low_Limit.value) > int(self.High_Limit.value):
                print("Low limit should be less than high limit!")
            else:
                if int(self.Indicator.value) < int(self.Low_Limit.value):
                    self.Indicator.SetAlarm()
                    self.Alarm = True
                    print(str(self.Label.text()) + " reading is lower than the low limit")
                elif int(self.Indicator.value) > int(self.High_Limit.value):
                    self.Indicator.SetAlarm()
                    self.Alarm = True
                    print(str(self.Label.text()) + " reading is higher than the high limit")
                else:
                    self.Indicator.ResetAlarm()
                    self.Alarm = False
        else:
            self.Indicator.ResetAlarm()
            self.Alarm = False


class BoolIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.setObjectName("BoolIndicator")
        self.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.setMinimumSize(70, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_RADIUS)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setObjectName("value")
        self.Field.setGeometry(QtCore.QRect(0, 20, 70, 20))
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
        self.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.setMinimumSize(70, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_STYLE)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Indicator")
        self.Label.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setObjectName("value")
        self.Field.setGeometry(QtCore.QRect(0, 20, 70, 20))
        self.Field.setAlignment(QtCore.Qt.AlignCenter)
        self.Field.setReadOnly(True)
        self.Field.setStyleSheet(
            "QWidget{" + BORDER_STYLE + C_WHITE + FONT + "} QWidget[Alarm = true]{" + C_ORANGE +
            "} QWidget[Alarm = false]{" + C_MEDIUM_GREY + "}")
        self.Field.Property = False
        self.Field.setProperty("Alarm", False)

        self.Unit = " °C"
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
        self.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.setMinimumSize(70, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_STYLE)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Control")
        self.Label.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setGeometry(QtCore.QRect(0, 20, 70, 20))
        self.Button.setStyleSheet(C_BLUE + C_WHITE + FONT + BORDER_RADIUS)

        self.Unit = " °C"
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


class Menu(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("Menu")
        self.setGeometry(QtCore.QRect(0, 0, 140, 40))
        self.setMinimumSize(140, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 140, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_STYLE)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Menu")
        self.Label.setGeometry(QtCore.QRect(0, 0, 140, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.Combobox = QtWidgets.QComboBox(self)
        self.Combobox.setObjectName("Menu")
        self.Combobox.setGeometry(QtCore.QRect(0, 20, 140, 20))
        self.Combobox.addItem("0")
        self.Combobox.addItem("1")
        self.Combobox.addItem("2")


class Toggle(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("Toggle")
        self.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.setMinimumSize(70, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_STYLE)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Toggle")
        self.Label.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setGeometry(QtCore.QRect(0, 20, 70, 20))
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
        self.setGeometry(QtCore.QRect(0, 0, 70, 250))
        self.setMinimumSize(70, 250)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 70, 250))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_STYLE)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Position")
        self.Label.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setObjectName("value")
        self.Field.setGeometry(QtCore.QRect(0, 20, 70, 20))
        self.Field.setAlignment(QtCore.Qt.AlignCenter)
        self.Field.setReadOnly(True)
        self.Field.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[Alarm = true]{" + C_ORANGE
            + "} QWidget[Alarm = false]{" + C_MEDIUM_GREY + "}")
        self.Field.setProperty("Alarm", False)

        self.Max = QtWidgets.QLabel(self)
        self.Max.setObjectName("Max")
        self.Max.setGeometry(QtCore.QRect(0, 43, 40, 20))
        self.Max.setAlignment(QtCore.Qt.AlignRight)
        self.Max.setStyleSheet(FONT)

        self.Zero = QtWidgets.QLabel(self)
        self.Zero.setObjectName("Zero")
        self.Zero.setText("0\"")
        self.Zero.setAlignment(QtCore.Qt.AlignRight)
        self.Zero.setStyleSheet(FONT)

        self.Min = QtWidgets.QLabel(self)
        self.Min.setObjectName("Min")
        self.Min.setGeometry(QtCore.QRect(0, 230, 40, 20))
        self.Min.setAlignment(QtCore.Qt.AlignRight)
        self.Min.setStyleSheet(FONT)

        self.Slider = QtWidgets.QSlider(self)
        self.Slider.setObjectName("Slider")
        self.Slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.Slider.setGeometry(QtCore.QRect(40, 45, 25, 200))
        self.Slider.setStyleSheet("QSlider::handle:vertical{background: white; border-radius: 5px;}")
        self.Slider.setEnabled(False)

        self.SetLimits(-.88, 2.35)
        self.SetValue(0.)

    def SetValue(self, value):
        self.value = value
        self.Slider.setSliderPosition(value * 100)
        self.Field.setText(format(value, '#.2f') + "\"")

    def SetLimits(self, Min, Max):
        self.Slider.setMaximum(Max * 100)
        self.Slider.setMinimum(Min * 100)
        self.Max.setText(format(Max, '#.2f') + "\"")
        self.Min.setText(format(Min, '#.2f') + "\"")
        Offset = 43 - ((43 - 230) / (Max - Min)) * Max
        self.Zero.setGeometry(QtCore.QRect(0, Offset, 40, 20))

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
        self.setGeometry(QtCore.QRect(0, 0, 140, 40))
        self.setMinimumSize(140, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 140, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_STYLE)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("State")
        self.Label.setGeometry(QtCore.QRect(0, 0, 140, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.Field = QtWidgets.QLineEdit(self)
        self.Field.setObjectName("value")
        self.Field.setGeometry(QtCore.QRect(0, 20, 140, 20))
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
        self.setGeometry(QtCore.QRect(0, 0, 140, 40))
        self.setMinimumSize(140, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 140, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_STYLE)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Double button")
        self.Label.setGeometry(QtCore.QRect(0, 0, 140, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.LButton = QtWidgets.QPushButton(self)
        self.LButton.setObjectName("LButton")
        self.LButton.setText("On")
        self.LButton.setGeometry(QtCore.QRect(0, 20, 70, 20))
        self.LButton.setProperty("State", True)
        self.LButton.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[State = true]{" + C_GREEN
            + "} QWidget[State = false]{" + C_RED + "}")


        self.RButton = QtWidgets.QPushButton(self)
        self.RButton.setObjectName("RButton")
        self.RButton.setText("Off")
        self.RButton.setGeometry(QtCore.QRect(70, 20, 70, 20))
        self.RButton.setProperty("State", False)
        self.RButton.setStyleSheet(
            "QWidget{" + BORDER_RADIUS + C_WHITE + FONT + "} QWidget[State = true]{"
            + C_GREEN + "} QWidget[State = false]{" + C_RED + "}")


        self.LState = "Active"
        self.RState = "Inactive"
        self.SetButtonStateNames("Active", "Inactive")
        self.ButtonRState()
        self.Activate(True)

    def SetButtonStateNames(self, Active, Inactive):
        self.ActiveName = Active
        self.InactiveName = Inactive

    # Neutral means that the button shouldn't show any color
    def ButtonLState(self):
        if self.LState == self.InactiveName and self.RState == self.ActiveName:
            self.LButton.setProperty("State", True)
            self.LButton.setStyle(self.LButton.style())
            self.LState = self.ActiveName
            self.RButton.setProperty("State", "Neutral")
            self.RButton.setStyle(self.RButton.style())
            self.RState = self.InactiveName
        else:
            pass

    def ButtonRState(self):
        if self.LState == self.ActiveName and self.RState == self.InactiveName:
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
                self.LButton.clicked.connect(self.ButtonLClicked)
                self.RButton.clicked.connect(self.ButtonRClicked)
            except:
                pass
        else:
            try:
                self.LButton.clicked.disconnect(self.ButtonLClicked)
                self.RButton.clicked.disconnect(self.ButtonRClicked)
            except:
                pass


class SingleButton(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.Signals = ChangeValueSignal()

        self.setObjectName("SingleButton")
        self.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.setMinimumSize(70, 40)
        self.setSizePolicy(sizePolicy)

        self.Background = QtWidgets.QLabel(self)
        self.Background.setObjectName("Background")
        self.Background.setGeometry(QtCore.QRect(0, 0, 70, 40))
        self.Background.setStyleSheet(C_LIGHT_GREY + BORDER_STYLE)

        self.Label = QtWidgets.QLabel(self)
        self.Label.setObjectName("Label")
        self.Label.setText("Button")
        self.Label.setGeometry(QtCore.QRect(0, 0, 70, 20))
        self.Label.setAlignment(QtCore.Qt.AlignCenter)
        self.Label.setStyleSheet(FONT)

        self.Button = QtWidgets.QPushButton(self)
        self.Button.setObjectName("Button")
        self.Button.setText("Button")
        self.Button.setGeometry(QtCore.QRect(0, 20, 70, 20))
        self.Button.setStyleSheet(C_BLUE + C_WHITE + FONT + BORDER_RADIUS)

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


class ChangeValueSignal(QtCore.QObject):
    fSignal = QtCore.Signal(float)
    bSignal = QtCore.Signal(bool)
    sSignal = QtCore.Signal(str)
