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
# import count_people_from_image as cp
import load_app_configs as lc

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

# This is only if this is used as a main program
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

def send_message(message, kf_obj):
    ''' Send message to kafka topic '''
    # print(message)
    # The .encode is to convert str to bytes (utf-8 is default)
    kf_obj.producer.send(KAFKA_TOPIC, message.encode(), partition = 0)

######### OBSOLETE during next refactor ##############
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

first_frame = None
def count_people(pc):
    ''' Load image from the cameras, count number of persons in it
        and feed kafka with the results '''

    global first_frame
    # Go through each camera and count the number of people in them
    for cam_name in pc.all_cams_config.all_cams_name:
        print(cam_name)
        cam_obj = pc.all_cams_config.cam_config[cam_name]
        valid_image, image = cam_obj.cap_handle.read()

        if valid_image:
            ############### GG Expts ############################
            image_copy = image.copy()
            image_copy2 = image.copy()
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            # If first frame not grabbed, please do so now
            if first_frame is None:
                first_frame = gray
                continue

            # compute the absolute difference between the current frame and
            # first frame
            frameDelta = cv2.absdiff(first_frame, gray)

            # Subtract the background
            bgsub_img = cam_obj.bgsub.apply(gray)
            # Gaussian blur to background subtracted image
            # bgsub_gray = cv2.GaussianBlur(bgsub_img, (21, 21), 0)

            thresh = cv2.threshold(bgsub_img, 25, 255, cv2.THRESH_BINARY)[1]
            # dilate the thresholded image to fill in holes, then find contours
            # on thresholded image
            dilated = cv2.dilate(thresh, None, iterations=2)
            # Find the countours of this processed frame
            _, cnts, _ = cv2.findContours(dilated.copy(), 
                                    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # loop over the contours
            for c in cnts:
                # if the contour is too small, ignore it
                if cv2.contourArea(c) < 12000:
                    continue
                # compute the bounding box for the contour, 
                # draw it on the frame,and update the text
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(image_copy, (x, y),(x + w, y + h), (0, 255, 0), 2)
                rectangleCenterPont = (int((x + x + w) /2), int((y + y + h) /2))
                cv2.circle(image_copy, rectangleCenterPont, 1, (0, 0, 255), 5)
            ############### End GG Expts ############################


            # Write image to file if requested. Note here that the image
            # is written is as captured from cam (i.e. not annonated)
            if cam_obj.videowriter:
                cam_obj.videowriter.write(image)
            ided_persons = pc_utils.id_people(pc, image, 
                                           cam_obj.display_predictions)
            # Show image if requested.
            if cam_obj.display_image:
                ############### GG Expts ############################
                gray_name = '{}-{}'.format(cam_name, 'gray')
                cv2.namedWindow(gray_name)
                cv2.moveWindow(gray_name, 0, 0)
                cv2.imshow(gray_name, pc_utils.resize_half(gray))
                # delta_name = '{}-{}'.format(cam_name, 'delta')
                # cv2.namedWindow(delta_name)
                # cv2.imshow(delta_name, frameDelta)
                bg_sub_name = '{}-{}'.format(cam_name, 'bg_sub_name')
                cv2.namedWindow(bg_sub_name)
                cv2.moveWindow(bg_sub_name, 640, 0)
                cv2.imshow(bg_sub_name, pc_utils.resize_half(bgsub_img))
                tresh_name = '{}-{}'.format(cam_name, 'tresh')
                cv2.moveWindow(tresh_name, 1280, 0)
                cv2.namedWindow(tresh_name)
                cv2.imshow(tresh_name, pc_utils.resize_half(thresh))
                dilated_name = '{}-{}'.format(cam_name, 'dilated')
                cv2.namedWindow(dilated_name)
                cv2.moveWindow(dilated_name, 1920, 0)
                cv2.imshow(dilated_name, pc_utils.resize_half(dilated))
                copy_image_name = '{}-{}'.format(cam_name, 'copy')
                cv2.namedWindow(copy_image_name)
                cv2.moveWindow(copy_image_name, 640, 580)
                cv2.imshow(copy_image_name, pc_utils.resize_half(image_copy))
                ############### End GG Expts ############################
                # cv2.moveWindow(gray_name, 500, 0)
                # cv2.imshow(cam_name, cv2.resize(image, (960,540)))
                cv2.namedWindow(cam_name)
                cv2.moveWindow(cam_name, 0, 580)
                cv2.imshow(cam_name, pc_utils.resize_half(image))
                if cam_obj.display_gait:
                    # Get gaited image
                    humans = gait.get_humans(pc.gait_config, image_copy2)
                    gait_image = gait.draw_gait(image_copy, humans)
                    gait_window = '{}-{}'.format(cam_name, 'gait')
                    cv2.namedWindow(gait_window)
                    cv2.moveWindow(gait_window, 1280, 580)
                    cv2.imshow(gait_window, pc_utils.resize_half(gait_image))
                cv2.waitKey(1)

            # If person(s) have been detected in this image, 
            # feed the results to kafka
            if len(ided_persons) > 0:
                logging.info('Person(s) detected in image')
                for person in ided_persons:
                    timenow_secs = time.time()
                    person['detect_time'] = timenow_secs
                    # person['stream_name'] = pc.stream_name
                    # tmp for now
                    person['stream_name'] = 'Aruba_SLR01_Cams'
                    person['msg_format_version'] = pc.msg_format_ver
                    logging.info(person)
                    person_json = json.dumps(dict(person))
                    # send_message(person_json, pc)
            else:
                logging.info('No people IDed in image')
        else:
            # If image read failed, log error
            logging.error('Image read from camera {} failed.(error ret = {}'
                                                .format(cam_name, valid_image))

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
    args = parse_args()
    co = lc.config_obj(args)
    print('Dim')
    print(co.kafka_config.kafka_broker_hostname)
    sys.exit()
    # ------ Connect to camera
    co.connect_all_cams()
    # ------ load our serialized model from disk (this can be part of init itself)
    # pc.load_dnn_model()
    # ------ Do the main loop
    # main_loop(pc)
    # ------ Do the main loop
    co.release_all_cams()
    cleanup()

