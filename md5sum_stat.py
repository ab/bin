#!/usr/bin/env python

import hashlib
import optparse
import os
import sys

from datetime import datetime

class ParseError(Exception):
    pass

def digest(filename, algorithm='md5', chunk_size=None, binary=False):
    """"Compute the md5 digest of a file."""
    h = hashlib.new(algorithm)

    if chunk_size is None:
        chunk_size = 128 * h.block_size

    if binary:
        mode = 'rb'
    else:
        mode = 'r'

    with open(filename, mode) as f:
        chunk = f.read(chunk_size)
        while chunk:
            h.update(chunk)
            chunk = f.read(chunk_size)

    return h.hexdigest()

def create_mode(filenames, options):
    for name in filenames:
        entry = Entry(filename=name)
        print entry.to_line()

def warn(message):
    sys.stderr.write('Warning: ' + message + '\n')

class Entry(object):
    def __init__(self, filename=None, string=None,
                 binary=False, ):
        if (filename and string) or (filename is None and string is None):
            raise ValueError('exactly one of filename and string is required')

        if string:
            self.parse_string(string)
        elif filename:
            self.filename = filename
            self.refresh_data()
        else:
            assert(false)

    def parse_string(self, string):
        parts = string.rstrip('\r\n').split(' ', 3)
        if len(parts) != 4:
            raise ParseError('Cannot parse cache line: %r' % line)

        digest, mtime, size, name = parts
        try:
            mtime = float(mtime)
            size = int(size)
        except ValueError:
            raise ParseError('Cannot parse cache line: %r' % line)

        self.digest = digest
        self.mtime = mtime
        self.size = size
        self.filename = name

    def refresh_data(self):
        self.mtime, self.size = self.stat()
        self.digest = digest(self.filename)

    def stat(self):
        stats = os.stat(self.filename)
        return stats.st_mtime, stats.st_size

    def check_stats(self):
        """
        Return True if the file's mtime and size remain the same, else False.
        """
        mtime, size = self.stat()
        if mtime != self.mtime:
            return False
        if size != self.size:
            return False
        return True

    def check_digest(self):
        """
        Return True if the file's hash digest remains the same, else False.
        """
        return self.digest == digest(self.filename)

    def to_tuple(self):
        return self.digest, self.mtime, self.size, self.filename

    def to_line(self):
        return ' '.join(map(str, self.to_tuple()))

def check_file(filename, options):
    f = open(filename, 'r')
    for line in f:
        entry = Entry(string=line)
        if entry.check_digest():
            print entry.filename + ': OK'
        else:
            raise NotImplementedError

def check_mode(filenames, options):
    for name in filenames:
        check_file(name, options)

if __name__ == '__main__':
    p = optparse.OptionParser(usage='usage: %prog [options] FILE...')
    p.add_option('-b', '--binary', action='store_true', dest='binary',
                 help='read in binary mode')
    p.add_option('-t', '--text', action='store_false', dest='binary',
                 help='read in text mode (default)')
    p.add_option('-c', '--check', action='store_true', dest='check_mode',
                 help='read MD5 sums from the FILEs and check them')
    p.add_option('-f', '--file', dest='cache', metavar='CACHE',
                 help='cache checksums in CACHE,'
                      ' updating if mtime or size changed')

    g = optparse.OptionGroup(p,
                             'The following options are useful only when'
                             ' verifying checksums')
    g.add_option('-q', '--quiet', action='store_true', dest='quiet',
                 help="don't print OK for each successfully verified file")
    p.add_option_group(g)

    opts, files = p.parse_args()
    if not files:
        p.error('FILE is required')
        sys.exit(1)

    if opts.check_mode:
        check_mode(files, opts)
    else:
        create_mode(files, opts)
