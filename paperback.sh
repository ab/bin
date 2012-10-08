#!/bin/sh
set -eux

file="$1"

file "$file"
base64 "$file" > "$file.base64"
# TODO: use split
qrencode -o "$file.qr.png" < "$file.base64"
