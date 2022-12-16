#!/usr/bin/env python2
import re
import sys

def proportion_null(handle, block_size=512):
    if block_size < 1:
        raise ValueError('block_size must be > 0')

    null_block = '\0' * block_size

    count_null = 0
    total = 0

    while True:
        block = handle.read(block_size)
        if not block:
            break

        total += 1
        if block == null_block[:len(block)]:
            count_null += 1

    if total == 0:
        percentage = None
    else:
        percentage = 100.0 * count_null / total

    return {'null': count_null,
            'total': total,
            'percentage': percentage}

if __name__ == '__main__':
    for filename in sys.argv[1:]:
        if filename == '-':
            f = sys.stdin
        else:
            f = open(filename, 'r')

        data = proportion_null(f)
        if data['percentage'] is None:
            print '-',
        else:
            print '%d%%' % round(data['percentage'], 0),

        print '%d/%d' % (data['null'], data['total']),

        print f.name
