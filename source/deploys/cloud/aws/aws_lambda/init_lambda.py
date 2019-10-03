''' This code runs all that is necessary to run lambda functions on AWS
    for project neutrino

    The steps that this code performs are:
        - Created all needed functions
'''

import os
import sys
import logging
import tempfile
import zipfile
import boto3

from pylibs.io.logging_utils import set_logging
from neutrino.source.utils import file_utils
from pylibs.cloud.aws.iam import iam_utils
from pylibs.cloud.aws.aws_lambda import lambda_utils

# Constants
LAMBDA_CONFIG_FN = 'source/configs/aws/aws_lambda.yml'


def create_functions(cfg_ffn):
    ''' This will create all of the functions specified in aws_lambda.yml
    '''

    # Open a client for lambda functions
    lambda_client = boto3.client('lambda')

    # Create a temp directory. This is to hold the lambda zip files
    tempdir_handler = tempfile.TemporaryDirectory()
    tempdir_name = tempdir_handler.name

    # Load the lambda config
    lambda_cfg_dict = file_utils.yaml2dict(cfg_ffn)

    # Get a list of functions already on AWS
    existing_functions, _ = lambda_utils.list_functions()

    # Now go over the functions specified in lambda config yaml and create it
    # if it has not been already
    for fspec in lambda_cfg_dict['create_lambda_functions']:
        # unfurl the function specifications
        func_name = list(fspec.keys())[0]
        aws_func_name = fspec[func_name]['function_name_in_aws']

        # If function already exists, do nothing
        if aws_func_name in existing_functions:
            logging.info(f'Function {func_name} already exists '
                            'Doing nothing and moving on')
            continue

        logging.info(f'Creating function {func_name}')

        func_params = fspec[func_name]
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

def init_aws_lambda(cfg_ffn):
    ''' This will do all of the necessary AWS Lambda initialition needed for
        running neutrino apps 

        Arugments: None
        Return: None
    '''
    # I know there is only one function call here. But maybe more in future 
    create_functions(cfg_ffn)

if __name__ == '__main__':

    set_logging()

    # get full name of deploy config file
    neutrino_home = os.environ['NEUTRINO_HOME']
    cfg_ffn = os.path.join(neutrino_home, LAMBDA_CONFIG_FN)

    # Init lambda
    init_aws_lambda(cfg_ffn)


