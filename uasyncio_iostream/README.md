# Changes to usayncio

This archive contains suggestions for changes to new `uasyncio`:

 1. Implement as a Python package.
 2. Implement synchronisation primitives as package modules to conserve RAM.
 3. Add `.priority` method to `Stream` class. Enables I/O to be handled at high
 priority on a per-device basis.
 4. Rename task queue class `TQueue` to avoid name clash with Queue primitive.
 5. Rename task queue instance to `tqueue` as it is used by primitives.

## Minor changes

 1. Move `StreamReader` and `StreamWriter` assignments out of legacy section of
 code: these classes exist in `asyncio` 3.8.
 2. `.CreateTask` produces an assertion fail if called with a generator function.
 Avoids obscure traceback if someone omits the parens.
 3. Add machine readable version info. Useful in testing.

# CPython-compatible synchronisation primitives

The ones I implemented are adapted to work efficiently with the new version.
All are separate modules to conserve RAM.

 1. `Event`: just moved to separate module.
 2. `Lock`: Kevin Köck's solution.
 3. `Queue`: Paul's solution adapted for efficiency.
 4. `Semaphore`: Also implements `BoundedSemaphore`.
 5. `Condition`.

# Other primitives

Included as examples of user-contributed primitives.

 1. `Message`: Awaitable `Event` subclass with a data payload.
 2. `Barrier`: Multiple tasks wait until all reach a Barrier instance. Or some
 tasks wait until others have triggered the Barrier instance.

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
