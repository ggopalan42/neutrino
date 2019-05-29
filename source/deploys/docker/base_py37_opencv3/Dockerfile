### Acknowledgement: The started for this dockerfile was from:
#                    https://github.com/janza/docker-python3-opencv
FROM python:3.7
LABEL author="ggopalan"
LABEL project="neutrino"
MAINTAINER Giri Gopalan <ggopalan42@gmail.com>

RUN apt-get update \
    && apt-get install -y \
        git \
        wget \
        unzip \
        vim

RUN pip install ipython
RUN pip install numpy
RUN pip install opencv-contrib-python-headless
