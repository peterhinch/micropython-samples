# semaphore.py

import uasyncio


class Semaphore():
    def __init__(self, value=1):
        self._count = value
        self.waiting = uasyncio.TQueue()  # Linked list of Tasks waiting on completion of this event

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.release()

    async def acquire(self):
        if self._count == 0:
            # Semaphore unavailable, put the calling Task on the waiting queue
            self.waiting.push_head(uasyncio.cur_task)
            # Set calling task's data to double-link it
            uasyncio.cur_task.data = self
            yield
        self._count -= 1

    def release(self):
        self._count += 1
        if self.waiting.next:
            # Task(s) waiting on semaphore, schedule first Task
            uasyncio.tqueue.push_head(self.waiting.pop_head())

class BoundedSemaphore(Semaphore):
    def __init__(self, value=1):
        super().__init__(value)
        self._initial_value = value

    def release(self):
        if self._count < self._initial_value:
            super().release()
        else:
            raise ValueError('Semaphore released more than acquired')

uasyncio.Semaphore = Semaphore
uasyncio.BoundedSemaphore = BoundedSemaphore
