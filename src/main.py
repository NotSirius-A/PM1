import initialization.device_init
import utime
# import ntptime
from machine import Pin, WDT
from gc import collect as gc_collect, mem_free as gc_mem_free

import app
import initialization

# import measurements.measurements as m
# import communications.communications as c
# import web.web as w

gc_collect()

app_state = app.AppState()
app_config = app.AppConfig()

objs = initialization.device_init.initialize_device(app_state, app_config)

IO_pins, measurement_controller, usb_controller, modbus_controller, web_server, wdt = objs

app_state.is_initialized = True

if app_config.other_config["debug_enabled"]:
    print("Initialized")


def main():

    last_ticks_ms = 0
    last_ticks_ms_2 = 0


    while True:
        
        measurement_controller.run()

        app_state.measurement_results = measurement_controller.get_current_results()

        usb_controller.run()

        modbus_controller.run()

        if web_server and app_state.wifi_ok:
            web_server.run()
        
        gc_collect()

        if (utime.ticks_diff(utime.ticks_ms(), last_ticks_ms) > 250):
            for led in IO_pins["signal_leds"]:
                led.toggle()
        
            app_state.free_memory = gc_mem_free()

            measurement_controller.config = app_config.channel_config

            last_ticks_ms = utime.ticks_ms()

            if wdt:
                wdt.feed()

        if (utime.ticks_diff(utime.ticks_ms(), last_ticks_ms_2) > 10000):
            
            if app_config.other_config["debug_enabled"]:
                print(app_state.asdict())

            app_state.time_utc = utime.gmtime()

            last_ticks_ms_2 = utime.ticks_ms()

            app_state.save_to_file()
            app_config.save_to_file()

main()



