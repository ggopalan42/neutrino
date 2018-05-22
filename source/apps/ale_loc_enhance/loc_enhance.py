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
import loc_utils
import ale_utils

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

def loadnshow_floor_image(filename):
    loc_images = np.load(filename)
    print(loc_images.shape)
    cv2.imshow('tmpstuff', loc_images)
    cv2.waitKey(1)

# This stuff below is temporary. Will not work with two floor images.
# It needs to be done differently
locs_dict = {}
def show_floor_image(loc, au, topicInit):
    ''' Tmp stuff '''
    global locs_dict
    # Get a single message from ALE Server
    ale_msg = au.get_topic_message(topicInit)
    # Now get its floor id
    ale_msg_floor_id = ale_msg['location']['floor_id']

    # Now get the floor IDs that neeeds to be displayed 
    # (currently will work only for 1 floor)
    for cam_name in loc.all_cams_config.all_cams_name:
        cam_obj = loc.all_cams_config.cam_config[cam_name]
        cam_floor_id = cam_obj.floor_id

    # If a station is found on floor_id of interest, then show it
    if ale_msg_floor_id.lower() == cam_floor_id.lower():
        msg_epoch_ts = ale_msg['timestamp']
        msg_ts = time.strftime('%Y-%m-%d_%H:%M:%S',
                                             time.localtime(msg_epoch_ts))
        msg_loc = ale_msg['location']
        loc_x = msg_loc['sta_location_x']
        loc_y = msg_loc['sta_location_y']
        loc_err = msg_loc['error_level']
        sta_mac = msg_loc['hashed_sta_eth_mac']
        curr_time = time.time()
        locs_dict[sta_mac]={'sta_location_x': loc_x,
                            'sta_location_y': loc_y,
                            'error_level': loc_err,
                            'associated': msg_loc['associated'],
                            'timestamp': curr_time}

        # for k in locs_dict:
        #   print(k)
        # print(len(locs_dict))

        logging.info('Found station: {}, {} (ts: {})'
                                     .format(loc_x, loc_y, msg_ts))

        au.draw_locs(ale_msg_floor_id, locs_dict)

        # Age out entries in locs_dict. This is a crude way of doing it
        # and will be a temp fix
        au.age_out_locs(locs_dict)

def show_cam_image(loc):
    ''' Load image from the cameras, identify objects in it. Also load
        the floor map, connect to ALE and get and plot station locations '''

    # Go through each camera and count the number of people in them
    for cam_name in loc.all_cams_config.all_cams_name:
        cam_obj = loc.all_cams_config.cam_config[cam_name]
        valid_image, image = cam_obj.cap_handle.read()

        if valid_image:
            # Write image to file if requested. Note here that the image
            # is written is as captured from cam (i.e. not annonated)
            if cam_obj.videowriter:
                cam_obj.videowriter.write(image)
            ided_persons = loc_utils.id_people(loc, image, 
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
                    # person['stream_name'] = loc.stream_name
                    # tmp for now
                    person['stream_name'] = 'Aruba_SLR01_Cams'
                    person['msg_format_version'] = loc.msg_format_ver
                    logging.info(person)
                    person_json = json.dumps(dict(person))
                    # send_message(person_json, loc)
            else:
                logging.info('No people IDed in image')
        else:
            # If image read failed, log error
            logging.error('Image read from camera {} failed.(error ret = {}'
                                                .format(cam_name, valid_image))

def cleanup(au, loc):
    ''' Cleanup before exiting '''
    au.disconnect()
    loc.release_all_cams()
    cv2.destroyAllWindows()
    # Should anything be released on kafka and others?

def main_loop(loc, au, topicInit):
    ''' Continously detect persons and quit on keyboard interrupt '''
    try:
        while True:
            show_cam_image(loc)
            show_floor_image(loc, au, topicInit)
            # loadnshow_floor_image('loc_corr_f3_elevators_ale_r1.npy')
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Exiting . . . ')
        cleanup(au, loc)
        return ['Keyboard Interrupt']

def get_valid_floors(loc):
    ''' Return a list of floor IDs that are attached to 'valid' cameras '''
    floor_id_list = []
    for cam_name in loc.all_cams_config.all_cams_name:
        cam_obj = loc.all_cams_config.cam_config[cam_name]
        floor_id_list.append(cam_obj.floor_id)
    return floor_id_list


# All Tmp Stuff Below
# LOC_WRITE_FN = None
LOC_WRITE_FN = 'loc_corr_f3_elevators_ale_r1.mjpg'
if __name__ == '__main__':
    # Initialize
    args = parse_args()
    loc = loc_utils.loc_config(args)
    au = ale_utils.ale_config(args)

    ##### Setup all ALE related stuff #####
    # Load and preprocess floor images
    au.load_floor_images()
    # Get the list of floor images from the cameras set as 'valid' and show them
    # valid_floor_ids = get_valid_floors(loc)
    # au.show_floor_images(valid_floor_ids)
    # Connect and subscribe to ALE server
    au.connect_to_server()
    # topicInit='geofence_notify'
    topicInit = 'location'
    au.subscribe_to_topics(topicInit)

    ###### Setup all Camera related stuff #####
    # Connect to camera
    loc.connect_all_cams()
    # load our serialized model from disk (this can be part of init itself)
    loc.load_dnn_model()

    # Do the main loop
    main_loop(loc, au, topicInit)

