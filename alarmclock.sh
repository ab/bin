#!/bin/bash
set -eu
set -o pipefail

SOUND_FILE="$HOME/media/music/Straus/Also Sprach Zarathustra - Der Held/01 - Sunrise.ogg"

# You can find out the hardware clock time zone by comparing `hwclock -r` and
# `hwclock -r --localtime` to the actual current time. Note that hwclock always
# prints the result in your local timezone.
HWCLOCK_TZ="--local"

if [ $# -lt 1 ]; then
    cat >&2 <<EOM
usage: $(basename "$0") TIME [SOUND_FILE]

Immediately suspend the computer until TIME (as understood by date(1) -d), then
play SOUND_FILE.

The hardware clock is considered to be in $(echo $HWCLOCK_TZ | tr -d '-') time.

Default SOUND_FILE:
    $SOUND_FILE
EOM
    exit 1
fi

if [ $# -gt 2 ]; then
    SOUND_FILE="$2"
fi

wake_time_string="$1"

if [ ! -e "$SOUND_FILE" ]; then
    echo >&2 "Error: No such file or directory: $SOUND_FILE"
    exit 2
fi
if [ ! -r "$SOUND_FILE" ]; then
    echo >&2 "Error: permission denied: $SOUND_FILE"
    exit 3
fi

which cvlc >/dev/null

wake_time_secs="$(date +%s -d "$wake_time_string")"
if amixer sget Master | grep -F '[off]' >/dev/null; then
    amixer sget Master
    echo >&2 "Error: sound appears to be muted!"
    exit 4
fi
volume="$(amixer sget Master | grep -Eo '[0-9]+%' | tr -d '%')"
if [ "$volume" -lt 15 ]; then
    echo >&2 "Warning: volume appears to be < 15% (${volume}%)"
fi

set -x
date
sudo rtcwake $HWCLOCK_TZ -m mem -t "$wake_time_secs"
date
cvlc "$SOUND_FILE"
