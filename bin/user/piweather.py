#!/usr/bin/python
#
# Copyright 2020 Bram Oosterlynck
#
# weewx driver that reads values from various sensors connected to a Raspberry Pi
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
#
# See http://www.gnu.org/licenses/


# To use this driver, put this file in the weewx user directory, then make
# the following changes to weewx.conf:
#
# [Station]
#     station_type = PiWaether
# [PiWeather]
#     poll_interval = 2          # number of seconds
#     driver = user.piweather
#

from __future__ import with_statement
import syslog
import time

import weewx.drivers

# Imports for needed for the various versions
from gpiozero import Button
import time
import math
import bme280_sensor
import wind_direction_byo
#import statistics
import numpy
import ds18b20_therm

DRIVER_NAME = 'PiWeather'
DRIVER_VERSION = "0.1"

def logmsg(dst, msg):
    syslog.syslog(dst, 'piweather: %s' % msg)

def logdbg(msg):
    logmsg(syslog.LOG_DEBUG, msg)

def loginf(msg):
    logmsg(syslog.LOG_INFO, msg)

def logerr(msg):
    logmsg(syslog.LOG_ERR, msg)

def _get_as_float(d, s):
    v = None
    if s in d:
        try:
            v = float(d[s])
        except ValueError as e:
            logerr("cannot read value for '%s': %s" % (s, e))
    return v

def loader(config_dict, engine):
    return PiWeatherDriver(**config_dict[DRIVER_NAME])

class PiWeatherDriver(weewx.drivers.AbstractDevice):
    """weewx driver that reads data from different sensors connected to a Pi"""

    def __init__(self, **stn_dict):
        # the interval in which the measurements are taken, seconds
        self.interval = float(stn_dict.get('interval', 60))
        # the GPIO pin to which the anemometer is connected 
        self.anemometer_pin = int(stn_dict.get('anemometer_pin', 5))
        # the GPIO pin to which the rain bucket is connected 
        self.bucket_pin = int(stn_dict.get('bucket_pin', 6))
        # the interval in which the wind speed is calculated
        self.wind_interval = float(stn_dict.get('wind_interval', 5))
        # the radius of the anemometer
        self.radius_cm = float(stn_dict.get('radius_cm', 9.0))
        # the bucket size in millilitres
        self.bucket_size = float(stn_dict.get('bucket_size', 0.2794))
        # the class from which to fetch the measurements
        self.weather = Weather(self.anemometer_pin, self.bucket_pin, self.interval, self.wind_interval, self.radius_cm, self.bucket_size)


        loginf("interval is %s" % self.interval)
        loginf("wind_interval is %s" % self.wind_interval)
        loginf("anemometer_pin is %s" % self.anemometer_pin)
        loginf("bucket_pin is %s" % self.bucket_pin)
        loginf("bucket_size is %s" % self.bucket_size)
        loginf("radius_cm is %s" % self.radius_cm)

    def genLoopPackets(self):
        while True:
            data = self.weather.get_values()

            # map the data into a weewx loop packet
            _packet = {'dateTime': int(time.time() + 0.5),
                       'usUnits': weewx.METRICWX}
            for vname in data:
                _packet[vname] = data[vname]
                if data[vname] is not None:
                    _packet[vname] = _get_as_float(data, vname)

            yield _packet

    @property
    def hardware_name(self):
        return "PiWeather"


class Weather():
    def __init__(self, anemometer_pin, bucket_pin, interval, wind_interval, radius_cm, bucket_size):
        self.wind_speed_sensor = Button(anemometer_pin)
        self.bucket = Button(bucket_pin)

        self.wind_interval = wind_interval
        self.bucket_size = bucket_size
        self.interval = interval
        self.radius_cm = radius_cm

        self.tip_count = 0
        self.wind_count = 0

        self.wind_speed_sensor.when_pressed = self.spin
        self.bucket.when_pressed = self.tip

        self.ground_thermometer = ds18b20_therm.DS18B20()

    def spin(self):
        self.wind_count = self.wind_count + 1

    def calculate_speed(self, time_sec):
        time_hour = float(time_sec) / 3600
        circumference_cm = (2 * math.pi) * self.radius_cm
        rotations = self.wind_count / 2.0
        dist_km = circumference_cm * rotations / 100000
        speed_kmh = dist_km / time_hour
        speed = speed_kmh * 1.18
        speed_ms = speed / 3.6

        return speed_ms

    def reset_wind(self):
        self.wind_count = 0

    def tip(self):
        self.tip_count = self.tip_count + 1

    def reset_bucket(self):
        self.tip_count = 0

    def get_values(self):
        store_speeds = []
        store_directions = []
        start_time = time.time()
        try:
            while time.time() - start_time <= self.interval:
                wind_start_time = time.time()
                self.reset_wind()
                #time.sleep(wind_interval)
                while time.time() - wind_start_time <= self.wind_interval:
                    store_directions.append(wind_direction_byo.get_value())

                final_speed = self.calculate_speed(self.wind_interval)
                store_speeds.append(final_speed)

            wind_average = wind_direction_byo.get_average(store_directions)
        except ZeroDivisionError:
            logerr("there was a division by zero error calculating wind data")
            wind_average = None

        wind_gust = max(store_speeds)
        wind_speed = numpy.mean(store_speeds)
        rainfall = self.tip_count * self.bucket_size 
        self.reset_bucket()

        humidity, pressure, ambient_temperature = None, None, None
        try:
            humidity, pressure, ambient_temperature = bme280_sensor.read_all()
        except OSError:
            logerr("something went wrong communicating with bme280 sensor")
            bme280_sensor.reset_sensor()
        except IOError:
            logerr("something went wrong communicating with bme280 sensor")
            bme280_sensor.reset_sensor()

        ground_temperature = self.ground_thermometer.read_temp()

        data = {}

        data['outTemp'] = ambient_temperature
        data['outHumidity'] = humidity
        data['pressure'] = pressure
        data['soilTemp1'] = ground_temperature
        data['windSpeed'] = wind_speed
        data['windGust'] = wind_gust
        data['windDir'] = wind_average
        data['rain'] = rainfall
        
        return data        

# To test this driver, run it directly as follows:
#   PYTHONPATH=/home/weewx/bin python /home/weewx/bin/user/piweather.py
if __name__ == "__main__":
    import weeutil.weeutil
    driver = PiWeatherDriver()
    for packet in driver.genLoopPackets():
        print weeutil.weeutil.timestamp_to_string(packet['dateTime']), packet
