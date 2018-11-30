# client_w.py Demo of a resilient asynchronous full-duplex ESP8266 client

# Released under the MIT licence.
# Copyright (C) Peter Hinch 2018

import usocket as socket
import uasyncio as asyncio
import ujson
import network
import utime
from machine import Pin
import primitives as asyn  # Stripped-down asyn.py
# Get local config. ID is string of form '1\n'
from client_id import MY_ID, PORT, SERVER


class Client():
    def __init__(self, timeout, loop):
        self.timeout = timeout
        self.led = Pin(2, Pin.OUT, value = 1)
        self._sta_if = network.WLAN(network.STA_IF)
        self._sta_if.active(True)
        self.server = socket.getaddrinfo(SERVER, PORT)[0][-1]  # server read
        self.evfail = asyn.Event(100)
        self.lock = asyn.Lock(100)  # 100ms pause
        self.connects = 0  # Connect count
        self.sock = None
        loop.create_task(self._run(loop))

    # Make an attempt to connect to WiFi. May not succeed.
    async def _connect(self, s):
        print('Connecting to WiFi')
        s.active(True)
        s.connect()  # ESP8266 remembers connection.
        # Break out on fail or success.
        while s.status() == network.STAT_CONNECTING:
            await asyncio.sleep(1)
        t = utime.ticks_ms()
        print('Checking WiFi stability for {}ms'.format(2 * self.timeout))
        # Timeout ensures stable WiFi and forces minimum outage duration
        while s.isconnected() and utime.ticks_diff(utime.ticks_ms(), t) < 2 * self.timeout:
            await asyncio.sleep(1)

    async def _run(self, loop):
        s = self._sta_if
        while True:
            while not s.isconnected():  # Try until stable for 2*server timeout
                await self._connect(s)
            print('WiFi OK')
            self.sock = socket.socket()
            try:
                self.sock.connect(self.server)
                self.sock.setblocking(False)
                await self.send(self.sock, MY_ID)  # Can throw OSError
            except OSError:
                pass
            else:
                self.evfail.clear()
                loop.create_task(asyn.Cancellable(self.reader)())
                loop.create_task(asyn.Cancellable(self.writer, loop)())
                loop.create_task(asyn.Cancellable(self._keepalive)())
                await self.evfail  # Pause until something goes wrong
                await asyn.Cancellable.cancel_all()
                self.close()  # Close sockets
                print('Fail detected. Coros stopped, disconnecting.')
            s.disconnect()
            await asyncio.sleep(1)
            while s.isconnected():
                await asyncio.sleep(1)

    @asyn.cancellable
    async def reader(self):
        c = self.connects  # Count and transmit successful connects
        try:
            while True:
                r = await self.readline()  # OSError on fail
                if c == self.connects:  # If read succeeded
                    self.connects += 1  # update connect count
                d = ujson.loads(r)
                print('Got data', d)
        except OSError:
            self.evfail.set()

    @asyn.cancellable
    async def writer(self, loop):
        data = [0, 0]
        try:
            while True:
                data[0] = self.connects  # Send connection count
                async with self.lock:
                    await self.send(self.sock, '{}\n'.format(ujson.dumps(data)))
                print('Sent data', data)
                data[1] += 1  # Packet counter
                await asyncio.sleep(5)
        except OSError:
            self.evfail.set()

    @asyn.cancellable
    async def _keepalive(self):
        tim = self.timeout * 2 // 3  # Ensure  >= 1 keepalives in server t/o
        try:
            while True:
                await asyncio.sleep_ms(tim)
                async with self.lock:
                    await self.send(self.sock, '\n')
        except OSError:
            self.evfail.set()

    # Read a line from nonblocking socket: reads can return partial data which
    # are joined into a line. Blank lines are keepalive packets which reset
    # the timeout: readline() pauses until a complete line has been received.
    async def readline(self):
        line = b''
        start = utime.ticks_ms()
        while True:
            if line.endswith(b'\n'):
                if len(line) > 1:
                    return line
                line = b''
                start = utime.ticks_ms()  # Blank line is keepalive
                self.led(not self.led())
            await asyncio.sleep_ms(100)  # nonzero wait seems empirically necessary
            d = self.sock.readline()
            if d == b'':
                raise OSError
            if d is not None:
                line = b''.join((line, d))
            if utime.ticks_diff(utime.ticks_ms(), start) > self.timeout:
                raise OSError
 
    async def send(self, s, d):  # Write a line to either socket.
        start = utime.ticks_ms()
        while len(d):
            ns = s.send(d)  # OSError if client fails
            d = d[ns:]  # Possible partial write
            await asyncio.sleep_ms(100)
            if utime.ticks_diff(utime.ticks_ms(), start) > self.timeout:
                raise OSError

    def close(self):
        print('Closing sockets.')
        if isinstance(self.sock, socket.socket):
            self.sock.close()


loop = asyncio.get_event_loop()
client = Client(1500, loop)  # Server timeout set by server side app: 1.5s
try:
    loop.run_forever()
finally:
    client.close()  # Close sockets in case of ctrl-C or bug
