# installer for the piweather driver
# Copyright 2020 Bram Oosterlynck

from weecfg.extension import ExtensionInstaller


def loader():
    return PiWeatherInstaller()


class PiWeatherInstaller(ExtensionInstaller):
    def __init__(self):
        super(PiWeatherInstaller, self).__init__(
            version="0.1",
            name='piweather',
            description='Homebrew Raspberry Pi with sensers connected to it, driver for weewx.',
            author="Bram Oosterlynck",
            author_email="bram.oosterlynck@gmail.com",
            config={
                'Station': {
                    'station_type': 'PiWeather'},
                'PiWeather': {
                    'interval': '60',
                    'wind_interval': '5',
                    'anemometer_pin': '5',
                    'bucket_pin': '6',
                    'bucket_size': '0.2794',
                    'radius_cm': '9.0',
                    'driver': 'user.piweather'}},
                    files=[('bin/user', [
                        'bin/user/piweather.py',
                        'bin/user/bme280_sensor.py',
                        'bin/user/wind_direction_byo.py',
                        'bin/user/ds18b20_therm.py',
                    ])]
        )
