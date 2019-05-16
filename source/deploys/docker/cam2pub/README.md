## This will build a docker image based on Ubuntu 18.04 with python 3.7 OpenCV
### The main use of this image is to gather inputs from Video cameras and publish frames as numpy ndarray 

### Some Notes:
- Since in Docker only files from the local build context can be added to the container, at this point, I have decided to soft link files that are needed to a dir under the build context. For now, this dir will be called neutrino and will be copied to the container: /opt/neutrino


