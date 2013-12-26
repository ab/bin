#!/usr/bin/env python
import sys
from datetime import datetime

def parse_date(line):
    prefix = '%Y-%m!'
    line = datetime.now().strftime(prefix) + line
    fmt = prefix + '%d %H:%M'
    return datetime.strptime(line, fmt)

data = []
while True:
    try:
        line = raw_input('day hour:min -- ').strip()
    except EOFError:
        print ''
        break

    if not line:
        break

    date = parse_date(line)
    hours = date.hour + date.minute / 60.0
    data.append((date.day, hours, date.strftime('%F %R')))

for row in data:
    sys.stderr.write('%s %f "%s"\n' % row)
