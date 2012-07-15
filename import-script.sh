#!/bin/sh
# Imports a script into this repo. It's a little meta.

set -eux
git add "$1"
git commit -m "Import $1." --date="$(stat --format=%y "$1")"
