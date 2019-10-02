''' This is the  main deploy file to bringup the entire neutrino application '''

import os
import sys
import logging

from neutrino.source.utils.file_utils import yaml2dict
from pylibs.io.logging_utils import set_logging


# Constants
DEPLOY_PATH = 'source/configs/deploys'     # Relative to NEUTRINO_HOME
DEPLOY_FN = 'neutrino_deploy.yaml'

def deploy_sub(sub_name, sub_list):
    ''' Deploy a sub component of neutrino deploy

        Arguments:
            - sub_name: The name of the sub-component to deploy
            - sub_list: List of sub-component deploys and their cmd line params
    '''
    for sub_ffn_params in sub_list:
        # Form the command
        sub_file = list(sub_ffn_params.keys())[0]
        sub_args = list(sub_ffn_params.values())[0]
        sub_cmd = 'python {} {}'.format(sub_file, sub_args)
        logging.info(f'Running init for {sub_name} with args {sub_args}')
        os.system(sub_cmd)


def deploy_main(deploy_ffn):
    ''' This is the main script to deploy neutrino in its entirety

        Arguments: None

        Returns: None
    '''


    deploy_cfg = yaml2dict(deploy_ffn)

    # Now start running through the various setups
    logging.info('Starting neutrino deploy . . . ')
    for (dep_name, dep_params) in deploy_cfg.items():
        if not dep_params['valid']:
            logging.info(f'Skipping deploy for {dep_name}, valid flag not set')
            continue
        logging.info(f'Deploying for: {dep_name}')
        pathtype = dep_params['pathtype']
        files_list = dep_params['filenames']

        if pathtype == 'relative':
            if 'NEUTRINO_HOME' not in os.environ:
                # Do nothing
                logging.error('Env variable "NEUTRINO_HOME" not set. '
                              f'Not doing anything for deploy type {dep_name}')
                continue
            filedir = dep_params['filedir']
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
            abs_path = dep_params['filedir']
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
