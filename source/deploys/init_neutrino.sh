#! /bin/bash

This is fake (pseudo) code for initializing neutrino app.
This is supposed to be run once per deploy

1. Run docker/docker_make_base_images.sh
    - This will make the base python and opencv images for furtehr use
2. Run "make build" on docker/cam2pub dir
    - This will make the main cam2pub image for use by compose
3. Run: ./cloud/aws/aws_iot_core/init_iot_core.py. 
    - This will init IoT Core by setting up thing groups and rules
4. 
   
