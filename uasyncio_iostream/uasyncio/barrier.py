# barrier.py MicroPython optimised version

# A Barrier synchronises N coros. In normal use each issues await barrier.
# Execution pauses until all other participant coros are waiting on it.
# At that point the callback is executed. Then the barrier is 'opened' and
# execution of all participants resumes.
# .trigger enables a coro to signal it has passed the barrier without waiting.

try:
    import asyncio
    raise RuntimeError('This version of barrier is MicroPython specific')
except ImportError:
    import uasyncio

async def _g():
    pass
type_coro = type(_g())

# If a callback is passed, run it and return.
# If a coro is passed initiate it and return.
# coros are passed by name i.e. not using function call syntax.
def launch(func, tup_args):
    res = func(*tup_args)
    if isinstance(res, type_coro):
        uasyncio.create_task(res)


class Barrier(uasyncio.Primitive):
    def __init__(self, participants, func=None, args=()):
        super().__init__()
        self._participants = participants
        self._func = func
        self._args = args
        self._reset(True)

    def trigger(self):
        self._update()
        if self._at_limit():  # All other coros are also at limit
            if self._func is not None:
                launch(self._func, self._args)
            self._reset(not self._down)  # Toggle direction and release others
            self.run_all()

    def __iter__(self):  # MicroPython
        self._update()
        if self._at_limit():  # All other coros are also at limit
            if self._func is not None:
                launch(self._func, self._args)
            self._reset(not self._down)  # Toggle direction and release others
            self.run_all()
            return
        direction = self._down
        # Other tasks have not reached barrier, put the calling task on the barrier's waiting queue
        self.save_current()
        yield

    def _reset(self, down):
        self._down = down
        self._count = self._participants if down else 0

    def busy(self):
        if self._down:
            done = self._count == self._participants
        else:
            done = self._count == 0
        return not done

    def _at_limit(self):  # Has count reached up or down limit?
        limit = 0 if self._down else self._participants
        return self._count == limit

    def _update(self):
        self._count += -1 if self._down else 1
        if self._count < 0 or self._count > self._participants:
            raise ValueError('Too many tasks accessing Barrier')
