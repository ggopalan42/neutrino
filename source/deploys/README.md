# Deploy Scripts

This is where all deploy scripts reside. These scripts are used to setup various types of bare machines (servers, rpis, etc.)

## CentOS 7 Setup:
    - Setup a CentOS 7 server with the required hardware specs
    - Install CentOS 7. Even a minimal install will do
    - Copy the script: "setup_base_server_centos7.sh" to the server's "/root"
    - Login to server and change the script to be executable
    - Run the script
    - Good luck! 

## docker:
    - This dir contains a number of sub dirs that each will build an image.
    - These images are then brought up and run via configurations in the docker_compose dir (in other words, this is the dir that contains the orchestration parts)

    - Specific documentation for cam2pub:
        - For cam2pub to run, this is the sequence:
            1. First build all base images (That is run docker_make_base_images.sh)
            2. Then cd into cam2pub and run "make build". This step is needed whenever anything is pushed into github. These builds are run with caching off so they pull from github everytime. Not sure how to do it more efficiently
            3. Then use the corresponding docker_compose to get the application up and running



## local_docker_deploys:
     - This contains a number of docker compose yaml files that run several docker containers locally (that is local server) that is part of the neutrino application

## AWS IoT Core:
    - This code to deploy to AWS IoT Core is under: ./cloud/aws/aws_iot_core
    - The code "init_iot_core.py" under this dir needs to be run to setup
      AWS IoT Core for neutrino

## Initialization steps for Neutrino
1. Run init_iot_core.py located at: neutrino/source/deploys/cloud/aws/aws_iot_core. This will init AWS IoT Core
2. 
