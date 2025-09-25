from machine import Pin, SPI, ADC
import utime

from measurements import channels as ch 
from measurements import sensors as s
from measurements import queries as q



class SimpleADC:

    def __init__(self, ID: int, channels: tuple[ch.BaseChannel, ...], *args, **kwargs) -> None:
    
        self.ID = ID
        self.channels = channels

        self.is_waiting_for_conversion: bool | None = None

        self.query_in_progress: q.MeasurementQuery | None = None


    def measure(self, query: q.MeasurementQuery) -> q.MeasurementResponse:
        raise NotImplementedError
            

class OnBoardADC(SimpleADC):   
    # TODO
    # def calculate_voltage_from_reading(self, reading) -> float:
    #     # 2^16 = 65536, ADC returns 16 bits
    #     return (self.VRef / 65535) * reading

    # def get_voltage_now(self) -> float:
    #     reading = self.perform_measurement()
    #     return self.calculate_voltage_from_reading(reading)

    # def get_voltage_avg(self) -> float:
    #     # voltage should be converted to float only after avg to reduce memory usage
    #     avg_reading = self.get_avg_reading()
    #     return self.calculate_voltage_from_reading(avg_reading)
    pass

    


class SPI_ADC(SimpleADC):

    def __init__(self, ID: int, channels: tuple[ch.SPI_ADC_BaseChannel, ...], *args, **kwargs) -> None:
        super().__init__(ID, channels, *args, **kwargs)

        self.channels: tuple[ch.SPI_ADC_BaseChannel, ...]
        self.is_initialized: bool = False

    def initialize(self, spi_object: SPI, CS_pin_id: int, CS_active_state: bool=False) -> None:
        self.spi: SPI = spi_object

        self.CS_pin_id = CS_pin_id
        self.CS: Pin = Pin(self.CS_pin_id, Pin.OUT)

        self.CS_ACTIVE: bool = CS_active_state

        self.CS.value(not self.CS_ACTIVE)

        self.perform_initialization()
        
        self.is_initialized = True
    
    def perform_initialization(self) -> None:
        raise NotImplementedError       

    
    def measure(self, query: q.MeasurementQuery) -> q.MeasurementResponse:
        if not self.is_initialized:
                raise Exception("ADC not initialized, call `ADC.initialize()`")
        
        return super().measure(query)

class ADS1148_ADC(SPI_ADC):


    DEFAULT_CONFIGURATION = {
        "MUX0":     0b00001010, # 00 aaa bbb, 00 001 010, AIN1 positive AIN2 negative input
        "VBIAS":    0b00000000, # 0x00 for no vbias
        "MUX1":     0b00100000, # internal oscilator, vref and REFP0 REFPN0 enabled
        "SYS0":     0b00100010, # 0 aaa bbbb, 0 reserved, a is PGA gain 010 is 4 (gain in powers of 2), b is SPS 0010 = 20
        "IDAC0":    0b00000110, # 0000 a bbb, a is data ready mode 0 for disabled drdy, bbb is IEXC value 110 = 1mA
        "IDAC1":    0b00000011, # aaaa bbbb, 0000 0011, IEXC1 to AIN0, IEXC2 to AIN3
        "!IDAC1":   0b00110000, # IEXC are inverted for accuracy
    }

    configuration2 = {
        "MUX0":     0b00101110,
        "IDAC1":    0b01000111,
        "!IDAC1":   0b01110100,
    }


    def __init__(self, ID: int, channels: tuple[ch.ADS1148_Channel, ...], start_pin_id: int, reset_pin_id: int, *args, **kwargs) -> None:
        super().__init__(ID, channels, *args, **kwargs)

        self.channels: tuple[ch.ADS1148_Channel, ...]

        self.START = Pin(start_pin_id, Pin.OUT)
        self.RESET = Pin(reset_pin_id, Pin.OUT) 
        self.DRDY_pin = Pin(20, Pin.IN)     
        

    def perform_initialization(self) -> None:

        self.is_waiting_for_conversion = False

        self.START.high()

        utime.sleep_ms(1)

        self.RESET.low()
        utime.sleep_ms(10)
        self.RESET.high()


        self.CS.value(self.CS_ACTIVE)
        utime.sleep_us(1)

        # RESET
        msg = bytearray()
        msg.append(0x06)
        self.spi.write(msg)

        utime.sleep_ms(10)

        # SDATAC

        msg = bytearray()
        msg.append(0x16)
        self.spi.write(msg)

        utime.sleep_ms(5)
        
        # WREG configuration
        self.perform_configuration(configuration=self.DEFAULT_CONFIGURATION)

        self.CS.value(self.CS_ACTIVE)
        utime.sleep_us(1)

        # SYNC    
        msg = bytearray()
        msg.append(0x04)
        self.spi.write(msg)

        utime.sleep_ms(1)

        self.CS.value(not self.CS_ACTIVE)
        utime.sleep_us(5)


        for channel in self.channels:
            channel.initialize(self.spi, self.CS_pin_id, self.CS_ACTIVE)

    def perform_configuration(self, configuration: dict, chopped: bool=False):
        c = configuration

        self.CS.value(self.CS_ACTIVE)
        utime.sleep_us(1)

        #WREG START
        msg = bytearray()
        msg.append(0x40)
        msg.append(0x03)

        #MUX0
        msg.append(c["MUX0"]) 
        #VBIAS
        msg.append(c["VBIAS"])
        #MUX1
        msg.append(c["MUX1"])
        #SYS0
        msg.append(c["SYS0"])
        self.spi.write(msg)

        utime.sleep_ms(5)

        #WREG START

        msg = bytearray()
        msg.append(0x4a)
        msg.append(0x01)

        #IDAC0
        msg.append(c["IDAC0"]) 
        
        #IDAC1
        # chopped means that IEXC are reversed
        # reversing half of the measurements improves accuracy
        if chopped:
            msg.append(c["!IDAC1"])
        else:
            msg.append(c["IDAC1"])

        self.spi.write(msg)
        #WREG END

       # SYNC    
        msg = bytearray()
        msg.append(0x04)
        self.spi.write(msg)

        self.CS.value(not self.CS_ACTIVE)
        utime.sleep_us(5)
        

    def measure_channel(self, channel_id: int) -> list[int]:
        channel = self.channels[channel_id]

        reading = channel.measure() 
        return reading
        
    def configure(self, channel_id: int, chopped: bool=False) -> None:
            
        # TODO make better
        c = {}
        c.update(self.DEFAULT_CONFIGURATION)

        if channel_id == 0:
            pass
        elif channel_id == 1:
            c.update(self.configuration2)

        self.perform_configuration(configuration=c, chopped=chopped)



    def measure(self, query: q.MeasurementQuery) -> q.MeasurementResponse:
        
        perform_chopping = bool(query.extra_attrs.get("chopped"))

        if query.num_of_readings > 1:
            return q.MeasurementResponse(
                query_in_progress=None,
                status=q.ADC_REFUSE,
                message="ADS1148_ADC currently does not support taking multiple readings in bulk",
            )


        if (not self.is_waiting_for_conversion):
            self.query_in_progress = query
            self.is_waiting_for_conversion = True

            self.configure(query.adc_channel_id, chopped=perform_chopping)

            return q.MeasurementResponse(
                query_in_progress=self.query_in_progress,
                status=q.ADC_ACCEPT,
            )

        assert self.query_in_progress is not None

        if (self.DRDY_pin.value() == 0):
            readings = self.measure_channel(self.query_in_progress.adc_channel_id)

            response = q.MeasurementResponse(
                query_in_progress=self.query_in_progress,
                status=q.ADC_DATA_READY,
                readings=readings,
            )
            self.is_waiting_for_conversion = False
            self.query_in_progress = None

            return response
        

        return q.MeasurementResponse(
            query_in_progress=self.query_in_progress,
            status=q.ADC_WAITING_FOR_CONVERSION,
        )

class MCP3204_ADC(SPI_ADC):
    pass



class ADS124S08_ADC(SPI_ADC):


    DEFAULT_CONFIGURATION = {
        "INPMUX":   0b00010010, #12 AIN1 AIN2 inputs
        "PGA":      0b00001010,
        "DATARATE": 0b10110010, #chop enabled 10SPS 
        "REF": 0b00000010,  
        "IDACMAG": 0b00000101, #05 1000uA
        "IDACMUX": 0b00000011, #03 
        "VBIAS": 0b00000000, #00
        "SYS": 0b00010000, #10
        # "GPIODAT": 0b00000000, #00
        # "GPI0CON": 0b00000000, #00  q     
    }

    CH0_INPUTS_CONFIGURATION = {
        "INPMUX": 0x12, # AIN1 AIN2
        "IDACMUX": 0x03, # AIN0 AIN3
    }
    CH1_INPUTS_CONFIGURATION = {
        "INPMUX": 0x56, # AIN5 AIN6
        "IDACMUX": 0x47, # AIN4 AIN7
    }
    CH2_INPUTS_CONFIGURATION = {
        "INPMUX": 0x9a, # AIN9 AIN10
        "IDACMUX": 0x8b, # AIN8 AIN11
    }

    PT100_CONFIGURATION = {
        "PGA":      0b00001100, #0b 16
        "IDACMAG": 0b00000101, #05 500uA
    }
    PT1000_CONFIGURATION = {
        "PGA":      0b00001001, #0b 2
        "IDACMAG": 0b00000100 #250uA
    }

    CONVERSION_TIMEOUT_MS = 275
    conversion_timeout_start_ms: int = 0


    def __init__(self, ID: int, channels: tuple[ch.ADS124S08_Channel, ...], start_pin_id: int, reset_pin_id: int, drdy_pin_id: int, *args, **kwargs) -> None:
        super().__init__(ID, channels, *args, **kwargs)

        self.channels: tuple[ch.ADS124S08_Channel, ...]

        self.START = Pin(start_pin_id, Pin.OUT)
        self.RESET = Pin(reset_pin_id, Pin.OUT) 
        self.DRDY_pin = Pin(drdy_pin_id, Pin.IN)     
        

    def perform_initialization(self) -> None:

        self.is_waiting_for_conversion = False

        self.START.low()

        utime.sleep_ms(1)

        self.RESET.low()
        utime.sleep_ms(10)
        self.RESET.high()


        self.CS.value(self.CS_ACTIVE)
        utime.sleep_us(1)

        # RESET
        msg = bytearray()
        msg.append(0x06)
        self.spi.write(msg)

        utime.sleep_ms(10)

        # WREG configuration
        self.perform_configuration(configuration=self.DEFAULT_CONFIGURATION)

        self.CS.value(self.CS_ACTIVE)
        utime.sleep_us(1)

        # # START    
        # msg = bytearray()
        # msg.append(0x08)
        # self.spi.write(msg)

        utime.sleep_ms(1)

        self.CS.value(not self.CS_ACTIVE)
        utime.sleep_us(5)


        for channel in self.channels:
            channel.initialize(self.spi, self.CS_pin_id, self.CS_ACTIVE)

    def perform_configuration(self, configuration: dict):
        c = configuration

        self.CS.value(self.CS_ACTIVE)
        utime.sleep_us(1)

        #WREG START
        msg = bytearray()
        msg.append(0b01000010)
        msg.append(0x07)

        msg.append(c["INPMUX"])
        msg.append(c["PGA"]) 
        msg.append(c["DATARATE"]) 
        msg.append(c["REF"]) 
        msg.append(c["IDACMAG"])
        msg.append(c["IDACMUX"])
        msg.append(c["VBIAS"])
        msg.append(c["SYS"])

        self.spi.write(msg)

        self.CS.value(not self.CS_ACTIVE)
        utime.sleep_us(50)

    def start_conversion(self) -> None:
        self.CS.value(self.CS_ACTIVE)
        utime.sleep_us(1)

        # START   
        msg = bytearray()
        msg.append(0x08)
        self.spi.write(msg)

        self.CS.value(not self.CS_ACTIVE)
        utime.sleep_us(5)

    def measure_channel(self, channel_id: int) -> list[int]:
        channel = self.channels[channel_id]

        reading = channel.measure() 
        return reading
        
    def configure(self, query: q.MeasurementQuery) -> None:

        c = {}
        c.update(self.DEFAULT_CONFIGURATION)

        channel_id = query.adc_channel_id
        probe = query.probe

        if channel_id == 0:
            c.update(self.CH0_INPUTS_CONFIGURATION)
        elif channel_id == 1:
            c.update(self.CH1_INPUTS_CONFIGURATION)
        elif channel_id == 2: 
            c.update(self.CH2_INPUTS_CONFIGURATION)
        else:
            raise Exception(f"Invalid channel id = `{channel_id}`")

        if probe == s.SensorPt100:
            c.update(self.PT100_CONFIGURATION)
        elif probe == s.SensorPt1000:
            c.update(self.PT1000_CONFIGURATION)

        self.perform_configuration(configuration=c)



    def measure(self, query: q.MeasurementQuery) -> q.MeasurementResponse:

        if query.num_of_readings > 1:
            return q.MeasurementResponse(
                query_in_progress=None,
                status=q.ADC_REFUSE,
                message="ADS124S08_ADC currently does not support taking multiple readings in bulk",
            )


        if (not self.query_in_progress):
            self.query_in_progress = query

            self.configure(query)
            self.conversion_timeout_start_ms = utime.ticks_ms()

            return q.MeasurementResponse(
                query_in_progress=self.query_in_progress,
                status=q.ADC_ACCEPT,
            )

        assert self.query_in_progress is not None

        if (utime.ticks_diff(utime.ticks_ms(), self.conversion_timeout_start_ms) > self.CONVERSION_TIMEOUT_MS):
            if not self.is_waiting_for_conversion:
                self.start_conversion()
                self.is_waiting_for_conversion = True
                # if self.query_in_progress.adc_channel_id == 0:
                #     print(self.CONVERSION_TIMEOUT_MS, end=",")
                #     self.CONVERSION_TIMEOUT_MS += 1
                return q.MeasurementResponse(
                query_in_progress=self.query_in_progress,
                status=q.ADC_CONVERSION_TIMEOUT,
                )
            
        if (self.DRDY_pin.value() == 0):
            readings = self.measure_channel(self.query_in_progress.adc_channel_id)

            response = q.MeasurementResponse(
                query_in_progress=self.query_in_progress,
                status=q.ADC_DATA_READY,
                readings=readings,
            )
            self.is_waiting_for_conversion = False
            self.query_in_progress = None

            return response
        

        return q.MeasurementResponse(
            query_in_progress=self.query_in_progress,
            status=q.ADC_WAITING_FOR_CONVERSION,
        )
