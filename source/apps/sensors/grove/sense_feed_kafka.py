#! /usr/bin/env python3

import os
import sys
import json
import urllib.request
import numpy as np
from time import sleep, time
from kafka import KafkaProducer
import grovepi

KAFKA_BROKER = '10.2.13.29'
KAFKA_PORT = '9092'
KAFKA_TOPIC = 'sensegrove2'

# Analog Port that the Grove Temp & Hum Sensor (DHT11) is connected to
ANA_DHT11_SENSOR_PORT = 0  
# Version of DHT11 board
GROVE_DHT11_VERSION = '1.2'
# Analog port of light sensor
ANA_LIGHT_SENSOR_PORT = 0
# Analog port of Air Quality Sensor
ANA_AIR_QUALITY_SENSOR_PORT = 1
# Analog port of HCHO sensor
ANA_HCHO_SENSOR = 2

# Digital port to which the Ultrasonic sensor is connected
DIG_ULTRASONIC_PORT = 3

class kafka_obj():
    def __init__(self):
        self.producer=KafkaProducer(bootstrap_servers=
                                   '{}:{}'.format(KAFKA_BROKER, KAFKA_PORT))
        self.msg_format_ver = '1.0.0'

def send_message(message, kf_obj):
    ''' Send message to kafka topic '''
    # print(message)
    # The .encode is to convert str to bytes (utf-8 is default)
    kf_obj.producer.send(KAFKA_TOPIC, message.encode(), partition = 0)

def init_sensors():
    grovepi.pinMode(ANA_LIGHT_SENSOR_PORT,"INPUT")
    grovepi.pinMode(ANA_AIR_QUALITY_SENSOR_PORT,"INPUT")

def read_grove_ultra_sensor(dig_port):
    ''' Read the Grove Ultrasonic Distance sensor '''
    try:
        ultra_dist = grovepi.ultrasonicRead(dig_port)
    except Exception as e:
        # Raise a proper error later
        print('ERROR: Reading Ultrasonic sensor gave error: {}'.format(e))
        return 'Error'
    return ultra_dist

def read_grove_dht11_sensor(ana_port):
    ''' Read the Grove DHT11 sensor '''
    try:
        temp = grovepi.temp(ana_port, GROVE_DHT11_VERSION)
    except Exception as e:
        # Raise a proper error later
        print('ERROR: Reading temp sensor (DHT11) gave error: {}'.format(e))
        return 'Error'
    return temp

def read_grove_light_sensor(ana_port):
    ''' Read th sensorevalue and return it '''
    # Get sensor value
    sensor_value = grovepi.analogRead(ana_port)
    # Calculate resistance of sensor in K
    resistance = (float)(1023 - sensor_value) * 10 / sensor_value
    return sensor_value, resistance

def read_air_quality_sensor(ana_port):
    ''' Read the air quality sensor value and return it '''
    # Get sensor value
    # Treshold of 700 comes from the reference code
    treshold = 700
    sensor_value = grovepi.analogRead(ana_port)
    return sensor_value, treshold

def read_hcho_sensor(ana_port):
    ''' Read the HCHO sensor value and return the value and voltage '''
    # Grove VCC value comes from reference code (and schematics)
    grove_vcc = 5
    # Get sensor value
    sensor_value = grovepi.analogRead(ana_port)
    voltage = (float)(sensor_value * grove_vcc / 1024)
    return sensor_value, voltage


def main_loop(kf_obj):
    ''' Go through each sensor type and (for now) print the returned value '''
    while True:
        msg_dict = {'data_type': 'sensor', 
                    'stream_name': 'piesense2', 
                    'stream_subname': 'grove'}
        try:
            # temp = read_grove_dht11_sensor(ANA_DHT11_SENSOR_PORT)
            # print('Temp Reading from DHT11 is: {}'.format(temp))
            ultra = read_grove_ultra_sensor(DIG_ULTRASONIC_PORT)
            print('Distance reading from Ultrasonic Rangefinder is: {}cm'
                                                                .format(ultra))
            msg_dict['ultra_range1'] = ultra 
            light, _ = read_grove_light_sensor(ANA_LIGHT_SENSOR_PORT)
            print('Light Sensor Reading is: {}'.format(light))
            msg_dict['light_sensor1'] = light 
            air_q, tresh = read_air_quality_sensor(ANA_AIR_QUALITY_SENSOR_PORT)
            print('Air quality reading is: {}. (Treshold is: {})'
                                                         .format(air_q, tresh))
            msg_dict['air_quality1'] = air_q 
            hcho_val, hcho_volt = read_hcho_sensor(ANA_HCHO_SENSOR)
            print('HCHO reading is: {}. Corresponding voltage is: {}'
                                                  .format(hcho_val, hcho_volt))
            msg_dict['hcho1'] = hcho_val

            # Format and send message to kafka
            timenow_secs = time()
            msg_dict['detect_time'] = timenow_secs
            msg_dict['msg_format_version'] = kf_obj.msg_format_ver
            msg_str = json.dumps(msg_dict)
            print('Sending message to kafka topic: {}'.format(KAFKA_TOPIC))
            send_message(msg_str, kf_obj)
            # 'Record' separator
            print('')

            sleep(1)
        except KeyboardInterrupt:
            print('Keyboard interrupt received. Exiting')
            return

if __name__ == '__main__':

    kf_obj = kafka_obj()

    init_sensors()
    main_loop(kf_obj)



