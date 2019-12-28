import uasyncio

# Event class for primitive events that can be waited on, set, and cleared
class Event(uasyncio.Primitive):
    def __init__(self):
        super().__init__()
        self.state = False
    def set(self):        # Event becomes set, schedule any tasks waiting on it
        self.run_all()
        self.state = True
    def clear(self):
        self.state = False
    def is_set(self):
        return self.state  # CPython compatibility
    async def wait(self):
        if not self.state:
            # Event not set, put the calling task on the event's waiting queue
            self.save_current()
            yield
        return True

uasyncio.Event = Event
