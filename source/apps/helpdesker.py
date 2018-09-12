#! /usr/bin/env python
''' Taked helpdesk images and sends detected objects to Kafka '''

# Python lib imports
import argparse
import os
import yaml
import sys
import logging

# Local imports
# import count_people_from_image as cp
import cam2kaf as c2k
import load_app_configs as lc

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

# Constants
APP_NAME = 'helpdesk'
SEND_TO_KAFKA = False
HELPDESK_YAML = './helpdesker.yaml'

# This is only if this is used as a main program
def parse_args():
    ''' Parse the arguments and return a dict '''
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--neutrino-home",
            help="people Counter config YAML file")
    args = vars(ap.parse_args())

    # Check if NEUTRINO_HOME is provided as args. If not, check 
    # that its provided via env variable. If not, raise an error
    if not args['neutrino_home']:
        try:
            neutrino_home = os.environ['NEUTRINO_HOME']
            args['neutrino_home'] = neutrino_home
        except KeyError as e:
            raise RuntimeError('Need to set NEUTRINO_HOME or '
                               'provide it using the -n option') from e
    return args

def main_loop(co):
    ''' Continously detect persons and quit on keyboard interrupt '''
    try:
        while True:
            c2k.cam2kaf(co)
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Exiting . . . ')
        co.cleanup(cams_name)
        return ['Keyboard Interrupt']

if __name__ == '__main__':
    # This is for testing
    # This can also be used as a tamplate for future apps
    # Initialize
    args = parse_args()
    co = lc.config_obj(args)
    co.set_app_name(APP_NAME)
    co.set_kafka_send_state(SEND_TO_KAFKA)

    # Load ml model parameters
    ml_model_name = co.get_app_mlmodel(APP_NAME)
    co.load_dnn_model(ml_model_name)

    # Connect to cams
    cams_name = co.get_app_cams_name(APP_NAME)
    co.connect_to_cams(cams_name)

    # Connect to Kafka
    # kafka_params_dict = co.get_app_kafka_params(APP_NAME)
    co.set_kafka_app_obj(APP_NAME)

    # Do the main loop
    main_loop(co)

    # cleanup when done
    co.cleanup(cams_name)

