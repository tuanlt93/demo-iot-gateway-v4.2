from pymodbus.client.sync import ModbusSerialClient, ModbusTcpClient
import logging, json, time
import utils.vntime as VnTimeStamps
from configure import *
from app.model.data_model import MachineData, ProductionData, DowntimeData
from app.model.sync_model import MachineSyncData, MachineOtherSyncData
from app import db
from .map_data import map_data_plc as map_data_modbus
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import struct

from hmi.hmi import PROD_STATE, MACH_STATE

class DELTA_SA2():
    def __init__(self,redisClient, configure):
        self.__redisClient          = redisClient
        self.__modbusConnection     = False
        self.__kernelActive         = False
        self.__configure            = configure
        self.deviceData             = {}
        self.register_data          = {}

        self.lastUpTime             = {}
        self.lastOtherTime          = {}

        self.productionData         = {}
        self.maxActual              = {} # so actual theo runningnumber
        self.__get_redis_data()

    def start(self):
        """
        Start function
        """
        self.__kernelActive = True
        logging.warning("Init Kernel successful")
        self.__connect_modbus()
        self.__start_reading_modbus()
       
    def __get_redis_data(self):
        """
        Load old data from redis
        """
        for device in self.__configure["LISTDEVICE"]:
            deviceId    = device["ID"]
            #-- new
            timeNow = round(VnTimeStamps.now())

            #load production data
            productionTopic    = "/device/V2/" + device["ID"] + "/production"
            self.productionData[deviceId] = self.__redisClient.hgetall(productionTopic)
            if not self.productionData[deviceId]:
                self.productionData[deviceId] = {
                    "runningNumber" : 0,
                    "start_time" : timeNow,               # => bat dau chay thu
                    "start_production_time" : timeNow,    # bat dau san xuat
                    "end_time" : 0,                  # ket thuc san xuat
                    "actual": 0                     # so luong san xuat trong 1 period          
                }
                self.__save_raw_data_to_redis(productionTopic, self.productionData[deviceId])
            for key in self.productionData[deviceId]:
                self.productionData[deviceId][key] = round(float(self.productionData[deviceId][key]))

            #=--- load device data
            deviceData  = self.__redisClient.hgetall("/device/V2/" + device["ID"] + "/raw")

            self.deviceData[deviceId]               = {}
            self.deviceData[deviceId]["timestamp"]  = timeNow
            self.register_data[deviceId] = {
                "connect": False,
                "production": 0,
                "mach_state": MACH_STATE.STOP,
                "prod_state": PROD_STATE.STOP,
            }

            if "maxActual" not in deviceData:
                self.deviceData[deviceId]["runningNumber"]      = 0
                self.deviceData[deviceId]["status"]             = STATUS.DISCONNECT
                self.deviceData[deviceId]["actual"]             = 0
                self.deviceData[deviceId]["ng"]                 = 0
                self.deviceData[deviceId]["gap"]                 = 0
                self.deviceData[deviceId]["changeProduct"]      = 0
                self.deviceData[deviceId]["lastChangeStatus"]   = timeNow
                self.deviceData[deviceId]["lastOtherTime"]      = timeNow
                self.deviceData[deviceId]["lastUptime"]         = timeNow
                self.deviceData[deviceId]["maxActual"]          = 0
            else:
                for key in deviceData:
                    if key != "Device_id":
                        self.deviceData[deviceId][key] = int(float(deviceData[key]))

    def save_production_to_redis(self, deviceId):
        productionTopic    = "/device/V2/" + deviceId + "/production"
        self.__save_raw_data_to_redis(productionTopic, self.productionData[deviceId])
    
    def __connect_modbus(self):
        """
        Init MODBUS RTU connection
        """
        try:
            logging.info(self.__configure)
            # self.__modbusMaster = ModbusSerialClient(
            #     method      = self.__configure["METHOD"], 
            #     port        = self.__configure["PORT"], 
            #     timeout     = self.__configure["TIMEOUT"], 
            #     baudrate    = self.__configure["BAUDRATE"]
            # )

            self.__modbusMaster = ModbusTcpClient(
                host        = self.__configure["HOST"], 
                port        = self.__configure["PORT"], 
                timeout     = self.__configure["TIMEOUT"], 
            )

            self.__modbusMaster.connect()
            self.__modbusConnection = True
        except Exception as e:
            self.__modbusConnection = False
            logging.info(str(e))

    def __save_raw_data_to_redis(self, topic, data):
        """
        Save raw data to redis
        """
        # logging.info(topic)
        for key in data.keys():
            self.__redisClient.hset(topic,key ,data[key])

    def __start_reading_modbus(self):
        """
        Start reading modbus from device 
        """
        
        while self.__kernelActive:
            if not self.__modbusConnection:
                self.__connect_modbus()
            else:
                
                for device in self.__configure["LISTDEVICE"]:
                    deviceId                                = device["ID"]
                    self.deviceData[deviceId]["Device_id"]  = deviceId
                    rawTopic                                = "/device/V2/" + deviceId + "/raw"
                    # logging.warning(deviceId)
                    # self.__read_modbus_data(device,deviceId)
                    try:
                        self.__read_modbus_data(device,deviceId)
                    except Exception as e:
                        
                        logging.error(deviceId + "->> " + str(e))
                        self.register_data[deviceId]["connect"] = False
                        self.deviceData[deviceId]["status"] = STATUS.DISCONNECT
                        redisKey = f"{deviceId}/uptime"
                        self.__redisClient.hset(redisKey, "status" ,  STATUS.DISCONNECT)
                        
                    self.__save_raw_data_to_redis(rawTopic,self.deviceData[deviceId])
            time.sleep(GeneralConfig.READINGRATE)


    def save_sync_machine_data(self, deviceId, status, actual, ng, timeNow, runningNumber, changeover, upTime, changeType):
        countRecords = MachineData.query.count()
        if countRecords > GeneralConfig.LIMITRECORDS:
            firstRecord = db.session.query(MachineData).first()
            db.session.query(MachineData).filter_by(id=firstRecord.id).delete()
            countRecordsSync = MachineSyncData.query.count()
            if countRecordsSync > GeneralConfig.LIMITRECORDS:
                firstRecordSync = db.session.query(MachineSyncData).first()
                db.session.query(MachineSyncData).filter_by(id=firstRecordSync.id).delete()
        insertData = MachineData(
            deviceId            = deviceId, 
            machineStatus       = status,
            actual              = actual,
            ng                  = ng,
            timestamp           = timeNow,     
            runningNumber       = runningNumber,
            changeover          = changeover,
            upTime              = upTime,
            changeType          = changeType
        )

        insertUnsyncedData = MachineSyncData(
            deviceId            = deviceId, 
            machineStatus       = status,
            actual              = actual,
            ng                  = ng,
            timestamp           = timeNow,     
            runningNumber       = runningNumber,
            changeover          = changeover,
            upTime              = upTime,
            changeType          = changeType
        )
        try:
            db.session.add(insertData)
            db.session.add(insertUnsyncedData)
            # if not self.offline:
            #     db.session.add(insertUnsyncedData)
            #     if changeProduct == 2:
            #         logging.warning("Offline")
            #         self.offline = True
            db.session.commit()
            db.session.close() 
            logging.info(f"Complete saving data! -- type {changeType} -- runningnumber {runningNumber} -- changeover {changeover}")
        except Exception as e:
            db.session.rollback()
            db.session.close() 
            logging.error(str(e))

    def save_production_data(self,deviceId, data): # luu du lieu san xuat
        """Luu du lieu san xuat
        """
        # print("save production data")
        countRecords = ProductionData.query.count()
        if countRecords > GeneralConfig.LIMITRECORDS:
            firstRecord = db.session.query(ProductionData).first()
            db.session.query(ProductionData).filter_by(id=firstRecord.id).delete()
        insertData = ProductionData(
            deviceId                = deviceId, 
            start_time              = data['start_time'],
            start_production_time   = data['start_production_time'],
            end_time                = data['end_time'],     
            actual                  = data['actual'],
            ng                      = data['ng'],
            gap                     = data['gap'],
            test_qty                = data['test_qty'],
            runningNumber           = data["runningNumber"]
        )
        # print(data)
        db.session.add(insertData)
        db.session.commit()
        db.session.close() 
        logging.warning(f"Saving production Data: {data}")


    def __read_modbus_datablock_siemen(self, device) -> list:

        results = []
        for reg_name, (data_type, offset) in registers.items():
            # Tính số lượng thanh ghi cần đọc (4 byte cho float/dint, 2 byte cho int/word)
            count = 2 if data_type in ['int', 'word'] else 4

            # Đọc thanh ghi
            address = offset // 2
            result = self.__modbusMaster.read_holding_registers(address, count, unit= 1)

            if result.isError():
                results.append(0)
                logging.error(f'Error reading {reg_name}')
                continue

            # Giải mã dữ liệu dựa trên loại dữ liệu
            if data_type == 'real':
                decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big, wordorder=Endian.Little)
                results.append(decoder.decode_32bit_float())
            elif data_type == 'int':
                results.append(result.registers[0]) # Giả sử là 16-bit integer
            elif data_type == 'word':
                results.append(result.registers[0])  # Giả sử là 16-bit word
            elif data_type == 'dint':
                # Đọc 32-bit signed integer từ hai thanh ghi
                result_dint = struct.unpack('>i', struct.pack('>HH', result.registers[0], result.registers[1]))[0]
                results.append(result_dint)

        return results



    def __read_modbus_data(self,device,deviceId):
        """
        Make request to read modbus and parse data 
        """
        # r = self.__modbusMaster.read_holding_registers(
        #     address = device["ADDRESS"], 
        #     count   = device["COUNT"], 
        #     unit    = device["UID"]
        # )
        # if r.isError():
        #     self.__redisClient.hset(f"/device/V2/{deviceId}/raw", "is_connected", 0)
        # else:
        #     self.__redisClient.hset(f"/device/V2/{deviceId}/raw", "is_connected", 1)
        # registerData = r.registers
        registerData = self.__read_modbus_datablock_siemen(device= device["UID"])
        print(registerData)
        timeNow = round(VnTimeStamps.now())
    
        [raw_status, actual ,changeover, ng , gap, test_qty] = map_data_modbus(deviceId, registerData)
        # print([raw_status, actual ,changeover, ng , gap, test_qty])
        # use for monitor from hmi
        self.register_data[deviceId] = {
            "connect": True,
            "production": actual,
            "mach_state": raw_status,
            "prod_state": changeover
        }
        
        # mapping lai gia tri status
        if raw_status == 0:
            status = 2
        elif raw_status == 2:
            status = 3
        else:
            status = raw_status
        lastStatus = self.deviceData[deviceId]["status"]
        prevChange = self.deviceData[deviceId]["changeProduct"]
        currChange = changeover
        
        self.deviceData[deviceId]["maxActual"] = max(self.deviceData[deviceId]["maxActual"] , actual )

        productionChange = True
        if (prevChange == 2 ) and (currChange == 0):
            logging.warning(f"Dung -> THU:")
            #Start new production period
            self.productionData[deviceId]["runningNumber"] += 1 # increase running number for new period
            self.productionData[deviceId]["actual"] = 0
            self.productionData[deviceId]["start_production_time"] = timeNow
            self.productionData[deviceId]["end_time"] = 0
            self.productionData[deviceId]["ng"] = 0
            self.productionData[deviceId]["gap"] = 0
            self.productionData[deviceId]["start_time"] = timeNow # start
            self.deviceData[deviceId]["maxActual"] = 0
            self.productionData[deviceId]["test_qty"] =  0
            self.save_production_data(deviceId, self.productionData[deviceId])
            logging.info(self.productionData[deviceId])
        elif (prevChange == 0 ) and (currChange == 1):
            logging.warning(f"Thu -> SX")
            self.productionData[deviceId]["start_production_time"] = timeNow
            self.deviceData[deviceId]["maxActual"] = 0
            self.productionData[deviceId]["ng"] = 0
            self.productionData[deviceId]["gap"] = 0
            self.productionData[deviceId]["test_qty"] =  0
            self.save_production_data(deviceId, self.productionData[deviceId])
            logging.info(self.productionData[deviceId])
        elif (prevChange == 1 ) and (currChange == 0):
            logging.warning(f"SX -> THU:")
            self.productionData[deviceId]["end_time"] = timeNow
            self.productionData[deviceId]["actual"] = self.deviceData[deviceId]["maxActual"]
            self.productionData[deviceId]["ng"] = self.deviceData[deviceId]["ng"]
            self.productionData[deviceId]["gap"] = self.deviceData[deviceId]["gap"]
            self.productionData[deviceId]["test_qty"] =  self.deviceData[deviceId]["test_qty"]
            # save data
            self.save_production_data(deviceId, self.productionData[deviceId])
            # bat dau chu ky moi
            self.productionData[deviceId]["runningNumber"] += 1 # increase running number for new period
            self.productionData[deviceId]["start_time"] = timeNow
            self.productionData[deviceId]["start_production_time"] = self.productionData[deviceId]["start_time"]
            self.productionData[deviceId]["actual"] = 0
            self.productionData[deviceId]["end_time"] = 0
            self.productionData[deviceId]["ng"] = 0
            self.productionData[deviceId]["gap"] = 0
            self.deviceData[deviceId]["maxActual"] = 0
            self.productionData[deviceId]["test_qty"] =  0
            self.save_production_data(deviceId, self.productionData[deviceId])
            logging.info(self.productionData[deviceId])

        elif (prevChange == 0 ) and (currChange == 2):
            logging.warning(f"Thu -> Dung: {self.productionData[deviceId]}")
            self.productionData[deviceId]["end_time"] = timeNow
            self.productionData[deviceId]["start_production_time"] = self.productionData[deviceId]["end_time"]
            self.productionData[deviceId]["actual"] = self.deviceData[deviceId]["maxActual"]
            # self.save_production_data(deviceId, self.productionData[deviceId])
            
        ##-- them
        elif (prevChange == 1 ) and (currChange == 2):
            logging.warning(f"SX -> DUNG: {self.productionData[deviceId]}")
            self.productionData[deviceId]["end_time"] = timeNow
            self.productionData[deviceId]["actual"] = self.deviceData[deviceId]["maxActual"]
            self.productionData[deviceId]["ng"] = self.deviceData[deviceId]["ng"]
            self.productionData[deviceId]["gap"] = self.deviceData[deviceId]["gap"]
            self.productionData[deviceId]["test_qty"] =  self.deviceData[deviceId]["test_qty"]
            self.save_production_data(deviceId, self.productionData[deviceId])
            self.deviceData[deviceId]["maxActual"] = 0

        elif (prevChange == 2 ) and (currChange == 1):
            # bat dau chu ky moi
            logging.warning(f"Dung -> SX: {self.productionData[deviceId]}")
            self.deviceData[deviceId]["maxActual"] = 0
            self.productionData[deviceId]["runningNumber"] += 1 # increase running number for new period
            self.productionData[deviceId]["start_time"] = timeNow
            self.productionData[deviceId]["start_production_time"] = self.productionData[deviceId]["start_time"]
            self.productionData[deviceId]["actual"] = 0
            self.productionData[deviceId]["end_time"] = 0
            self.productionData[deviceId]["ng"] = 0
            self.productionData[deviceId]["gap"] = 0
            self.productionData[deviceId]["test_qty"] = 0
            
            self.save_production_data(deviceId, self.productionData[deviceId])
        elif self.deviceData[deviceId]["gap"] != gap:
            self.productionData[deviceId]["gap"] = gap
            self.save_production_data(deviceId, self.productionData[deviceId])
        else:
            productionChange = False
            pass
            # logging.error(f"{deviceId} --- unknonw changeover prev {prevChange} -- cur {currChange}")
        #-------
        if  productionChange:
            logging.info('production change')
            self.save_production_to_redis(deviceId)

        statusChange = lastStatus != status
        runningNumber = self.productionData[deviceId]["runningNumber"]
        
        #-----
        if statusChange and  (changeover != 2):
            logging.warning("change status")
            lastChangeStatus = self.deviceData[deviceId]["lastChangeStatus"]
            if status == 1: # -> Tu trang thai khac doi sang 1
                duration =  timeNow - max(lastChangeStatus, self.productionData[deviceId]["start_time"])
                # print(lastStatus, duration)
                if duration >= 120 :
                    logging.info("this is downtime")
                    newDowntime = DowntimeData(
                        deviceId = deviceId,
                        machineStatus = lastStatus,
                        timestamp = lastChangeStatus,
                        duration = duration,
                        end_time = timeNow,
                        runningNumber = runningNumber
                    )
                    db.session.add(newDowntime)
                    db.session.commit()

            self.deviceData[deviceId]["lastChangeStatus"] = timeNow

        actualChange = self.deviceData[deviceId]['actual'] != actual
        ngChange = self.deviceData[deviceId]['ng'] != ng
        productChange = self.deviceData[deviceId]['changeProduct'] != changeover
    
        #----- check uptime
        upTime = round(timeNow - int(self.productionData[deviceId]["start_production_time"]))
        # logging.info(f"uptime = {round(upTime)}")
        self.deviceData[deviceId]["timestamp"]  = timeNow
        

        
        logging.info(f"Uptime >> {deviceId} RunningNumber = {runningNumber}, Status = {status}, changeover = {changeover}, actual = {actual}")

        uptimeData = {
            "deviceId" : deviceId,
            "start_production_time" : self.productionData[deviceId]["start_production_time"],
            "upTime" : upTime,
            "runningNumber" : runningNumber,
            "changeover" : changeover,
            "actual" : actual,
            "ng" : ng,
            "status" : status
        }

        electrical_data = {
            "voltage"   : registerData[0],
            "ampere"    : registerData[1]

        }

        machine_state_data = {
            "status"    : registerData[3],
            "error_id"     : registerData[4]
        }
        redisKey = f"{deviceId}/uptime"
        redis_electrical_key = f"{deviceId}/electrical"
        redis_machine_state_key = f"{deviceId}/machine_state"

        self.__redisClient.hset(redisKey, mapping = uptimeData)
        self.__redisClient.hset(redis_electrical_key, mapping = electrical_data)
        self.__redisClient.hset(redis_machine_state_key, mapping = machine_state_data)
        
        changeType = 0
        if statusChange:
            changeType = 1
        if actualChange or ngChange:
            changeType += 10
        if productChange:
            changeType += 100

        if changeType !=0:
            self.save_sync_machine_data(deviceId, status, actual, ng, timeNow, runningNumber, changeover, upTime, changeType)
        elif changeType == 10:
            start_production_time = self.productionData[deviceId]["start_production_time"]
            self.save_sync_machine_data(deviceId, status, actual, ng, start_production_time, runningNumber, changeover, upTime, changeType)
            
        #check change
        # logging.info([status, actual ,changeProduct , speed ,temperature, humidity])
        self.deviceData[deviceId]["status"]         = status
        self.deviceData[deviceId]["actual"]         = actual
        self.deviceData[deviceId]["changeProduct"]  = changeover
        self.deviceData[deviceId]["ng"]          = ng
        self.deviceData[deviceId]["gap"]    = gap
        self.deviceData[deviceId]["test_qty"]    = test_qty

        msg = " ->>> "
        if status == 1:
            msg += "RUN"
        elif status == 2:
            msg += "IDLE"
        elif status == 3:
            msg += "ERROR"
        elif status == 0:
            msg += "DISCONNECT"
        msg += " actual: " + str(actual) + " changeover: " + str(changeover)
        # logging.info(msg)