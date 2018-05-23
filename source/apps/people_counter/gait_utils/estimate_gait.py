#! /usr/bin/env python
'''
All code is highly based on Ildoo Kim's code (https://github.com/ildoonet/tf-openpose)
and derived from the OpenPose Library (https://github.com/CMU-Perceptual-Computing-Lab/openpose/blob/master/LICENSE)
'''

import cv2
import yaml
import argparse
import sys
import logging

import tensorflow as tf
import numpy as np

from tensorflow.core.framework import graph_pb2

# Local imports
# from common import estimate_pose, draw_humans, read_imgfile, preprocess
from .common import estimate_pose, draw_humans, read_imgfile, preprocess

import time

# Constants
TEST_MJPEG_FN ='/home/ggopalan/data/videos/aruba_cams/slr01_bldg_d_f1_elevators_save1.mjpg'
TEST_IMAGE_FN = '/home/ggopalan/data/images/gait_image1.jpg'
WINDOW_NAME = 'Test'
DEF_WIDTH = 656
DEF_HEIGHT = 368

# Set logging level
logging.basicConfig(level=logging.INFO)

class gait_config():
    ''' Object that holds all info needed for gait estimation '''
    def __init__(self, gait_init_fn = './gait_config.yml'):
        # Open and load the gait config file
        with open(gait_init_fn) as gfh:
            gait_config_dict = yaml.load(gfh)
        self.models = gait_config_dict['models']
        self._init_tf()

    def _init_tf(self):
        ''' Init tensoflow model '''
        tf.reset_default_graph()
        self.gait_graph = graph_pb2.GraphDef()

        # Load the openpose model
        with open(self.models['openpose_model'], 'rb') as fh:
            self.gait_graph.ParseFromString(fh.read())
        tf.import_graph_def(self.gait_graph, name='')
        logging.info('OpenPose model loading complete')

        # Load heatmap & pafs tensors
        self.inputs = tf.get_default_graph().get_tensor_by_name('inputs:0')
        self.heatmaps_tensor = tf.get_default_graph().get_tensor_by_name(
                                                 'Mconv7_stage6_L2/BiasAdd:0')
        self.pafs_tensor = tf.get_default_graph().get_tensor_by_name(
                                                 'Mconv7_stage6_L1/BiasAdd:0')
        logging.info('Heatmap and PAF tensors loaded')

def get_humans(gc, image):
    ''' From image, estimate humans and return it '''
    # Preprocess image
    # TBD: Look into why we need DEF_WIDTH/HEIGHT
    prep_image = preprocess(image, DEF_WIDTH, DEF_HEIGHT)

    # Get Heat matrix and PAFS matrix
    t0 = time.time()
    with tf.Session() as sess:
        heatMat, pafMat = sess.run([gc.heatmaps_tensor, gc.pafs_tensor], 
                                           feed_dict={gc.inputs: prep_image})
        t1 = time.time()
        logging.info('Heat matrix and PAFS matrix calculated in {} secs'
                                                              .format(t1-t0))
        heatMat, pafMat = heatMat[0], pafMat[0]
        humans = estimate_pose(heatMat, pafMat)
        t2 = time.time()
        logging.info('Pose estimated in in {} secs'.format(t2-t1))
    return humans

def draw_gait(image, humans):
    ''' Draw gait onto image using the humans data and return it '''
    return draw_humans(image, humans)


if __name__ == '__main__':
    '''
    parser = argparse.ArgumentParser(description='Tensorflow Openpose Inference')
    parser.add_argument('--imgpath', type=str, default='./images/wywh.jpg')
    parser.add_argument('--input-width', type=int, default=656)
    parser.add_argument('--input-height', type=int, default=368)
    args = parser.parse_args()



    t3 = time.time()
    with tf.Session() as sess:
        heatMat, pafMat = sess.run([heatmaps_tensor, pafs_tensor], 
                                    feed_dict={inputs: prep_image})

        t4 = time.time()
        print('Gotched heatmaps and pafs in {} secs'.format(t4-t3))

        heatMat, pafMat = heatMat[0], pafMat[0]
        humans = estimate_pose(heatMat, pafMat)

        # display
        # image = cv2.imread(args.imgpath)
        image_h, image_w = image.shape[:2]
        image = draw_humans(image, humans)

        scale = 480.0 / image_h
        newh, neww = 480, int(scale * image_w + 0.5)

        image = cv2.resize(image, (neww, newh), 
                                   interpolation=cv2.INTER_AREA)

        print('Yay! Done')
        cv2.imshow(WINDOW_NAME, image)
        t5 = time.time()
        print('Processed and showed image in {} secs'.format(t5-t4))
        cv2.waitKey(1)

    '''
    gc = gait_config()
    image = cv2.imread(TEST_IMAGE_FN, cv2.IMREAD_COLOR)

    # get the humans in the image
    humans = get_humans(gc, image)
    print(type(humans))
    print(len(humans))
    # print(humans)

    gait_image = draw_gait(image, humans)

    cv2.imshow('Original', image)
    cv2.imshow('Gaited', gait_image)
    cv2.waitKey(10000)
    cv2.destroyAllWindows()
