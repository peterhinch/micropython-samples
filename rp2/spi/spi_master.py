# spi_mater.py A nonblocking SPI master for RP2040/RP2350
# Inspired by
# https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_spi.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

# API
# .write() is the only way to send data. If constucted with an input buffer, any data
# received from the slave (MISO) will be captured. Incoming data is truncated to fit buffer.

import rp2
from micropython import alloc_emergency_exception_buf

alloc_emergency_exception_buf(100)

# Output-only SM
@rp2.asm_pio(autopull=True, pull_thresh=8, sideset_init=rp2.PIO.OUT_LOW, out_init=rp2.PIO.OUT_LOW)
def spi_out():
    wrap_target()
    set(x, 7).side(0x0)
    label("bitloop")
    out(pins, 1).side(0x0)  # Stalls with CLK low while FIFO is empty
    jmp(x_dec, "bitloop").side(0x1)
    wrap()


# Version accepts incoming data
@rp2.asm_pio(
    autopull=True,
    autopush=True,
    pull_thresh=8,
    push_thresh=8,
    sideset_init=rp2.PIO.OUT_LOW,
    out_init=rp2.PIO.OUT_LOW,
)
def spi_inout():
    wrap_target()
    set(x, 7).side(0x0)
    label("bitloop")
    out(pins, 1).side(0x0)  # Stalls with CLK low while FIFO is empty
    mov(y, y).side(0x1)  # Set clock high
    in_(pins, 1).side(0x1)
    jmp(x_dec, "bitloop").side(0x0)
    wrap()


# Get data request channel for a SM: RP2040 datasheet 2.5.3 RP2350 12.6.4.1
def dreq(sm, rx=False):
    d = (sm & 3) + ((sm >> 2) << 3)
    return 4 + d if rx else d


# The callback runs when DMA is complete. This may be up to four byte times prior to
# the SM running out of data (FIFO depth).
class SpiMaster:
    def __init__(self, sm_num, freq, sck, mosi, callback, *, miso=None, ibuf=None):
        self._sm_num = sm_num
        self._cb = callback
        self._dma = rp2.DMA()
        self._dma.irq(handler=self._done, hard=True)  # Assign callback
        dc = dreq(sm_num)  # Data request channel
        # Transfer bytes, don't increment the write address, irq at end, and pace the transfer.
        self._ctrl = self._dma.pack_ctrl(size=0, inc_write=False, irq_quiet=False, treq_sel=dc)
        self._io = 0 if ibuf is None else len(ibuf)
        self._ibuf = ibuf
        if ibuf is None:  # Output only
            f = 2 * freq  # 2 clock cycles per bit
            self._sm = rp2.StateMachine(sm_num, spi_out, freq=f, sideset_base=sck, out_base=mosi)
            self._sm.active(1)
        else:
            # I/O
            f = 4 * freq  # 4 cycles per bit
            self._sm = rp2.StateMachine(
                sm_num,
                spi_inout,
                freq=f,
                sideset_base=sck,
                out_base=mosi,
                in_base=miso,
            )
            self._idma = rp2.DMA()
            dc = dreq(sm_num, True)  # Data in
            self._ictrl = self._idma.pack_ctrl(
                size=0, inc_read=False, irq_quiet=False, treq_sel=dc
            )
        # self._idma.irq(self._done)
        self._sm.active(1)

    def _done(self, dma):  # I/O transfer complete
        self._dma.active(0)
        self._sm.restart()
        if self._io:
            self._idma.active(0)
        self._sm.active(0)
        self._cb()
        # callback = self._cb
        # callback()

    def write(self, data):
        ld = len(data)
        self._dma.config(read=data, write=self._sm, count=ld, ctrl=self._ctrl)
        self._dma.active(1)
        if self._io:
            cnt = min(ld, self._io)  # Prevent overrun of ibuf
            self._idma.config(read=self._sm, write=self._ibuf, count=cnt, ctrl=self._ictrl)
            self._idma.active(1)
        self._sm.active(1)  # Start SM

    def deinit(self):
        self._dma.close()
        self._sm.active(0)
        if self._io:
            self._idma.close()
