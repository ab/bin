#!/usr/bin/env python3
import curses
import optparse
import os
import sys
from subprocess import call

VERSION = '0.1'

def get_term_size():
    """
    Return the current terminal size as a tuple:
        (lines, columns)
    """
    size = os.get_terminal_size()
    return (size.lines, size.columns)

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
        print(''.join(row))

def graph_loop(*args, **kwargs):
    call('clear')
    graph(*args, **kwargs)

def curses_graph(stdscr, stream, width=None, height=None, char='|',
                 scale=True, strict_input=False):
    if width is None:
        width = stdscr.getmaxyx()[1]
    if height is None:
        height = stdscr.getmaxyx()[0]

    # don't display a flashing cursor, don't block waiting for keyboard input
    curses.curs_set(0)
    stdscr.nodelay(1)

    vmax = 0
    values = []
    while True:
        line = stream.readline()
        if not line:
            break
        try:
            v = int(line)
        except ValueError:
            try:
                v = float(line)
            except ValueError:
                if strict_input:
                    raise
                else:
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

        # label max value
        stdscr.addstr(0, 0, str(vmax))

        stdscr.refresh()

        # check for keyboard input, allow pausing (NB: nodelay enabled above)
        # also note that this will NOT work when input is piped to stdin
        c = stdscr.getch()
        if c != -1:
            stdscr.refresh()
            stdscr.nodelay(0)
            stdscr.addstr(1, 0, "[PAUSED]")
            stdscr.getch()  # unpause on any keypress
            stdscr.nodelay(1)
        

if __name__ == '__main__':
    usage = 'usage: %prog [options] {FILENAME | -}'
    p = optparse.OptionParser(usage)
    p.add_option('-s', '--stream', dest='stream', action='store_true',
                 help='draw a streaming graph')
    p.add_option('-e', '--error-mode', dest='strict_input', action='store_true',
                 help='raise an error on invalid input data')
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

    if options.stream:
        # use curses for streaming graph output
        try:
            curses.wrapper(curses_graph, f, strict_input=options.strict_input)
        except KeyboardInterrupt:
            print('^C',)
    else:
        values = []
        for line in f:
            try:
                v = int(line)
            except ValueError:
                try:
                    v = float(line)
                except ValueError:
                    if options.strict_input:
                        raise
                    else:
                        continue
            values.append(v)

        f.close()
        graph(values)

