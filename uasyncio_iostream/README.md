# Changes to usayncio

This archive contains suggestions for changes to new `uasyncio`. Item 3 below
added 2 Dec, task queue name reverted to `_queue` as this can now be private.

 1. Implement as a Python package.
 2. Implement synchronisation primitives as package modules to conserve RAM.
 3. `Primitive` class has methods common to most synchronisation primitives.
 Avoids the need for primitives to access the task queue directly.
 4. Add `.priority` method to `Stream` class. Enables I/O to be handled at high
 priority on a per-device basis.
 5. Rename task queue class `TQueue` to avoid name clash with Queue primitive.

## Minor changes

 1. Move `StreamReader` and `StreamWriter` assignments out of legacy section of
 code: these classes exist in `asyncio` 3.8.
 2. `.CreateTask` produces an assertion fail if called with a generator function.
 Avoids obscure traceback if someone omits the parens.
 3. Add machine readable version info. Useful in testing.

# CPython-compatible synchronisation primitives

These aim to work efficiently with the new version. All are separate modules to
conserve RAM. Items 1-4 use classes based on `uasyncio.Primitive`.

 1. `Event`: Moved to separate module.
 2. `Lock`: Kevin Köck's solution.
 3. `Queue`: Paul's solution adapted for efficiency.
 4. `Semaphore`: Also implements `BoundedSemaphore`.
 5. `Condition`.

# Other primitives

Included as examples of user-contributed primitives - see final section.

 1. `Message`: Awaitable `Event` subclass with a data payload.
 2. `Barrier`: Multiple tasks wait until all are either waiting on a Barrier
 instance or have triggered the instance without waiting. Similar to  `gather`
 without the controlling coro: a barrier is shared between peers and may be
 used in loops.

# Test scripts

Hopefully these are self-documenting on import.

 1. `prim_test.py` Tests for synchronisation primitives.
 2. `test_fast_scheduling.py` Demonstrates difference between normal and priority
 I/O scheduling. Runs on Pyboard.
 3. `ms_timer.py` and `ms_timer_test.py` A practical use of priority scheduling to
 implement a timer with higher precision than `asyncio.sleep_ms`. Runs on Pyboard.

# CPython compatibility

`prim_test.py` runs on MicroPython or CPython 3.8, demonstrating that MicroPython
primitives behave similarly to the native CPython ones.

`Message` is common to CPython and MicroPython.
There are two implementations of `Barrier` with the same functionality: a CPython
version and a MicroPython version with specific optimisations. The `Barrier` class
is loosely based on
[a Microsoft concept](https://docs.microsoft.com/en-us/windows/win32/sync/synchronization-barriers).

## Directory structure

MicroPython optimised primitives are in `uasyncio/`. Primitives compatible with
`asyncio` are in `primitives/`.

# Future uasyncio implementations

If part of `uasyncio` is to be implemented in C, it would be good if the following
capabilities were retained to facilitate writing efficient add-on modules along the
lines of the `Message` and `Barrier` classes:
 1. The ability to subclass the `asyncio` compatible primitives.
 2. The ability to subclass `uasyncio.Primitive` (if you implement it).
 3. Some means of creating awaitable classes (e.g. `__iter__`).

The mechanism for doing these things might change, but it would be a shame to lose
the capability.

# Suggestion

Implement `wait_for_ms` as per V2.

# Awaitable classes

I reviewed the code samples in my tutorial: with minor changes to remove event
loop methods they will run under CPython 3.8 and the new uasyncio without
version-specific code. The one exception remains awaitable classes. The `Foo`
class works under both versions but isn't pretty. I guess this is a minor
problem: a similar hack is required for V2 and nobody has complained.
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
