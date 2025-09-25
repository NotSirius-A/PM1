from measurements import sensors

class DeviceMode():
    pass
class EmergencyMode(DeviceMode):
    pass
class ContinuousMode(DeviceMode):
    pass
class NormalMode(DeviceMode):
    pass

class __DeviceConfig():
    """
    This class hold parameters which describe the configuration of the actual physical device
    These parameters should NOT be changed by the program
    """

    APP_NAME: str = "PM1"
    APP_VERSION: str = "1.0"
    
    NUM_OF_CHANNELS: int = 3
    NUM_OF_ADCs: int = 1
    ADS124S08_1_RRef: float = 2000

    ALLOWED_PROBES_TYPES: set = {sensors.SensorPt100, sensors.SensorPt1000}

    USB_CHANNEL_SPECIFIERS: dict[str, int] = {"C0": 0, "C1": 1, "C2": 2}

    MODBUS_HARDWARE_SETTINGS: dict = {
        "uart_id": 0,
        "pins": (16, 17),
        "ctrl_pin": 18,
    }

    MODBUS_MIN_BAUDRATE: int = 1200
    MODBUS_MAX_BAUDRATE: int = 115200


    SENSORS_AS_TEXT: dict[type[sensors.SensorProbe], str] = {
        sensors.SensorNTC: "NTC",
        sensors.SensorPt100: "Pt100",
        sensors.SensorPt1000: "Pt1000",
    }
    TEXT_AS_SENSOR: dict[str, type[sensors.SensorProbe]]= dict((v, k) for k, v in SENSORS_AS_TEXT.items())

    MODES_AS_TEXT: dict[type[DeviceMode], str] = {
        EmergencyMode: "Emergency",
        ContinuousMode: "Continuous",
        NormalMode: "Normal",
    }
    TEXT_AS_MODE: dict[str, type[DeviceMode]]= dict((v, k) for k, v in MODES_AS_TEXT.items())



    EMODE_PIN_ID: int = 20
    CMODE_PIN_ID: int = 21

    LED1_PIN_ID: int = 14

    @classmethod
    def calculate_resistance_ADS124S08(cls, reading: float, probe: type[sensors.SensorProbe], calibration: tuple):
        assert len(calibration) == 2

        if probe == sensors.SensorPt100:
            gain = 16
        elif probe == sensors.SensorPt1000:
            gain = 2
        else:
            gain = 1

        RRef_offset = calibration[0]
        R_offset = calibration[1]

        RRef = cls.ADS124S08_1_RRef + RRef_offset

        R =  RRef * (reading / (gain * 2**22))

        R = R + R_offset

        return R

