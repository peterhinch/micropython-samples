# spi_slave.py An asynchronous, DMA driven, SPI slave using the PIO.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

import rp2
from machine import Pin
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
    label("bit")  # Await a +ve clock edge or incoming "quit" signal
    jmp(pin, "next")
    jmp(not_osre, "done")  # Data received: quit
    jmp("bit")
    label("next")  # clk leading edge
    in_(pins, 1)  # Input a bit MSB first
    wait(0, pins, 1)  # clk trailing
    jmp(y_dec, "continue")
    # Last trailing clock edge received
    label("overrun")  # An overrun would occur. Wait for CS/ ISR to send data.
    jmp(not_osre, "done")  # Data received
    jmp("overrun")
    label("continue")
    jmp(x_dec, "bit")  # Post decrement
    # push()
    wrap()  # Next byte
    label("done")  # ISR has sent data
    out(x, 32)  # Discard it
    in_(y, 30)  # Return amount of unfilled buffer truncated to 30 bits
    # Truncation ensures that overrun returns a short int
    # push()
    jmp("escape")


# in_base = MOSI. Offsets CLK(1), CS/(2)
# out_base = MISO
# DMA feeds OSR via autopull


@rp2.asm_pio(autopull=True, pull_thresh=8, out_init=rp2.PIO.OUT_LOW)
def spi_out():
    wait(0, pins, 2)  # Wait for CS/ True
    wrap_target()
    set(x, 7)
    label("bit")
    wait(0, pins, 1)  # Await clock low
    out(pins, 1)  # Stalls here if out of data: IRQ resets SM
    wait(1, pins, 1)  # Await high going clock edge
    jmp(x_dec, "bit")
    wrap()


class SpiSlave:
    def __init__(self, buf=None, callback=None, sm_num=0, *, mosi, sck, csn, miso=None):
        # Get data request channel for a SM: RP2040 datasheet 2.5.3 RP2350 12.6.4.1
        def dreq(sm, rx=False):
            d = (sm & 3) + ((sm >> 2) << 3)
            return 4 + d if rx else d

        self._io = miso is not None
        self._csn = csn
        self._wq = []  # Write queue
        self._callback = callback
        self._docb = False  # By default CB des not run
        # Set up read DMA
        self._dma = rp2.DMA()
        # Transfer bytes, rather than words, don't increment the read address and pace the transfer.
        self._cfg = self._dma.pack_ctrl(size=0, inc_read=False, treq_sel=dreq(sm_num, True))
        # Input (MOSI) SM
        self._buf = buf
        self._nbytes = 0  # Number of received bytes
        if buf is not None:
            self._mvb = memoryview(buf)
        self._tsf = asyncio.ThreadSafeFlag()
        self._read_done = False  # Synchronisation for .read()
        # IRQ occurs at end of transfer
        csn.irq(self._done, trigger=Pin.IRQ_RISING, hard=False)
        self._sm = rp2.StateMachine(
            sm_num,
            spi_in,
            in_shiftdir=rp2.PIO.SHIFT_LEFT,
            push_thresh=8,
            in_base=mosi,
            jmp_pin=sck,
        )
        if self._io:
            # Output (MISO) SM
            # Write DMA
            self._wdma = rp2.DMA()
            self._wcfg = self._wdma.pack_ctrl(size=0, inc_write=False, treq_sel=dreq(sm_num + 1))
            self._osm = rp2.StateMachine(
                sm_num + 1,
                spi_out,
                pull_thresh=8,
                in_base=mosi,
                out_base=miso,
            )

    def __aiter__(self):  # Asynchronous iterator support
        return self

    async def __anext__(self):
        self._bufcheck()  # Ensure there is a valid buffer
        self._rinto(self._buf)  # Initiate DMA and return.
        await self._tsf.wait()  # Wait for CS/ high (master signals transfer complete)
        return self._mvb[: self._nbytes]

    def _bufcheck(self):
        if self._buf is None:
            raise OSError("No buffer provided to constructor.")

    def read(self):  # Blocking read, own buffer
        self._bufcheck()
        self._read_done = False
        self._rinto(self._buf)
        while not self._read_done:
            pass
        return self._mvb[: self._nbytes]

    # Initiate a nonblocking read into a buffer. Immediate return.
    def read_into(self, buf):
        if self._callback is not None:
            self._docb = True
            self._rinto(buf)
        else:
            raise ValueError("Missing callback function.")

    # Queue a buffer for transmission.
    def write(self, buf):
        if not self._io:
            raise ValueError("Write error: no MISO specified.")
        self._wq.append(buf[:])  # Copy in case caller modifies before it's sent

    def _rinto(self, buf):  # .read_into() without callback
        buflen = len(buf)
        self._buflen = buflen  # Save for ISR
        self._dma.active(0)  # De-activate befor re-configuring
        self._sm.active(0)
        self._tsf.clear()
        self._dma.config(read=self._sm, write=buf, count=buflen, ctrl=self._cfg)
        if self._io:
            self._wdma.active(0)
            self._osm.active(0)
            if len(self._wq):  # Queue is not empty
                wb = self._wq.pop(0)  # Assign oldest message to write buffer
                # Write buffer can be bigger than read buf. SPI interface causes write data
                # to be truncated to length of data sent by master.
                n = len(wb)
                print("sending", n, wb[:n])
                self._wdma.config(read=wb, write=self._osm, count=n, ctrl=self._wcfg, trigger=True)
                self._wdma.active(1)
                self._osm.restart()  # osm waits for CS/ low
                self._osm.active(1)

        self._dma.active(1)
        self._sm.restart()
        self._sm.active(1)  # Start SM
        self._sm.put(buflen, 3)  # Number of expected bits

    # Hard ISR for CS/ rising edge.
    # This is dependent on the integrity of the logic signals. Poor wiring can cause
    # spurious IRQ's and erratic SM behaviour leading to invalid data, memfails, etc.
    def _done(self, _):  # Get no. of bytes received.
        self._dma.active(0)
        if self._io:
            self._wdma.active(0)
        self._sm.put(0)  # Request no. of received bits
        if not self._sm.rx_fifo():  # Occurs if ._rinto() never called while CSN is low:
            # master has sent data that was never read. A transmission was missed.
            print("Missed TX?")
            return  # ISR runs on trailing edge but SM is not running. Nothing to do.
        # See above comment re memfails on next line
        sp = self._sm.get() >> 3  # Bits->bytes: space left in buffer or 7ffffff on overflow
        self._nbytes = self._buflen - sp if sp != 0x07FF_FFFF else self._buflen
        self._dma.active(0)
        self._sm.active(0)
        self._tsf.set()
        self._read_done = True
        if self._docb:  # Only run CB if user has called .read_into()
            self._docb = False
            schedule(self._callback, self._nbytes)  # Soft ISR

    # Await a read into a user-supplied buffer. Return no. of bytes read.
    async def as_read_into(self, buf):
        self._rinto(buf)  # Start the read
        await self._tsf.wait()  # Wait for CS/ high (master signals transfer complete)
        return self._nbytes

    def deinit(self):
        self._dma.active(0)
        self._dma.close()
        self._csn.irq(None)
        if self._io:
            self._wdma.active(0)
            self._wdma.close()
            self._osm.active(0)
        self._sm.active(0)
