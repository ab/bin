#!/bin/sh

set -u

if [ $# -ne 2 ]; then
    cat >&2 <<EOM
usage: $(basename "$0") KEY NEW_KEY

Convert an SSH private key from the traditional SSH private key format (which
uses only a single round of MD5 to derive the encryption key) with the PKCS8
(RFC 5208) format keys where the encryption key is derived using 2048 rounds of
PBKDF2 (PKCS5 / RFC 2898).

You can use \`openssl asn1parse\` to dump the resulting NEW_KEY file. The
OpenSSH suite should have no trouble reading it.

See also: ssh(1), ssh-keygen(1), asn1parse(1ssl), pkcs8(1ssl)

http://martin.kleppmann.com/2013/05/24/improving-security-of-ssh-private-keys.html
EOM
    exit 1
fi

input="$1"
output="$2"

if [ "$1" = "$2" ]; then
    echo fail
    exit 2
fi

set -x

openssl pkcs8 -topk8 -v2 aes-256-cbc -in "$input" -out "$output" \
    && chmod 400 "$output"
