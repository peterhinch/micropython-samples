# ms_timer_test.py Test/demo program for MillisecTimer. Adapted for new uasyncio.

import uasyncio as asyncio
import utime
import ms_timer

async def timer_test(n, fast):
    timer = ms_timer.MillisecTimer(fast)
    while True:
        t = utime.ticks_ms()
        await timer(30)
        print('Task {} time {}ms'.format(n, utime.ticks_diff(utime.ticks_ms(), t)))
        await asyncio.sleep(0.5 + n/5)

async def foo():
    while True:
        await asyncio.sleep(0)
        utime.sleep_ms(10)  # Emulate slow processing


def main(fast=True):
    for _ in range(10):
        asyncio.create_task(foo())
    for n in range(3):
        asyncio.create_task(timer_test(n, fast))
    await asyncio.sleep(10)

def test(fast=True):
    asyncio.run(main(fast))

s = '''This test creates ten tasks each of which blocks for 10ms.
It also creates three tasks each of which runs a MillisecTimer for 30ms,
timing the period which elapses while it runs. With fast I/O scheduling
the elapsed time is ~30ms as expected. With normal scheduling it is
about 130ms because of competetion from the blocking coros.

Run test() to test fast I/O, test(False) to test normal I/O.

Test prints the task number followed by the actual elapsed time in ms.
Test runs for 10s.'''

print(s)
