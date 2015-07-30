#!/bin/sh
set -eu

cd "$(dirname "$0")"

mkdir -vp /etc/ramdisk.d
mkdir -vp /mnt/ramdisk
cp -v create-userdirs /etc/ramdisk.d/
cp -v mount-ramdisk /etc/init.d/
update-rc.d mount-ramdisk defaults
