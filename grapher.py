#!/usr/bin/env python
import curses
import optparse
import re
import sys
from subprocess import call, Popen, PIPE

def get_term_size():
    p = Popen(['tput', '-S'], stdin=PIPE, stdout=PIPE)
    out = p.communicate('lines\ncols\n')[0]
    return map(int, out.strip().split('\n'))

def graph(values, width=None, height=None, char='|'):
    if width is None or height is None:
        rows, cols = get_term_size()
        if width is None:
            width = cols
        if height is None:
            height = rows - 2
    
    # skip values when there are more than WIDTH columns. TODO average instead
    if len(values) > width:
        values = [values[i * len(values) // width] for i in range(width)]

    # get max for Y scale
    vmax = max(values)

    display = [list(' '*width) for i in range(height)]
    for c, v in enumerate(values):
        scaled = v * height // vmax
        for r in range(height - scaled, height):
            display[r][c] = char
    
    for row in display:
        print ''.join(row)

def graph_loop(*args, **kwargs):
    call('clear')
    graph(*args, **kwargs)

def curses_graph(stdscr, stream, width=None, height=None, char='|', scale=True):
    if width is None:
        width = stdscr.getmaxyx()[1]
    if height is None:
        height = stdscr.getmaxyx()[0]

    vmax = 0
    values = []
    while True:
        line = stream.readline()
        if not line:
            break
        try:
            v = int(line)
        except ValueError:
            continue
        values.append(v)
        if v > vmax:
            vmax = v

        # fit width as needed
        if len(values) > width:
            x = values.pop(0)
            if scale and x == vmax:
                # readjust Y scale if we popped off max value
                vmax = max(values)

        # main drawing loop
        stdscr.erase()
        for col, val in enumerate(values):
            scaled = val * height // vmax
            if scaled <= 0:
                continue
            stdscr.vline(height - scaled, col, char, scaled)
        stdscr.refresh()

if __name__ == '__main__':
    usage = 'usage: %prog [options] {FILENAME | -}'
    p = optparse.OptionParser(usage)
    p.add_option('-s', '--stream', dest='stream', action='store_true',
                 help='draw a streaming graph')
    (options, args) = p.parse_args()

    try:
        fname = args[0]
    except IndexError:
        p.print_help()
        sys.exit(2)

    if fname == '-':
        f = sys.stdin
    else:
        f = open(fname)

    try:
        if options.stream:
            # use curses for streaming graph output
            curses.wrapper(curses_graph, f)
        else:
            values = []
            for line in f:
                values.append(int(line))
            f.close()
            graph(values)
    except KeyboardInterrupt:
        print ''

