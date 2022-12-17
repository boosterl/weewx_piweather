# ⚠ DEPRECATION NOTICE ⚠

This driver is not in development anymore. And is not compatible with Python 3
and WeeWX >= 4. Please use an up-to-date driver like the [AlgerP572/WeatherPi](https://github.com/AlgerP572/WeatherPi)
driver.

# weewx_piweather
weewx driver for custom Raspberry Pi based weather stations

## Installation instructions

1. install the extension

```
wee_extension --install=weewx_piweather
```

2. select the driver

```
wee_config --reconfigure
```

3. restart WeeWX

```
sudo /etc/init.d/weewx stop
sudo /etc/init.d/weewx start
```
