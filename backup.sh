#!/bin/bash
set -e
set -o nounset

VERBOSE=1

SCRIPT="$(basename $0)"
HOST="$(hostname -s)"
SSH_HOST=root@dellaptop-remote
REMOTE_DIR=/media/T-disk/snapshot
CUR_SNAP=daily.0

SOURCES=( "/home" "/usr/local" )

function log() { logger -t "$SCRIPT[$$]" "$*" ; }
function logerr() { log "$*"; echo >&2 "$(date '+%F %R') $*" ; }
function vlog() { if [ -n "$VERBOSE" ]; then echo "$*"; fi ; }

function SSH() {
	vlog "+ $*"
	ssh $SSH_HOST $*
}

function check_dir_exists() {
	if ! ssh $SSH_HOST test -d "$REMOTE_DIR"; then
		logerr "ERROR: Cannot find $REMOTE_DIR on $SSH_HOST."
		exit 2
	fi
}

function rotate_snaps() {
	oldest_snap=$(ssh $SSH_HOST "ls $REMOTE_DIR" | grep daily | sort -rn | head -1)
	snapnum=$(echo $oldest_snap | cut -f2 -d.)
	snap=daily

	# increment number of snapshots 0..$snapnum by renaming them
	for i in `seq $snapnum -1 0`; do
		SSH mv "$REMOTE_DIR/$snap.$i" "$REMOTE_DIR/$snap.$(( $i + 1 ))"
	done

	# hardlink snapshot.1 to snapshot.0
	SSH cp -al "$REMOTE_DIR/$snap.1" "$REMOTE_DIR/$snap.0"
}

function do_rsync() {
	dest="$SSH_HOST:$REMOTE_DIR/$CUR_SNAP/$HOST/"
	vlog "transferring $1 to $dest"
	[ -n "$VERBOSE" ] && v="-v" || v=""
	rsync -axR $v --numeric-ids --del "$1" "$dest"
}

check_dir_exists

rotate_snaps

for src in "${SOURCES[@]}"; do
	do_rsync "$src"
done

SSH touch $REMOTE_DIR/$CUR_SNAP

