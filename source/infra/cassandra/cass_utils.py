#! /usr/bin/env python

''' General cassandra utilities '''

import logging

from cassandra.cluster import Cluster

# Set logging level
logging.basicConfig(level=logging.INFO)

# Constants
HOSTNAME = '127.0.0.1'       # Localhost. Later move this to a config
SYSTEM_KS = ['system_schema', 'system', 'system_distributed', 
             'system_auth', 'system_traces',]
KEYSPACE = 'gg_expt1'

class cassandra_cluster():
    ''' Object that holds all cassandra related information '''
    def __init__(self, hosts_list):
        self.hosts_list = hosts_list
        # For now, this is hardcoded. Make it configurable later
        self.replication = { 'class': 'SimpleStrategy', 
                             'replication_factor': 1 };
        self._connect_to_cluster()

    # Private methods
    def _connect_to_cluster(self):
        logging.info('connecting to Cassandra at: {}'.format(self.hosts_list))
        self.cluster = Cluster(self.hosts_list)
        self.session = self.cluster.connect()
        self.cluster_name = self.cluster.metadata.cluster_name
        logging.info('Connected to cluster named: {}'.format(self.cluster_name))

    # Public methods
    def get_replication(self):
        ''' Simply return the replication setting for now '''
        return self.replication

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

def main():
    ''' main program '''
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
    cass.cleanup()

if __name__ == '__main__':
    # Mainly used for testing. Can also be used as a tenmplate for other scripts
    main()
