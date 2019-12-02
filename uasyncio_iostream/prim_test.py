# prim_test.py Test/demo of the 'micro' synchronisation primitives
# for the new uasyncio

# The MIT License (MIT)
#
# Copyright (c) 2017-2019 Peter Hinch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

try:
    import asyncio
except ImportError:
    # Specific imports under MicroPython to conserve RAM
    import uasyncio as asyncio
    import uasyncio.lock
    import uasyncio.event
    import uasyncio.semaphore
    import uasyncio.condition
    import uasyncio.queue
    from uasyncio.barrier import Barrier  # MicroPython optimised
else:
    from primitives.barrier import Barrier  # CPython generic
from primitives.message import Message  # Portable



def print_tests():
    st = '''Available functions:
print_tests()  Print this list.
ack_test()  Test event acknowledge and Message class.
message_test() Test Message class.
event_test()  Test Event and Lock objects.
barrier_test()  Test the Barrier class.
semaphore_test(bounded=False)  Test Semaphore or BoundedSemaphore.
condition_test()  Test the Condition class.
queue_test()  Test the  Queue class

Recommended to issue ctrl-D after running each test.
'''
    print('\x1b[32m')
    print(st)
    print('\x1b[39m')

print_tests()

def printexp(exp, runtime=0):
    print('Expected output:')
    print('\x1b[32m')
    print(exp)
    print('\x1b[39m')
    if runtime:
        print('Running (runtime = {}s):'.format(runtime))
    else:
        print('Running (runtime < 1s):')

# ************ Test Message class ************
# Demo use of acknowledge event

async def event_wait(message, ack_event, n):
    await message
    print('Eventwait {} got message with value {}'.format(n, message.value()))
    ack_event.set()

async def run_ack():
    message = Message()
    ack1 = asyncio.Event()
    ack2 = asyncio.Event()
    count = 0
    while True:
        asyncio.create_task(event_wait(message, ack1, 1))
        asyncio.create_task(event_wait(message, ack2, 2))
        message.set(count)
        count += 1
        print('message was set')
        await ack1.wait()
        ack1.clear()
        print('Cleared ack1')
        await ack2.wait()
        ack2.clear()
        print('Cleared ack2')
        message.clear()
        print('Cleared message')
        await asyncio.sleep(1)

async def ack_coro(delay):
    asyncio.create_task(run_ack())
    await asyncio.sleep(delay)
    print("I've seen attack ships burn on the shoulder of Orion...")
    print("Time to die...")

def ack_test():
    printexp('''Running (runtime = 10s):
message was set
Eventwait 1 got message with value 0
Eventwait 2 got message with value 0
Cleared ack1
Cleared ack2
Cleared message
message was set
Eventwait 1 got message with value 1
Eventwait 2 got message with value 1
Cleared ack1
Cleared ack2
Cleared message
message was set

... text omitted ...

Eventwait 1 got message with value 9
Eventwait 2 got message with value 9
Cleared ack1
Cleared ack2
Cleared message
I've seen attack ships burn on the shoulder of Orion...
Time to die...
''', 10)
    asyncio.get_event_loop().run_until_complete(ack_coro(10))

# ************ Test Message class ************

async def wait_message(message):
    print('Waiting for message')
    msg = await message
    message.clear()
    print('Got message {}'.format(msg))

async def run_message_test():
    message = Message()
    asyncio.create_task(wait_message(message))
    await asyncio.sleep(1)
    message.set('Hello world')
    await asyncio.sleep(1)

def message_test():
    printexp('''Running (runtime = 2s):
Waiting for message
Got message Hello world
''', 2)
    asyncio.get_event_loop().run_until_complete(run_message_test())

# ************ Test Lock and Event classes ************

async def run_lock(n, lock):
    print('run_lock {} waiting for lock'.format(n))
    await lock.acquire()
    print('run_lock {} acquired lock'.format(n))
    await asyncio.sleep(1)  # Delay to demo other coros waiting for lock
    lock.release()
    print('run_lock {} released lock'.format(n))

async def eventset(event):
    print('Waiting 5 secs before setting event')
    await asyncio.sleep(5)
    event.set()
    print('event was set')

async def eventwait(event):
    print('waiting for event')
    await event.wait()
    print('got event')
    event.clear()

async def run_event_test():
    print('Test Lock class')
    lock = asyncio.Lock()
    asyncio.create_task(run_lock(1, lock))
    asyncio.create_task(run_lock(2, lock))
    asyncio.create_task(run_lock(3, lock))
    print('Test Event class')
    event = asyncio.Event()
    asyncio.create_task(eventset(event))
    await eventwait(event)  # run_event_test runs fast until this point
    print('Event status {}'.format('Incorrect' if event.is_set() else 'OK'))
    print('Tasks complete')

def event_test():
    printexp('''Test Lock class
Test Event class
waiting for event
run_lock 1 waiting for lock
run_lock 1 acquired lock
run_lock 2 waiting for lock
run_lock 3 waiting for lock
Waiting 5 secs before setting event
run_lock 1 released lock
run_lock 2 acquired lock
run_lock 2 released lock
run_lock 3 acquired lock
run_lock 3 released lock
event was set
got event
Event status OK
Tasks complete
''', 5)
    asyncio.get_event_loop().run_until_complete(run_event_test())

# ************ Barrier test ************

async def main(duration):
    barrier = Barrier(3, callback, ('Synch',))
    for _ in range(3):
        asyncio.create_task(report(barrier))
    await asyncio.sleep(duration)

def callback(text):
    print(text)

async def report(barrier):
    for i in range(5):
        print('{} '.format(i), end='')
        await barrier

def barrier_test():
    printexp('''0 0 0 Synch
1 1 1 Synch
2 2 2 Synch
3 3 3 Synch
4 4 4 Synch
''')
    asyncio.get_event_loop().run_until_complete(main(2))

# ************ Semaphore test ************

async def run_sema(n, sema, barrier):
    print('run_sema {} trying to access semaphore'.format(n))
    async with sema:
        print('run_sema {} acquired semaphore'.format(n))
        # Delay demonstrates other coros waiting for semaphore
        await asyncio.sleep(1 + n/10)  # n/10 ensures deterministic printout
    print('run_sema {} has released semaphore'.format(n))
    barrier.trigger()

async def run_sema_test(bounded):
    num_coros = 5
    barrier = Barrier(num_coros + 1)
    if bounded:
        semaphore = asyncio.BoundedSemaphore(3)
    else:
        semaphore = asyncio.Semaphore(3)
    for n in range(num_coros):
        asyncio.create_task(run_sema(n, semaphore, barrier))
    await barrier  # Quit when all coros complete
    try:
        semaphore.release()
    except ValueError:
        print('Bounded semaphore exception test OK')

def semaphore_test(bounded=False):
    if bounded:
        exp = '''run_sema 0 trying to access semaphore
run_sema 0 acquired semaphore
run_sema 1 trying to access semaphore
run_sema 1 acquired semaphore
run_sema 2 trying to access semaphore
run_sema 2 acquired semaphore
run_sema 3 trying to access semaphore
run_sema 4 trying to access semaphore
run_sema 0 has released semaphore
run_sema 4 acquired semaphore
run_sema 1 has released semaphore
run_sema 3 acquired semaphore
run_sema 2 has released semaphore
run_sema 4 has released semaphore
run_sema 3 has released semaphore
Bounded semaphore exception test OK

Exact sequence of acquisition may vary when 3 and 4 compete for semaphore.'''
    else:
        exp = '''run_sema 0 trying to access semaphore
run_sema 0 acquired semaphore
run_sema 1 trying to access semaphore
run_sema 1 acquired semaphore
run_sema 2 trying to access semaphore
run_sema 2 acquired semaphore
run_sema 3 trying to access semaphore
run_sema 4 trying to access semaphore
run_sema 0 has released semaphore
run_sema 3 acquired semaphore
run_sema 1 has released semaphore
run_sema 4 acquired semaphore
run_sema 2 has released semaphore
run_sema 3 has released semaphore
run_sema 4 has released semaphore

Exact sequence of acquisition may vary when 3 and 4 compete for semaphore.'''
    printexp(exp, 3)
    asyncio.get_event_loop().run_until_complete(run_sema_test(bounded))

# ************ Condition test ************

tim = 0

async def cond01():
    while True:
        await asyncio.sleep(2)
        with await cond:
            cond.notify(2)  # Notify 2 tasks

async def cond03():  # Maintain a count of seconds
    global tim
    await asyncio.sleep(0.5)
    while True:
        await asyncio.sleep(1)
        tim += 1

async def cond01_new(cond):
    while True:
        await asyncio.sleep(2)
        async with cond:
            cond.notify(2)  # Notify 2 tasks

async def cond03_new():  # Maintain a count of seconds
    global tim
    await asyncio.sleep(0.5)
    while True:
        await asyncio.sleep(1)
        tim += 1

async def cond02(n, cond, barrier):
    async with cond:
        print('cond02', n, 'Awaiting notification.')
        await cond.wait()
        print('cond02', n, 'triggered. tim =', tim)
        barrier.trigger()

def predicate():
    return tim >= 8 # 12

async def cond04(n, cond, barrier):
    async with cond:
        print('cond04', n, 'Awaiting notification and predicate.')
        await cond.wait_for(predicate)
        print('cond04', n, 'triggered. tim =', tim)
        barrier.trigger()

async def cond_go():
    cond = asyncio.Condition()
    ntasks = 7
    barrier = Barrier(ntasks + 1)
    t1 = asyncio.create_task(cond01_new(cond))
    t3 = asyncio.create_task(cond03_new())
    for n in range(ntasks):
        asyncio.create_task(cond02(n, cond, barrier))
    await barrier  # All instances of cond02 have completed
    # Test wait_for
    barrier = Barrier(2)
    asyncio.create_task(cond04(99, cond, barrier))
    await barrier
    # cancel continuously running coros.
    t1.cancel()
    t3.cancel()
    await asyncio.sleep(0)
    print('Done.')

def condition_test():
    printexp('''cond02 0 Awaiting notification.
cond02 1 Awaiting notification.
cond02 2 Awaiting notification.
cond02 3 Awaiting notification.
cond02 4 Awaiting notification.
cond02 5 Awaiting notification.
cond02 6 Awaiting notification.
cond02 5 triggered. tim = 1
cond02 6 triggered. tim = 1
cond02 3 triggered. tim = 3
cond02 4 triggered. tim = 3
cond02 1 triggered. tim = 5
cond02 2 triggered. tim = 5
cond02 0 triggered. tim = 7
cond04 99 Awaiting notification and predicate.
cond04 99 triggered. tim = 9
Done.
''', 13)
    asyncio.get_event_loop().run_until_complete(cond_go())

# ************ Queue test ************

async def fillq(myq):
    for x in range(8):
        print('Waiting to put item {} on queue'.format(x))
        await myq.put(x)

async def mtq(myq):
    await asyncio.sleep(1)  # let q fill
    while myq.qsize():
        res = await myq.get()
        print('Retrieved {} from queue'.format(res))
        await asyncio.sleep(0.2)

async def queue_go():
    myq = asyncio.Queue(5)
    asyncio.create_task(fillq(myq))
    await mtq(myq)
    t = asyncio.create_task(fillq(myq))
    await asyncio.sleep(1)
    print('Queue filled. Cancelling fill task. Queue should be full.')
    t.cancel()
    await mtq(myq)
    t = asyncio.create_task(myq.get())
    await asyncio.sleep(1)
    print('Cancelling attempt to get from empty queue.')
    t.cancel()
    print('Queue size:', myq.qsize())

def queue_test():
    printexp('''Running (runtime = 7s):
Waiting to put item 0 on queue
Waiting to put item 1 on queue
Waiting to put item 2 on queue
Waiting to put item 3 on queue
Waiting to put item 4 on queue
Waiting to put item 5 on queue
Retrieved 0 from queue
Waiting to put item 6 on queue
Retrieved 1 from queue
Waiting to put item 7 on queue
Retrieved 2 from queue
Retrieved 3 from queue
Retrieved 4 from queue
Retrieved 5 from queue
Retrieved 6 from queue
Retrieved 7 from queue
Waiting to put item 0 on queue
Waiting to put item 1 on queue
Waiting to put item 2 on queue
Waiting to put item 3 on queue
Waiting to put item 4 on queue
Waiting to put item 5 on queue
Queue filled. Cancelling fill task. Queue should be full.
Retrieved 0 from queue
Retrieved 1 from queue
Retrieved 2 from queue
Retrieved 3 from queue
Retrieved 4 from queue
Cancelling attempt to get from empty queue.
Queue size: 0
''', 7)
    asyncio.get_event_loop().run_until_complete(queue_go())
