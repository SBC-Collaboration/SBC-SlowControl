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
from Database_SBC import *
from email.mime.text import MIMEText
from email.header import Header
from smtplib import SMTP_SSL
import requests
import logging,os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# delete random number package when you read real data from PLC
import random
from pymodbus.client.sync import ModbusTcpClient

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


        self.TT_FP_address = {"TT2420": 31000, "TT2422": 31002, "TT2424": 31004, "TT2425": 31006, "TT2442": 36000,
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

        self.TT_BO_address = {"TT2101": 12988, "TT2111": 12990, "TT2113": 12992, "TT2118": 12994, "TT2119": 12996,
                           "TT4330": 12998, "TT6203": 13000, "TT6207": 13002, "TT6211": 13004, "TT6213": 13006,
                           "TT6222": 13008, "TT6407": 13010, "TT6408": 13012, "TT6409": 13014, "TT6415": 13016,
                           "TT6416": 13018}

        self.PT_address={"PT1325": 12794, "PT2121": 12796, "PT2316": 12798, "PT2330": 12800, "PT2335": 12802,
                         "PT3308": 12804, "PT3309": 12806, "PT3311": 12808, "PT3314": 12810, "PT3320": 12812,
                         "PT3332": 12814, "PT3333": 12816, "PT4306": 12818, "PT4315": 12820,"PT4319": 12822,
                         "PT4322": 12824, "PT4325": 12826, "PT6302": 12828}

        self.LEFT_REAL_address = {'BFM4313': 12788, 'LT3335': 12790, 'MFC1316_IN': 12792,"CYL3334_FCALC":12832, "SERVO3321_IN_REAL":12830,"TS1_MASS":16288,"TS2_MASS":16290,"TS3_MASS":16292}


        self.TT_FP_dic = {"TT2420": 0, "TT2422": 0, "TT2424": 0, "TT2425": 0, "TT2442": 0,
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
                              "TT6412": 0, "TT6413": 0, "TT6414": 0}

        self.TT_BO_dic = {"TT2101": 0, "TT2111": 0, "TT2113": 0, "TT2118": 0, "TT2119": 0, "TT4330": 0,
                     "TT6203": 0, "TT6207": 0, "TT6211": 0, "TT6213": 0, "TT6222": 0,
                     "TT6407": 0, "TT6408": 0, "TT6409": 0, "TT6415": 0, "TT6416": 0}

        self.PT_dic = {"PT1325": 0, "PT2121": 0, "PT2316": 0, "PT2330": 0, "PT2335": 0,
                       "PT3308": 0, "PT3309": 0, "PT3311": 0, "PT3314": 0, "PT3320": 0,
                       "PT3332": 0, "PT3333": 0, "PT4306": 0, "PT4315": 0, "PT4319": 0,
                       "PT4322": 0, "PT4325": 0, "PT6302": 0}

        self.LEFT_REAL_dic = {'BFM4313': 0, 'LT3335': 0, 'MFC1316_IN': 0, "CYL3334_FCALC": 0, "SERVO3321_IN_REAL": 0, "TS1_MASS": 0, "TS2_MASS": 0, "TS3_MASS": 0}



        self.TT_FP_LowLimit = {"TT2420": 0, "TT2422": 0, "TT2424": 0, "TT2425": 0, "TT2442": 0,
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
                              "TT6412": 0, "TT6413": 0, "TT6414": 0}

        self.TT_FP_HighLimit = {"TT2420": 30, "TT2422": 30, "TT2424": 30, "TT2425": 30, "TT2442": 30,
                              "TT2403": 30, "TT2418": 30, "TT2427": 30, "TT2429": 30, "TT2431": 30,
                              "TT2441": 30, "TT2414": 30, "TT2413": 30, "TT2412": 30, "TT2415": 30,
                              "TT2409": 30, "TT2436": 30, "TT2438": 30, "TT2440": 30, "TT2402": 30,
                              "TT2411": 30, "TT2443": 30, "TT2417": 30, "TT2404": 30, "TT2408": 30,
                              "TT2407": 30, "TT2406": 30, "TT2428": 30, "TT2432": 30, "TT2421": 30,
                              "TT2416": 30, "TT2439": 30, "TT2419": 30, "TT2423": 30, "TT2426": 30,
                              "TT2430": 30, "TT2450": 30, "TT2401": 30, "TT2449": 30, "TT2445": 30,
                              "TT2444": 30, "TT2435": 30, "TT2437": 30, "TT2446": 30, "TT2447": 30,
                              "TT2448": 30, "TT2410": 30, "TT2405": 30, "TT6220": 30, "TT6401": 30,
                              "TT6404": 30, "TT6405": 30, "TT6406": 30, "TT6410": 30, "TT6411": 30,
                              "TT6412": 30, "TT6413": 30, "TT6414": 30}

        self.TT_BO_LowLimit = {"TT2101": 0, "TT2111": 0, "TT2113": 0, "TT2118": 0, "TT2119": 0, "TT4330": 0,
                            "TT6203": 0, "TT6207": 0, "TT6211": 0, "TT6213": 0, "TT6222": 0,
                            "TT6407": 0, "TT6408": 0, "TT6409": 0, "TT6415": 0, "TT6416": 0}


        self.TT_BO_HighLimit = {"TT2101": 30, "TT2111": 30, "TT2113": 30, "TT2118": 30, "TT2119": 30, "TT4330": 30,
                            "TT6203": 30, "TT6207": 30, "TT6211": 30, "TT6213": 30, "TT6222": 30,
                            "TT6407": 30, "TT6408": 30, "TT6409": 30, "TT6415": 30, "TT6416": 30}

        self.PT_LowLimit = {"PT1325": 0, "PT2121": 0, "PT2316": 0, "PT2330": 0, "PT2335": 0,
                            "PT3308": 0, "PT3309": 0, "PT3311": 0, "PT3314": 0, "PT3320": 0,
                            "PT3332": 0, "PT3333": 0, "PT4306": 0, "PT4315": 0, "PT4319": 0,
                            "PT4322": 0, "PT4325": 0, "PT6302": 0}
        self.PT_HighLimit = {"PT1325": 300, "PT2121": 300, "PT2316": 300, "PT2330": 300, "PT2335": 300,
                            "PT3308": 300, "PT3309": 300, "PT3311": 300, "PT3314": 300, "PT3320": 300,
                            "PT3332": 300, "PT3333": 300, "PT4306": 300, "PT4315": 300, "PT4319": 300,
                            "PT4322": 300, "PT4325": 300, "PT6302": 300}

        self.TT_FP_Activated = {"TT2420": True, "TT2422": True, "TT2424": True, "TT2425": True, "TT2442": True,
                              "TT2403": True, "TT2418": True, "TT2427": True, "TT2429": True, "TT2431": True,
                              "TT2441": True, "TT2414": True, "TT2413": True, "TT2412": True, "TT2415": True,
                              "TT2409": True, "TT2436": True, "TT2438": True, "TT2440": True, "TT2402": True,
                              "TT2411": True, "TT2443": True, "TT2417": True, "TT2404": True, "TT2408": True,
                              "TT2407": True, "TT2406": True, "TT2428": True, "TT2432": True, "TT2421": True,
                              "TT2416": True, "TT2439": True, "TT2419": True, "TT2423": True, "TT2426": True,
                              "TT2430": True, "TT2450": True, "TT2401": True, "TT2449": True, "TT2445": True,
                              "TT2444": True, "TT2435": True, "TT2437": True, "TT2446": True, "TT2447": True,
                              "TT2448": True, "TT2410": True, "TT2405": True, "TT6220": True, "TT6401": True,
                              "TT6404": True, "TT6405": True, "TT6406": True, "TT6410": True, "TT6411": True,
                              "TT6412": True, "TT6413": True, "TT6414": True}

        self.TT_BO_Activated = {"TT2101": True, "TT2111": True, "TT2113": True, "TT2118": True, "TT2119": True, "TT4330": True,
                             "TT6203": True, "TT6207": True, "TT6211": True, "TT6213": True, "TT6222": True,
                             "TT6407": True, "TT6408": True, "TT6409": True, "TT6415": True, "TT6416": True}

        self.PT_Activated = {"PT1325": True, "PT2121": True, "PT2316": True, "PT2330": True, "PT2335": True,
                             "PT3308": True, "PT3309": True, "PT3311": True, "PT3314": True, "PT3320": True,
                             "PT3332": True, "PT3333": True, "PT4306": True, "PT4315": True, "PT4319": True,
                             "PT4322": True, "PT4325": True, "PT6302": True}

        self.TT_FP_Alarm = {"TT2420": False, "TT2422": False, "TT2424": False, "TT2425": False, "TT2442": False,
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
                              "TT6412": False, "TT6413": False, "TT6414": False}

        self.TT_BO_Alarm = {"TT2101": False, "TT2111": False, "TT2113": False, "TT2118": False, "TT2119": False, "TT4330": False,
                         "TT6203": False, "TT6207": False, "TT6211": False, "TT6213": False, "TT6222": False,
                         "TT6407": False, "TT6408": False, "TT6409": False, "TT6415": False, "TT6416": False}

        self.PT_Alarm = {"PT1325": False, "PT2121": False, "PT2316": False, "PT2330": False, "PT2335": False,
                         "PT3308": False, "PT3309": False, "PT3311": False, "PT3314": False, "PT3320": False,
                         "PT3332": False, "PT3333": False, "PT4306": False, "PT4315": False, "PT4319": False,
                         "PT4322": False, "PT4325": False, "PT6302": False}
        self.MainAlarm = False
        self.nTT_BO = len(self.TT_BO_address)
        self.nTT_FP = len(self.TT_FP_address)
        self.nPT = len(self.PT_address)
        self.nREAL = len(self.LEFT_REAL_address)

        self.TT_BO_setting = [0.] * self.nTT_BO
        self.nTT_BO_Attribute = [0.] * self.nTT_BO
        self.PT_setting = [0.] * self.nPT
        self.nPT_Attribute = [0.] * self.nPT

        self.Switch_address = {"PUMP3305": 12688}
        self.nSwitch = len(self.Switch_address)
        self.Switch = {}
        self.Switch_OUT = {"PUMP3305": 0}
        self.Switch_MAN = {"PUMP3305": False}
        self.Switch_INTLKD = {"PUMP3305": False}
        self.Switch_ERR = {"PUMP3305": False}






        self.valve_address = {"PV1344": 12288, "PV4307": 12289, "PV4308": 12290, "PV4317": 12291, "PV4318": 12292, "PV4321": 12293,
                        "PV4324": 12294, "PV5305": 12295, "PV5306": 12296,
                        "PV5307": 12297, "PV5309": 12298, "SV3307": 12299, "SV3310": 12300, "SV3322": 12301,
                        "SV3325": 12302, "SV3329": 12304,
                        "SV4327": 12305, "SV4328": 12306, "SV4329": 12307, "SV4331": 12308, "SV4332": 12309,
                        "SV4337": 12310, "HFSV3312":12311, "HFSV3323": 12312, "HFSV3331": 12313}
        self.nValve = len(self.valve_address)
        self.Valve = {}
        self.Valve_OUT = {"PV1344": 0, "PV4307": 0, "PV4308": 0, "PV4317": 0, "PV4318": 0, "PV4321": 0,
                          "PV4324": 0, "PV5305": 0, "PV5306": 0,
                          "PV5307": 0, "PV5309": 0, "SV3307": 0, "SV3310": 0, "SV3322": 0,
                          "SV3325": 0, "SV3329": 0,
                          "SV4327": 0, "SV4328": 0, "SV4329": 0, "SV4331": 0, "SV4332": 0,
                          "SV4337": 0, "HFSV3312":0, "HFSV3323": 0, "HFSV3331": 0}
        self.Valve_MAN = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                          "PV4324": False, "PV5305": True, "PV5306": True,
                          "PV5307": True, "PV5309": True, "SV3307": True, "SV3310": True, "SV3322": True,
                          "SV3325": True,  "SV3329": True,
                          "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                          "SV4337": False, "HFSV3312": True, "HFSV3323": True, "HFSV3331": True}
        self.Valve_INTLKD = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                          "PV4324": False, "PV5305": False, "PV5306": False,
                          "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
                          "SV3325": False, "SV3329": False,
                          "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                          "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False}
        self.Valve_ERR = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                          "PV4324": False, "PV5305": False, "PV5306": False,
                          "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
                          "SV3325": False, "SV3329": False,
                          "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                          "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False}

        self.LOOPPID_ADR_BASE = {'SERVO3321': 14288, 'HTR6225': 14306, 'HTR2123': 14324, 'HTR2124': 14342, 'HTR2125': 14360,
                              'HTR1202': 14378, 'HTR2203': 14396, 'HTR6202': 14414, 'HTR6206': 14432, 'HTR6210': 14450,
                              'HTR6223': 14468, 'HTR6224': 14486, 'HTR6219': 14504, 'HTR6221': 14522, 'HTR6214': 14540}

        self.LOOPPID_MODE0 = {'SERVO3321': True, 'HTR6225': True, 'HTR2123': True, 'HTR2124': True, 'HTR2125': True,
                             'HTR1202': True, 'HTR2203': True, 'HTR6202': True, 'HTR6206': True, 'HTR6210': True,
                             'HTR6223': True, 'HTR6224': True, 'HTR6219': True, 'HTR6221': True, 'HTR6214': True}

        self.LOOPPID_MODE1 = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False, 'HTR2125': False,
                                                'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                                'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_MODE2 = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False, 'HTR2125': False,
                                                'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                                'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_MODE3 = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False, 'HTR2125': False,
                                                'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                                'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_INTLKD = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                                                'HTR2125': False,
                                                'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                                'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_MAN = {'SERVO3321': True, 'HTR6225': True, 'HTR2123': True, 'HTR2124': True,
                                             'HTR2125': True,
                                             'HTR1202': True, 'HTR2203': True, 'HTR6202': True, 'HTR6206': True, 'HTR6210': True,
                                             'HTR6223': True, 'HTR6224': True, 'HTR6219': True, 'HTR6221': True, 'HTR6214': True}

        self.LOOPPID_ERR = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                                                'HTR2125': False,
                                                'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                                'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_SATHI = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                                              'HTR2125': False,
                                              'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                              'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_SATLO = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                                               'HTR2125': False,
                                               'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                               'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_EN = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                                              'HTR2125': False,
                                              'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                              'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_OUT = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                                               'HTR2125': 0,
                                               'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                                               'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

        self.LOOPPID_IN = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                                                'HTR2125': 0,
                                                'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                                                'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

        self.LOOPPID_HI_LIM = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                                              'HTR2125': 0,
                                              'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                                              'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

        self.LOOPPID_LO_LIM = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                                             'HTR2125': 0,
                                             'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                                             'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

        self.LOOPPID_SET0 = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                                              'HTR2125': 0,
                                              'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                                              'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

        self.LOOPPID_SET1 = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                                           'HTR2125': 0,
                                           'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                                           'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

        self.LOOPPID_SET2 = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                                         'HTR2125': 0,
                                         'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                                         'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

        self.LOOPPID_SET3 = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                           'HTR2125': 0,
                           'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                           'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}



        self.LiveCounter = 0
        self.NewData_Display = False
        self.NewData_Database = False
        self.NewData_ZMQ=False

    def __del__(self):
        self.Client.close()
        self.Client_BO.close()

    def ReadAll(self):
        # print(self.TT_BO_HighLimit["TT2119"])
        # print(self.TT_BO_Alarm["TT2119"])
        if self.Connected:
            # Reading all the RTDs
            Raw_RTDs_FP={}
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

            #test endian of TT BO

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

                self.Valve_OUT[key]= self.ReadCoil(1,self.valve_address[key])
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

            Raw_LOOPPID_2 = {}
            Raw_LOOPPID_4 = {}
            Raw_LOOPPID_6 = {}
            Raw_LOOPPID_8 = {}
            Raw_LOOPPID_10 = {}
            Raw_LOOPPID_12 = {}
            Raw_LOOPPID_14 = {}
            Raw_LOOPPID_16 ={}
            for key in self.LOOPPID_ADR_BASE:
                self.LOOPPID_MODE0[key] = self.ReadCoil(1, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_MODE1[key] = self.ReadCoil(2, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_MODE2[key] = self.ReadCoil(2**2, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_MODE3[key] = self.ReadCoil(2**3, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_INTLKD[key] = self.ReadCoil(2**8, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_MAN[key] = self.ReadCoil(2 ** 9, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_ERR[key] = self.ReadCoil(2 ** 10, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_SATHI[key] = self.ReadCoil(2 ** 11, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_SATLO[key] = self.ReadCoil(2 ** 12, self.LOOPPID_ADR_BASE[key])
                self.LOOPPID_EN[key] = self.ReadCoil(2 ** 15, self.LOOPPID_ADR_BASE[key])
                Raw_LOOPPID_2[key] = self.Client_BO.read_holding_registers(self.LOOPPID_ADR_BASE[key]+2, count=2, unit=0x01)
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


            #test the writing function
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

            self.NewData_Display = True
            self.NewData_Database = True
            self.NewData_ZMQ = True

            return 0
        else:
            raise Exception('Not connected to PLC') #will it restart the PLC ?

            return 1

    def Read_BO_1(self,address):
        Raw_BO = self.Client_BO.read_holding_registers(address, count=1, unit=0x01)
        output_BO = struct.pack("H", Raw_BO.getRegister(0))
        # print("valve value is", output_BO)
        return output_BO

    def Read_BO_2(self,address):
        Raw_BO = self.Client_BO.read_holding_registers(address, count=2, unit=0x01)
        output_BO = round(struct.unpack(">f", struct.pack(">HH", Raw_BO.getRegister(1), Raw_BO.getRegister(0)))[
                0], 3)
        # print("valve value is", output_BO)
        return output_BO

    def float_to_2words(self,value):
        fl = float(value)
        x = np.arange(fl, fl+1, dtype='<f4')
        if len(x) == 1:
            word = x.tobytes()
            piece1,piece2 = struct.unpack('<HH',word)
        else:
            print("ERROR in float to words")
        return piece1,piece2

    def Write_BO_2(self,address, value):
        word1, word2 = self.float_to_2words(value)
        print('words',word1,word2)
        # pay attention to endian relationship
        Raw1 = self.Client_BO.write_register(address, value=word1, unit=0x01)
        Raw2 = self.Client_BO.write_register(address+1, value=word2, unit=0x01)

        print("write result = ", Raw1, Raw2)


    def WriteOpen(self,address):
        output_BO = self.Read_BO_1(address)
        input_BO= struct.unpack("H",output_BO)[0] | 0x0002
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write open result=", Raw)

    def WriteClose(self,address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H",output_BO)[0] | 0x0004
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write close result=", Raw)

    def Reset(self,address):
        Raw = self.Client_BO.write_register(address, value=0x0010, unit=0x01)
        print("write reset result=", Raw)

    # mask is a number to read a particular digit. for example, if you want to read 3rd digit, the mask is 0100(binary)
    def ReadCoil(self, mask,address):
        output_BO = self.Read_BO_1(address)
        masked_output = struct.unpack("H",output_BO)[0] & mask
        if masked_output == 0:
            return False
        else:
            return True


    def ReadFPAttribute(self,address):
        Raw = self.Client.read_holding_registers(address, count=1, unit=0x01)
        output = struct.pack("H", Raw.getRegister(0))
        print(Raw.getRegister(0))
        return output

    def SetFPRTDAttri(self,mode,address):
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

        print("write result:", "mode=",  Raw)

    def LOOPPID_OUT_ENA(self,address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x2000
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write OUT result=", Raw)

    def LOOPPID_OUT_DIS(self,address):
        output_BO = self.Read_BO_1(address)
        input_BO = struct.unpack("H", output_BO)[0] | 0x4000
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write OUT result=", Raw)

    def LOOPPID_SETPOINT(self, address, setpoint, mode = 0):
        if mode == 0:
            self.Write_BO_2(address+10, setpoint)
        elif mode == 1:
            self.Write_BO_2(address+12, setpoint)
        elif mode == 2:
            self.Write_BO_2(address+14, setpoint)
        elif mode == 3:
            self.Write_BO_2(address+16, setpoint)
        else:
            pass

        print("LOOPPID_SETPOINT")

    def LOOPPID_SET_HI_LIM(self,address, value):
        self.Write_BO_2(address + 6, value)
        print("LOOPPID_HI")

    def LOOPPID_SET_LO_LIM(self,address, value):
        self.Write_BO_2(address + 8, value)
        print("LOOPPID_LO")

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
        self.base_period=1
        self.para_TT=0
        self.rate_TT=30
        self.para_PT=0
        self.rate_PT=30
        self.para_REAL = 0
        self.rate_REAL = 30
        # c is for valve status
        self.para_Valve = 0
        self.rate_Valve = 30
        self.para_Switch = 0
        self.rate_Switch = 30
        self.para_LOOPPID = 0
        self.rate_LOOPPID = 30
        self.Valve_buffer = {"PV1344": 0, "PV4307": 0, "PV4308": 0, "PV4317": 0, "PV4318": 0, "PV4321": 0,
                          "PV4324": 0, "PV5305": 0, "PV5306": 0,
                          "PV5307": 0, "PV5309": 0, "SV3307": 0, "SV3310": 0, "SV3322": 0,
                          "SV3325": 0,  "SV3329": 0,
                          "SV4327": 0, "SV4328": 0, "SV4329": 0, "SV4331": 0, "SV4332": 0,
                          "SV4337": 0, "HFSV3312":0, "HFSV3323": 0, "HFSV3331": 0}
        self.Switch_buffer = {"PUMP3305": 0}
        self.LOOPPID_EN_buffer = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                                              'HTR2125': False,
                                              'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                              'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_MODE0_buffer = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                                  'HTR2125': False,
                                  'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                  'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_MODE1_buffer = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                                  'HTR2125': False,
                                  'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                  'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_MODE2_buffer = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                                  'HTR2125': False,
                                  'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                  'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_MODE3_buffer = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                                  'HTR2125': False,
                                  'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                                  'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

        self.LOOPPID_OUT_buffer = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                                  'HTR2125': 0,
                                  'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                                  'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

        self.LOOPPID_IN_buffer = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                                  'HTR2125': 0,
                                  'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                                  'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

        print("begin updating Database")

    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:
            self.dt = datetime_in_1e5micro()
            self.early_dt= early_datetime()
            print("Database Updating", self.dt)

            if self.PLC.NewData_Database:
                if self.para_TT>= self.rate_TT:
                    for key in self.PLC.TT_FP_dic:
                        self.db.insert_data_into_datastorage(key, self.dt, self.PLC.TT_FP_dic[key])
                    for key in self.PLC.TT_BO_dic:
                        self.db.insert_data_into_datastorage(key, self.dt, self.PLC.TT_BO_dic[key])
                    # print("write RTDS")
                    self.para_TT=0
                if self.para_PT >= self.rate_PT:
                    for key in self.PLC.PT_dic:
                        self.db.insert_data_into_datastorage(key, self.dt, self.PLC.PT_dic[key])
                    # print("write pressure transducer")
                    self.para_PT=0

                for key in self.PLC.Valve_OUT:
                    # print(key, self.PLC.Valve_OUT[key] != self.Valve_buffer[key])
                    if self.PLC.Valve_OUT[key] != self.Valve_buffer[key]:
                        self.db.insert_data_into_datastorage(key + '_OUT', self.early_dt, self.Valve_buffer[key])
                        self.db.insert_data_into_datastorage(key+'_OUT', self.dt, self.PLC.Valve_OUT[key])
                        self.Valve_buffer[key] = self.PLC.Valve_OUT[key]
                        # print(self.PLC.Valve_OUT[key])
                    else:
                        pass

                if self.para_Valve >= self.rate_Valve:
                    for key in self.PLC.Valve_OUT:
                        self.db.insert_data_into_datastorage(key+'_OUT', self.dt, self.PLC.Valve_OUT[key])
                        self.Valve_buffer[key] = self.PLC.Valve_OUT[key]
                    self.para_Valve = 0


                for key in self.PLC.Switch_OUT:
                    # print(key, self.PLC.Switch_OUT[key] != self.Switch_buffer[key])
                    if self.PLC.Switch_OUT[key] != self.Switch_buffer[key]:
                        self.db.insert_data_into_datastorage(key + '_OUT', self.early_dt, self.Switch_buffer[key])
                        self.db.insert_data_into_datastorage(key+'_OUT', self.dt, self.PLC.Switch_OUT[key])
                        self.Switch_buffer[key] = self.PLC.Switch_OUT[key]
                        # print(self.PLC.Switch_OUT[key])
                    else:
                        pass

                if self.para_Switch >= self.rate_Switch:
                    for key in self.PLC.Switch_OUT:
                        self.db.insert_data_into_datastorage(key+'_OUT', self.dt, self.PLC.Switch_OUT[key])
                        self.Switch_buffer[key] = self.PLC.Switch_OUT[key]
                    self.para_Switch = 0

                # if state of bool variable changes, write the data into database

                for key in self.PLC.LOOPPID_EN:
                    # print(key, self.PLC.Valve_OUT[key] != self.Valve_buffer[key])
                    if self.PLC.LOOPPID_EN[key] != self.LOOPPID_EN_buffer[key]:
                        self.db.insert_data_into_datastorage(key + '_EN', self.early_dt, self.LOOPPID_EN_buffer[key])
                        self.db.insert_data_into_datastorage(key+'_EN', self.dt, self.PLC.LOOPPID_EN[key])
                        self.LOOPPID_EN_buffer[key] = self.PLC.LOOPPID_EN[key]
                        # print(self.PLC.Valve_OUT[key])
                    else:
                        pass

                for key in self.PLC.LOOPPID_MODE0:
                    # print(key, self.PLC.Valve_OUT[key] != self.Valve_buffer[key])
                    if self.PLC.LOOPPID_MODE0[key] != self.LOOPPID_MODE0_buffer[key]:
                        self.db.insert_data_into_datastorage(key + '_MODE0', self.early_dt, self.LOOPPID_MODE0_buffer[key])
                        self.db.insert_data_into_datastorage(key+'_MODE0', self.dt, self.PLC.LOOPPID_MODE0[key])
                        self.LOOPPID_MODE0_buffer[key] = self.PLC.LOOPPID_MODE0[key]
                        # print(self.PLC.Valve_OUT[key])
                    else:
                        pass

                for key in self.PLC.LOOPPID_MODE1:
                    # print(key, self.PLC.Valve_OUT[key] != self.Valve_buffer[key])
                    if self.PLC.LOOPPID_MODE1[key] != self.LOOPPID_MODE1_buffer[key]:
                        self.db.insert_data_into_datastorage(key + '_MODE1', self.early_dt, self.LOOPPID_MODE1_buffer[key])
                        self.db.insert_data_into_datastorage(key+'_MODE1', self.dt, self.PLC.LOOPPID_MODE1[key])
                        self.LOOPPID_MODE1_buffer[key] = self.PLC.LOOPPID_MODE1[key]
                        # print(self.PLC.Valve_OUT[key])
                    else:
                        pass

                for key in self.PLC.LOOPPID_MODE2:
                    # print(key, self.PLC.Valve_OUT[key] != self.Valve_buffer[key])
                    if self.PLC.LOOPPID_MODE2[key] != self.LOOPPID_MODE2_buffer[key]:
                        self.db.insert_data_into_datastorage(key + '_MODE2', self.early_dt, self.LOOPPID_MODE2_buffer[key])
                        self.db.insert_data_into_datastorage(key+'_MODE2', self.dt, self.PLC.LOOPPID_MODE2[key])
                        self.LOOPPID_MODE2_buffer[key] = self.PLC.LOOPPID_MODE2[key]
                        # print(self.PLC.Valve_OUT[key])
                    else:
                        pass

                for key in self.PLC.LOOPPID_MODE3:
                    # print(key, self.PLC.Valve_OUT[key] != self.Valve_buffer[key])
                    if self.PLC.LOOPPID_MODE3[key] != self.LOOPPID_MODE3_buffer[key]:
                        self.db.insert_data_into_datastorage(key + '_MODE3', self.early_dt, self.LOOPPID_MODE3_buffer[key])
                        self.db.insert_data_into_datastorage(key+'_MODE3', self.dt, self.PLC.LOOPPID_MODE3[key])
                        self.LOOPPID_MODE3_buffer[key] = self.PLC.LOOPPID_MODE3[key]
                        # print(self.PLC.Valve_OUT[key])
                    else:
                        pass

                #if no changes, write the data every fixed time interval

                if self.para_LOOPPID >= self.rate_LOOPPID:
                    for key in self.PLC.LOOPPID_EN:
                        self.db.insert_data_into_datastorage(key+'_EN', self.dt, self.PLC.LOOPPID_EN[key])
                        self.LOOPPID_EN_buffer[key] = self.PLC.LOOPPID_EN[key]
                    for key in self.PLC.LOOPPID_MODE0:
                        self.db.insert_data_into_datastorage(key+'_MODE0', self.dt, self.PLC.LOOPPID_MODE0[key])
                        self.LOOPPID_MODE0_buffer[key] = self.PLC.LOOPPID_MODE0[key]
                    for key in self.PLC.LOOPPID_MODE1:
                        self.db.insert_data_into_datastorage(key+'_MODE1', self.dt, self.PLC.LOOPPID_MODE1[key])
                        self.LOOPPID_MODE1_buffer[key] = self.PLC.LOOPPID_MODE1[key]
                    for key in self.PLC.LOOPPID_MODE2:
                        self.db.insert_data_into_datastorage(key+'_MODE2', self.dt, self.PLC.LOOPPID_MODE2[key])
                        self.LOOPPID_MODE2_buffer[key] = self.PLC.LOOPPID_MODE2[key]
                    for key in self.PLC.LOOPPID_MODE3:
                        self.db.insert_data_into_datastorage(key+'_MODE3', self.dt, self.PLC.LOOPPID_MODE3[key])
                        self.LOOPPID_MODE3_buffer[key] = self.PLC.LOOPPID_MODE3[key]
                    # write float data.
                    for key in self.PLC.LOOPPID_OUT:
                        self.db.insert_data_into_datastorage(key+'_OUT', self.dt, self.PLC.LOOPPID_OUT[key])
                        self.LOOPPID_OUT_buffer[key] = self.PLC.LOOPPID_OUT[key]
                    for key in self.PLC.LOOPPID_IN:
                        self.db.insert_data_into_datastorage(key+'_IN', self.dt, self.PLC.LOOPPID_IN[key])
                        self.LOOPPID_IN_buffer[key] = self.PLC.LOOPPID_IN[key]
                    self.para_LOOPPID = 0

                if self.para_REAL >= self.rate_REAL:
                    for key in self.PLC.LEFT_REAL_address:
                        # print(key, self.PLC.LEFT_REAL_dic[key])
                        self.db.insert_data_into_datastorage(key, self.dt, self.PLC.LEFT_REAL_dic[key])
                    # print("write pressure transducer")
                    self.para_REAL=0

                # print("a",self.para_TT,"b",self.para_PT )

                print("Wrting PLC data to database...")
                self.para_TT += 1
                self.para_PT += 1
                self.para_Valve += 1
                self.para_Switch += 1
                self.para_LOOPPID += 1
                self.para_REAL += 1
                self.PLC.NewData_Database = False

            else:

                print("No new data from PLC")
                pass

            time.sleep(self.base_period)


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
        self.period=1

    @QtCore.Slot()
    def run(self):
        try:
            self.Running = True

            while self.Running:
                print("PLC updating", datetime.datetime.now())
                self.PLC.ReadAll()
                for keyTT_FP in self.PLC.TT_FP_dic:
                    self.check_TT_FP_alarm(keyTT_FP)
                for keyTT_BO in self.PLC.TT_BO_dic:
                    self.check_TT_BO_alarm(keyTT_BO)
                for keyPT in self.PLC.PT_dic:
                    self.check_PT_alarm(keyPT)
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

    def check_TT_FP_alarm(self, pid):

        if self.PLC.TT_FP_Activated[pid]:
            if int(self.PLC.TT_FP_LowLimit[pid]) > int(self.PLC.TT_FP_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if int(self.PLC.TT_FP_dic[pid]) < int(self.PLC.TT_FP_LowLimit[pid]):
                    self.setTTFPalarm(pid)
                    self.PLC.TT_FP_Alarm[pid] = True
                    # print(pid , " reading is lower than the low limit")
                elif int(self.PLC.TT_FP_dic[pid]) > int(self.PLC.TT_FP_HighLimit[pid]):
                    self.setTTFPalarm(pid)
                    # print(pid,  " reading is higher than the high limit")
                else:
                    self.resetTTFPalarm(pid)
                    # print(pid, " is in normal range")

        else:
            self.resetTTFPalarm(pid)
            pass

    def check_TT_BO_alarm(self, pid):

        if self.PLC.TT_BO_Activated[pid]:
            if int(self.PLC.TT_BO_LowLimit[pid]) > int(self.PLC.TT_BO_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if int(self.PLC.TT_BO_dic[pid]) < int(self.PLC.TT_BO_LowLimit[pid]):
                    self.setTTBOalarm(pid)
                    self.PLC.TT_BO_Alarm[pid] = True
                    # print(pid , " reading is lower than the low limit")
                elif int(self.PLC.TT_BO_dic[pid]) > int(self.PLC.TT_BO_HighLimit[pid]):
                    self.setTTBOalarm(pid)
                    # print(pid,  " reading is higher than the high limit")
                else:
                    self.resetTTBOalarm(pid)
                    # print(pid, " is in normal range")

        else:
            self.resetTTBOalarm(pid)
            pass

    def check_PT_alarm(self, pid):

        if self.PLC.PT_Activated[pid]:
            if int(self.PLC.PT_LowLimit[pid]) > int(self.PLC.PT_HighLimit[pid]):
                print("Low limit should be less than high limit!")
            else:
                if int(self.PLC.PT_dic[pid]) < int(self.PLC.PT_LowLimit[pid]):
                    self.setPTalarm(pid)
                    self.PLC.PT_Alarm[pid] = True
                    # print(pid , " reading is lower than the low limit")
                elif int(self.PLC.PT_dic[pid]) > int(self.PLC.PT_HighLimit[pid]):
                    self.setPTalarm(pid)
                    # print(pid,  " reading is higher than the high limit")
                else:
                    self.resetPTalarm(pid)
                    # print(pid, " is in normal range")

        else:
            self.resetPTalarm(pid)
            pass

    def setTTFPalarm(self, pid):
        self.PLC.TT_FP_Alarm[pid] = True
        # and send email or slack messages
        msg = "SBC alarm: {pid} is out of range".format(pid=pid)
        # self.message_manager.tencent_alarm(msg)
        # self.message_manager.slack_alarm(msg)

    def resetTTFPalarm(self, pid):
        self.PLC.TT_FP_Alarm[pid] = False
        # and send email or slack messages

    def setTTBOalarm(self, pid):
        self.PLC.TT_BO_Alarm[pid] = True
        # and send email or slack messages
        msg = "SBC alarm: {pid} is out of range".format(pid=pid)
        # self.message_manager.tencent_alarm(msg)
        # self.message_manager.slack_alarm(msg)

    def resetTTBOalarm(self, pid):
        self.PLC.TT_BO_Alarm[pid] = False
        # and send email or slack messages

    def setPTalarm(self, pid):
        self.PLC.PT_Alarm[pid] = True
        # and send email or slack messages
        msg = "SBC alarm: {pid} is out of range".format(pid=pid)
        # self.message_manager.tencent_alarm(msg)
        # self.message_manager.slack_alarm(msg)

    def resetPTalarm(self, pid):
        self.PLC.PT_Alarm[pid] = False
        # and send email or slack messages

    def or_alarm_signal(self):
        if (True in self.PLC.TT_BO_Alarm) or (True in self.PLC.PT_Alarm) or (True in self.PLC.TT_FP_Alarm):
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
        self.period=1
        print("connect to the PLC server")


        self.TT_FP_dic_ini = self.PLC.TT_FP_dic
        self.TT_BO_dic_ini = self.PLC.TT_BO_dic
        self.PT_dic_ini = self.PLC.PT_dic
        self.LEFT_REAL_ini = self.PLC.LEFT_REAL_dic
        self.TT_FP_LowLimit_ini = self.PLC.TT_FP_LowLimit
        self.TT_FP_HighLimit_ini = self.PLC.TT_FP_HighLimit
        self.TT_BO_LowLimit_ini = self.PLC.TT_BO_LowLimit
        self.TT_BO_HighLimit_ini = self.PLC.TT_BO_HighLimit
        self.PT_LowLimit_ini = self.PLC.PT_LowLimit
        self.PT_HighLimit_ini = self.PLC.PT_HighLimit
        self.TT_FP_Activated = self.PLC.TT_FP_Activated
        self.TT_BO_Activated_ini = self.PLC.TT_BO_Activated
        self.PT_Activated_ini = self.PLC.PT_Activated
        self.TT_FP_Alarm_ini = self.PLC.TT_FP_Alarm
        self.TT_BO_Alarm_ini = self.PLC.TT_BO_Alarm
        self.PT_Alarm_ini = self.PLC.PT_Alarm
        self.MainAlarm_ini = self.PLC.MainAlarm
        self.Valve_OUT_ini = self.PLC.Valve_OUT
        self.Valve_MAN_ini = self.PLC.Valve_MAN
        self.Valve_INTLKD_ini = self.PLC.Valve_INTLKD
        self.Valve_ERR_ini = self.PLC.Valve_ERR
        self.Switch_OUT_ini = self.PLC.Switch_OUT
        self.Switch_MAN_ini = self.PLC.Switch_MAN
        self.Switch_INTLKD_ini = self.PLC.Switch_INTLKD
        self.Switch_ERR_ini = self.PLC.Switch_ERR
        self.LOOPPID_MODE0_ini = self.PLC.LOOPPID_MODE0
        self.LOOPPID_MODE1_ini = self.PLC.LOOPPID_MODE1
        self.LOOPPID_MODE2_ini = self.PLC.LOOPPID_MODE2
        self.LOOPPID_MODE3_ini = self.PLC.LOOPPID_MODE3
        self.LOOPPID_INTLKD_ini = self.PLC.LOOPPID_INTLKD
        self.LOOPPID_MAN_ini = self.PLC.LOOPPID_MAN
        self.LOOPPID_ERR_ini = self.PLC.LOOPPID_ERR
        self.LOOPPID_SATHI_ini = self.PLC.LOOPPID_SATHI
        self.LOOPPID_SATLO_ini = self.PLC.LOOPPID_SATLO
        self.LOOPPID_EN_ini = self.PLC.LOOPPID_EN
        self.LOOPPID_OUT_ini = self.PLC.LOOPPID_OUT
        self.LOOPPID_IN_ini = self.PLC.LOOPPID_IN
        self.LOOPPID_HI_LIM_ini = self.PLC.LOOPPID_HI_LIM
        self.LOOPPID_LO_LIM_ini = self.PLC.LOOPPID_LO_LIM
        self.LOOPPID_SET0_ini = self.PLC.LOOPPID_SET0
        self.LOOPPID_SET1_ini = self.PLC.LOOPPID_SET1
        self.LOOPPID_SET2_ini = self.PLC.LOOPPID_SET2
        self.LOOPPID_SET3_ini = self.PLC.LOOPPID_SET3

        self.data_dic={"data":{"TT":{"FP":self.TT_FP_dic_ini,
                                     "BO":self.TT_BO_dic_ini},
                               "PT":self.PT_dic_ini,
                               "LEFT_REAL":self.LEFT_REAL_ini,
                               "Valve":{"OUT":self.Valve_OUT_ini,
                                        "INTLKD":self.Valve_INTLKD_ini,
                                        "MAN":self.Valve_MAN_ini,
                                        "ERR":self.Valve_ERR_ini},
                               "Switch": {"OUT": self.Switch_OUT_ini,
                                         "INTLKD": self.Switch_INTLKD_ini,
                                         "MAN": self.Switch_MAN_ini,
                                         "ERR": self.Switch_ERR_ini},
                               "LOOPPID":{"MODE0": self.LOOPPID_MODE0_ini,
                                          "MODE1": self.LOOPPID_MODE1_ini,
                                          "MODE2": self.LOOPPID_MODE2_ini,
                                          "MODE3": self.LOOPPID_MODE3_ini,
                                          "INTLKD" : self.LOOPPID_INTLKD_ini,
                                          "MAN" : self.LOOPPID_MAN_ini,
                                         "ERR" : self.LOOPPID_ERR_ini,
                                         "SATHI" : self.LOOPPID_SATHI_ini,
                                        "SATLO" : self.LOOPPID_SATLO_ini,
                                        "EN" : self.LOOPPID_EN_ini,
                                        "OUT" : self.LOOPPID_OUT_ini,
                                        "IN" : self.LOOPPID_IN_ini,
                                        "HI_LIM" : self.LOOPPID_HI_LIM_ini,
                                        "LO_LIM" : self.LOOPPID_LO_LIM_ini,
                                        "SET0" : self.LOOPPID_SET0_ini,
                                        "SET1" : self.LOOPPID_SET1_ini,
                                        "SET2" : self.LOOPPID_SET2_ini,
                                        "SET3" : self.LOOPPID_SET3_ini}},
                       "Alarm":{"TT" : {"FP":self.TT_FP_Alarm_ini,
                                      "BO":self.TT_BO_Alarm_ini},
                                "PT" : self.PT_Alarm_ini},
                       "MainAlarm" : self.MainAlarm_ini}

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


        for key in self.PLC.TT_FP_dic:
            self.TT_FP_dic_ini[key] = self.PLC.TT_FP_dic[key]

        for key in self.PLC.TT_BO_dic:
            self.TT_BO_dic_ini[key]=self.PLC.TT_BO_dic[key]
        for key in self.PLC.PT_dic:
            self.PT_dic_ini[key]=self.PLC.PT_dic[key]
        for key in self.PLC.LEFT_REAL_dic:
            self.LEFT_REAL_ini[key]=self.PLC.LEFT_REAL_dic[key]
        for key in self.PLC.Valve_OUT:
            self.Valve_OUT_ini[key]=self.PLC.Valve_OUT[key]
        for key in self.PLC.Valve_INTLKD:
            self.Valve_INTLKD_ini[key]=self.PLC.Valve_INTLKD[key]
        for key in self.PLC.Valve_MAN:
            self.Valve_MAN_ini[key]=self.PLC.Valve_MAN[key]
        for key in self.PLC.Valve_ERR:
            self.Valve_ERR_ini[key]=self.PLC.Valve_ERR[key]
        for key in self.PLC.Switch_OUT:
            self.Switch_OUT_ini[key]=self.PLC.Switch_OUT[key]
        for key in self.PLC.Switch_INTLKD:
            self.Switch_INTLKD_ini[key]=self.PLC.Switch_INTLKD[key]
        for key in self.PLC.Switch_MAN:
            self.Switch_MAN_ini[key]=self.PLC.Switch_MAN[key]
        for key in self.PLC.Switch_ERR:
            self.Switch_ERR_ini[key]=self.PLC.Switch_ERR[key]


        for key in self.PLC.TT_FP_Alarm:
            self.TT_FP_Alarm_ini[key] = self.PLC.TT_FP_Alarm[key]
        for key in self.PLC.TT_BO_Alarm:
            self.TT_BO_Alarm_ini[key] = self.PLC.TT_BO_Alarm[key]
        for key in self.PLC.PT_dic:
            self.PT_Alarm_ini[key] = self.PLC.PT_Alarm[key]
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

        self.data_dic["MainAlarm"]=self.PLC.MainAlarm
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

        self.data_package=pickle.dumps(self.data_dic)

    def write_data(self):
        message = pickle.loads(self.socket.recv())
        print(message)
        if message == {}:
            pass
        else:
            for key in message:
                print(message[key]["type"])
                print(message[key]["type"]=="valve")
                if message[key]["type"]=="valve":
                    if message[key]["operation"]=="OPEN":
                        self.PLC.WriteOpen(address= message[key]["address"])
                    elif message[key]["operation"]=="CLOSE":
                        self.PLC.WriteClose(address= message[key]["address"])
                    else:
                        pass
                if message[key]["type"]=="switch":
                    if message[key]["operation"]=="ON":
                        self.PLC.WriteOpen(address= message[key]["address"])
                    elif message[key]["operation"]=="OFF":
                        self.PLC.WriteClose(address= message[key]["address"])
                    else:
                        pass
                elif message[key]["type"] == "TT":
                    if message[key]["server"] == "BO":
                        self.PLC.TT_BO_Activated[key] = message[key]["operation"]["Act"]
                        self.PLC.TT_BO_LowLimit[key] = message[key]["operation"]["LowLimit"]
                        self.PLC.TT_BO_HighLimit[key] = message[key]["operation"]["HighLimit"]

                    elif message[key]["server"] == "FP":
                        self.PLC.TT_FP_Activated[key] = message[key]["operation"]["Act"]
                        self.PLC.TT_FP_LowLimit[key] = message[key]["operation"]["LowLimit"]
                        self.PLC.TT_FP_HighLimit[key] = message[key]["operation"]["HighLimit"]
                    else:
                        pass
                elif message[key]["type"] == "PT":
                    if message[key]["server"] == "BO":
                        self.PLC.PT_Activated[key] = message[key]["operation"]["Act"]
                        self.PLC.PT_LowLimit[key] = message[key]["operation"]["LowLimit"]
                        self.PLC.PT_HighLimit[key] = message[key]["operation"]["HighLimit"]
                    else:
                        pass
                elif message[key]["type"] == "heater_power":
                    if message[key]["operation"] == "EN":
                        self.PLC.LOOPPID_OUT_ENA(address = message[key]["address"])
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
                        self.PLC.LOOPPID_SETPOINT( address= message[key]["address"], setpoint = message[key]["value"]["SETPOINT"], mode = 0)
                        # self.PLC.LOOPPID_HI_LIM(address=message[key]["address"], value=message[key]["value"]["HI_LIM"])
                        # self.PLC.LOOPPID_LO_LIM(address=message[key]["address"], value=message[key]["value"]["LO_LIM"])
                        self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["HI_LIM"])
                        self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["LO_LIM"])

                    elif message[key]["operation"] == "SET1":
                        # self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=1)
                        self.PLC.LOOPPID_SETPOINT( address= message[key]["address"], setpoint = message[key]["value"]["SETPOINT"], mode = 1)
                        self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["HI_LIM"])
                        self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["LO_LIM"])
                    elif message[key]["operation"] == "SET2":
                        # self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=2)
                        self.PLC.LOOPPID_SETPOINT( address= message[key]["address"], setpoint = message[key]["value"]["SETPOINT"], mode = 2)
                        self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["HI_LIM"])
                        self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"],
                                                    value=message[key]["value"]["LO_LIM"])
                    elif message[key]["operation"] == "SET3":
                        # self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode=3)
                        self.PLC.LOOPPID_SETPOINT( address= message[key]["address"], setpoint = message[key]["value"]["SETPOINT"], mode = 3)
                        self.PLC.LOOPPID_SET_HI_LIM(address=message[key]["address"], value=message[key]["value"]["HI_LIM"])
                        self.PLC.LOOPPID_SET_LO_LIM(address=message[key]["address"], value=message[key]["value"]["LO_LIM"])
                    else:
                        pass

                elif message[key]["type"] == "heater_setmode":
                    if message[key]["operation"] == "SET0":
                        self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode= 0)

                    elif message[key]["operation"] == "SET1":
                        print(True)
                        self.PLC.LOOPPID_SET_MODE(address=message[key]["address"], mode = 1)

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



                else:
                    pass



        # if message == b'this is a command':
        #     self.PLC.WriteOpen()
        #     self.PLC.Read_BO_1()
        #     print("I will set valve")
        # elif message == b'no command':
        #     self.PLC.WriteClose()
        #     self.PLC.Read_BO_1()
        #     print("I will stay here")
        # elif message == b'this an anti_conmmand':
        #
        #     print("reset the valve")
        # else:
        #     print("I didn't see any command")
        #     pass



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

        # wait for PLC initialization finished
        time.sleep(2)

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
        self.client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
        self.logger = logging.getLogger(__name__)
        self.channel_id = "C01918B8WDD"

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

    def slack_alarm(self, message):
        # ID of channel you want to post message to


        try:
            # Call the conversations.list method using the WebClient
            result = self.client.chat_postMessage(
                channel=self.channel_id,
                text=message
                # You could also use a blocks[] array to send richer content
            )
            # Print result, which includes information about the message (like TS)
            print(result)

        except SlackApiError as e:
            print(f"Error: {e}")




if __name__ == "__main__":
    # msg_mana=message_manager()
    # msg_mana.tencent_alarm("this is a test message")

    App = QtWidgets.QApplication(sys.argv)
    Update=Update()


    # PLC=PLC()
    # PLC.ReadAll()

    sys.exit(App.exec_())


