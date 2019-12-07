# Shows that MicroPython seems to cancel a task earlier than CPython
# Also demonstrates that CPython cancels tasks when run() terminates.
try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

async def foo(n):
    try:
        while True:
            await asyncio.sleep(0)
            print(n)
    except asyncio.CancelledError:
        print('Task {} canned.'.format(n))
        raise

async def main(n):
    tasks = []
    for n in range(3):
        tasks.append(asyncio.create_task(foo(n)))
    for _ in range(n):
        await asyncio.sleep(0)
    print('Cancelling task 1')
    tasks[1].cancel()
    for _ in range(3):
        await asyncio.sleep(0)

asyncio.run(main(n=3))

# CPython 3.8
#>>> import test_can
#0
#1
#2
#Cancelling task 1
#0
#Task 1 canned.
#2
#0
#2
#0
#2
#0
#2
#Task 0 canned.
#Task 2 canned.
#>>> 

# MicroPython
#>>> import test_can
#0
#1
#2
#Cancelling task 1
#Task 1 canned.
#0
#2
#0
#2
#0
#2
#>>> 
