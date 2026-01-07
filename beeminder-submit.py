#!/usr/bin/env python3
"""
%prog [options] GOAL VALUE

Submit a new data point to Beeminder via an HTTP webhook.

GOAL: slug of the beeminder goal
VALUE: float value to submit

The webhook is configured in a config file under the key "webhook_url".

It's unclear whether having the IFTTT/make.com webhook intermediary really adds
any value. In theory this limits the number of places we have to keep the fully
privileged Beeminder API key.

Config file format:

    {
      "webhook_url": "https://hook.us2.make.com/...",
      # optional headers
      "http_headers": {
        "x-make-apikey": "<secret>"
      }
    }

For example:

    %prog eat-pie 3.14

"""

import sys
import os
import socket
import json
import optparse
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, Optional


# Default config path
DEFAULT_CONFIG: str = os.path.expanduser("~/.config/beeminder-submit.json")


def get_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r') as f:
        return json.load(f)


def submit_datapoint(
    goal: str,
    value: float,
    config_path: str,
    comment: Optional[str] = None,
) -> int:
    """
    Post a data point to a URL (IFTTT/make.com) for submission to Beeminder.

    Return HTTP status code on success.
    """

    config: Dict[str, Any] = get_config(config_path)
    try:
        url: str = config['webhook_url']
    except KeyError:
        sys.stderr.write("Missing key in config file\n")
        raise

    headers: Dict[str, str] = config.get("http_headers", {})

    if comment is None:
        # Metadata for the comment
        script_name = os.path.basename(__file__)
        hostname = socket.gethostname()
        current_time = datetime.now().strftime("%H:%M")
        comment = (
            f"Source: {script_name} | Host: {hostname} | Time: {current_time}"
        )

    # Prepare JSON payload
    payload: Dict[str, Any] = {
        "beeminder_datapoint": {
            "goal": goal,
            "value": value,
            "comment": comment,
        }
    }

    json_data: bytes = json.dumps(payload).encode('utf-8')

    req: urllib.request.Request = urllib.request.Request(
        url, data=json_data, method='POST'
    )
    req.add_header('Content-Type', 'application/json')
    for k, v in headers.items():
        req.add_header(k, v)

    with urllib.request.urlopen(req) as response:
        print("Response: " + response.read().decode("utf-8"))
        return response.getcode()


if __name__ == "__main__":
    parser = optparse.OptionParser(usage=__doc__.strip())

    parser.add_option(
        "--config",
        dest="config_path",
        default=DEFAULT_CONFIG,
        help="Path to config JSON [default: %default]"
    )

    parser.add_option(
        "-c", "--comment",
        dest="comment",
        help="Override default data point comment",
    )

    options, args = parser.parse_args()

    # Strict check for exactly 2 positional arguments
    if len(args) != 2:
        parser.print_help()
        sys.exit(1)

    goal_name: str = args[0]
    try:
        value: float = float(args[1])
    except ValueError:
        parser.error(f"Value must be a number, got {args[1]!r}")

    try:
        status: int = submit_datapoint(
            goal=goal_name,
            value=value,
            config_path=options.config_path,
            comment=options.comment,
        )
        print(f"Success: Sent {value} to '{goal_name}' (Status: {status})")
    except Exception as e:
        print(f"{e.__class__.__name__}: {e}", file=sys.stderr)
        sys.exit(1)
