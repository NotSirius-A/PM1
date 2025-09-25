import machine
import network
import time
import mip
import utime

from device_config import __DeviceConfig
from app import AppConfig

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(AppConfig.DEFAULTS["wifi_config"]["ssid"], AppConfig.DEFAULTS["wifi_config"]["password"])

# Wait for Wi-Fi connection
connection_timeout = 5
while connection_timeout > 0:
    if wlan.status() >= 3:
        break
    connection_timeout -= 1
    print('Waiting for Wi-Fi connection...')
    utime.sleep(1)

time.sleep(1)
print('Device connected to network: {}'.format(wlan.isconnected()))
mip.install('github:brainelectronics/micropython-modbus')
print('Installation completed')
machine.soft_reset()