# test_fast_scheduling.py Test fast_io PR
# https://github.com/micropython/micropython-lib/pull/287

# Test is designed to quantify the difference between fast and normal I/O without
# recourse to electronic testgear. Run on Pyboard.

# The MyIO class supports .readline() which updates a call counter and clears the
# .ready_rd flag. This is set by a timer (emulating the arrival of data from
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
    def __init__(self):
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

async def receiver(myior, fast):
    sreader = asyncio.StreamReader(myior)
    if fast:
        sreader.priority()
    while True:
        await sreader.readline()

def test(fast=False):
    loop = asyncio.get_event_loop()
    myior = MyIO()
    loop.create_task(receiver(myior, fast))
    for _ in range(10):
        loop.create_task(myior.dummy())
    loop.run_until_complete(myior.killer())

print('Test case of I/O competing with zero delay tasks.')
print('fast False, uasyncio V2: approx I/O count 25, dummy count 510.')
print('fast False, new uasyncio: I/O count 46, dummy 509.')
print('fast True, new uasyncio: approx I/O count 509, dummy count 509.')
print('Run test() to check I/O performance at normal priority.')
print('Run test(True) to check I/O performance at high priority.')
