# SBC-SlowControl
SBC Slow Control server and related code
1.TCP conection:
if you force the PLC.py code to stop i.e. ctrl+Z, the tcp connection won't be closed and the port is still be occupied. Please source the clear_tcp.sh before you rerun the PLC.py
2. Some protocol between PLC and GUI:

2.a from PLC(background code) the data form is

{$"data"$:{pid:value},$"Alarm"$:value, "MainAlarm":value}
$$ means it is a constant value.
example: {"data":{"PT9998":0, "PT9999":0},"Alarm":{"PT9998": False, "PT9999": False}, "MainAlarm":False}

Reason why I choose this form: it is easier to direcly catch all alarm status
an alternative way to manage the information flow is transpose the matrix and the outest index is pid(PTXXXX).
If this introduce some trouble in the future, we may change it. But for now, it at least works...0


2.b from GUI to PLC
{pid:{$"server"$:modbus server name,$"address"$: address in modbus, $"operation"$:write true or else, $"value"$: True, false or float}}

we may need to create another file to describe the two info flows in more detailed.