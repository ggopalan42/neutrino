#! /bin/bash

# The following two vars are set such that it will be easier when/if the 
# source structure changes. It may be better if they are passed in as args
DOCKER_CODE="source/apps/docker_utils/code"
DOCKER_CONFIG="source/apps/docker_utils/configs"

# Copy all requred files locally.. I think this is a stupid way to do
# this. There should be a better way. But in the spirit of moving quickly,
# going with this

# First clear out the local neutrino directory
rm -f neutrino/*

# Then link
cp $NEUTRINO_HOME/$DOCKER_CODE/cam2pub.py ./neutrino/cam2pub.py
cp $NEUTRINO_HOME/$DOCKER_CODE/load_cam2pub_configs.py ./neutrino/load_cam2pub_configs.py
cp $NEUTRINO_HOME/$DOCKER_CONFIG/list_of_cams.yml ./neutrino/list_of_cams.yml
cp $NEUTRINO_HOME/$DOCKER_CONFIG/aruba_cams.yml ./neutrino/aruba_cams.yml
