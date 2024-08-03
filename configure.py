class NetworkCnf(object):
    CONNECTION = "eth0" # "wlan0"

class ModbusCnf(object):
    SAVETIME    = 10 
    METHOD      = "rtu"
    # PORT        = "/dev/ttyAMA1"
    PORT        = "COM6"
    COUNT       = 7
    TIMEOUT     = 1
    BAUDRATE    = 9600

class STATUS(object):
    DISCONNECT = 0
    RUN        = 1
    IDLE       = 2
    ERROR      = 3

class MQTTCnf(object):
    BROKER              = "172.174.244.95"
    # BROKER              = "localhost"
    PORT                = 1883
    MQTT_USERNAME       = "rostek"
    MQTT_PASSWORD       = "rostek2019"
    MQTT_KEEPALIVE      = 5
    MQTT_TLS_ENABLED    = False

class RedisCnf(object):
    HOST        = "localhost"
    PORT        = 6379
    PASSWORD    = ""
    SIEMENSINFO = "/info/siemens"
    DELTAINFO   = "/info/delta"
    HUMTEMPTOPIC= "/humtemp" 

class GeneralConfig(object):
    READINGRATE     = 1
    SENDINGRATE     = 1
    DEFAULTRATE     = 5
    DATAFILE        = "data.db"
    ENTERPRISE      = "etek"
    ACTUALRATE      = 5
    LIMITRECORDS    = 50000
    UPTIME_RATE     = 5
    OTHER_RATE      = 30
    ACTIVE_READ_OTHER = False
    VERSION         = "v31"
    # BASE_URL        = "http://192.168.1.48"
    BASE_URL        = "http://172.174.244.95"
    SYNC_MACHINE_URL    = f"{BASE_URL}:5100/sync/machine"
    SYNC_PRODUCTION_URL = f"{BASE_URL}:5100/sync/production"
    SYNC_DOWNTIME_URL   = f"{BASE_URL}:5100/sync/downtime"

class FLASK(object):
    HOST    = '0.0.0.0'
    PORT    = 5000
    DEBUG   = False

deltaConfigure = {
    "METHOD"        :  "rtu",
    "HOST"          :  "192.168.0.1",
    # "PORT"          :  "/dev/ttyAMA1",
    "PORT"          :  "502",
    "TIMEOUT"       :  1,
    "BAUDRATE"      :  9600,
    "LISTDEVICE"    : [
        # {
        #     "ID"        : "NIDEC-M01",
        #     "UID"       : 1,
        #     "COUNT"     : 10,
        #     "ADDRESS"   : 4096 + 450,
        # },
        # {
        #     "ID"        : "NIDEC-M02",
        #     "UID"       : 2,
        #     "COUNT"     : 10,
        #     "ADDRESS"   : 4096 + 450,
        # },
        # {
        #     "ID"        : "NIDEC-M03",
        #     "UID"       : 3,
        #     "COUNT"     : 10,
        #     "ADDRESS"   : 4096 + 450,
        # },
        {
            "ID"        : "ETEK-01",
            "UID"       : 1,
            "COUNT"     : 50,
            "ADDRESS"   : 0,
        }

    ]
}

registers = {
    'DB100.DBD0': ('real', 0),
    'DB100.DBD4': ('real', 2),
    'DB100.DBW8': ('int', 4),
    'DB100.DBW10': ('int', 5),
    'DB100.DBW12': ('word', 6),
    'DB100.DBW14': ('int', 7),
    'DB100.DBW16': ('int', 8),
    'DB100.DBW18': ('int', 9),
    'DB100.DBD20': ('dint', 10),
    'DB100.DBW24': ('int', 12),
    'DB100.DBW26': ('int', 13),
    'DB100.DBW28': ('dint', 14),
    'DB100.DBD32': ('dint', 16),
    'DB100.DBW36': ('int', 18),
    'DB100.DBD38': ('dint', 19),
    'DB100.DBD42': ('real', 21),

    # trục 1
    'DB100.DBD46': ('real', 23),
    'DB100.DBD50': ('real', 25),

    # trục 2
    'DB100.DBD54': ('real', 27),
    'DB100.DBD58': ('real', 29),

    # trục 3
    'DB100.DBD62': ('real', 31),
    'DB100.DBD66': ('real', 33),

    # trục 4
    'DB100.DBD70': ('real', 35),
    'DB100.DBD74': ('real', 37),

    # trục 5
    'DB100.DBD78': ('real', 39),
    'DB100.DBD82': ('real', 41),

    # trục 6
    'DB100.DBD86': ('real', 43),
    'DB100.DBD90': ('real', 45),


}