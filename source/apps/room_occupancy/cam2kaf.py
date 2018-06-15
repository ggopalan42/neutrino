#! /usr/bin/env python
''' Given an URL, keep getting image from it, detect if there are any person(s)
    in the image and feed the results to kafka '''

# Python lib imports
import argparse
import glob
import cv2
import os
import sys
import json
import time
import yaml
import logging

import numpy as np

from kafka import KafkaProducer

# Local imports
# import count_people_from_image as cp
import load_app_configs as lc
import obj_nn_utils as obj_nn

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

# Constants
APP_NAME = 'room_occ'    # Used to get topic from kafka config file
STREAM_NAME = 'archimedes_conf_cam1'    # In theory this should be in a
                                        # config file

CAM_URL = 'something.com/api/bmp'
CAM_NUM = 0



# This is only if this is used as a main program
def parse_args():
    ''' Parse the arguments and return a dict '''
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--neutrino-home",
            help="people Counter config YAML file")
    args = vars(ap.parse_args())

    # Check if NEUTRINO_HOME is provided as args. If not, check 
    # that its provided via env variable. If not, raise an error
    if not args['neutrino_home']:
        try:
            neutrino_home = os.environ['NEUTRINO_HOME']
            args['neutrino_home'] = neutrino_home
        except KeyError as e:
            raise RuntimeError('Need to set NEUTRINO_HOME or '
                               'provide it using the -n option') from e
    return args

def cleanup(co, ch):
    # Cleanup cv2 windows
    cv2.destroyAllWindows()
    # cleanup kafka
    kc = getattr(co.kafka_config, APP_NAME)
    kc.close_connection()
    # release cam
    ch.release()

#### All of this below needs to be put into proper configs #####
def init_cam():
    ''' Connect to the camera '''
    logging.info('Connecting to camera')
    cap_handle = cv2.VideoCapture(CAM_NUM)
    return cap_handle


def cam2kaf(co, ch, display_image = False, send2kaf = False):
    ''' Read image from cam, process it (id persons etc.) and send to kafka '''

    # Get the kafka config so messages can be sent
    kc = getattr(co.kafka_config, APP_NAME)

    t0 = int(time.time() * 1e3)
    valid_image, image = ch.read()
    t1 = int(time.time() * 1e3)
    logging.info('Read image in {} milli-seconds'.format(t1-t0))

    if valid_image:
        ided_persons = obj_nn.id_people(co, image, display_predictions = False)
        if len(ided_persons) > 0:
            logging.info('Identified {} persons in frame'
                                                    .format(len(ided_persons)))
            # Go through all id-ed persons, add a few more bits
            # of info and send it to kafka
            for person in ided_persons:
                timenow_usecs = int(time.time() * 10e6)
                person['detect_time'] = timenow_usecs
                person['stream_name'] = STREAM_NAME
                person['msg_format_version'] = kc.kafka_msg_fmt
                person_json = json.dumps(dict(person))
                if send2kaf:
                    kc.send_message(person_json)
                else:
                    logging.info('Not sending to kafka, '
                                 'but this is what I got: {}'
                                               .format(person_json))
        else:
            logging.info('No people IDed in image')

        if display_image:
            cv2.imshow(STREAM_NAME, image)
            cv2.waitKey(1)
    else:
        print('Not valid: {}'.format(valid_image))

def main_loop(co, ch):
    ''' Continously detect persons and quit on keyboard interrupt '''

    try:
        while True:
            cam2kaf(co, ch, display_image = False, send2kaf = True)
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Exiting . . . ')
        cleanup(co, ch)

if __name__ == '__main__':
    # Initialize
    args = parse_args()
    co = lc.config_obj(args)
    # Load our serialized model from disk (this can be part of init itself)
    co.load_dnn_model()
    # Setup kafka and also connect to the brokers
    co.get_kafka_app_obj(APP_NAME)
    # Connect to local cam
    ch = init_cam()

    # Do the main loop
    main_loop(co, ch)
    # cleanup(co, ch)
