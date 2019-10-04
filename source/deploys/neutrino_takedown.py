''' This is the  main takedown code that will take a deployed neutrino app down
'''

import os
import sys
import logging

from neutrino.source.utils.file_utils import yaml2dict
from pylibs.io.logging_utils import set_logging


# Constants
TAKEDOWN_PATH = 'source/configs/deploys'     # Relative to NEUTRINO_HOME
TAKEDOWN_FN = 'neutrino_takedown.yaml'

def down_sub(sub_name, sub_list):
    ''' Takedown a sub component of neutrino

        Arguments:
            - sub_name: The name of the sub-component to takedown
            - sub_list: List of sub-component takedowns and their 
                        cmd line params
    '''
    for sub_ffn_params in sub_list:
        # Form the command
        sub_file = list(sub_ffn_params.keys())[0]
        sub_args = list(sub_ffn_params.values())[0]
        sub_cmd = 'python {} {}'.format(sub_file, sub_args)
        logging.info(f'Running init for {sub_name} with args {sub_args}')
        os.system(sub_cmd)


def takedown_main(cfg_ffn):
    ''' This is the main script to deploy neutrino in its entirety

        Arguments:
            - Config file: Neutrino takedown full filename

        Returns: None
    '''


    takedown_cfg = yaml2dict(cfg_ffn)

    # Now start running through the various takedowns
    logging.info('Starting neutrino takedown . . . ')
    for (down_name, down_params) in takedown_cfg.items():
        if not down_params['valid']:
            logging.info(f'Skipping takedown for {down_name}, '
                          'valid flag not set')
            continue
        logging.info(f'Taking down: {down_name}')
        pathtype = down_params['pathtype']
        files_list = down_params['filenames']

        if pathtype == 'relative':
            if 'NEUTRINO_HOME' not in os.environ:
                # Do nothing
                logging.error('Env variable "NEUTRINO_HOME" not set. '
                              f'Not doing anything for deploy type {down_name}')
                continue
            filedir = down_params['filedir']
            base_path = os.environ['NEUTRINO_HOME']
            rel_path = os.path.join(base_path, filedir)
            # Coulda done this with list comp + dict comp, but woulda lost
            # readability . . .
            files_ffn_list = []
            for d in files_list:
                file_ffn = {os.path.join(rel_path, k):v for (k,v) in d.items()}
                files_ffn_list.append(file_ffn)
        elif pathtype == 'local':
            cwd = os.getcwd()
            files_ffn_list = []
            for d in files_list:
                file_ffn = {os.path.join(cwd, k):v for (k,v) in d.items()}
                files_ffn_list.append(file_ffn)
        elif pathtype == 'absolute':
            abs_path = down_params['filedir']
            files_ffn_list = []
            for d in files_list:
                file_ffn = {os.path.join(abs_path, k):v for (k,v) in d.items()}
                files_ffn_list.append(file_ffn)
        else:
            logging.error(f'Unknown path type: {pathtype}. Skipping deploy '
                          f'of {down_name}')
            continue

        print(down_name, files_ffn_list)
        down_sub(down_name, files_ffn_list)


if __name__ == '__main__':
    set_logging()

    # get full name of takedown config file
    neutrino_home = os.environ['NEUTRINO_HOME']
    cfg_ffn = os.path.join(neutrino_home, TAKEDOWN_PATH, TAKEDOWN_FN)
    takedown_main(cfg_ffn)
