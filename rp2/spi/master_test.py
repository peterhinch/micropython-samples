# master_test.py Test script for spi_dma.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

# Performs SPI output: check on scope or LA.

from machine import Pin
import asyncio
from .spi_master import SpiMaster

pin_cs = Pin(20, Pin.OUT, value=1)
pin_sck = Pin(18, Pin.OUT, value=0)
pin_mosi = Pin(19, Pin.OUT, value=0)

tsf = asyncio.ThreadSafeFlag()


def callback(dma):  # Hard ISR
    tsf.set()  # Flag user code that transfer is complete


spi = SpiMaster(6, 1_000_000, pin_sck, pin_mosi, callback)


async def send(data):
    pin_cs(0)  # Assert CS/
    spi.write(data)  # "Immediate" return: minimal blocking.
    await tsf.wait()  # Wait for transfer complete (other tasks run)
    pin_cs(1)  # Deassert CS/


async def main():
    src_data = b"\xFF\x55\xAA\x00the quick brown fox jumps over the lazy dog"
    n = 0
    while True:
        asyncio.create_task(send(src_data))  # Send as a background task
        await asyncio.sleep(1)
        print(n)
        n += 1


try:
    asyncio.run(main())
except KeyboardInterrupt:
    spi.deinit()
    asyncio.new_event_loop()
