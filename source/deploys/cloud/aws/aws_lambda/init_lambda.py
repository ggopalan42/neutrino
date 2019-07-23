''' This code runs all that is necessary to setup AWS IoT code for
    neutrino

    The steps that this code performs are:
        - Check and create the thing types specified in the config file
        - Check and create the things specified in the config file
'''

import os
import logging

from neutrino.source.utils import file_utils
from pylibs.cloud.aws.s3 import s3_utils

# Set logging level
# logging.basicConfig(level=logging.INFO)

# Constands
LOCAL_AWS_LAMBDA_CODE_DIR = 'source/apps/aws_lambda'
S3_CONFIG_FN = 'source/configs/aws/aws_s3.yml'


def copy_files_to_s3():
    ''' This will copy all of the local lambda code located at: 
        LOCAL_AWS_LAMBDA_CODE_DIR to the S3 remote bucket defined by
        s3_bucket_name: in the YAML file in configs
    '''

    # Setup some paths
    neutrino_home = os.environ['NEUTRINO_HOME']
    s3_config_full_fn = os.path.join(neutrino_home, S3_CONFIG_FN)
    s3_config = file_utils.yaml2dict(s3_config_full_fn)
    local_aws_lambda_dir = os.path.join(neutrino_home,LOCAL_AWS_LAMBDA_CODE_DIR)

    # Now copy local lambda files to remote s3 bucket
    remote_s3_bucket = s3_config['s3_bucket_name']
    for filename in os.listdir(local_aws_lambda_dir):
        local_full_fn = os.path.join(neutrino_home,
                                     LOCAL_AWS_LAMBDA_CODE_DIR, filename)
        logging.info(f'Putting file {filename} to AWS S3 bucket')
        s3_utils.put_object(remote_s3_bucket, filename, local_full_fn) 

    



def init_aws_lambda():
    ''' This will do all of the necessary AWS Lambda initialition needed for
        running neutrino apps 

        Arugments: None
        Return: None
    '''
    copy_files_to_s3()
    return
    # Determine the local aws lambda path
    config_ffn = os.path.join(neutrino_home, 
                              'source/configs/aws/aws_iot_core.yml')
    iot_core_cfg_dict = file_utils.yaml2dict(config_ffn)
    thing_type_list = iot_core_cfg_dict['aws_iot_core_init']['thing_types']
    things_list = iot_core_cfg_dict['aws_iot_core_init']['things']

    # Now initialize the Core IoT Thing Types needed
    init_thing_types(thing_type_list)
    # And then initialize the Core IoT Things
    init_things(things_list)

if __name__ == '__main__':
    init_aws_lambda()


