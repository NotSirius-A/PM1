import select
import sys
import machine


from app import AppState, AppConfig
from device_config import __DeviceConfig
import measurements.sensors


class Command():
    def __init__(self, type: str, arg1: str, arg2: str, val: str) -> None:
        self._type = type
        self._arg1 = arg1
        self._arg2 = arg2
        self._val = val 

    @property
    def type(self):
        return self._type
    @property
    def arg1(self):
        return self._arg1
    @property
    def arg2(self):
        return self._arg2
    @property
    def val(self):
        return self._val




class USBController():
    LISTEN_CHAR_LIMIT = 255

    COMMAND_DELIMITER: str = ';'
    RESPONSE_DELIMITER: str = '_@_'
    
    VALID_COMMAND_TYPES: set[str] = {"WC", "RS", "RM", "RC", "RT"}
    CHANNEL_SPECIFIERS = __DeviceConfig.USB_CHANNEL_SPECIFIERS
    VALID_CHANNEL_SPECIFIERS: set = set(CHANNEL_SPECIFIERS.keys())
    VALID_COMMAND_ARG1: set[str] = {"", "MB", "WF", "OT"}.union(VALID_CHANNEL_SPECIFIERS)
    VALID_COMMAND_ARG2: set[str] = {"", 
                               "VN", "EN", "PB", "NM", "TM", "NS",
                               "AD", "BR", "DB", "SB", "PR",
                               "EN", "SS", "PW",
                               "DB"
    }


    def __init__(self, app_state: AppState, app_config: AppConfig) -> None:

        self.poll_obj = select.poll()
        self.poll_obj.register(sys.stdin, select.POLLIN)

        self.app_state = app_state
        self.app_config = app_config

    def run(self) -> bool:
        msg = self.listen()

        if not msg:
            return False

        is_successful, response = self.process_message(msg)

        print(response)

        return is_successful

    def process_message(self, msg: str) -> tuple[bool, str]:
        command, error = self.parse_command(msg)

        if command and not error:
            is_successful, response = self.execute_command(command)
        else:
            is_successful = False
            response = error

        response = self.get_response(msg, is_successful, response)

        return is_successful, response

    def listen(self, timeout_ms: int=1) -> str|None:

        poll_results = self.poll_obj.poll(timeout_ms) 
        if poll_results:
            data = sys.stdin.readline(self.LISTEN_CHAR_LIMIT).strip()
            return data


    def parse_command(self, command_str: str) -> tuple[Command|None, str|None]:
        
        command_list = command_str.split(self.COMMAND_DELIMITER)

        if self.RESPONSE_DELIMITER in command_str:
            return (None, f"Illegal character used")

        if len(command_list) != 4:
            return (None, f"Wrong format, expected 4 words separated by '{self.COMMAND_DELIMITER}'")      

        command = Command(
            type=command_list[0],
            arg1=command_list[1],
            arg2=command_list[2],
            val=command_list[3],
        )
        
        is_valid_format, error = self.is_valid_command_format(command)

        if is_valid_format:
            return (command, None)
        else:
            return (None, error) 

    def is_valid_command_format(self, command: Command) -> tuple[bool, str|None]:
        valid = False
        error = None

        if command.type not in self.VALID_COMMAND_TYPES:
            error = f"Invalid command type `{command.type}`, not in `{self.VALID_COMMAND_TYPES}`"
        elif command.arg1 not in self.VALID_COMMAND_ARG1:
            error = f"Invalid command arg1 `{command.arg1}`, not in `{self.VALID_COMMAND_ARG1}`"
        elif command.arg2 not in self.VALID_COMMAND_ARG2:
            error = f"Invalid command arg2 `{command.arg2}`, not in `{self.VALID_COMMAND_ARG2}`"
        else:
            valid = True
    
        return (valid, error)

    def execute_command(self, command: Command) -> tuple[bool, str|None]:
        
        if command.type == "WC":
            return self.execute_WC(command)

        elif command.type == "RC":
            return (True, str(self.app_config.asjson()))

        elif command.type == "RS":
            return (True, str(self.app_state.asjson()))

        elif command.type == "RM":
            return (True, str(self.app_state.measurements_asjson()))

        elif command.type == "RT":
            machine.reset()

        raise NotImplementedError("Provided type `{command.type}` is not implemented, this error signifies that command was incorrectly validated")
    
    def execute_WC(self, command: Command) -> tuple[bool, str|None]:
        assert command.type == "WC"
        error = None

        a = self.app_config

        # This part may need to be rewritten in the future
        # Too much nesting, looks confusing
        if command.arg1 in self.VALID_CHANNEL_SPECIFIERS:
            global_channel_id = self.CHANNEL_SPECIFIERS[command.arg1]
            id = global_channel_id

            if command.arg2 == "VN":
                a.channel_config[id]["verbose_name"] = command.val
                
            elif command.arg2 == "EN":
                if command.val in ["True", "true", "1"]:
                    a.channel_config[id]["is_enabled"] = True
                elif command.val in ["False", "false", "0"]:
                    a.channel_config[id]["is_enabled"] = False
                else:
                    error = f"Value must either True/true/1 or False/false/0, not `{command.val}`"

            elif command.arg2 == "PB":
                if command.val in ["Pt100", "pt100"] and measurements.sensors.SensorPt100 in __DeviceConfig.ALLOWED_PROBES_TYPES:
                    a.channel_config[id]["probe"] = measurements.sensors.SensorPt100
                elif command.val in ["Pt1000", "pt1000"] and measurements.sensors.SensorPt1000 in __DeviceConfig.ALLOWED_PROBES_TYPES:
                    a.channel_config[id]["probe"] = measurements.sensors.SensorPt1000
                elif command.val in ["NTC", "ntc"] and measurements.sensors.SensorNTC in __DeviceConfig.ALLOWED_PROBES_TYPES:
                    a.channel_config[id]["probe"] = measurements.sensors.SensorNTC
                else:
                    error = f"Invalid probe type `{command.val}`"


            elif command.arg2 == "TM":
                try:
                    time = int(command.val)

                    if time >= 0:
                        a.channel_config[global_channel_id]["time_between_measurements_ms"] = time
                    else:
                        error = f"Time between measurements must be non-negative, not {time}" 
                    
                except ValueError:
                    error = f"Time between measurements must be an integer, not {command.val}" 


            elif command.arg2 == "NS":
                try:
                    num = int(command.val)

                    if num > 0 and num < 2049:
                        a.channel_config[global_channel_id]["num_of_readings_to_store"] = num
                    else:
                        error = f"Number of readings to store must be positive and lower than 2049, not {num}" 
                    
                except ValueError:
                    error = f"Number of readings to store must be an integer, not {command.val}" 

            else:
                error = f"Incorrect register address: {command.arg1}, {command.arg2}"


        elif command.arg1 == "MB":
            if command.arg2 == "AD":
                try:
                    num = int(command.val)

                    if num >= 1 and num <= 247:
                        a.modbus_config["addr"] = num
                    else:
                        error = f"Modbus slave address must be in range 1-247, not {num}" 
                except ValueError:
                    error = f"Modbus slave address must be an integer, not {command.val}" 


            elif command.arg2 == "BR":
                try:
                    num = int(command.val)

                    if num >= __DeviceConfig.MODBUS_MIN_BAUDRATE and num <= __DeviceConfig.MODBUS_MAX_BAUDRATE:
                        a.modbus_config["baudrate"] = num
                    else:
                        error = f"Modbus baud rate must be in range {__DeviceConfig.MODBUS_MIN_BAUDRATE}-{__DeviceConfig.MODBUS_MAX_BAUDRATE}, not {num}" 
                except ValueError:
                    error = f"Modbus slave address must be an integer, not {command.val}" 

            elif command.arg2 == "DB":
                try:
                    num = int(command.val)

                    if num >= 7 and num <= 9:
                        a.modbus_config["data_bits"] = num
                    else:
                        error = f"Modbus data bits must be in range 7-9, not {num}" 
                except ValueError:
                    error = f"Modbus data bits must be an integer, not {command.val}" 

            elif command.arg2 == "SB":
                try:
                    num = int(command.val)

                    if num == 1 or num == 2:
                        a.modbus_config["stop_bits"] = num
                    else:
                        error = f"Modbus stop bits must be either 1 or 2, not {num}" 
                except ValueError:
                    error = f"Modbus stop bits must be an integer, not {command.val}" 

            elif command.arg2 == "PR":

                try:
                    num = int(command.val)
                except ValueError:
                    num = None

                if num == 0 or num == 1:
                    a.modbus_config["parity"] = num
                elif command.val == "none" or command.val == "None":
                    a.modbus_config["parity"] = None
                else:
                    error = f"Modbus parity must be either 0 (even) or 1 (odd) or none/None, not {num}" 

            else:
                error = f"Incorrect register address: {command.arg1}, {command.arg2}"


        elif command.arg1 == "WF":
            if command.arg2 == "SS":
                a.wifi_config["ssid"] = command.val
            
            elif command.arg2 == "PW":
                a.wifi_config["password"] = command.val

            elif command.arg2 == "EN":
                if command.val in ["True", "true", "1"]:
                    a.wifi_config["wifi_enabled"] = True
                elif command.val in ["False", "false", "0"]:
                    a.wifi_config["wifi_enabled"] = False
                else:
                    error = f"Value must either True/true/1 or False/false/0, not `{command.val}`"

            else:
                error = f"Incorrect register address: {command.arg1}, {command.arg2}"


        elif command.arg1 == "OT":
            if command.arg2 == "DB":
                if command.val in ["True", "true", "1"]:
                    a.other_config["debug_enabled"] = True
                elif command.val in ["False", "false", "0"]:
                    a.other_config["debug_enabled"] = False
                else:
                    error = f"Value must either True/true/1 or False/false/0, not `{command.val}`"

            else:
                error = f"Incorrect register address: {command.arg1}, {command.arg2}"

        if error:
            return (False, error)
        else:
            self.app_config.save_to_file()
            return (True, "Register updated")

    def get_response(self, command_str: str, is_successful: bool, payload: str|None) -> str:
        
        response = "{status_code}_@_{command_str}_@_{payload}"

        if is_successful:
            status_code = "OK"
        else:
            status_code = "ER"

        response = response.format(status_code=status_code, command_str=command_str, payload=payload)

        return response