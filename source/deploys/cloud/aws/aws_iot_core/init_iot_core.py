''' This code runs all that is necessary to setup AWS IoT code for
    neutrino

    The steps that this code performs are:
        - Check and create the thing types specified in the config file
        - Check and create the things specified in the config file
'''

import os
import logging

from neutrino.source.utils import file_utils
from pylibs.cloud.aws.iot_core import iot_core_utils

# Constants
IOT_CORE_CONFIG_FILE = 'source/configs/aws/aws_iot_core.yml'


def init_thing_types(thing_type_list):
    ''' Initialize AWS IoT Core Thing Types 

        Arguments: thing_type_dict: A list of dicts. Each
                   dict key is the thing types to be created and value is 
                   to be used in setting the thing type properties and tags
    '''
    # First get the list of thing types already created in AWS IoT Core
    aws_thing_type = iot_core_utils.aws_iot_thing_type()
    existing_thing_types, _ = aws_thing_type.list_all_thing_types()

    # Iterate over the dict keys
    for tt in thing_type_list:
        # Surely there is a better way to do this?
        thing_type_name = list(tt.keys())[0]
        thing_type_params = list(tt.values())[0]

        # Check if thing type already exists.
        if thing_type_name in existing_thing_types:
            # Just log and continue
            logging.info(f'AWS IoT Thing Type "{thing_type_name}" already '
                         'exists. Continuing . . . ')
            continue
        else:
            logging.info(f'Creating AWS IoT Thing Type "{thing_type_name}"')
            # Extract the properties and tags for the thing_type_name
            properties = thing_type_params['properties']
            # Getting the tags is a bit more manipulations
            tags_list = thing_type_params['tags']
            # After this, tags_tmp will looks like: 
            # ['Key: type1, Value: camera1', 'Key: type2, Value: camera2']
            # Below converts this to a list of dicts
            tags = []
            for s in tags_list:
                # Remove all whitespace from the string as AWS API
                # will bomb if there are spaces in the keys
                s = s.replace(' ', '')
                d = dict(x.split(':') for x in s.split(','))
                tags.append(d)
            resp = aws_thing_type.create_thing_type(thing_type_name, 
                                      properties=properties, tags=tags)
            status_bool,status_code = iot_core_utils.check_response_status(resp)
            if status_bool:
                logging.info(f'Successfully created thing type '
                             f'"{thing_type_name}"')
            else:
                logging.info(f'Failed to create thing type "{thing_type_name}" '
                             f'API call returned: {resp}')

def init_things(things_list):
    ''' Initialize things in AWS IoT Core

        Arguments:
            - things_list: A dictionary whose keys are the names of things 
                           to create and values are the parameters for the thing
    '''
    # First get the list of things already created in AWS IoT Core
    aws_things = iot_core_utils.aws_iot_all_things()
    existing_things, _ = aws_things.list_all_things()

    # Iterate over thing_list
    for thing_name, thing_params in things_list.items():
        # Check if the thing_name has already been created
        if thing_name in existing_things:
            # Log this fact and continue
            logging.info(f'AWS IoT Thing "{thing_name}" already '
                         'exists. Continuing . . . ')
            continue
        else:
            # Create this thing. LoL
            thing_type_name = thing_params['thing_type_name']
            resp = aws_things.create_thing(thing_name, thing_type_name)
            status_bool,status_code = iot_core_utils.check_response_status(resp)
            if status_bool:
                logging.info(f'Successfully created thing "{thing_name}"')
            else:
                logging.info(f'Failed to create thing "{thing_name}" '
                             f'API call returned: {resp}')




def init_iot_core(config_file=IOT_CORE_CONFIG_FILE):
    ''' This will do all of the necessary AWS IoT Core initialition needed for
        running neutrino apps 

        Arugments: Optional config file (YAML)
        Return: None
    '''

    # Determine the config file path
    neutrino_home = os.environ['NEUTRINO_HOME']
    config_ffn = os.path.join(neutrino_home, IOT_CORE_CONFIG_FILE) 
    iot_core_cfg_dict = file_utils.yaml2dict(config_ffn)
    thing_type_list = iot_core_cfg_dict['aws_iot_core_init']['thing_types']
    things_list = iot_core_cfg_dict['aws_iot_core_init']['things']

    # Now initialize the Core IoT Thing Types needed
    init_thing_types(thing_type_list)
    # And then initialize the Core IoT Things
    init_things(things_list)

if __name__ == '__main__':
    # Set logging level
    logging.basicConfig(level=logging.INFO)

    init_iot_core()


