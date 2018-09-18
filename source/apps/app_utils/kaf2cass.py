#! /usr/bin/env python

''' Reads from Kafka and populates Cassandra tables '''

# Some more documentation.
# Idecided to implement the table addition logic in this script itself. 
# This is quite inefficient since the existance of a table is checked every
# time a messae is received. A far better implementation is a separate
# script that wakes up now and then and creates the table if it does not exist

import sys
import json
import logging
import time
import pytz
import datetime
from kafka import KafkaConsumer

# Local imports
import cass_utils

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

# Kafka constants: Again lotsa magic variables
TOPIC = 'camsfeed1'
KAFKA_SERVER = '10.2.13.29'
KAFKA_PORT = '9092'
STREAM_NAME = 'Aruba_SLR01_Cams'
PC_PKL_FILENAME = 'pkl_files/archimedes_{}.pkl'
PC_DF_SAVE_COUNT = 100    # Save the DF every PC_DF_SAVE_COUNT rows

# Cassandra constants: Again lotsa magic variables
CASS_HOSTNAME = '127.0.0.1'       # Localhost. Later move this to a config
CASS_KEYSPACE = 'aruba_slr01_camfeedsv1'
CASS_TABLE_PREFIX = 'camfeeds'
CASS_TABLE_DATE_FORMAT = '%Y%m%d'
# The dummy_count below is added to be able to have the same detect_time 
# in multiple rows.  This is a common occurance becasue multiple objects will
# most always be detected in a video frame. This field will simply increment
# by one every time same same detect_time is inserted into the table.
CASS_COL_NAMES = ['detect_time100', 'detect_time_hr', 
                  'confidence', 'found', 'stream_name', 'stream_group_name', 
                  'msg_format_version', 'startX', 'endX', 'startY', 'endY']

# Epoch time is in us.  So divide by 1e6 to get it in secs
EPOCHTIME_DIVISOR = 1e6 
'''
CASS_TABLE_COL_NAMES = 'detect_time dummy_count confidence found stream_name msg_format_version startX endX startY endY'

SYSTEM_KS = ['system_schema', 'system', 'system_distributed',
             'system_auth', 'system_traces',]
'''

class kafka_consumer():
        def __init__(self, name):
            logging.info('Connecting to Kafka broker: {}:{}'
                                              .format(KAFKA_SERVER, TOPIC))
            self.consumer = KafkaConsumer(TOPIC, 
                  bootstrap_servers='{}:{}'.format(KAFKA_SERVER, KAFKA_PORT))
            # Delete self.pc_df=pd.DataFrame(columns=PC_COL_NAMES)
            self.pc_name = name

def get_today_table_name(table_prefix):
    ''' Get Cassandra table name with today's date in the correct format '''
    cass_table_today = '{}_{}'.format(table_prefix, 
                datetime.datetime.today().strftime(CASS_TABLE_DATE_FORMAT))
    return cass_table_today
    # return 'ggexpt_table1'

def get_tomorrow_table_name(table_prefix):
    ''' Get Cassandra table name with tomorrow's date in the correct format '''
    tomorrow_date = datetime.date.today() + datetime.timedelta(days=1)

    cass_table_tomorrow = '{}_{}'.format(table_prefix, 
                           tomorrow_date.strftime(CASS_TABLE_DATE_FORMAT))
    return cass_table_tomorrow

def check_tomorrow_table(cass):
    ''' This function checks if tomorrows table exists in Cassandra DB
        and makes it if one does not exist '''
    tables_in_ks = cass.get_tables_in_keyspace(CASS_KEYSPACE)
    tomorrow_table_name = get_tomorrow_table_name(CASS_TABLE_PREFIX) 
    if tomorrow_table_name not in tables_in_ks:
        # Create tomorrow's table if it does not exist
        logging.info('Creating tomorrows table. Table name: {}'
                                              .format(tomorrow_table_name))
        cass.create_table(CASS_KEYSPACE, tomorrow_table_name)
        return 'Table Created: {}.format(tomorrow_table_name)'
    else:
        return 'Table Exists'

def epoch_to_time_hr(epoch_time):
    ''' Convert epoch to Human readable time. Including the time zone in the
        resulting string '''
    # Below seems to be a very complicated way of inserting tz
    # into the hr time string. Would be nice to find a better method.
    # Also need to remove hardcode of 'America/Los_Angeles'
    tz = pytz.timezone('America/Los_Angeles')
    time_wtz = datetime.datetime.fromtimestamp(epoch_time/EPOCHTIME_DIVISOR, tz)
    time_wtz = time_wtz.strftime('%Y-%m-%d_%H:%M:%S%z')
    return time_wtz

def make_cass_entry(cass, insert_dict):
    ''' Take the given Kafka message and enter it into Cassandra
        specified by kespace and table (in constants currently) '''
    logging.info('Inserting this whole dict into Cassandra: {}'
                                                      .format(insert_dict))
    cass_today_table_name = get_today_table_name(CASS_TABLE_PREFIX)
    # Get the values of the insert dict into a list
    values_list = [insert_dict[cname] for cname in CASS_COL_NAMES]
    # Now make the insert command as per the CQL format
    icmd = "INSERT INTO {table_name} ({col_tuple}) VALUES {val_tuple}".format(
                   table_name = cass_today_table_name,
                   col_tuple  = ', '.join(CASS_COL_NAMES),
                   val_tuple  = tuple(values_list))
    logging.info('Inserting into Cassandra with command: {}'.format(icmd))
    # And now do the deed
    cass.session.execute(icmd)

def kafka_to_cass(kaf, cass):
    ''' Gets messages from kafka topic and writes it to specified
        keyspace.table in Cassandra '''

    try:
        for msg in kaf.consumer:
            check_tomorrow_table(cass)
            kafka_msg_json = json.loads(msg.value)
            if kafka_msg_json['msg_format_version'] == '1.1.0':
                print('Processing message of format 1.1.0')
                dummy_count = 0
                df_json = {}
                detect_time_epoch = kafka_msg_json['detect_time']
                df_json['detect_time100'] = detect_time_epoch
                df_json['detect_time_hr'] = epoch_to_time_hr(detect_time_epoch)
                df_json['stream_group_name']=kafka_msg_json['stream_group_name']
                df_json['stream_name'] = kafka_msg_json['stream_name']
                df_json['msg_format_version'] = kafka_msg_json['msg_format_version']
                # Unfurl the lis of objects detected into the single dict
                for df_sub_json in kafka_msg_json['objects_list']:
                    combined_dict = dict(df_json, **df_sub_json)
                    # The equation below creates a unique primary key for 
                    # insertion. TBD Later: Move to a function with better
                    # doc if this works
                    combined_dict['detect_time100'] = ((detect_time_epoch * 100)
                                                           + dummy_count)
                    dummy_count += 1
                    # Now after processing a message from Kafka, enter it(them)
                    # into Cassandra
                    make_cass_entry(cass, combined_dict)
            else:
               logging.info('Sorry. Do not deal with this msg format yet: {}'
                                 .format(kafka_msg_json['msg_format_version']))
               continue


    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Exiting . . . ')
        return ['Keyboard Interrupt']

def main():
    ''' Main program '''
    # Init Kafka and Casandra connections
    kaf = kafka_consumer(STREAM_NAME)
    cass = cass_utils.cassandra_utils([CASS_HOSTNAME])
    # This below is to init the cass object with all keyspaces
    cass.get_keyspaces()
    # Set the Cassandra keyspace
    cass.set_session_keyspace(CASS_KEYSPACE)

    # Now read from kafka and write to Cassandra
    kafka_to_cass(kaf, cass)

if __name__ == '__main__':
    main()


