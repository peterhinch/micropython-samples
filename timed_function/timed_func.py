# Time a function call by means of a decorator

import utime

# @timed_function
# Print time taken by a function call

def timed_function(f, *args, **kwargs):
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(utime.ticks_us(), t) 
        print('Function {} Time = {:6.3f}ms'.format(f.__name__, delta/1000))
        return result
    return new_func

@timed_function
def test():
    utime.sleep_us(10000)

# @time_acc_function
# applied to a function causes it to print the number of times it was called
# with the accumulated time used.

def time_acc_function(f, *args, **kwargs):
    ncalls = 0
    ttime = 0.0
    def new_func(*args, **kwargs):
        nonlocal ncalls, ttime
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(utime.ticks_us(), t) 
        ncalls += 1
        ttime += delta
        print('Function: {} Call count = {} Total time = {:6.3f}ms'.format(f.__name__, ncalls, ttime/1000))
        return result
    return new_func

