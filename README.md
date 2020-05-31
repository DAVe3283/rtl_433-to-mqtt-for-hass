# rtl_433 to MQTT gateway for Home Assistant

Vaguely based off [mverleun/RTL433-to-mqtt], but formatting the MQTT topics such that they will be used automatically by Home Assistant without any configuration needed on the Home Assistant side.

Only tested on Debian-based Linux, specifically vanilla Debian 10 (buster).

# Configuration

To use this tool, you need to create the configuration file `config.py`:

```py
# MQTT Credentials
MQTT_USER='user'
MQTT_PASS='password'
MQTT_HOST="host.fqdn or ip"
MQTT_PORT=1883
MQTT_TOPIC="homeassistant"
MQTT_QOS=0

# When run as a service, sometimes the script will start before DNS is available
# Instead of crashing, retry once a second this many times before giving up
CONNECTION_ATTEMPTS=60

LOG_FILENAME="/tmp/rtl2mqtt.log"
LOG_DEBUG=True

# Restrict publishing to sensors you expect/want
FILTER_IDS=["acurite-tower_6478", "and so on"]

RECONFIG_INTERVAL=10 # minutes
UPDATE_EXPIRATION=60 # seconds

rtl_433_cmd = "/usr/local/bin/rtl_433 -F json"
```

# Installation

## [rtl_433]

This project uses [merbanan/rtl_433][rtl_433], which will need installed on your system.
Some Linux distributions have this available as a package (usually `rtl-433`), but Debian 10 (buster) doesn't, so follow the instructions in that repo to install it.

If it is not installed to the default location (`/usr/local/bin/rtl_433`), be sure to update `config.py` with the correct path.

## rtl_433 to MQTT gateway for Home Assistant

You just run `rtl2mqtt.py` from this repo for now.

TODO / Coming Soon: directions to run it as a service!

[mverleun/RTL433-to-mqtt]: https://github.com/mverleun/RTL433-to-mqtt
[rtl_433]: https://github.com/merbanan/rtl_433
