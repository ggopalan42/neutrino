''' This is the  main deploy file to bringup the entire neutrino application '''

import os
import sys
import logging

from neutrino.source.utils.file_utils import yaml2dict
from pylibs.io.logging_utils import set_logging


# Constants
DEPLOY_PATH = 'source/configs/deploys'     # Relative to NEUTRINO_HOME
DEPLOY_FN = 'neutrino_deploy.yaml'

def deploy_sub(sub_name, sub_cfg_dict):
    ''' Deploy a sub component of neutrino deploy

        Arguments:
            - sub_cfg_dict: Config dict for deploying sub component
    '''
    # Setup to call the sub-component initialization file
    # pathtype = sub_cfg_dict['init_pathtype']
    # init_importpath = sub_cfg_dict['init_importpath']
    # init_funcname = sub_cfg_dict['init_funcname']

    '''
    # Get to the init file
    if pathtype == 'relative':
        if 'NEUTRINO_HOME' not in os.environ:
            # Do nothing
            logging.error('Env variable "NEUTRINO_HOME" not set. '
                          f'Not doing anything for sub deploy type {sub_name}')
            return False
        filedir = sub_cfg_dict['init_filedir']
        base_path = os.environ['NEUTRINO_HOME']
        init_file_ffn = os.path.join(base_path, filedir, init_filename)
    elif pathtype == 'absolute':
        init_file_ffn = init_filename
    else:
        logging.error(f'Unknown path type: {pathtype}. Skipping deploy '
                      f'of {sub_name}')
        return False
    '''

    print(sub_name, sub_cfg_dict)


def deploy_main(deploy_ffn):
    ''' This is the main script to deploy neutrino in its entirety

        Arguments: None

        Returns: None
    '''


    deploy_cfg = yaml2dict(deploy_ffn)

    # Now start running through the various setups
    logging.info('Starting neutrino deploy . . . ')
    for (dep_name, dep_files) in deploy_cfg.items():
        logging.info(f'Deploying for: {dep_name}')
        pathtype = dep_files['pathtype']
        files_list = dep_files['filenames']

        if pathtype == 'relative':
            if 'NEUTRINO_HOME' not in os.environ:
                # Do nothing
                logging.error('Env variable "NEUTRINO_HOME" not set. '
                              f'Not doing anything for deploy type {dep_name}')
                continue
            filedir = dep_files['filedir']
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
            abs_path = dep_files['filedir']
            files_ffn_list = []
            for d in files_list:
                file_ffn = {os.path.join(abs_path, k):v for (k,v) in d.items()}
                files_ffn_list.append(file_ffn)
        else:
            logging.error(f'Unknown path type: {pathtype}. Skipping deploy '
                          f'of {dep_name}')
            continue

        deploy_sub(dep_name, files_ffn_list)


if __name__ == '__main__':
    set_logging()

    # get full name of deploy config file
    neutrino_home = os.environ['NEUTRINO_HOME']
    deploy_ffn = os.path.join(neutrino_home, DEPLOY_PATH, DEPLOY_FN)
    deploy_main(deploy_ffn)
