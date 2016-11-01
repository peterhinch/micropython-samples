# Time a function call by means of a decorator

# On or shortly beore 1st November 2016 the semantics of utime.ticks_diff changed. If using
# older firmware please use the second example below

import utime
def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(utime.ticks_us(), t)  # Argument order new, old
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

@timed_function
def test():
    utime.sleep_us(10000)

# Version for use with older firmware
def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(t, utime.ticks_us())  # Argument order old, new
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func


