#! /usr/bin/env python
''' Given a numpy saved file, read it, adjust frames for time delay and
    display it '''

# Python lib imports
from __future__ import print_function

import cv2
import os
import glob
import sys
import time
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
NP_IMAGES_BASE = '/home/ggopalan/data/videos/aruba_cams/conf_rooms/archimedes/0613'
NP_IMAGES_FN = 'archimedes_cam_1528912415.npy'
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

def cleanup():
    cv2.destroyAllWindows()
    
def show_image_f1(co, format_img_array):
    # The time delta between frames has been converted to uint8 using (t0 - t1)/10. This will
    # convert it back to seconds
    inter_frame_delta = format_img_array[1] / 100.0 
    flat_image = format_img_array[2:]
    # get the image from the flat array
    image = flat_image.reshape((FRAME_HEIGHT, FRAME_WIDTH, 3))

    # Now id any persons in it
    ided_persons = obj_nn.id_people(co, image, display_predictions = True)
    if len(ided_persons) > 0:
        logging.info('IDed persons: {}'.format(ided_persons))
    cv2.imshow('Archimedes', image_utils.resize_half(image))
    cv2.waitKey(1)
    logging.info('Sleeping for inter frame delay of {} secs'
                                              .format(inter_frame_delta))
    time.sleep(inter_frame_delta)
    
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
    # Do the main loop
    main_loop(co)
    cleanup()

