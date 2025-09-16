#!/usr/bin/env python3
"""
usage: tls-get-server-cert.py HOST [PORT]

Get the TLS server certificate for HOST. Verify it, and print JSON info about
the certificate to stdout.

This is useful for certificate pinning or hardcoding HTTPS cert fingerprints.

For example:

    tls-get-server-cert.py accounts.google.com
{
  "host": "accounts.google.com",
  "port": 443,
  "success": true,
  "exception": null,
  "error": null,
  "digest_sha1": "9e3ff6d0b89dc0bdba37c713e5978fd8aacd4225",
  "digest_sha256": "3c1848935992b08c2c0b308a62fd5cfcb82308cbda061d9b2861417027566d96",
  "subject_alt_names": [
    "DNS:accounts.google.com",
    "DNS:*.partner.android.com"
  ],
  "issuer": "countryName=US/organizationName=Google Trust Services/commonName=WR2",
  "not_before": "Jul  7 08:35:56 2025 GMT",
  "not_after": "Sep 29 08:35:55 2025 GMT"
}
"""

import hashlib
import json
import socket
import ssl
import sys

from dataclasses import asdict, dataclass


@dataclass
class Result:
    host: str
    port: int
    success: bool
    exception: str | None = None
    error: str | None = None
    digest_sha1: str | None = None
    digest_sha256: str | None = None
    subject_alt_names: list[str] | None = None
    issuer: list[str] | None = None
    not_before: str | None = None
    not_after: str | None = None


def check_ssl_certificate(hostname: str, port: int = 443) -> Result:
    """
    Return a dict of info containing the certificate info and SHA1 and SHA256
    certificate digests.
    """

    data = Result(
        host=hostname,
        port=port,
        success=False,
    )

    cert = None
    info = None

    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert(binary_form=True)
                info = ssock.getpeercert()

    except Exception as e:
        if e.__class__.__module__:
            data.exception = e.__class__.__module__ + "." +  e.__class__.__name__
        else:
            data.exception = e.__class__.__name__
        data.error = str(e)
        return data

    data.digest_sha1 = hashlib.sha1(cert).hexdigest()
    data.digest_sha256 = hashlib.sha256(cert).hexdigest()

    data.subject_alt_names = [':'.join(parts) for parts in info['subjectAltName']]
    data.not_before = info['notBefore']
    data.not_after = info['notAfter']
    data.issuer = '/'.join(format_subject(i) for i in info['issuer'])

    data.success = True

    return data


def format_subject(subj_list) -> str:
    return ', '.join('='.join(parts) for parts in subj_list)


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(__doc__.strip())
        sys.exit(1)

    hostname = sys.argv[1]

    port = 443
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])

    res = check_ssl_certificate(hostname=hostname, port=port)

    json.dump(asdict(res), sys.stdout, indent=2)
    sys.stdout.write("\n")

    if res.success:
        sys.exit()
    else:
        sys.exit(2)
