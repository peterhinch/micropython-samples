# server.py Minimal server.

# Released under the MIT licence.
# Copyright (C) Peter Hinch 2018

# Maintains bidirectional full-duplex links between server applications and
# multiple WiFi connected clients. Each application instance connects to its
# designated client. Connections areresilient and recover from outages of WiFi
# and of the connected endpoint.
# This server and the server applications are assumed to reside on a device
# with a wired interface.

# Run under MicroPython Unix build.

import usocket as socket
import uasyncio as asyncio
import utime
import primitives as asyn
from client_id import PORT

# Global list of open sockets. Enables application to close any open sockets in
# the event of error.
socks = []

# Read a line from a nonblocking socket. Nonblocking reads and writes can
# return partial data.
# Timeout: client is deemed dead if this period elapses without receiving data.
# This seems to be the only way to detect a WiFi failure, where the client does
# not get the chance explicitly to close the sockets.
# Note: on WiFi connected devices sleep_ms(0) produced unreliable results.
async def readline(s, timeout):
    line = b''
    start = utime.ticks_ms()
    while True:
        if line.endswith(b'\n'):
            if len(line) > 1:
                return line
            line = b''
            start = utime.ticks_ms()  # A blank line is just a  keepalive
        await asyncio.sleep_ms(100)  # See note above
        d = s.readline()
        if d == b'':
            raise OSError
        if d is not None:
            line = b''.join((line, d))
        if utime.ticks_diff(utime.ticks_ms(), start) > timeout:
            raise OSError

async def send(s, d, timeout):
    start = utime.ticks_ms()
    while len(d):
        ns = s.send(d)  # OSError if client fails
        d = d[ns:]
        await asyncio.sleep_ms(100)  # See note above
        if utime.ticks_diff(utime.ticks_ms(), start) > timeout:
            raise OSError

# Return the connection for a client if it is connected (else None)
def client_conn(client_id):
    try:
        c = Connection.conns[client_id]
    except KeyError:
        return 
    if c.ok():
        return c

# API: application calls server.run()
# Not using uasyncio.start_server because of https://github.com/micropython/micropython/issues/4290
async def run(timeout, nconns=10, verbose=False):
    addr = socket.getaddrinfo('0.0.0.0', PORT, 0, socket.SOCK_STREAM)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socks.append(s)
    s.bind(addr)
    s.listen(nconns)
    verbose and print('Awaiting connection.')
    while True:
        yield asyncio.IORead(s)  # Register socket for polling
        conn, addr = s.accept()
        conn.setblocking(False)
        try:
            idstr = await readline(conn, timeout)
            verbose and print('Got connection from client', idstr)
            socks.append(conn)
            Connection.go(int(idstr), timeout, verbose, conn)
        except OSError:
            if conn is not None:
                conn.close()

# A Connection persists even if client dies (minimise object creation).
# If client dies Connection is closed: .close() flags this state by closing its
# socket and setting .conn to None (.ok() == False).
class Connection():
    conns = {}  # index: client_id. value: Connection instance
    @classmethod
    def go(cls, client_id, timeout, verbose, conn):
        if client_id not in cls.conns:  # New client: instantiate Connection
            Connection(client_id, timeout, verbose)
        cls.conns[client_id].conn = conn
            
    def __init__(self, client_id, timeout, verbose):
        self.client_id = client_id
        self.timeout = timeout
        self.verbose = verbose
        Connection.conns[client_id] = self
        # Startup timeout: cancel startup if both sockets not created in time
        self.lock = asyn.Lock(100)
        self.conn = None  # Socket
        loop = asyncio.get_event_loop()
        loop.create_task(self._keepalive())

    def ok(self):
        return self.conn is not None

    async def _keepalive(self):
        to = self.timeout * 2 // 3
        while True:
            await self.write('\n')
            await asyncio.sleep_ms(to)

    async def readline(self):
        while True:
            if self.verbose and not self.ok():
                print('Reader Client:', self.client_id, 'awaiting OK status')
            while not self.ok():
                await asyncio.sleep_ms(100)
            self.verbose and print('Reader Client:', self.client_id, 'OK')
            try:
                line = await readline(self.conn, self.timeout)
                return line
            except (OSError, AttributeError):  # AttributeError if ok status lost while waiting for lock
                self.verbose and print('Read client disconnected: closing connection.')
                self.close()

    async def write(self, buf):
        while True:
            if self.verbose and not self.ok():
                print('Writer Client:', self.client_id, 'awaiting OK status')
            while not self.ok():
                await asyncio.sleep_ms(100)
            self.verbose and print('Writer Client:', self.client_id, 'OK')
            try:
                async with self.lock:  # >1 writing task?
                    await send(self.conn, buf, self.timeout)  # OSError on fail
                return
            except (OSError, AttributeError):
                self.verbose and print('Write client disconnected: closing connection.')
                self.close()

    def close(self):
        if self.conn is not None:
            if self.conn in socks:
                socks.remove(self.conn)
            self.conn.close()
            self.conn = None
