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

# SPI send a passed buffer
def send(cs, spi, obuf):
    cs(0)
    spi.write(obuf)
    cs(1)
    sleep_ms(100)


buf = bytearray(300)  # Read buffer

# Callback runs when transfer complete (soft ISR context)
def receive(nbytes):
    print(f"Received: {nbytes} bytes:")
    print(bytes(buf[:nbytes]))
    print()


def test():
    obuf = bytearray(range(512))  # Test data
    cs = Pin(17, Pin.OUT, value=1)  # Ensure CS/ is False before we try to receive.
    # Pins for slave
    mosi = Pin(0, Pin.IN)
    sck = Pin(1, Pin.IN)
    csn = Pin(2, Pin.IN)
    piospi = SpiSlave(callback=receive, sm_num=4, mosi=mosi, sck=sck, csn=csn)
    # Pins for master
    pin_miso = Pin(16, Pin.IN)  # Not used: keep driver happy
    pin_sck = Pin(18, Pin.OUT, value=0)
    pin_mosi = Pin(19, Pin.OUT, value=0)
    spi = SPI(0, baudrate=10_000_000, sck=pin_sck, mosi=pin_mosi, miso=pin_miso)

    print("\nBasic test\n")
    piospi.read_into(buf)
    send(cs, spi, obuf[:256])
    piospi.read_into(buf)
    send(cs, spi, obuf[:20])
    print("\nOverrun test: send 512 bytes, rx buffer is 300 bytes.\n")
    piospi.read_into(buf)
    send(cs, spi, obuf)
    print("\nTest subsequent transfers\n")
    piospi.read_into(buf)
    send(cs, spi, b"The quick brown fox jumps over the lazy dog")
    piospi.read_into(buf)
    send(cs, spi, b"A short message")
    piospi.read_into(buf)
    send(cs, spi, b"A longer message")
    print("\nDone")


test()
