#!/usr/bin/env python
# A simple selecting echo server

import select
import socket
import sys

class EchoServ(object):
    def __init__(self, host, port, verbose=True):
        self.BACKLOG = 5
        self.SIZE = 1024
        self.verbose = verbose
        self.socks = {}
        self.running = False
        self.host = host
        self.port = port

    def info(self, *args):
        if self.verbose:
            for a in args:
                print a,
            print ''
    def debug(self, *args):
        if self.verbose > 1:
            for a in args:
                print a,
            print ''
    def debugdot(self):
        if self.verbose > 1:
            sys.stderr.write('.')
            sys.stderr.flush()

    def run(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen(self.BACKLOG)
        self.info('Listening on TCP', self.server.getsockname())

        self.socks = {}
        self.running = True
        while self.running:
            inputs = self.socks.keys() + [self.server]
            readready, writeready, exready = select.select(inputs, [], [])
            for s in readready:
                if s == self.server:
                    # accept new client from server socket
                    client, address = self.server.accept()
                    self.info('New connection from:', address)
                    self.socks[client] = address

                else:
                    # handle client sockets
                    try:
                       data = s.recv(self.SIZE)
                    except socket.error, e:
                        # error while reading
                        if e.errno == 104:
                            self.info('Conn reset by peer: ',
                                      self.socks[s])
                            s.close()
                            del self.socks[s]
                            continue
                        else:
                            raise

                    if data:
                        s.send(data)
                        self.debugdot()
                    else:
                        self.info('Client disconnected:', self.socks[s])
                        s.close()
                        del self.socks[s]
            for s in exready:
                self.info('Socket error on:', s)

    def shutdown(self):
        if not self.running:
            # no-op if server wasn't running
            return False
        self.running = False
        self.info('Shutting down')
        for s, addr in self.socks.iteritems():
            self.debug('Disconnecting', addr)
            s.close()

        self.debug('Closing listen socket')
        self.server.close()

if __name__ == '__main__':
    host = ''
    try:
        port = int(sys.argv[1])
    except (IndexError, ValueError):
        print 'echoserv.py PORT'
        sys.exit(2)

    e = EchoServ(host, port)

    try:
        e.run()
    except KeyboardInterrupt:
        print ''
        e.shutdown()
    except Exception, err:
        print 'Unhandled exception!'
        e.shutdown()
        raise

