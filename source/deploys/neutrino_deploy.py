''' This is the  main deploy file to bringup the entire neutrino application '''

import os
import sys

from neutrino.source.utils.file_utils import yaml2dict

# Constants
DEPLOY_PATH = 'source/configs/deploys'     # Relative to NEUTRINO_HOME
DEPLOY_FN = 'neutrino_deploy.yaml'

def main():
    neutrino_home = os.environ['NEUTRINO_HOME']
    deploy_fn = os.path.join(neutrino_home, DEPLOY_PATH, DEPLOY_FN)
    print(deploy_fn)


if __name__ == '__main__':
    main()
