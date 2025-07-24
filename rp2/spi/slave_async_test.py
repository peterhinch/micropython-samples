# slave_async_test.py Test asynchronous interface of SpiSlave class

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

# Link pins
# 0-19 MOSI
# 1-18 SCK
# 2-17 CSN

from machine import Pin, SPI
import asyncio
from .spi_slave import SpiSlave


async def send(cs, spi, obuf):
    cs(0)
    spi.write(obuf)
    cs(1)
    await asyncio.sleep_ms(100)


async def receive(piospi):
    async for msg in piospi:
        print(f"Received: {len(msg)} bytes:")
        print(bytes(msg))
        print()


async def get_msg(piospi):
    rbuf = bytearray(200)
    nbytes = await piospi.as_read_into(rbuf)
    print(bytes(rbuf[:nbytes]))
    print(f"Received: {nbytes} bytes")


async def test():
    obuf = bytearray(range(512))  # Test data
    # Master CS/
    cs = Pin(17, Pin.OUT, value=1)  # Ensure CS/ is False before we try to receive.
    # Pins for slave
    mosi = Pin(0, Pin.IN)
    sck = Pin(1, Pin.IN)
    csn = Pin(2, Pin.IN)
    piospi = SpiSlave(buf=bytearray(300), sm_num=0, mosi=mosi, sck=sck, csn=csn)
    rt = asyncio.create_task(receive(piospi))
    await asyncio.sleep_ms(0)  # Ensure receive task is running
    # Pins for Master
    pin_miso = Pin(16, Pin.IN)  # Not used: keep driver happy
    pin_sck = Pin(18, Pin.OUT, value=0)
    pin_mosi = Pin(19, Pin.OUT, value=0)
    spi = SPI(0, baudrate=10_000_000, sck=pin_sck, mosi=pin_mosi, miso=pin_miso)
    print(spi)
    print("\nBasic test\n")
    await send(cs, spi, obuf[:256])
    await send(cs, spi, obuf[:20])
    print("\nOverrun test: send 512 bytes, rx buffer is 300 bytes.\n")
    await send(cs, spi, obuf)
    print("\nTest subsequent transfers\n")
    await send(cs, spi, b"The quick brown fox jumps over the lazy dog")
    await send(cs, spi, b"A short message")
    await send(cs, spi, b"A longer message")
    rt.cancel()  # Terminate the read task
    await asyncio.sleep_ms(0)
    print("\nAsynchronous read into user supplied buffer\n")
    asyncio.create_task(get_msg(piospi))  # Set up for a single read
    await asyncio.sleep_ms(0)  # Ensure above task gets to run
    await send(cs, spi, b"Received by .as_read_into()")
    await asyncio.sleep_ms(100)
    print("\nDone")


asyncio.run(test())
