import bme280
import smbus2
from time import sleep
import syslog

port = 1
address = 0x77 # Adafruit BME280 address. Other BME280s may be different
bus = smbus2.SMBus(port)

bme280_register_softreset = 0xE0
bme280_data_softreset = 0xB6

try:
    bme280.load_calibration_params(bus,address)
except IOError:
    syslog.syslog(syslog.LOG_ERR, 'piweather: error calibrating bme280') 

def read_all():
    bme280_data = bme280.sample(bus,address)
    humidity  = bme280_data.humidity
    pressure  = bme280_data.pressure
    ambient_temperature = bme280_data.temperature
    return humidity, pressure, ambient_temperature

def reset_sensor():
    try:
        bus.write_byte_data(address, bme280_register_softreset, bme280_data_softreset)
    except IOError:
        syslog.syslog(syslog.LOG_ERR, 'piweather: error resetting bme280') 
