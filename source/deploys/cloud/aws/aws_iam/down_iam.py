''' This code takes down all AWS IAM related entities
    for project neutrino
'''

import os
import sys
import logging
import json
import tempfile
import boto3

from pylibs.io.logging_utils import log_if_false
from pylibs.io.logging_utils import set_logging
from neutrino.source.utils import file_utils
from pylibs.cloud.aws.iam import iam_utils

# Constants
# For now using same config as init.
IAM_CONFIG_FN = 'source/configs/aws/aws_iam.yml'


def down_iam_roles(cfg_file_ffn):
    ''' Create all needed IAM roles from config file

        Arguments: 
            - cfg_file_ffn: Name of config file from which to create roles

        Returns:
            - tuple of (status, message)
                - Status: True if success, False if fails
                - Message: Error message if status is false
    '''

    ret_status = True
    ret_msg = 'OK'

    # Load the config file
    iam_cfg_dict = file_utils.yaml2dict(cfg_file_ffn)
    # Get the roles. These roles will be deleted
    roles = iam_cfg_dict['create_roles']

    # Get a list of existing roles
    # logging.info('Getting list of existing roles from IAM')
    # created_roles, _, _ = iam_utils.list_roles()

    # Now loop through and delete policies
    for role in roles:
        # Assemble the args for role creation
        role_name = role['role_name']

        logging.info(f'Deleting role {role_name}')
        status, _ = iam_utils.delete_role(role_name)

        if not status:
            ret_status = False
            ret_msg = 'Something went wrong deleting role. Check logs.'

    return ret_status, ret_msg


def down_aws_iam(cfg_file):
    ''' This will do all of the necessary AWS IAM initialition needed for
        running neutrino apps 

        Arugments: Config file name (incl. full path)
        Return: None
    '''
    # I know there is only one function call here. But maybe more in future 
    status, msg = down_iam_roles(cfg_file)
    log_if_false(status, msg)


if __name__ == '__main__':

    set_logging()

    # get full name of deploy config file
    neutrino_home = os.environ['NEUTRINO_HOME']
    aws_iam_ffn = os.path.join(neutrino_home, IAM_CONFIG_FN)
    down_aws_iam(aws_iam_ffn)


