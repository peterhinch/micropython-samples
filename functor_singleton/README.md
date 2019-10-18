# Singleton class decorator

A singleton is a class which has only one instance. IT gurus debate whether
they should be used, mainly on the grounds that project aims can change: a need
for multiple instances may arise later. I would argue that singleton classes
have merit in defining interfaces to hardware objects. You can be sure that
(for example) a Pyboard D will only have one RTC instance.

The advantage of a singleton is that it removes the need for a global instance
or for passing an instance between functions. The sole instance is retrieved at
any point in the code using constructor call syntax.

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
The first instantiation sets the object's initial state. Thereafter
'instantiations' retrieve the original object.

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
A use case is in asynchronous programming. The constructor launches a task:
this will only occur once. Subsequent calls might alter the behaviour of that
task. An example may be found
[in the Latency class](https://github.com/peterhinch/micropython-async/blob/master/lowpower/rtc_time.py).
