#! /usr/bin/env python
''' Given a numpy format saved file, do the following:
      1. read each row and un-flatten it
      2. Process each frame for objects detected
      3. Send detected person message to kafka
      4. Display frame if asked for
   Note: This numpy file situatiuon is a temporary situation. Later straight
         cam to kaf will be done '''

# Python lib imports
from __future__ import print_function

import cv2
import os
import glob
import sys
import time
import json
import argparse
import logging

import numpy as np

# Local imports
import image_utils
import load_app_configs as lc
import obj_nn_utils as obj_nn

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

# The numpy array format is as follows:
#
#   [ 
#           Format version. Currently 1.0, Timestamp in milliseconds and as a float, The flattened image numpy array
#           (dtype is int)
#         [1, timestamp, flattened_image],
#         [1, timestamp, flattened_image],
#         [1, timestamp, flattened_image]
#   ]
#
#

# Constants
WRITE_FN_BASE = os.path.join(os.path.expanduser("~"), 'archimedes_cam_{}.npy')
NP_IMAGES_BASE = '/home/ggopalan/data/videos/aruba_cams/conf_rooms/archimedes/0612'
NP_IMAGES_FN = 'archimedes_cam_1528817373.npy'
NP_IMAGES_GLOB = '*.npy'
NP_IMAGES_FULL_FN = os.path.join(NP_IMAGES_BASE, NP_IMAGES_FN)
NP_IMAGES_FULL_GLOB = os.path.join(NP_IMAGES_BASE, NP_IMAGES_GLOB)

FPS = 10
FRAME_HEIGHT = 1536
FRAME_WIDTH = 2304
NUM_FRAMES_TO_WRITE = 100

CAM_URL = 'something.com/api/bmp'
CAM_NUM = 0

NPY_FILE_FORMAT = 1

APP_NAME = 'room_occ'    # Used to get topic from kafka config file
STREAM_NAME = 'archimedes_conf_cam1'    # In theory this should be in a
                                        # config file

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


def read_numpy_file(filename):
    ''' Load the specified filename into an numpy array and return it '''
    read_images = np.load(filename)
    return read_images

def cleanup(co):
    # Cleanup cv2 windows
    cv2.destroyAllWindows()
    # cleanup kafka
    kc = getattr(co.kafka_config, APP_NAME)
    kc.close_connection()

def show_image_f1(co, format_img_array):
    # The time delta between frames has been converted to 
    # uint8 using (t0 - t1)/10. This will convert it back to seconds
    inter_frame_delta = format_img_array[1] / 100.0 
    flat_image = format_img_array[2:]
    # get the image from the flat array
    image = flat_image.reshape((FRAME_HEIGHT, FRAME_WIDTH, 3))

    # Get the kafka config so messages can be sent
    kc = getattr(co.kafka_config, APP_NAME)
    # Now id any persons in it
    ided_persons = obj_nn.id_people(co, image, display_predictions = True)
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
            kc.send_message(person_json)
    else:
        logging.info('No people IDed in image')

    '''
    cv2.imshow('Archimedes', image_utils.resize_half(image))
    cv2.waitKey(1)
    logging.info('Sleeping for inter frame delay of {} secs'
                                              .format(inter_frame_delta))
    # time.sleep(inter_frame_delta)
    '''
    
def read_n_show_frames(co, images_array):
    ''' Read images from numpy array and show them '''
    for i, format_img_array in enumerate(images_array):
        # print(format_img_array.shape)
        # print(format_img_array[0], format_img_array[1])
        if format_img_array[0] == NPY_FILE_FORMAT:
            logging.info('Processing and showing frame number {}'.format(i))
            show_image_f1(co, format_img_array)
            prev_frame_time = format_img_array[1]
        else:
            logging.info('Unsupported format {}. Not processing array'
                                                .format(format_img_array[0]))

def main_loop(co):
    glob_files = glob.glob(NP_IMAGES_FULL_GLOB)
    # for np_images_fn in sorted(glob_files):
    for np_images_fn in [NP_IMAGES_FULL_FN]:
        logging.info('Showing from file: {}'.format(np_images_fn))
        images_array = read_numpy_file(np_images_fn)
        read_n_show_frames(co, images_array)

if __name__ == '__main__':
    args = parse_args()
    co = lc.config_obj(args)
    # Load our serialized model from disk (this can be part of init itself)
    co.load_dnn_model()
    # Setup kafka and also connect to the brokers
    co.get_kafka_app_obj(APP_NAME)
    # Do the main loop
    main_loop(co)
    cleanup(co)