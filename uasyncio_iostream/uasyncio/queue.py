# queue.py: adapted from uasyncio V2
from ucollections import deque
import uasyncio


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
        self.p_tasks = uasyncio.TQueue() # Queue of Tasks waiting to put to queue
        self.g_tasks = uasyncio.TQueue() # Queue of Tasks waiting to get from queue

    def _get(self):
        return self._queue.popleft()

    async def get(self):  #  Usage: item = await queue.get()
        if not self._queue:
            # Queue is empty, put the calling Task on the waiting queue
            task = uasyncio.cur_task
            self.g_tasks.push_head(task)
            # Set calling task's data to double-link it
            task.data = self
            try:
                yield
            except asyncio.CancelledError:
                self.g_tasks.remove(task)
                raise
        if self.p_tasks.next:
            # Task(s) waiting to put on queue, schedule first Task
            uasyncio.tqueue.push_head(self.p_tasks.pop_head())
        return self._get()

    def get_nowait(self):  # Remove and return an item from the queue.
        # Return an item if one is immediately available, else raise QueueEmpty.
        if not self._queue:
            raise QueueEmpty()
        return self._get()

    def _put(self, val):
        self._queue.append(val)

    async def put(self, val):  # Usage: await queue.put(item)
        if self.qsize() >= self.maxsize and self.maxsize:
            # Queue full, put the calling Task on the waiting queue
            task = uasyncio.cur_task
            self.p_tasks.push_head(task)
            # Set calling task's data to double-link it
            uasyncio.cur_task.data = self
            try:
                yield
            except asyncio.CancelledError:
                self.p_tasks.remove(task)
                raise
        if self.g_tasks.next:
            # Task(s) waiting to get from queue, schedule first Task
            uasyncio.tqueue.push_head(self.g_tasks.pop_head())
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

# Name collision fixed
uasyncio.Queue = Queue
