# -*- coding: utf-8 -*-

# by wangweicheng

__version__ = "1.0.2"

from sys import argv
from ipublish import core
from ipublish import data

def publish():
    core.main()
    
def add_pgy_key():
    if len(argv) <= 1:
        print('Damn!')
        print('Use ipublish-pgy <key>\n\
Detailed information:\n\
    https://www.pgyer.com/doc/view/api\
        ')
    else:
        key = argv[1]
        data.add_pgy_key(key)

def add_fir_key():
    if len(argv) <= 1:
        print('Damn!')
        print('Use ipublish-fir <key>\n\
Detailed information:\n\
    https://fir.im/docs/publish\
        ')
    else:
        key = argv[1]
        data.add_fir_key(key)
