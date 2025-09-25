from umodbus.serial import ModbusRTU # type: ignore
from math import modf

import app
from device_config import __DeviceConfig


class ModbusController():
    def __init__(self, app_state: app.AppState, app_config: app.AppConfig, client: ModbusRTU) -> None:
        self.app_state = app_state
        self.app_config = app_config
        self.client = client

        self.register_definitions = {
            "IREGS": {
                "TEMPERATURE": {
                    "register": 1,
                    "len": 2 * __DeviceConfig.NUM_OF_CHANNELS,
                    "val": (-9999,) * 2 * __DeviceConfig.NUM_OF_CHANNELS
                },
                "NEGATIVE": {
                    "register": 100,
                    "len": 1,
                    "val": -34
                }
            }
        }

    def listen(self) -> bool:

        try:
            result = self.client.process()
            return result
        except Exception as e:
            return False

    def update_registers(self) -> None:
        
        vals = []

        for global_channel_id in range(__DeviceConfig.NUM_OF_CHANNELS):

            try:
                reading = self.app_state.measurement_results[global_channel_id]
                temp_C = reading["temperature_C"]

            except Exception:
                vals.append(-9999)
                vals.append(-9999)
                continue

            temp_C = round(temp_C, 4)

            fractional_part, whole_number  = modf(temp_C)

            first_register = int(whole_number)
            second_register = abs(int(fractional_part*1e+4))

            vals.append(first_register)
            vals.append(second_register)
            
        self.register_definitions["IREGS"]["TEMPERATURE"]["val"] = vals
        
        self.client.setup_registers(registers=self.register_definitions)


    def run(self) -> None:
        self.update_registers()

        is_successful = self.listen()










# self.register_definitions = {
#     "COILS": {
#         "EXAMPLE_COIL": {
#             "register": 123,
#             "len": 1,
#             "val": 1
#         }
#     },
#     "HREGS": {
#         "EXAMPLE_HREG": {
#             "register": 93,
#             "len": 1,
#             "val": 19
#         }
#     },
#     "ISTS": {
#         "EXAMPLE_ISTS": {
#             "register": 67,
#             "len": 1,
#             "val": 0
#         }
#     },
#     "IREGS": {
#         "EXAMPLE_IREG": {
#             "register": 1,
#             "len": 2,
#             "val": (1111, 22)
#         },
#         "NEGATIVE": {
#             "register": 3,
#             "len": 1,
#             "val": -34
#         }
#     }
# }