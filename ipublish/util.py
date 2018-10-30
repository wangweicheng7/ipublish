# -*- coding: utf-8 -*-

# by wangweicheng


__all__ = ['HUD','ProgressBar', 'IterableToFileAdapter']

import sys
import sys
import threading
import itertools
import time

def _singleton(cls):
    instance = cls()
    instance.__call__ = lambda: instance
    return instance

@_singleton
class HUD:
    def __init__(self):
        self.isloading = False
        self.loading = threading.Thread(target=self._loadingcycle, name='LoadingThread')

    def start(self):
        self.isloading = True
        self.loading.start()

    def stop(self):
        self.isloading = False
    
    def _loadingcycle(self):
        for c in itertools.cycle('|/-\\'): 
            if not self.isloading:
                print('\r')
                return
            sys.stdout.write(c + '\r')
            sys.stdout.flush()
            time.sleep(0.2)

class ProgressBar:
    def __init__(self, count = 0, total = 0, width = 50):
        self.count = count
        self.total = total
        self.width = width
        self.complete = False
        self.progress = False

    def move(self, progress=0):
        self.count = int(progress)
        self.progress = True
        self.run()

    def log(self, s):
        sys.stdout.write(' ' * (self.width + 19) + '\r')
        sys.stdout.flush()
        print(s)
        self.run()

    def run(self):
        if self.complete or not self.progress:
            return
        progress = float(self.count)/float(self.total)
        sys.stdout.write('{0:.2f}% |'.format(progress*100))
        sys.stdout.write('█' * int(progress * self.width) + \
        ' ' * int((1 - progress) * self.width) + \
        ' |[{0:3}K/{1:3}K]\r'.format(self.count/1024, self.total/1024))
        if int(progress) == 1:
            print('')
            self.complete = True
        sys.stdout.flush()

class IterableToFileAdapter(object):
    def __init__(self, iterable):
        self.iterator = iter(iterable)
        self.length = iterable.total
 
    def read(self, size=-1):
        return next(self.iterator, b'')
 
    def __len__(self):
        return self.length