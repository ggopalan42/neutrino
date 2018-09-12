#! /usr/bin/env python

import sys
import json
import logging
import time
import pandas as pd
from kafka import KafkaConsumer

# Set logging level
logging.basicConfig(level=logging.INFO)
# Set kafka module level higher. It spews a lot of junk
logging.getLogger('kafka').setLevel(logging.WARNING)

# Below is a hack to get going quick. Need to define a schema properly
# and all that
PC_COL_NAMES = ['detect_time', 'msg_format_version', 'stream_name', 'found', 
                'startX', 'startY', 'endX', 'endY', 'confidence']
# Again lotsa magic variables
TOPIC = 'camsfeed1'
KAFKA_SERVER = '10.2.13.29'
KAFKA_PORT = '9092'
PC_STREAM_NAME = 'Aruba_SLR01_Cams'
PC_PKL_FILENAME = 'pkl_files/archimedes_{}.pkl'
PC_DF_SAVE_COUNT = 100    # Save the DF every PC_DF_SAVE_COUNT rows


class pc_kafka_pandas_consumer():
        def __init__(self, name):
            logging.info('Connecting to Kafka broker: {}:{}'
                                              .format(KAFKA_SERVER, TOPIC))
            self.consumer = KafkaConsumer(TOPIC, 
                  bootstrap_servers='{}:{}'.format(KAFKA_SERVER, KAFKA_PORT))
            self.pc_df=pd.DataFrame(columns=PC_COL_NAMES)
            self.pc_name = name

def get_pkl_filename():
    return PC_PKL_FILENAME.format(int(time.time()))

def get_kafka_msg_to_pandas(pc_kafka):
    ''' Gets messages from kafka topic and adds it DataFrame. Then writes it
        out every now and then '''

    pkl_fn = get_pkl_filename()
    
    try:
        df_row_count = 0
        df_batch_count = 0
        for msg in pc_kafka.consumer:
            kafka_msg = json.loads(msg.value)
            kafka_msg_json = json.loads(msg.value)
            if kafka_msg_json['msg_format_version'] == '1.1.0':
                print('Proc 1.1.0')
                df_json = {}
                df_json['detect_time'] = kafka_msg_json['detect_time']
                df_json['stream_name'] = kafka_msg_json['stream_name']
                df_json['msg_format_version'] = kafka_msg_json['msg_format_version']
                for df_sub_json in kafka_msg_json['objects_list']:
                    combined_dict = dict(df_json, **df_sub_json)
                    temp_df = pd.DataFrame(combined_dict, index=[0])
                    pc_kafka.pc_df = pc_kafka.pc_df.append(temp_df, 
                                                        ignore_index=True)
                    df_row_count += 1
                    logging.info(combined_dict)
                    logging.info('Row Count = {}, Total rows = {}\n'
                             .format(df_row_count, df_row_count + 
                                     (df_batch_count * PC_DF_SAVE_COUNT  )))
                    # Save the df now and then
                    if df_row_count > PC_DF_SAVE_COUNT:
                        logging.info('Saving PC DataFrame to: {}'
                                                     .format(PC_PKL_FILENAME))
                        df_row_count = 0
                        df_batch_count += 1

                        pc_kafka.pc_df.to_pickle(pkl_fn)
            else:
               logging.info('Sorry. Do not deal with this msg format yet: {}'
                                 .format(kafka_msg_json['msg_format_version']))
               continue


    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Exiting . . . ')
        return ['Keyboard Interrupt']



if __name__ == '__main__':
    pc_kafka = pc_kafka_pandas_consumer(PC_STREAM_NAME)
    get_kafka_msg_to_pandas(pc_kafka)


