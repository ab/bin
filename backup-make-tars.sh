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

run_quiet() {
    local output ret
    output=$(run "$@" 2>&1) && ret=$? || ret=$?
    if [ $ret -ne 0 ]; then
        echo "$output"
    fi
    return $ret
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

check_tools() {
    echo "Checking that we have all CLI tools needed"
    run_quiet gpg --version
    run_quiet tar --version
    run_quiet zstdmt --version
    run_quiet prompt_yn --help
    run_quiet which pwgen
}

phase() {
    colorecho cyan "==== $* ====" >&2
    "$@"
}

get_file_size() {
    local stat
    if [[ $OSTYPE == darwin* ]]; then
        stat=gstat
    else
        stat=stat
    fi
    "$stat" --format='%s' -- "$1"
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
        size=$(gpg -d "$PASS_FILE" | gpg -d | wc -c)
        if [ "$size" -eq 0 ]; then
            colorecho red "Invalid passphrase file: passphrase is empty"
            return 1
        fi
        return
    fi

    echo "Generating new symmetric pass file"
    echo "Don't forget to create/copy the passphrase hint!"

    run pwgen -s 52 1 | gpg -c -z0 | gpg -e -z0 -r "$GPG_RECIP" -o "$PASS_FILE" || {
        colorecho yellow "You should probably delete $PASS_FILE"
        return 1
    }
}

# Check whether existing output file exists.
# If so, prompt the user for whether it's OK to skip.
#
# Return:
#   0   file does not exist
#   1   error
#   10  file exists, user refuses to skip
#   42  file exists, user confirms OK to skip
#
check_exists() {
    local outfile min_size ret
    outfile="$1"
    min_size="$2"
    if [ -s "$outfile" ]; then
        local size
        size=$(get_file_size "$outfile")
        if [ "$size" -le "$min_size" ]; then
            colorecho red "Error: backup file $outfile already exists, but looks empty"
            return 1
        fi
        echo >&2 "Backup file $outfile already exists ($((size / 1024 / 1024)) MiB)..."
        if [ -n "$AUTO_SKIP" ]; then
            echo "--auto-skip is enabled"
            return 42
        fi
        if ! prompt_yn "OK to skip?"; then
            return 10
        fi
        return 42
    fi

    return 0
}

backup_single() {
    local tar_opts exclude_tag=
    tar_opts=()

    colorecho cyan >&2 "## backup_single $*"

    while [ $# -ge 1 ] && [[ $1 == -* ]]; do
        case "$1" in
            --excl-tag)
                exclude_tag=.ab-backup-exclude
                tar_opts+=("--exclude-tag=$exclude_tag")
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

    local ret

    if [ -n "$VERBOSE" ]; then
        tar_opts+=(-v)
    fi

    # save a list of excluded files
    if [ -n "$exclude_tag" ]; then
        local excluded_list
        excluded_list="$PREFIX.$shortname.excluded-ls.txt.zst.gpg"

        check_exists "$excluded_list" 78 && ret=$? || ret=$?
        if ! [[ $ret -eq 0 || $ret -eq 42 ]]; then
            return "$ret"
        fi
        if [[ $ret -eq 42 ]]; then
            echo "Skipped $excluded_list"
        elif [[ $ret -ne 0 ]]; then
            return "$ret"
        else
            run sudo --validate

            echo "Saving list of excluded files"

            run sudo "$(dirname "$0")/backup-excluded-directories" --one-file-system -t "$exclude_tag" --print-contents "$path" \
                | run zstdmt \
                | gpg -c -z0 -o "$excluded_list" --batch --passphrase-fd 3 \
                3< <(gpg -d "$PASS_FILE" | gpg -d)

            echo "Wrote list of excluded files to $excluded_list"
        fi
    fi

    check_exists "$outfile" 16 && ret=$? || ret=$?
    if [[ $ret -eq 42 ]]; then
        echo "Skipped $outfile"
        return
    elif [[ $ret -ne 0 ]]; then
        return "$ret"
    fi

    # be sure we have sudo working before opening pipes
    run sudo --validate

    run sudo tar -c "${tar_opts[@]}" "$path" \
        | run zstdmt \
        | gpg -c -z0 -o "$outfile" --batch --passphrase-fd 3 \
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

AUTO_SKIP=
while [ $# -ge 1 ] && [[ $1 == -* ]]; do
    case "$1" in
        -h|--help)
            usage
            exit
            ;;
        --auto-skip)
            AUTO_SKIP=1
            ;;
        *)
            usage
            echo >&2 "Invalid option: $1"
            exit 1
            ;;
    esac
    shift
done

check_tools

phase generate_passphrase

phase backups_main

phase checksums_compute
phase checksums_sign
