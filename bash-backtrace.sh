# shellcheck shell=bash
#
# Add python-like backtraces to your bash shell scripts!
#
# Use like so:
#
#   #!/bin/bash
#   set -eu
#   source "../bin/bash-backtrace.sh"
#   ...
#
# It uses the ERR trap to trigger on errors and FUNCNAME for the traceback.
#
# It's recommended to use `set -e` (set -o errexit), which will cause your
# script to exit on errors. Without errexit, you may see duplicate tracebacks
# for functions, because each function/command separately invokes the ERR
# handler when they exit nonzero.
#

if [ -z "${BASH_VERSION-}" ]; then
    echo >&2 "Error: this script only works in bash"
    # shellcheck disable=SC2317
    return 1 || exit 1
fi

set -E

# References:
# - https://gist.github.com/ryo1kato/3102982
# - https://gist.github.com/kergoth/6395873

bash_backtrace() {
    local ret=$?
    local frame
    local FRAMES=${#BASH_SOURCE[@]}

    echo >&2 "Traceback (most recent call last):"

    for ((frame=FRAMES-2; frame >= 0; frame--)); do
        local lineno=${BASH_LINENO[frame]}
        local source=${BASH_SOURCE[frame+1]}

        printf >&2 '  File "%s", line %d, in %s\n' \
            "$source" "$lineno" "${FUNCNAME[frame+1]}"

        if [ -f "$source" ] && [ -r "$source" ]; then
            sed >&2 -n "${lineno}s/^[   ]*/    /p" "$source"
        else
            echo >&2 "    <source file not readable>"
        fi
    done

    printf >&2 "Command exited with status %d\n" "$ret"
}

trap bash_backtrace ERR
