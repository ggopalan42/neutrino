#! /usr/bin/env python
''' Load configs needed for cam2pubsub function '''

# Python lib imports
import cv2
import base64
import os
import sys
import yaml
import logging

import numpy as np

from urllib.parse import urlparse


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
        self.stream_name = cam_dict[cam_name]['stream_name']
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
        elif self.cam_type == 'local_usb':
            logging.info('Connecting to local camera on bus: {}'
                                                  .format(self.cam_uri))
            self.cap_handle = cv2.VideoCapture(self.cam_uri)
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

class cam_group_config():
    ''' This class holds the configs and defaults of all camera groups '''
    def __init__(self, cfg_yaml_dict):
        self.cam_config = {}
        self.cam_grp_names = []
        self.cam_grp_config_dict = cfg_yaml_dict['cams']
        # Set all of the default creds
        self.default_creds = cfg_yaml_dict['defaults']['creds']
        self.stream_group_name = cfg_yaml_dict['defaults']['stream_group_name']
        # Now setup all of the cams with their params
        self._setup_cam_grp_configs()

    # Private methods
    def _setup_cam_grp_configs(self):
        for cam in self.cam_grp_config_dict:
            cam_name = list(cam.keys())[0]
            # Only set single cam configs if valid field is set to True
            if cam[cam_name]['valid']:
                self.cam_grp_names.append(cam_name)
                cam_obj = single_cam_config(cam, self.default_creds)
                self.cam_config[cam_name] = cam_obj

def get_cam_yaml(configs_dir, list_of_cams_fn='list_of_cams.yml')

class config_obj():
    def __init__(self, args):
        # Load configs functions dict
        self.load_configs_func_dict = {
                        'ml_models': self._load_mlmodels_configs,
                        'cams': self._load_cams_configs,
                        'locs': self._load_locs_configs,
                        'kafka': self._load_kafka_config,
                        'cassandra': self._load_cassandra_config,
                        'apps_map': self._load_apps_map,
        }
        # ml_model init class dict. This is basically map between the
        # model name and the class name so the class can be instantiated
        # based on model name. Need to figure out a way to do this
        # automagically rather than edit source code evry time a new
        # model is introduced
        self.ml_models_class_dict = {
            'MobilenetSSD_V1': mobilenetssd_v1
        }
        # Load all configs
        self.args = args
        self.home_path = args['neutrino_home']
        self._set_some_paths()
        self._load_all_configs(args)
        
    def _load_cams_configs(self, cfg_fn):
        ''' Go through the list of cam config files specified and 
            process them '''
        logging.info('Loading list of camera configs from file: {}'
                                                            .format(cfg_fn))
        self.cams_grp_cfg = cams_config_class()
        self.cams_grp_names = []

        # Open the cams list file and get the configs
        cams_list_fn = os.path.join(self.configs_path, cfg_fn)
        with open(cams_list_fn) as fh:
            cams_list_dict = yaml.load(fh)
        for cam_cfg_fn in cams_list_dict['cams_list']:
            logging.info('Loading cam config from {}'.format(cam_cfg_fn))
            cam_cfg_full_fn = os.path.join(self.configs_path, cam_cfg_fn)
            with open(cam_cfg_full_fn) as fh:
                cams_cfg_dict = yaml.load(fh)
            cams_grp_name = cams_cfg_dict['cams_name']
            cams_config_obj = cam_grp_config(cams_cfg_dict)
            setattr(self.cams_grp_cfg, cams_grp_name, cams_config_obj)
            # Add the name of the cams if all of above successful
            self.cams_grp_names.append(cams_grp_name)

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
            logging.info('Loading {} config from file'.format(cfg_type, cfg_fn))
            self.load_configs_func_dict[cfg_type](cfg_fn) 
        return

    # Public methods
    # ---------- Cam Methods ----------------
    def get_cam_grp_config_obj(self, cam_grp_name):
        ''' Get and return the cam group config object from cam_grp_name '''
        # The cam group config object is the class that holds information
        # for the cam group cam_grp_name. This includes the single cam objects
        # as well
        cam_grp_config_obj = getattr(self.cams_grp_cfg, cam_grp_name)
        return cam_grp_config_obj

    def get_cam_grp_stream_name(self, cam_grp_name):
        ''' Get the default stream_name for cam_grp_name '''
        cam_grp_config_obj = getattr(self.cams_grp_cfg, cam_grp_name)
        return cam_grp_config_obj.stream_group_name

    def connect_to_cams(self, cams_grp_name):
        ''' Connect to all specified cameras '''
        # Go through all cameras and connect to them
        # First get the cams config object associated with cams_name 
        cams_config_obj = getattr(self.cams_grp_cfg, cams_grp_name)
        for cam_name in cams_config_obj.cam_grp_names:
            logging.info('Connecting to camera: {}'.format(cam_name))
            single_cam_obj = cams_config_obj.cam_config[cam_name]
            single_cam_obj.connect_to_cam()

    def release_all_cams(self, cam_grp_name):
        ''' Release all cameras' resources '''
        # Go through all cameras and release to them
        cam_grp_config_obj = getattr(self.cams_grp_cfg, cam_grp_name)
        for cam_name in cam_grp_config_obj.cam_grp_names:
            logging.info('Releasing camera: {}'.format(cam_name))
            # get the single cam object
            single_cam_obj = cam_grp_config_obj.cam_config[cam_name]
            single_cam_obj.cam_release()

    # -------------------- App methods ---------------------
    def get_app_cams_name(self, app_name):
        ''' Given an app name, return the cams name '''
        return self.apps_map[app_name]['cams']

    # ------------------- Others ------------------------
    def set_app_name(self, app_name):
        ''' Set the app name '''
        self.app_name = app_name

    def get_app_name(self):
        ''' Return the app name '''
        return self.app_name
 
    def cleanup(self, cams_name):
        ''' Cleanup before exiting '''
        cv2.destroyAllWindows()
        self.release_all_cams(cams_name)
        # Should anything be released on kafka 
        # Any others?
 

CAM2PUBSUB_CONFIG_DIR = '../configs/'
if __name__ == '__main__':
    APP_NAME = 'camfeeds1'
    SEND_TO_KAFKA = False


