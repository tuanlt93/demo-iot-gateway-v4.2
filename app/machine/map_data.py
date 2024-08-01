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
    
    status          = 0
    actual          = 0
    ng              = 0
    changeProduct   = 0
    gap             = 0
    test_qty        = 0
    return [
        status,
        actual,
        changeProduct,
        ng,
        gap,
        test_qty
    ]