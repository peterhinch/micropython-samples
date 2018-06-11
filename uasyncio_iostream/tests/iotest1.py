# iotest1.py Test PR #3836. User class write() performs unbuffered writing.

import io, pyb
import uasyncio as asyncio
import micropython
micropython.alloc_emergency_exception_buf(100)

MP_STREAM_POLL_RD = const(1)
MP_STREAM_POLL_WR = const(4)
MP_STREAM_POLL = const(3)
MP_STREAM_ERROR = const(-1)

def printbuf(this_io):
    print(bytes(this_io.wbuf[:this_io.wprint_len]).decode(), end='')

class MyIO(io.IOBase):
    def __init__(self):
        self.ready_rd = False
        self.ready_wr = False
        self.wbuf = bytearray(100)  # Write buffer
        self.wprint_len = 0
        self.widx = 0
        self.wch = b''
        self.rbuf = b'ready\n'  # Read buffer
        pyb.Timer(4, freq = 1, callback = self.do_input)
        pyb.Timer(5, freq = 10, callback = self.do_output)

    # Read callback: emulate asynchronous input from hardware.
    # Typically would put bytes into a ring buffer and set .ready_rd.
    def do_input(self, t):
        self.ready_rd = True  # Data is ready to read

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
            if arg & MP_STREAM_POLL_RD:
                if self.ready_rd:
                    ret |= MP_STREAM_POLL_RD
            if arg & MP_STREAM_POLL_WR:
                if not self.wch:
                    ret |= MP_STREAM_POLL_WR  # Ready if no char pending
        return ret

    def readline(self):
        self.ready_rd = False
        return self.rbuf

    def write(self, buf, off, sz):
        self.wch = buf[off]  # A real driver would trigger hardware to write a char
        return 1  # No. of bytes written. uasyncio waits on ioctl write ready

myio = MyIO()

async def receiver():
    sreader = asyncio.StreamReader(myio)
    while True:
        res = await sreader.readline()
        print('Received', res)

async def sender():
    swriter = asyncio.StreamWriter(myio, {})
    await asyncio.sleep(5)
    count = 0
    while True:
        count += 1
        tosend = 'Wrote Hello MyIO {}\n'.format(count)
        await swriter.awrite(tosend.encode('UTF8'))
        # Once this has occurred reading stops. ioctl keeps being called with arg == 0
        # which normally occurs once only after a read
        # IOWriteDone is never yielded: is this right?
        await asyncio.sleep(2)


loop = asyncio.get_event_loop()
loop.create_task(receiver())
loop.create_task(sender())
loop.run_forever()

