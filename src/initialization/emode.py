import app
from communications import usb_

def run_mode(app_state: app.AppState, app_config: app.AppConfig) -> None:

    usb_controller = usb_.USBController(app_state, app_config)

    app_state.is_initialized = True
    while True:
        usb_controller.run()