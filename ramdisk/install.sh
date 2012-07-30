#!/bin/sh
set -eu

cd "$(dirname "$0")"

mkdir -vp /etc/ramdisk.d
cp -v create-userdirs /etc/ramdisk.d/
cp -v mount-ramdisk /etc/init.d/
