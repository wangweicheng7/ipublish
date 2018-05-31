# -*- coding: utf-8 -*-

# by wangweicheng

__all__ = ['fir_key', 'pgy_key', 'add_fir_key', 'add_pgy_key']

import json
import os
from sys import argv

path = os.path.expandvars('$HOME')

def fir_key():
    data = read()
    return None if 'fir_key' not in data else read()['fir_key']

def add_fir_key(key):
    data = read()
    data['fir_key'] = key
    write(data)

def pgy_key():
    data = read()
    return None if 'pgy_key' not in data else read()['pgy_key']

def add_pgy_key(key):
    data = read()
    data['pgy_key'] = key
    write(data)

def custom_upload():
    data = read()
    key = os.getcwd()
    custom_upload = {}
    custom_script = None
    if 'custom_upload' in data:
        custom_upload = data['custom_upload']
        if key in custom_upload:
            custom_script = custom_upload[key]
        
    return custom_script

def add_custom_upload(script):
    data = read()
    key = os.getcwd()
    custom_upload = {}
    if 'custom_upload' in data:
        custom_upload = data['custom_upload']
        custom_upload[key] = script
        data['custom_upload'] = custom_upload
    else:
        data['custom_upload'] = {key:script}
    write(data)

def write(data):
    json_str = json.dumps(data)
    new_dict = json.loads(json_str)
    with open(path + '/.ipublish', 'w') as f:
        json.dump(new_dict,f)
    f.close()

def read():
    content = {}
    try:
        with open(path + '/.ipublish','r') as f:
            content = json.load(f)
            f.close()
    except IOError as error:
        pass
    return content