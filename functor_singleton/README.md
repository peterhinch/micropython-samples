# Singletons and Functors

These closely related concepts describe classes which support only a single
instance. They share a common purpose of avoiding the need for global data by
providing a callable capable of retaining state and whose scope may be that of
the module.

In both cases implementation is via very similar class decorators.

# Singleton class decorator

A singleton is a class with only one instance. Some IT gurus argue against them
on the grounds that project aims can change: a need for multiple instances may
arise later. My view is that they have merit in defining interfaces to hardware
objects. You might be quite certain that your brometer will have only one
pressure sensor.

The advantage of a singleton is that it removes the need for a global instance
or for passing an instance between functions. The sole instance is efficiently
retrieved at any point in the code using function call syntax.

```python
def singleton(cls):
    instance = None
    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
        return instance
    return getinstance

@singleton
class MySingleton:
    def __init__(self, arg):
        self.state = arg
        print('In __init__', arg)

    def foo(self, arg):
        print('In foo', arg + self.state)

ms = MySingleton(42)  # prints 'In __init__ 42'
x = MySingleton()  # No output: assign existing instance to x
x.foo(5)  # prints 'In foo 47': original state + 5
```
The first call instantiates the object and sets its initial state. Subsequent
calls retrieve the original object.

There are other ways of achieving singletons. One is to define a (notionally
private) class in a module. The module API contains an access function. There
is a private instance, initially `None`. The function checks if the instance is
`None`. If so it instantiates the object and assigns it to the instance. In all
cases it returns the instance.

Both have similar logic. The decorator avoids the need for a separate module.

# Functor class decorator

The term "functor" derives from "function constructor". It is a function-like
object which can retain state. Like singletons the aim is to avoid globals: the
state is contained in the functor instance.

```python
def functor(cls):
    instance = None
    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
            return instance
        return instance(*args, **kwargs)
    return getinstance

@functor
class MyFunctor:
    def __init__(self, arg):
        self.state = arg
        print('In __init__', arg)

    def __call__(self, arg):
        print('In __call__', arg + self.state)

MyFunctor(42)  # prints 'In __init__ 42'
MyFunctor(5)  # 'In __call__ 47'
```
A use case is in asynchronous programming. The constructor launches a
continuously running task. Subsequent calls alter the behaviour of that task.
The following simple example has the task waiting for a period which can be
changed at runtime:

```python
import uasyncio as asyncio
import pyb

def functor(cls):
    instance = None
    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
            return instance
        return instance(*args, **kwargs)
    return getinstance

@functor
class FooFunctor:
    def __init__(self, led, interval):
        self.led = led
        self.interval = interval
        asyncio.create_task(self._run())

    def __call__(self, interval):
        self.interval = interval

    async def _run(self):
        while True:
            await asyncio.sleep_ms(self.interval)
            # Do something useful here
            self.led.toggle()

def go_fast():  # FooFunctor is available anywhere in this module
    FooFunctor(100)

async def main():
    FooFunctor(pyb.LED(1), 500)
    await asyncio.sleep(3)
    go_fast()
    await asyncio.sleep(3)

asyncio.run(main())
```
