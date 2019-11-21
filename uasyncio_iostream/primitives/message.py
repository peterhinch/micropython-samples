# message.py
# A coro waiting on a message issues msg = await message_instance
# A coro rasing the message issues message_instance.set(msg)
# When all waiting coros have run
# message_instance.clear() should be issued

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio


class Message(asyncio.Event):
    def __init__(self):
        super().__init__()
        self._data = None

    def clear(self):
        super().clear()

    def __await__(self):
        yield from self.wait().__await__()  # CPython
        return self._data

    def __iter__(self):
        yield from self.wait()  # MicroPython
        return self._data

    def set(self, data=None):
        super().set()
        self._data = data

    def value(self):
        return self._data
