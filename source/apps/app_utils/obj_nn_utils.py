#!/usr/bin/env python
''' Utilities for People Counter application '''

import sys
import cv2
import time
import logging

import numpy as np

def format_message(co, det_obj_list, stream_name, message_version):
    ''' Format a message in the expected format ready for sending to kafka. '''
    # Return formated message as a dict. Upto the requester how its converted
    kafka_message_dict = {}
    # Setup base message
    timenow_secs = time.time()
    kafka_message_dict['detect_time'] = int(timenow_secs * 1e6) # ts is in us
    kafka_message_dict['stream_name'] = stream_name
    kafka_message_dict['msg_format_version'] = message_version
    kafka_message_dict['objects_list'] = det_obj_list
    return kafka_message_dict
 
# Below is lazy implementation of process_object_detections.
# Refactor when I'm feeling like it
def process_object_detections(model_obj, image, detections, 
                                               display_predictions = False):
    ''' Go over each object detected and return the (x,y) locations '''

    objects_list = []
    min_conf = model_obj.min_confidence
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

                label = "{}".format(model_obj.classes[idx])
                object_info = {  
                    'found'      : label, 
                    'confidence' : float(confidence),
                    'startX'     : int(startX),
                    'startY'     : int(startY),
                    'endX'       : int(endX),
                    'endY'       : int(endY) }
                objects_list.append(object_info)

                # If requested to superimpose ided objects to image, do it
                if display_predictions:
                    # display the prediction
                    label = "{}: {:.2f}%".format(model_obj.classes[idx],
                                                               confidence*100)
                    logging.info("Found {}".format(label))
                    cv2.rectangle(image, (startX, startY), (endX, endY),
                                                      model_obj.colors[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(image, label, (startX, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, model_obj.colors[idx], 2)
    return objects_list


# Below is lazy implementation of id_objects.
# Refactor when I'm feeling like it
def id_objects(co, image, model_obj, display_predictions = False):
    ''' Load the image and id any people in it '''
    # Construct an input blob for the image
    # by resizing to a fixed 300x300 pixels and then normalizing it
    # (note: normalization is done via the authors of the MobileNet SSD
    # implementation)
    start_t = time.time()
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)),
                                             0.007843, (300, 300), 127.5)
    # pass the blob through the network and obtain the detections and
    # predictions
    logging.info("Computing object detections...")
    model_obj.net.setInput(blob)
    detections = model_obj.net.forward()

    # This is a stupid hack. For some reason, net.forward returns previously 
    # detected objects if image is a blank image. Don't know why. Fix later
    if np.array_equal(detections, model_obj.previous_det):
        logging.info('No image found. IDed in {} seconds'
                                        .format(int(time.time()-start_t)))
        # Return an empty list in this case
        return []
    else:
        model_obj.previous_det = detections
        ided_objects = process_object_detections(model_obj, image, detections,
                                                          display_predictions)
        logging.info('Imaged IDed in {} seconds'
                                        .format(int(time.time()-start_t)))
        return ided_objects

def process_person_detections(model_obj, image, detections, 
                                               display_predictions = False):
    ''' Go over each object detected and if its a person, return the
        (x,y) locations '''

    person_list = []
    min_conf = model_obj.min_confidence
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
                if idx == model_obj.person_idx:
                    label = "{}".format(model_obj.classes[idx])
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
                    label = "{}: {:.2f}%".format(model_obj.classes[idx],
                                                               confidence*100)
                    logging.info("Found {}".format(label))
                    cv2.rectangle(image, (startX, startY), (endX, endY),
                                                      model_obj.colors[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(image, label, (startX, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, model_obj.colors[idx], 2)
    return person_list


def id_people(co, image, model_obj, display_predictions = False):
    ''' Load the image and id any people in it '''
    # Construct an input blob for the image
    # by resizing to a fixed 300x300 pixels and then normalizing it
    # (note: normalization is done via the authors of the MobileNet SSD
    # implementation)
    start_t = time.time()
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)),
                                             0.007843, (300, 300), 127.5)
    # pass the blob through the network and obtain the detections and
    # predictions
    logging.info("Computing object detections...")
    model_obj.net.setInput(blob)
    detections = model_obj.net.forward()

    # This is a stupid hack. For some reason, net.forward returns previously 
    # detected objects if image is a blank image. Don't know why. Fix later
    if np.array_equal(detections, model_obj.previous_det):
        logging.info('No image found. IDed in {} seconds'
                                        .format(int(time.time()-start_t)))
        # Return an empty list in this case
        return []
    else:
        model_obj.previous_det = detections
        ided_persons = process_person_detections(model_obj, image, detections,
                                                          display_predictions)
        logging.info('Imaged IDed in {} seconds'
                                        .format(int(time.time()-start_t)))
        return ided_persons

if __name__ == '__main__':
    # mostly for testing
    CAM_CONFIG_YAML_FILE = 'pc_aruba_slr01_cams.yml'
    PC_CONFIG_YAML_FILE = 'pc_config.yml'

    with open(CAM_CONFIG_YAML_FILE) as kfh:
        cam_config_yaml = yaml.load(kfh)
    cc = all_cams_config(cam_config_yaml)
    for cam in cc.all_cams_name:
        cam_obj = cc.cam_config[cam]
        logging.info(cam_obj.cam_name, cam_obj.cam_user)
        logging.info(cam_obj.cam_url)

    with open(PC_CONFIG_YAML_FILE) as pcfh:
        pc_config_yaml = yaml.load(pcfh)

    pcc = pc_config(pc_config_yaml)
    logging.info(pcc.confidence)

