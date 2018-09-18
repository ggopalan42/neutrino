#! /usr/bin/env python
# Note: This script is primarily for testing insertion into a table

import os
import sys
import logging

from cassandra.cluster import Cluster

# Set logging level
logging.basicConfig(level=logging.INFO)

# Constants
HOSTNAME = '127.0.0.1'       # Localhost. Later move this to a config
SYSTEM_KS = ['system_schema', 'system', 'system_distributed', 
             'system_auth', 'system_traces',]

# Insertion example
NUM_ENTRIES = 20
KEYSPACE = 'gg_expt3'
TABLE_NAME = 'gg_table3v1'

# The dummy_count below is added to be able to have the same detect_time 
# in multiple rows.  This is a common occurance becasue multiple objects will
# most always be detected in a video frame. This field will simply increment
# by one every time same same detect_time is inserted into the table.
COLUMN_NAMES = 'detect_time100 confidence found stream_name msg_format_version startX endX startY endY'

INSERTION_ROWS = [
(153515573431109500, 0.5251787304878235, 'chair', 'Aruba_SLR01_Cams', '1.1.0', 1299, 1563, 588, 922),
(153515573431109501, 0.34599068760871887, 'chair', 'Aruba_SLR01_Cams', '1.1.0', 624, 877, 559, 983),
(153515573431109502, 0.8212401866912842, 'diningtable', 'Aruba_SLR01_Cams', '1.1.0', 726, 1435, 621, 1079),
(153515573431109503, 0.4583374261856079, 'person', 'Aruba_SLR01_Cams', '1.1.0', 1301, 1554, 508, 840),
(153515573447043500, 0.5029921531677246, 'chair', 'Aruba_SLR01_Cams', '1.1.0', 1300, 1564, 587, 918),
(153515573447043501, 0.38384515047073364, 'chair', 'Aruba_SLR01_Cams', '1.1.0', 622, 879, 558, 981),
(153515573447043502, 0.806638240814209, 'diningtable', 'Aruba_SLR01_Cams', '1.1.0', 725, 1430, 622, 1079),
(153515573447043503, 0.4751611351966858, 'person', 'Aruba_SLR01_Cams', '1.1.0', 1302, 1555, 510, 839),
(153515573447043504, 0.29024815559387207, 'person', 'Aruba_SLR01_Cams', '1.1.0', 694, 903, 489, 859),
(153515573464331000, 0.5867025852203369, 'chair', 'Aruba_SLR01_Cams', '1.1.0', 1301, 1563, 592, 922),
(153515573464331001, 0.41244974732398987, 'chair', 'Aruba_SLR01_Cams', '1.1.0', 624, 881, 560, 988),
(153515573464331002, 0.7770668268203735, 'diningtable', 'Aruba_SLR01_Cams', '1.1.0', 724, 1429, 624, 1079),
(153515573464331003, 0.43301472067832947, 'person', 'Aruba_SLR01_Cams', '1.1.0', 1305, 1553, 509, 842)
]


class cassandra_cluster():
    ''' Object that holds all cassandra related information '''
    def __init__(self, hosts_list):
        self.hosts_list = hosts_list
        self._connect_to_cluster()

    # Private methods
    def _connect_to_cluster(self):
        logging.info('connecting to Cassandra at: {}'.format(self.hosts_list))
        self.cluster = Cluster(self.hosts_list)
        self.session = self.cluster.connect()
        self.cluster_name = self.cluster.metadata.cluster_name
        logging.info('Connected to cluster named: {}'.format(self.cluster_name))

    # Public methods
    def get_keyspaces(self):
        ''' Return the list of keyspaces in this cluster. Also init
            a dict of keyspaces and keyspace objects '''
        self.system_ks_list = []
        self.db_ks_list = []
        self.system_ks_dict = {}
        self.db_ks_dict = {}
        for ks, ks_obj in self.cluster.metadata.keyspaces.items():
            logging.info('Setting up keyspace: {}'.format(ks))
            setattr(self, ks, ks_obj)
            if ks in SYSTEM_KS:
                self.system_ks_list.append(ks)
                self.system_ks_dict[ks] = ks_obj
            else:
                self.db_ks_list.append(ks)
                self.db_ks_dict[ks] = ks_obj

        return self.db_ks_list, self.system_ks_list

    def get_tables_in_keyspace(self, keyspace):
        ''' Given a key space, return a list of tables.
            Also set the table obj as an attr in this (self) obj '''
        table_list = []
        # get the keyspace attribute
        ks_obj = getattr(self, keyspace)
        # roll through the ks_obj tables dict and set things up
        for table_name, table_obj in ks_obj.tables.items():
            logging.info('Setting up for table: {} in keyspace: {}'
                                             .format(table_name, keyspace))
            table_list.append(table_name)
            setattr(ks_obj, table_name, table_obj)
        return table_list
    
    def set_session_keyspace(self, keyspace):
        ''' Set the default keyspace '''
        logging.info('Setting cluster keyspace to: {}'.format(keyspace))
        self.session.set_keyspace(keyspace)

    def cleanup(self):
        ''' Close all connections to the Cassandra cluster '''
        logging.info('Closing connection to cluster: {}'
                                                   .format(self.cluster_name))
        self.cluster.shutdown()

def get_eg2_dict():
    insert_list = []
    for row in INSERTION_ROWS:
        insd = dict(zip(COLUMN_NAMES.split(), list(row)))
        insert_list.append(insd)
    return insert_list
            
def make_insert_cmd(insert_dict):
    ''' Make the insert command from the provided dict '''
    # insert_cmd = "INSERT INTO calendar (race_id, race_name, race_start_date, race_end_date) VALUES (200, 'placeholder', '2015-05-27', '2015-05-27')"
    values_list = [insert_dict[cname] for cname in COLUMN_NAMES.split()]
    icmd = "INSERT INTO {table_name} ({col_tuple}) VALUES {val_tuple}".format(
                   table_name = TABLE_NAME,
                   col_tuple  = ', '.join(COLUMN_NAMES.split()),
                   val_tuple  = tuple(values_list))
    '''
    icmd = "INSERT INTO {table_name} (mykey, col1 ,col2) VALUES {val_tuple}".format(
                   table_name = TABLE_NAME,
                   val_tuple  = tuple(values_list))
    '''
    return icmd

def example2_inserts(cass):
    ''' Example insertions into cassandra db '''
    insert_list = get_eg2_dict()

    for insd in insert_list:
        insert_cmd = make_insert_cmd(insd)
        print(insert_cmd)
        cass.session.execute(insert_cmd)

def main():
    ''' main program '''
    # INSERTION_ROWS:
    # init the cass obj with all keyspaces and tables
    cass = cassandra_cluster([HOSTNAME])
    ks_list, _ = cass.get_keyspaces()

    logging.info('Keyspaces found in the db: {}'.format(', '.join(ks_list)))
    for ks in ks_list:
        table_list = cass.get_tables_in_keyspace(ks)
        logging.info('Tables found in keyspace: {} are {}'
                                         .format(ks, ', '.join(table_list)))
    # Set the keyspace
    cass.set_session_keyspace(KEYSPACE)
    # Some experiments with inserting into cassandra
    example2_inserts(cass)
    cass.cleanup()

if __name__ == '__main__':
    main()
