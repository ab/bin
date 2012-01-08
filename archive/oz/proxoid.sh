#!/bin/sh

set -e
ssh_config="$HOME/.ssh/config"

# disable proxy
disable() {
    gconftool -t string -s /system/proxy/mode "none"
    gconftool -t bool -s /system/http_proxy/use_http_proxy false
    sed -i -r --follow-symlinks 's/^  (ProxyCommand .+ # proxoid)$/  # \1/' "$ssh_config"
    echo 'All done.'
}

trap 'disable' EXIT
trap 'echo "Exiting on signal"' HUP INT TERM QUIT

set -x

adb forward tcp:8080 tcp:8080

# enable proxy
gconftool -t string -s /system/proxy/mode "manual"
gconftool -t bool -s /system/http_proxy/use_http_proxy true

# http settings
gconftool -t string -s /system/http_proxy/host "localhost"
gconftool -t int -s /system/http_proxy/port "8080"

# https settings
gconftool -t string -s /system/proxy/secure_host "localhost"
gconftool -t int -s /system/proxy/secure_port "8080"

# ssh settings
sed -i -r --follow-symlinks 's/^  # (ProxyCommand .+ # proxoid)$/  \1/' "$ssh_config"

read -p 'Proxy enabled. Press enter to exit. ' ans
