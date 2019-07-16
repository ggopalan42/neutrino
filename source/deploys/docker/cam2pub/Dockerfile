# syntax=docker/dockerfile:experimental

FROM nbase_py37_opencv3
LABEL author="ggopalan"
LABEL project="neutrino"
MAINTAINER Giri Gopalan <ggopalan42@gmail.com>

# Prepare for cloning private repos from git.
# download public key for github.com
RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
# ~lone private repos: neutrino and pylibs
RUN --mount=type=ssh git clone git@github.com:ggopalan42/neutrino.git /opt/neutrino
RUN --mount=type=ssh git clone git@github.com:ggopalan42/pylibs.git /opt/pylibs

# Install required packages
RUN pip install pip pyyaml boto3

# Set env variables
ENV PYTHONPATH="/opt"

WORKDIR /opt/neutrino/source/apps/docker_utils/code
ENTRYPOINT ["python", "cam2pub.py"]
