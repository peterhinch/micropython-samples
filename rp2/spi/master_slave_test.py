# master_slave_test.py Test asynchronous interface of SpiSlave and master class

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

# Link pins
# 0-19 MOSI
# 1-18 SCK
# 2-17 CSN

from machine import Pin
import asyncio
from .spi_slave import SpiSlave
from .spi_master import RP2_SPI_DMA_MASTER


tsf = asyncio.ThreadSafeFlag()


def callback(dma):  # Hard ISR
    tsf.set()  # Flag user code that transfer is complete


async def send(cs, spi, data):
    cs(0)  # Assert CS/
    spi.write(data)  # "Immediate" return: minimal blocking.
    await tsf.wait()  # Wait for transfer complete (other tasks run)
    cs(1)  # Deassert CS/
    await asyncio.sleep_ms(100)


async def receive(piospi):
    async for msg in piospi:
        print(f"Received: {len(msg)} bytes:")
        print(bytes(msg))
        print()


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
    pin_sck = Pin(18, Pin.OUT, value=0)
    pin_mosi = Pin(19, Pin.OUT, value=0)
    spi = RP2_SPI_DMA_MASTER(4, 10_000_000, pin_sck, pin_mosi, callback)
    print("\nBasic test\n")
    await send(cs, spi, obuf[:256])
    await send(cs, spi, obuf[:20])
    await send(cs, spi, b"The quick brown fox jumps over the lazy dog")
    print("\nDone")


asyncio.run(test())
