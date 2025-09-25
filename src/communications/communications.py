from machine import Pin
import utime
from umodbus.serial import ModbusRTU # type: ignore


from communications import modbus_ as c_modbus
from communications import usb_ as c_usb

import app
from device_config import __DeviceConfig

def initialize_communications(app_state: app.AppState, app_config: app.AppConfig) -> tuple[c_usb.USBController, c_modbus.ModbusController]:

    usb_controller = c_usb.USBController(app_state, app_config)


    client = ModbusRTU(
        **__DeviceConfig.MODBUS_HARDWARE_SETTINGS,
        **app_config.modbus_config
    )

    modbus_controller = c_modbus.ModbusController(app_state, app_config, client)

    return usb_controller, modbus_controller