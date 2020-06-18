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
FILTER_IDS = [
    "acurite-tower_6478_a",
    "and so on",
]

RECONFIG_INTERVAL=10 # minutes
UPDATE_EXPIRATION=60 # seconds

rtl_433_cmd = "/usr/local/bin/rtl_433 -F json"
```

## FILTER_IDS

To find values to use for `FILTER_IDS`, run the `rtl_433` executable, and watch for the data to come through on the sensor(s) you want.

The ID string is `<model>_<id>_<channel>` with everything in lowercase. Leave off the last underscore and channel for sensors with no channel. For example:

```
time      : 2020-06-17 19:26:25
model     : Acurite-Tower id        : 6478
channel   : A            battery_ok: 1             Temperature: 19.7 C       Humidity  : 45            Integrity : CHECKSUM
```

This sensor would be enabled with the string `"acurite-tower_6478_a"`.

## MQTT with TLS

It is recommended to use MQTT over TLS where possible, especially over the public Internet. To secure the connection, the server's certificate needs to be verified by the client.

* If your MQTT server has a commercial certificate from a recognized Certificate Authority (CA), no special client configuration is necessary!
* If your server uses a self-signed certificate, you will need a copy of the server's public cert, and update `MQTT_ROOT_CA` in `config.py` with the path to the public cert.
* If you have an internal CA, you can set `MQTT_ROOT_CA`, but the recommended method is to add the root CA to the operating system's CA store.

### Add a root CA to the OS CA store

For example, in Debian 10 (stretch):

```bash
# Create directory for your domain
sudo mkdir /usr/local/share/ca-certificates/your.domain

# Get root CA from a webserver. Could also rsync it over, etc.
sudo wget -P /usr/local/share/ca-certificates/your.domain http://www.your.domain/pki/root.crt
# Repeat for any other/intermediate certs to trust (not usually needed)

# Refresh the OS CA store
sudo update-ca-certificates
```

# Prerequisites

## Python 3 & [pip]

Virtually every Linux distribution has Python 3, either pre-installed, or as a package.
We also need [pip] to support a later dependency.

```bash
sudo apt install python3 python3-pip
```

## [rtl_433]

Some Linux distributions have this available as a package (usually `rtl-433`), but Debian 10 (buster) doesn't, so follow the instructions in [merbanan/rtl_433][rtl_433] to install it.

If it is not installed to the default location, be sure to update `rtl_433_cmd` in `config.py` with the correct path.

Older versions of this tool had different names in the JSON output.
Known working versions (launch launch with `-h` to view version information):
* `rtl_433 version 20.02-61-gf82c025 branch master at 202005272108`

## [paho-mqtt]

Use `pip` to install `paho-mqtt` for the current user.
(If you are going to run the service as a different user, install `paho-mqtt` for that user instead.)

```bash
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
[pip]: https://pip.pypa.io/en/stable/
[rtl_433]: https://github.com/merbanan/rtl_433
