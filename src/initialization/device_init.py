from gc import collect as gc_collect, mem_free as gc_mem_free
from machine import Pin, WDT, reset
import utime

import app
from device_config import __DeviceConfig, DeviceMode, NormalMode, EmergencyMode, ContinuousMode
from initialization import emode

import web.web as w
import measurements.measurements as m
import communications.communications as c

def initialize_device(app_state: app.AppState, app_config: app.AppConfig) -> tuple[dict, m.ct.MeasurementController, c.c_usb.USBController, c.c_modbus.ModbusController, w.WebServer|None, WDT|None]:

    emode_pin = Pin(__DeviceConfig.EMODE_PIN_ID, Pin.IN, Pin.PULL_UP)
    cmode_pin = Pin(__DeviceConfig.CMODE_PIN_ID, Pin.IN, Pin.PULL_UP)

    device_mode: type[DeviceMode]

    if emode_pin.value() == 0:
        device_mode = EmergencyMode
    elif cmode_pin.value() == 0:
        device_mode = ContinuousMode
    else:
        device_mode = NormalMode
    app_state.device_mode = device_mode

    if device_mode is EmergencyMode:
        emode.run_mode(app_state, app_config)
        reset()
    elif device_mode is ContinuousMode:
        wdt = WDT(timeout=7000)
        wdt.feed()
    else:
        wdt = None

    try:
        app_config.load_from_json()
    except Exception as e:
        if app_config.other_config["debug_enabled"]:
            print("Config loading failed, exception: {e}")


    if app_config.other_config["debug_enabled"]:
        print("Device is running with debug enabled, which is only intended for troubleshooting. Use `WC;OT;DB;False` command to disable it.")

    board_led = Pin('LED', Pin.OUT)
    board_led.high()

    led1 = Pin(__DeviceConfig.LED1_PIN_ID, Pin.OUT)
    led1.high()

    measurement_controller = m.initialize_measurements(app_state, app_config)

    usb_controller, modbus_controller = c.initialize_communications(app_state, app_config)


    app_state.start_time_utc = utime.gmtime()


    reset_device_after_fail = bool(device_mode is ContinuousMode)

    if app_config.wifi_config["wifi_enabled"]:
        if wdt:
            wdt.feed()

        network_info = w.connect_wifi(
            app_config.wifi_config, 
            reset_after_fail=reset_device_after_fail, 
            allow_print=app_config.other_config["debug_enabled"],
            wdt=wdt
        )
    else:
        if app_config.other_config["debug_enabled"]:
            print("Wi-Fi disabled, skipping connection attempt")
        network_info = None

    if network_info:
        app_state.network_info = network_info
        app_state.wifi_ok = True

        utime.sleep(0.2)
        s = w.open_socket()
        utime.sleep(0.2)

        web_server = w.WebServer(socket=s, app_state=app_state, app_config=app_config, usb_controller=usb_controller)

    else:
        app_state.wifi_ok = False
        web_server = None

    return (
        {
            "signal_leds": (board_led, led1),
            "mode_pins": (emode_pin, cmode_pin),
        },
        measurement_controller,
        usb_controller,
        modbus_controller,
        web_server,
        wdt,
    )