#! /usr/bin/env python
''' Given an URL, keep getting image from it, detect if there are any person(s)
    in the image and feed the results to kafka '''

# Python lib imports
from __future__ import print_function

import argparse
import glob
import cv2
import os
import sys
import json
import time
import yaml
import logging

# Constants
WRITE_FN_BASE = os.path.join(os.path.expanduser("~"), 'archimedes_cam_{}.mjpg')
# WRITE_FN_BASE = os.path.join(os.path.expanduser("~"), 'archimedes_cam_{}.xvid')
# WRITE_FN_BASE = os.path.join(os.path.expanduser("~"), 'archimedes_cam_{}.dvix')

FPS = 10
FRAME_HEIGHT = 1536
FRAME_WIDTH = 2304
NUM_FRAMES_TO_WRITE = 100

CAM_URL = 'something.com/api/bmp'
CAM_NUM = 0

def get_fn_with_ts():
    ''' Add timestamp in epoch to WRITE_FN_BASE and return it '''
    now_time = time.time()
    time_in_secs = int(now_time)
    return WRITE_FN_BASE.format(time_in_secs)

def init_cam():
    ''' Connect to the camera '''
    print('Connecting to camera')
    cap_handle = cv2.VideoCapture(CAM_NUM)
    return cap_handle

def set_videowriter():
    ''' Set videowriter with current time as file timestamp'''
    img_write_fn = get_fn_with_ts()
    print('Setting image file write to: {}'.format(img_write_fn))
    video_writer = cv2.VideoWriter(img_write_fn,
                                 # cv2.VideoWriter_fourcc('X','V','I','D'), 
                                 cv2.VideoWriter_fourcc('M','J','P','G'), 
                                 # cv2.VideoWriter_fourcc('D','V','I','X'), 
                                 FPS, (FRAME_WIDTH,FRAME_HEIGHT))
    return video_writer

def read_write_n_frames(cap_handle, video_writer, nframes = NUM_FRAMES_TO_WRITE):
    ''' Read fro mcam and write n frames to the specified videowriter '''
    for i in range(nframes):
        t0 = time.time()
        valid_image, image = cap_handle.read()
        t1 = time.time()
        print('Read took {0:.2f} secs'.format(t1 - t0))
        if valid_image:
            print('Writing {}-th image of size: {}'.format(i, image.shape))
            video_writer.write(image)

def main():
    ''' Read from cam and write to file. Also exit on Ctrl-C '''
    try:
        # Get a new file to write to
        cap_handle = init_cam()
        # print('Width: {}'.format(cap_handle.get(3)))
        # print('Height: {}'.format(cap_handle.get(4)))
        video_writer = set_videowriter()
        read_write_n_frames(cap_handle, video_writer)
        # Release the file
        video_writer.release()
        cap_handle.release()
    except KeyboardInterrupt:
        print('Received Ctrl-C. Exiting . . . ')
        cap_handle.release()
        video_writer.release()

if __name__ == '__main__':
    main() 

