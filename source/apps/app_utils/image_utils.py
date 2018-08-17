#!/usr/bin/env python
''' Utilities for People Counter application '''

import cv2
import numpy as np

def resize_half(image):
    ''' Resizes any image given to it by half '''
    img_half_h = int(image.shape[0]/2)
    img_half_w = int(image.shape[1]/2)
    return cv2.resize(image, (img_half_w, img_half_h))

def resize_qtr(image):
    ''' Resizes any image given to it by half '''
    img_half_h = int(image.shape[0]/4)
    img_half_w = int(image.shape[1]/4)
    return cv2.resize(image, (img_half_w, img_half_h))

def cleanup(co):
    ''' Cleanup before exiting '''
    cv2.destroyAllWindows()
    # Should anything be released on kafka and others?

if __name__ == '__main__':
    # Write tests here
    pass
