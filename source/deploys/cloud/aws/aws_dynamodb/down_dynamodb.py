''' This code runs all that is necessary to takedown AWS DynamoDB
    for project neutrino
'''

import os
import sys
import logging
import time

from pylibs.io.logging_utils import set_logging
from neutrino.source.utils import file_utils
from pylibs.cloud.aws.dynamodb import dynamodb_utils

# Constants
# For now using same config as init.
DYNAMODB_CONFIG_FN = 'source/configs/aws/aws_dynamodb.yml'
DYNDB_CREATE_TABLE_TIMEOUT = 60    # Seconds. At some point, this 
                                   # should move to a central config location

def delete_dyndb_tables(config_fn):
    ''' Delete all DynamoDB tables specified in config file

        Arguments:
            - config_fn: path to the config file

        Returns:
            - Status: True if success, False if fails
            - Message: Error message if status is false
    '''
    # Load the config YAML
    dyndb_cfg_dict = file_utils.yaml2dict(config_fn)

    rstat, rval = True, 'OK'

    # Get list of exisitng tables so we attempt to delete only if table exists
    existing_tables = dynamodb_utils.list_tables()
    logging.info('Starting table deletion')
    table_list = dyndb_cfg_dict['create_dynamodb_tables']
    for table_dict in table_list:
        # Surely there is a better way?
        table_name = list(table_dict.keys())[0]
        if table_name not in existing_tables:
            logging.info(f'Table {table_name} does not exist. Doing nothing')
            continue
        else:
            logging.info(f'Deleting table {table_name} . . .')
            retval, _ = dynamodb_utils.delete_table(table_name)
            # How to check if delete is successful? Not doing anything
            # as of now

    return rstat, rval


def down_dynamodb(cfg_ffn):
    ''' This will takedown all of the databases needed for neutrino

        Arugments: None
        Return: status and message.
            rstat: Status is True or False. 
            rval: Is a string, usually "OK" if status is True
                  and a more detailed message if status is False
    '''
    # I know there is only one function call here. But maybe more in future 
    rstat, rval = delete_dyndb_tables(cfg_ffn)
    return rstat, rval


if __name__ == '__main__':

    set_logging()

    # get full name of deploy config file
    neutrino_home = os.environ['NEUTRINO_HOME']
    cfg_ffn = os.path.join(neutrino_home, DYNAMODB_CONFIG_FN)

    # Takedown DynamoDB
    rstat, rval = down_dynamodb(cfg_ffn)
