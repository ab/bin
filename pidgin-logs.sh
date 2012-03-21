#!/bin/sh
set -eux
cd ~/.purple/logs
git pull
git add aim irc jabber
git commit -m "Logs from $(hostname -s)"
git push
