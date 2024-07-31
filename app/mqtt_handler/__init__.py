
from app import mqtt, db, redisClient

from app.model.sync_model import MachineSyncData, MachineOtherSyncData
from app.model.data_model import ProductionData, DowntimeData

import logging, json
from configure import GeneralConfig, deltaConfigure
from .cmd import cmd_handler

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    logging.warning("ON CONNECT")
    mqtt.subscribe(f'/{GeneralConfig.VERSION}/{GeneralConfig.ENTERPRISE}/sync')
    # mqtt.subscribe(f'/{GeneralConfig.VERSION}/{GeneralConfig.ENTERPRISE}/sync_other')
    # mqtt.subscribe(f'/{GeneralConfig.VERSION}/{GeneralConfig.ENTERPRISE}/sync_production')

    mqtt.subscribe(f'/{GeneralConfig.VERSION}/{GeneralConfig.ENTERPRISE}/cmd')
    for device in deltaConfigure["LISTDEVICE"]:
        topic =  f"/{device['ID']}/setting"
        mqtt.subscribe(topic)
    
    # mqtt.subscribe(f'/duchieu/machine/sync')
    
@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    topic=message.topic
    payload=message.payload.decode()
    logging.error(f"{topic} -- {payload}")

    if "/sync" in topic:
        try:
            data = json.loads(payload)
            if data["type"] == "sync_other":
                db.session.query(MachineOtherSyncData).filter_by(id=data["id"]).delete()
            if data["type"] == "sync_production":
                db.session.query(ProductionData).filter_by(id=data["id"]).delete()
            if data["type"] == "sync_machine":
                db.session.query(MachineSyncData).filter_by(id=data["id"]).delete()
            if data["type"] == "sync_downtime":
                db.session.query(DowntimeData).filter_by(id=data["id"]).delete()
            db.session.commit()
            db.session.close()
            logging.info(f"delete ->> {payload}")
        except Exception as e:
            logging.error(str(e))
    elif "/cmd" in topic:
        try:
            cmd_handler(payload)
        except Exception as e:
            logging.error(str(e))
    elif "/setting" in topic:
        try:
            data = json.loads(payload)
            if "runningNumber" in data:
                redisClient.hset(f"/device/V2/{data['deviceId']}/raw","runningNumber", data["runningNumber"] )
        except:
            pass