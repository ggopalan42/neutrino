''' This code runs all that is necessary to run lambda functions on AWS
    for project neutrino

    The steps that this code performs are:
        - Created all needed functions
'''

import os
import logging
import time

from neutrino.source.utils import file_utils
from pylibs.cloud.aws.dynamodb import dynamodb_utils

# Constants
DYNAMODB_CONFIG_FN = 'source/configs/aws/aws_dynamodb.yml'
DYNDB_CREATE_TABLE_TIMEOUT = 60    # Seconds. At some point, this 
                                   # should move to a central config location

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
        Returns: Nothing
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
    return True, True

def create_dyndb_tables(config_fn):
    ''' Create all needed DynamoDB tables

        Arguments:
            - config_fn: path to the config file relative to NEUTRINO_HOME

        Returns: Nothing
    '''

    # Setup some paths
    neutrino_home = os.environ['NEUTRINO_HOME']

    # Load the lambda config
    ffn = os.path.join(neutrino_home, config_fn)
    dyndb_cfg_dict = file_utils.yaml2dict(ffn)

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
            resp = create_single_table(table_name, table_args_dict)



########################### Delete below here #######################
def create_functions():
    ''' This will create all of the functions specified in aws_lambda.yml
    '''

    # Open a client for lambda functions
    lambda_client = boto3.client('lambda')

    # Setup some paths
    neutrino_home = os.environ['NEUTRINO_HOME']

    # Create a temp directory. This is to hold the lambda zip files
    tempdir_handler = tempfile.TemporaryDirectory()
    tempdir_name = tempdir_handler.name

    # Load the lambda config
    ffn = os.path.join(neutrino_home, LAMBDA_CONFIG_FN)
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

def init_dynamodb():
    ''' This will initialize all of the databases needed for neutrino

        Arugments: None
        Return: None
    '''
    create_dyndb_tables(DYNAMODB_CONFIG_FN)

if __name__ == '__main__':
    # Set logging level
    logging.basicConfig(level=logging.INFO)

    init_dynamodb()


