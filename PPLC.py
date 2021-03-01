"""
Class PPLC is used to read/write via modbus to the pressure PLC

To read the variable, just call the ReadAll() method
To write to a variable, call the proper setXXX() method

By: Mathieu Laurin														

v1.0 Initial code 25/11/19 ML	
v1.1 Initialize values, flag when values are updated more modbus variables 04/03/20 ML
"""

import struct, time

from pymodbus.client.sync import ModbusTcpClient

class PPLC:
    def __init__(self):
        super().__init__()
        
        # IP = "192.168.32.50"
        IP = "localhost"
        PORT = 5020
        
        self.Client = ModbusTcpClient(IP, port = PORT)
        self.Connected = self.Client.connect()
        print("PPLC connected: " + str(self.Connected))

        self.LabAirPressureState = 0
        self.ExpansionValve = 0
        self.FastCompressValveCart = 0
        self.SlowCompressValve = False
        self.FastCompressValve1 = 0
        self.FastCompressValve2 = 0
        self.FastCompressValve3 = 0
        self.PumpState = 0
        self.OilReliefValve = 0
        self.FreonOutValve = 0
        self.FreonInValve = 0      
        self.PT1 = 0.
        self.PT2 = 0.
        self.PT3 = 0.
        self.PT4 = 0.
        self.PT8 = 0.
        self.PT9 = 0.
        self.PT10 = 0.
        self.PT11 = 0.
        self.AirRegulator = 0.
        self.PDiff = 0.
        self.AirRegulatorSetpoint = 0.
        self.PressureSetpoint = 0.
        self.BellowsPosition = 0.
        self.IVPosition = 0.
        self.CurrentState = "Unknown"
        self.FFCamera = 0
        self.FFManual = 0
        self.FFdP1 = 0
        self.FFdP5 = 0
        self.FFdP4 = 0
        self.FFPDiff = 0
        self.FFP1PSet = 0
        self.FFP5PSet = 0
        self.FFP4PSet = 0
        self.FFP3Max = 0
        self.FFP2Min = 0
        self.FFTCPIP = 0
        self.FFdBellows = 0
        self.FFEmergency = 0
        self.LiveCounter = 0
        self.NewData = False
                    
    def __del__(self):
        self.Client.close()
        
    def ReadAll(self):
        if self.Connected:
            # Man valves
            Raw = self.Client.read_holding_registers(0x46E, count = 1, unit = 0x01)
            Bits = [j for j in reversed([bool(int(i)) for i in format(Raw.getRegister(0), '016b')])]
            self.LabAirPressureState = Bits[0]
            self.ExpansionValve = Bits[1]
            self.FastCompressValveCart = Bits[2]
            if Bits[3] == True: # NO valve
                self.SlowCompressValve = False
            else:
                self.SlowCompressValve = True
            self.FastCompressValve1 = Bits[4]
            self.FastCompressValve2 = Bits[5]
            self.FastCompressValve3 = Bits[6]
            self.PumpState = Bits[7]
            self.OilReliefValve = Bits[8]
            self.FreonOutValve = Bits[9]
            self.FreonInValve = Bits[10]  
            self.DetectorPressurized = Bits[0]
            
            # PT
            Raw = self.Client.read_holding_registers(0x400, count = 6, unit = 0x01)
            self.PT1 = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            self.PT2 = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            self.PT3 = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(5), Raw.getRegister(4)))[0], 2)
            Raw = self.Client.read_holding_registers(0x420, count = 10, unit = 0x01)
            self.PT4 = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            self.PT8 = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            self.PT9 = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(5), Raw.getRegister(4)))[0], 2)
            self.PT10 = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(7), Raw.getRegister(6)))[0], 2)
            self.PT11 = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(9), Raw.getRegister(8)))[0], 2)
            Raw = self.Client.read_holding_registers(0x40E, count = 2, unit = 0x01)
            self.AirRegulator = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            Raw = self.Client.read_holding_registers(0x460, count = 2, unit = 0x01)
            self.PDiff = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            
            # Setpoint
            Raw = self.Client.read_holding_registers(0xB6, count = 2, unit = 0x01)
            self.AirRegulatorSetpoint = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            Raw = self.Client.read_holding_registers(0xC0, count = 2, unit = 0x01)
            self.PressureSetpoint = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            
            # Positions
            Raw = self.Client.read_holding_registers(0xF4, count = 2, unit = 0x01)
            self.BellowsPosition = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            Raw = self.Client.read_holding_registers(0xF6, count = 2, unit = 0x01)
            self.IVPosition = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
            
            # Current state
            Raw = self.Client.read_holding_registers(0x454, count = 1, unit = 0x01)
            if Raw.getRegister(0) == 0:
                self.CurrentState = "Idle"
            elif Raw.getRegister(0) == 1:
                self.CurrentState = "Expanding"
            elif Raw.getRegister(0) == 2:
                self.CurrentState = "Expanded"
            elif Raw.getRegister(0) == 3:
                self.CurrentState = "Compressing"
            elif Raw.getRegister(0) == 4:
                self.CurrentState = "Compressed"
            elif Raw.getRegister(0) == 5:
                self.CurrentState = "Manual"
            elif Raw.getRegister(0) == 6:
                self.CurrentState = "Emergency"
            else:
                self.CurrentState = "Unknown"
                
            # First fault
            Raw = self.Client.read_holding_registers(0x455, count = 1, unit = 0x01)
            Bits = [j for j in reversed([bool(int(i)) for i in format(Raw.getRegister(0), '016b')])]
            self.FFCamera = Bits[1]
            self.FFManual = Bits[2]
            self.FFdP1 = Bits[8]
            self.FFdP5 = Bits[9]
            self.FFdP4 = Bits[10]
            self.FFPDiff = Bits[11]
            self.FFP1PSet = Bits[12]
            self.FFP5PSet = Bits[13]
            self.FFP4PSet = Bits[14]
            self.FFP3Max = Bits[15]
            Raw = self.Client.read_holding_registers(0x456, count = 1, unit = 0x01)
            Bits = [j for j in reversed([bool(int(i)) for i in format(Raw.getRegister(0), '016b')])]
            self.FFP2Min = Bits[0]
            self.FFTCPIP = Bits[1]
            self.FFdBellows = Bits[2]
            self.FFEmergency = Bits[3]

            # Detector state
            Raw = self.Client.read_holding_registers(0x457, count = 1, unit = 0x01)
            Bits = [j for j in reversed([bool(int(i)) for i in format(Raw.getRegister(0), '016b')])]
            self.DetectorPressurized = Bits[0]

            # PLC
            Raw = self.Client.read_holding_registers(0x46A, count = 1, unit = 0x01)
            self.LiveCounter = Raw.getRegister(0)

            self.NewData = True

            return 0
        else:
            return 1
        
    def SetFastCompressValve1(self, State):
        if State == "Close":
            Value = 0
        elif State == "Open":
            Value = 1
            
        return self.WriteBool(0xB0, 0, Value)

    def SetFastCompressValve2(self, State):
        if State == "Close":
            Value = 0
        elif State == "Open":
            Value = 1
            
        return self.WriteBool(0xB0, 1, Value)  

    def SetFastCompressValve3(self, State):
        if State == "Close":
            Value = 0
        elif State == "Open":
            Value = 1
            
        return self.WriteBool(0xB0, 2, Value)  

    def SetPumpState(self, State):
        if State == "Off":
            Value = 0
        elif State == "On":
            Value = 1
            
        return self.WriteBool(0xB0, 6, Value)  

    def SetSlowCompressValve(self, State):
        if State == "Close":
            Value = 1
        elif State == "Open":
            Value = 0
            
        return self.WriteBool(0xB0, 7, Value)  

    def SetFastCompressValveCart(self, State):
        if State == "Close":
            Value = 0
        elif State == "Open":
            Value = 1
            
        return self.WriteBool(0xB0, 8, Value)  

    def SetExpansionValve(self, State):
        if State == "Close":
            Value = 0
        elif State == "Open":
            Value = 1
            
        return self.WriteBool(0xB0, 9, Value)  

    def SetOilReliefValve(self, State):
        if State == "Close":
            Value = 0
        elif State == "Open":
            Value = 1
            
        return self.WriteBool(0xB0, 12, Value)  

    def SetFreonInValve(self, State):
        if State == "Close":
            Value = 0
        elif State == "Open":
            Value = 1
            
        return self.WriteBool(0xB0, 13, Value)  

    def SetFreonOutValve(self, State):
        if State == "Close":
            Value = 0
        elif State == "Open":
            Value = 1
            
        return self.WriteBool(0xB0, 14, Value)          
        
    def SetAirRegulatorSetpoint(self, Value):
            
        return self.WriteFloat(0xB6, Value)
        
    def SetPressureSetpoint(self, Value):
            
        return self.WriteFloat(0xC0, Value)
        
    def SaveSetting(self):
        self.WriteBool(0x100, 0, 1) 
        
        return 0 # There is no way to know if it worked... Cross your fingers!
        
    def Compress(self):
        self.WriteBool(0xB8, 0, 1) 
        
        return 0 # To know if it worked, read CurrentState
        
    def GoIdle(self):
        self.WriteBool(0xB8, 1, 1) 
        
        return 0 # To know if it worked, read CurrentState
        
    def Expand(self):
        self.WriteBool(0xB8, 2, 1)
         
        return 0 # To know if it worked, read CurrentState
        
    def GoManual(self):
        self.WriteBool(0xB8, 3, 1)
                    
        return 0 # To know if it worked, read CurrentState
            
    def WriteFloat(self, Address, Value):
        if self.Connected:
            Value = round(Value, 3)
            Dummy = self.Client.write_register(Address, struct.unpack("<HH", struct.pack("<f", Value))[1], unit = 0x01)
            Dummy = self.Client.write_register(Address + 1, struct.unpack("<HH", struct.pack("<f", Value))[0], unit = 0x01)
        
            time.sleep(1)
        
            Raw = self.Client.read_holding_registers(Address, count = 2, unit = 0x01)
            rValue = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 3)
        
            if Value == rValue:
                return 0
            else:
                return 2
        else:
            return 1
                
    def WriteBool(self, Address, Bit, Value):
        if self.Connected:
            Raw = self.Client.read_holding_registers(Address, count = 1, unit = 0x01)

            Mask = 1 << Bit 
            nValue = (Raw.getRegister(0) & ~Mask) | ((Value << Bit) & Mask)

            Dummy = self.Client.write_register(Address, nValue, unit = 0x01)
        
            time.sleep(1)
        
            Raw = self.Client.read_holding_registers(Address, count = 1, unit = 0x01)
            rValue = Raw.getRegister(0)
        
            if nValue == rValue:
                return 0
            else:
                return 2
        else:
            return 1