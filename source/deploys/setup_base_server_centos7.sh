#! /bin/bash

# This script is used to setup a neturino base server. This is the server
# that will run all the application and infra dockers.
# This script is for servers running centos 7

# This script dores the following setups:
#    1) Instals python 3.6.5
#    2) Creates a python3 env called: npy3
#    3) Sets up docker (engine, client, etc.)

set -e

function yum_update {
    # Start by making sure your system is up-to-date:
    # Note: Need to be careful about this. 
    #       Maybe its best to let user do this step
    echo "$(tput setaf 2) Running yum update $(tput sgr 0)"
    yum -y update
}

function install_dev_tools {
    echo "$(tput setaf 2) Installing dev tools $(tput sgr 0)"
    # Install Compilers and related tools:
    yum groupinstall -y "development tools"

    # Libraries needed during compilation to enable all features of Python:
    yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel

    # If you are on a clean "minimal" install you also need the wget tool:
    yum install -y wget
}

function install_python3 {
    echo "$(tput setaf 2) Installing python3 $(tput sgr 0)"
    # Now start install of python3.
    # Note: python 3.6.5 is being installed (this is the latest version as of
    #       April, 2018.
    #       python 2.x is being left alone as its best NOT to mess with this on
    #       CentOS 7
    wget http://www.python.org/ftp/python/3.6.5/Python-3.6.5.tar.xz
    tar xf Python-3.6.5.tar.xz
    cd Python-3.6.5
    ./configure --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
    make && make altinstall
}

function install_pip3 {
    echo "$(tput setaf 2) Installing pip3 $(tput sgr 0)"
    # Install pip3
    # First get the script:
    wget https://bootstrap.pypa.io/get-pip.py
    # Then execute it using Python 3.6:
    python3.6 get-pip.py
}

function make_venv {
    echo "$(tput setaf 2) Settingup venv npy3 $(tput sgr 0)"
    # Make the virtualenv npy3 and install python
    python3.6 -m venv npy3
}

# Run all of the steps
yum_update
install_dev_tools
install_python3
install_pip3
make_venv

