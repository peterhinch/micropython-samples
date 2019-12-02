# semaphore.py

import uasyncio


class Semaphore((uasyncio.Primitive)):
    def __init__(self, value=1):
        super().__init__()
        self._count = value

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.release()

    async def acquire(self):
        if self._count == 0:
            # Semaphore unavailable, put the calling Task on the waiting queue
            self.save_current()
            yield
        self._count -= 1

    def release(self):
        self._count += 1
        self.run_next()  # Task(s) waiting on semaphore, schedule first Task

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
