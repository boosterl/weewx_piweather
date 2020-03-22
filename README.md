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
