#!/bin/sh
set -eux

bdir="/mnt/backups/snapshot"

test -d "$bdir"

test $(id -u) -eq 0

lastsnap="$(ls -t "$bdir" | head -1)"
today="$(date +%F)"

cp -al "$bdir/$lastsnap" "$bdir/$today"

rsync -avxR --del /boot "$bdir/$today/./"
rsync -avx --del / "$bdir/$today/root/"
touch "$bdir/$today"
