#!/usr/bin/env bash
set -eu

source "$1"

outer() {
    inner
}

inner() {
    cat /nonexistent

    echo notreached
}

outer
