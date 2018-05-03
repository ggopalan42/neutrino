#! /usr/bin/env python
# coding: utf-8

#################################################################
#
# NOTE:
#
#     A large portion of the code in this file is credit to: Fabien Giraud
#                                                            giraud@hpe.com
#
################################################################## 

import os
import sys
import time
import yaml
import zmq
import json
import cv2
import logging

import schema_pb2 as loco_pb2
import google.protobuf as pb
import ale_json_format as jsonf
import numpy as np

# Constants
CONFIG_BASE = '../configs'
IMAGES_BASE = '../images'
ALE_CONFIG_YAML_FILE = os.path.join(CONFIG_BASE, 'pc_ale_config.yml')
AGE_OUT_PERIOD = 60 * 10     # 10 minutes


# TMP_FLOOR_ID = '99E9DB7AAEA13F07B783CB4650811630'    # 1st floor
TMP_FLOOR_ID = '044EBA35ADB937D9B20F040E1C1CC5CB'      # 3rd floor



# Set logging level
logging.basicConfig(level=logging.INFO)

class ale_utils():
    def __init__(self, ale_config_file = ALE_CONFIG_YAML_FILE):
        # Load ALE configs
        self._load_ale_configs(ale_config_file)
        self._age_out_period = AGE_OUT_PERIOD

    # Private methods
    def _load_ale_configs(self, ale_config_file):
        ''' Load all needed configs '''
        # Set people counter config
        with open(ale_config_file) as alefh:
            ale_config_dict = yaml.load(alefh)
        self.ale_rem_server = ale_config_dict['ale_params']['ale_rem_hostname']
        self.ale_rem_port = ale_config_dict['ale_params']['ale_rem_port']
        # For now, unfurl this stuff into separate dicts. Later a hierarchy may
        # be needed
        self.campus_info = {}
        self.building_info = {}
        self.floor_info = {}
        for campus in ale_config_dict['ale_campus_info']:
            for campus_name in campus:
                campus_id = campus[campus_name]['campus_id']
                self.campus_info[campus_id] = {
                  'campus_name': campus[campus_name]['campus_name'],
                  'description': campus[campus_name]['description']}
                for buildings in campus[campus_name]['building']:
                    for building in buildings:
                        building_id = buildings[building]['building_id']
                        self.building_info[building_id] = {
                          'building_name': buildings[building]['building_name']}
                        for floors in buildings[building]['floor']:
                            for floor in floors:
                                floor_id = floors[floor]['floor_id']
                                self.floor_info[floor_id] = {
                                  'floor_name': floors[floor]['floor_name'],
                                  'floor_dwg_width': floors[floor]['floor_dwg_width'],
                                  'floor_dwg_length': floors[floor]['floor_dwg_length'],
                                  'floor_dwg_unit': floors[floor]['floor_dwg_unit'],
                                  'floor_image_fn': floors[floor]['floor_image'],
                                }


    # Public methods
    def age_out_locs(self, locs_dict):
        ''' Age out entries in the locs dict '''
        delete_list = []
        for key in locs_dict:
            loc_timestamp = locs_dict[key]['timestamp']
            # If that location has stayed around long enough, remove it
            curr_time = time.time()
            if curr_time - loc_timestamp > self._age_out_period:
                delete_list.append(key)

        for key in delete_list:
            print('Deleting key: {}'.format(key))
            del locs_dict[key]

    def connect_to_server(self):
        ''' Connect to the ALE server '''
        # This code courtest of: Fabien Giraud (giraud@hpe.com)
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        connect_str = 'tcp://{}:{}'.format(self.ale_rem_server,
                                                     self.ale_rem_port)
        logging.info('ZMQ connecting to {}'.format(connect_str))
        self.socket.connect(connect_str)

    def subscribe_to_topics(self, topic):
        ''' Subscribe to a topic. lated extend to list of topics '''
        # This code courtest of: Fabien Giraud (giraud@hpe.com)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)

    def get_topic_message(self, topic):
        ''' Get a message from the topic '''
        # This code courtest of: Fabien Giraud (giraud@hpe.com)
        # Right now only 1 topic is supported
        # print('Before recv')
        topicFull = self.socket.recv()
        data = self.socket.recv()
        topic = topicFull.decode().split("/")[0]
        # print('Topic full is {}\n'.format(topicFull))
        # print('Raw data = {}\n'.format(data))
        # print('Decoded topic = {}\n'.format(topic))

        aleMsg = loco_pb2.nb_event()
        aleMsg.Clear()
        aleMsg.ParseFromString(data)
        # print('ALE Message = {}\n'.format(aleMsg))

        msg_json = jsonf.MessageToJson(aleMsg,
                        preserving_proto_field_name=True, encoding_type='ALE')
        msg_dict = json.loads(msg_json)
        return msg_dict

    def load_floor_images(self):
        ''' Using cv2, load all floor images into numpy arrays '''
        for floor_id in self.floor_info:
            floor_fn = os.path.join(IMAGES_BASE, 
                                  self.floor_info[floor_id]['floor_image_fn'])
            floor_name = self.floor_info[floor_id]['floor_name']
            floor_image = cv2.imread(floor_fn)
            print('Loading floor Image: {}'.format(floor_name))
            self.floor_info[floor_id]['floor_image'] = floor_image
            # Set the floor image length and width in pixel count
            self.floor_info[floor_id]['floor_image'] = floor_image
            self.floor_info[floor_id]['floor_img_pxl_width'] =   \
                                                        floor_image.shape[1]
            self.floor_info[floor_id]['floor_img_pxl_length'] =  \
                                                        floor_image.shape[0]
            self.floor_info[floor_id]['width_ratio'] =           \
                           (float(floor_image.shape[1])/
                           float(self.floor_info[floor_id]['floor_dwg_width']))
            self.floor_info[floor_id]['length_ratio'] =          \
                           (float(floor_image.shape[0])/
                          float(self.floor_info[floor_id]['floor_dwg_length']))

    def show_floor_image(self):
        ''' Tmp: For now show only single floor image '''
        floor_name = self.floor_info[TMP_FLOOR_ID]['floor_name']
        floor_unique_name = '{} {}'.format(floor_name, TMP_FLOOR_ID)
        
        # Draw the floor image
        cv2.namedWindow(floor_unique_name)
        cv2.imshow(floor_unique_name, self.floor_info[TMP_FLOOR_ID]['floor_image'])
        cv2.waitKey(1)
        time.sleep(10)
        return floor_unique_name

    def draw_locs(self, floor_id, locs_dict):
        ''' Draw circles also showing uncertanity onto floor_id's image '''
        floor_image = self.floor_info[TMP_FLOOR_ID]['floor_image']
        floor_image_copy = floor_image.copy()
        width_ratio = self.floor_info[TMP_FLOOR_ID]['width_ratio']
        length_ratio = self.floor_info[TMP_FLOOR_ID]['length_ratio']
        # print('Image Shape: {}'.format(floor_image.shape))
        # Circle params. Move to the class later
        cir_radius = 3
        cir_color = (0, 255, 0)        # Green for inner circle
        cir_light_color = (0, 0, 255)  # Red for error circle
        cir_thickness = 5

        # Text params. Move to the class later
        txt_font  = cv2.FONT_HERSHEY_SIMPLEX
        txt_font_scale = 0.5
        txt_font_color = (0,255,0)
        txt_line_type  = 1

        for sta_mac in locs_dict:
            # Draw the station circle
            x_loc = locs_dict[sta_mac]['sta_location_x']
            y_loc = locs_dict[sta_mac]['sta_location_y']
            error_level = locs_dict[sta_mac]['error_level']
            associated = locs_dict[sta_mac]['associated']
            cir_loc = (int(x_loc * width_ratio), int(y_loc * length_ratio))
            # Draw error circle
            # cv2.circle(floor_image_copy, cir_loc, error_level, 
            #                             cir_light_color, -1)
            # Draw location circle
            cv2.circle(floor_image_copy, cir_loc, cir_radius,
                                                  cir_color, cir_thickness)
            # Draw the station ID text
            txt_left_corner = (int(x_loc * width_ratio)+10,
                                                 int(y_loc * length_ratio))
            station_id_abbr = sta_mac[-5:-1]
            cv2.putText(floor_image_copy, station_id_abbr, txt_left_corner,
                    txt_font, txt_font_scale, txt_font_color, txt_line_type)

        cv2.imshow(floor_id, floor_image_copy)
        cv2.waitKey(1)

def cook_up_locs():
    ''' Tmp stuff for development '''
    # The loc list is on the form: (x, y, error_level)
    loc_list = [
                   (252.0823516845703, 174.67062377929688, 143),
                   (59.642704010009766, 122.11890411376953, 143),
                   (248.9491424560547, 170.96319580078125, 143),
                   (239.71969604492188, 41.285621643066406, 143),
                   (123.23391723632812, 89.58060455322266, 143),
               ]
    return loc_list

def cleanup(au_obj):
    ''' Cleanup before exiting '''
    cv2.destroyAllWindows()

def main_loop(au_obj):
    ''' Continously query the ALE server and update floor image '''
    try:
        locs_dict = {}
        while True:
            msg = au_obj.get_topic_message(topicInit)
            # Filter out TMP_FLOOR_ID
            if msg['location']['floor_id'] == TMP_FLOOR_ID.lower():
                msg_epoch_ts = msg['timestamp']
                msg_ts = time.strftime('%Y-%m-%d_%H:%M:%S', 
                                             time.localtime(msg_epoch_ts))
                msg_loc = msg['location']
                loc_x = msg_loc['sta_location_x']
                loc_y = msg_loc['sta_location_y']
                loc_err = msg_loc['error_level']
                sta_mac = msg_loc['hashed_sta_eth_mac']
                curr_time = time.time()
                locs_dict[sta_mac]={'sta_location_x': loc_x,
                                  'sta_location_y': loc_y,
                                  'error_level': loc_err,
                                  'associated': msg_loc['associated'],
                                  'timestamp': curr_time}

                # for k in locs_dict:
                #   print(k)
                print(len(locs_dict))

                logging.info('Found station: {}, {} (ts: {})'
                                           .format(loc_x, loc_y, msg_ts))
                au_obj.draw_locs(TMP_FLOOR_ID, locs_dict)

                # Age out entries in locs_dict. This is a crude way of doing it
                # and will be a temp fix
                au_obj.age_out_locs(locs_dict)


    except KeyboardInterrupt:
        logging.info('Received Ctrl-C. Exiting . . . ')
        cleanup(au_obj)
        return ['Keyboard Interrupt']



# This is for test purposes only
if __name__ == '__main__':
    # Initialize
    au = ale_utils()
    # Connect and subscribe to ALE server
    au.connect_to_server()
    # topicInit='geofence_notify'
    topicInit = 'location'
    au.subscribe_to_topics(topicInit)

    # Load and preprocess floor images
    au.load_floor_images()
    # au.show_floor_image()

    main_loop(au)

    # Tmp stuff
    # locs_list = cook_up_locs()
    # au.draw_locs(TMP_FLOOR_ID, locs_list)
