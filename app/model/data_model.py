from sqlalchemy import Column, Integer, String
from app import db

"""
Database for saving events
TO DO: update auto clean after ... days
"""
class MachineData(db.Model):
    __tablename__ = "machine"
    id                  = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId            = Column("deviceId", String(16), nullable=False)
    machineStatus       = Column("machineStatus", Integer, nullable=False)
    actual              = Column("actual", Integer, nullable=False)
    ng                  = Column("ng", Integer)
    runningNumber       = Column("runningNumber", Integer, nullable=False)
    timestamp           = Column("timestamp", Integer)
    changeover          = Column("changeover", Integer)
    upTime              = Column("upTime", Integer)
    changeType          = Column("changeType", Integer)

class ProductionData(db.Model):
    __tablename__ = "production"
    id                          = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId                    = Column("deviceId", String(16), nullable=False)
    start_time                  = Column("start_time", Integer, nullable=False)
    start_production_time       = Column("start_production_time", Integer, nullable=False)
    end_time                    = Column("end_time", Integer, nullable=False)
    actual                      = Column("actual", Integer)
    ng                          = Column("ng", Integer)
    gap                      = Column("gap", Integer)
    test_qty                      = Column("test_qty", Integer)
    runningNumber       = Column("runningNumber", Integer, nullable=False)

class DowntimeData(db.Model):
    __tablename__ = "downtime"
    id                          = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId                    = Column("deviceId", String(16), nullable=False)
    machineStatus               = Column("machineStatus", Integer, nullable=False)
    timestamp                   = Column("start_time", Integer, nullable=False)
    duration                    = Column("start_production_time", Integer, nullable=False)
    end_time                    = Column("end_time", Integer, nullable=False)
    runningNumber               = Column("runningNumber", Integer, nullable=False)

db.create_all()

'''
fast_mqtt.client.subscribe("/+/+/machine")
fast_mqtt.client.subscribe("/+/+/uptime")

actual {"deviceId": "M01",  "runningNumber": 5, "timestamp": 1691147990, "actual" : 10}
status {"deviceId": "M01", "machineStatus": 0, "runningNumber": 5, "timestamp": 1691147990, "upTime": 118}
changeover {"deviceId": "M01",  "runningNumber": 5, "timestamp": 1691147990, "changeover" : 1}
'''