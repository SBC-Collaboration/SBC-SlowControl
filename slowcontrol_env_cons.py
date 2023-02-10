BASE_ADDRESS= 12288
# real address  = base+ comparative/2
# Initialization of Address, Value Matrix
TT_FP_ADDRESS = {"TT2420": 31000, "TT2422": 31002, "TT2424": 31004, "TT2425": 31006, "TT2442": 36000,
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

TT_BO_ADDRESS = {"TT2101": 12988, "TT2111": 12990, "TT2113": 12992, "TT2118": 12994, "TT2119": 12996,
                              "TT4330": 12998, "TT6203": 13000, "TT6207": 13002, "TT6211": 13004, "TT6213": 13006,
                              "TT6222": 13008, "TT6407": 13010, "TT6408": 13012, "TT6409": 13014, "TT6415": 13016,
                 "TT6416": 13018}

PT_ADDRESS = {"PT1325": 12794, "PT2121": 12796, "PT2316": 12798, "PT2330": 12800, "PT2335": 12802,
              "PT3308": 12804, "PT3309": 12806, "PT3311": 12808, "PT3314": 12810, "PT3320": 12812,
              "PT3332": 12814, "PT3333": 12816, "PT4306": 12818, "PT4315": 12820, "PT4319": 12822,
              "PT4322": 12824, "PT4325": 12826, "PT6302": 12828, 'PT1101': 12830, 'PT5304': 12834}

LEFT_REAL_ADDRESS = {'BFM4313': 12788, 'LT3335': 12790, 'MFC1316_IN': 12792, "CYL3334_FCALC": 12832, "SERVO3321_IN_REAL": 12830, "TS1_MASS": 16288, "TS2_MASS": 16290, "TS3_MASS": 16292,  "TS_ADDREM_N2MASSTX": 16818}

TT_FP_DIC = {"TT2420": 0, "TT2422": 0, "TT2424": 0, "TT2425": 0, "TT2442": 0,
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

TT_BO_DIC = {"TT2101": 0, "TT2111": 0, "TT2113": 0, "TT2118": 0, "TT2119": 0, "TT4330": 0,
             "TT6203": 0, "TT6207": 0, "TT6211": 0, "TT6213": 0, "TT6222": 0,
             "TT6407": 0, "TT6408": 0, "TT6409": 0, "TT6415": 0, "TT6416": 0}

PT_DIC = {"PT1325": 0, "PT2121": 0, "PT2316": 0, "PT2330": 0, "PT2335": 0,
          "PT3308": 0, "PT3309": 0, "PT3311": 0, "PT3314": 0, "PT3320": 0,
          "PT3332": 0, "PT3333": 0, "PT4306": 0, "PT4315": 0, "PT4319": 0,
          "PT4322": 0, "PT4325": 0, "PT6302": 0, "PT1101": 0, "PT5304": 0}

LEFT_REAL_DIC = {'BFM4313': 0, 'LT3335': 0, 'MFC1316_IN': 0, "CYL3334_FCALC": 0, "SERVO3321_IN_REAL": 0, "TS1_MASS": 0, "TS2_MASS": 0, "TS3_MASS": 0, "TS_ADDREM_N2MASSTX": 0}

TT_FP_LOWLIMIT = {"TT2420": 0, "TT2422": 0, "TT2424": 0, "TT2425": 0, "TT2442": 0,
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

TT_FP_HIGHLIMIT = {"TT2420": 30, "TT2422": 30, "TT2424": 30, "TT2425": 30, "TT2442": 30,
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

TT_BO_LOWLIMIT = {"TT2101": 0, "TT2111": 0, "TT2113": 0, "TT2118": 0, "TT2119": 0, "TT4330": 0,
                  "TT6203": 0, "TT6207": 0, "TT6211": 0, "TT6213": 0, "TT6222": 0,
                  "TT6407": 0, "TT6408": 0, "TT6409": 0, "TT6415": 0, "TT6416": 0}

TT_BO_HIGHLIMIT = {"TT2101": 30, "TT2111": 30, "TT2113": 30, "TT2118": 30, "TT2119": 30, "TT4330": 30,
                   "TT6203": 30, "TT6207": 30, "TT6211": 30, "TT6213": 30, "TT6222": 30,
                   "TT6407": 30, "TT6408": 30, "TT6409": 30, "TT6415": 30, "TT6416": 30}

PT_LOWLIMIT = {"PT1325": 0, "PT2121": 0, "PT2316": 0, "PT2330": 0, "PT2335": 0,
               "PT3308": 0, "PT3309": 0, "PT3311": 0, "PT3314": 0, "PT3320": 0,
               "PT3332": 0, "PT3333": 0, "PT4306": 0, "PT4315": 0, "PT4319": 0,
               "PT4322": 0, "PT4325": 0, "PT6302": 0,  "PT1101": 0, "PT5304": 0}
PT_HIGHLIMIT = {"PT1325": 300, "PT2121": 300, "PT2316": 300, "PT2330": 300, "PT2335": 300,
                "PT3308": 300, "PT3309": 300, "PT3311": 300, "PT3314": 300, "PT3320": 300,
                "PT3332": 300, "PT3333": 300, "PT4306": 300, "PT4315": 300, "PT4319": 300,
                "PT4322": 300, "PT4325": 300, "PT6302": 300,  "PT1101": 300, "PT5304": 300}

LEFT_REAL_HIGHLIMIT = {'BFM4313': 0, 'LT3335': 0, 'MFC1316_IN': 0, "CYL3334_FCALC": 0, "SERVO3321_IN_REAL": 0, "TS1_MASS": 0, "TS2_MASS": 0, "TS3_MASS": 0,"TS_ADDREM_N2MASSTX": 0}
LEFT_REAL_LOWLIMIT = {'BFM4313': 0, 'LT3335': 0, 'MFC1316_IN': 0, "CYL3334_FCALC": 0, "SERVO3321_IN_REAL": 0, "TS1_MASS": 0, "TS2_MASS": 0, "TS3_MASS": 0 , "TS_ADDREM_N2MASSTX": 0}

TT_FP_ACTIVATED = {"TT2420": False, "TT2422": False, "TT2424": False, "TT2425": False, "TT2442": False,
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

TT_BO_ACTIVATED = {"TT2101": False, "TT2111": False, "TT2113": False, "TT2118": False, "TT2119": False, "TT4330": False,
                   "TT6203": False, "TT6207": False, "TT6211": False, "TT6213": False, "TT6222": False,
                   "TT6407": False, "TT6408": False, "TT6409": False, "TT6415": False, "TT6416": False}

PT_ACTIVATED = {"PT1325": False, "PT2121": False, "PT2316": False, "PT2330": False, "PT2335": False,
                "PT3308": False, "PT3309": False, "PT3311": False, "PT3314": False, "PT3320": False,
                "PT3332": False, "PT3333": False, "PT4306": False, "PT4315": False, "PT4319": False,
                "PT4322": False, "PT4325": False, "PT6302": False,  "PT1101": False, "PT5304": False}
LEFT_REAL_ACTIVATED = {'BFM4313': False, 'LT3335': False, 'MFC1316_IN': False, "CYL3334_FCALC": False, "SERVO3321_IN_REAL": False, "TS1_MASS": False, "TS2_MASS": False, "TS3_MASS": False, "TS_ADDREM_N2MASSTX": False}

TT_FP_ALARM = {"TT2420": False, "TT2422": False, "TT2424": False, "TT2425": False, "TT2442": False,
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

TT_BO_ALARM = {"TT2101": False, "TT2111": False, "TT2113": False, "TT2118": False, "TT2119": False, "TT4330": False,
               "TT6203": False, "TT6207": False, "TT6211": False, "TT6213": False, "TT6222": False,
               "TT6407": False, "TT6408": False, "TT6409": False, "TT6415": False, "TT6416": False}

PT_ALARM = {"PT1325": False, "PT2121": False, "PT2316": False, "PT2330": False, "PT2335": False,
            "PT3308": False, "PT3309": False, "PT3311": False, "PT3314": False, "PT3320": False,
            "PT3332": False, "PT3333": False, "PT4306": False, "PT4315": False, "PT4319": False,
            "PT4322": False, "PT4325": False, "PT6302": False,  "PT1101": False, "PT5304": False}
LEFT_REAL_ALARM = {'BFM4313': False, 'LT3335': False, 'MFC1316_IN': False, "CYL3334_FCALC": False, "SERVO3321_IN_REAL": False, "TS1_MASS": False, "TS2_MASS": False, "TS3_MASS": False, "TS_ADDREM_N2MASSTX": False}
MAINALARM = False
MAN_SET = False
NTT_BO = len(TT_BO_ADDRESS)
NTT_FP = len(TT_FP_ADDRESS)
NPT = len(PT_ADDRESS)
NREAL = len(LEFT_REAL_ADDRESS)

TT_BO_SETTING = [0.] * NTT_BO
NTT_BO_ATTRIBUTE = [0.] * NTT_BO
PT_SETTING = [0.] * NPT
NPT_ATTRIBUTE = [0.] * NPT

SWITCH_ADDRESS = {"PUMP3305": 12688}
NSWITCH = len(SWITCH_ADDRESS)
SWITCH = {}
SWITCH_OUT = {"PUMP3305": 0}
SWITCH_MAN = {"PUMP3305": False}
SWITCH_INTLKD = {"PUMP3305": False}
SWITCH_ERR = {"PUMP3305": False}

DIN_ADDRESS = {"LS3338": (12778, 0), "LS3339": (12778, 1), "ES3347": (12778, 2), "PUMP3305_CON": (12778, 3),
               "PUMP3305_OL": (12778, 4),"PS2352":(12778, 5),"PS1361":(12778, 6),"PS8302":(12778, 7)}
NDIN = len(DIN_ADDRESS)
DIN = {}
DIN_DIC = {"LS3338": False, "LS3339": False, "ES3347": False, "PUMP3305_CON": False, "PUMP3305_OL": False,"PS2352":False,"PS1361":False,"PS8302":False}

DIN_LOWLIMIT = {"LS3338": False, "LS3339": False, "ES3347": False, "PUMP3305_CON": False, "PUMP3305_OL": False,"PS2352":False,"PS1361":False,"PS8302":False}

DIN_HIGHLIMIT = {"LS3338": True, "LS3339": True, "ES3347": True, "PUMP3305_CON": True, "PUMP3305_OL": True,"PS2352":True,"PS1361":True,"PS8302":True}

DIN_ACTIVATED = {"LS3338": False, "LS3339": False, "ES3347": False, "PUMP3305_CON": False, "PUMP3305_OL": False,"PS2352":False,"PS1361":False,"PS8302":False}

DIN_ALARM = {"LS3338": False, "LS3339": False, "ES3347": False, "PUMP3305_CON": False, "PUMP3305_OL": False,"PS2352":False,"PS1361":False,"PS8302":False}

VALVE_ADDRESS = {"PV1344": 12288, "PV4307": 12289, "PV4308": 12290, "PV4317": 12291, "PV4318": 12292, "PV4321": 12293,
                 "PV4324": 12294, "PV5305": 12295, "PV5306": 12296,
                 "PV5307": 12297, "PV5309": 12298, "SV3307": 12299, "SV3310": 12300, "SV3322": 12301,
                 "SV3325": 12302, "SV3329": 12304,
                 "SV4327": 12305, "SV4328": 12306, "SV4329": 12307, "SV4331": 12308, "SV4332": 12309,
                 "SV4337": 12310, "HFSV3312": 12311, "HFSV3323": 12312, "HFSV3331": 12313}
NVALVE = len(VALVE_ADDRESS)
VALVE = {}
VALVE_OUT = {"PV1344": 0, "PV4307": 0, "PV4308": 0, "PV4317": 0, "PV4318": 0, "PV4321": 0,
             "PV4324": 0, "PV5305": 0, "PV5306": 0,
             "PV5307": 0, "PV5309": 0, "SV3307": 0, "SV3310": 0, "SV3322": 0,
             "SV3325": 0, "SV3329": 0,
             "SV4327": 0, "SV4328": 0, "SV4329": 0, "SV4331": 0, "SV4332": 0,
             "SV4337": 0, "HFSV3312": 0, "HFSV3323": 0, "HFSV3331": 0}
VALVE_MAN = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
             "PV4324": False, "PV5305": True, "PV5306": True,
             "PV5307": True, "PV5309": True, "SV3307": True, "SV3310": True, "SV3322": True,
             "SV3325": True, "SV3329": True,
             "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
             "SV4337": False, "HFSV3312": True, "HFSV3323": True, "HFSV3331": True}
VALVE_INTLKD = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
                "PV4324": False, "PV5305": False, "PV5306": False,
                "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
                "SV3325": False, "SV3329": False,
                "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
                "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False}
VALVE_ERR = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
             "PV4324": False, "PV5305": False, "PV5306": False,
             "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
             "SV3325": False, "SV3329": False,
             "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
             "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False}
VALVE_COMMAND_CACHE = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
             "PV4324": False, "PV5305": False, "PV5306": False,
             "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
             "SV3325": False, "SV3329": False,
             "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
             "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False}
VALVE_BUSY = {"PV1344": False, "PV4307": False, "PV4308": False, "PV4317": False, "PV4318": False, "PV4321": False,
             "PV4324": False, "PV5305": False, "PV5306": False,
             "PV5307": False, "PV5309": False, "SV3307": False, "SV3310": False, "SV3322": False,
             "SV3325": False, "SV3329": False,
             "SV4327": False, "SV4328": False, "SV4329": False, "SV4331": False, "SV4332": False,
             "SV4337": False, "HFSV3312": False, "HFSV3323": False, "HFSV3331": False}
LOOPPID_ADR_BASE = {'SERVO3321': 14288, 'HTR6225': 14306, 'HTR2123': 14324, 'HTR2124': 14342, 'HTR2125': 14360,
                    'HTR1202': 14378, 'HTR2203': 14396, 'HTR6202': 14414, 'HTR6206': 14432, 'HTR6210': 14450,
                    'HTR6223': 14468, 'HTR6224': 14486, 'HTR6219': 14504, 'HTR6221': 14522, 'HTR6214': 14540}

LOOPPID_MODE0 = {'SERVO3321': True, 'HTR6225': True, 'HTR2123': True, 'HTR2124': True, 'HTR2125': True,
                 'HTR1202': True, 'HTR2203': True, 'HTR6202': True, 'HTR6206': True, 'HTR6210': True,
                 'HTR6223': True, 'HTR6224': True, 'HTR6219': True, 'HTR6221': True, 'HTR6214': True}

LOOPPID_MODE1 = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False, 'HTR2125': False,
                 'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                 'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

LOOPPID_MODE2 = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False, 'HTR2125': False,
                 'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                 'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

LOOPPID_MODE3 = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False, 'HTR2125': False,
                 'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                 'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

LOOPPID_INTLKD = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                  'HTR2125': False,
                  'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                  'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

LOOPPID_MAN = {'SERVO3321': True, 'HTR6225': True, 'HTR2123': True, 'HTR2124': True,
               'HTR2125': True,
               'HTR1202': True, 'HTR2203': True, 'HTR6202': True, 'HTR6206': True, 'HTR6210': True,
               'HTR6223': True, 'HTR6224': True, 'HTR6219': True, 'HTR6221': True, 'HTR6214': True}

LOOPPID_ERR = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
               'HTR2125': False,
               'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
               'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

LOOPPID_SATHI = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                 'HTR2125': False,
                 'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                 'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

LOOPPID_SATLO = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                 'HTR2125': False,
                 'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                 'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

LOOPPID_EN = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
              'HTR2125': False,
              'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
              'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

LOOPPID_ALARM = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
              'HTR2125': False,
              'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
              'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}

LOOPPID_OUT = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
               'HTR2125': 0,
               'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
               'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

LOOPPID_IN = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
              'HTR2125': 0,
              'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
              'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

LOOPPID_HI_LIM = {'SERVO3321': 100, 'HTR6225': 100, 'HTR2123': 100, 'HTR2124': 100,
                  'HTR2125': 100,
                  'HTR1202': 100, 'HTR2203': 100, 'HTR6202': 100, 'HTR6206': 100, 'HTR6210': 100,
                  'HTR6223': 100, 'HTR6224': 100, 'HTR6219': 100, 'HTR6221': 100, 'HTR6214': 100}

LOOPPID_LO_LIM = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                  'HTR2125': 0,
                  'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                  'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

LOOPPID_SET0 = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                'HTR2125': 0,
                'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

LOOPPID_SET1 = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                'HTR2125': 0,
                'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

LOOPPID_SET2 = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                'HTR2125': 0,
                'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

LOOPPID_SET3 = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                'HTR2125': 0,
                'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}

LOOPPID_ACTIVATED = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
                  'HTR2125': False,
                  'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
                  'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}


LOOPPID_COMMAND_CACHE = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
              'HTR2125': False,
              'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
              'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}


LOOPPID_BUSY = {'SERVO3321': False, 'HTR6225': False, 'HTR2123': False, 'HTR2124': False,
              'HTR2125': False,
              'HTR1202': False, 'HTR2203': False, 'HTR6202': False, 'HTR6206': False, 'HTR6210': False,
              'HTR6223': False, 'HTR6224': False, 'HTR6219': False, 'HTR6221': False, 'HTR6214': False}



LOOPPID_ALARM_HI_LIM = {'SERVO3321': 100, 'HTR6225': 100, 'HTR2123': 100, 'HTR2124': 100,
                  'HTR2125': 100,
                  'HTR1202': 100, 'HTR2203': 100, 'HTR6202': 100, 'HTR6206': 100, 'HTR6210': 100,
                  'HTR6223': 100, 'HTR6224': 100, 'HTR6219': 100, 'HTR6221': 100, 'HTR6214': 100}

LOOPPID_ALARM_LO_LIM = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                  'HTR2125': 0,
                  'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                  'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}


LOOP2PT_ADR_BASE = {'PUMP3305':14688}

LOOP2PT_MODE0 = {'PUMP3305': True}

LOOP2PT_MODE1 = {'PUMP3305': False}

LOOP2PT_MODE2 = {'PUMP3305': False}

LOOP2PT_MODE3 = {'PUMP3305': False}

LOOP2PT_INTLKD = {'PUMP3305': False}

LOOP2PT_MAN = {'PUMP3305': True}

LOOP2PT_ERR = {'PUMP3305': False}

LOOP2PT_OUT = {'PUMP3305': 0}

LOOP2PT_SET1 = {'PUMP3305': 0}

LOOP2PT_SET2 = {'PUMP3305': 0}

LOOP2PT_SET3 = {'PUMP3305': 0}

LOOP2PT_COMMAND_CACHE = {'PUMP3305': False}

LOOP2PT_BUSY = {'PUMP3305': False}

PROCEDURE_ADDRESS = {'TS_ADDREM': 15288, 'TS_EMPTY': 15290, 'TS_EMPTYALL': 15292, 'PU_PRIME': 15294, 'WRITE_SLOWDAQ': 15296, 'PRESSURE_CYCLE':15298}
PROCEDURE_RUNNING = {'TS_ADDREM': False, 'TS_EMPTY': False, 'TS_EMPTYALL': False, 'PU_PRIME': False, 'WRITE_SLOWDAQ': False, 'PRESSURE_CYCLE':False}
PROCEDURE_INTLKD = {'TS_ADDREM': False, 'TS_EMPTY': False, 'TS_EMPTYALL': False, 'PU_PRIME': False, 'WRITE_SLOWDAQ': False, 'PRESSURE_CYCLE':False}
PROCEDURE_EXIT = {'TS_ADDREM': 0, 'TS_EMPTY': 0, 'TS_EMPTYALL': 0, 'PU_PRIME': 0, 'WRITE_SLOWDAQ': 0, 'PRESSURE_CYCLE':0}

FLAG_ADDRESS={'MAN_TS':13288,'MAN_HYD':13289,"PCYCLE_AUTOCYCLE":13290}
FLAG_DIC = {'MAN_TS':False,'MAN_HYD':False,"PCYCLE_AUTOCYCLE":False}
FLAG_INTLKD={'MAN_TS':False,'MAN_HYD':False,"PCYCLE_AUTOCYCLE":False}
FLAG_BUSY={'MAN_TS':False,'MAN_HYD':False,"PCYCLE_AUTOCYCLE":False}

INTLK_D_ADDRESS={'TS1_INTLK': 13828, 'ES3347_INTLK': 13829, 'PUMP3305_OL_INTLK': 13830, 'TS2_INTLK': 13832, 'TS3_INTLK': 13836, 'PU_PRIME_INTLK': 13840}
INTLK_D_DIC={'TS1_INTLK': True, 'ES3347_INTLK': True, 'PUMP3305_OL_INTLK': True, 'TS2_INTLK': True, 'TS3_INTLK': True, 'PU_PRIME_INTLK': True}
INTLK_D_EN={'TS1_INTLK': True, 'ES3347_INTLK': True, 'PUMP3305_OL_INTLK': True, 'TS2_INTLK': True, 'TS3_INTLK': True, 'PU_PRIME_INTLK': True}
INTLK_D_COND={'TS1_INTLK': True, 'ES3347_INTLK': True, 'PUMP3305_OL_INTLK': True, 'TS2_INTLK': True, 'TS3_INTLK': True, 'PU_PRIME_INTLK': True}

INTLK_D_BUSY={'TS1_INTLK': True, 'ES3347_INTLK': True, 'PUMP3305_OL_INTLK': True, 'TS2_INTLK': True, 'TS3_INTLK': True, 'PU_PRIME_INTLK': True}

INTLK_A_ADDRESS={'TT2118_HI_INTLK': 13788, 'TT2118_LO_INTLK': 13792, 'PT4306_LO_INTLK': 13796, 'PT4306_HI_INTLK': 13800, 'PT4322_HI_INTLK': 13804, 'PT4322_HIHI_INTLK': 13808, 'PT4319_HI_INTLK': 13812, 'PT4319_HIHI_INTLK': 13816, 'PT4325_HI_INTLK': 13820, 'PT4325_HIHI_INTLK': 13824,
'TT6203_HI_INTLK': 13844, 'TT6207_HI_INTLK': 13848, 'TT6211_HI_INTLK': 13852, 'TT6213_HI_INTLK': 13856, 'TT6222_HI_INTLK': 13860,
'TT6407_HI_INTLK': 13864, 'TT6408_HI_INTLK': 13868, 'TT6409_HI_INTLK': 13872, 'TT6203_HIHI_INTLK': 13876, 'TT6207_HIHI_INTLK': 13880,
'TT6211_HIHI_INTLK': 13884, 'TT6213_HIHI_INTLK': 13888, 'TT6222_HIHI_INTLK': 13892, 'TT6407_HIHI_INTLK': 13896, 'TT6408_HIHI_INTLK': 13900,
'TT6409_HIHI_INTLK': 13904}
INTLK_A_DIC={'TT2118_HI_INTLK': True, 'TT2118_LO_INTLK': True, 'PT4306_LO_INTLK': True, 'PT4306_HI_INTLK': True, 'PT4322_HI_INTLK': True, 'PT4322_HIHI_INTLK': True, 'PT4319_HI_INTLK': True, 'PT4319_HIHI_INTLK': True, 'PT4325_HI_INTLK': True, 'PT4325_HIHI_INTLK': True,
             'TT6203_HI_INTLK': True, 'TT6207_HI_INTLK': True, 'TT6211_HI_INTLK': True, 'TT6213_HI_INTLK': True,
             'TT6222_HI_INTLK': True,
             'TT6407_HI_INTLK': True, 'TT6408_HI_INTLK': True, 'TT6409_HI_INTLK': True, 'TT6203_HIHI_INTLK': True,
             'TT6207_HIHI_INTLK': True,
             'TT6211_HIHI_INTLK': True, 'TT6213_HIHI_INTLK': True, 'TT6222_HIHI_INTLK': True,
             'TT6407_HIHI_INTLK': True, 'TT6408_HIHI_INTLK': True,
             'TT6409_HIHI_INTLK': True}
INTLK_A_EN={'TT2118_HI_INTLK': True, 'TT2118_LO_INTLK': True, 'PT4306_LO_INTLK': True, 'PT4306_HI_INTLK': True, 'PT4322_HI_INTLK': True, 'PT4322_HIHI_INTLK': True, 'PT4319_HI_INTLK': True, 'PT4319_HIHI_INTLK': True, 'PT4325_HI_INTLK': True, 'PT4325_HIHI_INTLK': True,
            'TT6203_HI_INTLK': True, 'TT6207_HI_INTLK': True, 'TT6211_HI_INTLK': True, 'TT6213_HI_INTLK': True,
            'TT6222_HI_INTLK': True,
            'TT6407_HI_INTLK': True, 'TT6408_HI_INTLK': True, 'TT6409_HI_INTLK': True, 'TT6203_HIHI_INTLK': True,
            'TT6207_HIHI_INTLK': True,
            'TT6211_HIHI_INTLK': True, 'TT6213_HIHI_INTLK': True, 'TT6222_HIHI_INTLK': True,
            'TT6407_HIHI_INTLK': True, 'TT6408_HIHI_INTLK': True,
            'TT6409_HIHI_INTLK': True
            }
INTLK_A_COND={'TT2118_HI_INTLK': True, 'TT2118_LO_INTLK': True, 'PT4306_LO_INTLK': True, 'PT4306_HI_INTLK': True, 'PT4322_HI_INTLK': True, 'PT4322_HIHI_INTLK': True, 'PT4319_HI_INTLK': True, 'PT4319_HIHI_INTLK': True, 'PT4325_HI_INTLK': True, 'PT4325_HIHI_INTLK': True,
              'TT6203_HI_INTLK': True, 'TT6207_HI_INTLK': True, 'TT6211_HI_INTLK': True, 'TT6213_HI_INTLK': True,
              'TT6222_HI_INTLK': True,
              'TT6407_HI_INTLK': True, 'TT6408_HI_INTLK': True, 'TT6409_HI_INTLK': True, 'TT6203_HIHI_INTLK': True,
              'TT6207_HIHI_INTLK': True,
              'TT6211_HIHI_INTLK': True, 'TT6213_HIHI_INTLK': True, 'TT6222_HIHI_INTLK': True,
              'TT6407_HIHI_INTLK': True, 'TT6408_HIHI_INTLK': True,
              'TT6409_HIHI_INTLK': True
              }
INTLK_A_SET={'TT2118_HI_INTLK': 0, 'TT2118_LO_INTLK': 0, 'PT4306_LO_INTLK': 0, 'PT4306_HI_INTLK': 0, 'PT4322_HI_INTLK': 0, 'PT4322_HIHI_INTLK': 0, 'PT4319_HI_INTLK': 0, 'PT4319_HIHI_INTLK': 0, 'PT4325_HI_INTLK': 0, 'PT4325_HIHI_INTLK': 0,
             'TT6203_HI_INTLK': 0, 'TT6207_HI_INTLK': 0, 'TT6211_HI_INTLK': 0, 'TT6213_HI_INTLK': 0,
             'TT6222_HI_INTLK': 0,
             'TT6407_HI_INTLK': 0, 'TT6408_HI_INTLK': 0, 'TT6409_HI_INTLK': 0, 'TT6203_HIHI_INTLK': 0,
             'TT6207_HIHI_INTLK': 0,
             'TT6211_HIHI_INTLK': 0, 'TT6213_HIHI_INTLK': 0, 'TT6222_HIHI_INTLK': 0,
             'TT6407_HIHI_INTLK': 0, 'TT6408_HIHI_INTLK': 0,
             'TT6409_HIHI_INTLK': 0 }

INTLK_A_BUSY={'TT2118_HI_INTLK': 0, 'TT2118_LO_INTLK': 0, 'PT4306_LO_INTLK': 0, 'PT4306_HI_INTLK': 0, 'PT4322_HI_INTLK': 0, 'PT4322_HIHI_INTLK': 0, 'PT4319_HI_INTLK': 0, 'PT4319_HIHI_INTLK': 0, 'PT4325_HI_INTLK': 0, 'PT4325_HIHI_INTLK': 0,
             'TT6203_HI_INTLK': 0, 'TT6207_HI_INTLK': 0, 'TT6211_HI_INTLK': 0, 'TT6213_HI_INTLK': 0,
             'TT6222_HI_INTLK': 0,
             'TT6407_HI_INTLK': 0, 'TT6408_HI_INTLK': 0, 'TT6409_HI_INTLK': 0, 'TT6203_HIHI_INTLK': 0,
             'TT6207_HIHI_INTLK': 0,
             'TT6211_HIHI_INTLK': 0, 'TT6213_HIHI_INTLK': 0, 'TT6222_HIHI_INTLK': 0,
             'TT6407_HIHI_INTLK': 0, 'TT6408_HIHI_INTLK': 0,
             'TT6409_HIHI_INTLK': 0 }

FF_ADDRESS={'TS_ADDREM_FF': 14788, 'TS_EMPTY_FF': 14789, 'TS_EMPTYALL_FF': 14790, 'SLOWDAQ_FF': 14791, 'PCYCLE_ABORT_FF': 14792, 'PCYCLE_FASTCOMP_FF': 14793, 'PCYCLE_SLOWCOMP_FF': 14794, 'PCYCLE_CYLEQ_FF': 14795, 'PCYCLE_CYLBLEED_FF': 14796, 'PCYCLE_ACCHARGE_FF': 14797}
FF_DIC={'TS_ADDREM_FF': 0, 'TS_EMPTY_FF': 0, 'TS_EMPTYALL_FF': 0, 'SLOWDAQ_FF': 0, 'PCYCLE_ABORT_FF': 0, 'PCYCLE_FASTCOMP_FF': 0, 'PCYCLE_SLOWCOMP_FF': 0, 'PCYCLE_CYLEQ_FF': 0, 'PCYCLE_CYLBLEED_FF': 0, 'PCYCLE_ACCHARGE_FF': 0}

PARAM_F_ADDRESS ={'TS_ADDREM_MASS': 16790,'PCYCLE_PSET': 16794,'PCYCLE_MAXEQPDIFF': 16802,'PCYCLE_MAXACCDPDT': 16806,'PCYCLE_MAXBLEEDDPDT': 16810, 'PCYCLE_SLOWCOMP_SET': 16812}
PARAM_F_DIC ={'TS_ADDREM_MASS': 0,'PCYCLE_PSET': 0,'PCYCLE_MAXEQPDIFF': 0,'PCYCLE_MAXACCDPDT': 0,'PCYCLE_MAXBLEEDDPDT':0, 'PCYCLE_SLOWCOMP_SET': 0}

PARAM_T_ADDRESS = {'PCYCLE_MAXEXPTIME': 16798, 'PCYCLE_MAXEQTIME': 16800,'PCYCLE_MAXACCTIME': 16804,'PCYCLE_MAXBLEEDTIME': 16808,"TS_ADDREM_MAXTIME":16814, "TS_ADDREM_FLOWET":16816}
PARAM_T_DIC = {'PCYCLE_MAXEXPTIME': 0, 'PCYCLE_MAXEQTIME': 0,'PCYCLE_MAXACCTIME': 0,'PCYCLE_MAXBLEEDTIME': 0,"TS_ADDREM_MAXTIME":0, "TS_ADDREM_FLOWET":0}

PARAM_I_ADDRESS = {'TS_SEL': 16788}
PARAM_I_DIC = {'TS_SEL': 0}

PARAM_B_ADDRESS = {'TS1_EMPTY':(16792,0),'TS2_EMPTY':(16792,1), 'TS3_EMPTY':(16792,2)}
PARAM_B_DIC = {'TS1_EMPTY':0,'TS2_EMPTY':0, 'TS3_EMPTY':0}

TIME_ADDRESS = {'PCYCLE_EXPTIME': 16796}
TIME_DIC = {'PCYCLE_EXPTIME': 0}
# This is for checkbox initialization when BKG restarts
# first digit means whether server(BKG) send check_ini request to client(GUI)
# second digit means whether client(GUI) send check box info to server(BKG)
# true value table
#[0,0]
#[0,1]
#[1,1]
#[1,0]
INI_CHECK= True

TT_FP_PARA = {"TT2420": 0, "TT2422": 0, "TT2424": 0, "TT2425": 0, "TT2442": 0,
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


TT_FP_RATE = {"TT2420": 30, "TT2422": 30, "TT2424": 30, "TT2425": 30, "TT2442": 30,
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

TT_BO_PARA = {"TT2101": 0, "TT2111": 0, "TT2113": 0, "TT2118": 0, "TT2119": 0, "TT4330": 0,
                  "TT6203": 0, "TT6207": 0, "TT6211": 0, "TT6213": 0, "TT6222": 0,
                  "TT6407": 0, "TT6408": 0, "TT6409": 0, "TT6415": 0, "TT6416": 0}


TT_BO_RATE =  {"TT2101": 30, "TT2111": 30, "TT2113": 30, "TT2118": 30, "TT2119": 30, "TT4330": 30,
                   "TT6203": 30, "TT6207": 30, "TT6211": 30, "TT6213": 30, "TT6222": 30,
                   "TT6407": 30, "TT6408": 30, "TT6409": 30, "TT6415": 30, "TT6416": 30}
PT_PARA = {"PT1325": 0, "PT2121": 0, "PT2316": 0, "PT2330": 0, "PT2335": 0,
               "PT3308": 0, "PT3309": 0, "PT3311": 0, "PT3314": 0, "PT3320": 0,
               "PT3332": 0, "PT3333": 0, "PT4306": 0, "PT4315": 0, "PT4319": 0,
               "PT4322": 0, "PT4325": 0, "PT6302": 0,  "PT1101": 0, "PT5304": 0}

PT_RATE = {"PT1325": 30, "PT2121": 30, "PT2316": 30, "PT2330": 30, "PT2335": 30,
                "PT3308": 30, "PT3309": 30, "PT3311": 30, "PT3314": 30, "PT3320": 30,
                "PT3332": 30, "PT3333": 30, "PT4306": 30, "PT4315": 30, "PT4319": 30,
                "PT4322": 30, "PT4325": 30, "PT6302": 30,  "PT1101": 30, "PT5304": 30}

LEFT_REAL_PARA = {'BFM4313': 0, 'LT3335': 0, 'MFC1316_IN': 0, "CYL3334_FCALC": 0, "SERVO3321_IN_REAL": 0, "TS1_MASS": 0, "TS2_MASS": 0, "TS3_MASS": 0, "TS_ADDREM_N2MASSTX": 0}

LEFT_REAL_RATE = {'BFM4313': 30, 'LT3335': 30, 'MFC1316_IN': 30, "CYL3334_FCALC": 30, "SERVO3321_IN_REAL": 30, "TS1_MASS": 30, "TS2_MASS": 30, "TS3_MASS": 30, "TS_ADDREM_N2MASSTX": 30}

DIN_PARA = {"LS3338": False, "LS3339": False, "ES3347": False, "PUMP3305_CON": False, "PUMP3305_OL": False,"PS2352":False,"PS1361":False,"PS8302":False}

DIN_RATE = {"LS3338": 30, "LS3339": 30, "ES3347": 30, "PUMP3305_CON": 30, "PUMP3305_OL": 30,"PS2352":30,"PS1361":30,"PS8302":30}

LOOPPID_PARA = {'SERVO3321': 0, 'HTR6225': 0, 'HTR2123': 0, 'HTR2124': 0,
                  'HTR2125': 0,
                  'HTR1202': 0, 'HTR2203': 0, 'HTR6202': 0, 'HTR6206': 0, 'HTR6210': 0,
                  'HTR6223': 0, 'HTR6224': 0, 'HTR6219': 0, 'HTR6221': 0, 'HTR6214': 0}
LOOPPID_RATE = {'SERVO3321': 30, 'HTR6225': 30, 'HTR2123': 30, 'HTR2124': 30,
                  'HTR2125': 30,
                  'HTR1202': 30, 'HTR2203': 30, 'HTR6202': 30, 'HTR6206': 30, 'HTR6210': 30,
                  'HTR6223': 30, 'HTR6224': 30, 'HTR6219': 30, 'HTR6221': 30, 'HTR6214': 30}

DIC_PACK = {"data": {"TT": {"FP": {"value": TT_FP_DIC, "high": TT_FP_HIGHLIMIT, "low": TT_FP_LOWLIMIT},
                                         "BO": {"value": TT_BO_DIC, "high": TT_BO_HIGHLIMIT, "low": TT_BO_LOWLIMIT}},
                                  "PT": {"value": PT_DIC, "high": PT_HIGHLIMIT, "low": PT_LOWLIMIT},
                                  "LEFT_REAL": {"value": LEFT_REAL_DIC, "high": LEFT_REAL_HIGHLIMIT, "low": LEFT_REAL_LOWLIMIT},
                                  "Valve": {"OUT": VALVE_OUT,
                                            "INTLKD": VALVE_INTLKD,
                                            "MAN": VALVE_MAN,
                                            "ERR": VALVE_ERR,
                                            "Busy":VALVE_BUSY},
                                  "Switch": {"OUT": SWITCH_OUT,
                                             "INTLKD": SWITCH_INTLKD,
                                             "MAN": SWITCH_MAN,
                                             "ERR": SWITCH_ERR},
                                  "Din": {'value': DIN_DIC,"high": DIN_HIGHLIMIT, "low": DIN_LOWLIMIT},
                                  "LOOPPID": {"MODE0": LOOPPID_MODE0,
                                              "MODE1": LOOPPID_MODE1,
                                              "MODE2": LOOPPID_MODE2,
                                              "MODE3": LOOPPID_MODE3,
                                              "INTLKD": LOOPPID_INTLKD,
                                              "MAN": LOOPPID_MAN,
                                              "ERR": LOOPPID_ERR,
                                              "SATHI": LOOPPID_SATHI,
                                              "SATLO": LOOPPID_SATLO,
                                              "EN": LOOPPID_EN,
                                              "OUT": LOOPPID_OUT,
                                              "IN": LOOPPID_IN,
                                              "HI_LIM": LOOPPID_HI_LIM,
                                              "LO_LIM": LOOPPID_LO_LIM,
                                              "SET0": LOOPPID_SET0,
                                              "SET1": LOOPPID_SET1,
                                              "SET2": LOOPPID_SET2,
                                              "SET3": LOOPPID_SET3,
                                              "Busy":LOOPPID_BUSY,
                                              "Alarm":LOOPPID_ALARM,
                                              "Alarm_HighLimit":LOOPPID_ALARM_HI_LIM,
                                              "Alarm_LowLimit":LOOPPID_ALARM_LO_LIM},
                                  "LOOP2PT": {"MODE0": LOOP2PT_MODE0,
                                              "MODE1": LOOP2PT_MODE1,
                                              "MODE2": LOOP2PT_MODE2,
                                              "MODE3": LOOP2PT_MODE3,
                                              "INTLKD": LOOP2PT_INTLKD,
                                              "MAN": LOOP2PT_MAN,
                                              "ERR": LOOP2PT_ERR,
                                              "OUT": LOOP2PT_OUT,
                                              "SET1": LOOP2PT_SET1,
                                              "SET2": LOOP2PT_SET2,
                                              "SET3": LOOP2PT_SET3,
                                              "Busy":LOOP2PT_BUSY},
                                  "INTLK_D": {"value": INTLK_D_DIC,
                                              "EN": INTLK_D_EN,
                                              "COND": INTLK_D_COND,
                                              "Busy":INTLK_D_BUSY},
                                  "INTLK_A": {"value":INTLK_A_DIC,
                                              "EN":INTLK_A_EN,
                                              "COND":INTLK_A_COND,
                                              "SET":INTLK_A_SET,
                                              "Busy":INTLK_A_BUSY},
                                  "FLAG": {"value":FLAG_DIC,
                                           "INTLKD":FLAG_INTLKD,
                                           "Busy":FLAG_BUSY},
                                  "Procedure": {"Running": PROCEDURE_RUNNING, "INTLKD": PROCEDURE_INTLKD, "EXIT": PROCEDURE_EXIT}},
                         "Alarm": {"TT": {"FP": TT_FP_ALARM,
                                          "BO": TT_BO_ALARM},
                                   "PT": PT_ALARM,
                                   "LEFT_REAL": LEFT_REAL_ALARM,
                                   "Din": DIN_ALARM,
                                   "LOOPPID": LOOPPID_ALARM},
                         "Active": {"TT": {"FP": TT_FP_ACTIVATED,
                                          "BO": TT_BO_ACTIVATED},
                                   "PT": PT_ACTIVATED,
                                   "LEFT_REAL": LEFT_REAL_ACTIVATED,
                                    "Din": DIN_ACTIVATED,
                                    "LOOPPID": LOOPPID_ACTIVATED,
                                    "INI_CHECK": INI_CHECK
                                    },
                         "MainAlarm": MAINALARM
                         }



# if same key conflicts, the later one will replace the previous one
def merge_dic(dic1,*args):
    res = dic1
    for dicts in args:
       res = {**res, **dicts}
    return res
