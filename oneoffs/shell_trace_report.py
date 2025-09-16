#!/usr/bin/env python3

import json
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
            start=data["start"],
            end=data["end"],
        )

def main(filename: str, indent=2):
    with open(filename, 'r') as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert isinstance(data["spans"], list)
    assert data["spans"][-1] == {}  # last span is empty for trailing comma

    raw_spans = data["spans"][:-1]
    raw_spans.sort(key=lambda x: x["start"])

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
    main(sys.argv[1])
