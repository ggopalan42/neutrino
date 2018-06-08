#! /usr/bin/env python
''' Given an URL, keep getting image from it, detect if there are any person(s)
    in the image and feed the results to kafka '''

# Python lib imports
from __future__ import print_function

import cv2
import os
import sys
import time
import logging

import numpy as np

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
# WRITE_FN_BASE = os.path.join(os.path.expanduser("~"), 'archimedes_cam_{}.mjpg')
# WRITE_FN_BASE = os.path.join(os.path.expanduser("~"), 'archimedes_cam_{}.xvid')
# WRITE_FN_BASE = os.path.join(os.path.expanduser("~"), 'archimedes_cam_{}.dvix')

FPS = 10
FRAME_HEIGHT = 1536
FRAME_WIDTH = 2304
NUM_FRAMES_TO_WRITE = 100

CAM_URL = 'something.com/api/bmp'
CAM_NUM = 0

NPY_FILE_FORMAT = 1

def get_fn_with_ts():
    ''' Add timestamp in epoch to WRITE_FN_BASE and return it '''
    now_time = time.time()
    time_in_secs = int(now_time)
    return WRITE_FN_BASE.format(time_in_secs)

def init_cam():
    ''' Connect to the camera '''
    logging.info('Connecting to camera')
    cap_handle = cv2.VideoCapture(CAM_NUM)
    return cap_handle

def cleanup(cap_handle):
    cap_handle.release()
    

def read_n_write_frames(cap_handle, filename, nframes = NUM_FRAMES_TO_WRITE):
    ''' Read from cam and write n frames to the specified videowriter '''
    # Initialize an empty numpy array of size as follows:
    #    - Row size of: NUM_FRAMES_TO_WRITE (reason should be obvious)
    #    - Column size of flattened image array ( FRAME_HEIGHT * FRAME_WIDTH * 3) + 2. The two is for image format
    #      timestamp of image 
    np_images = np.empty((NUM_FRAMES_TO_WRITE, (( FRAME_HEIGHT * FRAME_WIDTH * 3)+2)), dtype=np.uint8)
    
    # Now read in all other frames
    for i in range(0, nframes):
        # Read in a frame
        t0 = int(time.time() * 1e3)
        valid_image, image = cap_handle.read()
        t1 = int(time.time() * 1e3)
        logging.info('Read image in {} milli-seconds'.format(t1-t0))
 
        if valid_image:
            image_flat = image.reshape(( FRAME_HEIGHT * FRAME_WIDTH * 3), 1)
            # Doing the (t1-t0)/8 to fit the time delta between frames into a uint8. Need to find a better method
            tmp_array = np.array([NPY_FILE_FORMAT, np.uint8((t1-t0)/10)], dtype=np.uint8)
            single_img_array = np.append(tmp_array, image_flat)
            np_images[0] = single_img_array
            logging.info('Added image {} to numpy array'.format(i))
        else:
            raise RuntimeError('Valid image not read from camera. Exiting')
            cleanup(cap_handle)
            sys.exit()

    logging.info('Saving array to file: {}'.format(filename))
    np.save(filename, np_images)

def main():
    ''' Read from cam and write to file. Also exit on Ctrl-C '''
    try:
        cap_handle = init_cam()
        # cap_handle = None
        # Get a new file to write to
        filename = get_fn_with_ts()
        read_n_write_frames(cap_handle, filename)
        # Release the file
        cap_handle.release()
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Exiting . . . ')
        cleanup(cap_handle)

if __name__ == '__main__':
    main() 

