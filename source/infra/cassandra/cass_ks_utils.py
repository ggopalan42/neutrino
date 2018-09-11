#! /usr/bin/env python

''' Cassandra keySpace utilities:
      - Using this script, Keyspaces can be created and deleted
      - This script is wirtten such that it can be used as a module '''

import os
import sys
import argparse
import logging

from cassandra.cluster import Cluster

# Local imports
import cass_utils as cu

# Set logging level
logging.basicConfig(level=logging.INFO)

# Constants
HOSTNAME = '127.0.0.1'       # Localhost. Later move this to a config
SYSTEM_KS = ['system_schema', 'system', 'system_distributed', 
             'system_auth', 'system_traces',]
KEYSPACE_NAME = 'gg_expt2'    # The keyspace in which to create the table

def parse_args():
    ''' Parse the arguments and return a dict '''
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser(
       description='This script adds or deletes keyspace to the Cassandra DB',
       usage='./cass_ks_utils.py [-a|-d] <keyspace-name>')

    ap.add_argument("-a", "--add-ks",
            help="Keyspace name to add")
    ap.add_argument("-d", "--delete-ks",
            help="Keyspace name to delete")
    args = vars(ap.parse_args())

    return args

def create_keyspace(cass, ks_name):
    ''' Create specified keyspace in Cassandra DB if it does not exist '''
    cmd = ("CREATE KEYSPACE IF NOT EXISTS {ks_name} "
           "WITH REPLICATION = {replication};").format(
                         ks_name=ks_name, replication=cass.get_replication())
    logging.info('Creating keyspace with command: {}'.format(cmd))
    retval = cass.session.execute(cmd)
    # TBD: Not too sure how to check for creating failures
    logging.info('Create command returned: {}'.format(retval))

def delete_keyspace(cass, ks_name):
    ''' Delete specified keyspace in Cassandra DB  '''
    cmd = "DROP KEYSPACE {ks_name} ".format(ks_name=ks_name)
    logging.info('Deleting keyspace with command: {}'.format(cmd))
    retval = cass.session.execute(cmd)
    # TBD: Not too sure how to check for creating failures
    logging.info('Delete command returned: {}'.format(retval))

def main():
    ''' main program '''
    args = parse_args()
    # Connect to cassandra db
    cass = cu.cassandra_cluster([HOSTNAME])

    if args['add_ks']:
        logging.info('Adding Keyspace {} to Cassandra DB'
                                                    .format(args['add_ks']))
        create_keyspace(cass, args['add_ks'])
    elif args['delete_ks']:
        logging.info('Deleting Keyspace {} from Cassandra DB'
                                                  .format(args['delete_ks']))
        delete_keyspace(cass, args['delete_ks'])
    else:
        logging.error('Need to specify either add or delete option')
    cass.cleanup()

if __name__ == '__main__':
    main()
