# yasmarang pseudorandom number generator.
# Source http://www.literatecode.com/yasmarang

# Author: Peter Hinch
# Copyright Peter Hinch 2020 Released under the MIT license

def yasmarang():
    pad = 0xeda4baba
    n = 69
    d = 233
    dat = 0
    def func():
        nonlocal pad, n, d, dat
        pad = (pad + dat + d * n) & 0xffffffff
        pad = ((pad<<3) + (pad>>29)) & 0xffffffff
        n = pad | 2
        d = (d ^ ((pad<<31) + (pad>>1))) & 0xffffffff
        dat ^= ((pad & 0xff) ^ (d>>8) ^ 1) & 0xff
        return (pad^(d<<5)^(pad>>18)^(dat<<1)) & 0xffffffff
    return func

# Test: produces same outcome as website.
#ym = yasmarang()
#for _ in range(20):
    #print(hex(ym()))
