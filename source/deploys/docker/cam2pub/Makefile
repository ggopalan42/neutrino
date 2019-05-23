# MAke file for making cam2pub (camera to pubsub)

# Variables. So they can be overridden when the whole application is built

REPO_NAME=local
VERSION=0.1

help:
	cat Makefile
# The DOCKER_BUILDKIT shenanigan is being used because I did not want to bang
# any private keys into the image
build:
	DOCKER_BUILDKIT=1 docker build --ssh default=${HOME}/.ssh/git_repo  \
                                       -t $(REPO_NAME)/cam2pub:$(VERSION) .
