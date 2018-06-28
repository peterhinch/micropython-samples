# iotest7.py Test fast_io PR
# https://github.com/micropython/micropython-lib/pull/287

# Test the case where runq is empty

# The MyIO class supports .readline() which updates a call counter and clears the
# .ready_rd flag. This is set by a timer (emulating the arrival of data from
# some hardware device).


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
            await asyncio.sleep_ms(50)
            self.dummy_count += 1

    async def killer(self):
        print('Test runs for 5s')
        await asyncio.sleep(5)
        print('I/O count {} Dummy count {}'.format(self.read_count, self.dummy_count))

async def receiver(myior):
    sreader = asyncio.StreamReader(myior)
    while True:
        await sreader.readline()

def test(fast_io=False):
    loop = asyncio.get_event_loop(ioq_len = 6 if fast_io else 0)
    myior = MyIO()
    loop.create_task(receiver(myior))
    loop.create_task(myior.dummy())
    loop.run_until_complete(myior.killer())

print('Test case of empty runq: the fast_io option has no effect.')
print('I/O and dummy run at expected rates (around 500 and 99 counts respectively.')
print('Run test() to check normal I/O, test(True) for fast I/O')
