# Derived from https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_spi.py
import rp2
from machine import Pin
import asyncio
from micropython import alloc_emergency_exception_buf

alloc_emergency_exception_buf(100)


@rp2.asm_pio(autopull=True, pull_thresh=8, sideset_init=rp2.PIO.OUT_LOW, out_init=rp2.PIO.OUT_LOW)
def spi_cpha0():
    # Note X must be preinitialised by setup code before first byte, we reload after sending each byte
    set(x, 6)
    # Actual program body follows
    wrap_target()
    pull(ifempty).side(0x0)[1]
    label("bitloop")
    out(pins, 1).side(0x0)[1]
    jmp(x_dec, "bitloop").side(0x1)[1]

    out(pins, 1).side(0x0)
    set(x, 6).side(0x0)
    mov(y, y).side(0x1)  # NOP
    jmp(not_osre, "bitloop").side(0x1)  # Fallthru if TXFIFO empties
    wrap()


# Get data request channel for a SM: RP2040 datasheet 2.5.3 RP2350 12.6.4.1
def dreq(sm, rx=False):
    d = (sm & 3) + ((sm >> 2) << 3)
    return 4 + d if rx else d


class RP2_SPI_DMA_MASTER:
    def __init__(self, sm_num, freq, sck, mosi, callback):
        self._sm_num = sm_num
        self._dma = rp2.DMA()
        self._dma.irq(handler=callback, hard=True)  # Assign callback
        dc = dreq(sm_num)  # Data request channel
        # Transfer bytes, don't increment the write address, irq at end, and pace the transfer.
        self._ctrl = self._dma.pack_ctrl(size=0, inc_write=False, irq_quiet=False, treq_sel=dc)
        f = 4 * freq  # 4 clock cycles per bit
        self._sm = rp2.StateMachine(sm_num, spi_cpha0, freq=f, sideset_base=sck, out_base=mosi)
        self._sm.active(1)

    def close(self):
        self._dma.active(0)
        self._sm.active(0)

    def write(self, data):
        self._dma.config(read=data, write=self._sm, count=len(data), ctrl=self._ctrl, trigger=True)


# ***** Test Script *****
pin_cs = Pin(20, Pin.OUT, value=1)
pin_sck = Pin(18, Pin.OUT, value=0)
pin_mosi = Pin(19, Pin.OUT, value=0)

tsf = asyncio.ThreadSafeFlag()


def callback(dma):  # Hard ISR
    tsf.set()  # Flag user code that transfer is complete


spi = RP2_SPI_DMA_MASTER(0, 1_000_000, pin_sck, pin_mosi, callback)


async def eot():  # Handle end of transfer
    while True:
        await tsf.wait()
        pin_cs(1)


async def main():
    src_data = b"the quick brown fox jumps over the lazy dog"
    asyncio.create_task(eot())
    n = 0
    while True:
        pin_cs(0)
        spi.write(src_data)  # "Immediate" return.
        await asyncio.sleep(1)
        print(n)
        n += 1


try:
    asyncio.run(main())
except KeyboardInterrupt:
    spi.close()
    asyncio.new_event_loop()
