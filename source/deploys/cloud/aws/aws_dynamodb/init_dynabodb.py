''' This code runs all that is necessary to run lambda functions on AWS
    for project neutrino

    The steps that this code performs are:
        - Created all needed functions
'''

import os
import logging
import time

from pylibs.io.logging_utils import set_logging
from neutrino.source.utils import file_utils
from pylibs.cloud.aws.dynamodb import dynamodb_utils

# Constants
DYNAMODB_CONFIG_FN = 'source/configs/aws/aws_dynamodb.yml'
DYNDB_CREATE_TABLE_TIMEOUT = 60    # Seconds. At some point, this 
                                   # should move to a central config location

def get_table_args(table_name, table_dict):
    ''' Format table_dict into a dict format so DynamoDB create_table function
        can be called

        Arguments:
            - table_name: name of table
            - table_dict: All of the arguments needed for creating said table

        Return:
            - table_args_dict: Dictionary of parameters to use in DynamoDB
                               table creation
    '''

    # unfurl the table_dict
    # Pri and Sec keys
    args_dict = table_dict[table_name]
    primary_key = args_dict['primary_key']
    secondary_key = args_dict['secondary_key'] if 'secondary_key'   \
                                  in args_dict.keys() else None 
    # Table schema
    table_schema = [] 
    for items in args_dict['table_schema']:
        k = list(items.keys())[0]
        v = items[k]
        table_schema.append({'AttributeName': k, 'AttributeType': v})

    # Billing mode
    billing_mode = args_dict['billing_mode']
    if billing_mode == 'PAY_PER_REQUEST':
        billing_mode_params = {}
    elif billing_mode == 'PROVISIONED': 
        tmp_d = args_dict['billing_mode_params']
        billing_mode_params = {
            'ReadCapacityUnits': tmp_d['read_capacity_units'],
            'WriteCapacityUnits': tmp_d['write_capacity_units']
        }
    else:
        # Unknown billing mode type. Set to PAY_PER_REQUEST
        logging.warn(f'Unknown billing mode type {billing_mode} ' 
                     f'(Setting it to PAY_PER_REQUEST')

        billing_mode = 'PAY_PER_REQUEST'
        billing_mode_params = {}

    # Now make the entire args dict
    create_table_args_dict = {
        'table_name': table_name,
        'table_schema': table_schema,
        'primary_key': primary_key,
        'secondary_key': secondary_key,
        'billing_mode': billing_mode,
        # 'billing_mode_params': billing_mode_params  # Currently unused
    }

    return create_table_args_dict

def create_single_table(table_name, table_args_dict):
    ''' Creates a single Dynamo DB table with all error checking    

        Arguments:
            - table_name: name of table to create
            - table_args_dict: List of arguments formated properly to create
                               a table 
        Returns:
            - tuple of (status, message)
                - Status: True if success, False if fails
                - Message: Error message if status is false
    '''

    # Try and create the table
    try:
        resp = dynamodb_utils.create_table(**table_args_dict)
    except Exception as e:
        err_msg = (f'DynamoDB table creation of table {table_name} failed '
                   f'with error {e}')
        logging.error(err_msg)
        return False, err_msg

    # Wait till table becomes active
    t = 0
    for i in range(int(DYNDB_CREATE_TABLE_TIMEOUT/5)):
        resp = dynamodb_utils.describe_table(table_name)
        # resp = dynamodb_utils.describe_table('gg_test1')
        time.sleep(5)
        t += 5
        logging.info(f'Waiting for table to go active . . '
                     f'(waited {t} of {DYNDB_CREATE_TABLE_TIMEOUT} secs)')
        if resp['TableStatus'] == 'ACTIVE':
            break

    if t >= DYNDB_CREATE_TABLE_TIMEOUT:
        err_msg = (f'Table {table_name} did not become ACTIVE after '
                   f'waiting for {DYNDB_CREATE_TABLE_TIMEOUT} seconds')
        logging.error(err_msg)
        return False, err_msg
    
    # if we are here, all is well
    return True, 'OK'


def create_dyndb_tables(config_fn):
    ''' Create all needed DynamoDB tables

        Arguments:
            - config_fn: path to the config file relative to NEUTRINO_HOME

        Returns:
            - tuple of (status, message)
                - Status: True if success, False if fails
                - Message: Error message if status is false
    '''
    # Load the config YAML
    dyndb_cfg_dict = file_utils.yaml2dict(config_fn)

    rstat, rval = True, 'OK'

    # Get list of exisitng tables so we do not attempt te re-create tables
    existing_tables = dynamodb_utils.list_tables()
    logging.info('Starting table creation')
    table_list = dyndb_cfg_dict['create_dynamodb_tables']
    for table_dict in table_list:
        # Surely there is a better way?
        table_name = list(table_dict.keys())[0]
        if table_name in existing_tables:
            logging.info(f'Table {table_name} already exists. Doing nothing')
            continue
        else:
            logging.info(f'Creating table {table_name} . . .')
            table_args_dict = get_table_args(table_name, table_dict)
            rstat, rval = create_single_table(table_name, table_args_dict)
            if not rstat:
                rstat = False
                rval = ('Something went wrong in table creation. '
                       'Check log messages ')

    return rstat, rval


def init_dynamodb(cfg_ffn):
    ''' This will initialize all of the databases needed for neutrino

        Arugments: None
        Return: None
    '''
    # I know there is only one function call here. But maybe more in future 
    rstat, rval = create_dyndb_tables(cfg_ffn)
    return rstat, rval


if __name__ == '__main__':

    # Set logging level
    logging.basicConfig(level=logging.INFO)

    # get full name of deploy config file
    neutrino_home = os.environ['NEUTRINO_HOME']
    cfg_ffn = os.path.join(neutrino_home, DYNAMODB_CONFIG_FN)

    # init DynamoDB
    rstat, rval = init_dynamodb(cfg_ffn)

    if not rstat:
        logging.warning(f'Some table creation failed with message: {rval}')


'''
    # For testing
    table_name = 'gg_test1'
    primary_key = 'gg_test1_pri'
    secondary_key = 'gg_test1_sec'
    gg_test1_table_schema = [
        {
            'AttributeName': 'gg_test1_pri',
            'AttributeType': 'S'      # S = String
        },
        {
            'AttributeName': 'gg_test1_sec',
            'AttributeType': 'N'      # N = Number
        },
    ]

def create_table(table_name, table_schema, primary_key, secondary_key=None,
                 billing_mode='PAY_PER_REQUEST', other_attributes={},
                 aws_region=aws_settings.AWS_DEFAULT_REGION):

'''
