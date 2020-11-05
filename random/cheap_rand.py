# pseudorandom numbers for MicroPython. ISR friendly version.
# Probably poor quality numbers but useful in test scripts

# Author: Peter Hinch
# Copyright Peter Hinch 2020 Released under the MIT license

# Example usage to produce numbers between 0 and 99
# rand = cheap_rand(100)
# successive calls to rand() will produce the required result.

def cheap_rand(modulo, seed=0x3fba2):
    x = seed 
    def func():
        nonlocal x
        x ^= (x & 0x1ffff) << 13;
        x ^= x >> 17;
        x ^= (x & 0x1ffffff) << 5;
        return x % modulo
    return func

# The sum total of my statistical testing
#import pyb, micropython, time
#rand = cheap_rand(1000)
#sum = 0
#cnt = 0
#def avg(n):
    #global sum, cnt
    #sum += n
    #cnt += 1
#def cb(t):
    #n = rand()
    #micropython.schedule(avg, n)

#t = pyb.Timer(1, freq=20, callback=cb)
#while True:
    #time.sleep(1)
    #print(sum/cnt)
