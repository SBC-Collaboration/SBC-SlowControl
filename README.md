# SBC-SlowControl
SBC Slow Control server and related code
1.TCP conection:
if you force the PLC.py code to stop i.e. ctrl+Z, the tcp connection won't be closed and the port is still be occupied. Please source the clear_tcp.sh before you rerun the PLC.py
2. Some protocol between PLC and GUI:

2.a from PLC(background code) the data form is

{$"data"$:{"type":{pid:value},...},$"Alarm"$:{type: value,...}, "MainAlarm":value}
$$ means it is a constant value.
example:
{"data":{"TT":{"TT2101": 0, "TT2111": 0, "TT2113": 0, "TT2118": 0, "TT2119": 0, "TT4330": 0,
                                     "TT6203": 0, "TT6207": 0, "TT6211": 0, "TT6213": 0, "TT6222": 0,
                                     "TT6407": 0, "TT6408": 0, "TT6409": 0, "TT6415": 0, "TT6416": 0}
                               "PT":{"PT1325": 0, "PT2121": 0, "PT2316": 0, "PT2330": 0, "PT2335": 0,
                                     "PT3308": 0, "PT3309": 0, "PT3311": 0, "PT3314": 0, "PT3320": 0,
                                     "PT3332": 0, "PT3333": 0, "PT4306": 0, "PT4315": 0, " PT4319": 0,
                                     "PT4322": 0, "PT4325": 0, "PT6302": 0}},
                       "Alarm":{"TT":{"TT2101": False, "TT2111": False, "TT2113": False, "TT2118": False, "TT2119": False,
                                      "TT4330": False,
                                      "TT6203": False, "TT6207": False, "TT6211": False, "TT6213": False, "TT6222": False,
                                      "TT6407": False, "TT6408": False, "TT6409": False, "TT6415": False, "TT6416": False}
                                "PT":{"PT1325": False, "PT2121": False, "PT2316": False, "PT2330": False, "PT2335": False,
                                      "PT3308": False, "PT3309": False, "PT3311": False, "PT3314": False, "PT3320": False,
                                      "PT3332": False, "PT3333": False, "PT4306": False, "PT4315": False, " PT4319": False,
                                      "PT4322": False, "PT4325": False, "PT6302": False}},
                       "MainAlarm":False}

Reason why I choose this form: it is easier to direcly catch all alarm status
an alternative way to manage the information flow is transpose the matrix and the outest index is pid(PTXXXX).
If this introduce some trouble in the future, we may change it. But for now, it at least works...0


2.b from GUI to PLC
{pid:{$"server"$:modbus server name,$"address"$: address in modbus,$"type"$:pid's instrument type $"operation"$:write true or else, $"value"$: True, false or float}}

we may need to create another file to describe the two info flows in more detailed.