#! /usr/bin/env python
# Note: This script is primarily for testing insertion into a table

# import sys
import time
import logging

import pandas as pd

# from cassandra.query import dict_factory
# from cassandra.query import SimpleStatement

# Local imports
import cass_utils as cu

# Set logging level
logging.basicConfig(level=logging.INFO)

# Constants. Lots of magic crap. Oh, I'm going to pay for this . . .
HOSTNAME = '127.0.0.1'       # Localhost. Later move this to a config
CASS_HR_TIME_FORMAT = '%Y-%m-%d_%H:%M:%S%z'
COLUMN_NAMES = ['stream_group_name', 'stream_name', 'detect_time100',
                'confidence', 'detect_time_hr', 'endx', 'endy', 'found',
                'msg_format_version', 'startx', 'starty']

# Query constants
NUM_ENTRIES = 20
# TABLE_PREFIX = 'camfeeds_sv2p1'
TABLE_PREFIX = 'cf_person_sv2p1'
KEYSPACE = 'aruba_slr01_camfeedsv1'
# TABLE_NAME = 'camfeeds_sv2p1_20181109'
STREAM_GROUP_NAME = 'Aruba_SLR01_Cams'
STREAM_NAME = 'bldg_d_f4_helpdesk'

# cqlsh Query example
'''
cqlsh:> select * from camfeeds_sv2_20181019
        where stream_group_name='Aruba_SLR01_Cams' and
        stream_name='bldg_d_f2_conf_archimedes' and
        detect_time100>153999028474592500 and
        detect_time100<153999028527509899;
'''


START_TIME = '2019-02-07_08:00:00'
END_TIME = '2019-02-07_09:00:00'


def hr_time_to_epoch(hr_time):
    ''' Convert human readable time to epoch time '''
    tmp_time = time.mktime(time.strptime(hr_time, CASS_HR_TIME_FORMAT))
    return int(tmp_time * 1e6)    # The 1e6 is to return epoch in microseconds


def table_name_from_date(time_str):
    ''' Given a time string, derive the Cassandra table name and return in

        Arguments:
            time_str: Date/time as a string. Format is: YYYY-MM-DD_hh:mm:ss

        Returns:
            table_name: A cassandra table name.
                        Format is: camfeeds_sv2p1_YYYYMMDD
    '''
    date_str = time_str.split('_')[0]
    date_str = ''.join(date_str.split('-'))
    table_name = '{}_{}'.format(TABLE_PREFIX, date_str)
    return table_name


def pandas_factory(colnames, rows):
    ''' Pandas factory function '''
    return pd.DataFrame(rows, columns=colnames)


def make_query_cmd(table_name, stream_group_name, stream_name,
                   start_time, end_time):
    qcmd = 'select * from {table_name} where stream_group_name=\'{sgn}\' and stream_name=\'{sn}\' and detect_time100 > {start_time} and detect_time100 < {end_time};'.format(
            # The * 100 below is the conversion for unique key.
            # TBD: Better explanation needed for future
            table_name=table_name, sgn=stream_group_name,
            sn=stream_name, start_time=start_time * 100,
            end_time=end_time * 100)
    return qcmd


def check_table_exists(cass, start_time):
    ''' Check for existance of table. Return True if it exists.
        Else return False '''

    # Start & End times are in PST format. Need to add a "-0700" to them
    # to make them UTC. TBD: I know this is a fixed time zone. This is all
    # that is supported now.
    start_time_hr = '{}-0700'.format(start_time)

    # Get table name from start/emd times. For now, make an assumption that
    # queries are only within one day, so table name can be figured out
    # from either start time hr or end time hr
    table_name = table_name_from_date(start_time_hr)

    # Set keyspaces to populate the class cassandra_utils keyspaces.
    # This step should not be needed, but . . . moving fwd . . .
    ks_list, _ = cass.get_keyspaces()
    tables_list = cass.get_tables_in_keyspace(KEYSPACE)
    return True if table_name in tables_list else False

def make_empty_dataframe():
    ''' Return an empty dataframe with the correct columns.

        This is sometimes needed, for example when a table does not exist
    '''
    return pd.DataFrame(columns=COLUMN_NAMES)



def cass_query_to_dict(cass, stream_group_name, stream_name,
                       start_time_hr, end_time_hr):
    ''' Make the query between start and endtimes and return results as dict
    '''
    # Move this to utils
    # The code for this was obtained form:
    # https://datastax.github.io/python-driver/api/cassandra/query.html

    # Start & End times are in PST format. Need to add a "-0700" to them
    # to make them UTC. TBD: I know this is a fixed time zone. This is all
    # that is supported now.
    start_time_hr = '{}-0700'.format(start_time_hr)
    end_time_hr = '{}-0700'.format(end_time_hr)

    # Convert hr to epoch
    start_epoch = hr_time_to_epoch(start_time_hr)
    end_epoch = hr_time_to_epoch(end_time_hr)

    # Get table name from start/emd times. For now, make an assumption that
    # queries are only within one day, so table name can be figured out
    # from either start time hr or end time hr
    table_name = table_name_from_date(start_time_hr)

    # cass.session.row_factory = dict_factory
    qcmd = make_query_cmd(table_name, stream_group_name, stream_name,
                          start_epoch, end_epoch)
    # print(qcmd)

    # statement = SimpleStatement(qcmd, fetch_size=None)

    rows_iter = cass.session.execute(qcmd)
    return rows_iter


def cass_query(start_time, end_time):
    ''' main program '''
    # init the cass obj with all keyspaces and tables
    cass = cu.cassandra_utils([HOSTNAME])

    # Set the keyspace
    cass.set_session_keyspace(KEYSPACE)

    # Set the pandas factory
    cass.session.row_factory = pandas_factory

    # Set query fetch size to 5000. Otherwise things will timeout
    # TBD: Magic number alert
    cass.session.default_fetch_size = 5000

    # Before making the query, check that the table exists. If it does not
    # exists, create an empty data frame and return it
    # TBD: This should be handled better or more elagently
    table_exists = check_table_exists(cass, start_time)
    if not table_exists:
        # return an empty dataframe
        return make_empty_dataframe()

    # Now do the query
    ret_dict_iter = cass_query_to_dict(cass, STREAM_GROUP_NAME, STREAM_NAME,
                                       start_time, end_time)

    # Now go through the query page by page and assemble the dataframe of
    # interest
    person_df = pd.DataFrame()
    while ret_dict_iter.has_more_pages:
        # Get the page into a temp df and then appent only the rows of
        # interest into person_df
        tmp_df = ret_dict_iter._current_rows
        person_df = person_df.append(tmp_df[tmp_df.found == 'person'])
        # print(len(person_df))
        ret_dict_iter.fetch_next_page()
    # Now append the last remaining rows of the fetch (otherwise df will
    # always be multiple of cass.session.default_fetch_size)
    tmp_df = ret_dict_iter._current_rows
    person_df = person_df.append(tmp_df[tmp_df.found == 'person'])

    # query_df = ret_dict_iter._current_rows

    # Now get the count of only the persons detcted
    # person_df = query_df[query_df.found == 'person']

    # cass.session.cleanup()
    return person_df


def main():
    ''' main program '''

    # init the cass obj with all keyspaces and tables
    cass = cu.cassandra_utils([HOSTNAME])

    # Set the keyspace
    cass.set_session_keyspace(KEYSPACE)

    # Now do the query
    # ret_dict = cass_query_to_dict(cass, STREAM_GROUP_NAME, STREAM_NAME, 
    #                               START_TIME, END_TIME)

    person_df = cass_query(START_TIME, END_TIME)
    print(person_df.columns)
    print(person_df.head())
    # print(len(list(ret_dict)))

    cass.cleanup()

if __name__ == '__main__':
    main()


'''
def pandas_factory(colnames, rows):
    return pd.DataFrame(rows, columns=colnames)

session.row_factory = pandas_factory
session.default_fetch_size = None

query = "SELECT ..."
rslt = session.execute(query, timeout=None)
df = rslt._current_rows
'''
