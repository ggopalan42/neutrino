#! /usr/bin/env python
# Note: This script is primarily for testing insertion into a table

import os
import sys
import time
import logging

from cassandra.query import dict_factory

# Local imports
import cass_utils as cu

# Set logging level
logging.basicConfig(level=logging.INFO)

# Constants
HOSTNAME = '127.0.0.1'       # Localhost. Later move this to a config
CASS_HR_TIME_FORMAT = '%Y-%m-%d_%H:%M:%S%z'

# cqlsh Query example
'''
cqlsh:aruba_slr01_camfeedsv1> select * from camfeeds_sv2_20181019 where stream_group_name='Aruba_SLR01_Cams' and stream_name='bldg_d_f2_conf_archimedes' and detect_time100>153999028474592500 and detect_time100<153999028527509899;
'''

# Query constants
NUM_ENTRIES = 20
KEYSPACE = 'aruba_slr01_camfeedsv1'
TABLE_NAME = 'camfeeds_sv2p1_20181107'
STREAM_GROUP_NAME = 'Aruba_SLR01_Cams'
STREAM_NAME = 'bldg_d_f4_helpdesk'


START_TIME = '2018-11-07_08:00:00-0700'
END_TIME = '2018-11-07_12:09:00-0700'


COLUMN_NAMES = 'detect_time100 dummy_count detect_time_hr confidence found stream_group_name stream_name msg_format_version startX endX startY endY'

def hr_time_to_epoch(hr_time):
    ''' Convert human readable time to epoch time '''
    tmp_time = time.mktime(time.strptime(hr_time, CASS_HR_TIME_FORMAT))
    return int(tmp_time * 1e6)    # The 1e6 is to return epoch in microseconds

def make_query_cmd(table_name, stream_group_name, stream_name, 
                                         start_time, end_time):
    qcmd = 'select * from {table_name} where stream_group_name=\'{sgn}\' and stream_name=\'{sn}\' and detect_time100 > {start_time} and detect_time100 < {end_time};'.format(
            # The * 100 below is the conversion for unique key.
            # TBD: Better explanation needed for future
            table_name=table_name, sgn=stream_group_name, 
            sn=stream_name, start_time=start_time * 100 , 
                                   end_time=end_time * 100 )
    print(qcmd)
    return qcmd 

def cass_query_to_dict(cass, stream_group_name, stream_name, 
                                                 start_time_hr, end_time_hr):
    ''' Make the query between start and endtimes and return results as dict '''
    # Move this to utils
    # The code for this was obtained form: https://datastax.github.io/python-driver/api/cassandra/query.html
    
    # Convert hr to epoch
    start_epoch = hr_time_to_epoch(start_time_hr)
    end_epoch = hr_time_to_epoch(end_time_hr)
    print('Start epoch: {}'.format(start_epoch))
    print('End epoch: {}'.format(end_epoch))

    cass.session.row_factory = dict_factory
    qcmd = make_query_cmd(TABLE_NAME, stream_group_name, stream_name, 
                                                       start_epoch, end_epoch)
    rows = cass.session.execute(qcmd)
    return rows

def main():
    ''' main program '''

    # init the cass obj with all keyspaces and tables
    cass = cu.cassandra_utils([HOSTNAME])

    # Set the keyspace
    cass.set_session_keyspace(KEYSPACE)

    # Now do the query
    ret_dict = cass_query_to_dict(cass, STREAM_GROUP_NAME, STREAM_NAME, 
                                                       START_TIME, END_TIME)
    '''
    print('Ret dict: {}'.format(ret_dict))
    for d in ret_dict:
        print(d)
    '''

    print(len(list(ret_dict)))

    cass.cleanup()

if __name__ == '__main__':
    main()

