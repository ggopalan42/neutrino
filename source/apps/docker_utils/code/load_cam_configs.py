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

from collections import defaultdict


# Neutrino lib imports
from neutrino.source.utils import file_utils


# Constants
CONFIG_DIR = '../configs/'
LIST_OF_CAMS = 'list_of_cams.yml'

# Other variables

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

class single_cam_config():
    ''' Object that holds the config and methods of one camera '''
    def __init__(self, cam_name, single_cam_dict, default_creds):
        self.cam_name = cam_name
        self.default_creds = default_creds

        # Set the below two flags to false by default. The unfurling below
        # will overwrite if so specified in the config file
        self.write_to_file = False
        self.read_from_file = False

        # Now unfurl the single camera dict and set them as attributes
        # This is basically equivalent to: self.valid = single_cam_dict['valid']
        for key in single_cam_dict:
            setattr(self, key, single_cam_dict[key])
      
        '''
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
        '''
        # self._set_creds(cam_dict[cam_name]['cam_creds'], default_creds)
        self._set_creds()
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

    def _set_usb_creds(self, default_creds):
        ''' This is for USB camera.  Set them to none for now '''
        self.cam_user = None
        self.cam_pw = None

    def _set_null_creds(self, default_creds):
        ''' This is catch all to set creds to none '''
        self.cam_user = None
        self.cam_pw = None

    def _set_creds(self):
        ''' Set the user and pw credentials of the camera '''

        # Cred type to cred function map
        cred_func_map = defaultdict(str)
        cred_func_map['aruba_axis1'] = self._set_aruba_axis1_creds
        cred_func_map['USB'] = self._set_usb_creds
        cred_func_map['test'] = self._set_null_creds

        if self.cam_creds:    # If cred method is specified
            cred_func_map[self.cam_creds](self.default_creds)
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
        if self.valid:
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
            # self.bgsub = cv2.createBackgroundSubtractorMOG2(detectShadows = True)
        else:
            logging.info(f'Not connecting to {self.cam_name}. Valid flag not set')


    def release_cam(self):
        ''' Release the camera resources '''
        if self.valid:
            logging.info('Releasing camera: {}'.format(self.cam_name))
            self.cap_handle.release()

class cam_groups():
    ''' This class holds the configs and defaults of a camera groups '''
    def __init__(self, group_config_dict):
        self.cam_names = []         # Name of each camera
        self.cam_config = {}        # Config obj of a camera

        # Set default creds for the group if it exists
        if group_config_dict['defaults']:
            self.default_creds = group_config_dict['defaults']['creds']
        else:
            self.default_creds = False
        self.group_name = group_config_dict['group_name']
        # below redundancy is for compatibility with old code
        self.stream_group_name = group_config_dict['group_name']
        # Now setup all of the cams with their params
        self._load_cams_configs(group_config_dict)

    # Private methods
    def _load_cams_configs(self, group_config_dict):
        ''' Load the config of each camera specified in the config

            Arguments:
                group_config_dict: Dictionary of the entire camera group

            Returns:
                Nothing. But the object itself (self) is loaded will all needed
                info
        '''
        for single_config in group_config_dict['cams']:
            # Cams is a list of camera configs in this group. So iterate over it
            for cam_name, cam_config in single_config.items():
                # First append the camera names
                self.cam_names.append(cam_name)
                # Then add each single camera config to the dict
                 
                scc = single_cam_config(cam_name, cam_config,
                                                      self.default_creds)
                self.cam_config[cam_name] = scc

    # Public methods
    def connect_to_group_cams(self):
        ''' Connect to all cameras in this group '''
        for cam_name in self.cam_names:
            cam_config = self.cam_config[cam_name]
            cam_config.connect_to_cam()
    

    def release_group_cams(self):
        ''' Release all cameras in this group '''
        for cam_name in self.cam_names:
            cam_config = self.cam_config[cam_name]
            cam_config.release_cam()
    


class all_cams_config():
    ''' This class holds the configs and defaults of all camera groups '''
    def __init__(self, config_dir=CONFIG_DIR, list_of_cams=LIST_OF_CAMS):
        self.cam_grp_names = []      # List of cam group names
        self.cam_grp_config = {}     # Dict that holds cam group objects
        # Load the camera configs
        self._load_all_cam_configs(config_dir, list_of_cams)


    # Private methods
    def _load_all_cam_configs(self, configs_dir, list_of_cams_fn):
        ''' Load the configs of all camera groups from list_of_cams_fn

            Arguments:
                configs_dir: Location of the camera configurations
                list_of_cams_fn: YAML file that contains list of camera groups

            Return:  The class itself
        ''' 
        # First load the cams list
        ffn = os.path.join(configs_dir, list_of_cams_fn)
        logging.info(f'Loading all camps list from: {ffn}')
        self.cams_list_dict = file_utils.yaml2dict(ffn)
        for cam_grp_yaml_fn in self.cams_list_dict['cams_list']:
            ffn = os.path.join(configs_dir, cam_grp_yaml_fn)
                   # Load the camera group config
            logging.info(f'Loading cam groups config: {ffn}')
            group_dict = file_utils.yaml2dict(ffn)

            # Append the cam group name to the list
            cam_group_name = group_dict['group_name']
            self.cam_grp_names.append(cam_group_name)

            # Setup the cam group object
            cam_group_obj = cam_groups(group_dict)
            # Then add it to the group config dict
            self.cam_grp_config[cam_group_name] = cam_group_obj

    # Public methods
    def connect_to_all_cams(self):
        ''' Connect to all of the cameras that are set as valid '''
        for cam_grp_name in self.cam_grp_names:
            cam_grp_config = self.cam_grp_config[cam_grp_name]
            cam_grp_config.connect_to_group_cams()

    def release_all_cams(self):
        ''' release to all of the cameras that are connected '''
        for cam_grp_name in self.cam_grp_names:
            cam_grp_config = self.cam_grp_config[cam_grp_name]
            cam_grp_config.release_group_cams()


if __name__ == '__main__':
    cam_conf = all_cams_config()
    cam_conf.connect_to_all_cams()
    cam_conf.release_all_cams()
