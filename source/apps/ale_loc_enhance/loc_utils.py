#!/usr/bin/env python
''' Utilities for People Counter application '''

import base64
import sys
import yaml
import cv2
import logging
import os

from timeit import default_timer
from kafka import KafkaProducer
import numpy as np

# Config files (probably a good idea to move all config files to a single dir)
CONFIG_BASE = './configs'

class loc_config():
    ''' Object that holds all location specific paramaters '''
    def __init__(self, args):
        # Load all configs
        self.args = args
        self._load_configs(args)

        # previous_det is a stupid hack. See explanation below
        self.previous_det = np.array([[[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]]])
        # Not too sure if below should go into a YAML file somewhere
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3))

    # Private methods
    def _load_configs(self, args):
        ''' Load all needed configs '''
        loc_yaml_fn = args['config']

        # Set loc config
        with open(loc_yaml_fn) as locfh:
            loc_config_dict = yaml.load(locfh)
        # Set default params
        default_params = loc_config_dict['default_params']
        self.msg_format_ver = ['kafka_msg_format_ver']
        # Set kafka params
        kafka_params = loc_config_dict['kafka']
        self.kafka_broker_hostname = kafka_params['kafka_broker_hostname']
        self.kafka_broker_port = kafka_params['kafka_broker_port']
        self.producer=KafkaProducer(bootstrap_servers= '{}:{}'.format(
                                    self.kafka_broker_hostname,
                                    self.kafka_broker_port))
        # Load ALE params
        ale_params = loc_config_dict['ale_params']
        self.ale_rem_hostname: ale_params['ale_rem_hostname'] 
        self.ale_rem_port: ale_params['ale_rem_port'] 
        # Load Cams config
        cams_config = loc_config_dict['cams_config']
        self._load_cams_config(cams_config)
        dnn_configs = loc_config_dict['ml_config']
        self._load_dnn_configs(dnn_configs)

    def _load_cams_config(self, cams_config):
        ''' Load the camera configs '''
        # For now, simply load a single cam config yaml file. Later
        # expand to multiple cams
        cam_yaml_fn = os.path.join(CONFIG_BASE,cams_config['cams_config_fn'][0])
        with open(cam_yaml_fn) as cfh:
            cam_config_dict = yaml.load(cfh)
        self.all_cams_config = all_cams_config(cam_config_dict)

    def _load_dnn_configs(self, dnn_configs):
        ''' Load configs for various models '''
        obj_det_models = dnn_configs['obj_det_model_configs']
        # Again, for now, load only the single model config. Later
        # expand to multiple models
        mobilenet_ssd_v1_fn = os.path.join(CONFIG_BASE, 
                                 obj_det_models[0]['mobilenet_ssd_v1_fn'])
        print(mobilenet_ssd_v1_fn)
        with open(mobilenet_ssd_v1_fn) as mfh:
            ssd_config_dict = yaml.load(mfh)
        model = ssd_config_dict['model']
        self.model_file = model['model_file']
        self.prototxt_file = model['prototxt_file']
        self.classes = model['model_params']['object_classes'].split()
        # Again, below is using only first element. Later expand to a list
        self.person_idx = self.classes.index(model['object_filter'][0])
        self.confidence = model['model_params']['confidence']

   # Public methods
    def load_dnn_model(self):
        ''' Load a model and weights. Currently hard coded to MobileNet SSD '''
        logging.info('Loading model: {}'.format(self.model_file))
        self.net = cv2.dnn.readNetFromCaffe(self.prototxt_file, self.model_file)

    def connect_all_cams(self):
        ''' Connect to all specified cameras '''
        # Go through all cameras and connect to them
        # I know, this for loop can simply be done as: 
        # for cam_obj in self.all_cams_config.cam_config. 
        # But wanted to do it in order. 
        # But again I know, I could have used ordered dict . . .
        for cam_name in self.all_cams_config.all_cams_name:
            # logging.info('Connecting to camera: {}'.format(cam_name))
            cam_obj = self.all_cams_config.cam_config[cam_name]
            cam_obj.connect_to_cam()

    def release_all_cams(self):
        ''' Release all cameras' resources '''
        # Go through all cameras and connect to them
        for cam_name in self.all_cams_config.all_cams_name:
            logging.info('Releasing camera: {}'.format(cam_name))
            cam_obj = self.all_cams_config.cam_config[cam_name]
            cam_obj.cam_release()

class single_cam_config():
    ''' Object that holds the config and methods of one camera '''
    def __init__(self, cam_dict, default_creds):
        # Unfurl all of this cam's config.
        # And surely there is a better way to do this doc?
        cam_name = list(cam_dict.keys())[0]
        self.cam_name = cam_name
        self.valid = cam_dict[cam_name]['valid']
        self.display_name = cam_dict[cam_name]['display_name']
        self.description = cam_dict[cam_name]['description']
        self.cam_type = cam_dict[cam_name]['cam_type']
        self.cam_proto = cam_dict[cam_name]['cam_proto']
        self.cam_hostname = cam_dict[cam_name]['cam_hostname']
        self.cam_uri = cam_dict[cam_name]['cam_uri']
        self.cam_creds = cam_dict[cam_name]['cam_creds']  ###
        self.display_image = cam_dict[cam_name]['display_image']
        self.display_predictions = cam_dict[cam_name]['display_predictions']
        self.kafka_topic = cam_dict[cam_name]['kafka_topic']
        self.kafka_partition = cam_dict[cam_name]['kafka_partition']  ###
        self.kafka_key = cam_dict[cam_name]['kafka_key']
        self.write_to_file = cam_dict[cam_name]['write_to_file']     \
                          if 'write_to_file' in cam_dict[cam_name] else False
        self.read_from_file = cam_dict[cam_name]['read_from_file']     \
                          if 'read_from_file' in cam_dict[cam_name] else False
        self._set_creds(cam_dict[cam_name]['cam_creds'], default_creds)
        self._set_cam_url()

    def _set_aruba_axis1_creds(self, default_creds):
        ''' Set the user and pw for aruba_axis1 cred type '''
        self.cam_user = default_creds['aruba_axis1']['user']
        if default_creds['aruba_axis1']['enc_type'] == 'base64':
            b64_pw = default_creds['aruba_axis1']['pw']
            self.cam_pw = base64.b64decode(b64_pw).decode('utf-8')
        else:
            logging.warning('Unsupported enc_type. Setting password to None')
            self.cam_pw = None

    def _set_creds(self, cam_creds, default_creds):
        ''' Set the user and pw credentials of the camera '''
        # Cred type to cred function map
        cred_func_map = {'aruba_axis1': self._set_aruba_axis1_creds }
        if cam_creds:    # If cred method is specified
            cred_func_map[cam_creds](default_creds)
        else:
            logging.warning('Creds not specified. Setting them to None')
            self.cam_user = None
            self.cam_pw = None

    def _set_cam_url(self):
        ''' Set the full camera URL from all other fields '''
        self.cam_url = '{}://{}:{}@{}/{}'.format(self.cam_proto, self.cam_user,
                                  self.cam_pw, self.cam_hostname, self.cam_uri)

    def set_videowriter(self):
        ''' Set video write handler '''
        if self.write_to_file:
            logging.info('Setting video writer handle for cam {}'
                                                     .format(self.cam_name))
            self.videowriter = cv2.VideoWriter(self.write_to_file,
                                 cv2.VideoWriter_fourcc('M','J','P','G'), 
                                 self.cap_frame_fps,
                                 (self.cap_fwidth,self.cap_fheight))
        else:
            self.videowriter = False


    def connect_to_cam(self):
        ''' Connect to the camera URL or read from file if so specified '''
        if self.read_from_file:
            logging.info('Reading from file: {}. (Cam name: {})'
                               .format(self.read_from_file, self.cam_name))
            self.cap_handle = cv2.VideoCapture(self.read_from_file)
        else:
            logging.info('Connecting to camera: {}'.format(self.cam_name))
            self.cap_handle = cv2.VideoCapture(self.cam_url)
        # Once connected, set a few useful camera props
        self.cap_fwidth = int(self.cap_handle.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cap_fheight = int(self.cap_handle.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cap_frame_fps = int(self.cap_handle.get(cv2.CAP_PROP_FPS))
        # After connecting, call set videowriter
        # Its a little weird to do it at this stage
        # but a few params (like video height & width) are needed for video
        # writer. So it needs to be done only after connecting
        self.set_videowriter()
        # And also set the background subtractor object
        self.bgsub = cv2.createBackgroundSubtractorMOG2(detectShadows = True)


    def cam_release(self):
        ''' Release the camera resources '''
        self.cap_handle.release()

class all_cams_config():
    ''' This class holds the configs and defaults of all cameras '''
    def __init__(self, cfg_yaml_dict):
        self.cam_config = {}
        self.all_cams_name = []
        self.cam_config_dict = cfg_yaml_dict['cams']
        # Set all of the default creds
        self.default_creds = cfg_yaml_dict['defaults']['creds']
        # Now setup all of the cams with their params
        self._setup_all_cam_configs()

    # Private methods
    def _setup_all_cam_configs(self):
        for cam in self.cam_config_dict:
            cam_name = list(cam.keys())[0]
            # Only set single cam configs if valid field is set to True
            if cam[cam_name]['valid']:
                self.all_cams_name.append(cam_name)
                cam_obj = single_cam_config(cam, self.default_creds)
                self.cam_config[cam_name] = cam_obj

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
    # mostly for testing
    ''' Needs fixin'
    CAM_CONFIG_YAML_FILE = 'pc_aruba_slr01_cams.yml'
    PC_CONFIG_YAML_FILE = 'pc_config.yml'

    with open(CAM_CONFIG_YAML_FILE) as kfh:
        cam_config_yaml = yaml.load(kfh)
    cc = all_cams_config(cam_config_yaml)
    for cam in cc.all_cams_name:
        cam_obj = cc.cam_config[cam]
        print(cam_obj.cam_name, cam_obj.cam_user)
        print(cam_obj.cam_url)

    with open(PC_CONFIG_YAML_FILE) as pcfh:
        pc_config_yaml = yaml.load(pcfh)

    pcc = pc_config(pc_config_yaml)
    print(pcc.confidence)
    '''
