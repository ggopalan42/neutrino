#!/usr/bin/env python

import base64

raw_pw = b'root'

b64_pw = base64.b64encode(raw_pw)
print(b64_pw)
