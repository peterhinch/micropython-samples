# primitives.py A stripped-down verion of asyn.py with Lock and Event only.
# Save RAM on ESP8266

# Released under the MIT licence.
# Copyright (C) Peter Hinch 2018

import uasyncio as asyncio

class Lock():
    def __init__(self, delay_ms=0):
        self._locked = False
        self.delay_ms = delay_ms

    def locked(self):
        return self._locked

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        self.release()
        await asyncio.sleep(0)

    async def acquire(self):
        while True:
            if self._locked:
                await asyncio.sleep_ms(self.delay_ms)
            else:
                self._locked = True
                break

    def release(self):
        if not self._locked:
            raise RuntimeError('Attempt to release a lock which has not been set')
        self._locked = False


class Event():
    def __init__(self, delay_ms=0):
        self.delay_ms = delay_ms
        self.clear()

    def clear(self):
        self._flag = False
        self._data = None

    def __await__(self):
        while not self._flag:
            await asyncio.sleep_ms(self.delay_ms)

    __iter__ = __await__

    def is_set(self):
        return self._flag

    def set(self, data=None):
        self._flag = True
        self._data = data

    def value(self):
        return self._data


class Barrier():
    def __init__(self, participants, func=None, args=()):
        self._participants = participants
        self._func = func
        self._args = args
        self._reset(True)

    def __await__(self):
        self._update()
        if self._at_limit():  # All other threads are also at limit
            if self._func is not None:
                launch(self._func, self._args)
            self._reset(not self._down)  # Toggle direction to release others
            return

        direction = self._down
        while True:  # Wait until last waiting thread changes the direction
            if direction != self._down:
                return
            yield

    __iter__ = __await__

    def trigger(self):
        self._update()
        if self._at_limit():  # All other threads are also at limit
            if self._func is not None:
                launch(self._func, self._args)
            self._reset(not self._down)  # Toggle direction to release others

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

# Task Cancellation
try:
    StopTask = asyncio.CancelledError  # More descriptive name
except AttributeError:
    raise OSError('asyn.py requires uasyncio V1.7.1 or above.')

class TaskId():
    def __init__(self, taskid):
        self.taskid = taskid

    def __call__(self):
        return self.taskid

# Sleep coro breaks up a sleep into shorter intervals to ensure a rapid
# response to StopTask exceptions
async def sleep(t, granularity=100):  # 100ms default
    if granularity <= 0:
        raise ValueError('sleep granularity must be > 0')
    t = int(t * 1000)  # ms
    if t <= granularity:
        await asyncio.sleep_ms(t)
    else:
        n, rem = divmod(t, granularity)
        for _ in range(n):
            await asyncio.sleep_ms(granularity)
        await asyncio.sleep_ms(rem)


class Cancellable():
    task_no = 0  # Generated task ID, index of tasks dict
    tasks = {}  # Value is [coro, group, barrier] indexed by integer task_no

    @classmethod
    def _cancel(cls, task_no):
        task = cls.tasks[task_no][0]
        asyncio.cancel(task)

    @classmethod
    async def cancel_all(cls, group=0, nowait=False):
        tokill = cls._get_task_nos(group)
        barrier = Barrier(len(tokill) + 1)  # Include this task
        for task_no in tokill:
            cls.tasks[task_no][2] = barrier
            cls._cancel(task_no)
        if nowait:
            barrier.trigger()
        else:
            await barrier

    @classmethod
    def _is_running(cls, group=0):
        tasks = cls._get_task_nos(group)
        if tasks == []:
            return False
        for task_no in tasks:
            barrier = cls.tasks[task_no][2]
            if barrier is None:  # Running, not yet cancelled
                return True
            if barrier.busy():
                return True
        return False

    @classmethod
    def _get_task_nos(cls, group):  # Return task nos in a group
        return [task_no for task_no in cls.tasks if cls.tasks[task_no][1] == group]

    @classmethod
    def _get_group(cls, task_no):  # Return group given a task_no
        return cls.tasks[task_no][1]

    @classmethod
    def _stopped(cls, task_no):
        if task_no in cls.tasks:
            barrier = cls.tasks[task_no][2]
            if barrier is not None:  # Cancellation in progress
                barrier.trigger()
            del cls.tasks[task_no]

    def __init__(self, gf, *args, group=0, **kwargs):
        task = gf(TaskId(Cancellable.task_no), *args, **kwargs)
        if task in self.tasks:
            raise ValueError('Task already exists.')
        self.tasks[Cancellable.task_no] = [task, group, None]
        self.task_no = Cancellable.task_no  # For subclass
        Cancellable.task_no += 1
        self.task = task

    def __call__(self):
        return self.task

    def __await__(self):  # Return any value returned by task.
        return (yield from self.task)

    __iter__ = __await__


# @cancellable decorator

def cancellable(f):
    def new_gen(*args, **kwargs):
        if isinstance(args[0], TaskId):  # Not a bound method
            task_id = args[0]
            g = f(*args[1:], **kwargs)
        else:  # Task ID is args[1] if a bound method
            task_id = args[1]
            args = (args[0],) + args[2:]
            g = f(*args, **kwargs)
        try:
            res = await g
            return res
        finally:
            NamedTask._stopped(task_id)
    return new_gen

class NamedTask(Cancellable):
    instances = {}

    @classmethod
    async def cancel(cls, name, nowait=True):
        if name in cls.instances:
            await cls.cancel_all(group=name, nowait=nowait)
            return True
        return False

    @classmethod
    def is_running(cls, name):
        return cls._is_running(group=name)

    @classmethod
    def _stopped(cls, task_id):  # On completion remove it
        name = cls._get_group(task_id())  # Convert task_id to task_no
        if name in cls.instances:
            instance = cls.instances[name]
            barrier = instance.barrier
            if barrier is not None:
                barrier.trigger()
            del cls.instances[name]
        Cancellable._stopped(task_id())

    def __init__(self, name, gf, *args, barrier=None, **kwargs):
        if name in self.instances:
            raise ValueError('Task name "{}" already exists.'.format(name))
        super().__init__(gf, *args, group=name, **kwargs)
        self.barrier = barrier
        self.instances[name] = self
