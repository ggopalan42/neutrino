help:
	cat Makefile
build:
	DOCKER_BUILDKIT=1 docker build --ssh default=${HOME}/.ssh/git_repo -t cam2pub .
copy:
	./copy_files.sh
