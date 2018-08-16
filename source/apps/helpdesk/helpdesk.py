#! /usr/bin/env python
''' analyze helpdesk camera and provide useful stats '''

# Python lib imports
import os
import sys
import yaml
import logging
import argparse

# Local imports
import load_app_configs as lc
import cam2kaf

# Config file definition
HELPDESK_CONFIG = 'helpdesk.yml'

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

# Unfortunately this one function has to be repeated in all apps
# as this defines and sets the home variable
def parse_args():
    ''' Parse the arguments and return a dict '''
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--neutrino-home",
            help="Specify home dir of project")
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

if __name__ == '__main__':
    # Initialize
    args = parse_args()
    co = lc.config_obj(args)
    # ------ Connect to camera
    print(co.list_of_cams)
    print(co.aruba_cams.all_cams_name)
    print(co.aruba_cams.cam_config)
    # cam2kaf.main_loop(co)

