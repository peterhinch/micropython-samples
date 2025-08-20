# spi.arx.py Demo of asynchronous SPI slave

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

import asyncio
from machine import Pin, reset
from .spi_slave import SpiSlave
from time import sleep_ms

mosi = Pin(0, Pin.IN)
sck = Pin(1, Pin.IN)
csn = Pin(2, Pin.IN)

piospi = SpiSlave(buf=bytearray(300), sm_num=0, mosi=mosi, sck=sck, csn=csn)


async def main():
    async for msg in piospi:
        print(f"Received: {len(msg)} bytes:")
        print(bytes(msg))
        print()


try:
    asyncio.run(main())
finally:
    piospi.deinit()
