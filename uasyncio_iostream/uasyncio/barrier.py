# barrier.py

# A Barrier synchronises N coros. Each issues await barrier.
# Execution pauses until all other participant coros are waiting on it.
# At that point the callback is executed. Then the barrier is 'opened' and
# execution of all participants resumes.

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


class Barrier():
    def __init__(self, participants, func=None, args=()):
        self._participants = participants
        self._func = func
        self._args = args
        self.waiting = uasyncio.TQueue()  # Linked list of Tasks waiting on completion of barrier
        self._reset(True)

    def trigger(self):
        self._update()
        if self._at_limit():  # All other coros are also at limit
            if self._func is not None:
                launch(self._func, self._args)
            self._reset(not self._down)  # Toggle direction and release others
            while self.waiting.next:
                uasyncio.tqueue.push_head(self.waiting.pop_head())

    def __iter__(self):
        self._update()
        if self._at_limit():  # All other coros are also at limit
            if self._func is not None:
                launch(self._func, self._args)
            self._reset(not self._down)  # Toggle direction and release others
            while self.waiting.next:
                uasyncio.tqueue.push_head(self.waiting.pop_head())
            return
        direction = self._down
        # Other tasks have not reached barrier, put the calling task on the barrier's waiting queue
        self.waiting.push_head(uasyncio.cur_task)
        # Set calling task's data to this barrier that it waits on, to double-link it
        uasyncio.cur_task.data = self
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

uasyncio.Barrier = Barrier
