#!/usr/bin/env python3

import csv
import sys

from dataclasses import dataclass


@dataclass
class Span:
    id: str
    name: str
    parent_id: str
    start: float
    end: float
    depth: int | None = None

    @property
    def duration(self) -> float:
        return self.end - self.start

    @classmethod
    def from_dict(cls, data: dict[str, str]):
        return cls(
            id=data["span_id"],
            name=data["span_name"],
            parent_id=data["parent"],
            start=float(data["start"]),
            end=float(data["end"]),
        )


def main(filename: str, indent=2):
    expected_columns = ['span_id', 'span_name', 'parent', 'start', 'end']
    with open(filename, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
        assert reader.fieldnames, "No fields... empty file?"
        assert list(reader.fieldnames) == expected_columns, \
            f"Unexpected columns: {reader.fieldnames}"
        raw_spans = list(reader)

    raw_spans.sort(key=lambda x: float(x["start"]))

    spans: dict[str, Span] = {}
    for raw in raw_spans:
        s = Span.from_dict(raw)

        if s.parent_id:
            s.depth = spans[s.parent_id].depth + 1
        else:
            s.depth = 0

        spans[s.id] = s

    root = next(iter(spans.values()))
    beginning = root.start

    print("  ".join(["span", "start", "time", "gap", "span name"]))

    prev = None
    for s in spans.values():
        assert isinstance(s, Span)

        start_relative = s.start - beginning

        if prev:
            # gap is a measure of how much time is untracked between spans

            # if prev span is our parent, then measure gap from parent.start
            # else measure gap from prev.end
            if s.parent_id == prev.id:
                gap = s.start - prev.start
            else:
                gap = s.start - prev.end
        else:
            gap = 0

        use_color = sys.stdout.isatty()

        out = "  ".join([
            s.id,
            format_float(start_relative, color=False),
            format_float(s.duration, color=use_color),
            format_float(gap, color=use_color),
            s.name,
        ])
        print(" " * indent * s.depth + out)

        prev = s


def format_float(num: float, color: bool) -> str:
    out = f"{num:.3f}"
    if color:
        if num > 0.5:
            # red
            out = "\033[31;1m" + out + "\033[m"
        elif num > 0.1:
            # yellow
            out = "\033[33;1m" + out + "\033[m"

    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: shell_trace_report.py FILE.tsv", file=sys.stderr)
        sys.exit(1)

    main(sys.argv[1])
