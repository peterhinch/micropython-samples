def functor(cls):
    instance = None
    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = cls(*args, **kwargs)
            return instance
        return instance(*args, **kwargs)
    return getinstance

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
a = MySingleton(99)  # No output: assign existing instance to a
a.foo(5)  # prints 'In foo 47': original state + 5


@functor
class MyFunctor:
    def __init__(self, arg):
        self.state = arg
        print('In __init__', arg)

    def __call__(self, arg):
        print('In __call__', arg + self.state)
        return self

MyFunctor(42)  # prints 'In __init__ 42'
MyFunctor(5)  # 'In __call__ 47'
