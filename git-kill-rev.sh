#!/bin/sh
set -eu

usage() {
    echo >&2 <<EOM
usage: $(basename "$0") REVISION FILE...

Kill lines from FILEs that were changed by REVISION according to git blame.
EOM
}

run() {
    echo >&2 "+ $*"
    "$@"
}

if [ $# -lt 2 ]; then
    usage
    exit 1
fi

kill_revs() {
    cmd="$(git blame -lns "$file" | cut -d' ' -f1 | grep -n "^$rev" | cut -d: -f1 | perl -pe 's/\n/d;/')"
    run sed -i "$cmd" "$file"
}

rev="$1"
shift

for file in "$@"; do
    kill_revs "$rev" "$file"
done
