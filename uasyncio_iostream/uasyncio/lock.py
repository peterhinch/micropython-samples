import uasyncio

################################################################################
# Lock (optional component)

# Lock class for primitive mutex capability
import uasyncio


class Lock:
    def __init__(self):
        self._locked = False
        self.waiting = uasyncio.TQueue()  # Linked list of Tasks waiting on completion of this event
        self._awt = None  # task that is going to acquire the lock. Needed to prevent race
        # condition between pushing the next waiting task and the task actually acquiring
        # the lock because during that time another newly started task could acquire the
        # lock out-of-order instead of being pushed to the waiting list.
        # Also needed to not release another waiting Task if multiple Tasks are cancelled.

    async def acquire(self):
        if self._locked or self._awt:
            # Lock set or just released but has tasks waiting on it,
            # put the calling task on the Lock's waiting queue and yield
            self.waiting.push_head(uasyncio.cur_task)
            uasyncio.cur_task.data = self
            try:
                yield
            except uasyncio.CancelledError:
                if self._awt is uasyncio.cur_task:
                    # Task that was going to acquire got cancelled after being scheduled.
                    # Schedule next waiting task
                    self._locked = True
                    self.release()
                raise
        self._locked = True
        return True

    async def __aenter__(self):
        await self.acquire()
        return self

    def locked(self):
        return self._locked

    def release(self):
        if not self._locked:
            raise RuntimeError("Lock is not acquired.")
        self._locked = False
        self._awt = self.waiting.next  # Task which will get lock
        if self.waiting.next:
            # Lock becomes available, schedule next task waiting on it
            uasyncio.tqueue.push_head(self.waiting.pop_head())

    async def __aexit__(self, *args):
        return self.release()


uasyncio.Lock = Lock
