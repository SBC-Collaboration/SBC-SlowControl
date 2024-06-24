"""
Class TPLC is used to read/write via modbus to the temperature PLC

To read the variable, just call the ReadAll() method
To write to a variable, call the proper setXXX() method

By: Mathieu Laurin														

v1.0 Initial code 25/11/19 ML
v1.1 Initialize values, flag when values are updated more modbus variables 04/03/20 ML
"""

import struct, time

from pymodbus.client.sync import ModbusTcpClient


class TPLC:
    def __init__(self):
        super().__init__()
        
        # IP = "192.168.32.112"
        IP = "localhost"
        PORT = 5020
        
        self.Client = ModbusTcpClient(IP, port = PORT)
        self.Connected = self.Client.connect()
        print("TPLC connected: " + str(self.Connected))

        self.nRTD = 54
        self.RTD =  [0.] * self.nRTD 
        self.PT80 = 0.
        self.FlowValve = 0.
        self.BottomChillerSetpoint = 0.
        self.BottomChillerTemp = 0.
        self.BottomChillerState = 0
        self.BottomChillerPowerReset = 0
        self.TopChillerSetpoint = 0.
        self.TopChillerTemp = 0.
        self.TopChillerState = 0
        self.CameraChillerSetpoint = 0.
        self.CameraChillerTemp = 0.
        self.CameraChillerState = 0
        self.WaterChillerSetpoint = 0.
        self.WaterChillerTemp = 0.
        self.WaterChillerPressure = 0.
        self.WaterChillerState = 0
        self.InnerPower = 0.
        self.OuterClosePower = 0.
        self.OuterFarPower = 0.
        self.FreonPower = 0.
        self.ColdRegionSetpoint = 0.
        self.HotRegionSetpoint = 0.
        self.HotRegionP = 0.
        self.HotRegionI = 0.
        self.HotRegionD = 0.
        self.ColdRegionP = 0.
        self.ColdRegionI = 0.
        self.ColdRegionD = 0.
        self.HotRegionPIDState = 0
        self.ClodRegionPIDState = 0
        self.Camera0Temp = 0.
        self.Camera0Humidity = 0.
        self.Camera0AirTemp = 0.
        self.Camera1Temp = 0.
        self.Camera1Humidity = 0.
        self.Camera1AirTemp = 0.
        self.Camera2Temp = 0.
        self.Camera2Humidity = 0.
        self.Camera2AirTemp = 0.
        self.Camera3Temp = 0.
        self.Camera3Humidity = 0.
        self.Camera3AirTemp = 0.
        self.WaterFlow = 0.
        self.WaterTemp = 0.
        self.WaterConductivityBefore = 0.
        self.WaterConductivityAfter = 0.
        self.WaterPressure = 0.
        self.WaterLevel = 0.
        self.WaterPrimingPower = 0
        self.WaterPrimingStatus = 0 
        self.BeetleStatus = 0           
        self.LiveCounter = 0
        self.NewData = False

    def __del__(self):
        self.Client.close()
        
    def ReadAll(self):
        if self.Connected:
            # Reading all the RTDs
            Raw = self.Client.read_holding_registers(0x00, count = self.nRTD * 2, unit = 0x01)
                      
            for i in range(0, self.nRTD, 1):
                self.RTD[i] =  round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister((2 * i) + 1), Raw.getRegister(2 * i)))[0], 3)

            # PT80 (Cold Vacuum Conduit Pressure)
            Raw = self.Client.read_holding_registers(0xA0, count = 2, unit = 0x01)
            self.PT80 = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 7)
            
            # Flow valve
#            Raw = self.Client.read_holding_registers(0x, count = 2, unit = 0x01)
#            self.FlowValve = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 0)

            # Bottom chiller
            Raw = self.Client.read_holding_registers(0xA8, count = 4, unit = 0x01)
            self.BottomChillerSetpoint = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            self.BottomChillerTemp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            Raw = self.Client.read_coils(0x10, count = 1, unit = 0x01)
            self.BottomChillerState = Raw.bits[0]
#            self.BottomChillerPowerReset = Raw.bits[0]

            # Top chiller
            Raw = self.Client.read_holding_registers(0xB0, count = 4, unit = 0x01)
            self.TopChillerSetpoint = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            self.TopChillerTemp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            Raw = self.Client.read_coils(0x13, count = 1, unit = 0x01)
            self.TopChillerState = Raw.bits[0]

            # Camera chiller
            Raw = self.Client.read_holding_registers(0xBA, count = 4, unit = 0x01)
            self.CameraChillerSetpoint = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            self.CameraChillerTemp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            Raw = self.Client.read_coils(0x15, count = 1, unit = 0x01)
            self.CameraChillerState = Raw.bits[0]

            # Water chiller
            Raw = self.Client.read_holding_registers(0xC4, count = 4, unit = 0x01)
            self.WaterChillerSetpoint = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            self.WaterChillerTemp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
#            self.WaterChillerPressure = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            Raw = self.Client.read_coils(0x17, count = 1, unit = 0x01)
            self.WaterChillerState = Raw.bits[0]

            # Heaters
            Raw = self.Client.read_holding_registers(0xC8, count = 8, unit = 0x01)
            self.InnerPower = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            self.OuterClosePower = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 1)
            self.OuterFarPower = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(5), Raw.getRegister(4)))[0], 1)
            self.FreonPower = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(7), Raw.getRegister(6)))[0], 1)

            # Hot/cold region
            Raw = self.Client.read_holding_registers(0xD0, count = 4, unit = 0x01)
            self.ColdRegionSetpoint = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
            self.HotRegionSetpoint = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 1)
#            self.HotRegionP = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
#            self.HotRegionI = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
#            self.HotRegionD = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
#            self.ColdRegionP = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
#            self.ColdRegionI = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
#            self.ColdRegionD = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(3), Raw.getRegister(2)))[0], 2)
            Raw = self.Client.read_coils(0x19, count = 1, unit = 0x01)
            self.HotRegionPIDState = Raw.bits[0]
#            self.ClodRegionPIDState = Raw.bits[0]

            # Cameras
#            Raw = self.Client.read_holding_registers(0x, count = 24, unit = 0x01)
#            self.Camera0Temp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
#            self.Camera0Humidity = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
#            self.Camera0AirTemp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
#            self.Camera1Temp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
#            self.Camera1Humidity = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
#            self.Camera1AirTemp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
#            self.Camera2Temp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
#            self.Camera2Humidity = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
#            self.Camera2AirTemp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
#            self.Camera3Temp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
#            self.Camera3Humidity = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 1)
#            self.Camera3AirTemp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)

            # Water system
#            Raw = self.Client.read_holding_registers(0x, count = 12, unit = 0x01)
#            self.WaterFlow = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2) 
#            self.WaterTemp = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2) 
#            self.WaterConductivityBefore = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2) 
#            self.WaterConductivityAfter = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2) 
#            self.WaterPressure = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
#            self.WaterLevel = round(struct.unpack("<f", struct.pack("<HH", Raw.getRegister(1), Raw.getRegister(0)))[0], 2)
#            Raw = self.Client.read_coils(0x, count = 1, unit = 0x01)
#            self.WaterPrimingPower = Raw.bits[0]
#            self.WaterPrimingStatus = Raw.bits[1] 
#            self.BeetleStatus = Raw.bits[2]             

            # PLC
            Raw = self.Client.read_holding_registers(0x3E9, count = 1, unit = 0x01)
            self.LiveCounter = Raw.getRegister(0)

            self.NewData = True

            return 0
        else:
            return 1
            
    def SaveSetting(self):
        self.WriteBool(0x0, 0, 1)
            
        return 0 # There is no way to know if it worked... Cross your fingers!
        
    def SetFlowValve(self, Value):
            
        return self.WriteFloat(0x0, Value)
        
    def SetBottomChillerSetpoint(self, Value):
            
        return self.WriteFloat(0x0, Value)
        
    def SetBottomChillerState(self, State):
        if State == "Off":
            Value = 0
        elif State == "On":
            Value = 1
            
        return self.WriteBool(0x0, 0, Value)
        
    def SetBottomChillerPowerReset(self, State):
        if State == "Off":
            Value = 0
        elif State == "On":
            Value = 1
            
        return self.WriteBool(0x0, 0, Value)
        
    def SetTopChillerSetpoint(self, Value):
            
        return self.WriteFloat(0x0, Value)
        
    def SetTopChillerState(self, State):
        if State == "Off":
            Value = 0
        elif State == "On":
            Value = 1
            
        return self.WriteBool(0x0, 0, Value)

    def SetCameraChillerSetpoint(self, Value):
            
        return self.WriteFloat(0x0, Value)
        
    def SetCameraChillerState(self, State):
        if State == "Off":
            Value = 0
        elif State == "On":
            Value = 1
            
        return self.WriteBool(0x0, 0, Value)        
        
    def SetWaterChillerSetpoint(self, Value):
            
        return self.WriteFloat(0x0, Value)
        
    def SetWaterChillerState(self, State):
        if State == "Off":
            Value = 0
        elif State == "On":
            Value = 1
            
        return self.WriteBool(0x0, 0, Value)           
        
    def SetInnerPower(self, Value):
            
        return self.WriteFloat(0x0, Value)        
  
    def SetOuterClosePower(self, Value):
            
        return self.WriteFloat(0x0, Value)  

    def SetOuterFarPower(self, Value):
            
        return self.WriteFloat(0x0, Value)  

    def SetFreonPower(self, Value):
            
        return self.WriteFloat(0x0, Value)  
    
    def SetInnerPowerState(self, State):
        if State == "Off":
            self.WriteBool(0x0, 0, 1) 
        elif State == "On":
            self.WriteBool(0x0, 0, 1) 
            
        return 0 # There is no way to know if it worked... Cross your fingers!
    
    def SetOuterClosePowerState(self, State):
        if State == "Off":
            self.WriteBool(0x0, 0, 1) 
        elif State == "On":
            self.WriteBool(0x0, 0, 1) 
            
        return 0 # There is no way to know if it worked... Cross your fingers!
    
    def SetOuterFarPowerState(self, State):
        if State == "Off":
            self.WriteBool(0x0, 0, 1) 
        elif State == "On":
            self.WriteBool(0x0, 0, 1) 
            
        return 0 # There is no way to know if it worked... Cross your fingers!
        
    def SetFreonPowerState(self, State):
        if State == "Off":
            self.WriteBool(0x0, 0, 1) 
        elif State == "On":
            self.WriteBool(0x0, 0, 1) 
            
        return 0 # There is no way to know if it worked... Cross your fingers!
        
    def SetColdRegionSetpoint(self, Value):
            
        return self.WriteFloat(0x0, Value)  

    def SetHotRegionSetpoint(self, Value):
            
        return self.WriteFloat(0x0, Value)          
        
    def SetHotRegionP(self, Value):
            
        return self.WriteFloat(0x0, Value) 
    
    def SetHotRegionI(self, Value):
            
        return self.WriteFloat(0x0, Value) 
    
    def SetHotRegionD(self, Value):
            
        return self.WriteFloat(0x0, Value) 
        
    def SetColdRegionP(self, Value):
            
        return self.WriteFloat(0x0, Value) 
        
    def SetColdRegionI(self, Value):
            
        return self.WriteFloat(0x0, Value) 
        
    def SetColdRegionD(self, Value):
            
        return self.WriteFloat(0x0, Value) 
        
    def SetHotRegionPIDMode(self, Mode):
        if Mode == "Manual":
            Value = 0
        elif Mode == "Auto":
            Value = 1
            
        return self.WriteBool(0x0, 0, Value)
        
    def SetColdRegionPIDMode(self, Mode):
        if Mode == "Manual":
            Value = 0
        elif Mode == "Auto":
            Value = 1
            
        return self.WriteBool(0x0, 0, Value)
        
    def SetWaterPrimingPower(self, State):
        if State == "Off":
            Value = 0
        elif State == "On":
            Value = 1
            
        return self.WriteBool(0x0, 0, Value)      
            
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
            Raw = self.Client.read_coils(Address, count = Bit, unit = 0x01)
            Raw.bits[Bit] = Value
            Dummy = self.Client.write_coil(Address, Raw, unit = 0x01)
        
            time.sleep(1)
        
            Raw = self.Client.read_coils(Address, count = Bit, unit = 0x01)
            rValue = Raw.bits[Bit]
        
            if Value == rValue:
                return 0
            else:
                return 2
        else:
            return 1