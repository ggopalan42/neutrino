#! /usr/bin/env python
''' Load configs needed for cam2pubsub function '''

# Python lib imports
import cv2
import base64
import os
import sys
import yaml
import logging

import numpy as np

from collections import defaultdict


# Neutrino lib imports
from neutrino.source.utils import file_utils


# Constants
CONFIG_DIR = '../configs/'
LIST_OF_MLMODELS = 'list_of_mlmodels.yml'

# Other variables

# Set logging level
logging.basicConfig(level=logging.INFO)

class mobilenetssd_v1():
    ''' MoblenetSSD V1 model parameters '''
    def __init__(self, mlmodel_dict):
        self.model_name = mlmodel_dict['model_name']
        self.model_file = mlmodel_dict['model_file']
        self.prototxt_file = mlmodel_dict['prototxt_file']
        self.classes = mlmodel_dict['model_params']['object_classes'].split()
        self.min_confidence = mlmodel_dict['model_params']['confidence']
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3))
        # previous_det is a stupid hack. I have not figured out a way around
        self.previous_det = np.array([[[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]]])
        # Below is needed for person identification purposes only
        self.person_idx = self.classes.index('person')

    # Public methods
    def load_dnn_model(self):
        model_name = self.model_name
        logging.info('Loading net and weights for model: {}'.format(model_name))
        self.net = cv2.dnn.readNetFromCaffe(self.prototxt_file,
                                                        self.model_file)


# The below dict maps model names to model classes.
ml_models_class_map = {
    'MobilenetSSD_V1': mobilenetssd_v1
}

class all_mlmodels_config():
    ''' Config object for ML models '''
    def __init__(self, all_mlmodel_dict):
        self.mlmodel_names = []    # List of mlmodels specified
        self.mlmodel_config = {}   # And their configs keyed by their names
        # Load their configs
        self.all_mlmodel_dict = all_mlmodel_dict
        self._load_mlmodels_config()

    # Private methods
    def _load_mlmodels_config(self):
        ''' Load configs of mlmodels specified in the all_mlmodel_dict

        Arguments (implicit via self):
                all_mlmodel_dict: Dict of the configs of all mlmodels

            Return:  The class itself
        '''
        for mlmodel_name, mlmodel_dict in self.all_mlmodel_dict.items():

            try:
                # Init the ml object
                tmp_dict = mlmodel_dict['model']
                model_config_obj = ml_models_class_map[mlmodel_name](tmp_dict)
                # Set the inited object as an attribute to this class. 
                # The attribute is the name of the ml model specified in file
                self.mlmodel_names.append(mlmodel_name)
                self.mlmodel_config[mlmodel_name] = model_config_obj
            except KeyError:
                logging.error('Class to load model named {} not implemented'
                                           .format(model_name))
                raise RuntimeError('Class to load model named {} not '
                                           'implemented'.format(model_name))

    # Public Methods
    def load_all_dnn_models(self):
        ''' Load the network for all ML models '''
        for mlmodel_name in self.mlmodel_names:
            # For each model name, get the model object
            mlmodel_obj = self.mlmodel_config[mlmodel_name]
            # Then load the network
            mlmodel_obj.load_dnn_model()

    def get_dnn_model(self, mlmodel_name):
        ''' Given a model name, return the corresponding ml model object ''' 
        return self.mlmodel_config[mlmodel_name]


def load_all_mlmodel_config():
    ''' This will load the mlmodel config into a dictionary
        and return it. 

        Arguments: None

        Returns: dict with all mlmodel configs
    '''

    # Setup some stuff
    all_mlmodel_config_dict = defaultdict(list)
    configs_dir = CONFIG_DIR 
    list_of_mlmodels_fn = LIST_OF_MLMODELS 

    ffn = os.path.join(configs_dir, list_of_mlmodels_fn)
    logging.info(f'Loading all mlmodels from: {ffn}')
    list_of_mlmodels_dict = file_utils.yaml2dict(ffn)
    for mlmodel_fn in list_of_mlmodels_dict['ml_models']:
        ffn = os.path.join(configs_dir, mlmodel_fn)
               # Load the camera group config
        logging.info(f'Loading mlmodel config: {ffn}')
        # Read in the mlmodel configs
        mlmodel_dict = file_utils.yaml2dict(ffn)
        mlmodel_name = mlmodel_dict['model']['model_name']
        all_mlmodel_config_dict[mlmodel_name] = mlmodel_dict

    return all_mlmodel_config_dict


if __name__ == '__main__':
    all_mlmodel_dict = load_all_mlmodel_config()
    mlmodels_obj = all_mlmodels_config(all_mlmodel_dict) 
    mlmodels_obj.load_all_dnn_models()

