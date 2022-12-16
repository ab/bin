#!/usr/bin/env python2
import optparse
import os
import re
import sys
from subprocess import check_call

VERSION = '1.1'

verbose = True
dry_run = True

def rename(prefix, old, new):
    old = os.path.join(prefix, old)
    new = os.path.join(prefix, new)

    if os.path.exists(new):
        raise IOError('path exists: ' + new)
    if verbose:
        print "`%s' -> `%s'" % (old, new)

    if not dry_run:
        os.rename(old, new)

def shred_rename(path, isdir):
    if dry_run:
        print "shred_rename(%r)." % path
        return

    assert(isdir == os.path.isdir(path))

    parent, target = os.path.split(path)
    name = '0' * len(target)
    rename(parent, target, name)

    while len(name) > 1:
        newname = name[1:]
        rename(parent, name, newname)
        name = newname

    if isdir:
        os.rmdir(os.path.join(parent, name))
    else:
        os.unlink(os.path.join(parent, name))
    print "`%s' removed." % path

def shred_dir(path):
    return shred_rename(path, True)

def shred_link(path):
    return shred_rename(path, False)

def shred_file(path, iterations=3):
    opts = '-uzv' if verbose else '-uz'
    cmd = ('shred', opts, '-n', "%d" % iterations, path)
    if dry_run:
        print cmd
    else:
        check_call(cmd)

def shred(root_path, iterations=3):
    if dry_run:
        print 'DRY RUN'

    if os.path.islink(root_path):
        if verbose:
            print 'shredding symbolic link...'
        shred_link(root_path)
        return

    if not os.path.exists(root_path):
        raise IOError(2, "No such file or directory: %r" % root_path)

    if os.path.isfile(root_path):
        if verbose:
            print 'shredding file...'
        shred_file(root_path, iterations)
        return

    if verbose:
        print 'shredding directory...'

    # walk the root path from the bottom up
    for dirpath, dirs, files in os.walk(root_path, topdown=False):

        # rename all directories with only zeroes in the name
        for zerodir in (d for d in dirs if re.search('^0+$', d)):
            newname = zerodir + '_'
            while os.path.exists(newname):
                newname += '_'
            rename(dirpath, zerodir, newname)

        # shred all files
        for f in files:
            path = os.path.join(dirpath, f)
            if os.path.islink(path):
                shred_link(path)
            else:
                shred_file(path, iterations)

        # shred all directories
        for d in dirs:
            shred_dir(os.path.join(dirpath, d))

    # shred the root
    shred_dir(root_path)

if __name__ == '__main__':
    p = optparse.OptionParser(usage='%prog [options] FILE...',
                              version='%prog ' + VERSION)
    p.add_option('-v', '--verbose', dest='verbose', action='store_true',
                 help='increase verbosity', default=True)
    p.add_option('-q', '--quiet', dest='verbose', action='store_false',
                 help='decrease verbosity')
    p.add_option('-d', '--dry-run', dest='dry_run', action='store_true',
                 help='perform a trial run with no changes made')
    p.add_option('-n', '--iterations', dest='iterations', metavar='N',
                 help='overwrite N times instead of the default (3)',
                 type='int', default=3)

    opts, args = p.parse_args()
    if len(args) < 1:
        p.print_help()
        sys.exit(1)

    verbose = opts.verbose
    dry_run = opts.dry_run

    for path in args:
        try:
            shred(path, iterations=opts.iterations)
        except IOError, e:
            print 'IOError:', e
            sys.exit(e.errno)
        except Exception, e:
            print 'ERROR:', e
            sys.exit(3)

