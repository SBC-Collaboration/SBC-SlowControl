"""
Class PLC is used to read/write via modbus to the temperature PLC

To read the variable, just call the ReadAll() method
To write to a variable, call the proper setXXX() method

By: Mathieu Laurin

v1.0 Initial code 25/11/19 ML
v1.1 Initialize values, flag when values are updated more modbus variables 04/03/20 ML
"""

import struct, time, zmq, sys, pickle, copy, logging
import numpy as np
from PySide2 import QtWidgets, QtCore, QtGui
from Database_SBC import *
from email.mime.text import MIMEText
from email.header import Header
from smtplib import SMTP_SSL
import requests
import logging,os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import slowcontrol_env_cons as sec
import alarm_set as AS

# delete random number package when you read real data from PLC
import random
from pymodbus.client.sync import ModbusTcpClient



# Initialization of Address, Value Matrix

logging.basicConfig(filename="/home/hep/sbc_error_log.log")
sys._excepthook = sys.excepthook
def exception_hook(exctype, value, traceback):
    print("ExceptType: ", exctype, "Value: ", value, "Traceback: ", traceback)
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

class PLC(QtCore.QObject):
    DATA_UPDATE_SIGNAL=QtCore.Signal(object)
    DATA_TRI_SIGNAL = QtCore.Signal(bool)
    PLC_DISCON_SIGNAL = QtCore.Signal()
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

        # wait 1 second to init
        time.sleep(1)



        self.TT_FP_address = copy.copy(sec.TT_FP_ADDRESS)

        self.TT_BO_address = copy.copy(sec.TT_BO_ADDRESS)

        self.PT_address = copy.copy(sec.PT_ADDRESS)

        self.LEFT_REAL_address = copy.copy(sec.LEFT_REAL_ADDRESS)

        self.TT_FP_dic = copy.copy(sec.TT_FP_DIC)

        self.TT_BO_dic = copy.copy(sec.TT_BO_DIC)

        self.PT_dic = copy.copy(sec.PT_DIC)

        self.LEFT_REAL_dic = copy.copy(sec.LEFT_REAL_DIC)

        self.TT_FP_LowLimit = copy.copy(sec.TT_FP_LOWLIMIT)

        self.TT_FP_HighLimit = copy.copy(sec.TT_FP_HIGHLIMIT)

        self.TT_BO_LowLimit = copy.copy(sec.TT_BO_LOWLIMIT)

        self.TT_BO_HighLimit = copy.copy(sec.TT_BO_HIGHLIMIT)

        self.PT_LowLimit = copy.copy(sec.PT_LOWLIMIT)
        self.PT_HighLimit = copy.copy(sec.PT_HIGHLIMIT)

        self.LEFT_REAL_HighLimit = copy.copy(sec.LEFT_REAL_HIGHLIMIT)
        self.LEFT_REAL_LowLimit = copy.copy(sec.LEFT_REAL_LOWLIMIT)

        self.TT_FP_Activated = copy.copy(sec.TT_FP_ACTIVATED)

        self.TT_BO_Activated = copy.copy(sec.TT_BO_ACTIVATED)

        self.PT_Activated = copy.copy(sec.PT_ACTIVATED)
        self.LEFT_REAL_Activated = copy.copy(sec.LEFT_REAL_ACTIVATED)

        self.TT_FP_Alarm = copy.copy(sec.TT_FP_ALARM)

        self.TT_BO_Alarm = copy.copy(sec.TT_BO_ALARM)

        self.PT_Alarm = copy.copy(sec.PT_ALARM)
        self.LEFT_REAL_Alarm = copy.copy(sec.LEFT_REAL_ALARM)
        self.MainAlarm = copy.copy(sec.MAINALARM)
        self.MAN_SET = copy.copy(sec.MAN_SET)
        self.nTT_BO = copy.copy(sec.NTT_BO)
        self.nTT_FP = copy.copy(sec.NTT_FP)
        self.nPT = copy.copy(sec.NPT)
        self.nREAL = copy.copy(sec.NREAL)

        self.TT_BO_setting = copy.copy(sec.TT_BO_SETTING)
        self.nTT_BO_Attribute = copy.copy(sec.NTT_BO_ATTRIBUTE)
        self.PT_setting = copy.copy(sec.PT_SETTING)
        self.nPT_Attribute = copy.copy(sec.NPT_ATTRIBUTE)

        self.Switch_address = copy.copy(sec.SWITCH_ADDRESS)
        self.nSwitch = copy.copy(sec.NSWITCH)
        self.Switch = copy.copy(sec.SWITCH)
        self.Switch_OUT = copy.copy(sec.SWITCH_OUT)
        self.Switch_MAN = copy.copy(sec.SWITCH_MAN)
        self.Switch_INTLKD = copy.copy(sec.SWITCH_INTLKD)
        self.Switch_ERR = copy.copy(sec.SWITCH)

        self.Din_address = copy.copy(sec.DIN_ADDRESS)
        self.nDin = copy.copy(sec.NDIN)
        self.Din = copy.copy(sec.DIN)
        self.Din_dic = copy.copy(sec.DIN_DIC)
        self.Din_LowLimit = copy.copy(sec.DIN_LOWLIMIT)
        self.Din_HighLimit = copy.copy(sec.DIN_HIGHLIMIT)
        self.Din_Activated = copy.copy(sec.DIN_ACTIVATED)
        self.Din_Alarm = copy.copy(sec.DIN_ALARM)

        self.valve_address = copy.copy(sec.VALVE_ADDRESS)
        self.nValve = copy.copy(sec.NVALVE)
        self.Valve = copy.copy(sec.VALVE)
        self.Valve_OUT = copy.copy(sec.VALVE_OUT)
        self.Valve_MAN = copy.copy(sec.VALVE_MAN)
        self.Valve_INTLKD = copy.copy(sec.VALVE_INTLKD)
        self.Valve_ERR = copy.copy(sec.VALVE_ERR)
        self.Valve_Busy = copy.copy(sec.VALVE_BUSY)

        self.LOOPPID_ADR_BASE = copy.copy(sec.LOOPPID_ADR_BASE)

        self.LOOPPID_MODE0 = copy.copy(sec.LOOPPID_MODE0)

        self.LOOPPID_MODE1 = copy.copy(sec.LOOPPID_MODE1)

        self.LOOPPID_MODE2 = copy.copy(sec.LOOPPID_MODE2)

        self.LOOPPID_MODE3 = copy.copy(sec.LOOPPID_MODE3)

        self.LOOPPID_INTLKD = copy.copy(sec.LOOPPID_INTLKD)

        self.LOOPPID_MAN = copy.copy(sec.LOOPPID_MAN)

        self.LOOPPID_ERR = copy.copy(sec.LOOPPID_ERR)

        self.LOOPPID_SATHI = copy.copy(sec.LOOPPID_SATHI)

        self.LOOPPID_SATLO = copy.copy(sec.LOOPPID_SATLO)

        self.LOOPPID_EN = copy.copy(sec.LOOPPID_EN)

        self.LOOPPID_OUT = copy.copy(sec.LOOPPID_OUT)

        self.LOOPPID_IN = copy.copy(sec.LOOPPID_IN)

        self.LOOPPID_HI_LIM = copy.copy(sec.LOOPPID_HI_LIM)

        self.LOOPPID_LO_LIM = copy.copy(sec.LOOPPID_LO_LIM)

        self.LOOPPID_SET0 = copy.copy(sec.LOOPPID_SET0)

        self.LOOPPID_SET1 = copy.copy(sec.LOOPPID_SET1)

        self.LOOPPID_SET2 = copy.copy(sec.LOOPPID_SET2)

        self.LOOPPID_SET3 = copy.copy(sec.LOOPPID_SET3)
        self.LOOPPID_Busy = copy.copy(sec.LOOPPID_BUSY)
        self.LOOPPID_Activated = copy.copy(sec.LOOPPID_ACTIVATED)
        self.LOOPPID_Alarm = copy.copy(sec.LOOPPID_ALARM)
        self.LOOPPID_Alarm_HighLimit = copy.copy(sec.LOOPPID_ALARM_HI_LIM)
        self.LOOPPID_Alarm_LowLimit = copy.copy(sec.LOOPPID_ALARM_LO_LIM)
        # self.LOOPPID_ADR_BASE = sec.LOOPPID_ADR_BASE
        #
        # self.LOOPPID_MODE0 = sec.LOOPPID_MODE0
        #
        # self.LOOPPID_MODE1 = sec.LOOPPID_MODE1
        #
        # self.LOOPPID_MODE2 = sec.LOOPPID_MODE2
        #
        # self.LOOPPID_MODE3 = sec.LOOPPID_MODE3
        #
        # self.LOOPPID_INTLKD = sec.LOOPPID_INTLKD
        #
        # self.LOOPPID_MAN = sec.LOOPPID_MAN
        #
        # self.LOOPPID_ERR = sec.LOOPPID_ERR
        #
        # self.LOOPPID_SATHI = sec.LOOPPID_SATHI
        #
        # self.LOOPPID_SATLO = sec.LOOPPID_SATLO
        #
        # self.LOOPPID_EN = sec.LOOPPID_EN
        #
        # self.LOOPPID_OUT = sec.LOOPPID_OUT
        #
        # self.LOOPPID_IN = sec.LOOPPID_IN
        #
        # self.LOOPPID_HI_LIM = sec.LOOPPID_HI_LIM
        #
        # self.LOOPPID_LO_LIM = sec.LOOPPID_LO_LIM
        #
        # self.LOOPPID_SET0 = sec.LOOPPID_SET0
        #
        # self.LOOPPID_SET1 = sec.LOOPPID_SET1
        #
        # self.LOOPPID_SET2 = sec.LOOPPID_SET2
        #
        # self.LOOPPID_SET3 = sec.LOOPPID_SET3
        # self.LOOPPID_Busy = sec.LOOPPID_BUSY

        self.LOOP2PT_ADR_BASE = copy.copy(sec.LOOP2PT_ADR_BASE)
        self.LOOP2PT_MODE0 = copy.copy(sec.LOOP2PT_MODE0)
        self.LOOP2PT_MODE1 = copy.copy(sec.LOOP2PT_MODE1)
        self.LOOP2PT_MODE2 = copy.copy(sec.LOOP2PT_MODE2)
        self.LOOP2PT_MODE3 = copy.copy(sec.LOOP2PT_MODE3)
        self.LOOP2PT_INTLKD  = copy.copy(sec.LOOP2PT_INTLKD)
        self.LOOP2PT_MAN = copy.copy(sec.LOOP2PT_MAN)
        self.LOOP2PT_ERR = copy.copy(sec.LOOP2PT_ERR)
        self.LOOP2PT_OUT = copy.copy(sec.LOOP2PT_OUT)
        self.LOOP2PT_SET1 = copy.copy(sec.LOOP2PT_SET1)
        self.LOOP2PT_SET2 = copy.copy(sec.LOOP2PT_SET2)
        self.LOOP2PT_SET3 = copy.copy(sec.LOOP2PT_SET3)
        self.LOOP2PT_Busy =  copy.copy(sec.LOOP2PT_BUSY)

        self.Procedure_address = copy.copy(sec.PROCEDURE_ADDRESS)
        self.Procedure_running = copy.copy(sec.PROCEDURE_RUNNING)
        self.Procedure_INTLKD = copy.copy(sec.PROCEDURE_INTLKD)
        self.Procedure_EXIT = copy.copy(sec.PROCEDURE_EXIT)

        self.INTLK_D_ADDRESS = copy.copy(sec.INTLK_D_ADDRESS)
        self.INTLK_D_DIC = copy.copy(sec.INTLK_D_DIC)
        self.INTLK_D_EN = copy.copy(sec.INTLK_D_EN)
        self.INTLK_D_COND = copy.copy(sec.INTLK_D_COND)
        self.INTLK_D_Busy = copy.copy(sec.INTLK_D_BUSY)
        self.INTLK_A_ADDRESS = copy.copy(sec.INTLK_A_ADDRESS)
        self.INTLK_A_DIC = copy.copy(sec.INTLK_A_DIC)
        self.INTLK_A_EN = copy.copy(sec.INTLK_A_EN)
        self.INTLK_A_COND = copy.copy(sec.INTLK_A_COND)
        self.INTLK_A_SET = copy.copy(sec.INTLK_A_SET)
        self.INTLK_A_Busy = copy.copy(sec.INTLK_A_BUSY)

        self.FLAG_ADDRESS = copy.copy(sec.FLAG_ADDRESS)
        self.FLAG_DIC = copy.copy(sec.FLAG_DIC)
        self.FLAG_INTLKD = copy.copy(sec.FLAG_INTLKD)
        self.FLAG_Busy = copy.copy(sec.FLAG_BUSY)

        self.FF_ADDRESS = copy.copy(sec.FF_ADDRESS)
        self.FF_DIC = copy.copy(sec.FF_DIC)

        self.PARAM_F_ADDRESS = copy.copy(sec.PARAM_F_ADDRESS)
        self.PARAM_F_DIC = copy.copy(sec.PARAM_F_DIC)

        self.PARAM_I_ADDRESS = copy.copy(sec.PARAM_I_ADDRESS)
        self.PARAM_I_DIC = copy.copy(sec.PARAM_I_DIC)

        self.PARAM_B_ADDRESS = copy.copy(sec.PARAM_B_ADDRESS)
        self.PARAM_B_DIC = copy.copy(sec.PARAM_B_DIC)

        self.PARAM_T_ADDRESS = copy.copy(sec.PARAM_T_ADDRESS)
        self.PARAM_T_DIC = copy.copy(sec.PARAM_T_DIC)

        self.TIME_ADDRESS = copy.copy(sec.TIME_ADDRESS)
        self.TIME_DIC = copy.copy(sec.TIME_DIC)


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
                              "MAN_SET":self.MAN_SET,
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
                              "Din_LowLimit":self.Din_LowLimit,
                              "Din_HighLimit":self.Din_HighLimit,
                              "Din_Alarm": self.Din_Alarm,
                              "valve_address":self.valve_address,
                              "nValve":self.nValve,
                              "Valve":self.Valve,
                              "Valve_OUT":self.Valve_OUT,
                              "Valve_MAN":self.Valve_MAN,
                              "Valve_INTLKD":self.Valve_INTLKD,
                              "Valve_ERR":self.Valve_ERR,
                              "Valve_Busy":self.Valve_Busy,
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
                              "LOOPPID_Busy":self.LOOPPID_Busy,
                              "LOOPPID_Alarm": self.LOOPPID_Alarm,
                              "LOOPPID_Alarm_HighLimit":self.LOOPPID_Alarm_HighLimit,
                              "LOOPPID_Alarm_LowLimit":self.LOOPPID_Alarm_LowLimit,
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
                              "LOOP2PT_Busy":self.LOOP2PT_Busy,
                              "Procedure_address":self.Procedure_address,
                              "Procedure_running":self.Procedure_running,
                              "Procedure_INTLKD":self.Procedure_INTLKD,
                              "Procedure_EXIT":self.Procedure_EXIT,
                              "INTLK_D_ADDRESS":self.INTLK_D_ADDRESS,
                              "INTLK_D_DIC": self.INTLK_D_DIC,
                              "INTLK_D_EN":self.INTLK_D_EN,
                              "INTLK_D_COND":self.INTLK_D_COND,
                              "INTLK_D_Busy":self.INTLK_D_Busy,
                              "INTLK_A_ADDRESS":self.INTLK_A_ADDRESS,
                              "INTLK_A_DIC": self.INTLK_A_DIC,
                              "INTLK_A_EN":self.INTLK_A_EN,
                              "INTLK_A_COND":self.INTLK_A_COND,
                              "INTLK_A_SET":self.INTLK_A_SET,
                              "INTLK_A_Busy":self.INTLK_A_Busy,
                              "FLAG_ADDRESS":self.FLAG_ADDRESS,
                              "FLAG_DIC":self.FLAG_DIC,
                              "FLAG_INTLKD":self.FLAG_INTLKD,
                              "FLAG_Busy":self.FLAG_Busy,
                              "FF_ADDRESS": self.FF_ADDRESS,
                              "FF_DIC": self.FF_DIC,
                              "PARAM_F_ADDRESS": self.PARAM_F_ADDRESS,
                              "PARAM_F_DIC": self.PARAM_F_DIC,
                              "PARAM_I_ADDRESS": self.PARAM_I_ADDRESS,
                              "PARAM_I_DIC": self.PARAM_I_DIC,
                              "PARAM_B_ADDRESS": self.PARAM_B_ADDRESS,
                              "PARAM_B_DIC": self.PARAM_B_DIC,
                              "PARAM_T_ADDRESS": self.PARAM_T_ADDRESS,
                              "PARAM_T_DIC": self.PARAM_T_DIC,
                              "TIME_ADDRESS": self.TIME_ADDRESS,
                              "TIME_DIC": self.TIME_DIC}

        self.load_alarm_config()

        self.LiveCounter = 0
        self.NewData_Display = False
        self.NewData_Database = False
        self.NewData_ZMQ = False

    def __del__(self):
        self.Client.close()
        self.Client_BO.close()

    def load_alarm_config(self):
        self.Connected = self.Client.connect()
        self.Connected_BO = self.Client_BO.connect()
        if self.Connected_BO:
            self.alarm_config = AS.Alarm_Setting()
            self.alarm_config.read_Information()
            for key in self.TT_FP_HighLimit:
                try:
                    self.TT_FP_HighLimit[key] = self.alarm_config.high_dic[key]
                except:
                    pass
            for key in self.TT_BO_HighLimit:
                try:
                    self.TT_BO_HighLimit[key] = self.alarm_config.high_dic[key]
                except:
                    pass
            for key in self.PT_HighLimit:
                try:
                    self.PT_HighLimit[key] = self.alarm_config.high_dic[key]
                except:
                    pass
            for key in self.LEFT_REAL_HighLimit:
                try:
                    self.LEFT_REAL_HighLimit[key] = self.alarm_config.high_dic[key]
                except:
                    pass

            for key in self.TT_FP_LowLimit:
                try:
                    self.TT_FP_LowLimit[key] = self.alarm_config.low_dic[key]
                except:
                    pass
            for key in self.TT_BO_LowLimit:
                try:
                    self.TT_BO_LowLimit[key] = self.alarm_config.low_dic[key]
                except:
                    pass
            for key in self.PT_LowLimit:
                try:
                    self.PT_LowLimit[key] = self.alarm_config.low_dic[key]
                except:
                    pass
            for key in self.LEFT_REAL_LowLimit:
                try:
                    self.LEFT_REAL_LowLimit[key] = self.alarm_config.low_dic[key]
                except:
                    pass

            for key in self.TT_FP_Activated:
                try:
                    self.TT_FP_Activated[key] = self.alarm_config.active_dic[key]
                except:
                    pass
            for key in self.TT_BO_Activated:
                try:
                    self.TT_BO_Activated[key] = self.alarm_config.active_dic[key]
                except:
                    pass
            for key in self.PT_Activated:
                try:
                    self.PT_Activated[key] = self.alarm_config.active_dic[key]
                except:
                    pass

            for key in self.LEFT_REAL_Activated:
                try:
                    self.LEFT_REAL_Activated[key] = self.alarm_config.active_dic[key]
                except:
                    pass

            for key in self.Din_LowLimit:
                try:
                    self.Din_LowLimit[key] = self.alarm_config.low_dic[key]
                except:
                    pass
            for key in self.Din_HighLimit:
                try:
                    self.Din_HighLimit[key] = self.alarm_config.high_dic[key]
                except:
                    pass
            for key in self.Din_Activated:
                try:
                    self.Din_Activated[key] = self.alarm_config.active_dic[key]
                except:
                    pass

            for key in self.LOOPPID_Alarm_LowLimit:
                # self.LOOPPID_SET_LO_LIM(address=self.LOOPPID_ADR_BASE[key],
                #                         value=self.alarm_config.low_dic[key])
                try:
                    self.LOOPPID_Alarm_LowLimit[key] = self.alarm_config.low_dic[key]
                except:
                    pass

            for key in self.LOOPPID_Alarm_HighLimit:
                try:
                # self.LOOPPID_SET_HI_LIM(address=self.LOOPPID_ADR_BASE[key],
                #                         value=self.alarm_config.high_dic[key])
                    self.LOOPPID_Alarm_HighLimit[key] = self.alarm_config.high_dic[key]
                except:
                    pass

            for key in self.LOOPPID_Activated:
                try:
                    self.LOOPPID_Activated[key] = self.alarm_config.active_dic[key]
                except:
                    pass
        else:
            self.PLC_DISCON_SIGNAL.emit()
            # raise Exception('Not connected to PLC')  # will it restart the PLC ?

            return 1

    def ReadAll(self):
        # print(self.TT_BO_HighLimit["TT2119"])
        # print(self.TT_BO_Alarm["TT2119"])
        self.Connected = self.Client.connect()
        self.Connected_BO = self.Client_BO.connect()

        if self.Connected:
            # Reading all the RTDs
            Raw_RTDs_FP = {}
            for key in self.TT_FP_address:
                Raw_RTDs_FP[key] = self.Client.read_holding_registers(self.TT_FP_address[key], count=2, unit=0x01)
                # also transform C into K if value is not NULL
                read_value = round(struct.unpack("<f", struct.pack("<HH", Raw_RTDs_FP[key].getRegister(1), Raw_RTDs_FP[key].getRegister(0)))[0], 3)
                if read_value < 849:

                    self.TT_FP_dic[key] = 273.15 + read_value
                else:
                    self.TT_FP_dic[key] = read_value
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
        else:
            print("lost connection to PLC")
            self.PLC_DISCON_SIGNAL.emit()


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
                self.Valve_Busy[key] = self.ReadCoil(2, self.valve_address[key]) or self.ReadCoil(4, self.valve_address[key])
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

                self.LOOPPID_Busy[key] = self.ReadCoil(2**13, self.LOOPPID_ADR_BASE[key]) or self.ReadCoil(2**14,self.LOOPPID_ADR_BASE[key])

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
                self.LOOP2PT_Busy[key] = self.ReadCoil(2 ** 1, self.LOOP2PT_ADR_BASE[key]) or self.ReadCoil(
                    2 ** 2, self.LOOP2PT_ADR_BASE[key])


            ############################################################################################
            # procedure
            Raw_Procedure = {}
            Raw_Procedure_OUT = {}
            for key in self.Procedure_address:
                Raw_Procedure[key] = self.Client_BO.read_holding_registers(self.Procedure_address[key] + 1, count=1, unit=0x01)

                self.Procedure_running[key] = self.ReadCoil(1, self.Procedure_address[key])
                self.Procedure_INTLKD[key] = self.ReadCoil(2, self.Procedure_address[key])
                self.Procedure_EXIT[key] = Raw_Procedure[key].getRegister(0)


            ##################################################################################################
            Raw_INTLK_A = {}
            for key in self.INTLK_A_ADDRESS:
                Raw_INTLK_A[key] = self.Client_BO.read_holding_registers(self.INTLK_A_ADDRESS[key] + 2, count=2, unit=0x01)
                self.INTLK_A_SET[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_INTLK_A[key].getRegister(1),
                                                    Raw_INTLK_A[key].getRegister(0)))[0], 3)
                self.INTLK_A_DIC[key] = self.ReadCoil(1, self.INTLK_A_ADDRESS[key])
                self.INTLK_A_EN[key] = self.ReadCoil(2 ** 1 , self.INTLK_A_ADDRESS[key])
                self.INTLK_A_COND[key] = self.ReadCoil(2 ** 2, self.INTLK_A_ADDRESS[key])
                self.INTLK_A_Busy[key] = self.ReadCoil(2 ** 2, self.INTLK_A_ADDRESS[key]) or self.ReadCoil(
                    2 ** 3, self.INTLK_A_ADDRESS[key])


            for key in self.INTLK_D_ADDRESS:

                self.INTLK_D_DIC[key] = self.ReadCoil(1, self.INTLK_D_ADDRESS[key])
                self.INTLK_D_EN[key] = self.ReadCoil(2 ** 1, self.INTLK_D_ADDRESS[key])
                self.INTLK_D_COND[key] = self.ReadCoil(2 ** 2, self.INTLK_D_ADDRESS[key])
                self.INTLK_D_Busy[key] = self.ReadCoil(2 ** 2, self.INTLK_D_ADDRESS[key]) or self.ReadCoil(
                    2 ** 3, self.INTLK_D_ADDRESS[key])


            ############################################################################################
            #FLAG
            for key in self.FLAG_ADDRESS:
                self.FLAG_DIC[key] = self.ReadCoil(1, self.FLAG_ADDRESS[key])
                # print("\n",self.FLAG_DIC,"\n")
                self.FLAG_INTLKD[key] = self.ReadCoil(2 ** 3, self.FLAG_ADDRESS[key])
                self.FLAG_Busy[key] = self.ReadCoil(2 ** 1, self.FLAG_ADDRESS[key]) or self.ReadCoil(
                    2 ** 2, self.FLAG_ADDRESS[key])

                # print("MAN",key, self.ReadCoil(2 ** 2, self.FLAG_ADDRESS[key]) or self.ReadCoil(2 ** 3, self.FLAG_ADDRESS[key]))
                # print("OUT",self.FLAG_DIC[key])
                # print("INTLKC", self.FLAG_INTLKD[key])
            print("PLC FLAG",self.FLAG_DIC,datetime.datetime.now())



            #######################################################################################################

            ##FF
            Raw_FF = {}
            for key in self.FF_ADDRESS:
                Raw_FF[key] = self.Client_BO.read_holding_registers(self.FF_ADDRESS[key], count=2, unit=0x01)
                self.FF_DIC[key] = struct.unpack(">I", struct.pack(">HH", Raw_FF[key].getRegister(1),Raw_FF[key].getRegister(0)))[0]
                
            # print("FF",self.FF_DIC)



            ## PARAMETER
            Raw_PARAM_F= {}
            for key in self.PARAM_F_ADDRESS:
                Raw_PARAM_F[key] = self.Client_BO.read_holding_registers(self.PARAM_F_ADDRESS[key], count=2, unit=0x01)
                self.PARAM_F_DIC[key] = struct.unpack(">f", struct.pack(">HH", Raw_PARAM_F[key].getRegister(1), Raw_PARAM_F[key].getRegister(0)))[0]

            # print("PARAM_F", self.PARAM_F_DIC)

            Raw_PARAM_I = {}
            for key in self.PARAM_I_ADDRESS:
                Raw_PARAM_I[key] = self.Client_BO.read_holding_registers(self.PARAM_I_ADDRESS[key], count=1, unit=0x01)
                self.PARAM_I_DIC[key] = Raw_PARAM_I[key].getRegister(0)

            # print("PARAM_I", self.PARAM_I_DIC)

            for key in self.PARAM_B_ADDRESS:

                self.PARAM_B_DIC[key] = self.ReadCoil(2 ** (self.PARAM_B_ADDRESS[key][1]), self.PARAM_B_ADDRESS[key][0])

            # print("PARAM_B", self.PARAM_B_DIC)
            
            Raw_PARAM_T = {}
            for key in self.PARAM_T_ADDRESS:
                Raw_PARAM_T[key] = self.Client_BO.read_holding_registers(self.PARAM_T_ADDRESS[key], count=2, unit=0x01)
                self.PARAM_T_DIC[key] = struct.unpack(">I", struct.pack(">HH", Raw_PARAM_T[key].getRegister(1), Raw_PARAM_T[key].getRegister(0)))[0]

            # print("PARAM_T", self.PARAM_T_DIC)



            ###TIME
            Raw_TIME = {}
            for key in self.TIME_ADDRESS:
                Raw_TIME[key] = self.Client_BO.read_holding_registers(self.TIME_ADDRESS[key], count=2, unit=0x01)
                self.TIME_DIC[key] = struct.unpack(">I", struct.pack(">HH", Raw_TIME[key].getRegister(1), Raw_TIME[key].getRegister(0)))[0]
            # print("TIME", self.TIME_DIC)
            




            #########################################################################################################







            ##########################################################################################################

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

            # print(self.LOOP2PT_MAN)
            self.DATA_UPDATE_SIGNAL.emit(self.signal_data)
            self.DATA_TRI_SIGNAL.emit(True)
            # print("signal sent")
            # print(True,'\n',True,"\n",True,"\n")
            self.NewData_Display = True
            self.NewData_Database = True
            self.NewData_ZMQ = True

            return 0
        else:
            self.PLC_DISCON_SIGNAL.emit()
            # raise Exception('Not connected to PLC')  # will it restart the PLC ?

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

    def int16_to_word(self, value):
        try:
            it = int(value)
            x = np.arange(it, it + 1, dtype='<i2')
            if len(x) == 1:
                word = x.tobytes()
            else:
                print("ERROR in float to words")
            return word
        except:
            return 0

    def int32_to_2words(self, value):
        try:
            it = int(value)
            x = np.arange(it, it + 1, dtype='<i4')
            if len(x) == 1:
                word = x.tobytes()
                piece1, piece2 = struct.unpack('<HH', word)
            else:
                print("ERROR in float to words")
            return piece1, piece2
        except:
            return 0


    def Write_BO_2(self, address, value):
        word1, word2 = self.float_to_2words(value)
        print('words', word1, word2)
        # pay attention to endian relationship
        Raw1 = self.Client_BO.write_register(address, value=word1, unit=0x01)
        Raw2 = self.Client_BO.write_register(address + 1, value=word2, unit=0x01)

        print("write result = ", Raw1, Raw2)

    def Write_BO_2_int16(self, address, value):
        word = self.int16_to_word(value)
        print('word', word)
        # pay attention to endian relationship
        Raw = self.Client_BO.write_register(address, value=word, unit=0x01)

        print("write result = ", Raw)
    def Write_BO_2_int32(self, address, value):
        word1, word2 = self.int32_to_2words(value)
        print('words', word1, word2)
        # pay attention to endian relationship
        Raw1 = self.Client_BO.write_register(address, value=word1, unit=0x01)
        Raw2 = self.Client_BO.write_register(address + 1, value=word2, unit=0x01)

        print("write result = ", Raw1, Raw2)

    # def Write_BO_2(self, address, value):
    #     word1, word2 = self.float_to_2words(value)
    #     print('words', word1, word2)
    #     # pay attention to endian relationship
    #     Raw1 = self.Client_BO.write_register(address, value=word1, unit=0x01)
    #     Raw2 = self.Client_BO.write_register(address + 1, value=word2, unit=0x01)
    #
    #     print("write result = ", Raw1, Raw2)

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

    def WriteBase32(self, address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x0020
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write base32 result=", Raw)

    def WriteFF(self, address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x8000
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write FF result=", Raw)

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
        self.db = mydatabase()
        self.alarm_db = COUPP_database()
        self.Running = False
        # if loop runs with _counts times with New_Database = False(No written Data), then send alarm to slack. Otherwise, the code normally run(reset the pointer)
        self.Running_counts = 600
        self.Running_pointer = 0
        self.longsleep = 60

        self.base_period = 1

        self.COUPP_ERROR = False
        self.COUPP_ALARM = "k"
        self.COUPP_HOLD = True

        self.para_alarm = 0
        self.rate_alarm = 10
        self.para_TT = 0
        self.rate_TT = 3
        self.para_PT = 0
        self.rate_PT = 3
        self.para_REAL = 0
        self.rate_REAL = 3
        self.para_Din = 0
        self.rate_Din = 90
        # c is for valve status
        self.para_Valve = 0
        self.rate_Valve = 90
        self.para_Switch = 0
        self.rate_Switch = 90
        self.para_LOOPPID = 0
        self.rate_LOOPPID = 5
        self.para_LOOP2PT = 0
        self.rate_LOOP2PT = 90
        self.para_FLAG=0
        self.rate_FLAG=90
        self.para_INTLK_A=0
        self.rate_INTLK_A = 90
        self.para_INTLK_D = 0
        self.rate_INTLK_D = 90
        self.para_FF = 0
        self.rate_FF = 90
        self.para_PARAM_F = 0
        self.rate_PARAM_F = 90
        self.para_PARAM_I = 0
        self.rate_PARAM_I = 90
        self.para_PARAM_B = 0
        self.rate_PARAM_B = 90
        self.para_PARAM_T = 0
        self.rate_PARAM_T = 90
        self.para_TIME = 0
        self.rate_TIME = 90

        #status initialization
        self.status = False

        #commit initialization
        self.commit_bool = False
        # INITIALIZATION
        self.TT_FP_address = copy.copy(sec.TT_FP_ADDRESS)
        self.TT_BO_address = copy.copy(sec.TT_BO_ADDRESS)
        self.PT_address = copy.copy(sec.PT_ADDRESS)
        self.LEFT_REAL_address = copy.copy(sec.LEFT_REAL_ADDRESS)
        self.TT_FP_dic = copy.copy(sec.TT_FP_DIC)
        self.TT_BO_dic = copy.copy(sec.TT_BO_DIC)
        self.PT_dic = copy.copy(sec.PT_DIC)
        self.LEFT_REAL_dic = copy.copy(sec.LEFT_REAL_DIC)
        self.TT_FP_LowLimit = copy.copy(sec.TT_FP_LOWLIMIT)
        self.TT_FP_HighLimit = copy.copy(sec.TT_FP_HIGHLIMIT)
        self.TT_BO_LowLimit = copy.copy(sec.TT_BO_LOWLIMIT)
        self.TT_BO_HighLimit = copy.copy(sec.TT_BO_HIGHLIMIT)

        self.PT_LowLimit = copy.copy(sec.PT_LOWLIMIT)
        self.PT_HighLimit = copy.copy(sec.PT_HIGHLIMIT)
        self.LEFT_REAL_HighLimit= copy.copy(sec.LEFT_REAL_HIGHLIMIT)
        self.LEFT_REAL_LowLimit = copy.copy(sec.LEFT_REAL_LOWLIMIT)
        self.TT_FP_Activated = copy.copy(sec.TT_FP_ACTIVATED)
        self.TT_BO_Activated = copy.copy(sec.TT_BO_ACTIVATED)
        self.PT_Activated = copy.copy(sec.PT_ACTIVATED)
        self.LEFT_REAL_Activated = copy.copy(sec.LEFT_REAL_ACTIVATED)

        self.TT_FP_Alarm = copy.copy(sec.TT_FP_ALARM)
        self.TT_BO_Alarm = copy.copy(sec.TT_BO_ALARM)
        self.PT_Alarm = copy.copy(sec.PT_ALARM)
        self.LEFT_REAL_Alarm = copy.copy(sec.LEFT_REAL_ALARM)
        self.MainAlarm = copy.copy(sec.MAINALARM)
        self.MAN_SET = copy.copy(sec.MAN_SET)
        self.nTT_BO = copy.copy(sec.NTT_BO)
        self.nTT_FP = copy.copy(sec.NTT_FP)
        self.nPT = copy.copy(sec.NPT)
        self.nREAL = copy.copy(sec.NREAL)

        self.TT_BO_setting = copy.copy(sec.TT_BO_SETTING)
        self.nTT_BO_Attribute = copy.copy(sec.NTT_BO_ATTRIBUTE)
        self.PT_setting = copy.copy(sec.PT_SETTING)
        self.nPT_Attribute = copy.copy(sec.NPT_ATTRIBUTE)

        self.Switch_address = copy.copy(sec.SWITCH_ADDRESS)
        self.nSwitch = copy.copy(sec.NSWITCH)
        self.Switch = copy.copy(sec.SWITCH)
        self.Switch_OUT = copy.copy(sec.SWITCH_OUT)
        self.Switch_MAN = copy.copy(sec.SWITCH_MAN)
        self.Switch_INTLKD = copy.copy(sec.SWITCH_INTLKD)
        self.Switch_ERR = copy.copy(sec.SWITCH_ERR)
        self.Din_address = copy.copy(sec.DIN_ADDRESS)
        self.nDin = copy.copy(sec.NDIN)
        self.Din = copy.copy(sec.DIN)
        self.Din_dic = copy.copy(sec.DIN_DIC)
        self.valve_address = copy.copy(sec.VALVE_ADDRESS)
        self.nValve = copy.copy(sec.NVALVE)
        self.Valve = copy.copy(sec.VALVE)
        self.Valve_OUT = copy.copy(sec.VALVE_OUT)
        self.Valve_MAN = copy.copy(sec.VALVE_MAN)
        self.Valve_INTLKD = copy.copy(sec.VALVE_INTLKD)
        self.Valve_ERR = copy.copy(sec.VALVE_ERR)
        self.LOOPPID_ADR_BASE = copy.copy(sec.LOOPPID_ADR_BASE)
        self.LOOPPID_MODE0 = copy.copy(sec.LOOPPID_MODE0)
        self.LOOPPID_MODE1 = copy.copy(sec.LOOPPID_MODE1)
        self.LOOPPID_MODE2 = copy.copy(sec.LOOPPID_MODE2)
        self.LOOPPID_MODE3 = copy.copy(sec.LOOPPID_MODE3)
        self.LOOPPID_INTLKD = copy.copy(sec.LOOPPID_INTLKD)
        self.LOOPPID_MAN = copy.copy(sec.LOOPPID_MAN)
        self.LOOPPID_ERR = copy.copy(sec.LOOPPID_ERR)
        self.LOOPPID_SATHI = copy.copy(sec.LOOPPID_SATHI)
        self.LOOPPID_SATLO = copy.copy(sec.LOOPPID_SATLO)
        self.LOOPPID_EN = copy.copy(sec.LOOPPID_EN)
        self.LOOPPID_OUT = copy.copy(sec.LOOPPID_OUT)
        self.LOOPPID_IN = copy.copy(sec.LOOPPID_IN)
        self.LOOPPID_HI_LIM = copy.copy(sec.LOOPPID_HI_LIM)
        self.LOOPPID_LO_LIM = copy.copy(sec.LOOPPID_LO_LIM)
        self.LOOPPID_SET0 = copy.copy(sec.LOOPPID_SET0)
        self.LOOPPID_SET1 = copy.copy(sec.LOOPPID_SET1)
        self.LOOPPID_SET2 = copy.copy(sec.LOOPPID_SET2)
        self.LOOPPID_SET3 = copy.copy(sec.LOOPPID_SET3)
        self.LOOP2PT_ADR_BASE = copy.copy(sec.LOOP2PT_ADR_BASE)
        self.LOOP2PT_MODE0 = copy.copy(sec.LOOP2PT_MODE0)
        self.LOOP2PT_MODE1 = copy.copy(sec.LOOP2PT_MODE1)
        self.LOOP2PT_MODE2 = copy.copy(sec.LOOP2PT_MODE2)
        self.LOOP2PT_MODE3 = copy.copy(sec.LOOP2PT_MODE3)
        self.LOOP2PT_INTLKD = copy.copy(sec.LOOP2PT_INTLKD)
        self.LOOP2PT_MAN = copy.copy(sec.LOOP2PT_MAN)
        self.LOOP2PT_ERR = copy.copy(sec.LOOP2PT_ERR)
        self.LOOP2PT_OUT = copy.copy(sec.LOOP2PT_OUT)
        self.LOOP2PT_SET1 = copy.copy(sec.LOOP2PT_SET1)
        self.LOOP2PT_SET2 = copy.copy(sec.LOOP2PT_SET2)
        self.LOOP2PT_SET3 = copy.copy(sec.LOOP2PT_SET3)
        self.Procedure_address = copy.copy(sec.PROCEDURE_ADDRESS)
        self.Procedure_running = copy.copy(sec.PROCEDURE_RUNNING)
        self.Procedure_INTLKD = copy.copy(sec.PROCEDURE_INTLKD)
        self.Procedure_EXIT = copy.copy(sec.PROCEDURE_EXIT)
        # self.INTLK_D_ADDRESS = copy.copy(sec.INTLK_D_ADDRESS)
        # self.INTLK_D_DIC = copy.copy(sec.INTLK_D_DIC)
        # self.INTLK_D_EN = copy.copy(sec.INTLK_D_EN)
        # self.INTLK_D_COND = copy.copy(sec.INTLK_D_COND)
        # self.INTLK_A_ADDRESS = copy.copy(sec.INTLK_A_ADDRESS)
        # self.INTLK_A_DIC = copy.copy(sec.INTLK_A_DIC)
        # self.INTLK_A_EN = copy.copy(sec.INTLK_A_EN)
        # self.INTLK_A_COND = copy.copy(sec.INTLK_A_COND)
        # self.INTLK_A_SET = copy.copy(sec.INTLK_A_SET)
        #
        self.FLAG_ADDRESS = copy.copy(sec.FLAG_ADDRESS)
        self.FLAG_DIC = copy.copy(sec.FLAG_DIC)
        self.FLAG_INTLKD = copy.copy(sec.FLAG_INTLKD)
        self.FLAG_Busy =copy.copy(sec.FLAG_BUSY)

        self.FF_ADDRESS = copy.copy(sec.FF_ADDRESS)
        self.FF_DIC = copy.copy(sec.FF_DIC)

        self.PARAM_F_ADDRESS = copy.copy(sec.PARAM_F_ADDRESS)
        self.PARAM_F_DIC = copy.copy(sec.PARAM_F_DIC)
        self.PARAM_I_ADDRESS = copy.copy(sec.PARAM_I_ADDRESS)
        self.PARAM_I_DIC = copy.copy(sec.PARAM_I_DIC)
        self.PARAM_B_ADDRESS = copy.copy(sec.PARAM_B_ADDRESS)
        self.PARAM_B_DIC = copy.copy(sec.PARAM_B_DIC)
        self.PARAM_T_ADDRESS = copy.copy(sec.PARAM_T_ADDRESS)
        self.PARAM_T_DIC = copy.copy(sec.PARAM_T_DIC)
        self.TIME_ADDRESS = copy.copy(sec.TIME_ADDRESS)
        self.TIME_DIC = copy.copy(sec.TIME_DIC)



        # BUFFER parts
        self.Valve_buffer = copy.copy(sec.VALVE_OUT)
        self.Switch_buffer = copy.copy(sec.SWITCH_OUT)
        self.Din_buffer = copy.copy(sec.DIN_DIC)
        self.LOOPPID_EN_buffer = copy.copy(sec.LOOPPID_EN)
        self.LOOPPID_MODE0_buffer = copy.copy(sec.LOOPPID_MODE0)
        self.LOOPPID_MODE1_buffer = copy.copy(sec.LOOPPID_MODE1)
        self.LOOPPID_MODE2_buffer = copy.copy(sec.LOOPPID_MODE2)
        self.LOOPPID_MODE3_buffer = copy.copy(sec.LOOPPID_MODE3)
        self.LOOPPID_OUT_buffer = copy.copy(sec.LOOPPID_OUT)
        self.LOOPPID_IN_buffer = copy.copy(sec.LOOPPID_IN)


        self.LOOP2PT_MODE0_buffer = copy.copy(sec.LOOP2PT_MODE0)
        self.LOOP2PT_MODE1_buffer = copy.copy(sec.LOOP2PT_MODE1)
        self.LOOP2PT_MODE2_buffer = copy.copy(sec.LOOP2PT_MODE2)
        self.LOOP2PT_MODE3_buffer = copy.copy(sec.LOOP2PT_MODE3)
        self.LOOP2PT_OUT_buffer = copy.copy(sec.LOOP2PT_OUT)

        self.FLAG_INTLKD_buffer = copy.copy(sec.FLAG_INTLKD)

        self.FF_buffer = copy.copy(sec.FF_DIC)
        self.PARAM_B_buffer = copy.copy(sec.PARAM_B_DIC)



        print("begin updating Database")

    @QtCore.Slot()
    def run(self):

        self.Running = True
        while self.Running:
            try:
                self.dt = datetime_in_1e5micro()
                self.early_dt = early_datetime()
                print("Database Updating", self.dt)
                print("earlytime", self.early_dt)

            except Exception as e:
                print(e)
                logging.error(e)
                print(e)

            # if self.PLC.NewData_Database:
            if self.status:
                self.Running_pointer = 0
                try:
                    # print(0)
                    # print(self.para_alarm)
                    # print("ALARM:\n", "\n", self.COUPP_ALARM)
                    if self.para_alarm >= self.rate_alarm:

                    # if coupp alarm is blank which only comes from the PLC module, then write ok status
                    # if coupp alarm is "k", which means no new data from PLC module, then keep the previous status: if previous was ok, then update the ok, if it was alarm, then do nothing. waiting for next command from PLC
                    #if coupp alarm is neither blank nor k, then it should be a alarm from PLC module, so write the alarm to the COUPP database.



                        if self.COUPP_ALARM == "":
                            self.COUPP_ERROR = True
                            self.alarm_db.ssh_write()
                            # if the ssh write fails, the ERROR will be True
                            self.COUPP_ERROR = False
                            self.para_alarm = 0
                        elif self.COUPP_ALARM == "k":
                                if self.alarm_db.ssh_state_only()=="OK":
                                    self.COUPP_ERROR = True
                                    self.alarm_db.ssh_write()
                                    # if the ssh write fails, the ERROR will be True
                                    self.COUPP_ERROR = False
                                    self.para_alarm = 0
                                elif self.alarm_db.ssh_state_only()=="ALARM":
                                    self.COUPP_ERROR = True
                                    self.COUPP_ERROR = False
                                    self.para_alarm = 0


                        else:
                            self.COUPP_ERROR = True
                            self.alarm_db.ssh_alarm(message=self.COUPP_ALARM)
                            self.COUPP_ERROR = False
                            self.para_alarm = 0
                        if not self.COUPP_HOLD:
                            self.COUPP_ALARM = "k"


                except Exception as e:
                    if self.COUPP_ERROR == True:
                        self.DB_ERROR_SIG.emit("Failed to update PICO watchdog Database.")
                        self.COUPP_ERROR = False
                    print(e)
                    logging.error(e)



                try:
                    self.write_data()
                except Exception as e:
                    # self.DB_ERROR_SIG.emit(e)
                    print(e)
                    logging.error(e)
                    self.DB_ERROR_SIG.emit("There is some ERROR in writing slowcontrol database. Please check it.")

                    time.sleep(self.longsleep)


                self.status = False

            else:
                if self.Running_pointer >= self.Running_counts:
                    self.DB_ERROR_SIG.emit(
                        "DATA LOST: Mysql hasn't received the data from PLC for ~10 minutes. Please check them.")
                    self.Running_pointer = 0
                # print("pointer",self.Running_pointer)
                self.Running_pointer += 1

                print("No new data from PLC")

            time.sleep(self.base_period)
            # raise Exception("Test breakup")
            


    @QtCore.Slot()
    def stop(self):
        self.Running = False

    @QtCore.Slot()
    def receive_COUPP_ALARM(self, string):
        self.COUPP_HOLD = True
        self.COUPP_ALARM = string

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
        for key in self.FLAG_DIC:
            self.FLAG_DIC[key] = dic["FLAG_DIC"][key]
        for key in self.FLAG_INTLKD:
            self.FLAG_INTLKD[key] = dic["FLAG_INTLKD"][key]
        for key in self.FF_DIC:
            self.FF_DIC[key] = dic["FF_DIC"][key]
        for key in self.PARAM_F_DIC:
            self.PARAM_F_DIC[key] = dic["PARAM_F_DIC"][key]
        for key in self.PARAM_I_DIC:
            self.PARAM_I_DIC[key] = dic["PARAM_I_DIC"][key]
        for key in self.PARAM_B_DIC:
            self.PARAM_B_DIC[key] = dic["PARAM_B_DIC"][key]
        for key in self.PARAM_T_DIC:
            self.PARAM_T_DIC[key] = dic["PARAM_T_DIC"][key]
        for key in self.TIME_DIC:
            self.TIME_DIC[key] = dic["TIME_DIC"][key]

        self.MainAlarm = dic["MainAlarm"]
        self.MAN_SET = dic["MAN_SET"]
        print("Database received the data from PLC")

    @QtCore.Slot(bool)
    def update_status(self, status):
        self.status= status

    def write_data(self):
        if self.para_TT >= self.rate_TT:
            for key in self.TT_FP_dic:
                self.db.insert_data_into_stack(key, self.dt, self.TT_FP_dic[key])
            for key in self.TT_BO_dic:
                self.db.insert_data_into_stack(key, self.dt, self.TT_BO_dic[key])
            # print("write RTDS")
            self.commit_bool = True
            self.para_TT = 0
        # print(1)
        if self.para_PT >= self.rate_PT:
            for key in self.PT_dic:
                self.db.insert_data_into_stack(key, self.dt, self.PT_dic[key])
            # print("write pressure transducer")
            self.commit_bool = True
            self.para_PT = 0
        # print(2)
        for key in self.Valve_OUT:
            if key == 'SV3307':
                print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.Valve_OUT[key] != self.Valve_buffer[key]:
                self.db.insert_data_into_stack(key + '_OUT', self.early_dt, self.Valve_buffer[key])
                self.db.insert_data_into_stack(key + '_OUT', self.dt, self.Valve_OUT[key])
                self.Valve_buffer[key] = self.Valve_OUT[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass

        if self.para_Valve >= self.rate_Valve:
            for key in self.Valve_OUT:
                self.db.insert_data_into_stack(key + '_OUT', self.dt, self.Valve_OUT[key])
                self.Valve_buffer[key] = self.Valve_OUT[key]
                self.commit_bool = True
            self.para_Valve = 0
        # print(3)
        for key in self.Switch_OUT:
            # print(key, self.Switch_OUT[key] != self.Switch_buffer[key])
            if self.Switch_OUT[key] != self.Switch_buffer[key]:
                self.db.insert_data_into_stack(key + '_OUT', self.early_dt, self.Switch_buffer[key])
                self.db.insert_data_into_stack(key + '_OUT', self.dt, self.Switch_OUT[key])
                self.Switch_buffer[key] = self.Switch_OUT[key]
                self.commit_bool = True
                # print(self.Switch_OUT[key])
            else:
                pass

        if self.para_Switch >= self.rate_Switch:
            for key in self.Switch_OUT:
                self.db.insert_data_into_stack(key + '_OUT', self.dt, self.Switch_OUT[key])
                self.Switch_buffer[key] = self.Switch_OUT[key]
                self.commit_bool = True
            self.para_Switch = 0
        # print(4)
        for key in self.Din_dic:
            # print(key, self.Switch_OUT[key] != self.Switch_buffer[key])
            if self.Din_dic[key] != self.Din_buffer[key]:
                self.db.insert_data_into_stack(key, self.early_dt, self.Din_buffer[key])
                self.db.insert_data_into_stack(key, self.dt, self.Din_dic[key])
                self.Din_buffer[key] = self.Din_dic[key]
                self.commit_bool = True
            else:
                pass

        if self.para_Din >= self.rate_Din:
            for key in self.Din_dic:
                self.db.insert_data_into_stack(key, self.dt, self.Din_dic[key])
                self.Din_buffer[key] = self.Din_dic[key]
            self.commit_bool = True
            self.para_Din = 0

        # if state of bool variable changes, write the data into database
        # print(5)
        for key in self.LOOPPID_EN:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.LOOPPID_EN[key] != self.LOOPPID_EN_buffer[key]:
                self.db.insert_data_into_stack(key + '_EN', self.early_dt, self.LOOPPID_EN_buffer[key])
                self.db.insert_data_into_stack(key + '_EN', self.dt, self.LOOPPID_EN[key])
                self.LOOPPID_EN_buffer[key] = self.LOOPPID_EN[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass

        for key in self.LOOPPID_MODE0:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.LOOPPID_MODE0[key] != self.LOOPPID_MODE0_buffer[key]:
                self.db.insert_data_into_stack(key + '_MODE0', self.early_dt, self.LOOPPID_MODE0_buffer[key])
                self.db.insert_data_into_stack(key + '_MODE0', self.dt, self.LOOPPID_MODE0[key])
                self.LOOPPID_MODE0_buffer[key] = self.LOOPPID_MODE0[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass

        for key in self.LOOPPID_MODE1:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.LOOPPID_MODE1[key] != self.LOOPPID_MODE1_buffer[key]:
                self.db.insert_data_into_stack(key + '_MODE1', self.early_dt, self.LOOPPID_MODE1_buffer[key])
                self.db.insert_data_into_stack(key + '_MODE1', self.dt, self.LOOPPID_MODE1[key])
                self.LOOPPID_MODE1_buffer[key] = self.LOOPPID_MODE1[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass

        for key in self.LOOPPID_MODE2:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.LOOPPID_MODE2[key] != self.LOOPPID_MODE2_buffer[key]:
                self.db.insert_data_into_stack(key + '_MODE2', self.early_dt, self.LOOPPID_MODE2_buffer[key])
                self.db.insert_data_into_stack(key + '_MODE2', self.dt, self.LOOPPID_MODE2[key])
                self.LOOPPID_MODE2_buffer[key] = self.LOOPPID_MODE2[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass

        for key in self.LOOPPID_MODE3:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.LOOPPID_MODE3[key] != self.LOOPPID_MODE3_buffer[key]:
                self.db.insert_data_into_stack(key + '_MODE3', self.early_dt, self.LOOPPID_MODE3_buffer[key])
                self.db.insert_data_into_stack(key + '_MODE3', self.dt, self.LOOPPID_MODE3[key])
                self.LOOPPID_MODE3_buffer[key] = self.LOOPPID_MODE3[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass

        # if no changes, write the data every fixed time interval
        # print(6)
        if self.para_LOOPPID >= self.rate_LOOPPID:
            for key in self.LOOPPID_EN:
                self.db.insert_data_into_stack(key + '_EN', self.dt, self.LOOPPID_EN[key])
                self.LOOPPID_EN_buffer[key] = self.LOOPPID_EN[key]
            for key in self.LOOPPID_MODE0:
                self.db.insert_data_into_stack(key + '_MODE0', self.dt, self.LOOPPID_MODE0[key])
                self.LOOPPID_MODE0_buffer[key] = self.LOOPPID_MODE0[key]
            for key in self.LOOPPID_MODE1:
                self.db.insert_data_into_stack(key + '_MODE1', self.dt, self.LOOPPID_MODE1[key])
                self.LOOPPID_MODE1_buffer[key] = self.LOOPPID_MODE1[key]
            for key in self.LOOPPID_MODE2:
                self.db.insert_data_into_stack(key + '_MODE2', self.dt, self.LOOPPID_MODE2[key])
                self.LOOPPID_MODE2_buffer[key] = self.LOOPPID_MODE2[key]
            for key in self.LOOPPID_MODE3:
                self.db.insert_data_into_stack(key + '_MODE3', self.dt, self.LOOPPID_MODE3[key])
                self.LOOPPID_MODE3_buffer[key] = self.LOOPPID_MODE3[key]
            # write float data.
            for key in self.LOOPPID_OUT:
                self.db.insert_data_into_stack(key + '_OUT', self.dt, self.LOOPPID_OUT[key])
                self.LOOPPID_OUT_buffer[key] = self.LOOPPID_OUT[key]
            for key in self.LOOPPID_IN:
                self.db.insert_data_into_stack(key + '_IN', self.dt, self.LOOPPID_IN[key])
                self.LOOPPID_IN_buffer[key] = self.LOOPPID_IN[key]
            self.commit_bool = True
            self.para_LOOPPID = 0
        # print(7)

        for key in self.LOOP2PT_OUT:
            # print(7)
            # print(8)
            # print(key, self.LOOP2PT_OUT[key])
            if self.LOOP2PT_OUT[key] != self.LOOP2PT_OUT_buffer[key]:
                self.db.insert_data_into_stack(key + '_OUT', self.early_dt, self.LOOP2PT_OUT_buffer[key])
                self.db.insert_data_into_stack(key + '_OUT', self.dt, self.LOOP2PT_OUT[key])
                self.LOOP2PT_OUT_buffer[key] = self.LOOP2PT_OUT[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass

        for key in self.LOOP2PT_MODE0:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.LOOP2PT_MODE0[key] != self.LOOP2PT_MODE0_buffer[key]:
                self.db.insert_data_into_stack(key + '_MODE0', self.early_dt, self.LOOP2PT_MODE0_buffer[key])
                self.db.insert_data_into_stack(key + '_MODE0', self.dt, self.LOOP2PT_MODE0[key])
                self.LOOP2PT_MODE0_buffer[key] = self.LOOP2PT_MODE0[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass

        for key in self.LOOP2PT_MODE1:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.LOOP2PT_MODE1[key] != self.LOOP2PT_MODE1_buffer[key]:
                self.db.insert_data_into_stack(key + '_MODE1', self.early_dt, self.LOOP2PT_MODE1_buffer[key])
                self.db.insert_data_into_stack(key + '_MODE1', self.dt, self.LOOP2PT_MODE1[key])
                self.LOOP2PT_MODE1_buffer[key] = self.LOOP2PT_MODE1[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass
        for key in self.LOOP2PT_MODE2:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.LOOP2PT_MODE2[key] != self.LOOP2PT_MODE2_buffer[key]:
                self.db.insert_data_into_stack(key + '_MODE2', self.early_dt, self.LOOP2PT_MODE2_buffer[key])
                self.db.insert_data_into_stack(key + '_MODE2', self.dt, self.LOOP2PT_MODE2[key])
                self.LOOP2PT_MODE2_buffer[key] = self.LOOP2PT_MODE2[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass
        for key in self.LOOP2PT_MODE3:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.LOOP2PT_MODE3[key] != self.LOOP2PT_MODE3_buffer[key]:
                self.db.insert_data_into_stack(key + '_MODE3', self.early_dt, self.LOOP2PT_MODE3_buffer[key])
                self.db.insert_data_into_stack(key + '_MODE3', self.dt, self.LOOP2PT_MODE3[key])
                self.LOOP2PT_MODE3_buffer[key] = self.LOOP2PT_MODE3[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass
        if self.para_LOOP2PT >= self.rate_LOOP2PT:

            for key in self.LOOP2PT_MODE0:
                self.db.insert_data_into_stack(key + '_MODE0', self.dt, self.LOOP2PT_MODE0[key])
                self.LOOP2PT_MODE0_buffer[key] = self.LOOP2PT_MODE0[key]
            for key in self.LOOP2PT_MODE1:
                self.db.insert_data_into_stack(key + '_MODE1', self.dt, self.LOOP2PT_MODE1[key])
                self.LOOP2PT_MODE1_buffer[key] = self.LOOP2PT_MODE1[key]
            for key in self.LOOP2PT_MODE2:
                self.db.insert_data_into_stack(key + '_MODE2', self.dt, self.LOOP2PT_MODE2[key])
                self.LOOP2PT_MODE2_buffer[key] = self.LOOP2PT_MODE2[key]
            for key in self.LOOP2PT_MODE3:
                self.db.insert_data_into_stack(key + '_MODE3', self.dt, self.LOOP2PT_MODE3[key])
                self.LOOP2PT_MODE3_buffer[key] = self.LOOP2PT_MODE3[key]
            # write float data.
            for key in self.LOOP2PT_OUT:
                self.db.insert_data_into_stack(key + '_OUT', self.dt, self.LOOP2PT_OUT[key])
                self.LOOP2PT_OUT_buffer[key] = self.LOOP2PT_OUT[key]

            self.commit_bool = True
            self.para_LOOP2PT = 0

        if self.para_REAL >= self.rate_REAL:
            for key in self.LEFT_REAL_address:
                # print(key, self.LEFT_REAL_dic[key])
                self.db.insert_data_into_stack(key, self.dt, self.LEFT_REAL_dic[key])
                # print("write pressure transducer")
                self.commit_bool = True
            self.para_REAL = 0

        # #FLAGS
        for key in self.FLAG_INTLKD:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.FLAG_INTLKD[key] != self.FLAG_INTLKD_buffer[key]:
                self.db.insert_data_into_stack(key + '_INTLKD', self.early_dt, self.FLAG_INTLKD_buffer[key])
                self.db.insert_data_into_stack(key + '_INTLKD', self.dt, self.FLAG_INTLKD[key])
                self.db.insert_data_into_stack(key, self.dt, self.FLAG_DIC[key])
                self.FLAG_INTLKD_buffer[key] = self.FLAG_INTLKD[key]
                self.commit_bool = True
            else:
                pass

        if self.para_FLAG >= self.rate_FLAG:
            for key in self.FLAG_INTLKD:
                self.db.insert_data_into_stack(key, self.dt, self.FLAG_DIC[key])
                self.db.insert_data_into_stack(key + '_INTLKD', self.dt, self.FLAG_INTLKD[key])
                self.FLAG_INTLKD_buffer[key] = self.FLAG_INTLKD[key]
                self.commit_bool = True
            self.para_FLAG = 0

        # FF
        for key in self.FF_DIC:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.FF_DIC[key] != self.FF_buffer[key]:
                self.db.insert_data_into_stack(key, self.early_dt, self.FF_buffer[key])
                self.db.insert_data_into_stack(key, self.dt, self.FF_DIC[key])
                self.FF_buffer[key] = self.FF_DIC[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass

        if self.para_FF >= self.rate_FF:
            for key in self.FF_DIC:
                self.db.insert_data_into_stack(key, self.dt, self.FF_DIC[key])
                self.FF_buffer[key] = self.FF_DIC[key]
                self.commit_bool = True
            self.para_FF = 0

        # PARAM_B
        for key in self.PARAM_B_DIC:
            # print(key, self.Valve_OUT[key] != self.Valve_buffer[key])
            if self.PARAM_B_DIC[key] != self.PARAM_B_buffer[key]:
                self.db.insert_data_into_stack(key, self.early_dt, self.PARAM_B_buffer[key])
                self.db.insert_data_into_stack(key, self.dt, self.PARAM_B_DIC[key])
                self.PARAM_B_buffer[key] = self.PARAM_B_DIC[key]
                self.commit_bool = True
                # print(self.Valve_OUT[key])
            else:
                pass

        if self.para_PARAM_B >= self.rate_PARAM_B:
            for key in self.PARAM_B_DIC:
                self.db.insert_data_into_stack(key, self.dt, self.PARAM_B_DIC[key])
                self.PARAM_B_buffer[key] = self.PARAM_B_DIC[key]
                self.commit_bool = True
            self.para_PARAM_B = 0

        # other parameters I/F/T
        if self.para_PARAM_F >= self.rate_PARAM_F:
            for key in self.PARAM_F_DIC:
                self.db.insert_data_into_stack(key, self.dt, self.PARAM_F_DIC[key])

                self.commit_bool = True
            self.para_PARAM_F = 0

        if self.para_PARAM_I >= self.rate_PARAM_I:
            for key in self.PARAM_I_DIC:
                self.db.insert_data_into_stack(key, self.dt, self.PARAM_I_DIC[key])

                self.commit_bool = True
            self.para_PARAM_I = 0

        if self.para_PARAM_T >= self.rate_PARAM_T:
            for key in self.PARAM_T_DIC:
                self.db.insert_data_into_stack(key, self.dt, self.PARAM_T_DIC[key])

                self.commit_bool = True
            self.para_PARAM_T = 0

        if self.para_TIME >= self.rate_TIME:
            for key in self.TIME_DIC:
                self.db.insert_data_into_stack(key, self.dt, self.TIME_DIC[key])

                self.commit_bool = True
            self.para_TIME = 0

        # print("a",self.para_TT,"b",self.para_PT )
        # print(8)

        # commit the changes at last step only if it is time to write
        if self.commit_bool:
            # put alll commands into stack which is a pandas dataframe, reorder it by timestamp and then transform them into mysql queries
            self.db.sort_stack()
            self.db.convert_stack_into_queries()
            self.db.drop_stack()
            self.db.db.commit()
        print("Wrting PLC data to database...")
        self.para_alarm += 1

        self.para_TT += 1
        self.para_PT += 1
        self.para_Valve += 1
        self.para_Switch += 1
        self.para_LOOPPID += 1
        self.para_LOOP2PT += 1
        self.para_REAL += 1
        self.para_Din += 1
        self.para_FLAG += 1
        self.para_FF += 1
        self.para_PARAM_T += 1
        self.para_PARAM_I += 1
        self.para_PARAM_B += 1
        self.para_PARAM_F += 1
        self.para_TIME += 1
        # self.PLC.NewData_Database = False




# Class to read PLC value every 2 sec
class UpdatePLC(QtCore.QObject):
    AI_slack_alarm = QtCore.Signal(str)
    COUPP_TEXT_alarm = QtCore.Signal(str)


    def __init__(self, PLC, parent=None):
        super().__init__(parent)

        self.PLC = PLC
        self.alarm_db = COUPP_database()
        # self.message_manager = message_manager()
        self.Running = False
        self.period = 1
        # every pid should have one unique para and rate
        self.TT_FP_para = sec.TT_FP_PARA
        self.TT_FP_rate = sec.TT_FP_RATE
        self.TT_BO_para = sec.TT_BO_PARA
        self.TT_BO_rate = sec.TT_BO_RATE
        self.PT_para = sec.PT_PARA
        self.PT_rate = sec.PT_RATE
        self.PR_CYCLE_para = 0
        self.PR_CYCLE_rate = 30
        self.LEFT_REAL_para = sec.LEFT_REAL_PARA
        self.LEFT_REAL_rate = sec.LEFT_REAL_RATE
        self.Din_para = sec.DIN_PARA
        self.Din_rate = sec.DIN_RATE
        self.LOOPPID_para = sec.LOOPPID_PARA
        self.LOOPPID_rate = sec.LOOPPID_RATE
        self.alarm_stack=""

    @QtCore.Slot()
    def run(self):

            self.Running = True


            while self.Running:
                try:
                    print("PLC updating", datetime.datetime.now())
                    self.PLC.ReadAll()
                    # test signal
                    # self.AI_slack_alarm.emit("signal")
                    self.alarm_stack = ""
                    # check alarms
                    for keyTT_FP in self.PLC.TT_FP_dic:
                        self.check_TT_FP_alarm(keyTT_FP)
                    for keyTT_BO in self.PLC.TT_BO_dic:
                        self.check_TT_BO_alarm(keyTT_BO)
                    for keyPT in self.PLC.PT_dic:
                        self.check_PT_alarm(keyPT)
                    for keyLEFT_REAL in self.PLC.LEFT_REAL_dic:
                        self.check_LEFT_REAL_alarm(keyLEFT_REAL)
                    for keyDin in self.PLC.Din_dic:
                        self.check_Din_alarm(keyDin)
                    for keyLOOPPID in self.PLC.LOOPPID_OUT:
                        self.check_LOOPPID_alarm(keyLOOPPID)
                    self.or_alarm_signal()
                except:
                    self.PLC.PLC_DISCON_SIGNAL.emit()
                    (type, value, traceback) = sys.exc_info()
                    exception_hook(type, value, traceback)

                # if there is alarm, update the PICO watchdog and report the alarm
                try:
                    print("stack1"+"\n", "111", str(self.alarm_stack))
                    print(self.alarm_stack == "")
                    if self.PLC.MainAlarm:
                        # self.alarm_db.ssh_alarm(message=self.alarm_stack)

                        self.COUPP_TEXT_alarm.emit(self.alarm_stack)
                    else:
                        pass
                        # self.alarm_db.ssh_write()
                except:
                    self.AI_slack_alarm.emit("failed to ssh to PICO watchdog in PLC update module")
                    pass

                time.sleep(self.period)




    @QtCore.Slot()
    def stop(self):
        self.Running = False

    # def pressure_cycle(self):
    #     if self.PR_CYCLE_para >= self.PR_CYCLE_rate:
    #         self.PLC.
    @QtCore.Slot()
    def stack_alarm_msg(self, string):
        self.alarm_stack= self.alarm_stack+"\n" +str(string)
        print("stack2", self.alarm_stack)

    def check_TT_FP_alarm(self, pid):

        if self.PLC.TT_FP_Activated[pid]:
            if float(self.PLC.TT_FP_LowLimit[pid]) >= float(self.PLC.TT_FP_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if float(self.PLC.TT_FP_dic[pid]) <= float(self.PLC.TT_FP_LowLimit[pid]):
                    self.TTFPalarmmsg(pid)

                    # print(pid , " reading is lower than the low limit")
                elif float(self.PLC.TT_FP_dic[pid]) >= float(self.PLC.TT_FP_HighLimit[pid]):
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
            if float(self.PLC.TT_BO_LowLimit[pid]) >= float(self.PLC.TT_BO_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if float(self.PLC.TT_BO_dic[pid]) <= float(self.PLC.TT_BO_LowLimit[pid]):
                    self.TTBOalarmmsg(pid)

                    # print(pid , " reading is lower than the low limit")
                elif float(self.PLC.TT_BO_dic[pid]) >= float(self.PLC.TT_BO_HighLimit[pid]):
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
            if float(self.PLC.PT_LowLimit[pid]) >= float(self.PLC.PT_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if float(self.PLC.PT_dic[pid]) <= float(self.PLC.PT_LowLimit[pid]):
                    self.PTalarmmsg(pid)

                    # print(pid , " reading is lower than the low limit")
                elif float(self.PLC.PT_dic[pid]) >= float(self.PLC.PT_HighLimit[pid]):
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
            if float(self.PLC.LEFT_REAL_LowLimit[pid]) >= float(self.PLC.LEFT_REAL_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if float(self.PLC.LEFT_REAL_dic[pid]) <= float(self.PLC.LEFT_REAL_LowLimit[pid]):
                    self.LEFT_REALalarmmsg(pid)

                    # print(pid , " reading is lower than the low limit")
                elif float(self.PLC.LEFT_REAL_dic[pid]) >= float(self.PLC.LEFT_REAL_HighLimit[pid]):
                    self.LEFT_REALalarmmsg(pid)
                    # print(pid,  " reading is higher than the high limit")
                else:
                    self.resetLEFT_REALalarmmsg(pid)
                    # print(pid, " is in normal range")

        else:
            self.resetLEFT_REALalarmmsg(pid)
            pass

    def check_Din_alarm(self, pid):

        if self.PLC.Din_Activated[pid]:
            if float(self.PLC.Din_LowLimit[pid]) >= float(self.PLC.Din_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if float(self.PLC.Din_dic[pid]) <= float(self.PLC.Din_LowLimit[pid]):
                    self.Dinalarmmsg(pid)

                    # print(pid , " reading is lower than the low limit")
                elif float(self.PLC.Din_dic[pid]) >= float(self.PLC.Din_HighLimit[pid]):
                    self.Dinalarmmsg(pid)
                    # print(pid,  " reading is higher than the high limit")
                else:
                    self.resetDinalarmmsg(pid)
                    # print(pid, " is in normal range")

        else:
            self.resetDinalarmmsg(pid)
            pass

    def check_LOOPPID_alarm(self, pid):
        # if self.PLC.LOOPPID_Activated[pid]:
        #     if self.PLC.LOOPPID_SATLO[pid] or self.PLC.LOOPPID_SATHI[pid]:
        #         # print(pid, " is in normal range")
        #         self.LOOPPIDalarmmsg(pid)
        #     else:
        #         self.resetLOOPPIDalarmmsg(pid)
        #         # print(pid, " is in normal range")
        #
        # else:
        #     self.resetLOOPPIDalarmmsg(pid)
        #     pass

        if self.PLC.LOOPPID_Activated[pid]:
            if float(self.PLC.LOOPPID_Alarm_LowLimit[pid]) >= float(self.PLC.LOOPPID_Alarm_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if float(self.PLC.LOOPPID_OUT[pid]) <= float(self.PLC.LOOPPID_Alarm_LowLimit[pid]):
                    self.LOOPPIDalarmmsg(pid)

                    # print(pid , " reaLOOPPIDg is lower than the low limit")
                elif float(self.PLC.LOOPPID_OUT[pid]) >= float(self.PLC.LOOPPID_Alarm_HighLimit[pid]):
                    self.LOOPPIDalarmmsg(pid)
                    # print(pid,  " reaLOOPPIDg is higher than the high limit")
                else:
                    self.resetLOOPPIDalarmmsg(pid)
                    # print(pid, " is in normal range")

        else:
            self.resetLOOPPIDalarmmsg(pid)
            pass

    def TTFPalarmmsg(self, pid):
        self.PLC.TT_FP_Alarm[pid] = True
        # and send email or slack messages
        # every time interval send a alarm message
        print(self.TT_FP_para[pid])
        if self.TT_FP_para[pid] >= self.TT_FP_rate[pid]:
            msg = "SBC alarm: {pid} is out of range: CURRENT VALUE: {current}, LO_LIM: {low}, HI_LIM: {high}".format(pid=pid, current=self.PLC.TT_FP_dic[pid],
                                                                                                                     high=self.PLC.TT_FP_HighLimit[pid], low=self.PLC.TT_FP_LowLimit[pid])
            # self.message_manager.tencent_alarm(msg)
            self.AI_slack_alarm.emit(msg)
            self.stack_alarm_msg(msg)

            self.TT_FP_para[pid] = 0
        self.TT_FP_para[pid] += 1

    def resetTTFPalarmmsg(self, pid):
        self.PLC.TT_FP_Alarm[pid] = False
        # self.TT_FP_para = 0
        # and send email or slack messages

    def TTBOalarmmsg(self, pid):
        self.PLC.TT_BO_Alarm[pid] = True
        # and send email or slack messages
        print(self.TT_BO_para[pid])
        if self.TT_BO_para[pid] >= self.TT_BO_rate[pid]:
            msg = "SBC alarm: {pid} is out of range: CURRENT VALUE: {current}, LO_LIM: {low}, HI_LIM: {high}".format(pid=pid, current=self.PLC.TT_BO_dic[pid],
                                                                                                                     high=self.PLC.TT_BO_HighLimit[pid], low=self.PLC.TT_BO_LowLimit[pid])
            # self.message_manager.tencent_alarm(msg)
            self.AI_slack_alarm.emit(msg)
            self.stack_alarm_msg(msg)
            self.TT_BO_para[pid] = 0

        self.TT_BO_para[pid] += 1

    def resetTTBOalarmmsg(self, pid):
        self.PLC.TT_BO_Alarm[pid] = False
        # self.TT_BO_para = 0
        # and send email or slack messages

    def PTalarmmsg(self, pid):
        self.PLC.PT_Alarm[pid] = True
        # and send email or slack messages
        if self.PT_para[pid] >= self.PT_rate[pid]:
            msg = "SBC alarm: {pid} is out of range: CURRENT VALUE: {current}, LO_LIM: {low}, HI_LIM: {high}".format(pid=pid, current=self.PLC.PT_dic[pid],
                                                                                                                     high=self.PLC.PT_HighLimit[pid], low=self.PLC.PT_LowLimit[pid])

            # self.message_manager.tencent_alarm(msg)
            self.AI_slack_alarm.emit(msg)
            self.stack_alarm_msg(msg)
            self.PT_para[pid] = 0
        self.PT_para[pid] += 1

    def resetPTalarmmsg(self, pid):
        self.PLC.PT_Alarm[pid] = False
        # self.PT_para = 0
        # and send email or slack messages

    def LEFT_REALalarmmsg(self, pid):
        self.PLC.LEFT_REAL_Alarm[pid] = True
        # and send email or slack messages
        if self.LEFT_REAL_para[pid] >= self.LEFT_REAL_rate[pid]:
            msg = "SBC alarm: {pid} is out of range: CURRENT VALUE: {current}, LO_LIM: {low}, HI_LIM: {high}".format(pid=pid, current=self.PLC.LEFT_REAL_dic[pid],
                                                                                                                     high=self.PLC.LEFT_REAL_HighLimit[pid], low=self.PLC.LEFT_REAL_LowLimit[pid])

            # self.message_manager.tencent_alarm(msg)
            self.AI_slack_alarm.emit(msg)
            self.stack_alarm_msg(msg)
            self.LEFT_REAL_para[pid] = 0
        self.LEFT_REAL_para[pid] += 1

    def resetLEFT_REALalarmmsg(self, pid):
        self.PLC.LEFT_REAL_Alarm[pid] = False
        # self.LEFT_REAL_para = 0
        # and send email or slack messages

    def Dinalarmmsg(self, pid):
        self.PLC.Din_Alarm[pid] = True
        # and send email or slack messages
        if self.Din_para[pid] >= self.Din_rate[pid]:
            msg = "SBC alarm: {pid} is out of range: CURRENT VALUE: {current}, LO_LIM: {low}, HI_LIM: {high}".format(pid=pid, current=self.PLC.Din_dic[pid],
                                                                                                                     high=self.PLC.Din_HighLimit[pid], low=self.PLC.Din_LowLimit[pid])

            # self.message_manager.tencent_alarm(msg)
            self.AI_slack_alarm.emit(msg)
            self.stack_alarm_msg(msg)
            self.Din_para[pid] = 0
        self.Din_para[pid] += 1

    def resetDinalarmmsg(self, pid):
        self.PLC.Din_Alarm[pid] = False
        # self.Din_para = 0
        # and send email or slack messages

    def LOOPPIDalarmmsg(self, pid):
        self.PLC.LOOPPID_Alarm[pid] = True
        # and send email or slack messages
        if self.LOOPPID_para[pid] >= self.LOOPPID_rate[pid]:
            msg = "SBC alarm: {pid} is out of range: CURRENT VALUE: {current}, LO_LIM: {low}, HI_LIM: {high}".format(pid=pid, current=self.PLC.LOOPPID_OUT[pid],
                                                                                                                     high=self.PLC.LOOPPID_Alarm_HighLimit[pid], low=self.PLC.LOOPPID_Alarm_LowLimit[pid])

            # self.message_manager.tencent_alarm(msg)
            self.AI_slack_alarm.emit(msg)
            self.stack_alarm_msg(msg)
            self.LOOPPID_para[pid] = 0
        self.LOOPPID_para[pid] += 1

    def resetLOOPPIDalarmmsg(self, pid):
        self.PLC.LOOPPID_Alarm[pid] = False
        # self.LOOPPID_para = 0
        # and send email or slack messages

    def or_alarm_signal(self):
        if (True in self.PLC.TT_BO_Alarm) or (True in self.PLC.PT_Alarm) or (True in self.PLC.TT_FP_Alarm) or (True in self.PLC.LEFT_REAL_Alarm) or (True in self.PLC.Din_Alarm) or (True in self.PLC.LOOPPID_Alarm):
            self.PLC.MainAlarm = True
        else:
            self.PLC.MainAlarm = False


class UpdateServer(QtCore.QObject):
    def __init__(self, PLC, parent=None):
        super().__init__(parent)
        self.PLC = PLC
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.setsockopt(zmq.LINGER, 0)  # ____POLICY: set upon instantiations
        self.socket.setsockopt(zmq.AFFINITY, 1)  # ____POLICY: map upon IO-type thread
        self.socket.setsockopt(zmq.RCVTIMEO, 1000)
        self.socket.bind("tcp://*:5555")
        self.Running = False
        self.period = 1
        # self.socket.re
        print("connect to the PLC server")

        # self.TT_FP_dic_ini = copy.copy(sec.TT_FP_DIC)
        # self.TT_BO_dic_ini = copy.copy(sec.TT_BO_DIC)
        # self.PT_dic_ini = copy.copy(sec.PT_DIC)
        # self.LEFT_REAL_ini = copy.copy(sec.LEFT_REAL_DIC)
        # self.TT_FP_LowLimit_ini = copy.copy(sec.TT_FP_LOWLIMIT)
        # self.TT_FP_HighLimit_ini = copy.copy(sec.TT_FP_HIGHLIMIT)
        # self.TT_BO_LowLimit_ini = copy.copy(sec.TT_BO_LOWLIMIT)
        # self.TT_BO_HighLimit_ini = copy.copy(sec.TT_BO_HIGHLIMIT)
        # self.PT_LowLimit_ini = copy.copy(sec.PT_LOWLIMIT)
        # self.PT_HighLimit_ini = copy.copy(sec.PT_HIGHLIMIT)
        # self.LEFT_REAL_LowLimit_ini = copy.copy(sec.LEFT_REAL_LOWLIMIT)
        # self.LEFT_REAL_HighLimit_ini = copy.copy(sec.LEFT_REAL_HIGHLIMIT)
        # self.TT_FP_Activated_ini = copy.copy(sec.TT_FP_ACTIVATED)
        # self.TT_BO_Activated_ini = copy.copy(sec.TT_BO_ACTIVATED)
        # self.PT_Activated_ini = copy.copy(sec.PT_ACTIVATED)
        # self.TT_FP_Alarm_ini = copy.copy(sec.TT_FP_ALARM)
        # self.TT_BO_Alarm_ini = copy.copy(sec.TT_BO_ALARM)
        # self.PT_Alarm_ini = copy.copy(sec.PT_ALARM)
        # self.LEFT_REAL_Activated_ini= copy.copy(sec.LEFT_REAL_ACTIVATED)
        # self.LEFT_REAL_Alarm_ini = copy.copy(sec.LEFT_REAL_ALARM)
        # self.MainAlarm_ini = copy.copy(sec.MAINALARM)
        # self.Valve_OUT_ini = copy.copy(sec.VALVE_OUT)
        # self.Valve_MAN_ini = copy.copy(sec.VALVE_MAN)
        # self.Valve_INTLKD_ini = copy.copy(sec.VALVE_INTLKD)
        # self.Valve_ERR_ini = copy.copy(sec.VALVE_ERR)
        # self.Valve_Busy_ini = copy.copy(sec.VALVE_BUSY)
        # self.Switch_OUT_ini = copy.copy(sec.SWITCH_OUT)
        # self.Switch_MAN_ini = copy.copy(sec.SWITCH_MAN)
        # self.Switch_INTLKD_ini = copy.copy(sec.SWITCH_INTLKD)
        # self.Switch_ERR_ini = copy.copy(sec.SWITCH_ERR)
        # self.Din_dic_ini = copy.copy(sec.DIN_DIC)
        # self.LOOPPID_MODE0_ini = copy.copy(sec.LOOPPID_MODE0)
        # self.LOOPPID_MODE1_ini = copy.copy(sec.LOOPPID_MODE1)
        # self.LOOPPID_MODE2_ini = copy.copy(sec.LOOPPID_MODE2)
        # self.LOOPPID_MODE3_ini = copy.copy(sec.LOOPPID_MODE3)
        # self.LOOPPID_INTLKD_ini = copy.copy(sec.LOOPPID_INTLKD)
        # self.LOOPPID_MAN_ini = copy.copy(sec.LOOPPID_MAN)
        # self.LOOPPID_ERR_ini = copy.copy(sec.LOOPPID_ERR)
        # self.LOOPPID_SATHI_ini = copy.copy(sec.LOOPPID_SATHI)
        # self.LOOPPID_SATLO_ini = copy.copy(sec.LOOPPID_SATLO)
        # self.LOOPPID_EN_ini = copy.copy(sec.LOOPPID_EN)
        # self.LOOPPID_OUT_ini = copy.copy(sec.LOOPPID_OUT)
        # self.LOOPPID_IN_ini = copy.copy(sec.LOOPPID_IN)
        # self.LOOPPID_HI_LIM_ini = copy.copy(sec.LOOPPID_HI_LIM)
        # self.LOOPPID_LO_LIM_ini = copy.copy(sec.LOOPPID_LO_LIM)
        # self.LOOPPID_SET0_ini = copy.copy(sec.LOOPPID_SET0)
        # self.LOOPPID_SET1_ini = copy.copy(sec.LOOPPID_SET1)
        # self.LOOPPID_SET2_ini = copy.copy(sec.LOOPPID_SET2)
        # self.LOOPPID_SET3_ini = copy.copy(sec.LOOPPID_SET3)
        # self.LOOPPID_Busy_ini = copy.copy(sec.LOOPPID_BUSY)
        #
        # self.LOOP2PT_MODE0_ini = copy.copy(sec.LOOP2PT_MODE0)
        # self.LOOP2PT_MODE1_ini = copy.copy(sec.LOOP2PT_MODE1)
        # self.LOOP2PT_MODE2_ini = copy.copy(sec.LOOP2PT_MODE2)
        # self.LOOP2PT_MODE3_ini = copy.copy(sec.LOOP2PT_MODE3)
        # self.LOOP2PT_INTLKD_ini = copy.copy(sec.LOOP2PT_INTLKD)
        # self.LOOP2PT_MAN_ini = copy.copy(sec.LOOP2PT_MAN)
        # self.LOOP2PT_ERR_ini = copy.copy(sec.LOOP2PT_ERR)
        # self.LOOP2PT_OUT_ini = copy.copy(sec.LOOP2PT_OUT)
        # self.LOOP2PT_SET1_ini = copy.copy(sec.LOOP2PT_SET1)
        # self.LOOP2PT_SET2_ini = copy.copy(sec.LOOP2PT_SET2)
        # self.LOOP2PT_SET3_ini = copy.copy(sec.LOOP2PT_SET3)
        # self.LOOP2PT_Busy_ini = copy.copy(sec.LOOP2PT_BUSY)
        #
        # self.Procedure_running_ini = copy.copy(sec.PROCEDURE_RUNNING)
        # self.Procedure_INTLKD_ini = copy.copy(sec.PROCEDURE_INTLKD)
        # self.Procedure_EXIT_ini = copy.copy(sec.PROCEDURE_EXIT)
        #
        # self.INTLK_D_ADDRESS_ini = copy.copy(sec.INTLK_D_ADDRESS)
        # self.INTLK_D_DIC_ini = copy.copy(sec.INTLK_D_DIC)
        # self.INTLK_D_EN_ini = copy.copy(sec.INTLK_D_EN)
        # self.INTLK_D_COND_ini = copy.copy(sec.INTLK_D_COND)
        # self.INTLK_A_ADDRESS_ini = copy.copy(sec.INTLK_A_ADDRESS)
        # self.INTLK_A_DIC_ini = copy.copy(sec.INTLK_A_DIC)
        # self.INTLK_A_EN_ini = copy.copy(sec.INTLK_A_EN)
        # self.INTLK_A_COND_ini = copy.copy(sec.INTLK_A_COND)
        # self.INTLK_A_SET_ini = copy.copy(sec.INTLK_A_SET)
        #
        # self.FLAG_ADDRESS_ini = copy.copy(sec.FLAG_ADDRESS)
        # self.FLAG_DIC_ini = copy.copy(sec.FLAG_DIC)
        # self.FLAG_INTLKD_ini = copy.copy(sec.FLAG_INTLKD)
        # self.FLAG_Busy_ini = copy.copy(sec.FLAG_BUSY)

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

        self.data_dic = {"data": {"TT": {"FP": {"value": self.TT_FP_dic_ini, "high": self.TT_FP_HighLimit_ini, "low": self.TT_FP_LowLimit_ini},
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
                                  "FF":self.FF_DIC_ini,
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

        self.data_package = pickle.dumps(self.data_dic)

    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:
            print("refreshing the BKG-GUI communication server")
            if self.PLC.NewData_ZMQ:
                try:
                    # message = self.socket.recv()
                    # print("refreshing")
                    # print(f"Received request: {message}")
                    self.write_data()
                    print("data sent")

                    #  Send reply back to client
                    # self.socket.send(b"World")
                    self.pack_data()
                    print("data received")
                    # print(self.data_package)
                    # data=pickle.dumps([0,0])
                    # self.socket.send(data)
                    self.socket.send(self.data_package)
                    # self.socket.sendall(self.data_package)
                    self.PLC.NewData_ZMQ = False
                except Exception as e:
                    print("Error:",e)
                    print("Time out for fetching data from GUI, continue to wait")

            else:
                print("BKG-GUI communication server stops")
                pass
            time.sleep(self.period)

    @QtCore.Slot()
    def stop(self):
        self.socket.close()
        self.context.term()
        self.Running = False

    def pack_data(self):
        print("Updateserver", self.data_dic["data"]['FLAG']["value"],datetime.datetime.now())

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

        for key in self.PLC.TT_FP_Activated:
            self.TT_FP_Activated_ini[key]= self.PLC.TT_FP_Activated[key]
        for key in self.PLC.TT_BO_Activated:
            self.TT_BO_Activated_ini[key]= self.PLC.TT_BO_Activated[key]
        for key in self.PLC.PT_Activated:
            self.PT_Activated_ini[key]= self.PLC.PT_Activated[key]
        for key in self.PLC.LEFT_REAL_Activated:
            self.LEFT_REAL_Activated_ini[key]= self.PLC.LEFT_REAL_Activated[key]

        for key in self.PLC.Valve_OUT:
            self.Valve_OUT_ini[key] = self.PLC.Valve_OUT[key]
        for key in self.PLC.Valve_INTLKD:
            self.Valve_INTLKD_ini[key] = self.PLC.Valve_INTLKD[key]
        for key in self.PLC.Valve_MAN:
            self.Valve_MAN_ini[key] = self.PLC.Valve_MAN[key]
        for key in self.PLC.Valve_ERR:
            self.Valve_ERR_ini[key] = self.PLC.Valve_ERR[key]
        for key in self.PLC.Valve_Busy:
            self.Valve_Busy_ini[key] = self.PLC.Valve_Busy[key]
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
        for key in self.PLC.Din_LowLimit:
            self.Din_LowLimit_ini[key] = self.PLC.Din_LowLimit[key]
        for key in self.PLC.Din_HighLimit:
            self.Din_HighLimit_ini[key] = self.PLC.Din_HighLimit[key]
        for key in self.PLC.Din_Alarm:
            self.Din_Alarm_ini[key] = self.PLC.Din_Alarm[key]
        for key in self.PLC.Din_Activated:
            self.Din_Activated_ini[key] = self.PLC.Din_Activated[key]
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
        for key in self.PLC.LOOPPID_Busy:
            self.LOOPPID_Busy_ini[key] = self.PLC.LOOPPID_Busy[key]
        for key in self.PLC.LOOPPID_Activated:
            self.LOOPPID_Activated_ini[key] = self.PLC.LOOPPID_Activated[key]
        for key in self.PLC.LOOPPID_Alarm:
            self.LOOPPID_Alarm_ini[key] = self.PLC.LOOPPID_Alarm[key]
        for key in self.PLC.LOOPPID_Alarm_LowLimit:
            self.LOOPPID_Alarm_LowLimit_ini[key] = self.PLC.LOOPPID_Alarm_LowLimit[key]
        for key in self.PLC.LOOPPID_Alarm_HighLimit:
            self.LOOPPID_Alarm_HighLimit_ini[key] = self.PLC.LOOPPID_Alarm_HighLimit[key]




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
        for key in self.PLC.LOOP2PT_Busy:
            self.LOOP2PT_Busy_ini[key] = self.PLC.LOOP2PT_Busy[key]

        for key in self.PLC.Procedure_running:
            self.Procedure_running_ini[key] = self.PLC.Procedure_running[key]
        for key in self.PLC.Procedure_INTLKD:
            self.Procedure_INTLKD_ini[key] = self.PLC.Procedure_INTLKD[key]
        for key in self.PLC.Procedure_EXIT:
            self.Procedure_EXIT_ini[key] = self.PLC.Procedure_EXIT[key]
        for key in self.PLC.INTLK_D_DIC:
            self.INTLK_D_DIC_ini[key] = self.PLC.INTLK_D_DIC[key]
        for key in self.PLC.INTLK_D_EN:
            self.INTLK_D_EN_ini[key] = self.PLC.INTLK_D_EN[key]
        for key in self.PLC.INTLK_D_COND:
            self.INTLK_D_COND_ini[key] = self.PLC.INTLK_D_COND[key]
        for key in self.PLC.INTLK_A_DIC:
            self.INTLK_A_DIC_ini[key] = self.PLC.INTLK_A_DIC[key]
        for key in self.PLC.INTLK_A_EN:
            self.INTLK_A_EN_ini[key] = self.PLC.INTLK_A_EN[key]
        for key in self.PLC.INTLK_A_COND:
            self.INTLK_A_COND_ini[key] = self.PLC.INTLK_A_COND[key]
        for key in self.PLC.INTLK_A_SET:
            self.INTLK_A_SET_ini[key] = self.PLC.INTLK_A_SET[key]
        for key in self.PLC.FLAG_DIC:
            self.FLAG_DIC_ini[key] = self.PLC.FLAG_DIC[key]
        for key in self.PLC.FLAG_INTLKD:
            self.FLAG_INTLKD_ini[key] = self.PLC.FLAG_INTLKD[key]
        for key in self.PLC.FLAG_Busy:
            self.FLAG_Busy_ini[key] = self.PLC.FLAG_Busy[key]
        for key in self.PLC.FF_DIC:
            self.FF_DIC_ini[key] = self.PLC.FF_DIC[key]
        for key in self.PLC.PARAM_I_DIC:
            self.PARAM_I_DIC_ini[key] = self.PLC.PARAM_I_DIC[key]
        for key in self.PLC.PARAM_F_DIC:
            self.PARAM_F_DIC_ini[key] = self.PLC.PARAM_F_DIC[key]
        for key in self.PLC.PARAM_B_DIC:
            self.PARAM_B_DIC_ini[key] = self.PLC.PARAM_B_DIC[key]
        for key in self.PLC.PARAM_T_DIC:
            self.PARAM_T_DIC_ini[key] = self.PLC.PARAM_T_DIC[key]
        for key in self.PLC.TIME_DIC:
            self.TIME_DIC_ini[key] = self.PLC.TIME_DIC[key]







        self.data_dic["MainAlarm"] = self.PLC.MainAlarm

        self.data_package = pickle.dumps(self.data_dic)

        # for key in self.PLC.Valve_Busy:
        #     self.PLC.Valve_Busy[key] = False
        #
        # for key in self.PLC.LOOPPID_Busy:
        #     self.PLC.LOOPPID_Busy[key] = False
        #
        # for key in self.PLC.LOOP2PT_Busy:
        #     self.PLC.LOOP2PT_Busy[key] =False


    def write_data(self):
        message = pickle.loads(self.socket.recv())
        print(message)
        if not "MAN_SET" in message:
            if message == {}:
                pass
            else:
                for key in message:
                    print(message[key]["type"])
                    print(message[key]["type"] == "valve")
                    if message[key]["type"] == "valve":
                        print("Valve", datetime_in_1e5micro())
                        if message[key]["operation"] == "OPEN":
                            self.PLC.WriteBase2(address=message[key]["address"])
                        elif message[key]["operation"] == "CLOSE":
                            self.PLC.WriteBase4(address=message[key]["address"])
                        else:
                            pass
                        # write success signal

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

                    elif message[key]["type"] == "Din":
                        if message[key]["server"] == "BO":
                            if message[key]["operation"]["Update"]:
                                self.PLC.Din_Activated[key] = message[key]["operation"]["Act"]
                                self.PLC.Din_LowLimit[key] = message[key]["operation"]["LowLimit"]
                                self.PLC.Din_HighLimit[key] = message[key]["operation"]["HighLimit"]
                            else:
                                self.PLC.Din_Activated[key] = message[key]["operation"]["Act"]
                        else:
                            pass

                    elif message[key]["type"] == "LOOPPID_alarm":
                        if message[key]["server"] == "BO":
                            if message[key]["operation"]["Update"]:
                                self.PLC.LOOPPID_Activated[key] = message[key]["operation"]["Act"]
                                # self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                #                             value=message[key]["operation"]["LowLimit"])
                                # self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                #                             value=message[key]["operation"]["HighLimit"])
                                self.PLC.LOOPPID_Alarm_HighLimit[key] = message[key]["operation"]["HighLimit"]
                                self.PLC.LOOPPID_Alarm_LowLimit[key] = message[key]["operation"]["LowLimit"]


                            else:
                                self.PLC.LOOPPID_Activated[key] = message[key]["operation"]["Act"]
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

                    elif message[key]["type"] == "Procedure_TS":
                        if message[key]["server"] == "BO":
                            if message[key]["operation"]["RST_FF"]:
                                self.PLC.WriteFF(self.PLC.FF_ADDRESS["TS_ADDREM_FF"])
                            if message[key]["operation"]["update"]:
                                self.PLC.Write_BO_2_int16(self.PLC.PARAM_I_ADDRESS["TS_SEL"],message[key]["operation"]["SEL"])
                                self.PLC.Write_BO_2(self.PLC.PARAM_F_ADDRESS["TS_ADDREM_MASS"],message[key]["operation"]["ADDREM_MASS"])
                                self.PLC.Write_BO_2_int32(self.PLC.PARAM_T_ADDRESS["TS_ADDREM_MAXTIME"],round(float(message[key]["operation"]["MAXTIME"])*1000))

                            else:
                                pass
                        else:
                            pass

                    elif message[key]["type"] == "Procedure_PC":
                        if message[key]["server"] == "BO":
                            if message[key]["operation"]["ABORT_FF"]:
                                self.PLC.WriteFF(self.PLC.FF_ADDRESS["PCYCLE_ABORT_FF"])
                            if message[key]["operation"]["FASTCOMP_FF"]:
                                self.PLC.WriteFF(self.PLC.FF_ADDRESS["PCYCLE_FASTCOMP_FF"])
                            if message[key]["operation"]["SLOWCOMP_FF"]:
                                self.PLC.WriteFF(self.PLC.FF_ADDRESS["PCYCLE_SLOWCOMP_FF"])
                            if message[key]["operation"]["CYLEQ_FF"]:
                                self.PLC.WriteFF(self.PLC.FF_ADDRESS["PCYCLE_CYLEQ_FF"])
                            if message[key]["operation"]["ACCHARGE_FF"]:
                                self.PLC.WriteFF(self.PLC.FF_ADDRESS["PCYCLE_ACCHARGE_FF"])
                            if message[key]["operation"]["CYLBLEED_FF"]:
                                self.PLC.WriteFF(self.PLC.FF_ADDRESS["PCYCLE_CYLBLEED_FF"])

                            if message[key]["operation"]["update"]:
                                self.PLC.Write_BO_2(self.PLC.PARAM_F_ADDRESS["PSET"],message[key]["operation"]["PSET"])
                                self.PLC.Write_BO_2_int32(self.PLC.PARAM_T_ADDRESS["MAXEXPTIME"],round(float(message[key]["operation"]["MAXEXPTIME"])*1000))
                                self.PLC.Write_BO_2_int32(self.PLC.PARAM_T_ADDRESS["MAXEQTIME"],round(float(message[key]["operation"]["MAXEXQTIME"])*1000))
                                self.PLC.Write_BO_2(self.PLC.PARAM_F_ADDRESS["MAXEQPDIFF"],
                                                    message[key]["operation"]["MAXEQPDIFF"])
                                self.PLC.Write_BO_2_int32(self.PLC.PARAM_T_ADDRESS["MAXACCTIME"],
                                                    round(float(message[key]["operation"]["MAXACCTIME"])*1000))
                                self.PLC.Write_BO_2(self.PLC.PARAM_F_ADDRESS["MAXACCDPDT"],
                                                    message[key]["operation"]["MAXACCDPDT"])

                                self.PLC.Write_BO_2_int32(self.PLC.PARAM_T_ADDRESS["MAXBLEEDTIME"],
                                                    round(float(message[key]["operation"]["MAXBLEEDTIME"])*1000))
                                self.PLC.Write_BO_2(self.PLC.PARAM_F_ADDRESS["MAXBLEEDDPDT"],
                                                    message[key]["operation"]["MAXBLEEDDPDT"])
                                self.PLC.Write_BO_2(self.PLC.PARAM_F_ADDRESS["SLOWCOMP_SET"],
                                                    message[key]["operation"]["SLOWCOMP_SET"])

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
                            self.PLC.LOOPPID_SETPOINT(address=message[key]["address"],
                                                      setpoint=message[key]["value"]["SETPOINT"], mode=0)
                            # self.PLC.LOOPPID_HI_LIM(address=message[key]["address"], value=message[key]["value"]["HI_LIM"])
                            # self.PLC.LOOPPID_LO_LIM(address=message[key]["address"], value=message[key]["value"]["LO_LIM"])
                            self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                                        value=message[key]["value"]["HI_LIM"])
                            self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                                        value=message[key]["value"]["LO_LIM"])

                        elif message[key]["operation"] == "SET1":
                            # self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=1)
                            self.PLC.LOOPPID_SETPOINT(address=message[key]["address"],
                                                      setpoint=message[key]["value"]["SETPOINT"], mode=1)
                            self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                                        value=message[key]["value"]["HI_LIM"])
                            self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                                        value=message[key]["value"]["LO_LIM"])
                        elif message[key]["operation"] == "SET2":
                            # self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=2)
                            self.PLC.LOOPPID_SETPOINT(address=message[key]["address"],
                                                      setpoint=message[key]["value"]["SETPOINT"], mode=2)
                            self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                                        value=message[key]["value"]["HI_LIM"])
                            self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                                        value=message[key]["value"]["LO_LIM"])
                        elif message[key]["operation"] == "SET3":
                            # self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=3)
                            self.PLC.LOOPPID_SETPOINT(address=message[key]["address"],
                                                      setpoint=message[key]["value"]["SETPOINT"], mode=3)
                            self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                                        value=message[key]["value"]["HI_LIM"])
                            self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                                        value=message[key]["value"]["LO_LIM"])
                        else:
                            pass

                    elif message[key]["type"] == "heater_setmode":
                        if message[key]["operation"] == "SET0":
                            self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=0)

                        elif message[key]["operation"] == "SET1":
                            # print(True)
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
                        print("PUMP", datetime_in_1e5micro())
                        if message[key]["operation"] == "OPEN":
                            self.PLC.LOOP2PT_OPEN(address=message[key]["address"])
                        elif message[key]["operation"] == "CLOSE":
                            self.PLC.LOOP2PT_CLOSE(address=message[key]["address"])
                        else:
                            pass

                    elif message[key]["type"] == "LOOP2PT_para":

                        if message[key]["operation"] == "SET1":
                            # self.PLC.LOOP2PT_SET_MODE(address=message[key]["address"], mode=1)
                            self.PLC.LOOP2PT_SETPOINT(address=message[key]["address"],
                                                      setpoint=message[key]["value"]["SETPOINT"], mode=1)

                        elif message[key]["operation"] == "SET2":
                            # self.PLC.LOOP2PT_SET_MODE(address=message[key]["address"], mode=2)
                            self.PLC.LOOP2PT_SETPOINT(address=message[key]["address"],
                                                      setpoint=message[key]["value"]["SETPOINT"], mode=2)

                        elif message[key]["operation"] == "SET3":
                            # self.PLC.LOOP2PT_SET_MODE(address=message[key]["address"], mode=3)
                            self.PLC.LOOP2PT_SETPOINT(address=message[key]["address"],
                                                      setpoint=message[key]["value"]["SETPOINT"], mode=3)
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
                    elif message[key]["type"] == "INTLK_A":
                        if message[key]["server"] == "BO":
                            if message[key]["operation"] == "ON":
                                self.PLC.WriteBase8(address=message[key]["address"])
                            elif message[key]["operation"] == "OFF":
                                self.PLC.WriteBase16(address=message[key]["address"])
                            elif message[key]["operation"] == "RESET":
                                self.PLC.WriteBase32(address=message[key]["address"])
                            elif message[key]["operation"] == "update":
                                self.PLC.Write_BO_2(message[key]["address"] + 2, message[key]["value"])
                            else:
                                pass
                    elif message[key]["type"] == "INTLK_D":
                        if message[key]["server"] == "BO":
                            if message[key]["operation"] == "ON":
                                self.PLC.WriteBase8(address=message[key]["address"])
                            elif message[key]["operation"] == "OFF":
                                self.PLC.WriteBase16(address=message[key]["address"])
                            elif message[key]["operation"] == "RESET":
                                self.PLC.WriteBase32(address=message[key]["address"])
                            else:
                                pass
                    elif message[key]["type"] == "FLAG":
                        print("time", datetime.datetime.now())
                        if message[key]["operation"] == "OPEN":
                            self.PLC.WriteBase2(address=message[key]["address"])
                        elif message[key]["operation"] == "CLOSE":
                            self.PLC.WriteBase4(address=message[key]["address"])
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
        elif "MAN_SET" in message:
            # manuall set the configuration

            for key in message["MAN_SET"]["data"]["TT"]["FP"]["high"]:
                self.PLC.TT_FP_HighLimit[key] = message["MAN_SET"]["data"]["TT"]["FP"]["high"][key]

            for key in message["MAN_SET"]["data"]["TT"]["BO"]["high"]:
                self.PLC.TT_BO_HighLimit[key] = message["MAN_SET"]["data"]["TT"]["BO"]["high"][key]

            for key in message["MAN_SET"]["data"]["PT"]["high"]:
                self.PLC.PT_HighLimit[key] = message["MAN_SET"]["data"]["PT"]["high"][key]

            for key in message["MAN_SET"]["data"]["LEFT_REAL"]["high"]:
                self.PLC.LEFT_REAL_HighLimit[key] = message["MAN_SET"]["data"]["LEFT_REAL"]["high"][key]

            for key in message["MAN_SET"]["data"]["Din"]["high"]:
                self.PLC.Din_HighLimit[key] = message["MAN_SET"]["data"]["Din"]["high"][key]

            for key in message["MAN_SET"]["data"]["LOOPPID"]["Alarm_HighLimit"]:

                self.PLC.LOOPPID_Alarm_HighLimit[key] = message["MAN_SET"]["data"]["LOOPPID"]["Alarm_HighLimit"][key]


            for key in message["MAN_SET"]["data"]["TT"]["FP"]["low"]:
                self.PLC.TT_FP_LowLimit[key] = message["MAN_SET"]["data"]["TT"]["FP"]["low"][key]

            for key in message["MAN_SET"]["data"]["TT"]["BO"]["low"]:
                self.PLC.TT_BO_LowLimit[key] = message["MAN_SET"]["data"]["TT"]["BO"]["low"][key]

            for key in message["MAN_SET"]["data"]["PT"]["low"]:
                self.PLC.PT_LowLimit[key] = message["MAN_SET"]["data"]["PT"]["low"][key]

            for key in message["MAN_SET"]["data"]["LEFT_REAL"]["low"]:
                self.PLC.LEFT_REAL_LowLimit[key] = message["MAN_SET"]["data"]["LEFT_REAL"]["low"][key]

            for key in message["MAN_SET"]["data"]["Din"]["low"]:
                self.PLC.Din_LowLimit[key] = message["MAN_SET"]["data"]["Din"]["low"][key]

            for key in message["MAN_SET"]["data"]["LOOPPID"]["Alarm_LowLimit"]:
                self.PLC.LOOPPID_Alarm_LowLimit[key] = message["MAN_SET"]["data"]["LOOPPID"]["Alarm_LowLimit"][key]

            for key in message["MAN_SET"]["Active"]["TT"]["FP"]:
                self.PLC.TT_FP_Activated[key] =message["MAN_SET"]["Active"]["TT"]["FP"][key]

            for key in message["MAN_SET"]["Active"]["TT"]["BO"]:
                self.PLC.TT_BO_Activated[key] = message["MAN_SET"]["Active"]["TT"]["BO"][key]

            for key in message["MAN_SET"]["Active"]["PT"]:
                self.PLC.PT_Activated[key] = message["MAN_SET"]["Active"]["PT"][key]

            for key in message["MAN_SET"]["Active"]["LEFT_REAL"]:
                self.PLC.LEFT_REAL_Activated[key] = message["MAN_SET"]["Active"]["LEFT_REAL"][key]

            for key in message["MAN_SET"]["Active"]["Din"]:
                self.PLC.Din_Activated[key] = message["MAN_SET"]["Active"]["Din"][key]

            for key in message["MAN_SET"]["Active"]["LOOPPID"]:
                self.PLC.LOOPPID_Activated[key] = message["MAN_SET"]["Active"]["LOOPPID"][key]


        else:
            print("Failed to load data from Client. MAN_SET is not either in or not in the received directory. Please check the code")


class Update(QtCore.QObject):
    PATCH_TO_DATABASE = QtCore.Signal()
    UPDATE_TO_DATABASE = QtCore.Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
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

        time.sleep(2)

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
        print("PLC is stopped")

        self.UpDatabase.stop()
        self.DataUpdateThread.quit()
        self.DataUpdateThread.wait()

        print("Database is stopped")
        self.UpServer.stop()
        self.ServerUpdateThread.quit()
        self.ServerUpdateThread.wait()
        print("ZMQ server is stopped")

        for i in range(10):
            print(i)
            time.sleep(1)

        sys.exit(App.exec_())

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
        self.UpPLC.COUPP_TEXT_alarm.connect(self.UpDatabase.receive_COUPP_ALARM)

        self.UpPLC.PLC.DATA_UPDATE_SIGNAL.connect(self.UpDatabase.update_value)
        self.UpPLC.PLC.DATA_UPDATE_SIGNAL.connect(self.transfer_station)
        self.PATCH_TO_DATABASE.connect(lambda: self.UpDatabase.update_value(self.data_transfer))

        self.UpPLC.PLC.DATA_TRI_SIGNAL.connect(self.PLCstatus_transfer)
        self.UPDATE_TO_DATABASE.connect(lambda: self.UpDatabase.update_status(self.data_status))

        self.UpPLC.PLC.PLC_DISCON_SIGNAL.connect(self.StopUpdater)
        print("signal established")





class message_manager():
    # add here the other alarm and data base
    def __init__(self):
        # info about tencent mail settings
        self.host_server = "smtp.qq.com"
        self.sender_qq = "390282332"
        self.pwd = "bngozrzmzsbocafa"
        self.sender_mail = "390282332@qq.com"
        # self.receiver1_mail = "cdahl@northwestern.edu"
        self.receiver1_mail = "runzezhang@foxmail.com"
        self.mail_title = "Alarm from SBC"


        # server to pico watchdog

        # info about slack settings
        # SLACK_BOT_TOKEN is a linux enviromental variable saved locally on sbcslowcontrol mathine
        # it can be fetched on slack app page in SBCAlarm app: https://api.slack.com/apps/A035X77RW64/general
        # if not_in_channel error type /invite @SBC_Alarm in channel
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


    App = QtWidgets.QApplication(sys.argv)
    Update=Update()


    # PLC=PLC()
    # PLC.ReadAll()python

    sys.exit(App.exec_())


