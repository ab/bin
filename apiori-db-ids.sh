#!/bin/bash
set -eux

timestamp="$(date -d '-1 minute' +%s)"

query="select id from cards where created < $timestamp order by id"

tmpd="$(mktemp -d)"
trap "rm -rf '$tmpd'" EXIT

for host in apiori-db{2,4,-e1,-e2} aws-data1 data.{w2,e1,e3}; do
    ssh -C $host "mysql -e '$query' cards | md5sum" > $tmpd/$host.md5 &
done

wait

set +x

for host in apiori-db{2,4,-e1,-e2} aws-data1 data.{w2,e1,e3}; do
    cut -f1 -d' ' $tmpd/$host.md5 | tr -d '\n'
    echo " $host"
done
