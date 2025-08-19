from machine import Pin, reset
from .spi_slave import SpiSlave
from time import sleep_ms

mosi = Pin(0, Pin.IN)
sck = Pin(1, Pin.IN)
csn = Pin(2, Pin.IN)

nbytes = 0

buf = bytearray(300)  # Read buffer


def receive(num_bytes):
    global nbytes
    nbytes = num_bytes


piospi = SpiSlave(callback=receive, sm_num=4, mosi=mosi, sck=sck, csn=csn)


def test():
    global nbytes
    while True:
        nbytes = 0
        piospi.read_into(buf)  # Initiate a read
        while nbytes == 0:  # Wait for message arrival
            pass  # Can do something useful while waiting
        print(bytes(buf[:nbytes]))  # Message received. Process it.


try:
    test()
finally:
    reset()
