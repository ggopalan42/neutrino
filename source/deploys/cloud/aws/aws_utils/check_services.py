''' This utility checks that various services are up '''

# This utility will check that the services specified are up
# It will return a True is the services are up (or are reachable)
# or a False (and error message) if a timeout occurs

# Specify Timeouts
# Note: At a later re-factoring stage, maybe move all of these constants to
#       another central place

import boto3
import json
import logging

from typing import List

from pylibs.io.logging_utils import set_logging



TIMEOUT = 30 * 60    # Timeout is 30 mins

# This really must be done in a central YAML file
SERVICES_TO_CHECK = [
                      'aws-iot',
                      'aws-iot-data-message',
                    ]


def check_aws_iot() -> (bool, str):
    ''' This function will do simple client connect to AWS 'iot-data'
        - Arguments: None

        - Returns:
              - True, 'OK': if successful
              - False, <error msg>: If failed
    '''

    logging.info('Checking aws-iot on startup')
    try:
        client = boto3.client('iot-data')
    except Exception as e:
        print(e)
    
    
def check_aws_iot_data_message() -> (bool, str):
    ''' This function will send a message via 'iot-data' service to
        AWS and will return a success or failure message

        - Arguments: None

        - Returns:
              - True, 'OK': if successful
              - False, <error msg>: If failed
    '''

    # Setup message
    # Note: These all can be configured later if need be
    message = {'aws-startup-test' : 'aws-iot-data-startup-test'}
    topic = 'aws-test/startup-test'
    qos = 1    # Does not really matter
    message_json = json.dumps(message)
 
    logging.info('Checking aws-iot-data send message  on startup')
    try:
        client = boto3.client('iot-data')
        client.publish(topic=topic, qos=qos, payload=message_json)
 
    except Exception as e:
        print(e)
    
    
# Sevice type to function map
# Sevice type to function map
SERVICE_FUNCTION_MAP = {
    'aws-iot': check_aws_iot, 
    'aws-iot-data-message': check_aws_iot_data_message, 
}

def check_services_or_timeout(services_list: List[str]) -> (bool, str):
    ''' Check for services in services list and timeout if they do not
        suceed '''

    for service in services_list:
        SERVICE_FUNCTION_MAP[service]()



if __name__ == '__main__':

    set_logging()

    check_services_or_timeout(SERVICES_TO_CHECK)
