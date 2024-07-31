from app import mqtt, db, redisClient
from app.model.sync_model import MachineSyncData, MachineOtherSyncData
from app.model.data_model import MachineData
import socket, json, logging
from configure import GeneralConfig, deltaConfigure
from datetime import timedelta

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 5))
    ipv4 = s.getsockname()[0]
    s.close()
    return ipv4

def get_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
    return str(timedelta(seconds = round(uptime_seconds)))

def cmd_handler(payload):
    try:
        data = json.loads(payload)
        cmd = data["cmd"]
        if cmd =="delete":
            time = data["timestamp"]
            db.session.query(MachineData).filter(MachineData.timestamp <= time).delete()   
            db.session.query(MachineSyncData).filter(MachineSyncData.timestamp <= time).delete()   
            db.session.query(MachineOtherSyncData).filter(MachineOtherSyncData.timestamp <= time).delete()
            db.session.commit()
            db.session.close()
        if cmd =="get_info":
            machines = {}
            for device in deltaConfigure["LISTDEVICE"]:
                topic =  "/device/V2/" + device["ID"] + "/raw"
                machines[device["ID"]] = redisClient.hgetall(topic)
                logging.info("--<><>")
            mqtt.publish(f'/{GeneralConfig.VERSION}/{GeneralConfig.ENTERPRISE}/info', json.dumps({
                "local_ip" : get_ip(),
                "machine_count" : MachineData.query.count() ,
                "machine_sync_count" : MachineSyncData.query.count(),
                "machine_other_count" : MachineOtherSyncData.query.count(),
                "gateway_uptime" : get_uptime(),
                "machines" : machines
            }))
    except Exception as e:
        logging.error(str(e))
