#!/usr/bin/env bash

# This script is used to setup a neturino base server. This is the server
# that will run all the application and infra dockers.
# This script is for servers running centos 7

# This script dores the following setups:
#    1) Instals python 3.6.5
#    2) Creates a python3 env called: npy3
#    3) Sets up docker (engine, client, etc.)

PRODUCT_CODE_NAME=neutrino
NPY3_VENV_NAME=npy3

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
    echo "$(tput setaf 2) Setting up venv npy3 $(tput sgr 0)"
    # make directory for virtual env
    mkdir -p /opt/$PRODUCT_CODE_NAME/venvs/
    # Make the virtualenv npy3 and install python
    python3.6 -m venv /opt/$PRODUCT_CODE_NAME/venvs/$NPY3_VENV_NAME
}

function install_python_packages {
    echo "$(tput setaf 2) Installing python packages in $NPY3_VENV_NAME $(tput sgr 0)"
    # Switch to the appropriate env
    source /opt/neutrino/venvs/$NPY3_VENV_NAME/bin/activate
    pwd
    pip install -r requirements_centos7.txt 
}

function install_start_docker {
    echo "$(tput setaf 2) Install and start docker $(tput sgr 0)"
    yum -y install docker   # maybe good idea to install a particular version
    # Enable docker to start on reboot
    systemctl enable docker.service
    # Start docker
    systemctl start docker
}

function set_bash_aliases {
echo "$(tput setaf 2) Setup bash aliases, including activation of venv $(tput sgr 0)"
# Create .bash_aliases file if it does not exist
# if [[ ! -e $HOME/.bash_aliases ]]; then
#  touch $HOME/.bash_aliases
# fi
# Add needed aliases to bashrc file and source it
cat <<EOT >> ~/.bashrc

alias src='source /home/ggopalan/.bashrc'
alias tailf='tail -f'
alias npy3='source /opt/neutrino/venvs/npy3/bin/activate'
EOT
}

# Run all of the steps
yum_update
install_dev_tools
install_python3
install_pip3
make_venv
install_start_docker      # Note: This has not been tested extensively
install_python_packages
set_bash_aliases

echo "$(tput setaf 2) Please start a new bash shell or run 'source ~/.bashrc' to complete setup $(tput sgr 0)"
