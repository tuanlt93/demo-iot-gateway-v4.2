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
    if int(registerData[5]) == 0: 
        status = 0
    else:
        status = 1
        
    if int(registerData[6]) == 1: 
        status = 3
 
    actual          = int(registerData[14])
    ng              = int(registerData[10])
    # if int(registerData[7]) == 0
    changeProduct   = int(registerData[7])
    gap             = 0
    test_qty        = 0

    # print("status: " + str(status))
    return [
        status,
        actual,
        changeProduct,
        ng,
        gap,
        test_qty
    ]