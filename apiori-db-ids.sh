#!/bin/bash
set -eux

timestamp="$(date -d '-1 minute' +%s)"

query="select id from cards where created < $timestamp order by id"

tmpd="$(mktemp -d)"
trap "rm -rf '$tmpd'" EXIT

for host in apiori-db{2,4,-e1,-e2} aws-data{1,2}; do
    ssh -C $host "mysql -e '$query' cards | md5sum" > $tmpd/$host.md5 &
done

wait

set +x

for host in apiori-db{2,4,-e1,-e2} aws-data{1,2}; do
    echo -n "$host "
    cat $tmpd/$host.md5
done

set -x
