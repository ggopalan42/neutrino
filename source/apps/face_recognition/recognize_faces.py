#! /usr/bin/env python

''' This module uses the face_recognition library to recognoze faces seen
    on picamera. the recognized face is then fed (in next version) into
    a kafka feed '''

import sys
import os
import time
import subprocess
import pickle
import yaml
import picamera
import face_recognition

import numpy as np

from kafka import KafkaProducer


print('Done with imports')


# Constants
KNOWN_FACES_YAML_FILE='./known_faces.yml'
SCP_CMD = 'scp scp_file ggopalan@pievoice1:/tmp/incoming_txt'

KAFKA_BROKER = '10.2.13.29'
KAFKA_PORT = '9092'
KAFKA_TOPIC = 'TutorialTopic'

class known_faces():
    def __init__(self, yaml_dict):
        ''' Init known faces class '''
        self.known_faces_default = yaml_dict['defaults']
        self.known_faces_path = yaml_dict['defaults']['face_pic_path']
        self.known_faces_info = yaml_dict['faces']
        self.known_faces_encodings = []
        self.known_faces_encoding_idx = 0

        # Init the camera. For now, we are using picamera. I expect this to
        # change later to OpenCV
        self.camera = picamera.PiCamera()
        self.camera.resolution = (320, 240)
        self.cam_capture_image = np.empty((240, 320, 3), dtype=np.uint8)

        # Init kafka. ATM it will only be a producer
        self.producer=KafkaProducer(bootstrap_servers=
                                   '{}:{}'.format(KAFKA_BROKER, KAFKA_PORT))

    def set_face_encodings(self, name, face_encoding):
        ''' Appends the face-encoding to the known_face_encodings list '''
        # The known faces info is a list (in YAML). Since each of these
        # are processed in order, simply appending to the list should do
        self.known_faces_encodings.append(face_encoding)
        self.known_faces_encoding_idx += 1

    def get_face_encodings(self):
        return self.known_faces_encodings

    def pkl_save_face_encs(self):
        ''' Save the face encodings in the specified pickle file '''
        pkl_save_fn = self.known_faces_default['known_faces_pkl_save']
        print('Saving face encodings to pickle file')
        with open(pkl_save_fn, 'wb') as pkl_fh:
            pickle.dump(self.known_faces_encodings, pkl_fh)

    def pkl_load_face_encs(self):
        ''' Load the face encodings from the specified pickle file '''
        pkl_load_fn = self.known_faces_default['known_faces_pkl_load']
        print('Loading face encodings from pickle file')
        with open(pkl_load_fn, 'rb') as pkl_fh:
            self.known_faces_encodings = pickle.load(pkl_fh)


def get_yaml():
    ''' Load the known_faces yaml file and return corresponding dict '''
    with open(KNOWN_FACES_YAML_FILE) as kfh:
        known_yaml = yaml.load(kfh)
    return known_yaml

def load_faces(kf_obj):
    ''' This will load each face and store the face encodings in known_faces
        object '''
    # Get the known images base path
    ki_base_path = kf_obj.known_faces_path

    # Loop through each known faces info, encode it and store it in
    # a list
    for name_dict in kf_obj.known_faces_info:
        # Don't know if there is a better way to do this below 
        name = list(name_dict.items())[0][0]
        name_info = list(name_dict.items())[0][1]
        known_image_full_path = os.path.join(kf_obj.known_faces_path, 
                                               name_info['face_pic_name'])
        print('Loading and encoding image for: {}'
                                           .format(name_info['full_name']))
        image = face_recognition.load_image_file(known_image_full_path)
        face_encoding = face_recognition.face_encodings(image)[0]
        kf_obj.set_face_encodings(name, face_encoding)

def get_single_frame(kf_obj):
    ''' Grab a single frame from the Pi Camera and store it in the
        known faces object '''
    print("Capturing image.")
    # Grab a single frame of video from the RPi camera as a numpy array
    kf_obj.camera.start_preview()
    kf_obj.camera.capture(kf_obj.cam_capture_image, format="rgb")
    return

def cap_image_encodings(kf_obj):
    ''' Find all the faces and face encodings in the captured image '''
    cap_face_locs = face_recognition.face_locations(kf_obj.cam_capture_image)
    print("Found {} faces in image.".format(len(cap_face_locs)))
    cap_face_encs = face_recognition.face_encodings(kf_obj.cam_capture_image, 
                                                                cap_face_locs)
    return cap_face_encs

def find_matches(cap_face_encs, kf_obj):
    ''' Loop over found faces and return a list of indexes that match
        the found faces '''
    found_face_indices = []
    known_face_encodings = kf_obj.get_face_encodings()
    # Loop over each face found in the image to see if it's 
    # someone we know.
    for cap_face_encoding in cap_face_encs:
        # See if the face is a match for the known face(s)
        match = face_recognition.compare_faces(known_face_encodings, 
                                                        cap_face_encoding)
        # match will be a list like: [True, False, False, . . .]
        # The index of True is where the match occured in 
        # known_face_encodings
        if any(match):
            known_index = match.index(True)
            found_face_indices.append(known_index)
            
    return found_face_indices

def form_greeting(partial_greeting, kf_obj):
    ''' Form the full greeting string and return it '''
    prepend_string = ''
    append_string = 'How are you doing?'
    full_greeting = ' '.join([prepend_string, partial_greeting, append_string]) 
    return full_greeting

def send_message(message, kf_obj):
    ''' Currently print and scp the message. Later queue it properly '''
    print(message)
    # The .encode is to convert str to bytes (utf-8 is default)
    kf_obj.producer.send(KAFKA_TOPIC, message.encode())
    ''' Switching to kafka now
    # I know. I know. This is a lousy way of doing this.
    with open('./scp_file', 'wt') as scp_fh:
        scp_fh.write(message)
    subprocess.call(SCP_CMD.format(message), shell=True)
    with open('./scp_file', 'wt') as scp_fh:
        scp_fh.write('')
    '''

def process_known_faces(found_face_indices, kf_obj):
    ''' Process the faces found and send appropriate messages '''
    for known_index in found_face_indices:
        # Not sure if there is a better way of doing this
        found_info = list(kf_obj.known_faces_info[known_index].values())[0]
        found_full_name = found_info['full_name']
        found_greeting = found_info['greeting']

        # Log and message found information
        print('Found face full name: {}'.format(found_full_name)) # Log later

        greeting = form_greeting(found_greeting, kf_obj)
        send_message(greeting, kf_obj)
        time.sleep(5)

def process_unknown_faces(kf_obj):
    ''' Send a message saying that face in captured image is unknown '''
    unknown_message = 'Found an un-known face'
    print(unknown_message)
    send_message(unknown_message, kf_obj)

def run_recognition(kf_obj):
    ''' Run the face recognition continously and update output queue
        with the recognised face and meta info '''
    known_face_encodings = kf_obj.get_face_encodings()
    print('Number of known faces is: {}'.format(len(known_face_encodings)))

    try:
        while True:
            # Get a single frame from the camera. The frame is stored in kf_obj
            get_single_frame(kf_obj)

            # Now get the encodings of all faces in the captured image (if any)
            cap_face_encs = cap_image_encodings(kf_obj)

            # If there are any faces in the captured image, check if any
            # of them matches known faces
            if len(cap_face_encs) > 0:
                found_face_indices = find_matches(cap_face_encs, kf_obj)

                # Check if any of them match with known face db
                if len(found_face_indices) > 0:
                    process_known_faces(found_face_indices, kf_obj)
                else:
                    process_unknown_faces(kf_obj)

    except KeyboardInterrupt:
        print('Received Ctrl-C. Exiting . . . ')
        return ['Keyboard Interrupt']


def main():
    ''' This is the main function that does the face recognition '''
    known_faces_yaml = get_yaml()
    kf = known_faces(known_faces_yaml)

    # Now load the known faces and store the corresponding face encodings
    # load_faces(kf)
    # kf.pkl_save_face_encs()

    kf.pkl_load_face_encs()
    run_recognition(kf)


if __name__ == '__main__':
    main()
