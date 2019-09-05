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
RUN pip install pip pyyaml==3.13 boto3==1.9.111

# Set env variables
ENV PYTHONPATH="/opt"

# For debug
# ENV NEUTRINO_VALID_CAMS="Aruba_SLR01_Cams:slr01_bldg_d_f1_rear_lobby_entrance"


WORKDIR /opt/neutrino/source/apps/docker_utils/code
ENTRYPOINT ["python", "cam2pub.py"]
# CMD tail -f /dev/null
