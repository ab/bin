#!/usr/bin/env python3

import os
import sys


ALIASES = {
    ".": "source",
    "_c": "awk",
    "gg": "grep",
    "view": "vim",
    "open": "xdg-open",
    "py": "ipython",
    "per": "poetry",
    "be": "bundle",
    "wgetn": "wget",
}


REVERSE_ALIASES = {
    "git": [
        "g-",
        "ga",
        "gau",
        "gb",
        "gbl",
        "gbr",
        "gc",
        "gc-mtime",
        "gca",
        "gcam",
        "gcams",
        "gcas",
        "gcl",
        "gcm",
        "gcms",
        "gco",
        "gco-",
        "gcoh",
        "gcom",
        "gcs",
        "gcsempty",
        "gd",
        "gdc",
        "gdcw",
        "gdt",
        "gdw",
        "gf",
        "gfe",
        "gfep",
        "gfetch",
        "gg",
        "ggf",
        "ggp",
        "git-checkout-main",
        "git-commit-mtime",
        "git-config-email",
        "git-main-branch",
        "git_commit_s",
        "gl",
        "glf",
        "glg",
        "glgs",
        "glo",
        "gls",
        "glsf",
        "gmt",
        "gpl",
        "gplr",
        "gps",
        "gpsr",
        "gpsu",
        "gpull",
        "gpush",
        "gr",
        "grH",
        "grb",
        "grh",
        "grho",
        "grm",
        "grp",
        "grpH",
        "gru",
        "grv",
        "gs",
        "gsa",
        "gsd",
        "gsf",
        "gsh",
        "gshw",
        "gsi",
        "gsr",
        "gss",
        "gst",
        "gsu",
        "main",
        "master",
    ],
    "apt": [
        "ainstall",
        "aupdate",
        "aupgrade",
        "ashow",
        "asearch",
        "apt-get",
        "aptitude",
    ],
    "cd": ["cdg", "..", "...", "...."],
    "ls": ["ll", "l", "lla"],
    "vim": ["ge", "gse"],
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
