#!/bin/bash
set -euo pipefail

VERBOSE="${VERBOSE-}"
HOST="$HOSTNAME"
GPG_RECIP="${GPG_RECIP-0xC7090B1A5F57CDC5}"

if [ -z "$HOST" ]; then
    echo >&2 "error: missing HOSTNAME"
fi

DATE="$(date +%F)"

PREFIX="$HOST.$DATE"
PASS_FILE="$PREFIX.passphrase.gpg.gpg"

run() {
    echo >&2 "+ $*"
    "$@"
}

gpg() {
    echo >&2 "+ gpg $*"
    command gpg "$@"
}

# Use colorecho command, or fall back to echo.
if which colorecho >/dev/null; then
    colorecho() {
        command colorecho "$@"
    }
else
    colorecho() {
        shift
        echo "$@"
    }
fi

phase() {
    colorecho cyan "==== $* ====" >&2
    "$@"
}

generate_passphrase() {
    if [ -s "$PASS_FILE" ]; then
        echo "Found existing $PASS_FILE"
        # detect empty inner pass file
        local size
        size=$(gpg -d "$PASS_FILE" | wc -c)
        if [ "$size" -eq 0 ]; then
            colorecho red "Invalid passphrase file: inner .gpg is empty"
            return 1
        fi
        return
    fi

    echo "Generating new symmetric pass file"
    echo "Don't forget to create/copy the passphrase hint!"

    run pwgen -s 52 1 | gpg -c | gpg -e -r "$GPG_RECIP" -o "$PASS_FILE" || {
        colorecho yellow "You should probably delete $PASS_FILE"
        return 1
    }
}

backup_single() {
    local tar_opts
    tar_opts=()

    colorecho cyan >&2 "## backup_single $*"

    while [ $# -ge 1 ] && [[ $1 == -* ]]; do
        case "$1" in
            --excl-tag)
                tar_opts+=("--exclude-tag=.ab-backup-exclude")
                ;;
            --one-file-system)
                tar_opts+=("--one-file-system")
                ;;
            *)
                echo >&2 "backup_single: unknown option $1"
                return 1
                ;;
        esac
        shift
    done
    if [ $# -ne 2 ]; then
        echo >&2 "usage: backup_single [OPTS] PATH SHORTNAME"
        return 1
    fi
    local path shortname outfile
    path="$1"
    shortname="$2"

    outfile="$PREFIX.$shortname.tar.zst.gpg"

    if [ -s "$outfile" ]; then
        if [ "$(wc -c < "$outfile")" -le 16 ]; then
            colorecho red "Error: backup file $outfile already exists, but looks empty"
            return 1
        fi
        prompt_yn "Backup file $outfile already exists... OK to skip?"
        return
    fi

    if [ -n "$VERBOSE" ]; then
        tar_opts+=(-v)
    fi

    # be sure we have sudo working before opening pipes
    run sudo --validate

    run sudo tar -c "${tar_opts[@]}" "$path" \
        | run zstdmt \
        | gpg -c -z 0 -o "$outfile" --batch --passphrase-fd 3 \
        3< <(gpg -d "$PASS_FILE" | gpg -d)
}

backups_main() {
    backup_single /boot boot
    backup_single --one-file-system /etc etc
    backup_single --one-file-system --excl-tag / root
    backup_single --one-file-system --excl-tag /home/andy home
}

checksums_compute() {
    run sha256sum "$PREFIX".*.gpg > "$PREFIX.SHA256SUMS.txt"
}

checksums_sign() {
    gpg --detach-sign -a "$PREFIX.SHA256SUMS.txt"
}


phase generate_passphrase

phase backups_main

phase checksums_compute
phase checksums_sign
