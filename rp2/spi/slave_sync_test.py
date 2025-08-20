# slave_sync_test.py Test synchronous interface of SpiSlave class

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

# Link pins
# 0-19 MOSI
# 1-18 SCK
# 2-17 CSN

from machine import Pin, SPI, SoftSPI
from .spi_slave import SpiSlave
from time import sleep_ms

# Create synchronous master using standard library
cs = Pin(17, Pin.OUT, value=1)  # Ensure CS/ is False before we try to receive.
pin_miso = Pin(16, Pin.IN)  # Not used: keep driver happy
pin_sck = Pin(18, Pin.OUT, value=0)
pin_mosi = Pin(19, Pin.OUT, value=0)
spi = SPI(0, baudrate=10_000_000, sck=pin_sck, mosi=pin_mosi, miso=pin_miso)

# Callback for receiver
buf = bytearray(300)  # Read buffer


def receive(nbytes):  # Soft ISR runs when data received.
    print(f"Received: {nbytes} bytes:")
    print(bytes(buf[:nbytes]))
    print()


# Pins for slave
mosi = Pin(0, Pin.IN)
sck = Pin(1, Pin.IN)
csn = Pin(2, Pin.IN)
piospi = SpiSlave(callback=receive, sm_num=4, mosi=mosi, sck=sck, csn=csn)

# SPI send a passed buffer
def send(obuf):
    cs(0)
    spi.write(obuf)
    cs(1)
    sleep_ms(100)


def test():
    obuf = bytearray(range(512))  # Test data

    print("\nBasic test\n")
    piospi.read_into(buf)
    send(obuf[:256])
    piospi.read_into(buf)
    send(obuf[:20])
    print("\nOverrun test: send 512 bytes, rx buffer is 300 bytes.\n")
    piospi.read_into(buf)
    send(obuf)
    print("\nTest subsequent transfers\n")
    piospi.read_into(buf)
    send(b"The quick brown fox jumps over the lazy dog")
    piospi.read_into(buf)
    send(b"A short message")
    piospi.read_into(buf)
    send(b"A longer message")
    print("\nDone")


try:
    test()
finally:
    piospi.deinit()
