#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Original script:
#  https://github.com/mverleun/RTL433-to-mqtt
# Which was based on:
#  http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/

import subprocess
import sys
import time
import paho.mqtt.client as mqtt
import os
import json

import logging
import logging.handlers
import argparse

from config import *
#from datetime import datetime, time, timedelta
from datetime import datetime, timedelta

LOG_LEVEL=logging.INFO  # Could be e.g. "DEBUG", "INFO", "WARNING"

parser = argparse.ArgumentParser(description="rtl_443 to mqtt bridge")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")
parser.add_argument("-d", "--debug", help="debug output enabled", action='store_true')
parser.set_defaults(debug=LOG_DEBUG)

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
        LOG_FILENAME = args.log

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)


# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
    def __init__(self, logger, level):
        """Needs a logger and a logger level."""
        self.logger = logger
        self.level = level

    def write(self, message):
        # Only log if there is a message (not just a new line)
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())

    def flush(self):
        # write any pending stuff
        pass

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)

# Define MQTT event callbacks
def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code "+str(rc))

def on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.info("Unexpected disconnection.")

def on_message(client, obj, msg):
    logger.info(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def on_publish(client, obj, mid):
    logger.info("mid: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    logger.info("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(client, obj, level, string):
    logger.info(string)

# Setup MQTT connection

mqttc = mqtt.Client()
# Assign event callbacks
#mqttc.on_message = on_message
#mqttc.on_connect = on_connect
#mqttc.on_publish = on_publish
#mqttc.on_subscribe = on_subscribe
#mqttc.on_disconnect = on_disconnect

# Uncomment to enable debug messages
mqttc.on_log = on_log

# Uncomment the next line if your MQTT server requires authentication
mqttc.username_pw_set(MQTT_USER, password=MQTT_PASS)
connect_attempt = 0
while connect_attempt < CONNECTION_ATTEMPTS:
    connect_attempt += 1
    try:
        mqttc.connect(MQTT_HOST, MQTT_PORT, 60)
        break;
    except:
        import traceback
        print(f'Connection attempt {connect_attempt}/{CONNECTION_ATTEMPTS} failed!');
        print(traceback.format_exc())
    time.sleep(1)

mqttc.loop_start()

# Start RTL433 listener
rtl433_proc = subprocess.Popen(rtl_433_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

# Accepted messages
messages = {
    0:  [ # tower sensor doesn't have a message ID
        {
            "short": "Bat",
            "pretty": "Sensor Battery",
            "name_in": "battery_ok",
            "name_out": "battery_low",
            "process": (lambda x: "OFF" if x != 0 else "ON"),
            "component": "binary_sensor",
            "config": {
                "device_class": "battery",
                #"expire_after": UPDATE_EXPIRATION,
            }
        },
        {
            "short": "Temp",
            "pretty": "Temperature",
            "name_in": "temperature_C",
            "name_out": "temperature",
            "process": (lambda x: x),
            "component": "sensor",
            "config": {
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "expire_after": UPDATE_EXPIRATION,
            }
        },
        {
            "short": "Hum",
            "pretty": "Relative Humumidity",
            "name_in": "humidity",
            "name_out": "humidity",
            "process": (lambda x: x),
            "component": "sensor",
            "config": {
                "device_class": "humidity",
                "unit_of_measurement": "%",
                "expire_after": UPDATE_EXPIRATION,
            }
        }
    ],
    49: [
        {
            "short": "Bat",
            "pretty": "Weather Station Battery",
            "name_in": "battery",
            "name_out": "battery_low",
            "process": (lambda x: "OFF" if x == "OK" else "ON"),
            "component": "binary_sensor",
            "config": {
                "device_class": "battery",
            }
        },
        {
            "short": "WndSpd",
            "pretty": "Wind Speed",
            "name_in": "wind_speed_kph",
            "name_out": "wind_speed",
            "process": (lambda x: round(float(x)*0.621371, 1)),  # convert kph to mph
            "component": "sensor",
            "config": {
                "icon": "mdi:speedometer",
                "unit_of_measurement": "mph",
                "expire_after": UPDATE_EXPIRATION,
            }
        },
        {
            "short": "WndDir",
            "pretty": "Wind Direction",
            "name_in": "wind_dir_deg",
            "name_out": "wind_dir",
            "process": (lambda x: float(x)),
            "component": "sensor",
            "config": {
                "icon": "mdi:compass",
                "unit_of_measurement": "deg",
                "expire_after": UPDATE_EXPIRATION,
            }
        },
        {
            "short": "Rain",
            "pretty": "Rainfall",
            "name_in": "rain_inch",
            "name_out": "rain",
            "process": (lambda x: float(x)),
            "component": "sensor",
            "config": {
                "icon": "mdi:ruler",
                "unit_of_measurement": "inch",
                "expire_after": UPDATE_EXPIRATION,
            }
        }
    ],
    56: [
        {
            "short": "Bat",
            "pretty": "Weather Station Battery",
            "name_in": "battery",
            "name_out": "battery_low",
            "process": (lambda x: "OFF" if x == "OK" else "ON"),
            "component": "binary_sensor",
            "config": {
                "device_class": "battery",
            }
        },
        {
            "short": "WndSpd",
            "pretty": "Wind Speed",
            "name_in": "wind_speed_kph",
            "name_out": "wind_speed",
            "process": (lambda x: round(float(x)*0.621371, 1)), # convert kph to mph
            "component": "sensor",
            "config": {
                "icon": "mdi:speedometer",
                "unit_of_measurement": "mph",
                "expire_after": UPDATE_EXPIRATION,
            }
        },
        {
            "short": "Temp",
            "pretty": "Temperature",
            "name_in": "temperature_F",
            "name_out": "temperature",
            "process": (lambda x: float(x)),
            "component": "sensor",
            "config": {
                "device_class": "temperature",
                "unit_of_measurement": "°F",
                "expire_after": UPDATE_EXPIRATION,
            }
        },
        {
            "short": "Hum",
            "pretty": "Relative Humumidity",
            "name_in": "humidity",
            "name_out": "humidity",
            "process": (lambda x: float(x)),
            "component": "sensor",
            "config": {
                "device_class": "humidity",
                "unit_of_measurement": "%",
                "expire_after": UPDATE_EXPIRATION,
            }
        }
    ]
}

def main():
    # All known (configured) devices
    configured_sensors = []
    outbound_messages = {}
    last_config = datetime.now()

    logger.debug("Starting loop")
    while True:
        logger.debug("In loop")
        for line in iter(lambda: rtl433_proc.stdout.readline(), '\n'):
            logger.debug('Got message:\n  {}'.format(line))

            # Look for "time" as the marker that this is a valid payload
            if "time" in line:
                # Publish the raw JSON
                # mqttc.publish(MQTT_TOPIC, payload=line, qos=MQTT_QOS)

                # Incoming JSON looks like this:
                # {
                #   "time" : "2019-09-08 08:41:45",
                #   "model" : "Acurite 5n1 sensor",
                #   "message_type" : 56,
                #   "sensor_id" : 2006,
                #   "channel" : "A",
                #   "sequence_num" : 0,
                #   "battery" : "OK",
                #   "wind_speed_kph" : 3.483,
                #   "temperature_F" : 59.400,
                #   "humidity" : 90
                # }
                json_dict = json.loads(line)

                # Build up sensor ID string
                model = "model"
                id = "0"
                if "model" in json_dict:
                    model = json_dict["model"].lower().replace(" ", "_")

                if "sensor_id" in json_dict:
                    id = json_dict['sensor_id']
                elif "id" in json_dict:
                    id = json_dict['id']

                sensor_id = "{}_{}".format(model, id)

                # Skip unwanted devices
                if not sensor_id in FILTER_IDS:
                    logger.debug("Skipping message from sensor: {}".format(sensor_id))
                    continue

                # Get sensor info based on message type
                message_type = ""
                if "message_type" in json_dict:
                    message_type = json_dict['message_type']
                else:
                    message_type=0;

                if not message_type in messages:
                    logger.debug('Got unknown message type: {}'.format(message_type))
                    continue

                message = messages[message_type]

                for sensor in message:
                    if not sensor['name_in'] in json_dict:
                        logger.warn('Could not find sensor "{}" in message'.format(sensor['name_in']))
                        continue
                    sensor_val = sensor['process'](json_dict[sensor['name_in']])
                    logger.info("got sensor: {} - {}={}".format(sensor_id, sensor["name_out"], sensor_val))

                    long_sensor_name = sensor_id + sensor['short']
                    base_topic = '/'.join([MQTT_TOPIC, sensor['component'], sensor_id])

                    if not long_sensor_name in configured_sensors:
                        logger.info("Sending config for sensor: " + long_sensor_name)
                        # Log the long name so we know its already configured
                        config_topic = base_topic + "/" + sensor['short'] + "/config"
                        config_value = {
                            'name': sensor['pretty'],
                            'state_topic': base_topic + "/state",
                            'value_template': "{{{{ value_json.{} }}}}".format(sensor['name_out']),
                            'unique_id': long_sensor_name
                        }
                        config_value.update(sensor['config'])

                        # Send the config message
                        mqttc.publish(config_topic, payload=json.dumps(config_value), qos=MQTT_QOS)

                        # Note that we have configured this already
                        configured_sensors.append(long_sensor_name)

                    # Update the outbound message list with this sensor
                    state_topic = base_topic + '/state'
                    state_value = {}
                    if state_topic in outbound_messages:
                        state_value = outbound_messages[state_topic]
                    state_value.update( { sensor['name_out']: sensor_val } )
                    outbound_messages.update({state_topic: state_value})

                for topic, value in outbound_messages.items():
                    # Send sensor update
                    mqttc.publish(topic, payload=json.dumps(value), qos=MQTT_QOS)

                # Check if its time to redo the config
                config_delay = datetime.now() - last_config
                if config_delay > timedelta(minutes=RECONFIG_INTERVAL):
                    configured_sensors = []

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info('Received KeyboardInterrupt. Exiting...')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
