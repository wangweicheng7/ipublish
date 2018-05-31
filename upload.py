# -*- coding: utf-8 -*-

# by wangweicheng

import requests
from poster.encode import multipart_encode
from ipublish.progress import ProgressBar
from ipublish.progress import IterableToFileAdapter


def multipart_encode_for_requests(params, boundary=None, cb=None):
    datagen, headers = multipart_encode(params, boundary, cb)
    return IterableToFileAdapter(datagen), headers

bar = ProgressBar(total = 200)
def progress(param, current, total=0):
    if not param:
        return
    bar.total = total
    bar.move(current)

def upload_server():

    url = 'http://example.com'
    path = '/path/to/project.ipa'
    datagen, headers = multipart_encode_for_requests({
        'param1': 'value1',
        'param2': 'value2',
        'file': open(path, 'rb'),
    }, cb=progress)

    r = requests.post(
        url,
        data=datagen,
        headers=headers)
    print(r.text)

def main():
    upload_server()

if __name__ == '__main__':
    main()