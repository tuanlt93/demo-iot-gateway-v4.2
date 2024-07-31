from sqlalchemy import Column, Integer, String
from app import db

class MachineSyncData(db.Model):
    __tablename__ = "machine_sync"
    id                  = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId            = Column("deviceId", String(16), nullable=False)
    machineStatus       = Column("machineStatus", Integer, nullable=False)
    actual              = Column("actual", Integer, nullable=False)
    ng                  = Column("ng", Integer, nullable=False)
    runningNumber       = Column("runningNumber", Integer, nullable=False)
    timestamp           = Column("timestamp", Integer)
    changeover          = Column("changeover", Integer)
    upTime              = Column("upTime", Integer)
    changeType          = Column("changeType", Integer)

class MachineOtherSyncData(db.Model):
    __tablename__ = "machine_other_info"
    id                  = Column("id", Integer, primary_key=True, autoincrement=True)
    deviceId            = Column("deviceId", String(16), nullable=False)
    timestamp           = Column("timestamp", Integer)
    runningNumber       = Column("runningNumber", Integer, nullable=False)
    speed               = Column("speed", Integer)
    temperature         = Column("temperature", Integer)
    humidity            = Column("humidity", Integer)

db.create_all()