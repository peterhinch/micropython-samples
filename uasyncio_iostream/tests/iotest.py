# iotest.py Test PR #3836 timing using GPIO pins.

import io, pyb
import uasyncio as asyncio
import micropython
micropython.alloc_emergency_exception_buf(100)

MP_STREAM_POLL = const(3)
MP_STREAM_POLL_RD = const(1)

y1 = pyb.Pin('Y1', pyb.Pin.OUT)

class MyIO(io.IOBase):
    def __init__(self):
        self.ready = False
        self.count = 0
        tim = pyb.Timer(4)
        tim.init(freq=1)
        tim.callback(self.setready)
        
    def ioctl(self, req, arg):
        if req == MP_STREAM_POLL and (arg & MP_STREAM_POLL_RD):
            state = pyb.disable_irq()
            r = self.ready
            self.ready = False
            pyb.enable_irq(state)
            return r
        return 0

    def readline(self):
        y1.value(0)
        return '{}\n'.format(self.count)

    def setready(self, t):
        self.count += 1
        y1.value(1)
        self.ready = True

myio = MyIO()

async def foo(p):
    print('start foo', p)
    pin = pyb.Pin(p, pyb.Pin.OUT)
    while True:
        pin.value(1)
        await asyncio.sleep(0)
        pin.value(0)
        await asyncio.sleep(0)

async def receiver():
    last = None
    nmissed = 0
    sreader = asyncio.StreamReader(myio)
    while True:
        res = await sreader.readline()
        print('Recieved {} Missed {}'.format(res, nmissed))
        ires = int(res)
        if last is not None:
            if last != ires -1:
                print('Missed {}'.format(ires - 1))
                nmissed += 1
        last = ires

loop = asyncio.get_event_loop()
loop.create_task(receiver())
loop.create_task(foo('Y2'))
loop.create_task(foo('Y3'))
loop.run_forever()

