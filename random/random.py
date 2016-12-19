# pseudorandom numbers for MicroPython
# Uses the xorshift64star algorithm https://en.wikipedia.org/wiki/Xorshift
# Author: Peter Hinch
# Copyright Peter Hinch 2016 Released under the MIT license

# Example usage to produce numbers between 0 and 99
# rando = xorshift64star(100)
# successive calls to rando() will produce the required result.
# Timing 109us (Pyboard 1.1), 191us (Pyboard lite), 1.264ms (ESP8266)


def xorshift64star(modulo, seed = 0xf9ac6ba4):
    x = seed
    def func():
        nonlocal x
        x ^= x >> 12
        x ^= ((x << 25) & 0xffffffffffffffff)  # modulo 2**64
        x ^= x >> 27
        return (x * 0x2545F4914F6CDD1D) % modulo
    return func
