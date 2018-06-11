# iotest3.py Test PR #3836. User class write() performs unbuffered writing.

# This test was to demonstrate the workround to the original issue by having
# separate read and write classes.
# With modified moduselect.c and uasyncio.__init__.py the test is probably
# irrelevant.

import io, pyb
import uasyncio as asyncio
import micropython
micropython.alloc_emergency_exception_buf(100)

MP_STREAM_POLL_RD = const(1)
MP_STREAM_POLL_WR = const(4)
MP_STREAM_POLL = const(3)
MP_STREAM_ERROR = const(-1)

class MyIOR(io.IOBase):
    def __init__(self):
        self.ready_rd = False
        self.rbuf = b'ready\n'  # Read buffer
        pyb.Timer(4, freq = 1, callback = self.do_input)

    # Read callback: emulate asynchronous input from hardware.
    # Typically would put bytes into a ring buffer and set .ready_rd.
    def do_input(self, t):
        self.ready_rd = True  # Data is ready to read

    def ioctl(self, req, arg):  # see ports/stm32/uart.c
        ret = MP_STREAM_ERROR
        if req == MP_STREAM_POLL:
            ret = 0
            if not arg:
                print('ioctl arg 0')
            if arg & MP_STREAM_POLL_RD:
                if self.ready_rd:
                    ret |= MP_STREAM_POLL_RD
        return ret

    def readline(self):
        self.ready_rd = False
        return self.rbuf

# MyIOW emulates a write-only device which can only handle one character at a
# time. The write() method is called by uasyncio. A real driver would cause the
# hardware to write a character. By setting .wch it causes the ioctl to report
# a not ready status.
# Some time later an asynchronous event occurs, indicating that the hardware
# has written a character and is ready for another. In this demo this is done
# by the timer callback do_output(), which clears .wch so that ioctl returns
# a ready status. For the demo it stores the characters in .wbuf for printing.

def printbuf(this_io):
    print(bytes(this_io.wbuf[:this_io.wprint_len]).decode(), end='')

class MyIOW(io.IOBase):
    def __init__(self):
        self.wbuf = bytearray(20)  # Buffer for printing
        self.wprint_len = 0
        self.widx = 0
        self.wch = b''
        wtim = pyb.Timer(5, freq = 10, callback = self.do_output)

    # Write timer callback. Emulate hardware: if there's data in the buffer
    # write some or all of it
    def do_output(self, t):
        if self.wch:
            self.wbuf[self.widx] = self.wch
            self.widx += 1
            if self.wch == ord('\n'):
                self.wprint_len = self.widx  # Save for schedule
                micropython.schedule(printbuf, self)
                self.widx = 0
        self.wch = b''

    def ioctl(self, req, arg):  # see ports/stm32/uart.c
        ret = MP_STREAM_ERROR
        if req == MP_STREAM_POLL:
            ret = 0
            if arg & MP_STREAM_POLL_WR:
                if not self.wch:
                    ret |= MP_STREAM_POLL_WR  # Ready if no char pending
        return ret

    def write(self, buf, off, sz):
        self.wch = buf[off]  # A real driver would trigger hardware to write a char
        return 1  # No. of bytes written. uasyncio waits on ioctl write ready

myior = MyIOR()
myiow = MyIOW()

async def receiver():
    sreader = asyncio.StreamReader(myior)
    while True:
        res = await sreader.readline()
        print('Received', res)

async def sender():
    swriter = asyncio.StreamWriter(myiow, {})
    count = 0
    while True:
        count += 1
        tosend = 'Wrote Hello MyIO {}\n'.format(count)
        await swriter.awrite(tosend.encode('UTF8'))
        await asyncio.sleep(2)

loop = asyncio.get_event_loop()
loop.create_task(receiver())
loop.create_task(sender())
loop.run_forever()
