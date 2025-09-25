import json

from measurements import sensors
from device_config import __DeviceConfig, DeviceMode, NormalMode, EmergencyMode, ContinuousMode
    
class AppState:
    SAVE_FILE_FILENAME = "SAVE_STATE.json"

    DEFAULTS = {
        "device_mode": NormalMode,
        "is_initialized": False,
        "free_memory": None,
        "start_time_utc": None,
        "time_utc": None,
        "measurement_results": None,
        "network_info": None,
        "wifi_ok": False
    }

    def __init__(self) -> None:
        d = self.DEFAULTS
 
        self.device_mode: type[DeviceMode] = d["device_mode"]
        self.is_initialized: bool = d["is_initialized"]
        
        self.free_memory = d["free_memory"]
        self.start_time_utc = d["start_time_utc"]
        self.time_utc = d["time_utc"]

        self.measurement_results = d["measurement_results"]

        self.network_info = d["network_info"]
        self.wifi_ok = d["wifi_ok"]
    

    def asdict(self) -> dict:
        return {
            "device_mode": self.device_mode,
            "is_initialized": self.is_initialized, 
            "network_info": self.network_info,
            "wifi_ok": self.wifi_ok,
            "free_memory": self.free_memory,
            # "time_utc": self.time_utc, 
            # "start_time_utc": self.start_time_utc, 
            "measurement_results": self.measurement_results
        }

    def asjson(self) -> str:

        data = self.asdict()
        for i, channel in enumerate(data["measurement_results"]):
            if len(channel) > 0:
                probe = channel["probe"]
                data["measurement_results"][i]["probe"] = __DeviceConfig.SENSORS_AS_TEXT[probe]

        data["device_mode"] = __DeviceConfig.MODES_AS_TEXT[data["device_mode"]]

        attrs = {
            "info": {
                "NAME": __DeviceConfig.APP_NAME,
                "VERSION": __DeviceConfig.APP_VERSION,
            },
            "data": data,
        }

        json_str = json.dumps(attrs)

        # Reverse the operation, because it alters AppConfig state,
        # A deep copy should be used here, but the implementation is not available in stock micropython
        for i, channel in enumerate(data["measurement_results"]):
            if len(channel) > 0:
                probe = channel["probe"]
                data["measurement_results"][i]["probe"] = __DeviceConfig.TEXT_AS_SENSOR[probe]

        return json_str 

    def measurements_asjson(self) -> str:
        data = self.measurement_results.copy()
        for i, channel in enumerate(data):
            if len(channel) > 0:
                probe = channel["probe"]
                data[i]["probe"] = __DeviceConfig.SENSORS_AS_TEXT[probe]

        json_str = json.dumps(data)

        for i, channel in enumerate(data):
            if len(channel) > 0:
                probe = channel["probe"]
                data[i]["probe"] = __DeviceConfig.TEXT_AS_SENSOR[probe]

        return json_str

    def save_to_file(self, filename: str="") -> None:
        if len(filename) < 1:
            filename = self.SAVE_FILE_FILENAME

        json_str = self.asjson()

        with open(filename, "w", encoding="UTF-8") as f:
            f.write(json_str)


class AppConfig():
    SAVE_FILE_FILENAME = "SAVE_CONFIG.json"

    DEFAULTS = {
        "other_config": {
            "debug_enabled": False
        },
        "wifi_config" : {
            "ssid": "ssid",
            "password": "password",
            "wifi_enabled": False
        },
        "modbus_config": {
            "addr": 1,
            "baudrate": 19200,
            "data_bits": 8,
            "stop_bits": 1,
            "parity": None, #0 (even) or 1 (odd)
        },
        "channel_config": [
            {
                "_name": "CH0",
                "verbose_name": "CH0",
                "is_enabled": True,
                "probe": sensors.SensorPt100,
                "_num_readings_per_measurement": 1,
                "time_between_measurements_ms": 0, 
                "num_of_readings_to_store": 1,
                "_calibration": (0.3, 0),
                "_extra_attrs": {
                }
            },
            {
                "_name": "CH1",
                "verbose_name": "CH1",
                "is_enabled": True,
                "probe": sensors.SensorPt100,
                "_num_readings_per_measurement": 1,
                "time_between_measurements_ms": 0, 
                "num_of_readings_to_store": 1,
                "_calibration": (0.3, 0),
                "_extra_attrs": {
                }
            },
            {
                "_name": "CH2",
                "verbose_name": "CH2",
                "is_enabled": True,
                "probe": sensors.SensorPt100,
                "_num_readings_per_measurement": 1,
                "time_between_measurements_ms": 0, 
                "num_of_readings_to_store": 1,
                "_calibration": (0.3, 0),
                "_extra_attrs": {
                }
            },
        ],
    }


    def __init__(self) -> None:
        d = self.DEFAULTS

        self.wifi_config: dict = d["wifi_config"]
        self.modbus_config: dict = d["modbus_config"]
        self.channel_config: list[dict] = d["channel_config"]
        self.other_config: dict = d["other_config"]

        # self.is_publishing_enabled = True
        # self.publish_address = "http://filipgrzymski.com/data/"
        # self.publish_period_ms = 10000 
        # self.last_publish_ticks_ms = 0

    def asdict(self) -> dict:
        return {
            "other_config": self.other_config,
            "wifi_config": self.wifi_config,
            "modbus_config": self.modbus_config,
            "channel_config": self.channel_config
        }

    def asjson(self) -> str:
        data = self.asdict()
        for i, channel in enumerate(data["channel_config"]):
            if len(channel) > 0:
                probe = channel["probe"]
                data["channel_config"][i]["probe"] = __DeviceConfig.SENSORS_AS_TEXT[probe]

        json_str = json.dumps(data)

        # Reverse the operation, because it alters AppConfig state,
        # A deep copy should be used here, but the implementation is not available in stock micropython
        data = self.asdict()
        for i, channel in enumerate(data["channel_config"]):
            if len(channel) > 0:
                probe = channel["probe"]
                data["channel_config"][i]["probe"] = __DeviceConfig.TEXT_AS_SENSOR[probe]
        
        return json_str 

    def save_to_file(self, filename: str="") -> None:
        if len(filename) < 1:
            filename = self.SAVE_FILE_FILENAME

        data = self.asdict()
        for i, channel in enumerate(data["channel_config"]):
            probe = channel["probe"]
            data["channel_config"][i]["probe"] = __DeviceConfig.SENSORS_AS_TEXT[probe]

        with open(filename, "w", encoding="UTF-8") as f:
            attrs = {
                "info": {
                    "NAME": __DeviceConfig.APP_NAME,
                    "VERSION": __DeviceConfig.APP_VERSION,
                },
                "data": data,
            }

            json.dump(attrs, f)


        # Reverse the operation, because it alters AppConfig state,
        # A deep copy should be used here, but the implementation is not available in stock micropython
        data = self.asdict()
        for i, channel in enumerate(data["channel_config"]):
            probe = channel["probe"]
            data["channel_config"][i]["probe"] = __DeviceConfig.TEXT_AS_SENSOR[probe]

    def load_from_json(self, filename: str="") -> None:
        if len(filename) < 1:
            filename = self.SAVE_FILE_FILENAME

        with open(filename, "r", encoding="UTF-8") as f:
            attrs = json.load(f)

        data = attrs["data"]

        for i, channel in enumerate(data["channel_config"]):
            probe = channel["probe"]
            data["channel_config"][i]["probe"] = __DeviceConfig.TEXT_AS_SENSOR[probe]


        self.other_config = data["other_config"]
        self.wifi_config = data["wifi_config"]
        self.modbus_config = data["modbus_config"]
        self.channel_config = data["channel_config"]