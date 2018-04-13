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
import count_people_from_image as cp
import pc_utils

# Constamts

# Config files (probably a good idea to move all config files to a single dir)
CAM_CONFIG_YAML_FILE = './pc_aruba_slr01_cams.yml'
PC_CONFIG_YAML_FILE = './pc_config.yml'

# KAFKA_BROKER = '10.2.13.29'
# KAFKA_PORT = '9092'
# KAFKA_TOPIC = 'peoplecounter1'

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

class people_count():
    def __init__(self, args):
        # Load all configs
        self.args = args
        self._load_pc_configs(args)
        
        self.auth_done = False    # Auth needs to be done only once
        #### All of this below should go into config files ###
        # previous_det is a stupid hack. See explanation below
        self.previous_det = np.array([[[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]]])
        # Currently using the Mobilenet SSD models. Later make this
        # stuff more dynamic
        self.prototxt_file = './models/MobileNetSSD_deploy.prototxt.txt'
        self.model_file = './models/MobileNetSSD_deploy.caffemodel'
        self.classes = ["background", "aeroplane", "bicycle", "bird", "boat",
                "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                "sofa", "train", "tvmonitor"]
        self.person_idx = self.classes.index('person')
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3)) 
        self.producer=KafkaProducer(bootstrap_servers= '{}:{}'.format(
                                    self.pc_config.kafka_broker_hostname, 
                                    self.pc_config.kafka_port))
        # Again, specifying format ver below here is non ideal
        self.msg_format_ver = '1.0.0'

    # Private methods
    def _load_pc_configs(self, args):
        ''' Load all needed configs '''
        pc_yaml_fn = args['pc_config']
        cam_yaml_fn = args['cam_config']

        # Set people counter config
        with open(pc_yaml_fn) as pcfh:
            pc_config_dict = yaml.load(pcfh)
        self.pc_config = pc_utils.pc_config(pc_config_dict)
        # Below is a hack for backwards compatibility. Should be removed
        self.confidence = self.pc_config.confidence

        # Set camera config
        with open(cam_yaml_fn) as cfh:
            cam_config_dict = yaml.load(cfh)
        self.all_cams_config = pc_utils.all_cams_config(cam_config_dict)

    # Public methods
    def load_dnn_model(self):
        ''' Load a model and weights. Currently hard coded to MobileNet SSD '''
        logging.info('Loading model: {}'.format(self.model_file))
        self.net = cv2.dnn.readNetFromCaffe(self.prototxt_file, self.model_file)

    def connect_all_cams(self):
        ''' Connect to all specified cameras '''
        # Go through all cameras and connect to them
        # I know, this for loop can simply be done as: 
        # for cam_obj in self.all_cams_config.cam_config. 
        # But wanted to do it in order. 
        # But again I know, I could have used ordered dict . . .
        for cam_name in self.all_cams_config.all_cams_name:
            logging.info('Connecting to camera: {}'.format(cam_name))
            cam_obj = self.all_cams_config.cam_config[cam_name]
            cam_obj.connect_to_cam()

    def release_all_cams(self):
        ''' Release all cameras' resources '''
        # Go through all cameras and connect to them
        for cam_name in self.all_cams_config.all_cams_name:
            logging.info('Releasing camera: {}'.format(cam_name))
            cam_obj = self.all_cams_config.cam_config[cam_name]
            cam_obj.cam_release()

# This is only if this is used as a main program
def parse_args():
    ''' Parse the arguments and return a dict '''
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--pc_config", default=PC_CONFIG_YAML_FILE,
            help="people Counter config YAML file")
    ap.add_argument("-c", "--cam_config", default=CAM_CONFIG_YAML_FILE,
            help="Camera config YAML file")
    args = vars(ap.parse_args())
    return args

def send_message(message, kf_obj):
    ''' Send message to kafka topic '''
    # print(message)
    # The .encode is to convert str to bytes (utf-8 is default)
    kf_obj.producer.send(KAFKA_TOPIC, message.encode(), partition = 0)

def urllib_auth_url(pcu):
    ''' Authenticate a URL with provided username and password '''
    # Get the top level URL - I think this is what needs to be authenticated
    parsed = urlparse(pcu.url)
    top_level_url = '{}://{}'.format(parsed.scheme, parsed.netloc)
    logging.info('Authenticating top level URL: {}'.format(top_level_url))

    # create a password manager
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()

    # Add the username and password.
    # If we knew the realm, we could use it instead of None.
    # top_level_url = "http://example.com/foo/"
    password_mgr.add_password(None, top_level_url, pcu.username, pcu.password)

    handler = urllib.request.HTTPDigestAuthHandler(password_mgr)

    # create "opener" (OpenerDirector instance)
    opener = urllib.request.build_opener(handler)

    # use the opener to fetch a URL
    opener.open(top_level_url)

    # Install the opener.
    # Now all calls to urllib.request.urlopen use our opener.
    urllib.request.install_opener(opener)

    # Now set the auth done flag
    pcu.auth_done = True

def url_to_image(pcu):
    return pcu.cap_handle.read()

def count_people(pc):
    ''' Load image from the cameras, count number of persons in it
        and feed kafka with the results '''

    # Go through each camera and count the number of people in them
    for cam_name in pc.all_cams_config.all_cams_name:
        cam_obj = pc.all_cams_config.cam_config[cam_name]
        valid, image = cam_obj.cap_handle.read()

        if valid:
            ided_persons = cp.id_people(pc, image, display_predictions=False)
            cv2.imshow(cam_name, image)
            cv2.waitKey(1)

            # If person(s) have been detected in this image, 
            # feed the results to kafka
            if len(ided_persons) > 0:
                logging.info('Person(s) detected in image')
                for person in ided_persons:
                    timenow_secs = time.time()
                    person['detect_time'] = timenow_secs
                    # person['stream_name'] = pc.stream_name
                    person['msg_format_version'] = pc.msg_format_ver
                    logging.info(person)
                    person_json = json.dumps(dict(person))
                    # send_message(person_json, pc)
            else:
                logging.info('No people IDed in image')
        else:
            # If image read failed, log error
            logging.error('Image read from camera {} failed'.format(cam_name))

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
    pc = people_count(parse_args())
    # Connect to camera
    pc.connect_all_cams()
    # load our serialized model from disk (this can be part of init itself)
    pc.load_dnn_model()
    # Do the main loop
    main_loop(pc)
    # Do the main loop
    pc.release_all_cams()
    cleanup()

