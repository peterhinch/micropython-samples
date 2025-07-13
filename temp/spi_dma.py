# spi_dma.py A nonblocking SPI master for RP2040/RP2350
# Inspired by
# https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_spi.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

import rp2


@rp2.asm_pio(autopull=True, pull_thresh=8, sideset_init=rp2.PIO.OUT_LOW, out_init=rp2.PIO.OUT_LOW)
def spi_out():
    wrap_target()
    set(x, 7).side(0x0)
    label("bitloop")
    out(pins, 1).side(0x0)  # Stalls with CLK low while FIFO is empty
    jmp(x_dec, "bitloop").side(0x1)
    wrap()


# Get data request channel for a SM: RP2040 datasheet 2.5.3 RP2350 12.6.4.1
def dreq(sm, rx=False):
    d = (sm & 3) + ((sm >> 2) << 3)
    return 4 + d if rx else d


# The callback runs when DMA is complete. This may be up to four byte times prior to
# the SM running out of data (FIFO depth).
class RP2_SPI_DMA_MASTER:
    def __init__(self, sm_num, freq, sck, mosi, callback):
        self._sm_num = sm_num
        self._dma = rp2.DMA()
        self._dma.irq(handler=callback, hard=True)  # Assign callback
        dc = dreq(sm_num)  # Data request channel
        # Transfer bytes, don't increment the write address, irq at end, and pace the transfer.
        self._ctrl = self._dma.pack_ctrl(size=0, inc_write=False, irq_quiet=False, treq_sel=dc)
        f = 2 * freq  # 2 clock cycles per bit
        self._sm = rp2.StateMachine(sm_num, spi_out, freq=f, sideset_base=sck, out_base=mosi)
        self._sm.active(1)

    def deinit(self):
        self._dma.active(0)
        self._sm.active(0)

    def write(self, data):
        self._dma.config(read=data, write=self._sm, count=len(data), ctrl=self._ctrl, trigger=True)
