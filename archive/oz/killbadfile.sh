#!/bin/sh
set -e

echo "+ shred -vzn 0 $*"
shred -vzn 0 $*

echo "+ rm -vf $*"
rm -vf $*

for i in "$@"; do
	echo "+ echo \"BAD BLOCK REMOVED\" > \"$i~\""
	echo "BAD BLOCK REMOVED" > "$i~"
done
