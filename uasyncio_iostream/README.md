# 1. Changes to usayncio

This archive contains suggestions for changes to new `uasyncio`.

## 1.1 Changes implemented

 1. Implement as a Python package.
 2. Implement synchronisation primitives as package modules to conserve RAM.
 3. `Primitive` class has methods common to most synchronisation primitives.
 Avoids the need for primitives to access the task queue directly.
 4. Add `.priority` method to `Stream` class. Enables I/O to be handled at high
 priority on a per-device basis.
 5. Rename task queue class `TQueue` to avoid name clash with Queue primitive.

### Minor changes

 1. Move `StreamReader` and `StreamWriter` assignments out of legacy section of
 code: these classes exist in `asyncio` 3.8.
 2. `.CreateTask` produces an assertion fail if called with a generator function.
 Avoids obscure traceback if someone omits the parens.
 3. Add machine readable version info. Useful in testing.

## 1.2 Suggested changes

I haven't implemented these.

 1. Make `Event.set` capable of being triggered from an ISR.
 2. Implement `wait_for_ms` as per V2.

# 2. CPython-compatible synchronisation primitives

These aim to work efficiently with the new version. All are separate modules to
conserve RAM. Items 1-4 subclass `uasyncio.Primitive`.

 1. `Event`: Moved to separate module.
 2. `Lock`: Kevin Köck's solution.
 3. `Queue`: Paul's solution adapted for efficiency.
 4. `Semaphore`: Also implements `BoundedSemaphore`.
 5. `Condition`.

# 3. Other primitives

Included as examples of user-contributed primitives - see final section.

 1. `Message`: Awaitable `Event` subclass with a data payload.
 2. `Barrier`: Multiple tasks wait until all are either waiting on a Barrier
 instance or have triggered the instance without waiting. Similar to  `gather`
 without the controlling coro: a barrier is shared between peers and may be
 used in loops.

# 4. Test scripts

Hopefully these are self-documenting on import.

 1. `prim_test.py` Tests for synchronisation primitives. Runs on MicroPython and
 CPython V3.5-3.8. Demonstrates that MicroPython primitives behave similarly to
 native CPython ones.
 2. `test_fast_scheduling.py` Demonstrates difference between normal and priority
 I/O scheduling. Runs on Pyboard.
 3. `ms_timer.py` and `ms_timer_test.py` A practical use of priority scheduling to
 implement a timer with higher precision than `asyncio.sleep_ms`. Runs on Pyboard.
 4. `test_can.py` Demonstrates differences in behaviour between CPython 3.8 and
 MicroPython. See code comments.

# 5. CPython compatibility of user primitives

`Message` is common to CPython and MicroPython.  
There are two implementations of `Barrier` with the same functionality: a CPython
version and a MicroPython version with specific optimisations. The `Barrier` class
is loosely based on
[a Microsoft concept](https://docs.microsoft.com/en-us/windows/win32/sync/synchronization-barriers).

## 5.1 Directory structure of primitives

MicroPython optimised primitives are in `uasyncio/`. Primitives compatible with
`asyncio` are in `primitives/`.

# 6. Future uasyncio implementations

If part of `uasyncio` is to be implemented in C, it would be good if the following
capabilities were retained:
 1. The ability to subclass the `asyncio` compatible primitives.
 2. The ability to subclass `uasyncio.Primitive` (or provide other access to that
 functionality).
 3. A means of replacing the timebase by one based on the RTC for low power
 applications.
 4. A means of creating awaitable classes (e.g. `__iter__`).

# 7. Revisiting topics discussed via email

I am revising my tutorial to promote Python 3.8 syntax and to verify that code
samples run under MicroPython and CPython 3.8. I'm removing references to event
loop methods except for one minor section. This describes how to code for
compatibility with CPython versions 3.5-3.7.

Here are my observations on issues previously discussed.

## 7.1 Awaitable classes

I now have portable code which produces no syntax errors under CPython 3.8. It
is arguably hacky but a similar hack is required for V2. Nobody has complained.
```python
up = False  # Running under MicroPython?
try:
    import uasyncio as asyncio
    up = True  # Or can use sys.implementation.name
except ImportError:
    import asyncio

async def times_two(n):  # Coro to await
    await asyncio.sleep(1)
    return 2 * n

class Foo():
    def __await__(self):
        res = 1
        for n in range(5):
            print('__await__ called')
            if up:  # MicroPython
                res = yield from times_two(res)
            else:  # CPython
                res = yield from times_two(res).__await__()
        return res

    __iter__ = __await__  # MicroPython compatibility

async def bar():
    foo = Foo()  # foo is awaitable
    print('waiting for foo')
    res = await foo  # Retrieve value
    print('done', res)

asyncio.run(bar())
```

## 7.2 run_forever() behaviour

In an email I commented that the following code sample never terminates under
CPython 3.8, whereas under MicroPython it does:
```python
try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

async def test():
    print("test")
    for _ in range(2):
        await asyncio.sleep(0)
        print('test2')
        await asyncio.sleep(0.5)
    print('Done')

loop=asyncio.get_event_loop()
loop.create_task(test())
loop.run_forever()
# asyncio.run(test())
```
While the observation is true, using the preferred (commented out) syntax it
terminates in CPython 3.8 and in MicroPython. My view is that it's not worth
fixing.
