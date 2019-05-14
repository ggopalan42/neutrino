#! /bin/bash

DOCKER_BASE_DIRS=( "base_py37" "base_py37_opencv3" )


# Loop over the base dirs and build the docker images
for dir in "${DOCKER_BASE_DIRS[@]}"
do
    echo "$(tput setaf 2)Building docker image $dir $(tput sgr 0)"
    cd $dir && make build
    cd ..
done
