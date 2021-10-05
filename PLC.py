"""
Class PLC is used to read/write via modbus to the temperature PLC

To read the variable, just call the ReadAll() method
To write to a variable, call the proper setXXX() method

By: Mathieu Laurin

v1.0 Initial code 25/11/19 ML
v1.1 Initialize values, flag when values are updated more modbus variables 04/03/20 ML
"""

import struct, time, zmq, sys, pickle
import struct, time, zmq, sys

from PySide2 import QtWidgets, QtCore, QtGui
from Database_SBC import *
from email.mime.text import MIMEText
from email.header import Header
from smtplib import SMTP_SSL
import requests
import sys
import os

# delete random number package when you read real data from PLC
import random
from pymodbus.client.sync import ModbusTcpClient

sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    print("ExceptType: ", exctype, "Value: ", value, "Traceback: ", traceback)
    # sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook


class PLC:
    def __init__(self):
        super().__init__()

        IP_NI = "192.168.137.62"
        PORT_NI = 502

        self.Client = ModbusTcpClient(IP_NI, port=PORT_NI)
        self.Connected = self.Client.connect()
        print("NI connected: " + str(self.Connected))

        IP_BO = "192.168.137.11"
        PORT_BO = 502

        self.Client_BO = ModbusTcpClient(IP_BO, port=PORT_BO)
        self.Connected_BO = self.Client_BO.connect()
        print(" Beckoff connected: " + str(self.Connected_BO))

        self.nRTD = 8
        self.RTD = [0.] * self.nRTD
        self.RTD_setting = [0.] * self.nRTD
        self.nAttribute = [0.] * self.nRTD
        self.LowLimit = {"PT9998": 0, "PT9999": 0}
        self.HighLimit = {"PT9998": 0, "PT9999": 0}
        self.Activated = {"PT9998": True, "PT9999": True}
        self.Alarm = {"PT9998": False, "PT9999": False}
        self.MainAlarm = False
        self.nValve = 6
        self.Valve = [0]*self.nValve
        # self.PT80 = 0.
        # self.FlowValve = 0.
        # self.BottomChillerSetpoint = 0.
        # self.BottomChillerTemp = 0.
        # self.BottomChillerState = 0
        # self.BottomChillerPowerReset = 0
        # self.TopChillerSetpoint = 0.
        # self.TopChillerTemp = 0.
        # self.TopChillerState = 0
        # self.CameraChillerSetpoint = 0.
        # self.CameraChillerTemp = 0.
        # self.CameraChillerState = 0
        # self.WaterChillerSetpoint = 0.
        # self.WaterChillerTemp = 0.
        # self.WaterChillerPressure = 0.
        # self.WaterChillerState = 0
        # self.InnerPower = 0.
        # self.OuterClosePower = 0.
        # self.OuterFarPower = 0.
        # self.FreonPower = 0.
        # self.ColdRegionSetpoint = 0.
        # self.HotRegionSetpoint = 0.
        # self.HotRegionP = 0.
        # self.HotRegionI = 0.
        # self.HotRegionD = 0.
        # self.ColdRegionP = 0.
        # self.ColdRegionI = 0.
        # self.ColdRegionD = 0.
        # self.HotRegionPIDState = 0
        # self.ClodRegionPIDState = 0
        # self.Camera0Temp = 0.
        # self.Camera0Humidity = 0.
        # self.Camera0AirTemp = 0.
        # self.Camera1Temp = 0.
        # self.Camera1Humidity = 0.
        # self.Camera1AirTemp = 0.
        # self.Camera2Temp = 0.
        # self.Camera2Humidity = 0.
        # self.Camera2AirTemp = 0.
        # self.Camera3Temp = 0.
        # self.Camera3Humidity = 0.
        # self.Camera3AirTemp = 0.
        # self.WaterFlow = 0.
        # self.WaterTemp = 0.
        # self.WaterConductivityBefore = 0.
        # self.WaterConductivityAfter = 0.
        # self.WaterPressure = 0.
        # self.WaterLevel = 0.
        # self.WaterPrimingPower = 0
        # self.WaterPrimingStatus = 0
        # self.BeetleStatus = 0
        self.LiveCounter = 0
        self.NewData_Display = False
        self.NewData_Database = False
        self.NewData_ZMQ=False

    def __del__(self):
        self.Client.close()
        self.Client_BO.close()

    def ReadAll(self):
        if self.Connected:
            # Reading all the RTDs
            Raw = self.Client.read_holding_registers(38000, count=self.nRTD * 2, unit=0x01)
            # RTD_setting = self.Client.read_holding_registers(18002, count=1, unit=0x01)
            for i in range(0, self.nRTD):
                self.RTD[i] = round(
                    struct.unpack("<f", struct.pack("<HH", Raw.getRegister((2 * i) + 1), Raw.getRegister(2 * i)))[0], 3)
                # print("Updating PLC", i, "RTD",self.RTD[i])

            Raw2 = self.Client.read_holding_registers(38000, count=self.nRTD * 2, unit=0x01)
            for i in range(0, self.nRTD):
                self.RTD[i] = round(
                    struct.unpack("<f", struct.pack("<HH", Raw.getRegister((2 * i) + 1), Raw.getRegister(2 * i)))[0], 3)
                # self.RTD[i] = round(
                #     struct.unpack("<f", Raw2.getRegister(i))[0], 3)
                # self.RTD[i] = round(Raw2.getRegister(i), 3)
                # print("Updating PLC", i, "RTD",self.RTD[i])



            Attribute = [0.] * self.nRTD
            for i in range(0, self.nRTD):
                Attribute[i] = self.Client.read_holding_registers(18000 + i * 8, count=1, unit=0x01)
                self.nAttribute[i] = hex(Attribute[i].getRegister(0))
            # print("Attributes", self.nAttribute)

        if self.Connected_BO:
            Raw_BO = [0]*self.nValve
            for j in range(0,15):
                mask=struct.pack(("H",pow(2,j)))
                print(mask)
                print(j,"th digit is ", self.ReadCoil(mask=mask))
            for i in range(0, self.nValve):
                Raw_BO[i] = self.Client_BO.read_holding_registers(12296+i, count=1, unit=0x01)
                self.Valve[i] = struct.pack("H", Raw_BO.getRegister(0))
                print("Address with ",12296+i,"valve value is", self.Valve[i])
                # for i in range(12296):
                #     try:
                #         rr =self.Client_BO.read_coils(i,count=1,unit=0x01)
                #         print(i,"succeed")
                #         print(rr.getBit(0))
                #     except:
                #         print("error")
                #         pass
                # print("read coil")
                # self.ReadCoil()
                # self.ReadValve()
                # self.WriteOpen()
                # time.sleep(2)
                # print("2s...")
                # print("value after open")
                # self.ReadValve()
                # self.WriteClose()
                # time.sleep(2)
                # print("2s..")
                # self.ReadValve()



            # PT80 (Cold Vacuum Conduit Pressure)
            # Raw = self.Client.read_holding_registers(0xA0, count = 2, unit = 0x01)
            # self.PT80 = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 7)
            #
            # Flow valve
            #            Raw = self.Client.read_holding_registers(0x, count = 2, unit = 0x01)
            #            self.FlowValve = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1),
            #            Raw.getRegister(0)))[0], 0)

            # Bottom chiller
            # Raw = self.Client.read_holding_registers(0xA8, count = 4, unit = 0x01)
            # self.BottomChillerSetpoint = round(struct.unpack("<f", struct.pack
            # ("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            # self.BottomChillerTemp = round(struct.unpack("<f", struct.pack
            # ("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            # Raw = self.Client.read_coils(0x10, count = 1, unit = 0x01)
            # self.BottomChillerState = Raw.bits[0]
            #            self.BottomChillerPowerReset = Raw.bits[0]

            # Top chiller
            # Raw = self.Client.read_holding_registers(0xB0, count = 4, unit = 0x01)
            # self.TopChillerSetpoint = round(struct.unpack
            # ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            # self.TopChillerTemp = round(struct.unpack
            # ("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            # Raw = self.Client.read_coils(0x13, count = 1, unit = 0x01)
            # self.TopChillerState = Raw.bits[0]

            # Camera chiller
            # Raw = self.Client.read_holding_registers(0xBA, count = 4, unit = 0x01)
            # self.CameraChillerSetpoint = round(struct.unpack("<f", struct.pack
            # ("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            # self.CameraChillerTemp = round(struct.unpack("<f", struct.pack
            # ("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            # Raw = self.Client.read_coils(0x15, count = 1, unit = 0x01)
            # self.CameraChillerState = Raw.bits[0]

            # Water chiller
            #             Raw = self.Client.read_holding_registers(0xC4, count = 4, unit = 0x01)
            #             self.WaterChillerSetpoint = round(struct.unpack("<f", struct.pack
            #             ("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            #             self.WaterChillerTemp = round(struct.unpack("<f", struct.pack
            #             ("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            #            self.WaterChillerPressure = round(struct.unpack("<f", struct.pack
            #            ("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            #             Raw = self.Client.read_coils(0x17, count = 1, unit = 0x01)
            #             self.WaterChillerState = Raw.bits[0]

            # Heaters
            # Raw = self.Client.read_holding_registers(0xC8, count = 8, unit = 0x01)
            # self.InnerPower = round(struct.unpack
            # ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            # self.OuterClosePower = round(struct.unpack("<f", struct.pack
            # ("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 1)
            # self.OuterFarPower = round(struct.unpack("<f", struct.pack
            # ("<HH", Raw.getRegister(5), Raw.getRegister(4)))[0], 1)
            # self.FreonPower = round(struct.unpack("<f", struct.pack
            # ("<HH", Raw.getRegister(7), Raw.getRegister(6)))[0], 1)

            # Hot/cold region
            #             Raw = self.Client.read_holding_registers(0xD0, count = 4, unit = 0x01)
            #             self.ColdRegionSetpoint = round(struct.unpack
            #             ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            #             self.HotRegionSetpoint = round(struct.unpack
            #             ("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 1)
            #          self.HotRegionP = round(struct.unpack
            #          ("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            #            self.HotRegionI = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            #            self.HotRegionD = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            #            self.ColdRegionP = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            #            self.ColdRegionI = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            #            self.ColdRegionD = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            #             Raw = self.Client.read_coils(0x19, count = 1, unit = 0x01)
            #             self.HotRegionPIDState = Raw.bits[0]
            #            self.ClodRegionPIDState = Raw.bits[0]

            # Cameras
            #            Raw = self.Client.read_holding_registers(0x, count = 24, unit = 0x01)
            #            self.Camera0Temp = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.Camera0Humidity = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            #            self.Camera0AirTemp = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.Camera1Temp = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.Camera1Humidity = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            #            self.Camera1AirTemp = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.Camera2Temp = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.Camera2Humidity = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            #            self.Camera2AirTemp = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.Camera3Temp = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.Camera3Humidity = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            #            self.Camera3AirTemp = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)

            # Water system
            #            Raw = self.Client.read_holding_registers(0x, count = 12, unit = 0x01)
            #            self.WaterFlow = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.WaterTemp = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.WaterConductivityBefore = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.WaterConductivityAfter = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.WaterPressure = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            self.WaterLevel = round(struct.unpack
            #            ("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            #            Raw = self.Client.read_coils(0x, count = 1, unit = 0x01)
            #            self.WaterPrimingPower = Raw.bits[0]
            #            self.WaterPrimingStatus = Raw.bits[1]
            #            self.BeetleStatus = Raw.bits[2]

            # PLC
            Raw = self.Client.read_holding_registers(0x3E9, count=1, unit=0x01)
            self.LiveCounter = Raw.getRegister(0)

            self.NewData_Display = True
            self.NewData_Database = True
            self.NewData_ZMQ = True

            return 0
        else:
            return 1

    def ReadValve(self,address=12296):
        Raw_BO = self.Client_BO.read_holding_registers(address, count=1, unit=0x01)
        output_BO = struct.pack("H", Raw_BO.getRegister(0))
        print("valve value is", output_BO)
        return output_BO

    def WriteOpen(self,address=12296):
        output_BO = self.ReadValve(address)
        input_BO= output_BO or 0x0002
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write open result=", Raw)

    def WriteClose(self,address=12296):
        output_BO = self.ReadValve(address)
        input_BO = output_BO or 0x0004
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write close result=", Raw)

    def Reset(self,address):
        Raw = self.Client_BO.write_register(address, value=0x0010, unit=0x01)
        print("write reset result=", Raw)

    # mask is a number to read a particular digit. for example, if you want to read 3rd digit, the mask is 0100(binary)
    def ReadCoil(self, mask,address=12296):
        output_BO = self.ReadValve(address)
        masked_output= output_BO and mask
        if masked_output == 0:
            return False
        else:
            return True

    def SaveSetting(self):
        self.WriteBool(0x0, 0, 1)

        return 0  # There is no way to know if it worked... Cross your fingers!

    def SetFlowValve(self, value):

        return self.WriteFloat(0x0, value)

    def SetBottomChillerSetpoint(self, value):

        return self.WriteFloat(0x0, value)

    def SetBottomChillerState(self, State):
        if State == "Off":
            value = 0
        elif State == "On":
            value = 1
        else:
            print("State is either on or off in string format.")
            value = None

        return self.WriteBool(0x0, 0, value)

    def SetBottomChillerPowerReset(self, State):
        if State == "Off":
            value = 0
        elif State == "On":
            value = 1
        else:
            print("State is either on or off in string format.")
            value = None

        return self.WriteBool(0x0, 0, value)

    def SetTopChillerSetpoint(self, value):

        return self.WriteFloat(0x0, value)

    def SetTopChillerState(self, State):
        if State == "Off":
            value = 0
        elif State == "On":
            value = 1
        else:
            print("State is either on or off in string format.")
            value = None

        return self.WriteBool(0x0, 0, value)

    def SetCameraChillerSetpoint(self, value):

        return self.WriteFloat(0x0, value)

    def SetCameraChillerState(self, State):
        if State == "Off":
            value = 0
        elif State == "On":
            value = 1
        else:
            print("State is either on or off in string format.")
            value = None

        return self.WriteBool(0x0, 0, value)

    def SetWaterChillerSetpoint(self, value):

        return self.WriteFloat(0x0, value)

    def SetWaterChillerState(self, State):
        if State == "Off":
            value = 0
        elif State == "On":
            value = 1
        else:
            print("State is either on or off in string format.")
            value = None

        return self.WriteBool(0x0, 0, value)

    def SetInnerPower(self, value):

        return self.WriteFloat(0x0, value)

    def SetOuterClosePower(self, value):

        return self.WriteFloat(0x0, value)

    def SetOuterFarPower(self, value):

        return self.WriteFloat(0x0, value)

    def SetFreonPower(self, value):

        return self.WriteFloat(0x0, value)

    def SetInnerPowerState(self, State):
        if State == "Off":
            self.WriteBool(0x0, 0, 1)
        elif State == "On":
            self.WriteBool(0x0, 0, 1)

        return 0  # There is no way to know if it worked... Cross your fingers!

    def SetOuterClosePowerState(self, State):
        if State == "Off":
            self.WriteBool(0x0, 0, 1)
        elif State == "On":
            self.WriteBool(0x0, 0, 1)

        return 0  # There is no way to know if it worked... Cross your fingers!

    def SetOuterFarPowerState(self, State):
        if State == "Off":
            self.WriteBool(0x0, 0, 1)
        elif State == "On":
            self.WriteBool(0x0, 0, 1)

        return 0  # There is no way to know if it worked... Cross your fingers!

    def SetFreonPowerState(self, State):
        if State == "Off":
            self.WriteBool(0x0, 0, 1)
        elif State == "On":
            self.WriteBool(0x0, 0, 1)

        return 0  # There is no way to know if it worked... Cross your fingers!

    def SetColdRegionSetpoint(self, value):

        return self.WriteFloat(0x0, value)

    def SetHotRegionSetpoint(self, value):

        return self.WriteFloat(0x0, value)

    def SetHotRegionP(self, value):

        return self.WriteFloat(0x0, value)

    def SetHotRegionI(self, value):

        return self.WriteFloat(0x0, value)

    def SetHotRegionD(self, value):

        return self.WriteFloat(0x0, value)

    def SetColdRegionP(self, value):

        return self.WriteFloat(0x0, value)

    def SetColdRegionI(self, value):

        return self.WriteFloat(0x0, value)

    def SetColdRegionD(self, value):

        return self.WriteFloat(0x0, value)

    def SetHotRegionPIDMode(self, Mode):
        if Mode == "Manual":
            value = 0
        elif Mode == "Auto":
            value = 1
        else:
            print("State is either on or off in string format.")
            value = None

        return self.WriteBool(0x0, 0, value)

    def SetColdRegionPIDMode(self, Mode):
        if Mode == "Manual":
            value = 0
        elif Mode == "Auto":
            value = 1
        else:
            print("State is either on or off in string format.")
            value = None

        return self.WriteBool(0x0, 0, value)

    def SetWaterPrimingPower(self, State):
        if State == "Off":
            value = 0
        elif State == "On":
            value = 1
        else:
            print("State is either on or off in string format.")
            value = None

        return self.WriteBool(0x0, 0, value)

    def WriteFloat(self, Address, value):
        if self.Connected:
            value = round(value, 3)
            Dummy = self.Client.write_register(Address, struct.unpack("<HH", struct.pack("<f", value))[1], unit=0x01)
            Dummy = self.Client.write_register(Address + 1, struct.unpack("<HH", struct.pack("<f", value))[0],
                                               unit=0x01)

            time.sleep(1)

            Raw = self.Client.read_holding_registers(Address, count=2, unit=0x01)
            rvalue = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 3)

            if value == rvalue:
                return 0
            else:
                return 2
        else:
            return 1

    def WriteBool(self, Address, Bit, value):
        if self.Connected:
            Raw = self.Client.read_coils(Address, count=Bit, unit=0x01)
            Raw.bits[Bit] = value
            Dummy = self.Client.write_coil(Address, Raw, unit=0x01)

            time.sleep(1)

            Raw = self.Client.read_coils(Address, count=Bit, unit=0x01)
            rvalue = Raw.bits[Bit]

            if value == rvalue:
                return 0
            else:
                return 2
        else:
            return 1


# Class to update myseeq database
class UpdateDataBase(QtCore.QObject):
    def __init__(self, PLC, parent=None):
        super().__init__(parent)

        self.PLC = PLC
        self.db = mydatabase()
        self.Running = False
        self.period = 60
        print("begin updating Database")

    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:
            self.dt = datetime_in_s()
            print("Database Updating", self.dt)

            if self.PLC.NewData_Database:
                print("Wrting PLC data to database...")
                self.db.insert_data_into_datastorage("TT9998", self.dt, self.PLC.RTD[6])
                self.db.insert_data_into_datastorage("TT9999", self.dt, self.PLC.RTD[7])
                self.PLC.NewData_Database = False

            else:
                print("Database Updating stops.")
                pass

            time.sleep(self.period)


    @QtCore.Slot()
    def stop(self):
        self.Running = False

# Class to read PLC value every 2 sec
class UpdatePLC(QtCore.QObject):
    def __init__(self, PLC, parent=None):
        super().__init__(parent)

        self.PLC = PLC
        self.message_manager = message_manager()
        self.Running = False
        self.period=2

    @QtCore.Slot()
    def run(self):
        try:
            self.Running = True

            while self.Running:
                print("PLC updating", datetime.datetime.now())
                self.PLC.ReadAll()
                self.check_alarm(6, "PT9998")
                self.check_alarm(7, "PT9999")
                self.or_alarm_signal()
                time.sleep(self.period)
        except:
            (type, value, traceback) = sys.exc_info()
            exception_hook(type, value, traceback)

    @QtCore.Slot()
    def stop(self):
        self.Running = False

    def check_alarm(self, RTDNum, pid):

        if self.PLC.Activated[pid]:
            if int(self.PLC.LowLimit[pid]) > int(self.PLC.HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if int(self.PLC.RTD[RTDNum]) < int(self.PLC.LowLimit[pid]):
                    self.setalarm(RTDNum,pid)
                    self.PLC.Alarm[pid] = True
                    print(pid , " reading is lower than the low limit")
                elif int(self.PLC.RTD[RTDNum]) > int(self.PLC.HighLimit[pid]):
                    self.setalarm(RTDNum, pid)
                    print(pid,  " reading is higher than the high limit")
                else:
                    self.resetalarm(RTDNum, pid)
                    print("PT is in normal range")

        else:
            self.resetalarm(RTDNum, pid)
            pass

    def setalarm(self, RTDNum, pid):
        self.PLC.Alarm[pid] = True
        # and send email or slack messages
        msg = "SBC alarm: {pid} is out of range".format(pid=pid)
        # self.message_manager.tencent_alarm(msg)
        # self.message_manager.slack_alarm(msg)

    def resetalarm(self, RTDNum, pid):
        self.PLC.Alarm[pid] = False
        # and send email or slack messages

    def or_alarm_signal(self):
        if True in self.PLC.Alarm:
            self.PLC.MainAlarm = True
        else:
            self.PLC.MainAlarm = False


class UpdateServer(QtCore.QObject):
    def __init__(self, PLC, parent=None):
        super().__init__(parent)
        self.PLC = PLC
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")
        self.Running=False
        self.period=2
        print("connect to the PLC server")
        self.data_dic={"data":{"PT9998":None,"PT9999":None},"Alarm":self.PLC.Alarm, "MainAlarm":self.PLC.MainAlarm}
        self.data_package=pickle.dumps(self.data_dic)

    @QtCore.Slot()
    def run(self):
        self.Running=True
        while self.Running:
            print("refreshing the server")
            if self.PLC.NewData_ZMQ:

                # message = self.socket.recv()
                # print("refreshing")
                # print(f"Received request: {message}")
                self.write_data()

                #  Send reply back to client
                # self.socket.send(b"World")
                self.pack_data()
                # print(self.data_package)
                # data=pickle.dumps([0,0])
                # self.socket.send(data)
                self.socket.send(self.data_package)
                # self.socket.sendall(self.data_package)
                self.PLC.NewData_ZMQ = False
            else:
                print("PLC server stops")
                pass
            time.sleep(self.period)

    @QtCore.Slot()
    def stop(self):
        self.Running = False

    def pack_data(self):
        self.data_dic["data"]["PT9998"] = self.PLC.RTD[6]
        self.data_dic["data"]["PT9999"] = self.PLC.RTD[7]
        self.data_package=pickle.dumps(self.data_dic)

    def write_data(self):
        message = self.socket.recv()
        print(message)
        if message == b'this is a command':
            self.PLC.WriteOpen()
            self.PLC.ReadValve()
            print("I will set valve")
        elif message == b'no command':
            self.PLC.WriteClose()
            self.PLC.ReadValve()
            print("I will stay here")
        elif message == b'this an anti_conmmand':

            print("reset the valve")
        else:
            print("I didn't see any command")
            pass



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

        # Update database on another thread
        self.DataUpdateThread = QtCore.QThread()
        self.UpDatabase = UpdateDataBase(self.PLC)
        self.UpDatabase.moveToThread(self.DataUpdateThread)
        self.DataUpdateThread.started.connect(self.UpDatabase.run)
        self.DataUpdateThread.start()

        # Update database on another thread
        self.ServerUpdateThread = QtCore.QThread()
        self.UpServer = UpdateServer(self.PLC)
        self.UpServer.moveToThread(self.ServerUpdateThread)
        self.ServerUpdateThread.started.connect(self.UpServer.run)
        self.ServerUpdateThread.start()


        # Stop all updater threads
    @QtCore.Slot()
    def StopUpdater(self):
        self.UpPLC.stop()
        self.PLCUpdateThread.quit()
        self.PLCUpdateThread.wait()

        self.UpDatabase.stop()
        self.DataUpdateThread.quit()
        self.DataUpdateThread.wait()

        self.UpServer.stop()
        self.ServerUpdateThread.quit()
        self.ServerUpdateThread.wait()

class message_manager():
    def __init__(self):
        # info about tencent mail settings
        self.host_server = "smtp.qq.com"
        self.sender_qq = "390282332"
        self.pwd = "bngozrzmzsbocafa"
        self.sender_mail = "390282332@qq.com"
        # self.receiver1_mail = "cdahl@northwestern.edu"
        self.receiver1_mail = "runzezhang@foxmail.com"
        self.mail_title = "Alarm from SBC"

        #info about slack settings
        self.slack_webhook_url = 'https://hooks.slack.com/services/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'
        self.slack_channel = None
        self.alert_map = {
            "emoji": {
                "up": ":white_check_mark:",
                "down": ":fire:"
            },
            "text": {
                "up": "RESOLVED",
                "down": "FIRING"
            },
            "message": {
                "up": "Everything is good!",
                "down": "Stuff is burning!"
            },
            "color": {
                "up": "#32a852",
                "down": "#ad1721"
            }
        }

    def tencent_alarm(self, message):
        try:
            # The body content of the mail
            mail_content = " Alarm from SBC slowcontrol: " + message
            # sslLogin
            smtp = SMTP_SSL(self.host_server)
            # set_debuglevel() is used for debugging. The parameter value is 1 to enable debug mode and 0 to disable debug mode.
            smtp.set_debuglevel(1)
            smtp.ehlo(self.host_server)
            smtp.login(self.sender_qq, self.pwd)
            # Define mail content
            msg = MIMEText(mail_content, "plain", "utf-8")
            msg["Subject"] = Header(self.mail_title, "utf-8")
            msg["From"] = self.sender_mail
            msg["To"] = self.receiver1_mail
            # send email
            smtp.sendmail(self.sender_mail, self.receiver1_mail, msg.as_string())
            smtp.quit()
            print("mail sent successfully")
        except Exception as e:
            print("mail failed to send")
            print(e)

    def slack_alarm(self, message, status=None):
        data = {
            "text": "AlertManager",
            "username": "Notifications",
            "channel": self.slack_channel,
            "attachments": [{"text": message}]
        #     "attachments": [g
        #         {
        #             "text": "{emoji} [*{state}*] Status Checker\n {message}".format(
        #                 emoji=self.alert_map["emoji"][status],
        #                 state=self.alert_map["text"][status],
        #                 message=self.alert_map["message"][status]
        #             ),
        #             "color": self.alert_map["color"][status],
        #             "attachment_type": "default",
        #             "actions": [
        #                 {
        #                     "name": "Logs",f
        #                     "text": "Logs",
        #                     "type": "button",
        #                     "style": "primary",
        #                     "url": "https://grafana-logs.dashboard.local"
        #                 },
        #                 {
        #                     "name": "Metrics",
        #                     "text": "Metrics",
        #                     "type": "button",
        #                     "style": "primary",
        #                     "url": "https://grafana-metrics.dashboard.local"
        #                 }
        #             ]
        #         }]
        }
        r = requests.post(self.slack_webhook_url, json=data)
        return r.status_code




if __name__ == "__main__":
    # msg_mana=message_manager()
    # msg_mana.tencent_alarm("this is a test message")
    App = QtWidgets.QApplication(sys.argv)
    # Update=Update()
    PLC=PLC()
    PLC.ReadAll()



    sys.exit(App.exec_())

