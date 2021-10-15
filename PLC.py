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

        self.TT_BO_dic={"TT2101": 0, "TT2111": 0, "TT2113": 0, "TT2118": 0, "TT2119": 0, "TT4330": 0,
                     "TT6203": 0, "TT6207": 0, "TT6211": 0, "TT6213": 0, "TT6222": 0,
                     "TT6407": 0, "TT6408": 0, "TT6409": 0, "TT6415": 0, "TT6416": 0}

        self.PT_dic = {"PT1325": 0, "PT2121": 0, "PT2316": 0, "PT2330": 0, "PT2335": 0,
                       "PT3308": 0, "PT3309": 0, "PT3311": 0, "PT3314": 0, "PT3320": 0,
                       "PT3332": 0, "PT3333": 0, "PT4306": 0, "PT4315": 0, "PT4319": 0,
                       "PT4322": 0, "PT4325": 0, "PT6302": 0}

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
        self.TT_BO_setting = [0.] * self.nTT_BO
        self.nTT_BO_Attribute = [0.] * self.nTT_BO
        self.PT_setting = [0.] * self.nPT
        self.nPT_Attribute = [0.] * self.nPT

        self.valve_address = {"PV1344": 12288, "PV4307": 12289, "PV4308": 12290, "PV4317": 12291, "PV4318": 12292, "PV4321": 12293,
                        "PV4324": 12294, "PV5305": 12295, "PV5306": 12296,
                        "PV5307": 12297, "PV5309": 12298, "SV3307": 12299, "SV3310": 12300, "SV3322": 12301,
                        "SV3325": 12302, "SV3326": 12303, "SV3329": 12304,
                        "SV4327": 12305, "SV4328": 12306, "SV4329": 12307, "SV4331": 12308, "SV4332": 12309,
                        "SV4337": 12310, "HFSV3312":12311, "HFSV3323": 12312, "HFSV3331": 12313}
        self.nValve = len(self.valve_address)
        self.Valve = {}
        self.Valve_OUT = {"PV1344": 0, "PV4307": 0, "PV4308": 0, "PV4317": 0, "PV4318": 0, "PV4321": 0,
                          "PV4324": 0, "PV5305": 0, "PV5306": 0,
                          "PV5307": 0, "PV5309": 0, "SV3307": 0, "SV3310": 0, "SV3322": 0,
                          "SV3325": 0, "SV3326": 0, "SV3329": 0,
                          "SV4327": 0, "SV4328": 0, "SV4329": 0, "SV4331": 0, "SV4332": 0,
                          "SV4337": 0, "HFSV3312":0, "HFSV3323": 0, "HFSV3331": 0}
        self.Valve_MAN = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                          "PV4324": False, "PV5305": True, "PV5306": True,
                          "PV5307": True, "PV5309": True, "SV3307": True, "SV3310": True, "SV3322": True,
                          "SV3325": True, "SV3326": True, "SV3329": True,
                          "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                          "SV4337": False, "HFSV3312": True, "HFSV3323": True, "HFSV3331": True}
        self.Valve_INTLKD = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                          "PV4324": False, "PV5305": False, "PV5306": False,
                          "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
                          "SV3325": False, "SV3326": False, "SV3329": False,
                          "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                          "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False}
        self.Valve_ERR = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                          "PV4324": False, "PV5305": False, "PV5306": False,
                          "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
                          "SV3325": False, "SV3326": False, "SV3329": False,
                          "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                          "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False}
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
            Raw_RTDs_FP={}
            for key in self.TT_FP_address:
                Raw_RTDs_FP[key] = self.Client.read_holding_registers(self.TT_FP_address[key], count=2, unit=0x01)
                self.TT_FP_dic[key] = round(
                    struct.unpack("<f", struct.pack("<HH", Raw_RTDs_FP[key].getRegister(1), Raw_RTDs_FP[key].getRegister(0)))[0], 3)
                # print(key,self.TT_FP_address[key], "RTD",self.TT_FP_dic[key])
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

        if self.Connected_BO:
            Raw_BO_TT_BO = {}
            for key in self.TT_BO_address:
                Raw_BO_TT_BO[key] = self.Client_BO.read_holding_registers(self.TT_BO_address[key], count=2, unit=0x01)
                self.TT_BO_dic[key] = round(
                    struct.unpack(">f", struct.pack(">HH", Raw_BO_TT_BO[key].getRegister(1), Raw_BO_TT_BO[key].getRegister(0)))[0], 3)
                print(key, "little endian", hex(Raw_BO_TT_BO[key].getRegister(1)),"big endian",hex(Raw_BO_TT_BO[key].getRegister(0)))
                print(key, "'s' value is", self.TT_BO_dic[key])

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

            Raw_BO_PT = {}
            for key in self.PT_address:
                Raw_BO_PT[key] = self.Client_BO.read_holding_registers(self.PT_address[key], count=2, unit=0x01)
                self.PT_dic[key] = round(
                    struct.unpack("<f", struct.pack(">HH", Raw_BO_PT[key].getRegister(0 + 1),
                                                    Raw_BO_PT[key].getRegister(0)))[0], 3)

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
        # print("valve value is", output_BO)
        return output_BO

    def WriteOpen(self,address=12296):
        output_BO = self.ReadValve(address)
        input_BO= struct.unpack("H",output_BO)[0] | 0x0002
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write open result=", Raw)

    def WriteClose(self,address=12296):
        output_BO = self.ReadValve(address)
        input_BO = struct.unpack("H",output_BO)[0] | 0x0004
        Raw = self.Client_BO.write_register(address, value=input_BO, unit=0x01)
        print("write close result=", Raw)

    def Reset(self,address):
        Raw = self.Client_BO.write_register(address, value=0x0010, unit=0x01)
        print("write reset result=", Raw)

    # mask is a number to read a particular digit. for example, if you want to read 3rd digit, the mask is 0100(binary)
    def ReadCoil(self, mask,address=12296):
        output_BO = self.ReadValve(address)
        masked_output= struct.unpack("H",output_BO)[0] & mask
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
        self.base_period=1
        self.para_a=0
        self.rate_a=60
        self.para_b=0
        self.rate_b=120
        print("begin updating Database")

    @QtCore.Slot()
    def run(self):
        self.Running = True
        while self.Running:
            self.dt = datetime_in_s()
            print("Database Updating", self.dt)

            if self.PLC.NewData_Database:
                if self.para_a>= self.rate_a:
                    for key in self.PLC.TT_FP_dic:
                        self.db.insert_data_into_datastorage(key, self.dt, self.PLC.TT_FP_dic[key])
                    for key in self.PLC.TT_BO_dic:
                        self.db.insert_data_into_datastorage(key, self.dt, self.PLC.TT_BO_dic[key])
                    # print("write RTDS")
                    self.para_a=0
                if self.para_b >= self.rate_b:
                    for key in self.PLC.PT_dic:
                        self.db.insert_data_into_datastorage(key, self.dt, self.PLC.PT_dic[key])
                    # print("write pressure transducer")
                    self.para_b=0

                # print("a",self.para_a,"b",self.para_b )

                print("Wrting PLC data to database...")
                self.para_a += 1
                self.para_b += 1
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
        self.period=2

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
        self.period=2
        print("connect to the PLC server")
        self.data_dic={"data":{"TT":{"FP":{"TT2420": 0, "TT2422": 0, "TT2424": 0, "TT2425": 0, "TT2442": 0,
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
                                           "TT6412": 0, "TT6413": 0, "TT6414": 0},
                                      "BO":{"TT2101": 0, "TT2111": 0, "TT2113": 0, "TT2118": 0, "TT2119": 0, "TT4330": 0,
                                           "TT6203": 0, "TT6207": 0, "TT6211": 0, "TT6213": 0, "TT6222": 0,
                                           "TT6407": 0, "TT6408": 0, "TT6409": 0, "TT6415": 0, "TT6416": 0}},
                               "PT":{"PT1325": 0, "PT2121": 0, "PT2316": 0, "PT2330": 0, "PT2335": 0,
                                     "PT3308": 0, "PT3309": 0, "PT3311": 0, "PT3314": 0, "PT3320": 0,
                                     "PT3332": 0, "PT3333": 0, "PT4306": 0, "PT4315": 0, "PT4319": 0,
                                     "PT4322": 0, "PT4325": 0, "PT6302": 0},
                               "Valve":{"OUT":{"PV1344": 0, "PV4307": 0, "PV4308": 0, "PV4317": 0, "PV4318": 0, "PV4321": 0,
                                               "PV4324": 0, "PV5305": 0, "PV5306": 0,
                                               "PV5307": 0, "PV5309": 0, "SV3307": 0, "SV3310": 0, "SV3322": 0,
                                               "SV3325": 0, "SV3326": 0, "SV3329": 0,
                                               "SV4327": 0, "SV4328": 0, "SV4329": 0, "SV4331": 0, "SV4332": 0,
                                               "SV4337": 0, "HFSV3312": 0, "HFSV3323": 0, "HFSV3331": 0},
                                        "INTLKD":{"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                                                  "PV4324": False, "PV5305": False, "PV5306": False,
                                                  "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
                                                  "SV3325": False, "SV3326": False, "SV3329": False,
                                                  "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                                                  "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False},
                                        "MAN":{"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                                               "PV4324": False, "PV5305": True, "PV5306": True,
                                               "PV5307": True, "PV5309": True, "SV3307": True, "SV3310": True, "SV3322": True,
                                               "SV3325": True, "SV3326": True, "SV3329": True,
                                               "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                                               "SV4337": False, "HFSV3312": True, "HFSV3323": True, "HFSV3331": True},
                                        "ERR":{"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                                               "PV4324": False, "PV5305": False, "PV5306": False,
                                               "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
                                               "SV3325": False, "SV3326": False, "SV3329": False,
                                               "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                                               "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False}}},
                       "Alarm":{"TT":{"FP":{"TT2420": False, "TT2422": False, "TT2424": False, "TT2425": False, "TT2442": False,
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
                                            "TT6412": False, "TT6413": False, "TT6414": False},
                                      "BO":{"TT2101": False, "TT2111": False, "TT2113": False, "TT2118": False, "TT2119": False,
                                      "TT4330": False,
                                      "TT6203": False, "TT6207": False, "TT6211": False, "TT6213": False, "TT6222": False,
                                      "TT6407": False, "TT6408": False, "TT6409": False, "TT6415": False, "TT6416": False}},
                                "PT":{"PT1325": False, "PT2121": False, "PT2316": False, "PT2330": False, "PT2335": False,
                                      "PT3308": False, "PT3309": False, "PT3311": False, "PT3314": False, "PT3320": False,
                                      "PT3332": False, "PT3333": False, "PT4306": False, "PT4315": False, "PT4319": False,
                                      "PT4322": False, "PT4325": False, "PT6302": False}},
                       "MainAlarm":False}
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
            self.data_dic["data"]["TT"]["FP"][key]=self.PLC.TT_FP_dic[key]
        for key in self.PLC.TT_BO_dic:
            self.data_dic["data"]["TT"]["BO"][key]=self.PLC.TT_BO_dic[key]
        for key in self.PLC.PT_dic:
            self.data_dic["data"]["PT"][key]=self.PLC.PT_dic[key]
        for key in self.PLC.Valve_OUT:
            self.data_dic["data"]["Valve"]["OUT"][key]=self.PLC.Valve_OUT[key]
        for key in self.PLC.TT_FP_Alarm:
            self.data_dic["Alarm"]["TT"]["FP"][key] = self.PLC.TT_FP_Alarm[key]
        for key in self.PLC.TT_BO_Alarm:
            self.data_dic["Alarm"]["TT"]["BO"][key] = self.PLC.TT_BO_Alarm[key]
        for key in self.PLC.PT_dic:
            self.data_dic["Alarm"]["PT"][key] = self.PLC.PT_Alarm[key]

        self.data_dic["MainAlarm"]=self.PLC.MainAlarm
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
                else:
                    pass



        # if message == b'this is a command':
        #     self.PLC.WriteOpen()
        #     self.PLC.ReadValve()
        #     print("I will set valve")
        # elif message == b'no command':
        #     self.PLC.WriteClose()
        #     self.PLC.ReadValve()
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

