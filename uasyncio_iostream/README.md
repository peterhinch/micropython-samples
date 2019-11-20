# Changes to usayncio

 1. Implement as a Python package.
 2. Implement synchronisation primitives as package modules to conserve RAM.
 3. Add .priority method to Stream class. Enables I/O to be handled at high
 priority on a per-device basis.
 4. Rename task queue class TQueue to avoid name clash with Queue primitive.
 5. Rename task queue instance to tqueue as it is used by primitives.

## Minor changes

 1. Move StreamReader and StreamWriter assignments out of legacy section of code.
 2. CreateTask produces an assertion fail if called with a generator function.
 Avoids obscure traceback if someone omits the parens.
 3. Add machine readable version.

# CPython-compatible synchronisation primitives

These have been adapted to work efficiently with the new version.

 1. `Event`: moved to separate module for consistency with other primitives.
 2. `Lock`: Kevin Köck's solution.
 3. `Queue`: Paul's solution adapted for efficiency.
 4. `Semaphore`: Also implements BoundedSemaphore.
 5. `Condition`.

# Other primitives

 1. Message: Awaitable `Event` subclass with a data payload.
 2. Barrier: Multiple tasks wait until all reach a Barrier instance. Or some tasks
 wait until others have triggered the Barrier instance.

# Test scripts

Hopefully these are self-documenting on import.

 1. `prim_test.py` Tests for synchronisation primitives.
 2. `test_fast_scheduling.py` Demonstrates difference between normal and priority
 I/O scheduling. Runs on Pyboard.
 3. `ms_timer.py` and `ms_timer_test.py` A practical use of priority scheduling to
 implement a timer with higher precision than `asyncio.sleep_ms`. Runs on Pyboard.

# Note

Use of I/O is still incompatible with Unix.
