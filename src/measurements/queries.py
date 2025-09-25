from . import sensors

class MeasurementQuery():
    def __init__(self, global_channel_id: int, adc_id: int, adc_channel_id: int, probe: type[sensors.SensorProbe], num_of_readings: int, **kwargs) -> None:
        self._global_channel_id = global_channel_id
        self._adc_id = adc_id
        self._adc_channel_id = adc_channel_id
        self._probe = probe
        self._num_of_readings = num_of_readings
        self._extra_attrs = kwargs

    @property
    def global_channel_id(self):
        return self._global_channel_id

    @property
    def adc_id(self):
        return self._adc_id

    @property
    def adc_channel_id(self):
        return self._adc_channel_id
    
    @property
    def probe(self):
        return self._probe

    @property
    def num_of_readings(self):
        return self._num_of_readings
    
    @property
    def extra_attrs(self):
        return self._extra_attrs
    


class QueryResponseStatus():
    pass
class ADC_ACCEPT(QueryResponseStatus):
    pass
class ADC_WAITING_FOR_CONVERSION(QueryResponseStatus):
    pass
class ADC_DATA_READY(QueryResponseStatus):
    pass
class ADC_REFUSE(QueryResponseStatus):
    pass
class ADC_CONVERSION_TIMEOUT(QueryResponseStatus):
    pass

class MeasurementResponse():
    def __init__(self, query_in_progress: MeasurementQuery | None, status: type[QueryResponseStatus], readings: list | None=None, message: str|None=None) -> None:
        self._query_in_progress = query_in_progress
        self._status = status
        self._readings = readings
        self._message = message

    @property
    def query_in_progress(self):
        return self._query_in_progress

    @property
    def status(self):
        return self._status

    @property
    def readings(self):
        return self._readings
    
    @property
    def message(self):
        return self._message
