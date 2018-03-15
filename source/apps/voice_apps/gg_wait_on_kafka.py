#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import aiy.audio
import time
from kafka import KafkaConsumer

consumer = KafkaConsumer('TutorialTopic', bootstrap_servers='10.2.13.29:9092')


file_to_watch = '/tmp/incoming_txt'

while True:
    for msg in consumer:
        message = msg.value.decode()
        print(message)
        aiy.audio.say(message)

        # Sleep for a bit
        time.sleep(0.5)
