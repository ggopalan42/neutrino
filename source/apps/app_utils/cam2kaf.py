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
import load_app_configs as lc
import image_utils as iu
import obj_nn_utils as obj_nn

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

# Constants
APP_NAME = 'helpdesk'

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

def cam2kaf(co):
    ''' Read from image, identify objects and send ided objects to kafka '''
    # Get the ml model name
    ml_model_name = co.get_app_mlmodel(APP_NAME)
    model_obj = co.get_dnn_model(ml_model_name)
    message_format_version = co.kafka_cfg.kafka_msg_format_ver

    # Go through each camera and count the number of people in them
    for cam_grp_name in co.cams_grp_names:
        # Get the cams config object for the cams_grp group and further
        # dive into it
        cam_grp_config_obj = co.get_cam_grp_config_obj(cam_grp_name)
        cam_grp_stream_name = co.get_cam_grp_stream_name(cam_grp_name)
        # Now go through each cam in that cams group
        for cam_name in cam_grp_config_obj.cam_grp_names:
            cam_obj = cam_grp_config_obj.cam_config[cam_name]

            # Read from cam and process for objects if valid image
            valid_image, image = cam_obj.cap_handle.read()
            if valid_image:
                # Write image to file if requested. Note here that the image
                # is written is as captured from cam (i.e. not annonated)
                if cam_obj.videowriter:
                    cam_obj.videowriter.write(image)
                # ID Objects
                ided_objects = obj_nn.id_objects(co, image, model_obj, 
                          display_predictions = cam_obj.display_predictions)

                # Show image if requested.
                if cam_obj.display_image:
                    cv2.imshow(cam_name, image)
                    cv2.waitKey(1)

                # If objects(s) have been detected in this image, 
                # feed the results to kafka
                if len(ided_objects) > 0:
                    kafka_message_dict = obj_nn.format_message(co, ided_objects,
                                 cam_grp_stream_name, message_format_version)
                    kafka_message_str = json.dumps(kafka_message_dict)
                    logging.info('Object(s) detected in image: {}'
                                                   .format(kafka_message_str))
                else:
                    logging.info('No object IDed in image')
            else:
                # If image read failed, log error
                logging.error('Image read from camera {} failed.(error ret = {}'
                                                .format(cam_name, valid_image))

def main_loop(co):
    ''' Continously detect persons and quit on keyboard interrupt '''
    try:
        while True:
            cam2kaf(co)
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Exiting . . . ')
        co.cleanup(cams_name)
        return ['Keyboard Interrupt']

if __name__ == '__main__':
    # This is for testing
    # This can also be used as a tamplate for future apps
    # Initialize
    args = parse_args()
    co = lc.config_obj(args)

    # Load ml model parameters
    ml_model_name = co.get_app_mlmodel(APP_NAME)
    co.load_dnn_model(ml_model_name)

    # Connect to cams
    cams_name = co.get_app_cams_name(APP_NAME)
    co.connect_to_cams(cams_name)

    # Connect to Kafka
    # kafka_params_dict = co.get_app_kafka_params(APP_NAME)
    co.set_kafka_app_obj(APP_NAME)

    # Do the main loop
    main_loop(co)

    # cleanup when done
    co.cleanup(cams_name)

