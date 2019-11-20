import uasyncio

# Event class for primitive events that can be waited on, set, and cleared
class Event:
    def __init__(self):
        self.state = 0 # 0=unset; 1=set
        self.waiting = uasyncio.TQueue() # Queue of Tasks waiting on completion of this event
    def set(self):
        # Event becomes set, schedule any tasks waiting on it
        while self.waiting.next:
            uasyncio.tqueue.push_head(self.waiting.pop_head())
        self.state = 1
    def clear(self):
        self.state = 0
    def is_set(self):
        return self.state  # CPython compatibility
    async def wait(self):
        if self.state == 0:
            # Event not set, put the calling task on the event's waiting queue
            self.waiting.push_head(uasyncio.cur_task)
            # Set calling task's data to this event that it waits on, to double-link it
            uasyncio.cur_task.data = self
            yield
        return True

uasyncio.Event = Event

# A coro waiting on a message issues msg = await Message_instance
# A coro rasing the message issues event.set(msg)
# When all waiting coros have run
# Message.clear() should be issued
class Message(uasyncio.Event):
    def __init__(self, delay_ms=0):
        super().__init__()
        self._data = None

    def clear(self):
        super().clear()

    def __iter__(self):
        await self.wait()
        return self._data

    def set(self, data=None):
        super().set()
        self._data = data

    def value(self):
        return self._data

uasyncio.Message = Message
