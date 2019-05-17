''' Testing for the file utilities '''

import pytest
import os
import yaml
from pathlib import Path

# Neutrino import
from neutrino.source.utils import file_utils

# Constants
NEUTRINO_HOME = Path(os.environ['NEUTRINO_HOME'])
YAML_FN = NEUTRINO_HOME/'source/apps/docker_utils/configs/aruba_cams.yml'

def test_yaml2dict():
    ''' Test the YAML file to dict converter '''
    # Enhancements: Test with  a more complicated YAML file

    # This may sound like a dumb test, but this is a crucial function,
    # So adding this seemingly trivial test

    # First load the test YAML file
    with open(YAML_FN) as fh:
        correct_dict = yaml.load(fh)

    # Now load via the funtion to test
    test_dict = file_utils.yaml2dict(YAML_FN)

    assert correct_dict == test_dict

