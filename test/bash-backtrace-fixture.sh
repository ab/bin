#!/usr/bin/env bash
set -eu

source "$1"

outer() {
    inner
}

inner() {
    false args blah

    echo notreached
}

outer
