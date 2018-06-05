#! /usr/bin/env python
''' Given an URL, keep getting image from it, detect if there are any person(s)
    in the image and feed the results to kafka '''

# Python lib imports
import argparse
import os
import sys
import yaml
import logging

import numpy as np

from kafka import KafkaProducer
from urllib.parse import urlparse

# Constants
# KAFKA_BROKER = '10.2.13.29'
# KAFKA_PORT = '9092'
# KAFKA_TOPIC = 'peoplecounter1'


# Other variables

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

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
        self.display_gait = cam_dict[cam_name]['display_gait']
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

class mobilenetssd_v1():
    ''' MoblenetSSD V1 model parameters '''
    def __init__(self, models_path, mlmodel_dict):
        self.model_file = os.path.join(models_path, mlmodel_dict['model_file'])
        self.prototxt_file = os.path.join(models_path, 
                                                 mlmodel_dict['prototxt_file'])
        self.classes = mlmodel_dict['model_params']['object_classes'].split()
        self.min_confidence = mlmodel_dict['model_params']['confidence']
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3)) 
        # previous_det is a stupid hack. I have not figured out a way around
        self.previous_det = np.array([[[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]]])
        # Below is needed for person identification purposes only
        self.person_idx = self.classes.index('person')

class config_obj():
    def __init__(self, args):
        # Load configs functions dict
        self.load_configs_func_dict = {
                        'ml_models': self._load_mlmodels_configs,
                        'cams': self._load_cams_configs,
                        'locs': self._load_locs_configs,
                        'kafka': self._load_kafka_config,
                        'cassandra': self._load_cassandra_config,
        }
        # ml_model init class dict
        self.ml_models_class_dict = {
            'MobilenetSSD_V1': mobilenetssd_v1
        }
        # Load all configs
        self.args = args
        self.home_path = args['neutrino_home']
        self._set_some_paths()
        self._load_all_configs(args)
        
        # self.msg_format_ver = '1.0.0'

    # Private methods
    def _load_mlmodels_configs(self, cfg_fn):
        ''' Go through the list of ml models specified and load them '''
        logging.info('Loading list of ML models from file: {}'.format(cfg_fn))
        mlmodels_list_fn = os.path.join(self.configs_path, cfg_fn)
        with open(mlmodels_list_fn) as fh:
            mlmodels_dict = yaml.load(fh)
        # Now loop through the list of model files specified and load them
        for mlmodel_fn in mlmodels_dict['ml_models']:
            logging.info('Loading model from {}'.format(mlmodel_fn))
            mlmodel_full_fn = os.path.join(self.configs_path, mlmodel_fn)
            with open(mlmodel_full_fn) as fh:
                mlmodel_dict = yaml.load(fh)['model']
            model_name = mlmodel_dict['model_name']
            try:
                # Init the ml object
                model_config_class = self.ml_models_class_dict[model_name](
                                               self.models_path, mlmodel_dict)
                # Set the inited object as an attribete to this class. 
                # The attribute is the name of the ml model specified in file
                setattr(self, model_name, model_config_class)
            except KeyError:
                logging.error('Class to load model named {} not implemented'
                                           .format(model_name))
                raise RuntimeError('Class to load model named {} not '
                                           'implemented'.format(model_name))
        # Now set the list of models whose nets and weights are to be loaded
        self.model_weights_to_load = mlmodels_dict['model_weights_to_load']

    def _load_cams_configs(self, cfg_fn):
        ''' Go through the list of cam config files specified and process them '''
        print('Doing dis!')

    def _load_locs_configs(self, cfg_fn):
        logging.warning('Bypassing location config load for now')
    def _load_kafka_config(self, cfg_fn):
        print(sys._getframe().f_code.co_name, cfg_fn)
    def _load_cassandra_config(self, cfg_fn):
        print(sys._getframe().f_code.co_name, cfg_fn)

    def _set_some_paths(self):
        ''' Set some default paths and filenames '''
        self.configs_path = os.path.join(self.home_path, 'configs')
        self.all_configs_fn = os.path.join(self.configs_path, 'all_configs.yml')
        self.models_path = os.path.join(self.home_path, 'models')

    def _load_all_configs(self, args):
        ''' Load all needed configs '''
        # Load the all_configs file
        with open(self.all_configs_fn) as all_fh:
            all_configs_dict = yaml.load(all_fh)
        for cfg_type, cfg_fn in all_configs_dict['configs_list'].items():
            print('Loading {} config from file'.format(cfg_type, cfg_fn))
            self.load_configs_func_dict[cfg_type](cfg_fn) 
        return

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



'''
        # Set camera config
        with open(cam_yaml_fn) as cfh:
            cam_config_dict = yaml.load(cfh)
        self.all_cams_config = pc_utils.all_cams_config(cam_config_dict)
'''
