#!/bin/sh
set -eu

latency_bytes=10

input_dev=alsa_input.usb-Burr-Brown_from_TI_USB_Audio_CODEC-00-CODEC.iec958-stereo
output_dev=alsa_output.pci-0000_00_1b.0.analog-stereo

set -x

pacat -r --latency=$latency_bytes -d $input_dev \
    | pacat -p --latency=$latency_bytes -d $output_dev &
