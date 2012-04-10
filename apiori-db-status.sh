#!/bin/sh
set -eu

check="mysql -e 'show slave status \G'"

full=
if [ $# -ge 1 ] && [ "$1" = "--full" ]; then
    full=1
fi

set -x

if [ -n "$full" ]; then
  ssh apiori-db2 "$check"
  ssh apiori-db4 "$check"
  ssh apiori-db-e1 "sudo -H $check"
  ssh apiori-db-e2 "sudo -H $check"
else
  ssh apiori-db2 "$check | grep Seconds_Behind_Master"
  ssh apiori-db4 "$check | grep Seconds_Behind_Master"
  ssh apiori-db-e1 "sudo -H $check | grep Seconds_Behind_Master"
  ssh apiori-db-e2 "sudo -H $check | grep Seconds_Behind_Master"
fi
