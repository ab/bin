#!/usr/bin/env python

import re
import sys
import optparse
import zlib

def checksum(fname, sum_fun, binary_mode=False, raw=False):
    if fname == '-':
        f = sys.stdin
    else:
        opts = 'rb' if binary_mode else 'r'
        f = open(fname, opts)

    running_sum = sum_fun('')
    while True:
        buf = f.read(4096)
        if not buf:
            break
        running_sum = sum_fun(buf, running_sum)

    if raw:
        return running_sum & 0xffffffff
    else:
        return '%08x' % (running_sum & 0xffffffff)

def check_list(checkfile_name, sum_fun, win_mode=False):
    if checkfile_name == '-':
        f = sys.stdin
    else:
        f = open(checkfile_name, 'r')

    if win_mode:
        exp = r'^(?P<file>.*) (?P<value>[a-fA-F0-9]{8})$'
    else:
        exp = r'^(?P<value>[a-fA-F0-9]{8}) (\?ADLER32)?( |\*)(?P<file>.*)$'
    regex = re.compile(exp)

    for line in f:
        if line.startswith('#') or line.startswith(';'):
            continue

        x = regex.search(line.rstrip('\r\n'))
        if not x:
            print 'WARNING: Failed to parse:', line
            continue
        
        value = x.group('value').lower()
        fname = x.group('file').replace('\\', '/')

        print fname+':',

        try:
            newsum = checksum(fname, sum_fun)
        except IOError, e:
            if e.errno != 2:
                raise
            print 'FAILED open or read'
        else:
            if newsum == value:
                print 'OK'
            else:
                print 'FAILED'

def make_list(filenames, sum_fun):
    for name in filenames:
        c = checksum(name, sum_fun)
        print '%s  %s' % (c, name)

if __name__ == '__main__':
    p = optparse.OptionParser(usage='%prog [OPTION] [FILE]...')
    p.add_option('-c', '--check', dest='check', action='store_true',
                 help='read checksums from the FILEs and check them')
    p.add_option('-w', '--win-format', dest='win_format', action='store_true',
                 help='assume checksum files are in windows format')
    p.add_option('-a', '--algo', dest='algo', default='crc32',
                 help='algorithm: crc32 or adler32 [default: %default]')

    opts, args = p.parse_args()
    if len(args) == 0:
        files = ['-']
    else:
        files = args
    
    if opts.algo in ['crc', 'crc32']:
        algo = zlib.crc32
    elif opts.algo in ['adler', 'adler32']:
        algo = zlib.adler32
    else:
        p.error('unknown algorithm: %s' % opts.algo)

    if opts.check:
        for name in files:
            check_list(name, algo, opts.win_format)
    else:
        make_list(files, algo)

