#! /usr/bin/env python
''' This code will get images from specified cameras, detect objects in them
    using a standard model and publish these to a pubsub.

    Note: At this point, a shortcut is being taken and results published 
          directly to AWS or local kafka container. Later on, a 
          proper publish will be established. 
'''

# Python lib imports
import cv2
import os
import sys
import logging
import json

# Local imports
import neutrino.source.apps.app_utils.obj_nn_utils as obj_nn
import load_cam_configs
import load_mlmodel_configs

# Set logging level
# Not set in the function: set_logging.logging.basicConfig(level=logging.INFO)

# Constants

# Temp definitions
ML_MODEL_TO_USE = 'MobilenetSSD_V1'
MESSAGE_FORMAT_VERSION = '1.0.0'

def cam2pub(cam_conf, mlmodels_conf, ml_model_name=ML_MODEL_TO_USE):
    ''' Read from image, identify objects and publish ided objects '''
    model_obj = mlmodels_conf.get_dnn_model(ml_model_name)
    message_format_version = MESSAGE_FORMAT_VERSION

    # Go through each camera and count the number of people in them
    for cam_grp_name in cam_conf.cam_grp_names:
        # Get the cams config object for the cams_grp group and further
        # dive into it
        cam_grp_config_obj = cam_conf.get_cam_grp_config_obj(cam_grp_name)
        cam_grp_stream_name = cam_conf.get_cam_grp_stream_name(cam_grp_name)
        # Now go through each cam in that cams group
        for cam_name in cam_grp_config_obj.cam_names:
            cam_obj = cam_grp_config_obj.get_cam_obj(cam_name)
            # Process camera only if valid
            if cam_obj.valid:
                cam_stream_name = cam_obj.get_cam_stream_name()

                # Read from cam and process for objects if valid image
                valid_image, image = cam_obj.cap_handle.read()
                if valid_image:
                    # Write image to file if requested. Note here that the image
                    # is written is as captured from cam (i.e. not annonated)
                    if cam_obj.videowriter:
                        cam_obj.videowriter.write(image)

                    # ID Objects
                    # WARNING: The first argument to obj_nn.id_objects is not
                    #          used by that function. So passing some junk in
                    #          there for backwards compability. This is
                    #          obviously "NOT GOOD" (TM). It will be fixed
                    #          when I do a re-structuring
                    ided_objects = obj_nn.id_objects(cam_conf, image, model_obj,
                       display_predictions = cam_obj.get_display_predictions())

                    # Show image if requested.
                    if cam_obj.get_display_image():
                        cv2.imshow(cam_name, image)
                        cv2.waitKey(1)

                    # If objects(s) have been detected in this image, 
                    # send results out
                    if len(ided_objects) > 0:
                        # WARNING: The first argument to obj_nn.id_objects is 
                        #          not used by that function. So passing some 
                        #          just there for backwards compability. This is
                        #          obviously "NOT GOOD" (TM). It will be fixed
                        #          when I do a re-structuring
                        message_dict = obj_nn.format_message(cam_conf, 
                                     ided_objects,
                                     cam_grp_stream_name, cam_stream_name, 
                                     message_format_version)
                        message_str = json.dumps(message_dict)
                        # Simply print it for now
                        logging.info('Object(s) detected in image: {}'
                                                   .format(message_str))
                    else:
                        logging.info('No object IDed in image')
                else:
                    # If image read failed, log error
                    logging.error('Image read from camera {} failed. '
                                  '(error ret = {}'.format(cam_name, 
                                  valid_image))


def main_loop(cam_conf, mlmodels_conf):
    ''' Continously detect persons and quit on keyboard interrupt '''
    try:
        while True:
            cam2pub(cam_conf, mlmodels_conf)
    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Exiting . . . ')
        cam_conf.release_all_cams()
        return ['Keyboard Interrupt. Exiting']

def set_logging():
    ''' Setup logging so it works on both containers and locally

        The basic idea is to log to the specified file if os environment
        variable is set or to stdout if its not set
    '''

    if 'LOG_TO_FILE' in os.environ.keys():
        log_fn = os.environ['LOG_TO_FILE']
        # Now setup the logging.
        print(f'Logging everything to {log_fn}')
        logging.basicConfig(level=logging.INFO, filename=log_fn,
                            format='%(asctime)s - %(name)s - '
                            '%(levelname)s - %(message)s')



if __name__ == '__main__':
    APP_NAME = 'camfeeds1'
    SEND_TO_KAFKA = False

    # Initialize
    # Set logging
    set_logging()
    # Connect to all cams
    # cam_config_dict = load_cam_configs.load_all_cams_config()
    cam_config_dict = load_cam_configs.docker_load_all_cams_config()
    cam_conf = load_cam_configs.all_cams_config(cam_config_dict)
    cam_conf.connect_to_all_cams()

    # Load and initialize all ML models
    all_mlmodel_dict = load_mlmodel_configs.load_all_mlmodel_config()
    mlmodels_conf = load_mlmodel_configs.all_mlmodels_config(all_mlmodel_dict)
    mlmodels_conf.load_all_dnn_models()

    # Do the main loop
    main_loop(cam_conf, mlmodels_conf)

    # cleanup when done
    cam_conf.release_all_cams()

