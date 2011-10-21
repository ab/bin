#!/bin/sh

if [ $(id -u) -ne 0 ]; then
	echo "This script must be run as root."
	exit 1
fi

# send a SIGWINCH to all master apache2 processes (they'll be running as root)
# this is equivalent to an apache2ctl -k graceful-stop
killall -WINCH -v -u root apache2
