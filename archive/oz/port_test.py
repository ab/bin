#!/usr/bin/env python
import errno
import socket
import sys

def listen_range(start, end):
    sockets = []
    for i in range(start, end + 1):
        try:
            # create socket, allow multi-binding
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # bind to port
            s.bind(('', i))
        except socket.error, e:
            print 'FAIL:', i,
            if e.args[0] in [errno.EACCES, errno.EADDRINUSE]:
                # we can continue on these errors
                print '--', e.args[1]
            elif e.args[0] in [errno.EMFILE]:
                # we should exit on these errors
                print '--', e.args[1]
                return e.args[0]
            else:
                raise

        # listen for connections and append to socket list
        s.listen(3)
        sockets.append(s)

    raw_input('Sockets opened. Press enter to close down...')

    for s in sockets:
        s.close()
    print 'Closed all sockets.'

if __name__ == '__main__':
    try:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    except (IndexError, ValueError):
        sys.stderr.write('Usage: port_test.py START_PORT END_PORT\n')
        sys.stderr.write('Open listening sockets on a range of TCP ports.\n')
        sys.exit(2)
    
    sys.exit(listen_range(start, end))
