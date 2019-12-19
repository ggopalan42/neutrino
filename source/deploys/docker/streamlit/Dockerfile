# syntax=docker/dockerfile:experimental

FROM nbase_py37_opencv3
LABEL author="ggopalan"
LABEL project="neutrino"
MAINTAINER Giri Gopalan <ggopalan42@gmail.com>

# Prepare for cloning private repos from git.
# download public key for github.com
RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
# clone private repos: neutrino and pylibs
RUN --mount=type=ssh git clone git@github.com:ggopalan42/neutrino.git /opt/neutrino
RUN --mount=type=ssh git clone git@github.com:ggopalan42/pylibs.git /opt/pylibs

# Install required packages
RUN pip install pip streamlit    # pyyaml==3.13 boto3==1.9.111

# Set env variables
ENV PYTHONPATH="/opt"

# Copy some file
# When using streamlit run, can kill the copy and use server.headless, 
# --server.port and --browser.serverAddress on the command line
COPY st_config.toml /root/.streamlit/config.toml
COPY st_credentials.toml /root/.streamlit/credentials.toml

# For debug
# ENV NEUTRINO_VALID_CAMS="Aruba_SLR01_Cams:slr01_bldg_d_f1_rear_lobby_entrance"

# Uncomment below to set workdir from which ENTRYPOINT cna be run
# WORKDIR /opt/neutrino/source/apps/docker_utils/code

# Old: ENTRYPOINT ["python", "script_name.py"]
# Old: CMD tail -f /dev/null

# Uncomment below when when running python code. the --options are, well, 
# optional
# CMD streamlit run --server.headless true --server.port <port#> --browser.serverAddress <ip_addr> <python_script.py>

# Uncomment below to run the demo
CMD streamlit hello
