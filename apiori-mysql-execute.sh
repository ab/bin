#!/bin/sh
set -eu
set -x

check="mysql -e '$*'"
ssh apiori-db2 "$check"
ssh apiori-db4 "$check"
ssh apiori-db-e1 "$check"
ssh apiori-db-e2 "$check"
