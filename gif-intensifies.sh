#!/usr/bin/env bash
# Generates an animated version of image that shakes.
# Based on https://gist.github.com/alisdair/ffc7c884ee36ac132131f37e3803a1fe

set -euo pipefail
[[ -z ${TRACE-} ]] || set -x

# check dependencies
hash magick identify

usage() {
  echo "Usage: $(basename "$0") [OPTIONS] [--] INPUT [OUTPUT]"
  echo
  echo "Arguments:"
  echo "    INPUT...  File path of image to intensify"
  echo "    OUTPUT...  File path of intensified image"
  echo
  echo "Options:"
  echo "    --count <frames>"
  echo "        Number of frames of shaking (default: 10)"
  echo "    --delta <pixels>"
  echo "        Maximum number of pixels to move while shaking (default: 4)"
  echo "    --delay <centiseconds>"
  echo "        Delay between frames (default: 5)"
  echo "    -h, --help"
  echo "        Print (this) help message"
}

errexit() {
  printf '%s\n' "$@" >&2
  exit 1
}

get_file_size() {
  # BSD stat and GNU stat are totally incompatible
  case "$OSTYPE" in
    darwin*|*bsd*)
      stat -f '%z' "$1"
      return
      ;;
    linux-gnu)
      ;;
    *)
      echo >&2 "Unknown OSTYPE: $OSTYPE"
      ;;
  esac

  stat --printf='%s' "$1"
}

input=
output=
declare -i count=10 # Number of frames of shaking
declare -i delta=4  # Max pixels to move while shaking
declare -i delay=5
while [ $# -gt 0 ]; do
  case $1 in
  --count)
    count=${2?missing operand ${1@Q}}
    shift 2
    ;;
  --delta)
    delta=${2?missing operand ${1@Q}}
    shift 2
    ;;
  --delay)
    delay=${2?missing operand ${1@Q}}
    shift 2
    ;;
  -h | --help)
    usage
    exit 0
    ;;
  --)
    shift
    break
    ;;
  -*) errexit "unknown option ${1@Q}" ;;
  *) break ;;
  esac
done

if [ $# -lt 1 ]; then
  usage
  exit 1
fi

input=${1?"Missing input operand"}

[[ -f $input ]] || errexit "no such file ${input@Q}"

cd -- "$(dirname -- "$input")"

filename=$(basename -- "$input")

output=${2:-"${filename%.*}-intensifies.gif"}

[[ $input != "$output" ]] || errexit "input and output paths must be different"

# Add 10% padding to width and height, then scale to 128x128
width=$(identify -format "%w" "$filename")
height=$(identify -format "%h" "$filename")
new_width=$((width + width / 10))
new_height=$((height + height / 10))
extended="${filename%.*}-extended.png"
frames=()
for i in $(seq $count); do
  frames+=("${filename%.*}-frame-${i}.gif")
done

trap 'rm -v -f "$extended" "${frames[@]}"' EXIT

mkdir -p "$(dirname "$output")"

echo "generating ${extended@Q}"
magick \
  "$filename" \
  -gravity center \
  -background none \
  -extent "${new_width}x${new_height}" \
  -geometry 128x128 \
  "$extended"

# Generate some shaky frames
n=0
while ((n < count)); do
  x=$((RANDOM % (delta * 2) - delta))
  y=$((RANDOM % (delta * 2) - delta))

  # Shake the image!

  frame=${frames[$n]}
  echo "generating ${frame@Q}"
  magick "$extended" \
    -page "$(printf '%+d%+d' "${x}" "${y}")" \
    -background none \
    -flatten \
    "${frame}"

  n=$((n + 1))
done

# Combine the frames into a GIF
echo "generating $output"
magick \
  -delay $delay \
  "${frames[@]}" \
  -background none \
  -set dispose Background \
  -loop 0 \
  "$output"

# Optimise if file is too big
if [[ $(get_file_size "$output") -ge 128000 ]]; then
  echo "optimizing file size: $output"
  magick "$output" \
    -fuzz 80% \
    -layers Optimize \
    "$output"
fi

echo "wrote $output"
