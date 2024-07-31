from utils.threadpool import Worker
from .network import Ip_Parser, Network_Manager
from .modbus import Modbus_Server, Modbus_Address_Abs
from configure import NetworkCnf

from time import sleep

class MACH_STATE:
    STOP    = 0
    RUN     = 1
    ERROR   = 2

class PROD_STATE:
    TEST    = 0
    RUN     = 1
    STOP    = 2

class HMI_ADDRESS(Modbus_Address_Abs):
    REG_WIFI_CONNECTED      = 148
    REG_IP_START            = 139
    REG_SUBNET              = 143
    REG_GATEWAY_START       = 144
    
    REG_PLC                 = [99, 104, 109]
    PLC_CONNECTED           = 0
    PLC_PRODUCTION          = 1
    PLC_MACH_STATE          = 2
    PLC_PROD_STATE          = 3

    def __init__(self) -> None:
        super().__init__(0, 150)

class Hmi_Handler:
    class Plc_State:
        def __init__(self, id: int) -> None:
            self.id = id
            self.connected = False
            self.production = 0
            self.mach_state = MACH_STATE.STOP
            self.prod_state = PROD_STATE.STOP
        
        def updateModbus(self, mb: Modbus_Server):
            mb.write(HMI_ADDRESS.REG_PLC[self.id],
                [int(self.connected), self.production, self.mach_state, self.prod_state])
    
    def __init__(self) -> None:
        self.__ip = [0] * 4
        self.__subnet = 24
        self.__gateway = [0] * 4
        self.__connected = False

        self.__plc = [Hmi_Handler.Plc_State(0), Hmi_Handler.Plc_State(1), Hmi_Handler.Plc_State(2)]

        self.__mb = Modbus_Server(HMI_ADDRESS)
        self.__mb.start(type="RTU", port="/dev/ttyAMA4", baud=9600, data=8, stop=1, parity="N")
        self.__mb.start(type="TCP", host="0.0.0.0", port=5002)

        # self.__updateWifi()
    
    @Worker.employ
    def __updateWifi(self):
        """
        Read wifi status real time
        """
        while True:
            try:
                # print(self.__mb.read(HMI_ADDRESS.REG_IP_START, 10), " --------------- ")
                # UPDATE REGISTER
                self.__mb.write(HMI_ADDRESS.REG_WIFI_CONNECTED, [int(self.__connected)])
                self.__mb.write(HMI_ADDRESS.REG_IP_START, self.__ip[::-1])
                self.__mb.write(HMI_ADDRESS.REG_SUBNET, [self.__subnet])
                self.__mb.write(HMI_ADDRESS.REG_GATEWAY_START, self.__gateway[::-1])
                for plc in self.__plc:
                    plc.updateModbus(self.__mb)
                ip = Network_Manager.getConnectionIp(NetworkCnf.CONNECTION)
                if ip:
                    self.__ip = list(map(int, ip.split(".")))
                    self.__connected = True
                else:
                    self.__connected = False
                    self.__ip = [255,255,255,255]
                
                gateway = Network_Manager.getGateway(NetworkCnf.CONNECTION)
                if gateway != None:
                    self.__gateway = list(map(int, gateway.split(".")))
                else:
                    self.__gateway = [255,255,255,255]
                
                sleep(5)
            except Exception as e:
                print(str(e))

    def updatePlc(self, id: int, connected: bool, production: int, mach_state: int, prod_state: int):
        self.__plc[id-1].connected = connected
        self.__plc[id-1].production = production
        self.__plc[id-1].mach_state = mach_state
        self.__plc[id-1].prod_state = prod_state