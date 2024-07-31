from pymodbus.client.sync import ModbusSerialClient


modbusMaster = ModbusSerialClient(
    method      = 'rtu', 
    port        = "COM7", 
    timeout     = 1, 
    baudrate    = 9600
)

modbusMaster.connect()

r = modbusMaster.read_holding_registers(
    address = 4096 + 450,
    count   = 7,
    unit    = 1
)
registerData = r.registers

print(registerData)
