from app.model.data_model import MachineData, ProductionData, DowntimeData
from app.model.sync_model import MachineSyncData, MachineOtherSyncData
import logging, time, json, schedule
from configure import *
from sqlalchemy import and_
from app.machine.plc_delta import DELTA_SA2
from hmi.hmi import Hmi_Handler
from utils.threadpool import ThreadPool
from app import redisClient, db
from vntime import *
import requests
from time import sleep
import paho.mqtt.client as paho

workers = ThreadPool(10)

def on_connect(client, userdata, flags, rc):
    print('CONNACK received with code %d.' % (rc))
    
def send_message(client):
    topic = f"/{GeneralConfig.VERSION}/{GeneralConfig.ENTERPRISE}/uptime"
    topic_electic = f"/{GeneralConfig.VERSION}/{GeneralConfig.ENTERPRISE}/electrical"
    topic_machine_state = f"/{GeneralConfig.VERSION}/{GeneralConfig.ENTERPRISE}/machine_state"

    for device in deltaConfigure["LISTDEVICE"]:
        deviceId  = device["ID"]

        redisKey = f"{deviceId}/uptime"
        redis_electrical_key = f"{deviceId}/electrical"
        redis_machine_state_key = f"{deviceId}/machine_state"

        data = redisClient.hgetall(redisKey)
        # print(data)
        data_electrical_key = redisClient.hgetall(redis_electrical_key)
        data_machine_state_key = redisClient.hgetall(redis_machine_state_key)
        
        for key in data:
            if key!= "deviceId":
                data[key] = int(data[key])
        if "deviceId" not in data:
            logging.warning(f"Device {deviceId} not have data")
        else:
            status = client.publish(topic, json.dumps(data))
            logging.info(status)
            if status[0] != 0:
                raise Exception("-> Error publish to cloud")
            
        if data_electrical_key:
            status = client.publish(topic_electic, json.dumps(data_electrical_key))
            logging.info(status)
            if status[0] != 0:
                raise Exception("-> Error publish to cloud")
            
        if data_machine_state_key:
            status = client.publish(topic_machine_state, json.dumps(data_machine_state_key))
            logging.info(status)
            if status[0] != 0:
                raise Exception("-> Error publish to cloud")

        
def send_mqtt_uptime():
    """Send up time to server via mqtt
    """
    while True:
        try:
            client = paho.Client()
            client.on_connect = on_connect
            client.username_pw_set(MQTTCnf.MQTT_USERNAME, MQTTCnf.MQTT_PASSWORD)
            client.connect(MQTTCnf.BROKER, MQTTCnf.PORT )
            client.loop_start()
            while True:
                logging.warning("-- publish mqtt")
                send_message(client)
                time.sleep(GeneralConfig.UPTIME_RATE)
        except Exception as e:
            logging.error("MQTT ERROR: " + str(e) + "\nTrying to reconnect...")
            time.sleep(30)
        
def init_objects():
    """
    Create instance of machine object and start related functions
    """
    logging.warning("Starting program")
    plcDelta = DELTA_SA2(redisClient, deltaConfigure)
    start_service(plcDelta, deltaConfigure, redisClient)

def start_service(object,configure,redisClient):
    """
    1. Start scheduling for syncing at default sending rate and scheduling service
    2. Start instance's internal function
    3. Start microservice for sending data
    """

    workers.add_task(object.start)
    workers.add_task(synchronize_data)
    workers.add_task(synchronize_production_data)
    workers.add_task(synchronize_downtime_data)
    if GeneralConfig.ACTIVE_READ_OTHER:
        workers.add_task(synchronize_other_data)
    workers.add_task(updateHmi, object, configure)
    workers.add_task(send_mqtt_uptime)
    
    logging.warning("start sync data")

def start_scheduling_thread():
    """
    Thread to schedule service
    """
    while True:
        schedule.run_pending()
        time.sleep(1)

def synchronize_data():
    """
    Go to database named MachineSyncData, get data and publish by MQTT to server 
    """
    logging.info("--start sync")
    while True:   
        time.sleep(GeneralConfig.SENDINGRATE)
        try:
            results = db.session.query(MachineSyncData).order_by(MachineSyncData.id.asc()).limit(100).all()
            # db.session.close()
            # logging.info(result)
            if len(results) > 0:
                payload = []
                for result in results:
                    sendData = {
                        "id"                : result.id,
                        "deviceId"          : result.deviceId,
                        "runningNumber"     : result.runningNumber,
                        "timestamp"         : result.timestamp,
                        "actual"            : result.actual,
                        "ng"                : result.ng,
                        "machineStatus"     : result.machineStatus,
                        "upTime"            : result.upTime,
                        "changeover"        : result.changeover,
                        "changeType"        : result.changeType
                    }
                    payload.append(sendData)
           
                response = requests.post(GeneralConfig.SYNC_MACHINE_URL, json=payload)
            
                print("Status Code", response.status_code)
                if response.status_code == 200:
                    for result in results:
                        db.session.delete(result)
                    db.session.commit()
                else:
                    logging.error(response.json())
        except Exception as e:
            logging.error(e)

def synchronize_production_data():
    """
    Go to database named MachineSyncData, get data and publish by MQTT to server 
    """
    logging.info("--start sync")
    while True:   
        time.sleep(GeneralConfig.SENDINGRATE)
        time.sleep(3)
        try:
            results = db.session.query(ProductionData).order_by(ProductionData.id.asc()).limit(100).all()
            # db.session.close()
            # logging.info(result)
            if len(results) > 0:
                payload = []
                print("SEND SYNC PRODUCTION TIME --------------- ->> ")
                for result in results:
                    sendData = {
                        "id"                    : result.id,
                        "deviceId"              : result.deviceId,
                        "start_time"            : result.start_time,
                        "start_production_time" : result.start_production_time,
                        "end_time"              : result.end_time,
                        "actual"                : result.actual,
                        "ng"                    : result.ng,
                        "qty_report"            : result.gap,
                        "test_qty"              : result.test_qty,
                        "runningNumber"         : result.runningNumber,
                    }
                    
                    payload.append(sendData)
                    # print(sendData)
                
                response = requests.post(GeneralConfig.SYNC_PRODUCTION_URL, json=payload)
            
                print("Status Code", response.status_code)
                if response.status_code == 200:
                    for result in results:
                        db.session.delete(result)
                    db.session.commit()
                else:
                    logging.error(response.json())
        except Exception as e:
            logging.error(e)

def synchronize_downtime_data():
    """
    Go to database named MachineSyncData, get data and publish by MQTT to server 
    """
    logging.info("--start sync")
    while True:   
        time.sleep(GeneralConfig.SENDINGRATE)
        try:
            results = db.session.query(DowntimeData).order_by(DowntimeData.id.asc()).limit(1).all()
            # db.session.close()
            # logging.info(result)
            if len(results) == 1:
                payload = []
                for result in results:
                    sendData = {
                        "id" :  result.id,
                        "device_id" : result.deviceId,
                        "timestamp" : result.timestamp,
                        "duration" :  result.duration,
                        "status" :  result.machineStatus,
                        "reason_code" : 0,
                        "runningNumber" : result.runningNumber
                    }
                    payload.append(sendData)
                
                response = requests.post(GeneralConfig.SYNC_DOWNTIME_URL, json=payload)
            
                print("Status Code", response.status_code)
                if response.status_code == 200:
                    for result in results:
                        db.session.delete(result)
                    db.session.commit()
                else:
                    logging.error(response.json())
        except Exception as e:
            logging.error(e)

def synchronize_other_data():
    """
    Go to database named MachineSyncData, get data and publish by MQTT to server 
    """
    logging.info("--start sync other")
    while True:   
        # time.sleep(GeneralConfig.SENDINGRATE)
        time.sleep(5)
        try:
            result = db.session.query(MachineOtherSyncData).order_by(MachineOtherSyncData.id.asc()).first()
            db.session.close()
            logging.info(result)
            if not result:
                continue
            logging.warning(f"sync other: {result}")
            sendData = {
                "id"                : result.id,
                "deviceId"          : result.deviceId,
                "runningNumber"     : result.runningNumber,
                "timestamp"         : result.timestamp,
                "speed"             : result.speed,
                "temperature"       : result.temperature,
                "humidity"          : result.humidity
            }
            mqtt.publish(f"/{GeneralConfig.VERSION}/{GeneralConfig.ENTERPRISE}/other",json.dumps(sendData),qos = 0)
            # logging.warning(f"Complete sending ->> other speed {sendData['speed']}")
        except Exception as e:
            logging.error(e)

def updateHmi(plc: DELTA_SA2, configure):
    """
    Update to hmi
    """
    hmi = Hmi_Handler()
    while True:
        for device in configure["LISTDEVICE"]:
            device_uid  = device["UID"]
            device_id   = device["ID"]
            if not plc.register_data[device_id]:
                continue

            connect = plc.register_data[device_id]["connect"]
            production = plc.register_data[device_id]["production"]
            mach_state = plc.register_data[device_id]["mach_state"]
            prod_state = plc.register_data[device_id]["prod_state"]
            hmi.updatePlc(device_uid, connect, int(production), int(mach_state), int(prod_state))
        sleep(0.5)

def query_data(deviceId,timeFrom,timeTo):
    """
    Query data for request
    """
    data = []
    results = MachineData.query.filter(and_(MachineData.timestamp >= timeFrom,MachineData.timestamp <= timeTo, MachineData.deviceId == deviceId)).all()
    for result in results:
        data.append(
            {
                "deviceId"        : result.deviceId,
                "machineStatus"   : result.machineStatus,
                "actual"          : result.actual,
                "runningNumber"   : result.runningNumber,
                "timestamp"       : result.timestamp,
                "temperature"     : result.temperature,
                "humidity"        : result.humidity,
                "changeover"      : result.changeover
            }
        )
    return data
