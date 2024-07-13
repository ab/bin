#!/usr/bin/env python3

import os
import sys


ALIASES = {
    "ll": "ls",
    "gg": "grep",
    "view": "vim",
    "open": "xdg-open",
    "py": "ipython",
    "per": "poetry",
    "be": "bundle",
}


REVERSE_ALIASES = {
    "git": [
        "gs", "gls", "gd", "g", "gps", "gpl", "gc", "gca", "gcam", "gb", "git",
        "gr", "grv", "gsh", "gl", "gf", "gfe", "gst",
    ],
    "apt": ["aupdate", "aupgrade", "ashow", "asearch", "apt-get", "aptitude"],
    "cd": ["cdg", "..", "..."]
}


for target, sources in REVERSE_ALIASES.items():
    for source in sources:
        ALIASES[source] = target


def main(filenames: list[str]):
    if not filenames:
        raise ValueError("Must pass filenames")

    lines = []
    for filename in filenames:
        lines += open(filename).readlines()

    counts = {}

    for line in lines:
        cmd = get_command(line)

        counts[cmd] = counts.get(cmd, 0) + 1

    ordered = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    for name, count in ordered:
        print(str(count).rjust(6) + "\t" + name)


def get_command(line: str) -> str:
    parts = line.strip().split(" ")

    # strip out env var assignment
    while "=" in parts[0]:
        parts = parts[1:]
        if len(parts) == 0:
            return ""

    command = parts[0]
    if command.startswith("#"):
        return ""

    command = os.path.basename(command)

    if command in ALIASES:
        return ALIASES[command]

    return command


if __name__ == "__main__":
    main(sys.argv[1:])
