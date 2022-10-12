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
from Database_SBC_daemon import *
from email.mime.text import MIMEText
from email.header import Header
from smtplib import SMTP_SSL
import requests
import logging,os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import daemon, os, sys, psutil
import PLC_daemon
import time
# from PLC_damemon import *
from PLC import *
PORT_N=5555
PROCESS_NAME = "TCP"
pid = None
import slowcontrol_env_cons as sec


# delete random number package when you read real data from PLC
import random
from pymodbus.client.sync import ModbusTcpClient

BASE_ADDRESS= 12288

sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    print("ExceptType: ", exctype, "Value: ", value, "Traceback: ", traceback)
    os.system("echo 'ExceptType:{} Value: {}, Traceback: {}' | tee -a /home/hep/Documents/cron-tutorial/output/daemon_test.txt".format(exctype,value,traceback))
    # sys._excepthook(exctype, value, traceback)
    sys.exit(1)
sys.excepthook = exception_hook

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


def PLC_loop():

    while True:
        try:
            # clear_tcp()
            os.system("date | tee /home/hep/Documents/cron-tutorial/output/daemon_test.txt")
            os.system("echo 'while loop ' | tee -a /home/hep/Documents/cron-tutorial/output/daemon_test.txt")
            PLC_body()
        except:
            (type, value, traceback) = sys.exc_info()
            exception_hook(type, value, traceback)
            time.sleep(5)
            print("restarting the BKG loop...")
        time.sleep(5)

def PLC_run():
    # with daemon.DaemonContext():
    #     PLC_loop()

    PLC_loop()

def clear_tcp():
    os.system("source /home/hep/PycharmProjects/pythonProject/SBC-SlowControl/clear_tcp.sh")

def PLC_body():
    os.system("date | tee -a /home/hep/Documents/cron-tutorial/output/daemon_test.txt")
    os.system("echo 'PLC body ' | tee -a /home/hep/Documents/cron-tutorial/output/daemon_test.txt")
    App = QtWidgets.QApplication(sys.argv)
    os.system("date | tee -a /home/hep/Documents/cron-tutorial/output/daemon_test.txt")
    os.system("echo 'APP afterwards ' | tee -a /home/hep/Documents/cron-tutorial/output/daemon_test.txt")
    # print(int("feagrea")) # raise problems
    Update = PLC_daemon.Update()
    sys.exit(App.exec_())

class PLC(QtCore.QObject):
    DATA_UPDATE_SIGNAL=QtCore.Signal(object)
    DATA_TRI_SIGNAL = QtCore.Signal(bool)
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

        os.system("date | tee -a /home/hep/Documents/cron-tutorial/output/daemon_test.txt")
        os.system("echo 'BKG PLC ' | tee -a /home/hep/Documents/cron-tutorial/output/daemon_test.txt")

        self.TT_FP_address = sec.TT_FP_ADDRESS

        self.TT_BO_address = sec.TT_BO_ADDRESS

        self.PT_address = sec.PT_ADDRESS

        self.LEFT_REAL_address = sec.LEFT_REAL_ADDRESS

        self.TT_FP_dic = sec.TT_FP_DIC

        self.TT_BO_dic = sec.TT_BO_DIC

        self.PT_dic = sec.PT_DIC

        self.LEFT_REAL_dic = sec.LEFT_REAL_DIC

        self.TT_FP_LowLimit = sec.TT_FP_LOWLIMIT

        self.TT_FP_HighLimit = sec.TT_FP_HIGHLIMIT

        self.TT_BO_LowLimit = sec.TT_BO_LOWLIMIT

        self.TT_BO_HighLimit = sec.TT_BO_HIGHLIMIT

        self.PT_LowLimit = sec.PT_LOWLIMIT
        self.PT_HighLimit = sec.PT_HIGHLIMIT

        self.LEFT_REAL_HighLimit = sec.LEFT_REAL_HIGHLIMIT
        self.LEFT_REAL_LowLimit = sec.LEFT_REAL_LOWLIMIT

        self.TT_FP_Activated = sec.TT_FP_ACTIVATED

        self.TT_BO_Activated = sec.TT_BO_ACTIVATED

        self.PT_Activated = sec.PT_ACTIVATED
        self.LEFT_REAL_Activated = sec.LEFT_REAL_ACTIVATED

        self.TT_FP_Alarm = sec.TT_FP_ALARM

        self.TT_BO_Alarm = sec.TT_BO_ALARM

        self.PT_Alarm = sec.PT_ALARM
        self.LEFT_REAL_Alarm = sec.LEFT_REAL_ALARM
        self.MainAlarm = sec.MAINALARM
        self.nTT_BO = sec.NTT_BO
        self.nTT_FP = sec.NTT_FP
        self.nPT = sec.NPT
        self.nREAL = sec.NREAL

        self.TT_BO_setting = sec.TT_BO_SETTING
        self.nTT_BO_Attribute = sec.NTT_BO_ATTRIBUTE
        self.PT_setting = sec.PT_SETTING
        self.nPT_Attribute = sec.NPT_ATTRIBUTE

        self.Switch_address = sec.SWITCH_ADDRESS
        self.nSwitch = sec.NSWITCH
        self.Switch = sec.SWITCH
        self.Switch_OUT = sec.SWITCH_OUT
        self.Switch_MAN = sec.SWITCH_MAN
        self.Switch_INTLKD = sec.SWITCH_INTLKD
        self.Switch_ERR = sec.SWITCH

        self.Din_address = sec.DIN_ADDRESS
        self.nDin = sec.NDIN
        self.Din = sec.DIN
        self.Din_dic = sec.DIN_DIC

        self.valve_address = sec.VALVE_ADDRESS
        self.nValve = sec.NVALVE
        self.Valve = sec.VALVE
        self.Valve_OUT = sec.VALVE_OUT
        self.Valve_MAN = sec.VALVE_MAN
        self.Valve_INTLKD = sec.VALVE_INTLKD
        self.Valve_ERR = sec.VALVE_ERR

        self.LOOPPID_ADR_BASE = sec.LOOPPID_ADR_BASE

        self.LOOPPID_MODE0 = sec.LOOPPID_MODE0

        self.LOOPPID_MODE1 = sec.LOOPPID_MODE1

        self.LOOPPID_MODE2 = sec.LOOPPID_MODE2

        self.LOOPPID_MODE3 = sec.LOOPPID_MODE3

        self.LOOPPID_INTLKD = sec.LOOPPID_INTLKD

        self.LOOPPID_MAN = sec.LOOPPID_MAN

        self.LOOPPID_ERR = sec.LOOPPID_ERR

        self.LOOPPID_SATHI = sec.LOOPPID_SATHI

        self.LOOPPID_SATLO = sec.LOOPPID_SATLO

        self.LOOPPID_EN = sec.LOOPPID_EN

        self.LOOPPID_OUT = sec.LOOPPID_OUT

        self.LOOPPID_IN = sec.LOOPPID_IN

        self.LOOPPID_HI_LIM = sec.LOOPPID_HI_LIM

        self.LOOPPID_LO_LIM = sec.LOOPPID_LO_LIM

        self.LOOPPID_SET0 = sec.LOOPPID_SET0

        self.LOOPPID_SET1 = sec.LOOPPID_SET1

        self.LOOPPID_SET2 = sec.LOOPPID_SET2

        self.LOOPPID_SET3 = sec.LOOPPID_SET3

        self.LOOP2PT_ADR_BASE = sec.LOOP2PT_ADR_BASE
        self.LOOP2PT_MODE0 = sec.LOOP2PT_MODE0
        self.LOOP2PT_MODE1 = sec.LOOP2PT_MODE1
        self.LOOP2PT_MODE2 = sec.LOOP2PT_MODE2
        self.LOOP2PT_MODE3 = sec.LOOP2PT_MODE3
        self.LOOP2PT_INTLKD  = sec.LOOP2PT_INTLKD
        self.LOOP2PT_MAN = sec.LOOP2PT_MAN
        self.LOOP2PT_ERR = sec.LOOP2PT_ERR
        self.LOOP2PT_OUT = sec.LOOP2PT_OUT
        self.LOOP2PT_SET1 = sec.LOOP2PT_SET1
        self.LOOP2PT_SET2 = sec.LOOP2PT_SET2
        self.LOOP2PT_SET3 = sec.LOOP2PT_SET3

        self.Procedure_address = sec.PROCEDURE_ADDRESS
        self.Procedure_running = sec.PROCEDURE_RUNNING
        self.Procedure_INTLKD = sec.PROCEDURE_INTLKD
        self.Procedure_EXIT = sec.PROCEDURE_EXIT


        self.signal_data = {  "TT_FP_address":self.TT_FP_address,
                              "TT_BO_address":self.TT_BO_address,
                              "PT_address":self.PT_address,
                              "LEFT_REAL_address":self.LEFT_REAL_address,
                              "TT_FP_dic":self.TT_FP_dic,
                              "TT_BO_dic":self.TT_BO_dic,
                              "PT_dic":self.PT_dic,
                              "LEFT_REAL_dic":self.LEFT_REAL_dic,
                              "TT_FP_LowLimit":self.TT_FP_LowLimit,
                              "TT_FP_HighLimit":self.TT_FP_HighLimit,
                              "TT_BO_LowLimit":self.TT_BO_LowLimit,
                              "TT_BO_HighLimit":self.TT_BO_HighLimit,
                              "PT_LowLimit":self.PT_LowLimit,
                              "PT_HighLimit":self.PT_HighLimit,
                              "LEFT_REAL_HighLimit": self.LEFT_REAL_HighLimit,
                              "LEFT_REAL_LowLimit":self.LEFT_REAL_LowLimit,
                              "TT_FP_Activated":self.TT_FP_Activated,
                              "TT_BO_Activated":self.TT_BO_Activated,
                              "PT_Activated":self.PT_Activated,
                              "LEFT_REAL_Activated":self.LEFT_REAL_Activated,
                              "TT_FP_Alarm":self.TT_FP_Alarm,
                              "TT_BO_Alarm":self.TT_BO_Alarm,
                              "PT_Alarm":self.PT_Alarm,
                              "LEFT_REAL_Alarm":self.LEFT_REAL_Alarm,
                              "MainAlarm":self.MainAlarm,
                              "nTT_BO":self.nTT_BO,
                              "nTT_FP":self.nTT_FP,
                              "nPT":self.nPT,
                              "nREAL":self.nREAL,
                              "TT_BO_setting":self.TT_BO_setting,
                              "nTT_BO_Attribute":self.nTT_BO_Attribute,
                              "PT_setting":self.PT_setting,
                              "nPT_Attribute":self.nPT_Attribute,
                              "Switch_address":self.Switch_address,
                              "nSwitch":self.nSwitch,
                              "Switch":self.Switch,
                              "Switch_OUT":self.Switch_OUT,
                              "Switch_MAN":self.Switch_MAN,
                              "Switch_INTLKD":self.Switch_INTLKD,
                              "Switch_ERR":self.Switch_ERR,
                              "Din_address":self.Din_address,
                              "nDin":self.nDin,
                              "Din":self.Din,
                              "Din_dic":self.Din_dic,
                              "valve_address":self.valve_address,
                              "nValve":self.nValve,
                              "Valve":self.Valve,
                              "Valve_OUT":self.Valve_OUT,
                              "Valve_MAN":self.Valve_MAN,
                              "Valve_INTLKD":self.Valve_INTLKD,
                              "Valve_ERR":self.Valve_ERR,
                              "LOOPPID_ADR_BASE":self.LOOPPID_ADR_BASE,
                              "LOOPPID_MODE0":self.LOOPPID_MODE0,
                              "LOOPPID_MODE1":self.LOOPPID_MODE1,
                              "LOOPPID_MODE2":self.LOOPPID_MODE2,
                              "LOOPPID_MODE3":self.LOOPPID_MODE3,
                              "LOOPPID_INTLKD":self.LOOPPID_INTLKD,
                              "LOOPPID_MAN":self.LOOPPID_MAN,
                              "LOOPPID_ERR":self.LOOPPID_ERR,
                              "LOOPPID_SATHI":self.LOOPPID_SATHI,
                              "LOOPPID_SATLO":self.LOOPPID_SATLO,
                              "LOOPPID_EN":self.LOOPPID_EN,
                              "LOOPPID_OUT":self.LOOPPID_OUT,
                              "LOOPPID_IN":self.LOOPPID_IN,
                              "LOOPPID_HI_LIM":self.LOOPPID_HI_LIM,
                              "LOOPPID_LO_LIM":self.LOOPPID_LO_LIM,
                              "LOOPPID_SET0":self.LOOPPID_SET0,
                              "LOOPPID_SET1":self.LOOPPID_SET1,
                              "LOOPPID_SET2":self.LOOPPID_SET2,
                              "LOOPPID_SET3":self.LOOPPID_SET3,
                              "LOOP2PT_ADR_BASE":self.LOOP2PT_ADR_BASE,
                              "LOOP2PT_MODE0": self.LOOP2PT_MODE0,
                              "LOOP2PT_MODE1": self.LOOP2PT_MODE1,
                              "LOOP2PT_MODE2": self.LOOP2PT_MODE2,
                              "LOOP2PT_MODE3": self.LOOP2PT_MODE3,
                              "LOOP2PT_INTLKD": self.LOOP2PT_INTLKD,
                              "LOOP2PT_MAN": self.LOOP2PT_MAN,
                              "LOOP2PT_ERR": self.LOOP2PT_ERR,
                              "LOOP2PT_OUT": self.LOOP2PT_OUT,
                              "LOOP2PT_SET1": self.LOOP2PT_SET1,
                              "LOOP2PT_SET2": self.LOOP2PT_SET2,
                              "LOOP2PT_SET3": self.LOOP2PT_SET3,
                              "Procedure_address":self.Procedure_address,
                              "Procedure_running":self.Procedure_running,
                              "Procedure_INTLKD":self.Procedure_INTLKD,
                              "Procedure_EXIT":self.Procedure_EXIT}

        self.LiveCounter = 0
        self.NewData_Display = False
        self.NewData_Database = False
        self.NewData_ZMQ = False

    def __del__(self):
        self.Client.close()
        self.Client_BO.close()

    def ReadAll(self):
        # print(self.TT_BO_HighLimit["TT2119"])
        # print(self.TT_BO_Alarm["TT2119"])
        if self.Connected:
            # Reading all the RTDs
            Raw_RTDs_FP = {}
            for key in self.TT_FP_address:
                Raw_RTDs_FP[key] = self.Client.read_holding_registers(self.TT_FP_address[key], count=2, unit=0x01)
                self.TT_FP_dic[key] = round(
                    struct.unpack("<f", struct.pack("<HH", Raw_RTDs_FP[key].getRegister(1), Raw_RTDs_FP[key].getRegister(0)))[0], 3)

                # print(key,self.TT_FP_address[key], "RTD",self.TT_FP_dic[key])

            #################################################################################################

            # # Set Attributes could be commented(disabled) after it is done
            # Attribute_TTFP_address = {}
            # Raw_TT_FP_Attribute = {}
            # for key in self.TT_FP_address:
            #     Attribute_TTFP_address[key] = FPADS_OUT_AT(self.TT_FP_address[key])
            # print(Attribute_TTFP_address)
            # for key in Attribute_TTFP_address:
            #     print(self.ReadFPAttribute(address = Attribute_TTFP_address[key]))
            #
            #     # self.SetFPRTDAttri(mode = 0x2601, address = Attribute_TTFP_address[key])

        #
        #     Raw2 = self.Client.read_holding_registers(38000, count=self.nRTD * 2, unit=0x01)
        #     for i in range(0, self.nRTD):
        #         self.RTD[i] = round(
        #             struct.unpack("<f", struct.pack("<HH", Raw.getRegister((2 * i) + 1), Raw.getRegister(2 * i)))[0], 3)
        #         # self.RTD[i] = round(
        #         #     struct.unpack("<f", Raw2.getRegister(i))[0], 3)
        #         # self.RTD[i] = round(Raw2.getRegister(i), 3)
        #         # print("Updating PLC", i, "RTD",self.RTD[i])
        #
        #
        #
        #     Attribute = [0.] * self.nRTD
        #     for i in range(0, self.nRTD):
        #         Attribute[i] = self.Client.read_holding_registers(18000 + i * 8, count=1, unit=0x01)
        #         self.nAttribute[i] = hex(Attribute[i].getRegister(0))
        #     # print("Attributes", self.nAttribute)

        #########################################################################
        if self.Connected_BO:
            Raw_BO_TT_BO = {}
            for key in self.TT_BO_address:
                Raw_BO_TT_BO[key] = self.Client_BO.read_holding_registers(self.TT_BO_address[key], count=2, unit=0x01)
                self.TT_BO_dic[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_BO_TT_BO[key].getRegister(1), Raw_BO_TT_BO[key].getRegister(0)))[0], 3)
                # print(key, "little endian", hex(Raw_BO_TT_BO[key].getRegister(1)),"big endian",hex(Raw_BO_TT_BO[key].getRegister(0)))
                # print(key, "'s' value is", self.TT_BO_dic[key])

            ##########################################################################################

            # test endian of TT BO

            # for key in self.TT_BO_address:
            #     Raw_BO_TT_BO[key] = self.Client_BO.read_holding_registers(self.TT_BO_address[key], count=4, unit=0x01)
            #     self.TT_BO_dic[key] = round(
            #         struct.unpack("<d", struct.pack("<HHHH", Raw_BO_TT_BO[key].getRegister(3),Raw_BO_TT_BO[key].getRegister(2),Raw_BO_TT_BO[key].getRegister(1), Raw_BO_TT_BO[key].getRegister(0)))[0], 3)
            #     print(key, "0th", hex(Raw_BO_TT_BO[key].getRegister(0)),"1st",hex(Raw_BO_TT_BO[key].getRegister(1)),"2nd",hex(Raw_BO_TT_BO[key].getRegister(2)),"3rd",hex(Raw_BO_TT_BO[key].getRegister(3)))
            #     print(key, "'s' value is", self.TT_BO_dic[key])

            # for key in self.TT_BO_address:
            #     Raw_BO_TT_BO[key] = self.Client_BO.read_holding_registers(self.TT_BO_address[key], count=4, unit=0x01)
            #     self.TT_BO_dic[key] = round(
            #         struct.unpack("<f", struct.pack(">f",  Raw_BO_TT_BO[key].getRegister(0)))[0], 3)
            #     print(key, "0th", hex(Raw_BO_TT_BO[key].getRegister(0)),"1st",hex(Raw_BO_TT_BO[key].getRegister(1)),"2nd",hex(Raw_BO_TT_BO[key].getRegister(2)),"3rd",hex(Raw_BO_TT_BO[key].getRegister(3)))
            #     print(key, "'s' value is", self.TT_BO_dic[key])

            ##########################################################################################

            Raw_BO_PT = {}
            for key in self.PT_address:
                Raw_BO_PT[key] = self.Client_BO.read_holding_registers(self.PT_address[key], count=2, unit=0x01)
                self.PT_dic[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_BO_PT[key].getRegister(0 + 1),
                                                    Raw_BO_PT[key].getRegister(0)))[0], 3)

            Raw_BO_REAL = {}
            for key in self.LEFT_REAL_address:
                Raw_BO_REAL[key] = self.Client_BO.read_holding_registers(self.LEFT_REAL_address[key], count=2, unit=0x01)
                self.LEFT_REAL_dic[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_BO_REAL[key].getRegister(0 + 1),
                                                    Raw_BO_REAL[key].getRegister(0)))[0], 3)

                # print(key, "'s' value is", self.PT_dic[key])

            Raw_BO_Valve = {}
            Raw_BO_Valve_OUT = {}
            for key in self.valve_address:
                Raw_BO_Valve[key] = self.Client_BO.read_holding_registers(self.valve_address[key], count=1, unit=0x01)
                self.Valve[key] = struct.pack("H", Raw_BO_Valve[key].getRegister(0))

                self.Valve_OUT[key] = self.ReadCoil(1, self.valve_address[key])
                self.Valve_INTLKD[key] = self.ReadCoil(8, self.valve_address[key])
                self.Valve_MAN[key] = self.ReadCoil(16, self.valve_address[key])
                self.Valve_ERR[key] = self.ReadCoil(32, self.valve_address[key])
                # print(key,"Address with ", self.valve_address[key], "valve value is", self.Valve_OUT[key])
                # print(key, "Address with ", self.valve_address[key], "INTLKD is", self.Valve_INTLKD[key])
                # print(key, "Address with ", self.valve_address[key], "MAN value is", self.Valve_MAN[key])
                # print(key, "Address with ", self.valve_address[key], "ERR value is", self.Valve_ERR[key])

            Raw_BO_Switch = {}

            for key in self.Switch_address:
                Raw_BO_Switch[key] = self.Client_BO.read_holding_registers(self.Switch_address[key], count=1, unit=0x01)
                self.Switch[key] = struct.pack("H", Raw_BO_Switch[key].getRegister(0))

                self.Switch_OUT[key] = self.ReadCoil(1, self.Switch_address[key])
                self.Switch_INTLKD[key] = self.ReadCoil(8, self.Switch_address[key])
                self.Switch_MAN[key] = self.ReadCoil(16, self.Switch_address[key])
                self.Switch_ERR[key] = self.ReadCoil(32, self.Switch_address[key])

            # Din's address is a tuple, first number is BO address, the second number is the digit
            Raw_BO_Din = {}

            for key in self.Din_address:
                Raw_BO_Din[key] = self.Client_BO.read_holding_registers(self.Din_address[key][0], count=1, unit=0x01)
                # print(Raw_BO_Din[key])
                self.Din[key] = struct.pack("H", Raw_BO_Din[key].getRegister(0))

                self.Din_dic[key] = self.ReadCoil(2 ** (self.Din_address[key][1]), self.Din_address[key][0])

            Raw_LOOPPID_2 = {}
            Raw_LOOPPID_4 = {}
            Raw_LOOPPID_6 = {}
            Raw_LOOPPID_8 = {}
            Raw_LOOPPID_10 = {}
            Raw_LOOPPID_12 = {}
            Raw_LOOPPID_14 = {}
            Raw_LOOPPID_16 = {}
            for key in self.LOOPPID_ADR_BASE:
                self.LOOPPID_MODE0[key] = self.ReadCoil(1, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_MODE1[key] = self.ReadCoil(2, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_MODE2[key] = self.ReadCoil(2 ** 2, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_MODE3[key] = self.ReadCoil(2 ** 3, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_INTLKD[key] = self.ReadCoil(2 ** 8, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_MAN[key] = self.ReadCoil(2 ** 9, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_ERR[key] = self.ReadCoil(2 ** 10, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_SATHI[key] = self.ReadCoil(2 ** 11, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_SATLO[key] = self.ReadCoil(2 ** 12, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_EN[key] = self.ReadCoil(2 ** 15, self.LOOPPID_ADR_BASE[key])
                Raw_LOOPPID_2[key] = self.Client_BO.read_holding_registers(self.LOOPPID_ADR_BASE[key] + 2, count=2, unit=0x01)
                Raw_LOOPPID_4[key] = self.Client_BO.read_holding_registers(self.LOOPPID_ADR_BASE[key] + 4, count=2,
                                                                           unit=0x01)
                Raw_LOOPPID_6[key] = self.Client_BO.read_holding_registers(self.LOOPPID_ADR_BASE[key] + 6, count=2,
                                                                           unit=0x01)
                Raw_LOOPPID_8[key] = self.Client_BO.read_holding_registers(self.LOOPPID_ADR_BASE[key] + 8, count=2,
                                                                           unit=0x01)
                Raw_LOOPPID_10[key] = self.Client_BO.read_holding_registers(self.LOOPPID_ADR_BASE[key] + 10, count=2,
                                                                            unit=0x01)
                Raw_LOOPPID_12[key] = self.Client_BO.read_holding_registers(self.LOOPPID_ADR_BASE[key] + 12, count=2,
                                                                            unit=0x01)
                Raw_LOOPPID_14[key] = self.Client_BO.read_holding_registers(self.LOOPPID_ADR_BASE[key] + 14, count=2,
                                                                            unit=0x01)
                Raw_LOOPPID_16[key] = self.Client_BO.read_holding_registers(self.LOOPPID_ADR_BASE[key] + 16, count=2,
                                                                            unit=0x01)

                self.LOOPPID_OUT[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOPPID_2[key].getRegister(1),
                                                    Raw_LOOPPID_2[key].getRegister(0)))[0], 3)

                self.LOOPPID_IN[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOPPID_4[key].getRegister(0 + 1),
                                                    Raw_LOOPPID_4[key].getRegister(0)))[0], 3)
                self.LOOPPID_HI_LIM[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOPPID_6[key].getRegister(0 + 1),
                                                    Raw_LOOPPID_6[key].getRegister(0)))[0], 3)
                self.LOOPPID_LO_LIM[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOPPID_8[key].getRegister(0 + 1),
                                                    Raw_LOOPPID_8[key].getRegister(0)))[0], 3)
                self.LOOPPID_SET0[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOPPID_10[key].getRegister(0 + 1),
                                                    Raw_LOOPPID_10[key].getRegister(0)))[0], 3)
                self.LOOPPID_SET1[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOPPID_12[key].getRegister(0 + 1),
                                                    Raw_LOOPPID_12[key].getRegister(0)))[0], 3)
                self.LOOPPID_SET2[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOPPID_14[key].getRegister(0 + 1),
                                                    Raw_LOOPPID_14[key].getRegister(0)))[0], 3)
                self.LOOPPID_SET3[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOPPID_16[key].getRegister(0 + 1),
                                                    Raw_LOOPPID_16[key].getRegister(0)))[0], 3)

            ##########################################################################################
            Raw_LOOP2PT_2 = {}
            Raw_LOOP2PT_4 = {}
            Raw_LOOP2PT_6 = {}

            for key in self.LOOP2PT_ADR_BASE:
                self.LOOP2PT_OUT[key] = self.ReadCoil(1, self.LOOP2PT_ADR_BASE[key])
                self.LOOP2PT_INTLKD[key] = self.ReadCoil(2 ** 3 , self.LOOP2PT_ADR_BASE[key])
                self.LOOP2PT_MAN[key] = self.ReadCoil(2 ** 4, self.LOOP2PT_ADR_BASE[key])
                self.LOOP2PT_ERR[key] = self.ReadCoil(2 ** 5, self.LOOP2PT_ADR_BASE[key])
                self.LOOP2PT_MODE0[key] = self.ReadCoil(2 ** 6, self.LOOP2PT_ADR_BASE[key])
                self.LOOP2PT_MODE1[key] = self.ReadCoil(2 ** 7, self.LOOP2PT_ADR_BASE[key])
                self.LOOP2PT_MODE2[key] = self.ReadCoil(2 ** 8, self.LOOP2PT_ADR_BASE[key])
                self.LOOP2PT_MODE3[key] = self.ReadCoil(2 ** 9, self.LOOP2PT_ADR_BASE[key])

                Raw_LOOP2PT_2[key] = self.Client_BO.read_holding_registers(self.LOOP2PT_ADR_BASE[key] + 2, count=2, unit=0x01)
                Raw_LOOP2PT_4[key] = self.Client_BO.read_holding_registers(self.LOOP2PT_ADR_BASE[key] + 4, count=2,
                                                                           unit=0x01)
                Raw_LOOP2PT_6[key] = self.Client_BO.read_holding_registers(self.LOOP2PT_ADR_BASE[key] + 6, count=2,
                                                                           unit=0x01)

                self.LOOP2PT_SET1[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOP2PT_2[key].getRegister(1),
                                                    Raw_LOOP2PT_2[key].getRegister(0)))[0], 3)

                self.LOOP2PT_SET2[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOP2PT_4[key].getRegister(0 + 1),
                                                    Raw_LOOP2PT_4[key].getRegister(0)))[0], 3)
                self.LOOP2PT_SET3[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_LOOP2PT_6[key].getRegister(0 + 1),
                                                    Raw_LOOP2PT_6[key].getRegister(0)))[0], 3)


            ############################################################################################
            # procedure
            Raw_Procedure = {}
            Raw_Procedure_OUT = {}
            for key in self.Procedure_address:
                Raw_Procedure[key] = self.Client_BO.read_holding_registers(self.Procedure_address[key] + 1, count=1, unit=0x01)

                self.Procedure_running[key] = self.ReadCoil(1, self.Procedure_address[key])
                self.Procedure_INTLKD[key] = self.ReadCoil(2, self.Procedure_address[key])
                self.Procedure_EXIT[key] = Raw_Procedure[key].getRegister(0)

            # test the writing function
            # print(self.Read_BO_2(14308))
            # Raw_BO = self.Client_BO.read_holding_registers(14308, count=2, unit=0x01)
            # print('Raw0',Raw_BO.getRegister(0))
            # print('Raw1', Raw_BO.getRegister(1))
            # output_BO = round(struct.unpack(">f", struct.pack(">HH", Raw_BO.getRegister(1), Raw_BO.getRegister(0)))[
            #                       0], 3)
            # self.Write_BO_2(14308,2.0)
            # print(self.Read_BO_2(14308))

            # print("base",self.LOOPPID_MODE0,"\n",self.LOOPPID_MODE1,"\n",self.LOOPPID_MODE2,"\n",self.LOOPPID_MODE3,"\n")
            #
            # print("other",self.LOOPPID_HI_LIM, "\n", self.LOOPPID_LO_LIM, "\n", self.LOOPPID_SET0, "\n", self.LOOPPID_SET1,
            #           "\n")

            # PLC
            # Raw = self.Client.read_holding_registers(0x3E9, count=1, unit=0x01)
            # self.LiveCounter = Raw.getRegister(0)

            ##########################################################################################


            self.DATA_UPDATE_SIGNAL.emit(self.signal_data)
            self.DATA_TRI_SIGNAL.emit(True)
            # print("signal sent")
            # print(True,'\n',True,"\n",True,"\n")
            self.NewData_Display = True
            self.NewData_Database = True
            self.NewData_ZMQ = True

            return 0
        # else:
        #     raise Exception('Not connected to PLC')  # will it restart the PLC ?

        return 1

    def Read_BO_1(self, address):
        Raw_BO = self.Client_BO.read_holding_registers(address, count=1, unit=0x01)
        output_BO = struct.pack("H", Raw_BO.getRegister(0))
        # print("valve value is", output_BO)
        return output_BO

    def Read_BO_2(self, address):
        Raw_BO = self.Client_BO.read_holding_registers(address, count=2, unit=0x01)
        output_BO = round(struct.unpack(">f", struct.pack(">HH", Raw_BO.getRegister(1), Raw_BO.getRegister(0)))[
                              0], 3)
        # print("valve value is", output_BO)
        return output_BO

    def float_to_2words(self, value):
        fl = float(value)
        x = np.arange(fl, fl + 1, dtype='<f4')
        if len(x) == 1:
            word = x.tobytes()
            piece1, piece2 = struct.unpack('<HH', word)
        else:
            print("ERROR in float to words")
        return piece1, piece2

    def Write_BO_2(self, address, value):
        word1, word2 = self.float_to_2words(value)
        print('words', word1, word2)
        # pay attention to endian relationship
        Raw1 = self.Client_BO.write_register(address, value=word1, unit=0x01)
        Raw2 = self.Client_BO.write_register(address + 1, value=word2, unit=0x01)

        print("write result = ", Raw1, Raw2)

    def WriteBase2(self, address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x0002
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write base2 result=", Raw)

    def WriteBase4(self, address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x0004
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write base4 result=", Raw)

    def WriteBase8(self, address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x0008
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write base8 result=", Raw)

    def WriteBase16(self, address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x0010
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write base16 result=", Raw)

    def Reset(self, address):
        Raw = self.Client_BO.write_register(address, value=0x0010, unit=0x01)
        print("write Reset result=", Raw)

    # mask is a number to read a particular digit. for example, if you want to read 3rd digit, the mask is 0100(binary)
    def ReadCoil(self, mask, address):
        output_BO = self.Read_BO_1(address)
        masked_output = struct.unpack("H", output_BO)[0] & mask
        if masked_output == 0:
            return False
        else:
            return True

    def ReadFPAttribute(self, address):
        Raw = self.Client.read_holding_registers(address, count=1, unit=0x01)
        output = struct.pack("H", Raw.getRegister(0))
        print(Raw.getRegister(0))
        return output

    def SetFPRTDAttri(self, mode, address):
        # Highly suggested firstly read the value and then set as the FP menu suggests
        # mode should be wrtten in 0x
        # we use Read_BO_1 function because it can be used here, i.e read 2 word at a certain address
        output = self.ReadFPAttribute(address)
        print("output", address, output)
        Raw = self.Client.write_register(address, value=mode, unit=0x01)
        print("write open result=", Raw)
        return 0

    def LOOPPID_SET_MODE(self, address, mode=0):
        output_BO = self.Read_BO_1(address)
        if mode == 0:
            input_BO = struct.unpack("H", output_BO)[0] | 0x0010
            Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        elif mode == 1:
            input_BO = struct.unpack("H", output_BO)[0] | 0x0020
            Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        elif mode == 2:
            input_BO = struct.unpack("H", output_BO)[0] | 0x0040
            Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        elif mode == 3:
            input_BO = struct.unpack("H", output_BO)[0] | 0x0080
            Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        else:
            Raw = "ERROR in LOOPPID SET MODE"

        print("write result:", "mode=", Raw)

    def LOOPPID_OUT_ENA(self, address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x2000
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write OUT result=", Raw)

    def LOOPPID_OUT_DIS(self, address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x4000
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write OUT result=", Raw)

    def LOOPPID_SETPOINT(self, address, setpoint, mode=0):
        if mode == 0:
            self.Write_BO_2(address + 10, setpoint)
        elif mode == 1:
            self.Write_BO_2(address + 12, setpoint)
        elif mode == 2:
            self.Write_BO_2(address + 14, setpoint)
        elif mode == 3:
            self.Write_BO_2(address + 16, setpoint)
        else:
            pass

        print("LOOPPID_SETPOINT")

    def LOOPPID_SET_HI_LIM(self, address, value):
        self.Write_BO_2(address + 6, value)
        print("LOOPPID_HI")

    def LOOPPID_SET_LO_LIM(self, address, value):
        self.Write_BO_2(address + 8, value)
        print("LOOPPID_LO")


    def LOOP2PT_SET_MODE(self, address, mode=0):
        output_BO = self.Read_BO_1(address)
        if mode == 0:
            input_BO = struct.unpack("H", output_BO)[0] | 0x0400
            Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        elif mode == 1:
            input_BO = struct.unpack("H", output_BO)[0] | 0x0800
            Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        elif mode == 2:
            input_BO = struct.unpack("H", output_BO)[0] | 0x1000
            Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        elif mode == 3:
            input_BO = struct.unpack("H", output_BO)[0] | 0x2000
            Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        else:
            Raw = "ERROR in LOOP2PT SET MODE"

        print("write result:", "mode=", Raw)

    def LOOP2PT_OPEN(self, address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x0002
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write OUT result=", Raw)

    def LOOP2PT_CLOSE(self, address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x004
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write OUT result=", Raw)

    def LOOP2PT_SETPOINT(self, address, setpoint, mode):
        if mode == 1:
            self.Write_BO_2(address + 2, setpoint)
        elif mode == 2:
            self.Write_BO_2(address + 4, setpoint)
        elif mode == 3:
            self.Write_BO_2(address + 6, setpoint)
        else:
            pass

        print("LOOPPID_SETPOINT")


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
    DB_ERROR_SIG = QtCore.Signal(str)
    # def __init__(self, PLC, parent=None):
    def __init__(self, parent=None):
        super().__init__(parent)

        # self.PLC = PLC
        self.db = ucsbdatabase()
        # self.alarm_db = COUPP_database()
        self.Running = False
        # if loop runs with _counts times with New_Database = False(No written Data), then send alarm to slack. Otherwise, the code normally run(reset the pointer)
        self.Running_counts = 270
        self.Running_pointer = 0
        self.longsleep = 60

        self.base_period = 1

        self.para_alarm = 0
        self.rate_alarm = 10
        self.para_TT = 0
        self.rate_TT = 90
        self.para_PT = 0
        self.rate_PT = 90
        self.para_REAL = 0
        self.rate_REAL = 90
        self.para_Din = 0
        self.rate_Din = 90
        # c is for valve status
        self.para_Valve = 0
        self.rate_Valve = 90
        self.para_Switch = 0
        self.rate_Switch = 90
        self.para_LOOPPID = 0
        self.rate_LOOPPID = 90
        self.para_LOOP2PT = 0
        self.rate_LOOP2PT = 90
        #status initialization
        self.status = False

        #commit initialization
        self.commit_bool = False
        # INITIALIZATION
        self.TT_FP_address = sec.TT_FP_ADDRESS
        self.TT_BO_address = sec.TT_BO_ADDRESS
        self.PT_address = sec.PT_ADDRESS
        self.LEFT_REAL_address = sec.LEFT_REAL_ADDRESS
        self.TT_FP_dic = sec.TT_FP_DIC
        self.TT_BO_dic = sec.TT_BO_DIC
        self.PT_dic = sec.PT_DIC
        self.LEFT_REAL_dic = sec.LEFT_REAL_DIC
        self.TT_FP_LowLimit = sec.TT_FP_LOWLIMIT
        self.TT_FP_HighLimit = sec.TT_FP_HIGHLIMIT
        self.TT_BO_LowLimit = sec.TT_BO_LOWLIMIT
        self.TT_BO_HighLimit = sec.TT_BO_HIGHLIMIT

        self.PT_LowLimit = sec.PT_LOWLIMIT
        self.PT_HighLimit = sec.PT_HIGHLIMIT
        self.LEFT_REAL_HighLimit= sec.LEFT_REAL_HIGHLIMIT
        self.LEFT_REAL_LowLimit = sec.LEFT_REAL_LOWLIMIT
        self.TT_FP_Activated = sec.TT_FP_ACTIVATED
        self.TT_BO_Activated = sec.TT_BO_ACTIVATED
        self.PT_Activated = sec.PT_ACTIVATED
        self.LEFT_REAL_Activated = sec.LEFT_REAL_ACTIVATED

        self.TT_FP_Alarm = sec.TT_FP_ALARM
        self.TT_BO_Alarm = sec.TT_BO_ALARM
        self.PT_Alarm = sec.PT_ALARM
        self.LEFT_REAL_Alarm = sec.LEFT_REAL_ALARM
        self.MainAlarm = sec.MAINALARM
        self.nTT_BO = sec.NTT_BO
        self.nTT_FP = sec.NTT_FP
        self.nPT = sec.NPT
        self.nREAL = sec.NREAL

        self.TT_BO_setting = sec.TT_BO_SETTING
        self.nTT_BO_Attribute = sec.NTT_BO_ATTRIBUTE
        self.PT_setting = sec.PT_SETTING
        self.nPT_Attribute = sec.NPT_ATTRIBUTE

        self.Switch_address = sec.SWITCH_ADDRESS
        self.nSwitch = sec.NSWITCH
        self.Switch = sec.SWITCH
        self.Switch_OUT = sec.SWITCH_OUT
        self.Switch_MAN = sec.SWITCH_MAN
        self.Switch_INTLKD = sec.SWITCH_INTLKD
        self.Switch_ERR = sec.SWITCH_ERR
        self.Din_address = sec.DIN_ADDRESS
        self.nDin = sec.NDIN
        self.Din = sec.DIN
        self.Din_dic = sec.DIN_DIC
        self.valve_address = sec.VALVE_ADDRESS
        self.nValve = sec.NVALVE
        self.Valve = sec.VALVE
        self.Valve_OUT = sec.VALVE_OUT
        self.Valve_MAN = sec.VALVE_MAN
        self.Valve_INTLKD = sec.VALVE_INTLKD
        self.Valve_ERR = sec.VALVE_ERR
        self.LOOPPID_ADR_BASE = sec.LOOPPID_ADR_BASE
        self.LOOPPID_MODE0 = sec.LOOPPID_MODE0
        self.LOOPPID_MODE1 = sec.LOOPPID_MODE1
        self.LOOPPID_MODE2 = sec.LOOPPID_MODE2
        self.LOOPPID_MODE3 = sec.LOOPPID_MODE3
        self.LOOPPID_INTLKD = sec.LOOPPID_INTLKD
        self.LOOPPID_MAN = sec.LOOPPID_MAN
        self.LOOPPID_ERR = sec.LOOPPID_ERR
        self.LOOPPID_SATHI = sec.LOOPPID_SATHI
        self.LOOPPID_SATLO = sec.LOOPPID_SATLO
        self.LOOPPID_EN = sec.LOOPPID_EN
        self.LOOPPID_OUT = sec.LOOPPID_OUT
        self.LOOPPID_IN = sec.LOOPPID_IN
        self.LOOPPID_HI_LIM = sec.LOOPPID_HI_LIM
        self.LOOPPID_LO_LIM = sec.LOOPPID_LO_LIM
        self.LOOPPID_SET0 = sec.LOOPPID_SET0
        self.LOOPPID_SET1 = sec.LOOPPID_SET1
        self.LOOPPID_SET2 = sec.LOOPPID_SET2
        self.LOOPPID_SET3 = sec.LOOPPID_SET3
        self.LOOP2PT_ADR_BASE = sec.LOOP2PT_ADR_BASE
        self.LOOP2PT_MODE0 = sec.LOOP2PT_MODE0
        self.LOOP2PT_MODE1 = sec.LOOP2PT_MODE1
        self.LOOP2PT_MODE2 = sec.LOOP2PT_MODE2
        self.LOOP2PT_MODE3 = sec.LOOP2PT_MODE3
        self.LOOP2PT_INTLKD = sec.LOOP2PT_INTLKD
        self.LOOP2PT_MAN = sec.LOOP2PT_MAN
        self.LOOP2PT_ERR = sec.LOOP2PT_ERR
        self.LOOP2PT_OUT = sec.LOOP2PT_OUT
        self.LOOP2PT_SET1 = sec.LOOP2PT_SET1
        self.LOOP2PT_SET2 = sec.LOOP2PT_SET2
        self.LOOP2PT_SET3 = sec.LOOP2PT_SET3
        self.Procedure_address = sec.PROCEDURE_ADDRESS
        self.Procedure_running = sec.PROCEDURE_RUNNING
        self.Procedure_INTLKD = sec.PROCEDURE_INTLKD
        self.Procedure_EXIT = sec.PROCEDURE_EXIT


        # BUFFER parts
        self.Valve_buffer = sec.VALVE_OUT
        self.Switch_buffer = sec.SWITCH_OUT
        self.Din_buffer = sec.DIN_DIC
        self.LOOPPID_EN_buffer = sec.LOOPPID_EN
        self.LOOPPID_MODE0_buffer = sec.LOOPPID_MODE0
        self.LOOPPID_MODE1_buffer = sec.LOOPPID_MODE1
        self.LOOPPID_MODE2_buffer = sec.LOOPPID_MODE2
        self.LOOPPID_MODE3_buffer = sec.LOOPPID_MODE3
        self.LOOPPID_OUT_buffer = sec.LOOPPID_OUT
        self.LOOPPID_IN_buffer = sec.LOOPPID_IN


        self.LOOP2PT_MODE0_buffer = sec.LOOP2PT_MODE0
        self.LOOP2PT_MODE1_buffer = sec.LOOP2PT_MODE1
        self.LOOP2PT_MODE2_buffer = sec.LOOP2PT_MODE2
        self.LOOP2PT_MODE3_buffer = sec.LOOP2PT_MODE3
        self.LOOP2PT_OUT_buffer = sec.LOOP2PT_OUT

        print("begin updating Database")

    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:
            try:
                self.dt = datetime_in_1e5micro()
                self.early_dt = early_datetime()
                print("Database Updating", self.dt)

                # if self.PLC.NewData_Database:
                if self.status:
                    self.Running_pointer = 0
                    # print(0)
                    # print(self.para_alarm)
                    if self.para_alarm >= self.rate_alarm:

                        # self.alarm_db.ssh_write()
                        self.para_alarm=0

                #     if self.para_TT >= self.rate_TT:
                #         for key in self.TT_FP_dic:
                #             self.db.insert_data_into_datastorage_wocommit(key, self.dt, self.TT_FP_dic[key])
                #         for key in self.TT_BO_dic:
                #             self.db.insert_data_into_datastorage_wocommit(key, self.dt, self.TT_BO_dic[key])
                #         # print("write RTDS")
                #         self.commit_bool = True
                #         self.para_TT = 0
                #     # print(1)
                #     if self.para_PT >= self.rate_PT:
                #         for key in self.PT_dic:
                #             self.db.insert_data_into_datastorage_wocommit(key, self.dt, self.PT_dic[key])
                #         # print("write pressure transducer")
                #         self.commit_bool = True
                #         self.para_PT = 0
                #     # print(2)
                #     for key in self.Valve_OUT:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.Valve_OUT[key] != self.Valve_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_OUT', self.early_dt, self.Valve_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_OUT', self.dt, self.Valve_OUT[key])
                #             self.Valve_buffer[key] = self.Valve_OUT[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #
                #     if self.para_Valve >= self.rate_Valve:
                #         for key in self.Valve_OUT:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_OUT', self.dt, self.Valve_OUT[key])
                #             self.Valve_buffer[key] = self.Valve_OUT[key]
                #             self.commit_bool = True
                #         self.para_Valve = 0
                #     # print(3)
                #     for key in self.Switch_OUT:
                #         # print(key, self.Switch_OUT[key] != self.Switch_buffer[key])
                #         if self.Switch_OUT[key] != self.Switch_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_OUT', self.early_dt, self.Switch_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_OUT', self.dt, self.Switch_OUT[key])
                #             self.Switch_buffer[key] = self.Switch_OUT[key]
                #             self.commit_bool = True
                #             # print(self.Switch_OUT[key])
                #         else:
                #             pass
                #
                #     if self.para_Switch >= self.rate_Switch:
                #         for key in self.Switch_OUT:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_OUT', self.dt, self.Switch_OUT[key])
                #             self.Switch_buffer[key] = self.Switch_OUT[key]
                #             self.commit_bool = True
                #         self.para_Switch = 0
                #     # print(4)
                #     for key in self.Din_dic:
                #         # print(key, self.Switch_OUT[key] != self.Switch_buffer[key])
                #         if self.Din_dic[key] != self.Din_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key, self.early_dt, self.Din_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key, self.dt, self.Din_dic[key])
                #             self.Din_buffer[key] = self.Din_dic[key]
                #             self.commit_bool = True
                #         else:
                #             pass
                #
                #     if self.para_Din >= self.rate_Din:
                #         for key in self.Din_dic:
                #             self.db.insert_data_into_datastorage_wocommit(key, self.dt, self.Din_dic[key])
                #             self.Din_buffer[key] = self.Din_dic[key]
                #         self.commit_bool = True
                #         self.para_Din = 0
                #
                #     # if state of bool variable changes, write the data into database
                #     # print(5)
                #     for key in self.LOOPPID_EN:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.LOOPPID_EN[key] != self.LOOPPID_EN_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_EN', self.early_dt, self.LOOPPID_EN_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_EN', self.dt, self.LOOPPID_EN[key])
                #             self.LOOPPID_EN_buffer[key] = self.LOOPPID_EN[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #
                #     for key in self.LOOPPID_MODE0:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.LOOPPID_MODE0[key] != self.LOOPPID_MODE0_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE0', self.early_dt, self.LOOPPID_MODE0_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE0', self.dt, self.LOOPPID_MODE0[key])
                #             self.LOOPPID_MODE0_buffer[key] = self.LOOPPID_MODE0[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #
                #     for key in self.LOOPPID_MODE1:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.LOOPPID_MODE1[key] != self.LOOPPID_MODE1_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE1', self.early_dt, self.LOOPPID_MODE1_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE1', self.dt, self.LOOPPID_MODE1[key])
                #             self.LOOPPID_MODE1_buffer[key] = self.LOOPPID_MODE1[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #
                #     for key in self.LOOPPID_MODE2:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.LOOPPID_MODE2[key] != self.LOOPPID_MODE2_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE2', self.early_dt, self.LOOPPID_MODE2_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE2', self.dt, self.LOOPPID_MODE2[key])
                #             self.LOOPPID_MODE2_buffer[key] = self.LOOPPID_MODE2[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #
                #     for key in self.LOOPPID_MODE3:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.LOOPPID_MODE3[key] != self.LOOPPID_MODE3_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE3', self.early_dt, self.LOOPPID_MODE3_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE3', self.dt, self.LOOPPID_MODE3[key])
                #             self.LOOPPID_MODE3_buffer[key] = self.LOOPPID_MODE3[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #
                #     # if no changes, write the data every fixed time interval
                #     # print(6)
                #     if self.para_LOOPPID >= self.rate_LOOPPID:
                #         for key in self.LOOPPID_EN:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_EN', self.dt, self.LOOPPID_EN[key])
                #             self.LOOPPID_EN_buffer[key] = self.LOOPPID_EN[key]
                #         for key in self.LOOPPID_MODE0:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE0', self.dt, self.LOOPPID_MODE0[key])
                #             self.LOOPPID_MODE0_buffer[key] = self.LOOPPID_MODE0[key]
                #         for key in self.LOOPPID_MODE1:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE1', self.dt, self.LOOPPID_MODE1[key])
                #             self.LOOPPID_MODE1_buffer[key] = self.LOOPPID_MODE1[key]
                #         for key in self.LOOPPID_MODE2:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE2', self.dt, self.LOOPPID_MODE2[key])
                #             self.LOOPPID_MODE2_buffer[key] = self.LOOPPID_MODE2[key]
                #         for key in self.LOOPPID_MODE3:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE3', self.dt, self.LOOPPID_MODE3[key])
                #             self.LOOPPID_MODE3_buffer[key] = self.LOOPPID_MODE3[key]
                #         # write float data.
                #         for key in self.LOOPPID_OUT:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_OUT', self.dt, self.LOOPPID_OUT[key])
                #             self.LOOPPID_OUT_buffer[key] = self.LOOPPID_OUT[key]
                #         for key in self.LOOPPID_IN:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_IN', self.dt, self.LOOPPID_IN[key])
                #             self.LOOPPID_IN_buffer[key] = self.LOOPPID_IN[key]
                #         self.commit_bool = True
                #         self.para_LOOPPID = 0
                #     # print(7)
                #
                #     for key in self.LOOP2PT_OUT:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.LOOP2PT_OUT[key] != self.LOOP2PT_OUT_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_OUT', self.early_dt, self.LOOP2PT_OUT_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_OUT', self.dt, self.LOOP2PT_OUT[key])
                #             self.LOOP2PT_OUT_buffer[key] = self.LOOP2PT_OUT[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #
                #     for key in self.LOOP2PT_MODE0:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.LOOP2PT_MODE0[key] != self.LOOP2PT_MODE0_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE0', self.early_dt, self.LOOP2PT_MODE0_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE0', self.dt, self.LOOP2PT_MODE0[key])
                #             self.LOOP2PT_MODE0_buffer[key] = self.LOOP2PT_MODE0[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #
                #     for key in self.LOOP2PT_MODE1:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.LOOP2PT_MODE1[key] != self.LOOP2PT_MODE1_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE1', self.early_dt, self.LOOP2PT_MODE1_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE1', self.dt, self.LOOP2PT_MODE1[key])
                #             self.LOOP2PT_MODE1_buffer[key] = self.LOOP2PT_MODE1[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #     for key in self.LOOP2PT_MODE2:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.LOOP2PT_MODE2[key] != self.LOOP2PT_MODE2_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE2', self.early_dt, self.LOOP2PT_MODE2_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE2', self.dt, self.LOOP2PT_MODE2[key])
                #             self.LOOP2PT_MODE2_buffer[key] = self.LOOP2PT_MODE2[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #     for key in self.LOOP2PT_MODE3:
                #         # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
                #         if self.LOOP2PT_MODE3[key] != self.LOOP2PT_MODE3_buffer[key]:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE3', self.early_dt, self.LOOP2PT_MODE3_buffer[key])
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE3', self.dt, self.LOOP2PT_MODE3[key])
                #             self.LOOP2PT_MODE3_buffer[key] = self.LOOP2PT_MODE3[key]
                #             self.commit_bool = True
                #             # print(self.Valve_OUT[key])
                #         else:
                #             pass
                #     if self.para_LOOP2PT >= self.rate_LOOP2PT:
                #
                #         for key in self.LOOP2PT_MODE0:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE0', self.dt, self.LOOP2PT_MODE0[key])
                #             self.LOOP2PT_MODE0_buffer[key] = self.LOOP2PT_MODE0[key]
                #         for key in self.LOOP2PT_MODE1:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE1', self.dt, self.LOOP2PT_MODE1[key])
                #             self.LOOP2PT_MODE1_buffer[key] = self.LOOP2PT_MODE1[key]
                #         for key in self.LOOP2PT_MODE2:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE2', self.dt, self.LOOP2PT_MODE2[key])
                #             self.LOOP2PT_MODE2_buffer[key] = self.LOOP2PT_MODE2[key]
                #         for key in self.LOOP2PT_MODE3:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_MODE3', self.dt, self.LOOP2PT_MODE3[key])
                #             self.LOOP2PT_MODE3_buffer[key] = self.LOOP2PT_MODE3[key]
                #         # write float data.
                #         for key in self.LOOP2PT_OUT:
                #             self.db.insert_data_into_datastorage_wocommit(key + '_OUT', self.dt, self.LOOP2PT_OUT[key])
                #             self.LOOP2PT_OUT_buffer[key] = self.LOOP2PT_OUT[key]
                #
                #         self.commit_bool = True
                #         self.para_LOOP2PT = 0
                #
                #
                #     if self.para_REAL >= self.rate_REAL:
                #         for key in self.LEFT_REAL_address:
                #             # print(key, self.LEFT_REAL_dic[key])
                #             self.db.insert_data_into_datastorage_wocommit(key, self.dt, self.LEFT_REAL_dic[key])
                #         # print("write pressure transducer")
                #             self.commit_bool = True
                #         self.para_REAL = 0
                #
                #     # print("a",self.para_TT,"b",self.para_PT )
                #     # print(8)
                #
                #     #commit the changes at last step only if it is time to write
                #     if self.commit_bool:
                #         self.db.db.commit()
                #     print("Wrting PLC data to database...")
                #     self.para_alarm += 1
                #
                #     self.para_TT += 1
                #     self.para_PT += 1
                #     self.para_Valve += 1
                #     self.para_Switch += 1
                #     self.para_LOOPPID += 1
                #     self.para_LOOP2PT += 1
                #     self.para_REAL += 1
                #     self.para_Din += 1
                #     # self.PLC.NewData_Database = False
                #     self.status = False
                #
                # else:
                #     if self.Running_pointer >= self.Running_counts:
                #         self.DB_ERROR_SIG.emit(
                #             "DATA LOST: Mysql hasn't received the data from PLC for ~10 minutes. Please check them.")
                #         raise Exception("")
                #         self.Running_pointer = 0
                #     # print("pointer",self.Running_pointer)
                #     self.Running_pointer += 1
                #
                #     print("No new data from PLC")
                #     pass
                self.db.insert_data_into_datastorage(2,self.dt, 2)
                # self.db.update_data_into_datastorage(2, self.dt, 2)
                time.sleep(self.base_period*30)
                # raise Exception("Test breakup")
            except Exception as e:
                print(e)
                # self.DB_ERROR_SIG.emit(e)
                self.DB_ERROR_SIG.emit("There is some ERROR in writing slowcontrol database. Please check it.")
                time.sleep(self.longsleep)
                continue



    @QtCore.Slot()
    def stop(self):
        self.Running = False

    @QtCore.Slot(object)
    def update_value(self,dic):
        # print("Database received the data from PLC")
        # print(dic)
        for key in self.TT_FP_dic:
            self.TT_FP_dic[key] = dic["TT_FP_dic"][key]

        for key in self.TT_BO_dic:
            self.TT_BO_dic[key] = dic["TT_BO_dic"][key]
        for key in self.PT_dic:
            self.PT_dic[key] = dic["PT_dic"][key]
        for key in self.TT_FP_HighLimit:
            self.TT_FP_HighLimit[key] = dic["TT_FP_HighLimit"][key]

        for key in self.TT_BO_HighLimit:
            self.TT_BO_HighLimit[key] = dic["TT_BO_HighLimit"][key]
        for key in self.PT_HighLimit:
            self.PT_HighLimit[key] = dic["PT_HighLimit"][key]
        for key in self.LEFT_REAL_HighLimit:
            self.LEFT_REAL_HighLimit[key] = dic["LEFT_REAL_HighLimit"][key]

        for key in self.TT_FP_LowLimit:
            self.TT_FP_LowLimit[key] = dic["TT_FP_LowLimit"][key]

        for key in self.TT_BO_LowLimit:
            self.TT_BO_LowLimit[key] = dic["TT_BO_LowLimit"][key]
        for key in self.PT_LowLimit:
            self.PT_LowLimit[key] = dic["PT_LowLimit"][key]
        for key in self.LEFT_REAL_LowLimit:
            self.LEFT_REAL_LowLimit[key] = dic["LEFT_REAL_LowLimit"][key]
        for key in self.LEFT_REAL_dic:
            self.LEFT_REAL_dic[key] = dic["LEFT_REAL_dic"][key]
        for key in self.Valve_OUT:
            self.Valve_OUT[key] = dic["Valve_OUT"][key]
        for key in self.Valve_INTLKD:
            self.Valve_INTLKD[key] = dic["Valve_INTLKD"][key]
        for key in self.Valve_MAN:
            self.Valve_MAN[key] = dic["Valve_MAN"][key]
        for key in self.Valve_ERR:
            self.Valve_ERR[key] = dic["Valve_ERR"][key]
        for key in self.Switch_OUT:
            self.Switch_OUT[key] = dic["Switch_OUT"][key]
        for key in self.Switch_INTLKD:
            self.Switch_INTLKD[key] = dic["Switch_INTLKD"][key]
        for key in self.Switch_MAN:
            self.Switch_MAN[key] = dic["Switch_MAN"][key]
        for key in self.Switch_ERR:
            self.Switch_ERR[key] = dic["Switch_ERR"][key]
        for key in self.Din_dic:
            self.Din_dic[key] = dic["Din_dic"][key]

        for key in self.TT_FP_Alarm:
            self.TT_FP_Alarm[key] = dic["TT_FP_Alarm"][key]
        for key in self.TT_BO_Alarm:
            self.TT_BO_Alarm[key] = dic["TT_BO_Alarm"][key]
        for key in self.PT_dic:
            self.PT_Alarm[key] = dic["PT_Alarm"][key]
        for key in self.LEFT_REAL_dic:
            self.LEFT_REAL_Alarm[key] = dic["LEFT_REAL_Alarm"][key]
        for key in self.LOOPPID_MODE0:
            self.LOOPPID_MODE0[key] = dic["LOOPPID_MODE0"][key]
        for key in self.LOOPPID_MODE1:
            self.LOOPPID_MODE1[key] = dic["LOOPPID_MODE1"][key]
        for key in self.LOOPPID_MODE2:
            self.LOOPPID_MODE2[key] = dic["LOOPPID_MODE2"][key]
        for key in self.LOOPPID_MODE3:
            self.LOOPPID_MODE3[key] = dic["LOOPPID_MODE3"][key]
        for key in self.LOOPPID_INTLKD:
            self.LOOPPID_INTLKD[key] = dic["LOOPPID_INTLKD"][key]
        for key in self.LOOPPID_MAN:
            self.LOOPPID_MAN[key] = dic["LOOPPID_MAN"][key]
        for key in self.LOOPPID_ERR:
            self.LOOPPID_ERR[key] = dic["LOOPPID_ERR"][key]
        for key in self.LOOPPID_SATHI:
            self.LOOPPID_SATHI[key] = dic["LOOPPID_SATHI"][key]
        for key in self.LOOPPID_SATLO:
            self.LOOPPID_SATLO[key] = dic["LOOPPID_SATLO"][key]
        for key in self.LOOPPID_EN:
            self.LOOPPID_EN[key] = dic["LOOPPID_EN"][key]
        for key in self.LOOPPID_OUT:
            self.LOOPPID_OUT[key] = dic["LOOPPID_OUT"][key]
        for key in self.LOOPPID_IN:
            self.LOOPPID_IN[key] = dic["LOOPPID_IN"][key]
        for key in self.LOOPPID_HI_LIM:
            self.LOOPPID_HI_LIM[key] = dic["LOOPPID_HI_LIM"][key]
        for key in self.LOOPPID_LO_LIM:
            self.LOOPPID_LO_LIM[key] = dic["LOOPPID_LO_LIM"][key]
        for key in self.LOOPPID_SET0:
            self.LOOPPID_SET0[key] = dic["LOOPPID_SET0"][key]
        for key in self.LOOPPID_SET1:
            self.LOOPPID_SET1[key] = dic["LOOPPID_SET1"][key]
        for key in self.LOOPPID_SET2:
            self.LOOPPID_SET2[key] = dic["LOOPPID_SET2"][key]
        for key in self.LOOPPID_SET3:
            self.LOOPPID_SET3[key] = dic["LOOPPID_SET3"][key]

        for key in self.LOOP2PT_OUT:
            self.LOOP2PT_OUT[key] = dic["LOOP2PT_OUT"][key]
        for key in self.LOOP2PT_SET0:
            self.LOOP2PT_SET0[key] = dic["LOOP2PT_SET0"][key]
        for key in self.LOOP2PT_SET1:
            self.LOOP2PT_SET1[key] = dic["LOOP2PT_SET1"][key]
        for key in self.LOOP2PT_SET2:
            self.LOOP2PT_SET2[key] = dic["LOOP2PT_SET2"][key]
        for key in self.LOOP2PT_SET3:
            self.LOOP2PT_SET3[key] = dic["LOOP2PT_SET3"][key]

        for key in self.Procedure_running:
            self.Procedure_running[key] = dic["Procedure_running"][key]
        for key in self.Procedure_INTLKD:
            self.Procedure_INTLKD[key] = dic["Procedure_INTLKD"][key]
        for key in self.Procedure_EXIT:
            self.Procedure_EXIT[key] = dic["Procedure_EXIT"][key]

        self.MainAlarm = dic["MainAlarm"]
        print("Database received the data from PLC")

    @QtCore.Slot(bool)
    def update_status(self, status):
        self.status= status




# Class to read PLC value every 2 sec
class UpdatePLC(QtCore.QObject):
    AI_slack_alarm = QtCore.Signal(str)

    def __init__(self, PLC, parent=None):
        super().__init__(parent)

        self.PLC = PLC
        # self.message_manager = message_manager()
        self.Running = False
        self.period = 1
        self.TT_FP_para = 0
        self.TT_FP_rate = 30
        self.TT_BO_para = 0
        self.TT_BO_rate = 30
        self.PT_para = 0
        self.PT_rate = 30
        self.PR_CYCLE_para = 0
        self.PR_CYCLE_rate = 30
        self.LEFT_REAL_para = 0
        self.LEFT_REAL_rate = 30

    @QtCore.Slot()
    def run(self):
        try:
            self.Running = True

            while self.Running:
                print("PLC updating", datetime.datetime.now())
                self.PLC.ReadAll()
                # test signal
                # self.AI_slack_alarm.emit("signal")
                for keyTT_FP in self.PLC.TT_FP_dic:
                    self.check_TT_FP_alarm(keyTT_FP)
                for keyTT_BO in self.PLC.TT_BO_dic:
                    self.check_TT_BO_alarm(keyTT_BO)
                for keyPT in self.PLC.PT_dic:
                    self.check_PT_alarm(keyPT)
                for keyLEFT_REAL in self.PLC.LEFT_REAL_dic:
                    self.check_LEFT_REAL_alarm(keyLEFT_REAL)
                self.or_alarm_signal()
                time.sleep(self.period)
        except KeyboardInterrupt:
            print("PLC is interrupted by keyboard[Ctrl-C]")
            self.stop()
        except:
            (type, value, traceback) = sys.exc_info()
            exception_hook(type, value, traceback)

    @QtCore.Slot()
    def stop(self):
        self.Running = False

    # def pressure_cycle(self):
    #     if self.PR_CYCLE_para >= self.PR_CYCLE_rate:
    #         self.PLC.

    def check_TT_FP_alarm(self, pid):

        if self.PLC.TT_FP_Activated[pid]:
            if float(self.PLC.TT_FP_LowLimit[pid]) > float(self.PLC.TT_FP_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if float(self.PLC.TT_FP_dic[pid]) < float(self.PLC.TT_FP_LowLimit[pid]):
                    self.TTFPalarmmsg(pid)

                    # print(pid , " reading is lower than the low limit")
                elif float(self.PLC.TT_FP_dic[pid]) > float(self.PLC.TT_FP_HighLimit[pid]):
                    self.TTFPalarmmsg(pid)

                    # print(pid,  " reading is higher than the high limit")
                else:
                    self.resetTTFPalarmmsg(pid)
                    # print(pid, " is in normal range")

        else:
            self.resetTTFPalarmmsg(pid)
            pass

    def check_TT_BO_alarm(self, pid):

        if self.PLC.TT_BO_Activated[pid]:
            if float(self.PLC.TT_BO_LowLimit[pid]) > float(self.PLC.TT_BO_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if float(self.PLC.TT_BO_dic[pid]) < float(self.PLC.TT_BO_LowLimit[pid]):
                    self.TTBOalarmmsg(pid)

                    # print(pid , " reading is lower than the low limit")
                elif float(self.PLC.TT_BO_dic[pid]) > float(self.PLC.TT_BO_HighLimit[pid]):
                    self.TTBOalarmmsg(pid)

                    # print(pid,  " reading is higher than the high limit")
                else:
                    self.resetTTBOalarmmsg(pid)
                    # print(pid, " is in normal range")

        else:
            self.resetTTBOalarmmsg(pid)
            pass

    def check_PT_alarm(self, pid):

        if self.PLC.PT_Activated[pid]:
            if float(self.PLC.PT_LowLimit[pid]) > float(self.PLC.PT_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if float(self.PLC.PT_dic[pid]) < float(self.PLC.PT_LowLimit[pid]):
                    self.PTalarmmsg(pid)

                    # print(pid , " reading is lower than the low limit")
                elif float(self.PLC.PT_dic[pid]) > float(self.PLC.PT_HighLimit[pid]):
                    self.PTalarmmsg(pid)
                    # print(pid,  " reading is higher than the high limit")
                else:
                    self.resetPTalarmmsg(pid)
                    # print(pid, " is in normal range")

        else:
            self.resetPTalarmmsg(pid)
            pass

    def check_LEFT_REAL_alarm(self, pid):

        if self.PLC.LEFT_REAL_Activated[pid]:
            if float(self.PLC.LEFT_REAL_LowLimit[pid]) > float(self.PLC.LEFT_REAL_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if float(self.PLC.LEFT_REAL_dic[pid]) < float(self.PLC.LEFT_REAL_LowLimit[pid]):
                    self.LEFT_REALalarmmsg(pid)

                    # print(pid , " reading is lower than the low limit")
                elif float(self.PLC.LEFT_REAL_dic[pid]) > float(self.PLC.LEFT_REAL_HighLimit[pid]):
                    self.LEFT_REALalarmmsg(pid)
                    # print(pid,  " reading is higher than the high limit")
                else:
                    self.resetLEFT_REALalarmmsg(pid)
                    # print(pid, " is in normal range")

        else:
            self.resetLEFT_REALalarmmsg(pid)
            pass

    def TTFPalarmmsg(self, pid):
        self.PLC.TT_FP_Alarm[pid] = True
        # and send email or slack messages
        # every time interval send a alarm message
        print(self.TT_FP_para)
        if self.TT_FP_para >= self.TT_FP_rate:
            msg = "SBC alarm: {pid} is out of range: CURRENT VALUE: {current}, HI_LIM: {high}, LO_LIM: {low}".format(pid=pid, current=self.PLC.TT_FP_dic[pid],
                                                                                                                     high=self.PLC.TT_FP_HighLimit[pid], low=self.PLC.TT_FP_LowLimit[pid])
            # self.message_manager.tencent_alarm(msg)
            # self.message_manager.slack_alarm(msg)
            self.AI_slack_alarm.emit(msg)
            self.TT_FP_para = 0
        self.TT_FP_para += 1

    def resetTTFPalarmmsg(self, pid):
        self.PLC.TT_FP_Alarm[pid] = False
        # self.TT_FP_para = 0
        # and send email or slack messages

    def TTBOalarmmsg(self, pid):
        self.PLC.TT_BO_Alarm[pid] = True
        # and send email or slack messages
        print(self.TT_BO_para)
        if self.TT_BO_para >= self.TT_BO_rate:
            msg = "SBC alarm: {pid} is out of range: CURRENT VALUE: {current}, HI_LIM: {high}, LO_LIM: {low}".format(pid=pid, current=self.PLC.TT_BO_dic[pid],
                                                                                                                     high=self.PLC.TT_BO_HighLimit[pid], low=self.PLC.TT_BO_LowLimit[pid])
            # self.message_manager.tencent_alarm(msg)
            # self.message_manager.slack_alarm(msg)
            self.AI_slack_alarm.emit(msg)
            self.TT_BO_para = 0

        self.TT_BO_para += 1

    def resetTTBOalarmmsg(self, pid):
        self.PLC.TT_BO_Alarm[pid] = False
        # self.TT_BO_para = 0
        # and send email or slack messages

    def PTalarmmsg(self, pid):
        self.PLC.PT_Alarm[pid] = True
        # and send email or slack messages
        if self.PT_para >= self.PT_rate:
            msg = "SBC alarm: {pid} is out of range: CURRENT VALUE: {current}, HI_LIM: {high}, LO_LIM: {low}".format(pid=pid, current=self.PLC.PT_dic[pid],
                                                                                                                     high=self.PLC.PT_HighLimit[pid], low=self.PLC.PT_LowLimit[pid])

            # self.message_manager.tencent_alarm(msg)
            # self.message_manager.slack_alarm(msg)
            self.AI_slack_alarm.emit(msg)
            self.PT_para = 0
        self.PT_para += 1

    def resetPTalarmmsg(self, pid):
        self.PLC.PT_Alarm[pid] = False
        # self.PT_para = 0
        # and send email or slack messages

    def LEFT_REALalarmmsg(self, pid):
        self.PLC.LEFT_REAL_Alarm[pid] = True
        # and send email or slack messages
        if self.LEFT_REAL_para >= self.LEFT_REAL_rate:
            msg = "SBC alarm: {pid} is out of range: CURRENT VALUE: {current}, HI_LIM: {high}, LO_LIM: {low}".format(pid=pid, current=self.PLC.LEFT_REAL_dic[pid],
                                                                                                                     high=self.PLC.LEFT_REAL_HighLimit[pid], low=self.PLC.LEFT_REAL_LowLimit[pid])

            # self.message_manager.tencent_alarm(msg)
            # self.message_manager.slack_alarm(msg)
            self.AI_slack_alarm.emit(msg)
            self.LEFT_REAL_para = 0
        self.LEFT_REAL_para += 1

    def resetLEFT_REALalarmmsg(self, pid):
        self.PLC.LEFT_REAL_Alarm[pid] = False
        # self.LEFT_REAL_para = 0
        # and send email or slack messages

    def or_alarm_signal(self):
        if (True in self.PLC.TT_BO_Alarm) or (True in self.PLC.PT_Alarm) or (True in self.PLC.TT_FP_Alarm) or (True in self.PLC.LEFT_REAL_Alarm):
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
        self.Running = False
        self.period = 1
        print("connect to the PLC server")

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
        self.LEFT_REAL_Activated_ini= sec.LEFT_REAL_ACTIVATED
        self.LEFT_REAL_Alarm_ini = sec.LEFT_REAL_ALARM
        self.MainAlarm_ini = sec.MAINALARM
        self.Valve_OUT_ini = sec.VALVE_OUT
        self.Valve_MAN_ini = sec.VALVE_MAN
        self.Valve_INTLKD_ini = sec.VALVE_INTLKD
        self.Valve_ERR_ini = sec.VALVE_ERR
        self.Switch_OUT_ini = sec.SWITCH_OUT
        self.Switch_MAN_ini = sec.SWITCH_MAN
        self.Switch_INTLKD_ini = sec.SWITCH_INTLKD
        self.Switch_ERR_ini = sec.SWITCH_ERR
        self.Din_dic_ini = sec.DIN_DIC
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

        self.Procedure_running_ini = sec.PROCEDURE_RUNNING
        self.Procedure_INTLKD_ini = sec.PROCEDURE_INTLKD
        self.Procedure_EXIT_ini = sec.PROCEDURE_EXIT

        self.data_dic = {"data": {"TT": {"FP": {"value": self.TT_FP_dic_ini, "high": self.TT_FP_HighLimit_ini, "low": self.TT_FP_LowLimit_ini},
                                         "BO": {"value": self.TT_BO_dic_ini, "high": self.TT_BO_HighLimit_ini, "low": self.TT_BO_LowLimit_ini}},
                                  "PT": {"value": self.PT_dic_ini, "high": self.PT_HighLimit_ini, "low": self.PT_LowLimit_ini},
                                  "LEFT_REAL": {"value": self.LEFT_REAL_ini, "high": self.LEFT_REAL_HighLimit_ini, "low": self.LEFT_REAL_LowLimit_ini},
                                  "Valve": {"OUT": self.Valve_OUT_ini,
                                            "INTLKD": self.Valve_INTLKD_ini,
                                            "MAN": self.Valve_MAN_ini,
                                            "ERR": self.Valve_ERR_ini},
                                  "Switch": {"OUT": self.Switch_OUT_ini,
                                             "INTLKD": self.Switch_INTLKD_ini,
                                             "MAN": self.Switch_MAN_ini,
                                             "ERR": self.Switch_ERR_ini},
                                  "Din": {'value': self.Din_dic_ini},
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
                                              "SET3": self.LOOPPID_SET3_ini},
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
                                              "SET3": self.LOOP2PT_SET3_ini},
                                  "Procedure": {"Running": self.Procedure_running_ini, "INTLKD": self.Procedure_INTLKD_ini, "EXIT": self.Procedure_EXIT_ini}},
                         "Alarm": {"TT": {"FP": self.TT_FP_Alarm_ini,
                                          "BO": self.TT_BO_Alarm_ini},
                                   "PT": self.PT_Alarm_ini,
                                   "LEFT_REAL": self.LEFT_REAL_Alarm_ini},
                         "MainAlarm": self.MainAlarm_ini}

        self.data_package = pickle.dumps(self.data_dic)

    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:
            print("refreshing the BKG-GUI communication server")
            # if True:
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
                print("BKG-GUI communication server stops")
                pass
            time.sleep(self.period)

    @QtCore.Slot()
    def stop(self):
        self.Running = False
        try:
            self.socket.send('bye')
            self.socket.recv()
        except:
            print("Error disconnecting.")
        self.socket.close()

    def pack_data(self):

        for key in self.PLC.TT_FP_dic:
            self.TT_FP_dic_ini[key] = self.PLC.TT_FP_dic[key]

        for key in self.PLC.TT_BO_dic:
            self.TT_BO_dic_ini[key] = self.PLC.TT_BO_dic[key]
        for key in self.PLC.PT_dic:
            self.PT_dic_ini[key] = self.PLC.PT_dic[key]
        for key in self.PLC.TT_FP_HighLimit:
            self.TT_FP_HighLimit_ini[key] = self.PLC.TT_FP_HighLimit[key]

        for key in self.PLC.TT_BO_HighLimit:
            self.TT_BO_HighLimit_ini[key] = self.PLC.TT_BO_HighLimit[key]
        for key in self.PLC.PT_HighLimit:
            self.PT_HighLimit_ini[key] = self.PLC.PT_HighLimit[key]
        for key in self.PLC.LEFT_REAL_HighLimit:
            self.LEFT_REAL_HighLimit_ini[key] = self.PLC.LEFT_REAL_HighLimit[key]

        for key in self.PLC.TT_FP_LowLimit:
            self.TT_FP_LowLimit_ini[key] = self.PLC.TT_FP_LowLimit[key]

        for key in self.PLC.TT_BO_LowLimit:
            self.TT_BO_LowLimit_ini[key] = self.PLC.TT_BO_LowLimit[key]
        for key in self.PLC.PT_LowLimit:
            self.PT_LowLimit_ini[key] = self.PLC.PT_LowLimit[key]
        for key in self.PLC.LEFT_REAL_LowLimit:
            self.LEFT_REAL_LowLimit_ini[key] = self.PLC.LEFT_REAL_LowLimit[key]
        for key in self.PLC.LEFT_REAL_dic:
            self.LEFT_REAL_ini[key] = self.PLC.LEFT_REAL_dic[key]
        for key in self.PLC.Valve_OUT:
            self.Valve_OUT_ini[key] = self.PLC.Valve_OUT[key]
        for key in self.PLC.Valve_INTLKD:
            self.Valve_INTLKD_ini[key] = self.PLC.Valve_INTLKD[key]
        for key in self.PLC.Valve_MAN:
            self.Valve_MAN_ini[key] = self.PLC.Valve_MAN[key]
        for key in self.PLC.Valve_ERR:
            self.Valve_ERR_ini[key] = self.PLC.Valve_ERR[key]
        for key in self.PLC.Switch_OUT:
            self.Switch_OUT_ini[key] = self.PLC.Switch_OUT[key]
        for key in self.PLC.Switch_INTLKD:
            self.Switch_INTLKD_ini[key] = self.PLC.Switch_INTLKD[key]
        for key in self.PLC.Switch_MAN:
            self.Switch_MAN_ini[key] = self.PLC.Switch_MAN[key]
        for key in self.PLC.Switch_ERR:
            self.Switch_ERR_ini[key] = self.PLC.Switch_ERR[key]
        for key in self.PLC.Din_dic:
            self.Din_dic_ini[key] = self.PLC.Din_dic[key]

        for key in self.PLC.TT_FP_Alarm:
            self.TT_FP_Alarm_ini[key] = self.PLC.TT_FP_Alarm[key]
        for key in self.PLC.TT_BO_Alarm:
            self.TT_BO_Alarm_ini[key] = self.PLC.TT_BO_Alarm[key]
        for key in self.PLC.PT_dic:
            self.PT_Alarm_ini[key] = self.PLC.PT_Alarm[key]
        for key in self.PLC.LEFT_REAL_dic:
            self.LEFT_REAL_Alarm_ini[key] = self.PLC.LEFT_REAL_Alarm[key]
        for key in self.PLC.LOOPPID_MODE0:
            self.LOOPPID_MODE0_ini[key] = self.PLC.LOOPPID_MODE0[key]
        for key in self.PLC.LOOPPID_MODE1:
            self.LOOPPID_MODE1_ini[key] = self.PLC.LOOPPID_MODE1[key]
        for key in self.PLC.LOOPPID_MODE2:
            self.LOOPPID_MODE2_ini[key] = self.PLC.LOOPPID_MODE2[key]
        for key in self.PLC.LOOPPID_MODE3:
            self.LOOPPID_MODE3_ini[key] = self.PLC.LOOPPID_MODE3[key]
        for key in self.PLC.LOOPPID_INTLKD:
            self.LOOPPID_INTLKD_ini[key] = self.PLC.LOOPPID_INTLKD[key]
        for key in self.PLC.LOOPPID_MAN:
            self.LOOPPID_MAN_ini[key] = self.PLC.LOOPPID_MAN[key]
        for key in self.PLC.LOOPPID_ERR:
            self.LOOPPID_ERR_ini[key] = self.PLC.LOOPPID_ERR[key]
        for key in self.PLC.LOOPPID_SATHI:
            self.LOOPPID_SATHI_ini[key] = self.PLC.LOOPPID_SATHI[key]
        for key in self.PLC.LOOPPID_SATLO:
            self.LOOPPID_SATLO_ini[key] = self.PLC.LOOPPID_SATLO[key]
        for key in self.PLC.LOOPPID_EN:
            self.LOOPPID_EN_ini[key] = self.PLC.LOOPPID_EN[key]
        for key in self.PLC.LOOPPID_OUT:
            self.LOOPPID_OUT_ini[key] = self.PLC.LOOPPID_OUT[key]
        for key in self.PLC.LOOPPID_IN:
            self.LOOPPID_IN_ini[key] = self.PLC.LOOPPID_IN[key]
        for key in self.PLC.LOOPPID_HI_LIM:
            self.LOOPPID_HI_LIM_ini[key] = self.PLC.LOOPPID_HI_LIM[key]
        for key in self.PLC.LOOPPID_LO_LIM:
            self.LOOPPID_LO_LIM_ini[key] = self.PLC.LOOPPID_LO_LIM[key]
        for key in self.PLC.LOOPPID_SET0:
            self.LOOPPID_SET0_ini[key] = self.PLC.LOOPPID_SET0[key]
        for key in self.PLC.LOOPPID_SET1:
            self.LOOPPID_SET1_ini[key] = self.PLC.LOOPPID_SET1[key]
        for key in self.PLC.LOOPPID_SET2:
            self.LOOPPID_SET2_ini[key] = self.PLC.LOOPPID_SET2[key]
        for key in self.PLC.LOOPPID_SET3:
            self.LOOPPID_SET3_ini[key] = self.PLC.LOOPPID_SET3[key]

        for key in self.PLC.LOOP2PT_MODE0:
            self.LOOP2PT_MODE0_ini[key] = self.PLC.LOOP2PT_MODE0[key]
        for key in self.PLC.LOOP2PT_MODE1:
            self.LOOP2PT_MODE1_ini[key] = self.PLC.LOOP2PT_MODE1[key]
        for key in self.PLC.LOOP2PT_MODE2:
            self.LOOP2PT_MODE2_ini[key] = self.PLC.LOOP2PT_MODE2[key]
        for key in self.PLC.LOOP2PT_MODE3:
            self.LOOP2PT_MODE3_ini[key] = self.PLC.LOOP2PT_MODE3[key]
        for key in self.PLC.LOOP2PT_INTLKD:
            self.LOOP2PT_INTLKD_ini[key] = self.PLC.LOOP2PT_INTLKD[key]
        for key in self.PLC.LOOP2PT_MAN:
            self.LOOP2PT_MAN_ini[key] = self.PLC.LOOP2PT_MAN[key]
        for key in self.PLC.LOOP2PT_ERR:
            self.LOOP2PT_ERR_ini[key] = self.PLC.LOOP2PT_ERR[key]
        for key in self.PLC.LOOP2PT_OUT:
            self.LOOP2PT_OUT_ini[key] = self.PLC.LOOP2PT_OUT[key]
        for key in self.PLC.LOOP2PT_SET1:
            self.LOOP2PT_SET1_ini[key] = self.PLC.LOOP2PT_SET1[key]
        for key in self.PLC.LOOP2PT_SET2:
            self.LOOP2PT_SET2_ini[key] = self.PLC.LOOP2PT_SET2[key]
        for key in self.PLC.LOOP2PT_SET3:
            self.LOOP2PT_SET3_ini[key] = self.PLC.LOOP2PT_SET3[key]

        for key in self.PLC.Procedure_running:
            self.Procedure_running_ini[key] = self.PLC.Procedure_running[key]
        for key in self.PLC.Procedure_INTLKD:
            self.Procedure_INTLKD_ini[key] = self.PLC.Procedure_INTLKD[key]
        for key in self.PLC.Procedure_EXIT:
            self.Procedure_EXIT_ini[key] = self.PLC.Procedure_EXIT[key]

        self.data_dic["MainAlarm"] = self.PLC.MainAlarm
        # print("pack",self.data_dic)
        # print("HTR6214 \n", "MODE0", self.data_dic["data"]["LOOPPID"]["MODE0"]["HTR6214"],
        #             "\n","MODE1", self.data_dic["data"]["LOOPPID"]["MODE1"]["HTR6214"],
        #             "\n","MODE2", self.data_dic["data"]["LOOPPID"]["MODE2"]["HTR6214"],
        #             "\n","MODE3", self.data_dic["data"]["LOOPPID"]["MODE3"]["HTR6214"],
        #             "\n","INTLKD", self.data_dic["data"]["LOOPPID"]["INTLKD"]["HTR6214"],
        #             "\n","MAN", self.data_dic["data"]["LOOPPID"]["MAN"]["HTR6214"],
        #             "\n","ERR", self.data_dic["data"]["LOOPPID"]["ERR"]["HTR6214"],
        #             "\n","SATHI", self.data_dic["data"]["LOOPPID"]["SATHI"]["HTR6214"],
        #             "\n","SATLO", self.data_dic["data"]["LOOPPID"]["SATLO"]["HTR6214"],
        #             "\n","EN", self.data_dic["data"]["LOOPPID"]["EN"]["HTR6214"],
        #             "\n","OUT", self.data_dic["data"]["LOOPPID"]["OUT"]["HTR6214"],
        #             "\n","IN", self.data_dic["data"]["LOOPPID"]["IN"]["HTR6214"],
        #             "\n","HI_LIM", self.data_dic["data"]["LOOPPID"]["HI_LIM"]["HTR6214"],
        #             "\n","LO_LIM", self.data_dic["data"]["LOOPPID"]["LO_LIM"]["HTR6214"],
        #             "\n","SET0", self.data_dic["data"]["LOOPPID"]["SET0"]["HTR6214"],
        #             "\n","SET1", self.data_dic["data"]["LOOPPID"]["SET1"]["HTR6214"],
        #             "\n","SET2", self.data_dic["data"]["LOOPPID"]["SET2"]["HTR6214"],
        #             "\n","SET3", self.data_dic["data"]["LOOPPID"]["SET3"]["HTR6214"])

        self.data_package = pickle.dumps(self.data_dic)

    def write_data(self):
        message = pickle.loads(self.socket.recv())
        print(message)
        if message == {}:
            pass
        else:
            for key in message:
                print(message[key]["type"])
                print(message[key]["type"] == "valve")
                if message[key]["type"] == "valve":
                    if message[key]["operation"] == "OPEN":
                        self.PLC.WriteBase2(address=message[key]["address"])
                    elif message[key]["operation"] == "CLOSE":
                        self.PLC.WriteBase4(address=message[key]["address"])
                    else:
                        pass
                if message[key]["type"] == "switch":
                    if message[key]["operation"] == "ON":
                        self.PLC.WriteBase2(address=message[key]["address"])
                    elif message[key]["operation"] == "OFF":
                        self.PLC.WriteBase4(address=message[key]["address"])
                    else:
                        pass
                elif message[key]["type"] == "TT":
                    if message[key]["server"] == "BO":
                        # Update is to decide whether write new Low/High limit values into bkg code
                        if message[key]["operation"]["Update"]:
                            self.PLC.TT_BO_Activated[key] = message[key]["operation"]["Act"]
                            self.PLC.TT_BO_LowLimit[key] = message[key]["operation"]["LowLimit"]
                            self.PLC.TT_BO_HighLimit[key] = message[key]["operation"]["HighLimit"]
                        else:
                            self.PLC.TT_BO_Activated[key] = message[key]["operation"]["Act"]

                    elif message[key]["server"] == "FP":
                        if message[key]["operation"]["Update"]:
                            self.PLC.TT_FP_Activated[key] = message[key]["operation"]["Act"]
                            self.PLC.TT_FP_LowLimit[key] = message[key]["operation"]["LowLimit"]
                            self.PLC.TT_FP_HighLimit[key] = message[key]["operation"]["HighLimit"]
                        else:
                            self.PLC.TT_FP_Activated[key] = message[key]["operation"]["Act"]
                    else:
                        pass
                elif message[key]["type"] == "PT":
                    if message[key]["server"] == "BO":
                        if message[key]["operation"]["Update"]:
                            self.PLC.PT_Activated[key] = message[key]["operation"]["Act"]
                            self.PLC.PT_LowLimit[key] = message[key]["operation"]["LowLimit"]
                            self.PLC.PT_HighLimit[key] = message[key]["operation"]["HighLimit"]
                        else:
                            self.PLC.PT_Activated[key] = message[key]["operation"]["Act"]
                    else:
                        pass
                elif message[key]["type"] == "LEFT":
                    if message[key]["server"] == "BO":
                        if message[key]["operation"]["Update"]:
                            self.PLC.LEFT_REAL_Activated[key] = message[key]["operation"]["Act"]
                            self.PLC.LEFT_REAL_LowLimit[key] = message[key]["operation"]["LowLimit"]
                            self.PLC.LEFT_REAL_HighLimit[key] = message[key]["operation"]["HighLimit"]
                        else:
                            self.PLC.LEFT_REAL_Activated[key] = message[key]["operation"]["Act"]
                    else:
                        pass
                elif message[key]["type"] == "Procedure":
                    if message[key]["server"] == "BO":
                        if message[key]["operation"]["Start"]:
                            self.PLC.WriteBase4(address=message[key]["address"])
                        elif message[key]["operation"]["Stop"]:
                            self.PLC.WriteBase8(address=message[key]["address"])
                        elif message[key]["operation"]["Abort"]:
                            self.PLC.WriteBase16(address=message[key]["address"])
                        else:
                            pass
                    else:
                        pass
                elif message[key]["type"] == "heater_power":
                    if message[key]["operation"] == "EN":
                        self.PLC.LOOPPID_OUT_ENA(address=message[key]["address"])
                    elif message[key]["operation"] == "DISEN":
                        self.PLC.LOOPPID_OUT_DIS(address=message[key]["address"])
                    else:
                        pass
                    #
                    # if message[key]["operation"] == "SETMODE":
                    #     self.PLC.LOOPPID_SET_MODE(address = message[key]["address"], mode = message[key]["value"])
                    # else:
                    #     pass
                elif message[key]["type"] == "heater_para":
                    if message[key]["operation"] == "SET0":
                        # self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode= 0)
                        self.PLC.LOOPPID_SETPOINT(address=message[key]["address"], setpoint=message[key]["value"]["SETPOINT"], mode=0)
                        # self.PLC.LOOPPID_HI_LIM(address=message[key]["address"], value=message[key]["value"]["HI_LIM"])
                        # self.PLC.LOOPPID_LO_LIM(address=message[key]["address"], value=message[key]["value"]["LO_LIM"])
                        self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["HI_LIM"])
                        self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["LO_LIM"])

                    elif message[key]["operation"] == "SET1":
                        # self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=1)
                        self.PLC.LOOPPID_SETPOINT(address=message[key]["address"], setpoint=message[key]["value"]["SETPOINT"], mode=1)
                        self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["HI_LIM"])
                        self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["LO_LIM"])
                    elif message[key]["operation"] == "SET2":
                        # self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=2)
                        self.PLC.LOOPPID_SETPOINT(address=message[key]["address"], setpoint=message[key]["value"]["SETPOINT"], mode=2)
                        self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["HI_LIM"])
                        self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["LO_LIM"])
                    elif message[key]["operation"] == "SET3":
                        # self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=3)
                        self.PLC.LOOPPID_SETPOINT(address=message[key]["address"], setpoint=message[key]["value"]["SETPOINT"], mode=3)
                        self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"], value=message[key]["value"]["HI_LIM"])
                        self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"], value=message[key]["value"]["LO_LIM"])
                    else:
                        pass

                elif message[key]["type"] == "heater_setmode":
                    if message[key]["operation"] == "SET0":
                        self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=0)

                    elif message[key]["operation"] == "SET1":
                        print(True)
                        self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=1)

                    elif message[key]["operation"] == "SET2":
                        self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=2)

                    elif message[key]["operation"] == "SET3":
                        self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=3)

                    else:
                        pass

                    # if message[key]["operation"] == "HI_LIM":
                    #     self.PLC.LOOPPID_HI_LIM(address= message[key]["address"], value = message[key]["value"])
                    # else:
                    #     pass
                    #
                    # if message[key]["operation"] == "LO_LIM":
                    #     self.PLC.LOOPPID_HI_LIM(address= message[key]["address"], value = message[key]["value"])

                elif message[key]["type"] == "LOOP2PT_power":
                    if message[key]["operation"] == "OPEN":
                        self.PLC.LOOP2PT_OPEN(address=message[key]["address"])
                    elif message[key]["operation"] == "CLOSE":
                        self.PLC.LOOPPID_CLOSE(address=message[key]["address"])
                    else:
                        pass
                elif message[key]["type"] == "LOOP2PT_para":

                    if message[key]["operation"] == "SET1":
                        # self.PLC.LOOP2PT_SET_MODE(address=message[key]["address"], mode=1)
                        self.PLC.LOOP2PT_SETPOINT(address=message[key]["address"], setpoint=message[key]["value"]["SETPOINT"], mode=1)

                    elif message[key]["operation"] == "SET2":
                        # self.PLC.LOOP2PT_SET_MODE(address=message[key]["address"], mode=2)
                        self.PLC.LOOP2PT_SETPOINT(address=message[key]["address"], setpoint=message[key]["value"]["SETPOINT"], mode=2)

                    elif message[key]["operation"] == "SET3":
                        # self.PLC.LOOP2PT_SET_MODE(address=message[key]["address"], mode=3)
                        self.PLC.LOOP2PT_SETPOINT(address=message[key]["address"], setpoint=message[key]["value"]["SETPOINT"], mode=3)
                    else:
                        pass

                elif message[key]["type"] == "LOOP2PT_setmode":
                    if message[key]["operation"] == "SET0":
                        self.PLC.LOOP2PT_SET_MODE(address=message[key]["address"], mode=0)

                    elif message[key]["operation"] == "SET1":
                        self.PLC.LOOP2PT_SET_MODE(address=message[key]["address"], mode=1)

                    elif message[key]["operation"] == "SET2":
                        self.PLC.LOOP2PT_SET_MODE(address=message[key]["address"], mode=2)

                    elif message[key]["operation"] == "SET3":
                        self.PLC.LOOP2PT_SET_MODE(address=message[key]["address"], mode=3)

                    else:
                        pass

                else:
                    pass

        # if message == b'this is a command':
        #     self.PLC.WriteBase2()
        #     self.PLC.Read_BO_1()
        #     print("I will set valve")
        # elif message == b'no command':
        #     self.PLC.WriteBase4()
        #     self.PLC.Read_BO_1()
        #     print("I will stay here")
        # elif message == b'this an anti_conmmand':
        #
        #     print("reset the valve")
        # else:
        #     print("I didn't see any command")
        #     pass


class Update(QtCore.QObject):
    PATCH_TO_DATABASE = QtCore.Signal()
    UPDATE_TO_DATABASE = QtCore.Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        os.system("date | tee -a /home/hep/Documents/cron-tutorial/output/daemon_test.txt")
        os.system("echo 'Update ' | tee -a /home/hep/Documents/cron-tutorial/output/daemon_test.txt")
        #error?
        App.aboutToQuit.connect(self.StopUpdater)
        self.StartUpdater()
        self.slack_signals()
        self.connect_signals()
        self.data_transfer = {}
        self.data_status = False


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
        self.UpDatabase = UpdateDataBase()
        # self.UpDatabase = UpdateDataBase(self.PLC)
        self.UpDatabase.moveToThread(self.DataUpdateThread)
        self.DataUpdateThread.started.connect(self.UpDatabase.run)
        self.DataUpdateThread.start()

        # time.sleep(2)

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

    @QtCore.Slot(str)
    def printstr(self, string):
        print(string)

    @QtCore.Slot(object)
    def transfer_station(self, data):
        self.data_transfer = data
        self.PATCH_TO_DATABASE.emit()
        # print(self.data_transfer)

    @QtCore.Slot(object)
    def PLCstatus_transfer(self, status):
        self.data_status = status
        self.UPDATE_TO_DATABASE.emit()
        print(self.data_status)

    def slack_signals(self):
        self.message_manager = message_manager()
        self.UpPLC.AI_slack_alarm.connect(self.printstr)

        self.UpPLC.AI_slack_alarm.connect(self.message_manager.slack_alarm)
        self.UpDatabase.DB_ERROR_SIG.connect(self.message_manager.slack_alarm)

    def connect_signals(self):
        # self.UpPLC.PLC.DATA_UPDATE_SIGNAL.connect(self.UpDatabase.update_value)
        self.UpPLC.PLC.DATA_UPDATE_SIGNAL.connect(self.transfer_station)
        self.PATCH_TO_DATABASE.connect(lambda: self.UpDatabase.update_value(self.data_transfer))

        self.UpPLC.PLC.DATA_TRI_SIGNAL.connect(self.PLCstatus_transfer)
        self.UPDATE_TO_DATABASE.connect(lambda: self.UpDatabase.update_status(self.data_status))
        print("signal established")





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

        # info about slack settings
        # SLACK_BOT_TOKEN is a linux enviromental variable saved locally on sbcslowcontrol mathine
        # it can be fetched on slack app page in SBCAlarm app: https://api.slack.com/apps/A035X77RW64/general
        self.client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
        self.logger = logging.getLogger(__name__)
        self.channel_id = "C01A549VDHS"

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

    @QtCore.Slot(str)
    def slack_alarm(self, message):
        # ID of channel you want to post message to

        try:
            # Call the conversations.list method using the WebClient
            result = self.client.chat_postMessage(
                channel=self.channel_id,
                text=str(message)
                # You could also use a blocks[] array to send richer content
            )
            # Print result, which includes information about the message (like TS)
            print(result)

        except SlackApiError as e:
            print(f"Error: {e}")
            # print(e)




if __name__ == "__main__":
    # msg_mana=message_manager()
    # msg_mana.tencent_alarm("this is a test message")

    # App = QtWidgets.QApplication(sys.argv)
    # PLC_body()
    #
    # # PLC=PLC()
    # # PLC.ReadAll()
    #
    # sys.exit(App.exec_())

    PLC_run()