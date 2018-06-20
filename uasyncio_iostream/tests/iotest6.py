# iotest6.py Test fast_io PR

# Test is designed to quantify the difference between fast and normal I/O without
# recourse to electronic testgear.

# The MyIO class supports .readline() which updates a call counter and clears the
# .ready_read flag. This is set by a timer (emulating the arrival of data from
# some hardware device).
# The .dummy method emulates a relatively slow user coro which yields with a zero
# delay; the test runs 10 instances of this. Each instance updates a common call
# counter.
# The receiver coro awaits .readline continuously. With normal scheduling each is
# scheduled after the ten .dummy instances have run. With fast scheduling and a
# timer period <= 10ms readline and dummy alternate. If timer period is increased
# readline is sheduled progressively less frequently.

import io
import pyb
import utime
import uasyncio as asyncio
import micropython
micropython.alloc_emergency_exception_buf(100)

MP_STREAM_POLL_RD = const(1)
MP_STREAM_POLL_WR = const(4)
MP_STREAM_POLL = const(3)
MP_STREAM_ERROR = const(-1)

class MyIO(io.IOBase):
    def __init__(self, read=False, write=False):
        self.read_count = 0
        self.dummy_count = 0
        self.ready_rd = False
        pyb.Timer(4, freq = 100, callback = self.do_input)

    # Read callback: emulate asynchronous input from hardware.
    def do_input(self, t):
        self.ready_rd = True  # Data is ready to read

    def ioctl(self, req, arg):
        ret = MP_STREAM_ERROR
        if req == MP_STREAM_POLL:
            ret = 0
            if arg & MP_STREAM_POLL_RD:
                if self.ready_rd:
                    ret |= MP_STREAM_POLL_RD
        return ret

    def readline(self):
        self.read_count += 1
        self.ready_rd = False
        return b'a\n'

    async def dummy(self):
        while True:
            await asyncio.sleep(0)
            self.dummy_count += 1
            utime.sleep_ms(10)  # Emulate time consuming user code

    async def killer(self):
        print('Test runs for 5s')
        await asyncio.sleep(5)
        print('I/O count {} Dummy count {}'.format(self.read_count, self.dummy_count))

async def receiver(myior):
    sreader = asyncio.StreamReader(myior)
    while True:
        await sreader.readline()

def test(fast_io=False):
    loop = asyncio.get_event_loop(fast_io=fast_io)
    myior = MyIO()
    loop.create_task(receiver(myior))
    for _ in range(10):
        loop.create_task(myior.dummy())
    loop.run_until_complete(myior.killer())

print('Run test() to check normal I/O, test(True) for fast I/O')
