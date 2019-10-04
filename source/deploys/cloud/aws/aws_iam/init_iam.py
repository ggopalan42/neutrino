''' This code initializes all necessary entities in AWS IAM
    for project neutrino
'''

import os
import logging
import json
import tempfile
import boto3

from pylibs.io.logging_utils import set_logging
from neutrino.source.utils import file_utils
from pylibs.cloud.aws.iam import iam_utils

# Constants
IAM_CONFIG_FN = 'source/configs/aws/aws_iam.yml'


def create_iam_roles(cfg_file_ffn):
    ''' Create all needed IAM roles from config file

        Arguments: 
            - cfg_file_ffn: Name of config file from which to create roles

        Returns:
            - tuple of (status, message)
                - Status: True if success, False if fails
                - Message: Error message if status is false
    '''

    # Load the config file
    iam_cfg_dict = file_utils.yaml2dict(cfg_file_ffn)
    # Split it into its major constituents
    create_roles = iam_cfg_dict['create_roles']
    trust_policies = iam_cfg_dict['trust_policies']

    # Get a list of existing roles
    logging.info('Getting list of existing roles from IAM')
    created_roles, _, _ = iam_utils.list_roles()

    # Now loop through create policies
    for role in create_roles:
        # Assemble the args for role creation
        role_name = role['role_name']

        # If role already exists, then continue
        if role_name in created_roles:
            logging.info(f'Role {role_name} already exists. Doing nothing')
            continue
        else:
            logging.info(f'Creating role {role_name}')
            trust_policy_key = role['trust_policy']
            # Now get the JSON associated with the trust policy name
            trust_policy = json.dumps(trust_policies[trust_policy_key])
            path = role['path']

            # Set descriotion
            if 'description' in role:
                description = role['description']
            else:
                description = ''

            # Set max_session_duration
            if 'max_session_duration' in role:
                max_session_duration = int(role['max_session_duration'])
            else:
                max_session_duration = 3600
    
            # Set tags
            if 'tags' in role:
                tags = role['tags']
                tags_list = []
                for tag in tags:
                    key = list(tag.keys())[0]
                    value = list(tag.values())[0]
                    new_tag = {'Key': key, 'Value': value}
                    tags_list.append(new_tag) 
            else:
                tags = {}

            role_arn, _ = iam_utils.create_role(role_name, trust_policy, path, 
                                  description, max_session_duration, tags_list)

            logging.info(f'Role named: {role_name} created and corresponding '
                         f'role arn is: {role_arn}')

    return True, 'OK'


def init_aws_iam(cfg_file):
    ''' This will do all of the necessary AWS IAM initialition needed for
        running neutrino apps 

        Arugments: Config file name (incl. full path)
        Return: None
    '''
    # I know there is only one function call here. But maybe more in future 
    create_iam_roles(cfg_file)

if __name__ == '__main__':

    set_logging()

    # get full name of deploy config file
    neutrino_home = os.environ['NEUTRINO_HOME']
    aws_iam_ffn = os.path.join(neutrino_home, IAM_CONFIG_FN)
    init_aws_iam(aws_iam_ffn)


