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
    - These images are then brought up and run via configurations in the local_docker_deploys dir (in other words, this is the dir that contains the orchestration parts)


## local_docker_deploys:
     - This contains a number of docker compose yaml files that run several docker containers locally (that is local server) that is part of the neutrino application
