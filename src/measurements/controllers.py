import utime

from . import ADCs
from . import queries
from . import sensors


from device_config import __DeviceConfig


class MeasurementProcessor():
    def __init__(self, config: list[dict]) -> None:
        self.config = config

        self.storage: list[dict]
        self.storage = [{"readings":[], "processed": {}} for i in range(len(self.config))]

    def calculate_channel(self, readings: list[int], global_channel_id: int) -> dict:
        ch_config = self.config[global_channel_id]

        reading_avg = sum(readings)/len(readings)
        
        R = __DeviceConfig.calculate_resistance_ADS124S08(
            reading_avg, 
            ch_config["probe"],
            ch_config["_calibration"],
        )
        
        T_c = ch_config["probe"].calculate_temperature_celsius(R)
        T_k = ch_config["probe"].celsius_to_kelvin(T_c)
        T_f = ch_config["probe"].celsius_to_fahrenheit(T_c)

        return {
            "_name": ch_config["_name"],
            "verbose_name": ch_config["verbose_name"],
            "probe": ch_config["probe"],
            "avg_reading": reading_avg, "resistance_Om": R, 
            "temperature_C": T_c, "temperature_K": T_k, "temperature_F": T_f
        }

            
    def process_measurement(self, measurement_response: queries.MeasurementResponse) -> None:
        mr = measurement_response
        assert mr.query_in_progress is not None and mr.readings is not None

        global_channel_id = mr.query_in_progress.global_channel_id

        self.store_measurements(mr.readings, global_channel_id)

        all_readings = self.get_readings(global_channel_id)

        processed_values = self.calculate_channel(all_readings, global_channel_id)

        self.storage[global_channel_id]["processed"] = processed_values

       


    def store_measurements(self, readings: list[int], global_channel_id: int) -> None:
        gch_id = global_channel_id

        for reading in readings:
            self.storage[gch_id]["readings"].append(reading)

        num_of_readings_to_store = self.config[gch_id]["num_of_readings_to_store"]
        
        # keep a list of readings up to date, remove oldest sample when new one is present
        if len(self.storage[gch_id]["readings"]) > num_of_readings_to_store:
            self.storage[gch_id]["readings"].pop(0)

    def get_readings(self, global_channel_id: int) -> list[int]:
        return self.storage[global_channel_id]["readings"]


class MeasurementController():

    def __init__(self, config: list[dict], ADC_objects: tuple[ADCs.SimpleADC], processor: MeasurementProcessor, *args, **kwargs) -> None:
        
        for adc_object in ADC_objects:
            if not isinstance(adc_object, ADCs.SimpleADC):
                raise TypeError("`ADCs` must be of `SimpleADC` type")
            
        self.config = config
        self.ADCs = ADC_objects
        self.processor = processor

        self.last_measurement_times_ms = [0]*len(self.config)

        self.current_results: list = []

        self.channel_counter = 0
        self.last_measured_channel_id = None
        
    def query_measurement(self, query: queries.MeasurementQuery) -> queries.MeasurementResponse:
        adc = self.ADCs[query.adc_id]

        return adc.measure(query)

        
    def run(self):
        
        self.handle_channel(self.channel_counter)

        self.channel_counter += 1
        self.channel_counter = self.channel_counter % __DeviceConfig.NUM_OF_CHANNELS


    def handle_channel(self, global_channel_id):

        channel = self.config[global_channel_id]

        if (not channel["is_enabled"]):
            return

        if global_channel_id == self.last_measured_channel_id and __DeviceConfig.NUM_OF_CHANNELS:
            return

        if (utime.ticks_diff(utime.ticks_ms(), self.last_measurement_times_ms[global_channel_id]) < channel["time_between_measurements_ms"]):
            # Skip channel if not enough time has passed
            return

        # TODO implement dynamic adc selection
        adc_id = 0
        adc_channel_id = global_channel_id

        query = queries.MeasurementQuery(
            global_channel_id=global_channel_id,
            adc_id=adc_id,
            adc_channel_id=adc_channel_id,
            probe=channel["probe"],
            num_of_readings=channel["_num_readings_per_measurement"],
            **channel["_extra_attrs"],
        )
        
        response = self.query_measurement(query)
        

        if response.status == queries.ADC_DATA_READY:
            response_channel_id = response.query_in_progress.global_channel_id # type: ignore

            self.processor.process_measurement(response)
            self.current_results = [data["processed"] for data in self.processor.storage]
            # if self.current_results[response_channel_id]["_name"] == "CH0":
            #     print(self.current_results[response_channel_id]["resistance_Om"])
            self.last_measurement_times_ms[response_channel_id] = utime.ticks_ms()
            self.last_measured_channel_id = response_channel_id

    def get_current_results(self) -> list:
        return self.current_results

