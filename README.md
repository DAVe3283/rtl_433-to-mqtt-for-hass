# rtl_433 to MQTT gateway for Home Assistant

Vaguely based off [mverleun/RTL433-to-mqtt], but formatting the MQTT topics such that they will be used automatically by Home Assistant without any configuration needed on the Home Assistant side.

Only tested on Debian-based Linux, specifically vanilla Debian 10 (buster).

# Configuration

To use this tool, you need to create the configuration file `config.py`:

```py
# MQTT Configuration
MQTT_USER="user"
MQTT_PASS="password"
MQTT_HOST="host.fqdn or ip"
MQTT_TLS=False
MQTT_PORT=1883 # 8883 for TLS
MQTT_ROOT_CA="" # Leave blank to use system CA store, or provide the path to an internal CA or cert
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

# Prerequisites

## [rtl_433]

Some Linux distributions have this available as a package (usually `rtl-433`), but Debian 10 (buster) doesn't, so follow the instructions in [merbanan/rtl_433][rtl_433] to install it.

If it is not installed to the default location (`/usr/local/bin/rtl_433`), be sure to update `config.py` with the correct path.

## [paho-mqtt]

Use `pip` to install `paho-mqtt` for the current user.
(If you are going to run the service as a different user, install `paho-mqtt` for that user instead.)

```bash
sudo apt install python3-pip
pip3 install paho-mqtt
```

# Installation

The script will be configured to run as a service, so the machine can be rebooted without requiring any interaction to get the gateway working again.

It can run as a different user, but it is easier to just use your normal user account.
(Pull requests welcome to add instructions for running the service as a different user.)

First, edit the `rtl_433-to-mqtt.service` file.
* Update `User=your_username` with the correct username.
* Update `ExecStart=/usr/bin/python3 /home/your_username/rtl_433-to-mqtt-for-hass/rtl2mqtt.py` with the correct path to this repository

Now, add the service:

```bash
sudo cp rtl_433-to-mqtt.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rtl_433-to-mqtt.service
sudo service rtl_433-to-mqtt start
```

# Configuration changes

If any changes are made to `config.py`, the service will need restarted to apply them.

```bash
sudo service rtl_433-to-mqtt restart
```

[mverleun/RTL433-to-mqtt]: https://github.com/mverleun/RTL433-to-mqtt
[paho-mqtt]: https://pypi.org/project/paho-mqtt/
[rtl_433]: https://github.com/merbanan/rtl_433
