#! /usr/bin/env python
''' Given a numpy saved file, read it, adjust frames for time delay and
    display it '''

# Python lib imports
from __future__ import print_function

import cv2
import os
import sys
import time
import logging

import numpy as np

# Local imports
import image_utils

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
NP_IMAGES_BASE = '/home/ggopalan/projects/apps/people_counter/video_save'
NP_IMAGES_FN = 'archimedes_cam_1528741516.npy'
NP_IMAGES_FULL_FN = os.path.join(NP_IMAGES_BASE, NP_IMAGES_FN)

FPS = 10
FRAME_HEIGHT = 1536
FRAME_WIDTH = 2304
NUM_FRAMES_TO_WRITE = 100

CAM_URL = 'something.com/api/bmp'
CAM_NUM = 0

NPY_FILE_FORMAT = 1

def read_numpy_file(filename):
    read_images = np.load(filename)
    return read_images

def cleanup(cap_handle):
    cv2.destroyAllWindows()
    
def show_image_f1(format_img_array, prev_frame_time):
    inter_frame_delta = (format_img_array[1] - prev_frame_time)/100.0
    flat_image = format_img_array[2:]
    image = flat_image.reshape((FRAME_HEIGHT, FRAME_WIDTH, 3))
    cv2.imshow('Archimedes', image_utils.resize_half(image))
    cv2.waitKey(1)
    logging.info('Sleeping for inter frame delay of {} secs'
                                              .format(inter_frame_delta))
    time.sleep(inter_frame_delta)
    
def read_n_show_frames(images_array):
    ''' Read images from numpy array and show them '''
    prev_frame_time = 0
    for i, format_img_array in enumerate(images_array):
        # print(format_img_array.shape)
        # print(format_img_array[0], format_img_array[1])
        if format_img_array[0] == NPY_FILE_FORMAT:
            logging.info('Processing and showing frame number {}'.format(i))
            show_image_f1(format_img_array, prev_frame_time)
            prev_frame_time = format_img_array[1]
        else:
            logging.info('Unsupported format {}. Not processing array'
                                                .format(format_img_array[0]))

def main():
    images_array = read_numpy_file(NP_IMAGES_FULL_FN)
    read_n_show_frames(images_array)

if __name__ == '__main__':
    main() 

