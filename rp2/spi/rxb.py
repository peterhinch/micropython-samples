# spi.rxb.py Demo of SPI slave blocking read.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

from machine import Pin, reset
from .spi_slave import SpiSlave

mosi = Pin(0, Pin.IN)
sck = Pin(1, Pin.IN)
csn = Pin(2, Pin.IN)

piospi = SpiSlave(bytearray(300), sm_num=4, mosi=mosi, sck=sck, csn=csn)


def test():
    while True:
        print(bytes(piospi.read()))  # Message received. Process it.


try:
    test()
finally:
    piospi.deinit()
