#!/usr/bin/env python
import optparse
import os
import re
import socket
import sys
import time
from datetime import datetime
from subprocess import Popen, PIPE

VERSION = '0.8'

# TODO: put config in a separate file
VERBOSE = 1

HOST = socket.gethostname().split('.')[0]
SSH_HOST = "dellblue-backup"
REMOTE_DIR = "/media/T-disk/snapshot"
CUR_SNAP = "daily.0"
LOCAL_CHECK_DIR = "/home/andy/Private/.ssh/"

SOURCES = [("/home", ['.gvfs/']),
           ("/usr/local", [])]
# TODO: run rsync of ~/.Private with -W?
# TODO: more sane per-source ignore list (for .gvfs)

EXPIRE_DAYS = [('daily', 14),
               ('monthly', None)]

DRY_RUN = False

def log(message):
    # TODO: implement this
    # logger -t "$SCRIPT[$$]" "$*"
    raise NotImplementedError

def logerr(message):
    stamp = time.strftime('%F %R')
    sys.stderr.write(stamp + '\t' + str(message) + '\n')
    # log(message)

def vlog(message):
    if VERBOSE:
        print message

class DoesNotExist(Exception):
    pass

class BackupError(Exception):
    def __init__(self, *args):
        args = args[:2]
        Exception.__init__(self, *args)
        self.errno = None
        self.message = None
        if len(args) >= 2:
            self.errno = args[0]
            self.message = args[1]
        elif len(args):
            self.message = args[1]

    def __str__(self):
        if self.errno is None:
            return str(self.message)
        else:
            return '[Errno %s] ' + self.errno + str(self.message)


# =============================================================
# Subprocess code -- could be abstracted into a separate module

class ProcReturn(object):
    def __init__(self, returncode, stdout, stderr):
        self.returncode = int(returncode)
        self.stdout = stdout
        self.stderr = stderr

    def __nonzero__(self):
        """Object is True if exit status is 0. (To emulate shell behavior.)"""
        return self.returncode == 0

    def __str__(self):
        s = 'Process returned %d' % self.returncode
        if self.stdout:
            s += "\nstdout: '''" + self.stdout + "'''"
        if self.stderr:
            s += "\nstderr: '''" + self.stderr + "'''"
        return s

    def __repr__(self):
        return "<ProcReturn object at 0x%x, status %d>" % (id(self),
                                                           self.returncode)

class CommandError(Exception):
    """Exception raised for process errors.

    Attributes:
        returncode -- the command's return code
        command -- the command executed
    """
    def __init__(self, returncode, command, stdout=None, stderr=None):
        self.returncode = int(returncode)
        self.command = command
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return "[Exit status %d] %s" % (self.returncode, self.command)

class SshError(CommandError):
    """Exception raised for SSH errors.

    Attributes:
        returncode -- the command's return code
        command -- the command executed
    """

def run(arglist, raise_err=False, ssh_err=False):
    """Run a command, optionally raising an exception on errors."""
    p = Popen(arglist, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    if raise_err and p.returncode != 0:
        if ssh_err and p.returncode == 255:
            exc = SshError
        else:
            exc = CommandError
        raise exc(p.returncode, arglist, stdout=stdout, stderr=stderr)

    return ProcReturn(p.returncode, stdout, stderr)

def run_safe(arglist):
    """Convenience function to call run() and raise an exception on errors."""
    run(arglist, raise_err=True)

def ssh(command, raise_err=False, dry_safe=True):
    """Use run() to ssh to SSH_HOST and run command."""
    if DRY_RUN and not dry_safe:
        # we're in a dry run but command is not dry-run safe
        vlog('+ (ssh) [DRY RUN] ' + command)
        return None

    vlog('+ (ssh) ' + command)
    return run(['ssh', SSH_HOST, command], raise_err=raise_err, ssh_err=True)

def ssh_safe(command):
    """Convenience function to call ssh() and raise an exception on errors."""
    return ssh(command, raise_err=True)

def ssh_dry(command):
    """Convenience function to call ssh() for a command unsafe for dry runs."""
    return ssh(command, raise_err=True, dry_safe=False)

# =====================
# Main backup functions

class LockError(Exception):
    pass

class snap_lock(object):
    """A remote locking context manager."""

    def __init__(self):
        self.hostname = os.uname()[1].replace('/','')
        self.lockdir = REMOTE_DIR + '/lockdir'
        self.lockf = self.lockdir + '/' + self.hostname

    def __enter__(self):
        """Lock the lock."""
        try:
            ssh_safe('mkdir "%s"' % self.lockdir)
            ssh_safe('echo "%d" > "%s"' % (os.getpid(), self.lockf))
        except CommandError, e:
            logerr("ERROR: failed to acquire lockdir '%s'." % self.lockdir)
            logerr(e.stderr)
            raise LockError

    def __exit__(self, *exc_info):
        """Release the lock."""
        ssh_safe('rm "%s"' % self.lockf)
        ssh_safe('rmdir "%s"' % self.lockdir)

def check_dir_exists():
    r = ssh('test -d "%s"' % REMOTE_DIR)
    if not r:
        logerr("ERROR: Cannot find %s on %s." % (REMOTE_DIR, SSH_HOST))
        logerr("stdout: '%s'" % r.stdout)
        logerr("stderr: '%s'" % r.stderr)
        raise BackupError(2, 'check_dir_exists() failed')

def check_privs():
    if os.getuid() != 0:
        logerr("ERROR: This script should be run as root.")
        raise BackupError(3, 'check_privs() failed')

def check_local_dir_exists():
    if LOCAL_CHECK_DIR and not os.path.isdir(LOCAL_CHECK_DIR):
        logerr("ERROR: Local check directory doesn't exist.")
        raise BackupError(4, 'check_local_dir_exists() failed')

def get_snap_mtime(snap):
    path = '"%s/%s"' % (REMOTE_DIR, snap)
    try:
        result = ssh_safe('/usr/bin/stat --format="%Y" ' + path)
    except CommandError, e:
        if e.stderr.endswith('No such file or directory\n'):
            vlog('stat: %s: No such file or directory' % snap)
            raise DoesNotExist
        else:
            raise

    seconds_since_epoch = int(result.stdout.strip())
    return datetime.fromtimestamp(seconds_since_epoch)

def get_snap_num_factory(prefix):
    def get_snap_num(name):
        assert(name.startswith(prefix))
        return int(name[len(prefix):])
    return get_snap_num

def list_snaps(stype, sort=True):
    """List snapshots from given series (e.g. daily) in sorted order."""
    result = ssh_safe('ls "%s"' % REMOTE_DIR)
    snaps = result.stdout.split('\n')
    snaps = [x for x in snaps if x.startswith(stype + '.')]

    if sort:
        getnum = get_snap_num_factory(stype + '.')
        snaps.sort(key=getnum)

    return snaps

def rotate_snaps(stype='daily', hard_link=True):
    snaps = list_snaps(stype)
    getnum = get_snap_num_factory(stype + '.')
    snapnums = map(getnum, snaps)

    if not snapnums:
        vlog('No existing snapshots')
        return False

    # increment number of each snapshot by renaming it
    for i in reversed(snapnums):
        snapfrom = "%s/%s.%d" % (REMOTE_DIR, stype, i)
        snapto   = "%s/%s.%d" % (REMOTE_DIR, stype, i + 1)
        ssh_dry('mv -vT "%s" "%s"' % (snapfrom, snapto))

    if hard_link:
        recent_num = snapnums[0] + 1
        # hardlink most recent snapshot to snapshot.0
        snap_hard_link("%s.%d" % (stype, recent_num), "%s.0" % stype)

    return True

def snap_hard_link(source, dest):
    return ssh_dry('cp -al "%s/%s" "%s/%s"' % (REMOTE_DIR, source,
                                               REMOTE_DIR, dest))

def snap_delete(snap, verbose=False):
    assert(snap != '')
    opts = '-v ' if verbose else ''
    return ssh_dry('rm -rf ' + opts + '"%s/%s"' % (REMOTE_DIR, snap))

def find_snaps(stype, mtime):
    result = ssh_safe('find "%s" -maxdepth 1 -name "%s.*" -mtime "%s"' %
                      (REMOTE_DIR, stype, mtime))
    snaps = filter(None, result.stdout.split('\n'))
    return map(os.path.basename, snaps)

def snap_cleanup():
    """Clean up old snapshots according to EXPIRE_DAYS schedule."""
    vlog('Cleaning out old snapshots...')
    count = 0
    for stype, expire_days in EXPIRE_DAYS:
        if expire_days is None:
            continue
        for snap in find_snaps(stype, '+%d' % expire_days):
            if snap.endswith('.0'):
                # don't remove the last snapshot of any series
                continue
            count += 1
            snap_delete(snap)

    return count

def snap_archive_monthly():
    """
    If there is no monthly snapshot for the current month, rotate the monthly
    snapshots and hard link the most recent daily snapshot to monthly.0.
    """
    vlog('Archiving new monthly.0 as needed...')
    now = datetime.now()

    try:
        last_monthly = get_snap_mtime('monthly.0')
    except DoesNotExist:
        pass
    else:
        if last_monthly.year == now.year and last_monthly.month == now.month:
            vlog('monthly.0 is from the current month.')
            return

    for snap in reversed(list_snaps('daily')):
        mtime = get_snap_mtime(snap)
        if mtime.month == now.month and mtime.year == now.year:
            # found the first daily of this month
            break
    else:
        vlog('No daily snapshots from this month were found.')
        return

    vlog('Rotating monthly snapshots...')
    rotate_snaps('monthly', hard_link=False)

    vlog('Saving %s to monthly.0...' % snap)
    snap_hard_link(snap, 'monthly.0')
    return True

def do_rsync(source, excludes):
    dest_dir = '/'.join((REMOTE_DIR, CUR_SNAP, HOST))
    dest = SSH_HOST + ':' + dest_dir
    vlog("Transferring %s to %s..." % (source, dest))

    # ensure remote directory exists
    ssh_dry('mkdir -p "%s"' % dest_dir)

    opts = ['-axR', '-z']

    if VERBOSE:
        opts.append('-v')

    opts += ['--exclude=%s' % e for e in excludes]
    if excludes:
        vlog("excluding: " + ', '.join(excludes))

    cmd = ['rsync'] + opts + ['--numeric-ids', '--del', source, dest]

    if DRY_RUN:
        vlog('+ [DRY_RUN] ' + ' '.join(cmd))
        return True
    else:
        result = run(cmd)

    if result.returncode == 0:
        return True

    # if returncode is 255 and stderr contains 'Broken pipe', try again
    # otherwise, fail
    if result.returncode == 255:
        if 'Broken pipe' in result.stderr:
            logerr('rsync: Broken pipe (network failure?)')
            logerr('Retrying...')
            # TODO: institute max_retries rather than hitting RecursionLimit
            return do_rsync(source)

    logerr("Rsync failed : " + source + " -> " + dest)
    logerr("Writing stdout to /tmp/rsync.out")
    # TODO: this is a security risk. write to randomly named file
    f = open('/tmp/rsync.out', 'w')
    f.write(result.stdout)
    f.close()
    logerr("stderr: '''" + result.stderr + "'''")
    raise CommandError(result.returncode, cmd)

def main():
    p = optparse.OptionParser(usage = '%prog [options]',
                              version = '%prog ' + VERSION)
    p.add_option('-n', '--dry-run', dest='dry_run', action='store_true',
                 help="skip most actions with side effects", default=False)
    p.add_option('--no-rotate', dest='rotate', action='store_false',
                 help="skip rotation of numeric snapshots", default=True)
    p.add_option('--no-link', dest='link', action='store_false',
                 help="skip hard link of snap.1 to snap.0", default=True)
    p.add_option('--no-cleanup', dest='cleanup', action='store_false',
                 help='skip removal of old snapshots', default=True)
    p.add_option('--rotate-only', dest='rotate_only', metavar='SERIES',
                 help="rotate snapshots in SERIES (daily, etc.) and exit")
    p.add_option('--cleanup-only', dest='cleanup_only', action='store_true',
                 help="remove old snapshots and exit", default=False)
    opts, args = p.parse_args()

    if opts.rotate_only and not opts.rotate:
        p.error("--no-rotate and --rotate-only are mutually exclusive")
    if opts.cleanup_only and not opts.cleanup:
        p.error("--no-cleanup and --clenaup-only are mutually exclusive")
    if opts.rotate_only and opts.cleanup_only:
        p.error("at most one --foo-only option may be supplied")

    if not opts.rotate:
        # --no-rotate implies --no-link
        opts.link = False

    if opts.dry_run:
        global DRY_RUN
        vlog('DRY RUN')
        DRY_RUN = True

    check_privs()
    check_local_dir_exists()
    check_dir_exists()

    with snap_lock():
        if opts.rotate_only:
            vlog('Rotating snapshots in series %s...' % opts.rotate_only)
            rotate_snaps(opts.rotate_only, opts.link)
            return 0

        if opts.cleanup:
            snap_archive_monthly()
            snap_cleanup()
            if opts.cleanup_only:
                return 0

        if opts.rotate:
            vlog('Rotating daily snapshots...')
            rotate_snaps('daily', opts.link)

        # actually take a backup
        for src, excludes in SOURCES:
            do_rsync(src, excludes)

        ssh_dry('touch ' + REMOTE_DIR + '/' + CUR_SNAP)
        return 0

if __name__ == '__main__':
    try:
        r = main()
        if r == 0:
            vlog('Done!')
        sys.exit(r)

    except CommandError, e:
        if e.stdout:
            sys.stderr.write('stdout: ' + e.stdout)
        if e.stderr:
            sys.stderr.write('stderr: ' + e.stderr)
        raise

    except LockError:
        sys.exit(5)

    except BackupError, e:
        if e.errno:
            sys.exit(e.errno)
        else:
            sys.exit(1)

