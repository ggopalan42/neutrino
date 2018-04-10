#!/usr/bin/env python
''' Utilities for People Counter application '''

import yaml

class cam_config():
    def __init__(self, cfg_yaml_dict):
        self.default_creds = self._get_default_creds(
                                        cfg_yaml_dict['defaults']['creds'])
        print(self.def_user)
        print(self.def_pw)

    # Private methods
    def _get_default_creds(self, def_creds_dict):
        ''' Go through the creds and set the default user/passwords '''
        if def_creds_dict['enc_type'] == 'None':
            # Means user/pw is stored in clear text ### Bad Boy! (frown) ###
            self.def_user = def_creds_dict['user']
            self.def_pw = def_creds_dict['pw']
        else:
            # For future
            print('ERROR: Only raw user/pw supported for now')
            self.def_user = None
            self.def_pw = None
            
if __name__ == '__main__':
    # mostly for testing
    CAM_CONFIG_YAML_FILE = 'pc_aruba_slr01_cams.yml'
    with open(CAM_CONFIG_YAML_FILE) as kfh:
        cam_config_yaml = yaml.load(kfh)
    cc = cam_config(cam_config_yaml)
