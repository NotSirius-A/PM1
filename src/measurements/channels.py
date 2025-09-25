from machine import Pin, SPI, ADC
import utime



class BaseChannel():

    def __init__(self, ID_global: int, ID_adc_channel: int, *args, **kwargs) -> None:
        self.ID_global = ID_global
        self.ID_adc_channel = ID_adc_channel

    def initialize(self):
        raise NotImplementedError

    def measure(self, num_of_times: int=1, *args, **kwargs) -> list[int]:
        readings = []
        
        for i in range(num_of_times):
            readings.append(self.perform_measurement(*args, **kwargs))

        return readings

    def perform_measurement(self) -> int:
        raise NotImplementedError


class OnBoardADC_Channel(BaseChannel):
    # TODO

    # def __init__(self, adc_pin_id:int, *args, **kwargs) -> None:
    #     super().__init__(*args, **kwargs)

    #     self.adc_pin_id = adc_pin_id
    #     self.adc_pin = Pin(self.adc_pin_id, mode=Pin.IN)
    #     self.adc = ADC(self.adc_pin)


    # def perform_measurement(self) -> int:
    #     reading = self.adc.read_u16()

    #     return reading
    pass



class SPI_ADC_BaseChannel(BaseChannel):
    def __init__(self, ID_global: int, ID_adc_channel: int, *args, **kwargs) -> None:
        super().__init__(ID_global, ID_adc_channel, *args, **kwargs)

        self.is_initialized: bool = False

    def initialize(self, spi_object: SPI, CS_pin_id: int, CS_active_state: bool=False):
        self.perform_initialization(spi_object, CS_pin_id, CS_active_state)
        self.is_initialized = True
    
    def perform_initialization(self, spi_object: SPI, CS_pin_id: int, CS_active_state: bool=False):
        
        self.spi: SPI = spi_object

        self.CS_pin_id = CS_pin_id
        self.CS: Pin = Pin(CS_pin_id, Pin.OUT)

        self.CS_ACTIVE: bool = CS_active_state

        self.CS.value(not self.CS_ACTIVE)

    def measure(self, num_of_times: int = 1, *args, **kwargs) -> list[int]:
        if not self.is_initialized:
            raise Exception("Channel not initialized, call `channel.initialize()`")
        
        return super().measure(num_of_times, *args, **kwargs)

class ADS1148_Channel(SPI_ADC_BaseChannel):
     
    def __init__(self, ID_global: int, ID_adc_channel: int, *args, **kwargs) -> None:
        super().__init__(ID_global, ID_adc_channel, *args, **kwargs)

    def perform_measurement(self) -> int:
        self.CS.value(self.CS_ACTIVE)
        utime.sleep_us(1)
        
        #RDATA
        msg = bytearray()
        msg.append(0x12)
        self.spi.write(msg)

        reading = self.spi.read(2)
        reading = int.from_bytes(reading, "big")
        
        self.CS.value(not self.CS_ACTIVE)
        utime.sleep_us(5)

        return reading


class ADS124S08_Channel(SPI_ADC_BaseChannel):
     
    def __init__(self, ID_global: int, ID_adc_channel: int, *args, **kwargs) -> None:
        super().__init__(ID_global, ID_adc_channel, *args, **kwargs)

    def perform_measurement(self) -> int:
        self.CS.value(self.CS_ACTIVE)
        utime.sleep_us(1)
        
        #RDATA
        msg = bytearray()
        msg.append(0x12)
        self.spi.write(msg)

        reading = self.spi.read(3)
        reading = int.from_bytes(reading, "big")
        
        self.CS.value(not self.CS_ACTIVE)
        utime.sleep_us(5)

        return reading

class MCP3204BaseChannel(SPI_ADC_BaseChannel):
     
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def perform_measurement(self) -> int:
        
        self.CS.value(self.CS_ACTIVE)
        utime.sleep_us(5) 

        msg = bytearray()
        msg.append(0x06)
        self.spi.write(msg)

        channel_code = {"CH1": 0x00, "CH2": 0x40, "CH3": 0x80, "CH4": 0xC0}
        reading = self.spi.read(2, channel_code["CH1"])
        reading = int.from_bytes(reading, "big")

        self.CS.value(not self.CS_ACTIVE)
        utime.sleep_us(5)

        return reading
        
