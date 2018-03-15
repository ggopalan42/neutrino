#! /usr/bin/env python
''' Given an URL, keep getting image from it, detect if there are any person(s)
    in the image and feed the results to kafka '''

import argparse
import glob
import cv2
import os
import sys
import json
import time
import urllib.request
import count_people_fom_image as cp
import numpy as np
from kafka import KafkaProducer

KAFKA_BROKER = '10.2.13.29'
KAFKA_PORT = '9092'
KAFKA_TOPIC = 'peoplecounter1'

class people_count_url():
    def __init__(self, args):
        self.url = args['url']
        self.confidence = args['confidence']
        self.stream_name = args['name']
        # Currently using the Mobilenet SSD models. Later make this
        # stuff more dynamic
        self.prototxt_file = './models/MobileNetSSD_deploy.prototxt.txt'
        self.model_file = './models/MobileNetSSD_deploy.caffemodel'
        self.classes = ["background", "aeroplane", "bicycle", "bird", "boat",
                "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                "sofa", "train", "tvmonitor"]
        self.person_idx = self.classes.index('person')
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3)) 
        self.producer=KafkaProducer(bootstrap_servers=
                                   '{}:{}'.format(KAFKA_BROKER, KAFKA_PORT))
        # Again, specifying format ver below here is non ideal
        self.msg_format_ver = '1.0.0'


    def set_model(self, model_net):
         self.net = model_net

# This is only if this is used as a main program
def parse_args():
    ''' Parse the arguments and return a dict '''
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--url", required=True,
            help="URL to image")
    ap.add_argument("-n", "--name", required=True,
            help="Name for this kafak stream")
    ap.add_argument("-c", "--confidence", type=float, default=0.2,
            help="minimum probability to filter weak detections")
    args = vars(ap.parse_args())
    return args

def send_message(message, kf_obj):
    ''' Send message to kafka topic '''
    # print(message)
    # The .encode is to convert str to bytes (utf-8 is default)
    kf_obj.producer.send(KAFKA_TOPIC, message.encode(), partition = 0)

def load_dnn_model(pcu):
    ''' Load a model and weights. Currently hard coded to MobileNet SSD '''
    print("Loading model...")
    net = cv2.dnn.readNetFromCaffe(pcu.prototxt_file, pcu.model_file)
    pcu.set_model(net)

def url_to_image(pcu):
    ''' download the image, convert it to a NumPy array, and then read
        it into OpenCV format '''
    resp = urllib.request.urlopen(pcu.url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image

def count_people_feed_kafka(pcu):
    ''' Load image from the URL, count number of persons in it
        and feed kafka with the results '''

    # Fetch an image
    image = url_to_image(pcu)
    ided_persons = cp.id_people(pcu, image)

    # If person(s) have been detected in this image, feed the results to kafka
    if len(ided_persons) > 0:
        print('Person(s) detected in image')
        for person in ided_persons:
            timenow_secs = time.time()
            person['detect_time'] = timenow_secs
            person['stream_name'] = pcu.stream_name
            person['msg_format_version'] = pcu.msg_format_ver
            print(person)
            person_json = json.dumps(dict(person))
            send_message(person_json, pcu)
    else:
        print('No people IDed in image')

def main_loop(pcu):
    ''' Continously detect persons and quit on keyboard interrupt '''
    try:
        while True:
            count_people_feed_kafka(pcu)
    except KeyboardInterrupt:
        print('Received Ctrl-C. Exiting . . . ')
        return ['Keyboard Interrupt']

if __name__ == '__main__':
    # Initialize
    pcu = people_count_url(parse_args())
    # load our serialized model from disk
    load_dnn_model(pcu)
    # Do the main loop
    main_loop(pcu)

