#!/usr/bin/env python
import hashlib
import os
import sys

def md5(filename, chunk_size=None):
    """"Compute the md5 digest of a file."""
    h = hashlib.md5()

    if chunk_size is None:
        chunk_size = 128 * h.block_size

    with open(filename, 'rb') as f:
        chunk = f.read(chunk_size)
        while chunk:
            h.update(chunk)
            chunk = f.read(chunk_size)

    return h.hexdigest()

def stat_info(filename):
    """
    Call stat on a file and return (mtime, size).

    The mtime will be in seconds since the epoch and the size in bytes.
    """
    info = os.stat(filename)
    return (info.st_mtime, info.st_size)

def md5_stat(filename):
    digest = md5(filename)
    info = stat_info(filename)
    return (digest, info[0], info[1])

def main(filenames):
    for name in filenames:
        print ' '.join(map(str, md5_stat(name))) + ' ' + name

if __name__ == '__main__':
    filenames = sys.argv[1:]
    if not filenames:
        sys.stderr.write('usage: ' + os.path.basename(sys.argv[0]) +
                         ' FILE...\n')
        sys.exit(1)

    main(filenames)
