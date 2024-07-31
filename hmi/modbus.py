from utils.threadpool import Worker

from pymodbus.server.sync import StartTcpServer, StartSerialServer, ModbusSerialServer
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

class Modbus_Address_Abs:
    '''
    Declare this class for modbus server and/or client
        number_coils: number of coils
        number_registers: number of registers
    Holding registers (or Input registers):
        REG_<name> = <address>
    Coils (or Discrete inputs):
        COIL_<name> = <address>
    '''

    def __init__(self, number_coils: int, number_registers: int) -> None:
        self.number_coils = number_coils
        self.number_registers = number_registers

class Modbus_Function:
    READ_COILS  = 1
    READ_INPUTS = 2
    READ_H_REGS = 3
    READ_I_REGS = 4
    WRITE_COIL  = 5
    WRITE_REG   = 6
    WRITE_COILS = 15
    WRITE_REGS  = 16

class CustomModbusSlaveContext(ModbusSlaveContext):
    def __init__(self, setCallback = None, getCallback = None, *_args, **kwargs):
        """
        setCallback: set register callback (slave_id, is coil, address, values)
        getCallback: get reigster callback (slave_id, is coil, address, result)
        """
        super().__init__(*_args, **kwargs)
        self.__setCallback = setCallback
        self.__getCallback = getCallback

    def getValues(self, fc_as_hex: int, address: int, count: int = 1, internal: bool = False, id: int = 0) -> list:
        result = super().getValues(fc_as_hex, address, count)
        if not internal and self.__getCallback != None:
            self.__getCallback(
                id,
                True if fc_as_hex in [Modbus_Function.READ_COILS, Modbus_Function.READ_INPUTS] else False,
                address,
                result
            )
        return result

    def setValues(self, fc_as_hex: int, address: int, values: list, internal: bool = False, id: int = 0):
        super().setValues(fc_as_hex, address, values)
        if not internal and self.__setCallback != None:
            self.__setCallback(
                id,
                True if fc_as_hex in [Modbus_Function.WRITE_COIL, Modbus_Function.WRITE_COILS] else False,
                address,
                values
            )

class Modbus_Server:
    def __init__(self, address_class: Modbus_Address_Abs, id: int = 1, setCallback = None, getCallback = None) -> None:
        """
        address_class: Modbus_Address instance
        setCallback: set register callback (is coil, address, number of regs, values)
        getCallback: get reigster callback (is coil, address, new values)
        """
        self.address = address_class()
        self.__id = id
        
        holding_block = ModbusSequentialDataBlock(0, [0] * (self.address.number_registers + 1))
        coil_block = ModbusSequentialDataBlock(0, [0] * (self.address.number_coils + 1))
        self.__store = {
            self.__id: CustomModbusSlaveContext(
                co=coil_block, di=coil_block, hr=holding_block, ir=holding_block,
                setCallback=setCallback, getCallback=getCallback
            )
        }
        self.__context = ModbusServerContext(slaves=self.__store , single=False)

    @Worker.employ
    def start(self, **kwargs):
        """
        Kwargs:
            type: "RTU"
                port: str
                baud: int
                data: 7 | 8
                stop: 1 | 2
                parity: "N" - None | "E" - Even | "O" - Odd
            type: "TCP"
                host: str
                port: int
        """
        if kwargs["type"] == "RTU":
            StartSerialServer(
                context = self.__context,
                framer=ModbusRtuFramer,
                port = kwargs["port"],
                stopbits = kwargs["stop"],
                bytesize = kwargs["data"],
                parity = kwargs["parity"],
                baudrate = kwargs["baud"],
                timeout = 0.2
            )
        elif kwargs["type"] == "TCP":
            StartTcpServer(
                context = self.__context,
                address = (kwargs["host"], kwargs["port"])
            )

    def read(self, start: int, count: int = 1, is_coil: bool = False) -> list:
        """
        start: start address
        count: number of addresses
        is_coil: True if read coils

        return: list of values
        """
        return self.__store[self.__id].getValues(
            Modbus_Function.READ_COILS if is_coil else Modbus_Function.READ_H_REGS,
            start, count, True, self.__id
        )
    
    def write(self, start: int, values: list, is_coil: bool = False):
        """
        start: start address
        values: values to write
        is_coil: True if read coils

        return: True if success
        """
        self.__store[self.__id].setValues(
            Modbus_Function.WRITE_COILS if is_coil else Modbus_Function.WRITE_REGS,
            start, values, True, self.__id
        )