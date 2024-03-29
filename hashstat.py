#!/usr/bin/env python2

"""
Print or check file checksums, modification times, and sizes.
The MD5 algorithm is used for checksums by default.
"""

import errno
import fcntl
import hashlib
import optparse
import os
import sys

from datetime import datetime

HASH_LENGTHS = {
    32: 'md5',
    40: 'sha1',
    64: 'sha256',
    128: 'sha512'
}

BASENAME = os.path.basename(__file__)

class HasherError(Exception):
    pass

class ParseError(HasherError):
    pass

class VerificationError(HasherError):
    pass
class MtimeMismatch(VerificationError):
    pass
class SizeMismatch(VerificationError):
    pass
class DigestMismatch(VerificationError):
    pass
class FailedOpen(VerificationError):
    pass

class Cache(object):
    def __init__(self, filename, readonly=True):
        self.filename = filename
        self.readonly = readonly

        if not os.path.exists(filename):
            warn('Creating new cache file %r' % filename)
            fdno = os.open(filename, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0666)
            os.close(fdno)

        self.load()

    def open(self):
        # open cache file
        if self.readonly:
            fd = open(self.filename, 'r')
        else:
            fd = open(self.filename, 'r+')

        # lock it for reading or writing depending on self.readonly
        try:
            if self.readonly:
                fcntl.lockf(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            else:
                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError, e:
            if e.errno == errno.EAGAIN:
                raise HasherError('Failed to lock %r' % self.filename)
            else:
                raise

        self.fd = fd
        self.data = {}

    def load(self):
        self.open()

        for line in self.fd:
            self.add_string(line)

        info('Loaded %d entries from cache' % len(self.data))
        return len(self.data)

    def save(self):
        info('Saving cache to ' + repr(self.filename))
        self.fd.seek(0)
        self.fd.truncate(0)
        for _, entry in sorted(self.data.iteritems()):
            self.fd.write(entry.to_line() + '\n')
        self.fd.flush()
        info('Saved %d cache entries' % len(self.data))

    def add_string(self, line):
        entry = Entry(string=line)
        return self.add(entry.filename, entry)

    def add_entry(self, entry):
        return self.add(entry.filename, entry)

    def add(self, key, value):
        if self.data.get(key):
            warn('%r already found in cache' % key)
        self.data[key] = value
        return value

    def get(self, key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data

class CreateRunner(object):
    def __init__(self, filenames, options):
        if options.cache_file:
            self.cache = Cache(options.cache_file, readonly=False)
        else:
            self.cache = None

        self.filenames = filenames
        self.opts = options

    def run(self):
        self.modified = False
        failures = False

        # hash each file
        try:
            for name in self.filenames:
                try:
                    print self.hash_file(name)
                except FailedOpen, e:
                    sys.stderr.write(BASENAME + ': ' + name + ': ' + e.message
                                     + '\n')
                    failures = True
        finally:
            # always save the cache, even when bailing out
            if self.modified:
                self.cache.save()

        return 1 if failures else 0

    def hash_file(self, filename):
        if hasattr(self.opts, 'algorithm'):
            algorithm = self.opts.algorithm
        else:
            algorithm = None

        if self.cache:
            if filename in self.cache:
                entry = self.cache.get(filename)
                if entry.needs_refresh():
                    info('refreshing %r' % filename)
                    entry.refresh_data()
                    self.modified = True
            else:
                entry = Entry(filename=filename, algorithm=algorithm)
                self.cache.add_entry(entry)
                self.modified = True
        else:
            entry = Entry(filename=filename)

        return entry.to_line()

class CheckRunner(object):
    def __init__(self, filenames, options):
        self.filenames = filenames
        self.opts = options

    def check_file(self, filename):
        f = open(filename, 'r')
        for line in f:
            entry = Entry(string=line)
            try:
                entry.verify(stat=self.opts.do_stat,
                             digest=self.opts.do_digest)
            except FailedOpen:
                print entry.filename + ': FAILED open or read'
                self.failed_open += 1
            except (MtimeMismatch, SizeMismatch):
                print entry.filename + ': FAILED mtime/size check'
                self.failed_stat += 1
            except DigestMismatch:
                print entry.filename + ': FAILED'
                self.failed += 1
            else:
                if not self.opts.quiet:
                    print entry.filename + ': OK'

    def run(self):
        self.failed_open = 0
        self.failed_stat = 0
        self.failed = 0
        for name in self.filenames:
            self.check_file(name)

        if self.failed_open:
            warn('%d listed file%s could not be read' %
                 (self.failed_open, '' if self.failed_open == 1 else 's'))
        if self.failed:
            warn('%d computed checksum%s did NOT match' %
                 (self.failed, '' if self.failed == 1 else 's'))
        if self.failed_stat:
            warn('%d listed file%s had mismatched mtime or size' %
                 (self.failed_stat, '' if self.failed_stat == 1 else 's'))

        if self.failed_open or self.failed:
            return 1
        else:
            return 0

def warn(message):
    sys.stderr.write('WARNING: ' + message + '\n')
def info(message):
    sys.stderr.write('Info: ' + message + '\n')

class Entry(object):
    def __init__(self, filename=None, string=None,
                 binary=False, algorithm=None):
        if (filename and string) or (filename is None and string is None):
            raise ValueError('exactly one of filename and string is required')
        if algorithm is None:
            algorithm = 'md5'

        if string:
            self.parse_string(string)
        elif filename:
            self.filename = filename
            self.algorithm = algorithm
            self.refresh_data()
        else:
            assert(false)

    def parse_string(self, string):
        parts = string.rstrip('\r\n').split(' ', 3)
        if len(parts) != 4:
            raise ParseError('Cannot parse hashstat line: %r' % string)

        digest, mtime, size, name = parts
        try:
            mtime = float(mtime)
            size = int(size)
        except ValueError:
            raise ParseError('Cannot parse hashstat line: %r' % string)

        try:
            self.algorithm = HASH_LENGTHS[len(digest)]
        except KeyError:
            raise ParseError('Cannot find hash algorithm of length %d for %r'
                             % (len(digest), line))

        self.digest = digest
        self.mtime = mtime
        self.size = size
        self.filename = name

    def refresh_data(self):
        self.mtime, self.size = self.stat()
        self.digest = self.make_digest()

    def stat(self):
        """Stat a file and return its mtime and size."""
        try:
            stats = os.stat(self.filename)
        except (IOError, OSError), e:
            raise FailedOpen(e.strerror)

        return round(stats.st_mtime, 3), stats.st_size

    def make_digest(self, chunk_size=None, binary=False):
        """"Compute the hash digest of a file."""
        h = hashlib.new(self.algorithm)

        if chunk_size is None:
            chunk_size = 128 * h.block_size

        if binary:
            mode = 'rb'
        else:
            mode = 'r'

        try:
            with open(self.filename, mode) as f:
                chunk = f.read(chunk_size)
                while chunk:
                    h.update(chunk)
                    chunk = f.read(chunk_size)
        except IOError, e:
            raise FailedOpen(e.strerror)

        return h.hexdigest()

    def verify_stat(self):
        """
        Return True if the file's mtime and size remain the same, else False.
        """
        mtime, size = self.stat()

        if mtime != self.mtime:
            raise MtimeMismatch('%r: mtime has changed to %r' %
                                (self.filename, mtime))
        if size != self.size:
            raise SizeMismatch('%r: size has changed to %r' %
                               (self.filename, size))
        return True

    def needs_refresh(self):
        try:
            self.verify_stat()
        except (MtimeMismatch, SizeMismatch):
            return True
        else:
            return False

    def verify_digest(self):
        """
        Return True if the file's hash digest remains the same, else False.
        """
        new_digest = self.make_digest()
        if new_digest == self.digest:
            return True
        else:
            raise DigestMismatch('%r: digest has changed to %s' %
                                 (self.filename, new_digest))

    def verify(self, digest=True, stat=False):
        if not digest and not stat:
            raise ArgumentError('Must check either digest or stat')
        if stat:
            self.verify_stat()
        if digest:
            self.verify_digest()
        return True

    def to_tuple(self):
        return self.digest, self.mtime, self.size, self.filename

    def to_line(self):
        return ' '.join([self.digest, '%0.3f' % self.mtime, str(self.size),
                         self.filename])

if __name__ == '__main__':
    p = optparse.OptionParser(usage='usage: %prog [options] FILE...' +
                              __doc__.rstrip())
    p.add_option('-b', '--binary', action='store_true', dest='binary',
                 help='read in binary mode')
    p.add_option('-t', '--text', action='store_false', dest='binary',
                 help='read in text mode (default)')
    p.add_option('-c', '--check', action='store_true', dest='check_mode',
                 help='read checksums from the FILEs and check them')
    p.add_option('-f', '--file', dest='cache_file', metavar='PATH',
                 help='cache checksums in PATH,'
                      ' updating if mtime or size changed')
    p.add_option('-a', '--algorithm', dest='algorithm',
                 help='use ALGORITHM for checksums')

    g = optparse.OptionGroup(p,
                             'The following options are useful only when'
                             ' verifying checksums')
    g.add_option('-q', '--quiet', action='store_true', dest='quiet',
                 help="don't print OK for each successfully verified file")
    g.add_option('-s', '--stat-only', action='store_false', dest='do_digest',
                 default=True,
                 help='only check file mtime and size, not hash digest')
    g.add_option('-d', '--digest-only', action='store_false', dest='do_stat',
                 default=True,
                 help='only check file digest, not mtime and size')
    p.add_option_group(g)

    opts, files = p.parse_args()
    if not files:
        p.error('FILE is required')

    if opts.check_mode:
        if opts.cache_file:
            p.error('--check and --file are mutually exclusive')
        if opts.algorithm:
            p.error('Algorithm is determined automatically in check mode')
        runner = CheckRunner(files, opts)
        status = runner.run()
    else:
        runner = CreateRunner(files, opts)
        status = runner.run()

    sys.exit(status)
