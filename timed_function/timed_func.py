# Time a function call by means of a decorator

import utime

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(t, utime.ticks_us())
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

@timed_function
def test():
    utime.sleep_us(10000)

