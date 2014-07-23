#!/usr/bin/env python

import os
import sys
import time
from datetime import datetime

def format_delta(delta):
    s = ''
    if delta.days:
        s += str(delta.days) + ' '
        s += 'days ' if delta.days > 1 else 'day '

    s += "%d:%02d" % ((delta.seconds // 60) % 60,
                           delta.seconds % 60)

    return s

def timer(stream=sys.stdout):
    start = datetime.now()
    while True:
        stream.write('\r')
        stream.write(format_delta(datetime.now() - start))
        stream.flush()
        time.sleep(10)

def clear():
    os.system('clear')

if __name__ == '__main__':
    clear()
    try:
        timer()
    except KeyboardInterrupt:
        print ''
