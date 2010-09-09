#!/bin/bash

if [ -z "$1" ]; then
	rounds=500
else
	rounds=$1
fi

for i in `seq 1 $rounds`; do
	echo $RANDOM
	sleep 0.05
done
