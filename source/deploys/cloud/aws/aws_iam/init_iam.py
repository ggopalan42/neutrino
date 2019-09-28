''' This code runs all that is necessary to run lambda functions on AWS
    for project neutrino

    The steps that this code performs are:
        - Created all needed functions
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


 
def create_functions(config_fn):
    ''' This will create all of the functions specified in aws_lambda.yml
    '''

    # Open a client for lambda functions
    lambda_client = boto3.client('lambda')

    ############## Below is lambda init ###############

    # Load the lambda config
    ffn = os.path.join(neutrino_home, config_fn)
    lambda_cfg_dict = file_utils.yaml2dict(ffn)

    # Get a list of functions already on AWS
    existing_functions, _ = lambda_utils.list_functions()

    # Now go over the functions specified in lambda config yaml and create it
    # if it has not been already
    for fspec in lambda_cfg_dict['create_lambda_functions']:
        # unfurl the function specifications
        func_name = list(fspec.keys())[0]
        logging.info(f'Creating function {func_name}')
        func_params = fspec[func_name]

        aws_func_name = func_params['function_name_in_aws']
        aws_func_run_time = func_params['run_time']
        aws_func_handler = func_params['function_handler']
        aws_func_role_name = func_params['function_role_name']
        local_func_fn = func_params['local_function']
        local_func_env = func_params['local_function_env']

        # get the local function
        local_func_full_fn = os.path.join(neutrino_home, local_func_fn)
        # Extract the basename (without the ext) and make a zip file in
        # the tempdir
        local_func_basename = os.path.basename(local_func_full_fn)
        local_func_wo_ext = os.path.splitext(local_func_basename)[0]
        local_func_zip_fn = os.path.join(tempdir_name, 
                                         f'{local_func_wo_ext}.zip')
        # For testing: overwrite local_func_zip_fn
        local_func_zip_fn = '/tmp/zip_test1/init_test.zip'
        with zipfile.ZipFile(local_func_zip_fn, 'w') as ziph:
            # Control the name of the archive (using the base name of the func)
            # Otherwise the archive name is something like: 
            #      /home/<user>/../func_name.py whcih AWS rejects
            ziph.write(local_func_full_fn, arcname=local_func_basename) 
        # Now this may sound supremely dumb (to zip and then immediately unzip),        # but I know of no other way,
        # so please pardon
        with open(local_func_zip_fn, 'rb') as fh:
            zipped_code = fh.read()

        # Get the Arn for the role
        role_arn, _ = iam_utils.get_role_arn(aws_func_role_name)

        # Phew! Now finally create the lambda function
        logging.info(f'Creating lambda function {func_name}')
        lambda_client.create_function(
                   FunctionName = aws_func_name,
                   Runtime = aws_func_run_time,
                   Role = role_arn,
                   Handler = f'{local_func_wo_ext}.{aws_func_handler}',
                   Code = dict(ZipFile = zipped_code),
                   Timeout = 300,   # make this configurable
               )


    # Close stuff
    tempdir_handler.cleanup()

def init_aws_iam(cfg_file):
    ''' This will do all of the necessary AWS Lambda initialition needed for
        running neutrino apps 

        Arugments: Config file name (incl. full path)
        Return: None
    '''
    # I know there is only one function call here. But maybe more in future 
    create_iam_roles(cfg_file)

if __name__ == '__main__':

    # Set logging level
    logging.basicConfig(level=logging.INFO)

    # get full name of deploy config file
    neutrino_home = os.environ['NEUTRINO_HOME']
    aws_iam_ffn = os.path.join(neutrino_home, IAM_CONFIG_FN)
    init_aws_iam(aws_iam_ffn)


