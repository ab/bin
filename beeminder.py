#!/usr/bin/env python
import sys
from datetime import datetime

def parse_date(line):
    prefix = '%Y-%m!'
    if len(line.split(' ', 2)) > 2:
        one, two, comment = line.split(' ', 2)
        time_part = one + ' ' + two
    else:
        comment = None
        time_part = line

    time_part = datetime.now().strftime(prefix) + time_part

    fmt = prefix + '%d %H:%M'
    try:
        return datetime.strptime(time_part, fmt), comment
    except ValueError:
        sys.stderr.write("Failed to parse %r" % line)
        raise

if sys.stdin.isatty():
    sys.stderr.write('format: day hour:min [comment]\n')

data = []
while True:
    try:
        line = sys.stdin.readline().strip()
    except EOFError:
        break
    if not line:
        break

    date, comment = parse_date(line)
    hours = date.hour + date.minute / 60.0

    processed_input = date.strftime('%F %R')
    if comment:
        processed_input += ' ' + comment
    data.append((date.day, hours, processed_input))

for row in data:
    print '%s %f "%s"' % row
