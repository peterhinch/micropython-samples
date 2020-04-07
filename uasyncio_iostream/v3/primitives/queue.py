# queue.py: adapted from uasyncio V2
# Code is based on Paul Sokolovsky's work.
# This is a temporary solution until uasyncio V3 gets an efficient official version

from ucollections import deque
import uasyncio as asyncio


# Exception raised by get_nowait().
class QueueEmpty(Exception):
    pass


# Exception raised by put_nowait().
class QueueFull(Exception):
    pass

# A queue, useful for coordinating producer and consumer coroutines.

# If maxsize is less than or equal to zero, the queue size is infinite. If it
# is an integer greater than 0, then "await put()" will block when the
# queue reaches maxsize, until an item is removed by get().

# Unlike the standard library Queue, you can reliably know this Queue's size
# with qsize(), since your single-threaded uasyncio application won't be
# interrupted between calling qsize() and doing an operation on the Queue.


class Queue:

    def __init__(self, maxsize=0):
        self.maxsize = maxsize
        self._queue = deque((), maxsize)

    def _get(self):
        return self._queue.popleft()

    async def get(self):  #  Usage: item = await queue.get()
        while not self._queue:
            # Queue is empty, put the calling Task on the waiting queue
            await asyncio.sleep_ms(0)
        return self._get()

    def get_nowait(self):  # Remove and return an item from the queue.
        # Return an item if one is immediately available, else raise QueueEmpty.
        if not self._queue:
            raise QueueEmpty()
        return self._get()

    def _put(self, val):
        self._queue.append(val)

    async def put(self, val):  # Usage: await queue.put(item)
        while self.qsize() >= self.maxsize and self.maxsize:
            # Queue full
            await asyncio.sleep_ms(0)
            # Task(s) waiting to get from queue, schedule first Task
        self._put(val)

    def put_nowait(self, val):  # Put an item into the queue without blocking.
        if self.qsize() >= self.maxsize and self.maxsize:
            raise QueueFull()
        self._put(val)

    def qsize(self):  # Number of items in the queue.
        return len(self._queue)

    def empty(self):  # Return True if the queue is empty, False otherwise.
        return not self._queue

    def full(self):  # Return True if there are maxsize items in the queue.
        # Note: if the Queue was initialized with maxsize=0 (the default),
        # then full() is never True.

        if self.maxsize <= 0:
            return False
        else:
            return self.qsize() >= self.maxsize
