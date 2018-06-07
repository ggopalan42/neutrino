#! /usr/bin/env python
''' Given an URL, keep getting image from it, detect if there are any person(s)
    in the image and feed the results to kafka '''

# Python lib imports
import cv2
import os
import sys
import time
import numpy as np

READ_FILE_FN = '/home/ggopalan/projects/apps/people_counter/video_save/slr01_bldg_d_f1_rear_lobby_entrance_save1.mjpg'

def read_n_show(cap_handle):
    ''' Load image from cap_handleand show it '''

    while True:
        valid_image, image = cap_handle.read()

        if valid_image:
            print('Read frame successfully. Frame size: {}'.format(image.shape))
            cv2.imshow('Video', image)
            cv2.waitKey(1)

def cleanup(cap_handle):
    ''' Cleanup before exiting '''
    cap_handle.release()
    cv2.destroyAllWindows()

def main(cap_handle):
    ''' Read from file and show image '''
    try:
        read_n_show(cap_handle)
    except KeyboardInterrupt:
        print('Got keyboard interrupt. Exiting . .  .')
        cleanup(cap_handle)

if __name__ == '__main__':
    # Do the main loop
    cap_handle = cv2.VideoCapture(READ_FILE_FN)
    main(cap_handle)
    cleanup(cap_handle)

