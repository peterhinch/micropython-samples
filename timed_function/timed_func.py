# Time a function call by means of a decorator

import utime
def tdiff():
    new_semantics = utime.ticks_diff(2, 1) == 1
    def func(old, new):
        nonlocal new_semantics
        if new_semantics:
            return utime.ticks_diff(new, old)
        return utime.ticks_diff(old, new)
    return func

ticksdiff = tdiff()

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = ticksdiff(t, utime.ticks_us())
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

@timed_function
def test():
    utime.sleep_us(10000)

