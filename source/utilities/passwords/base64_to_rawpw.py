#!/usr/bin/env python

import base64

base64_pw = b'cm9vdA=='

raw_pw = base64.b64decode(base64_pw)
raw_pw_str = raw_pw.decode('utf-8')
print('Raw pw: {}'.format(raw_pw_str))
print('Raw pw type: {}'.format(type(raw_pw_str)))
