from configure import STATUS
from .ultils import parse_register_data

def map_data_plc(deviceId, registerData):
    status = 0
    actual = 0
    changeProduct = None
    # if int(registerData[2]) == 1:
    #     status = STATUS.IDLE
    # elif int(registerData[2]) == 2:
    #     status = STATUS.RUN
    # else:
    #     status = STATUS.ERROR
    # changeProduct   = int(registerData[0])
    # status =  int(registerData[2])
    # actual          = int(registerData[8])
    # ng              = int(registerData[4])
    # gap             = int(registerData[6])
    
    status          = int(registerData[0])
    actual          = int(registerData[6])
    ng              = int(registerData[2])
    changeProduct   = int(registerData[1])
    gap             = int(registerData[4])
    test_qty        = int(registerData[8])
    return [
        status,
        actual,
        changeProduct,
        ng,
        gap,
        test_qty
    ]