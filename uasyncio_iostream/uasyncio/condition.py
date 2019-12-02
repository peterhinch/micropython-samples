import uasyncio
import uasyncio.lock
import uasyncio.event

class Condition:
    def __init__(self, lock=None):
        self.lock = uasyncio.Lock() if lock is None else lock
        self.events = []

    async def acquire(self):
        await self.lock.acquire()

# enable this syntax:
# with await condition [as cond]:
    #def __iter__(self):
        #await self.lock.acquire()
        #return self

    async def __aenter__(self):
        await self.lock.acquire()
        return self

    async def __aexit__(self, *_):
        self.lock.release()

    def locked(self):
        return self.lock.locked()

    def release(self):
        self.lock.release()  # Will raise RuntimeError if not locked

    def notify(self, n=1):  # Caller controls lock
        if not self.lock.locked():
            raise RuntimeError('Condition notify with lock not acquired.')
        for _ in range(min(n, len(self.events))):
            ev = self.events.pop()
            ev.set()

    def notify_all(self):
        self.notify(len(self.events))

    async def wait(self):
        if not self.lock.locked():
            raise RuntimeError('Condition wait with lock not acquired.')
        ev = uasyncio.Event()
        self.events.append(ev)
        self.lock.release()
        await ev.wait()
        await self.lock.acquire()
        assert ev not in self.events, 'condition wait assertion fail'
        return True  # CPython compatibility

    async def wait_for(self, predicate):
        result = predicate()
        while not result:
            await self.wait()
            result = predicate()
        return result

uasyncio.Condition = Condition
