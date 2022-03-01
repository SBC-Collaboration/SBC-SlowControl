
import struct, time, zmq, sys, pickle
import numpy as np
from PySide2 import QtWidgets, QtCore, QtGui
from Database_SBC import *
from email.mime.text import MIMEText
from email.header import Header
from smtplib import SMTP_SSL
import requests
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

        self.FP_address = 12288

        self.BO_address = 14290
        # self.BO_address = 12988



    def __del__(self):
        self.Client.close()
        self.Client_BO.close()

    def ReadAll(self):
        # print(self.TT_BO_HighLimit["TT2119"])
        # print(self.TT_BO_Alarm["TT2119"])
        # if self.Connected:
        #     # Reading all the RTDs
        #
        #
        #     Raw_RTDs_FP = self.Client.read_holding_registers(self.FP_address, count=2, unit=0x01)
        #     self.TT_FP_dic = round(
        #         struct.unpack("<f", struct.pack("<HH", Raw_RTDs_FP.getRegister(1), Raw_RTDs_FP.getRegister(0)))[0], 3)
        #
        #
        #     print("FP",self.FP_address ,self.TT_FP_dic)


            #########################################################################
        #12288 +4000/2 + 6 HILIM

        if self.Connected_BO:
            Raw_RTDs_BO = self.Client_BO.read_holding_registers(self.BO_address, count=2, unit=0x01)
            # print(Raw_RTDs_BO)
            self.TT_BO_dic = round(
                struct.unpack(">f", struct.pack(">HH", Raw_RTDs_BO.getRegister(1), Raw_RTDs_BO.getRegister(0)))[0], 3)
            print("BO",self.BO_address, self.TT_BO_dic)

            self.LOOPPID_SET_MODE(address=self.BO_address, mode=1)



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
        print(struct.unpack("H", output_BO)[0])
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



#
#
# class Update(QtCore.QObject):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         App.aboutToQuit.connect(self.StopUpdater)
#         self.StartUpdater()
#
#     def StartUpdater(self):
#         self.PLC = PLC()
#
#         # Read PLC value on another thread
#         self.PLCUpdateThread = QtCore.QThread()
#         self.UpPLC = UpdatePLC(self.PLC)
#         self.UpPLC.moveToThread(self.PLCUpdateThread)
#         self.PLCUpdateThread.started.connect(self.UpPLC.run)
#         self.PLCUpdateThread.start()
#
#
#
#         # Stop all updater threads
#     @QtCore.Slot()
#     def StopUpdater(self):
#         self.UpPLC.stop()
#         self.PLCUpdateThread.quit()
#         self.PLCUpdateThread.wait()
#
#         self.UpDatabase.stop()
#         self.DataUpdateThread.quit()
#         self.DataUpdateThread.wait()
#
#         self.UpServer.stop()
#         self.ServerUpdateThread.quit()
#         self.ServerUpdateThread.wait()
#
# class message_manager():
#     def __init__(self):
#         # info about tencent mail settings
#         self.host_server = "smtp.qq.com"
#         self.sender_qq = "390282332"
#         self.pwd = "bngozrzmzsbocafa"
#         self.sender_mail = "390282332@qq.com"
#         # self.receiver1_mail = "cdahl@northwestern.edu"
#         self.receiver1_mail = "runzezhang@foxmail.com"
#         self.mail_title = "Alarm from SBC"
#
#         #info about slack settings
#         self.slack_webhook_url = 'https://hooks.slack.com/services/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'
#         self.slack_channel = None
#         self.alert_map = {
#             "emoji": {
#                 "up": ":white_check_mark:",
#                 "down": ":fire:"
#             },
#             "text": {
#                 "up": "RESOLVED",
#                 "down": "FIRING"
#             },
#             "message": {
#                 "up": "Everything is good!",
#                 "down": "Stuff is burning!"
#             },
#             "color": {
#                 "up": "#32a852",
#                 "down": "#ad1721"
#             }
#         }
#
#     def tencent_alarm(self, message):
#         try:
#             # The body content of the mail
#             mail_content = " Alarm from SBC slowcontrol: " + message
#             # sslLogin
#             smtp = SMTP_SSL(self.host_server)
#             # set_debuglevel() is used for debugging. The parameter value is 1 to enable debug mode and 0 to disable debug mode.
#             smtp.set_debuglevel(1)
#             smtp.ehlo(self.host_server)
#             smtp.login(self.sender_qq, self.pwd)
#             # Define mail content
#             msg = MIMEText(mail_content, "plain", "utf-8")
#             msg["Subject"] = Header(self.mail_title, "utf-8")
#             msg["From"] = self.sender_mail
#             msg["To"] = self.receiver1_mail
#             # send email
#             smtp.sendmail(self.sender_mail, self.receiver1_mail, msg.as_string())
#             smtp.quit()
#             print("mail sent successfully")
#         except Exception as e:
#             print("mail failed to send")
#             print(e)
#
#     def slack_alarm(self, message, status=None):
#         data = {
#             "text": "AlertManager",
#             "username": "Notifications",
#             "channel": self.slack_channel,
#             "attachments": [{"text": message}]
#         #     "attachments": [g
#         #         {
#         #             "text": "{emoji} [*{state}*] Status Checker\n {message}".format(
#         #                 emoji=self.alert_map["emoji"][status],
#         #                 state=self.alert_map["text"][status],
#         #                 message=self.alert_map["message"][status]
#         #             ),
#         #             "color": self.alert_map["color"][status],
#         #             "attachment_type": "default",
#         #             "actions": [
#         #                 {
#         #                     "name": "Logs",f
#         #                     "text": "Logs",
#         #                     "type": "button",
#         #                     "style": "primary",
#         #                     "url": "https://grafana-logs.dashboard.local"
#         #                 },
#         #                 {
#         #                     "name": "Metrics",
#         #                     "text": "Metrics",
#         #                     "type": "button",
#         #                     "style": "primary",
#         #                     "url": "https://grafana-metrics.dashboard.local"
#         #                 }
#         #             ]
#         #         }]
#         }
#         r = requests.post(self.slack_webhook_url, json=data)
#         return r.status_code
#



if __name__ == "__main__":
    # msg_mana=message_manager()
    # msg_mana.tencent_alarm("this is a test message")

    App = QtWidgets.QApplication(sys.argv)
    # Update=Update()


    PLC=PLC()
    PLC.ReadAll()


