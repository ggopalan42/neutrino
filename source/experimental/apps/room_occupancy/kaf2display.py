#! /usr/bin/env python

import os
import sys
import time
import cv2
import logging
import json

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from kafka import KafkaConsumer

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

# Constants
ARCHIMEDES_TEMPLATE_FN = './archimedes_template.jpg'
ARCHIMEDES_PKL_FN = './archimedes_1531855842.pkl'
SLR01_FLOOR2_IMAGE_FN = './slr01_floor2_429191a0df4d392c8df9ed35a2ce444d.jpg'
SLR01_FLOOR2_IMAGE_SHAPE = (900, 1412, 3)

ID_IMAGE_WIDTH = 300
ID_IMAGE_HEIGHT = 300

# Conf room image constants
CONF_TEMPLATE_WIDTH = 2304
CONF_TEMPLATE_HEIGHT = 1536
CONF_TEMPLATE_WIDTH_RATIO = float(CONF_TEMPLATE_WIDTH)/float(ID_IMAGE_WIDTH)
CONF_TEMPLATE_HEIGHT_RATIO = float(CONF_TEMPLATE_HEIGHT)/float(ID_IMAGE_HEIGHT)
CONF_CIR_RADIUS = 10
CONF_CIR_COLOR = (255, 0, 0)   # BGR => Blue
CONF_CIR_THICKNESS = 5

# Floor room image constants
F2_IMAGE_WIDTH = 200
F2_IMAGE_HEIGHT = 150
F2_IMAGE_WIDTH_RATIO = float(F2_IMAGE_WIDTH)/float(ID_IMAGE_WIDTH)
F2_IMAGE_HEIGHT_RATIO = float(F2_IMAGE_HEIGHT)/float(ID_IMAGE_HEIGHT)
FLOOR_CIR_RADIUS = 3
FLOOR_CIR_COLOR = (255, 0, 0)   # BGR => Blue
FLOOR_CIR_THICKNESS = 2

CIR_LOCS_FIFO = [(0, 0)] * 4

# Below kafka stuff is a hack to get going quick. 
# Need to define a schema properly and all that
PC_COL_NAMES = ['detect_time', 'msg_format_version', 'stream_name', 'found',
                'startX', 'startY', 'endX', 'endY', 'confidence']
# Again lotsa magic variables
TOPIC = 'roomocc1'
KAFKA_SERVER = '10.2.13.29'
KAFKA_PORT = '9092'
PC_STREAM_NAME = 'Aruba_SLR01_Cams'

class pc_kafka_pandas_consumer():
    def __init__(self, name):
        logging.info('Connecting to Kafka broker: {}:{}'
                                            .format(KAFKA_SERVER, TOPIC))
        self.consumer = KafkaConsumer(TOPIC,
                   bootstrap_servers='{}:{}'.format(KAFKA_SERVER, KAFKA_PORT))
        self.pc_name = name

def get_pkl_files():
    pkl_files = os.listdir(PKL_DIR)
    pkl_files = [ x for x in pkl_files if x.endswith('pkl')]
    # Now add the full path
    pkl_files = [os.path.join(PKL_DIR, x) for x in pkl_files]
    return pkl_files

def epoch_to_pacific(df_epoch):
    ''' Convert from epoch time to PST'''
    # Note: This TZ conversion is very temporary. There are several problems with this:
    #        1. Not sure why divide by 1e7 needs to be done. Some issue in time pipeline that needs to be debugged
    #        2. The entire "tz_localize('UTC').tz_convert('US/Pacific')" is confusing to me
    return pd.to_datetime(df_epoch/1e7, unit='s').dt.tz_localize('UTC').dt.tz_convert('US/Pacific')

def resize_half(image):
    ''' Resizes any image given to it by half '''
    img_half_h = int(image.shape[0]/2)
    img_half_w = int(image.shape[1]/2)
    return cv2.resize(image, (img_half_w, img_half_h))

def resize_qtr(image):
    ''' Resizes any image given to it by half '''
    img_half_h = int(image.shape[0]/4)
    img_half_w = int(image.shape[1]/4)
    return cv2.resize(image, (img_half_w, img_half_h))

def resize_double(image):
    ''' Doubles the size of any given image '''
    img_double_h = int(image.shape[0]*2)
    img_double_w = int(image.shape[1]*2)
    return cv2.resize(image, (img_double_w, img_double_h))

def resize_quadruple(image):
    ''' Doubles the size of any given image '''
    img_quadruple_h = int(image.shape[0]*4)
    img_quadruple_w = int(image.shape[1]*4)
    return cv2.resize(image, (img_quadruple_w, img_quadruple_h))

def kafka_to_display(pc_kafka, conf_image, f2_image):
    ''' Read the pkl dataframe and desiplay the "person" onto the conf room templates '''
    processing_ts = 0
    try:
        cv2.namedWindow('Archimedes Conf Room')
        cv2.namedWindow('Archimedes Floor Image')
        cv2.moveWindow('Archimedes Conf Room', 0, 0)
        cv2.moveWindow('Archimedes Floor Image', 1100, 0)
        for msg in pc_kafka.consumer:
            # Copy images (so circles do not accumulate)
            conf_image_copy = conf_image.copy()
            floor_image_copy = f2_image.copy()

            # Get the latest from kafka
            kafka_msg = json.loads(msg.value)
            kafka_msg_json = json.loads(msg.value)
            if kafka_msg_json['msg_format_version'] == '1.1.0':
                print('Proc 1.1.0')
                df_json = {}
                df_json['detect_time'] = kafka_msg_json['detect_time']
                df_json['stream_name'] = kafka_msg_json['stream_name']
                df_json['msg_format_version'] = kafka_msg_json['msg_format_version']
                for df_sub_json in kafka_msg_json['objects_list']:
                    combined_dict = dict(df_json, **df_sub_json)
                    temp_df = pd.DataFrame(combined_dict, index=[0])

                    # If detected obj is a person
                    if combined_dict['found'] == 'person':
                        # Compute center of person
                        centerX = float((temp_df.endX - temp_df.startX)/2)
                        centerY = float((temp_df.endY - temp_df.startY)/2)
                        print('CenterX: {}'.format(centerX))
                        print('CenterY: {}'.format(centerY))
                        # Set circle for conference room image
                        conf_cir_x = int(centerX * CONF_TEMPLATE_WIDTH_RATIO)
                        conf_cir_y = int(centerY * CONF_TEMPLATE_HEIGHT_RATIO)
                        conf_cir_loc = (conf_cir_x, conf_cir_y)
                        cv2.circle(conf_image_copy, conf_cir_loc, 
                                   CONF_CIR_RADIUS, CONF_CIR_COLOR, 
                                                          CONF_CIR_THICKNESS)
                        # Set circle for floor image of conf room
                        floor_cir_x = int(centerX * F2_IMAGE_WIDTH_RATIO) + 50
                        floor_cir_y = int(centerY * F2_IMAGE_HEIGHT_RATIO) - 20
                        floor_cir_loc = (floor_cir_x, floor_cir_y)
                        cv2.circle(floor_image_copy, floor_cir_loc, 
                                   FLOOR_CIR_RADIUS, FLOOR_CIR_COLOR, 
                                   FLOOR_CIR_THICKNESS)
                # Show the images
                cv2.imshow('Archimedes Conf Room', resize_half(conf_image_copy))
                cv2.imshow('Archimedes Floor Image', 
                                         resize_quadruple(floor_image_copy))
                cv2.waitKey(1)
            else:
               logging.info('Sorry. Do not deal with this msg format yet: {}'
                                 .format(kafka_msg_json['msg_format_version']))
               continue

    except KeyboardInterrupt:
        cv2.destroyAllWindows()
        logging.info('Received Ctrl-C. Exiting . . . ')
        return ['Keyboard Interrupt']

if __name__ == '__main__':
    
    # Load the conf room template image
    conf_image = cv2.imread(ARCHIMEDES_TEMPLATE_FN)
    # The array slice [50:200, 1200:1400] is to slice out Archimedes
    f2_image = cv2.imread(SLR01_FLOOR2_IMAGE_FN)[50:200, 1200:1400]

    # Setup and connect to kafka
    pc_kafka = pc_kafka_pandas_consumer(PC_STREAM_NAME)

    kafka_to_display(pc_kafka, conf_image, f2_image)
