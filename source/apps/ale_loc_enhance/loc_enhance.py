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
import urllib.request
import numpy as np

from kafka import KafkaProducer
from urllib.parse import urlparse

# Local imports
# import count_people_from_image as cp
import loc_utils

# Constamts

# Config files (probably a good idea to move all config files to a single dir)
CONFIG_BASE = './configs'
LOC_CONFIG_YAML_FILE = os.path.join(CONFIG_BASE, 'loc_config.yml')

# Other vars

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

# This is only if this is used as a main program
def parse_args():
    ''' Parse the arguments and return a dict '''
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", default=LOC_CONFIG_YAML_FILE,
            help="Location config YAML file")
    args = vars(ap.parse_args())
    return args

def send_message(message, kf_obj):
    ''' Send message to kafka topic '''
    # print(message)
    # The .encode is to convert str to bytes (utf-8 is default)
    kf_obj.producer.send(KAFKA_TOPIC, message.encode(), partition = 0)

def count_people(pc):
    ''' Load image from the cameras, count number of persons in it
        and feed kafka with the results '''

    # Go through each camera and count the number of people in them
    for cam_name in pc.all_cams_config.all_cams_name:
        cam_obj = pc.all_cams_config.cam_config[cam_name]
        valid_image, image = cam_obj.cap_handle.read()

        if valid_image:
            # Write image to file if requested. Note here that the image
            # is written is as captured from cam (i.e. not annonated)
            if cam_obj.videowriter:
                cam_obj.videowriter.write(image)
            ided_persons = loc_utils.id_people(pc, image, 
                                           cam_obj.display_predictions)
            # Show image if requested.
            if cam_obj.display_image:
                cv2.imshow(cam_name, loc_utils.resize_half(image))
                cv2.waitKey(1)

            # If person(s) have been detected in this image, 
            # feed the results to kafka
            if len(ided_persons) > 0:
                logging.info('Person(s) detected in image')
                for person in ided_persons:
                    timenow_secs = time.time()
                    person['detect_time'] = timenow_secs
                    # person['stream_name'] = pc.stream_name
                    # tmp for now
                    person['stream_name'] = 'Aruba_SLR01_Cams'
                    person['msg_format_version'] = pc.msg_format_ver
                    logging.info(person)
                    person_json = json.dumps(dict(person))
                    # send_message(person_json, pc)
            else:
                logging.info('No people IDed in image')
        else:
            # If image read failed, log error
            logging.error('Image read from camera {} failed.(error ret = {}'
                                                .format(cam_name, valid_image))

def cleanup():
    ''' Cleanup before exiting '''
    cv2.destroyAllWindows()
    # Should anything be released on kafka and others?

def main_loop(pc):
    ''' Continously detect persons and quit on keyboard interrupt '''
    try:
        while True:
            count_people(pc)
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Exiting . . . ')
        pc.release_all_cams()
        cleanup()
        return ['Keyboard Interrupt']

if __name__ == '__main__':
    # Initialize
    loc = loc_utils.loc_config(parse_args())
    # Connect to camera
    loc.connect_all_cams()
    # load our serialized model from disk (this can be part of init itself)
    loc.load_dnn_model()
    # Do the main loop
    main_loop(loc)
    # Do the main loop
    loc.release_all_cams()
    cleanup()

