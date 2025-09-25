from machine import Pin, SPI, ADC

from measurements import controllers as ct, sensors as s, channels as ch, ADCs, queries as q
import app


def initialize_measurements(app_state: app.AppState, app_config: app.AppConfig) -> ct.MeasurementController:

    # Initialize SPI
    spi = SPI(
        0,
        baudrate=2000000,
        polarity=0,
        phase=1,
        bits=8,
        firstbit=SPI.MSB,
        sck=Pin(2),
        mosi=Pin(3),
        miso=Pin(4)
    )


    ads124S08 = ADCs.ADS124S08_ADC(
        ID=1,
        start_pin_id=6, 
        reset_pin_id=0,
        drdy_pin_id=1,
        channels=(
            ch.ADS124S08_Channel(ID_global=0, ID_adc_channel=0),
            ch.ADS124S08_Channel(ID_global=1, ID_adc_channel=1),
            ch.ADS124S08_Channel(ID_global=2, ID_adc_channel=2),
        ),
    )

    ads124S08.initialize(spi_object=spi, CS_pin_id=5)


    mc = ct.MeasurementController(
        ADC_objects=(
            ads124S08,
        ),
        config=app_config.channel_config,
        processor=ct.MeasurementProcessor(
            config=app_config.channel_config,
        )
    )


    return mc
