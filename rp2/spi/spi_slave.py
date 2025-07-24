# spi_slave.py An asynchronous, DMA driven, SPI slave using the PIO.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

import rp2
from machine import Pin, mem32
import asyncio
from micropython import schedule, alloc_emergency_exception_buf

alloc_emergency_exception_buf(100)

# pin numbers (offset from start_pin)
# 0 MOSI
# 1 Clk
# 2 CS\


@rp2.asm_pio(autopush=True, autopull=True)
def spi_in():
    label("escape")  # Just started, transfer ended or overrun attempt.
    out(y, 32)  # Get maximum byte count (blocking wait)
    wait(0, pins, 2)  # Wait for CS/ True
    wrap_target()  # Input a byte
    set(x, 7)
    label("bit")
    jmp(pin, "next")
    jmp(not_osre, "done")  # Data received: quit
    jmp("bit")
    label("next")  # clk leading edge
    in_(pins, 1)  # Input a bit MSB first
    wait(0, pins, 1)  # clk trailing
    jmp(y_dec, "continue")
    label("overrun")  # An overrun would occur. Wait for CS/ ISR to send data.
    jmp(not_osre, "done")  # Data received
    jmp("overrun")
    label("continue")
    jmp(x_dec, "bit")  # Post decrement
    wrap()  # Next byte
    label("done")  # ISR has sent data
    out(x, 32)  # Discard it
    in_(y, 30)  # Return amount of unfilled buffer truncated to 30 bits
    # Truncation ensures that overrun returns a short int
    jmp("escape")


class SpiSlave:
    def __init__(self, buf=None, callback=None, sm_num=0, *, mosi, sck, csn):
        # Get data request channel for a SM: RP2040 datasheet 2.5.3 RP2350 12.6.4.1
        def dreq(sm, rx=False):
            d = (sm & 3) + ((sm >> 2) << 3)
            return 4 + d if rx else d

        self._callback = callback
        # Set up DMA
        self._dma = rp2.DMA()
        # Transfer bytes, rather than words, don't increment the read address and pace the transfer.
        self._cfg = self._dma.pack_ctrl(size=0, inc_read=False, treq_sel=dreq(sm_num, True))
        self._sm_num = sm_num
        self._buf = buf
        self._nbytes = 0  # Number of received bytes
        if buf is not None:
            self._mvb = memoryview(buf)
        self._tsf = asyncio.ThreadSafeFlag()
        csn.irq(self._done, trigger=Pin.IRQ_RISING, hard=True)  # IRQ occurs at end of transfer
        self._sm = rp2.StateMachine(
            sm_num,
            spi_in,
            in_shiftdir=rp2.PIO.SHIFT_LEFT,
            push_thresh=8,
            in_base=mosi,
            jmp_pin=sck,
        )

    def __aiter__(self):  # Asynchronous iterator support
        return self

    async def __anext__(self):
        if self._buf is None:
            raise OSError("No buffer provided to constructor.")

        self.read_into(self._buf)  # Initiate DMA and return.
        await self._tsf.wait()  # Wait for CS/ high (master signals transfer complete)
        return self._mvb[: self._nbytes]

    # Initiate a read into a buffer. Immediate return.
    def read_into(self, buf):
        buflen = len(buf)
        self._buflen = buflen  # Save for ISR
        self._dma.active(0)  # De-activate befor re-configuring
        self._sm.active(0)
        self._tsf.clear()
        self._dma.config(read=self._sm, write=buf, count=buflen, ctrl=self._cfg, trigger=False)
        self._dma.active(1)
        self._sm.restart()
        self._sm.active(1)  # Start SM
        self._sm.put(buflen, 3)  # Number of expected bits

    # Hard ISR for CS/ rising edge.
    def _done(self, _):  # Get no. of bytes received.
        self._dma.active(0)
        self._sm.put(0)  # Request no. of received bits
        if not self._sm.rx_fifo():  # Occurs if .read_into() never called while CSN is low:
            return  # ISR runs on trailing edge but SM is not running. Nothing to do.
        sp = self._sm.get() >> 3  # Bits->bytes: space left in buffer or 7ffffff on overflow
        self._nbytes = self._buflen - sp if sp != 0x7FFFFFF else self._buflen
        self._dma.active(0)
        self._sm.active(0)
        self._tsf.set()
        if self._callback is not None:
            schedule(self._callback, self._nbytes)  # Soft ISR

    # Await a read into a user-supplied buffer. Return no. of bytes read.
    async def as_read_into(self, buf):
        self.read_into(buf)  # Start the read
        await self._tsf.wait()  # Wait for CS/ high (master signals transfer complete)
        return self._nbytes
