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

# Set logging level
logging.basicConfig(level=logging.INFO)


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
            print(status_bool)
            if status_bool:
                logging.info(f'Successfully created thing type '
                             f'"{thing_type_name}"')
            else:
                logging.info(f'Failed to create thing type "{thing_type_name}" '
                             f'API call returned: {resp}')


def init_iot_core():
    ''' This will do all of the necessary AWS IoT Core initialition needed for
        running neutrino apps 

        Arugments: None
        Return: None
    '''

    # Determine the config file path
    neutrino_home = os.environ['NEUTRINO_HOME']
    config_ffn = os.path.join(neutrino_home, 
                              'source/configs/aws/aws_iot_core.yml')
    iot_core_cfg_dict = file_utils.yaml2dict(config_ffn)
    thing_type_list = iot_core_cfg_dict['aws_iot_core_init']['thing_types']
    things_list = iot_core_cfg_dict['aws_iot_core_init']['things']

    # Now initialize the Core IoT Thing Types needed
    init_thing_types(thing_type_list)
    # And then initialize the Core IoT Things

if __name__ == '__main__':
    init_iot_core()


