#!/usr/bin/env python
''' Utilities for People Counter application '''

import base64
import yaml
import logging


class pc_config():
    ''' Object that holds all People Counter specific paramaters '''
    def __init__(self, pc_config_dict):
        self.confidence = pc_config_dict['pc_params']['confidence']
        self.kafka_broker_hostname = pc_config_dict['kafka']['kafka_broker_hostname']
        self.kafka_port = pc_config_dict['kafka']['kafka_broker_port']


class single_cam_config():
    ''' Object that holds the config and methods of one camera '''
    def __init__(self, cam_dict, default_creds):
        # Unfurl all of this cam's config.
        # And surely there is a better way to do this doc?
        cam_name = list(cam_dict.keys())[0]
        self.cam_name = cam_name
        self.display_name = cam_dict[cam_name]['display_name']
        self.description = cam_dict[cam_name]['description']
        self.cam_type = cam_dict[cam_name]['cam_type']
        self.cam_proto = cam_dict[cam_name]['cam_proto']
        self.cam_hostname = cam_dict[cam_name]['cam_hostname']
        self.cam_uri = cam_dict[cam_name]['cam_uri']
        self.cam_creds = cam_dict[cam_name]['cam_creds']  ###
        self.kafka_topic = cam_dict[cam_name]['kafka_topic']
        self.kafka_partition = cam_dict[cam_name]['kafka_partition']  ###
        self.kafka_key = cam_dict[cam_name]['kafka_key']

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

class all_cams_config():
    ''' This class holds the configs and defaults of all cameras '''
    def __init__(self, cfg_yaml_dict):
        self.cam_config = {}
        self.all_cams_name = []
        self.cam_config_dict = cfg_yaml_dict
        # Set all of the default creds
        self.default_creds = cfg_yaml_dict['defaults']['creds']
        # Now setup all of the cams with their params
        self._setup_all_cam_configs()

    # Private methods
    def _setup_all_cam_configs(self):
        for cam in self.cam_config_dict['cams']:
            cam_name = list(cam.keys())[0]
            self.all_cams_name.append(cam_name)
            cam_obj = single_cam_config(cam, self.default_creds)
            self.cam_config[cam_name] = cam_obj
 
if __name__ == '__main__':
    # mostly for testing
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

