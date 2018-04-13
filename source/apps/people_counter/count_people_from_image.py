#! /usr/bin/env python
''' The purpose of this program is quite simple: given an image, count the
    number of people in it and return count, confidence & x/y location if
    a person is found '''

import argparse
import glob
import cv2
import os
import sys
import logging
from timeit import default_timer
import numpy as np

# Set logging level
logging.basicConfig(level=logging.INFO)

class person_id_info():
    def __init__(self, args):
        self.image_file = os.path.abspath(args['image'])
        self.confidence = args['confidence']
        # previous_det is a stupid hack. See explanation below
        self.previous_det = np.array([[[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]]])
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
        self.person_idx = self.classes.index('person')

    def set_model(self, model_net):
         self.net = model_net

# This is only if this is used as a main program
def parse_args():
    ''' Parse the arguments and return a dict '''
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True,
            help="path to input image")
    ap.add_argument("-c", "--confidence", type=float, default=0.2,
            help="minimum probability to filter weak detections")
    args = vars(ap.parse_args())
    return args

def load_dnn_model(pi_obj):
    ''' Load a model and weights. Currently hard coded to MobileNet SSD '''
    logging.info("Loading model...")
    net = cv2.dnn.readNetFromCaffe(pi_obj.prototxt_file, pi_obj.model_file)
    pi_obj.set_model(net)

def load_image(pi_obj):
    logging.info('Loading image: {}'.format(pi_obj.image_file))
    image = cv2.imread(pi_obj.image_file)
    return image


def process_detections(pi_obj, image, detections, display_predictions = False):
    ''' Go over each object detected and if its a person, return the
        (x,y) locations '''

    person_list = []
    min_conf = pi_obj.confidence
    (h, w) = image.shape[:2]

    # loop over the detections
    for i in np.arange(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the
            # prediction
            confidence = detections[0, 0, i, 2]
            # extract the index of the class label from the `detections`
            idx = int(detections[0, 0, i, 1])

            # filter out weak detections by ensuring the `confidence` is
            # greater than the minimum confidence
            if confidence > min_conf:
                # Compute the (x, y)-coordinates of the bounding box 
                # for the object
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # Process detection if its a person
                if idx == pi_obj.person_idx:
                    label = "{}".format(pi_obj.classes[idx])
                    person_info = {
                        'found'      : label, 
                        'confidence' : float(confidence),
                        'startX'     : int(startX),
                        'startY'     : int(startY),
                        'endX'       : int(endX),
                        'endY'       : int(endY) }
                    person_list.append(person_info)

                # If requested to superimpose ided objects to image, do it
                if display_predictions:
                    # display the prediction
                    label = "{}: {:.2f}%".format(pi_obj.classes[idx],
                                                               confidence*100)
                    logging.info("Found {}".format(label))
                    cv2.rectangle(image, (startX, startY), (endX, endY),
                                                        pi_obj.colors[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(image, label, (startX, y),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, pi_obj.colors[idx], 2)

    return person_list

def id_people(pi_obj, image, display_predictions = False):
    ''' Load the image and id any people in it '''
    # (h, w) = image.shape[:2]
    # Construct an input blob for the image
    # by resizing to a fixed 300x300 pixels and then normalizing it
    # (note: normalization is done via the authors of the MobileNet SSD
    # implementation)
    start_t = default_timer()
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)),
                                             0.007843, (300, 300), 127.5)
    # pass the blob through the network and obtain the detections and
    # predictions
    logging.info("Computing object detections...")
    pi_obj.net.setInput(blob)
    detections = pi_obj.net.forward()

    # This is a stupid hack. For some reason, net.forward returns previously 
    # detected objects if image is a blank image. Don't know why. Fix later
    if np.array_equal(detections, pi_obj.previous_det):
        logging.info('No image found. IDed in {} seconds'
                                        .format(int(default_timer()-start_t)))
        # Return an empty list in this case
        return []
    else:
        pi_obj.previous_det = detections
        ided_persons = process_detections(pi_obj, image, detections, 
                                                          display_predictions)
        logging.info('Imaged IDed in {} seconds'
                                        .format(int(default_timer()-start_t)))
        return ided_persons

if __name__ == '__main__':
    # This is for testing only. This is supposed to be used as a module
    pi_obj = person_id_info(parse_args())

    # load our serialized model from disk
    load_dnn_model(pi_obj)

    # load the image
    image = load_image(pi_obj)

    ided_persons = id_people(pi_obj, image)

    if len(ided_persons) > 0:
        for person in ided_persons:
            logging.info(person)
    else:
        logging.info(' ----------- No people IDed in image -----------------')
