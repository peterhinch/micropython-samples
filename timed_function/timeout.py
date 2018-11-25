# Implement a timeout using a closure
import utime

def to(t):
    tstart = utime.ticks_ms()
    def foo():
        return utime.ticks_diff(utime.ticks_ms(), tstart) > t
    return foo

# Usage
t = to(3000)
for _ in range(10):
    print(t())
    utime.sleep(0.5)

