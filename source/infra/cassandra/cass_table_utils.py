#! /usr/bin/env python

# Example commands for some quick shenanigans:
#   ./cass_table_utils.py -a gg_table2 -k gg_expt2    -> Add table
#   ./cass_table_utils.py -d gg_table2 -k gg_expt2    -> Delete table

''' Cassandra Table utilities:
      - Using this script, Tables can be created and deleted
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
# table columns for message format 1.1.0
# The dummy_count entry is to have a "second" primary key since detect_time
# WILL repeat many times. Many objects are typically detected in a single frame
TABLE_COLUMNS_1p1p0 = ('( detect_time100 bigint, '
                       'detect_time_hr text, ' 
                       'confidence float, '
                       'found text, '
                       'stream_group_name text, '
                       'stream_name text, '
                       'msg_format_version text, '
                       'startX float, '
                       'endX float, '
                       'startY float, '
                       'endY float, '
                       'PRIMARY KEY (detect_time100) '
                       ');' 
                      )

def parse_args():
    ''' Parse the arguments and return a dict '''
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser(
       description='This script adds or deletes a table to/from a keyspace',
       usage='./cass_ks_utils.py [-a|-d] <table-name> -k <keyspace-name>')

    ap.add_argument("-k", "--ks-name", required=True,
            help="Keyspace name table to be added to")
    ap.add_argument("-a", "--add-table",
            help="Table name to add")
    ap.add_argument("-d", "--delete-table",
            help="Table name to delete")
    args = vars(ap.parse_args())

    return args

''' ------------ Obsolete functions. They are in cassandra_cluster class now 
def create_table(cass, table_name, ks_name):
    # Create specified table in keyspace ks_name if it does not exist
    cmd = "CREATE TABLE IF NOT EXISTS {ks_name}.{table_name} {cols}".format(
                                   ks_name=ks_name, table_name=table_name,
                                   cols = TABLE_COLUMNS_1p1p0)
    logging.info('Creating table with command: {}'.format(cmd))
    retval = cass.session.execute(cmd)
    # TBD: Not too sure how to check for creating failures
    logging.info('Create command returned: {}'.format(retval))

def delete_table(cass, table_name, ks_name):
    # Delete specified table from keyspace ks_name
    cmd = "DROP TABLE IF EXISTS {ks_name}.{table_name};".format(
                             ks_name=ks_name, table_name=table_name)
    logging.info('Deleting keyspace with command: {}'.format(cmd))
    retval = cass.session.execute(cmd)
    # TBD: Not too sure how to check for creating failures
    logging.info('Delete command returned: {}'.format(retval))
'''


def main():
    ''' main program '''
    args = parse_args()
    # Connect to cassandra db
    cass = cu.cassandra_utils([HOSTNAME])

    if args['add_table']:
        logging.info('Adding Table {} to Keyspace {}'
                                .format(args['add_table'], args['ks_name']))
        cass.create_table(args['ks_name'], args['add_table'], 
                                                      TABLE_COLUMNS_1p1p0)
    elif args['delete_table']:
        logging.info('Deleting Table {} from Keyspace {}'
                                .format(args['delete_table'], args['ks_name']))
        cass.delete_table(args['ks_name'], args['delete_table'])
    else:
        logging.error('Need to specify either add or delete option')
    cass.cleanup()

if __name__ == '__main__':
    main()
