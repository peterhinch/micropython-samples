# Derived from https://github.com/raspberrypi/pico-micropython-examples/blob/master/pio/pio_spi.py
import rp2
from machine import Pin
import time

# ***** Define connfiguration *****
sm_num = 0
pio_num = 0
freq = 1_000_000
pincs = Pin(20, Pin.OUT)
pin_sck = Pin(18)
pin_mosi = Pin(19)

# ***** Transfer complete callback *****
def callback(dma):
    pincs(1)
    # Flag user code that transfer is complete

# *****

@rp2.asm_pio(autopull=True, pull_thresh=8, sideset_init=(rp2.PIO.OUT_LOW,), out_init=rp2.PIO.OUT_LOW)
def spi_cpha0():
    # Note X must be preinitialised by setup code before first byte, we reload after sending each byte
    set(x, 6)
    # Actual program body follows
    wrap_target()
    pull(ifempty)            .side(0x0)   [1]
    label("bitloop")
    out(pins, 1)             .side(0x0)   [1]
    #mov(y, y)                .side(0x1)
    jmp(x_dec, "bitloop")    .side(0x1)   [1]

    out(pins, 1)             .side(0x0)
    set(x, 6)                .side(0x0)
    mov(y, y)                .side(0x1)  # NOP
    jmp(not_osre, "bitloop") .side(0x1)  # Fallthru if TXFIFO empties
    wrap()

piospi_sm = rp2.StateMachine(sm_num, spi_cpha0, freq=4*freq, sideset_base=pin_sck, out_base=pin_mosi)
piospi_sm.active(1)

DATA_REQUEST_INDEX = (pio_num << 3) + sm_num

d = rp2.DMA()
d.irq(handler=callback, hard=True)  # Assign callback
# Transfer bytes, rather than words, don't increment the write address, irq at end, and pace the transfer.
c = d.pack_ctrl(size=0, inc_write=False, irq_quiet=False, treq_sel=DATA_REQUEST_INDEX)
def send(data):
    pincs(0)  # Assert CS/
    d.config(
        read=data,
        write=piospi_sm,
        count=len(data),
        ctrl=c,
        trigger=True
    )

# ***** Test Script *****
n = 0
while True:
    src_data = b'the quick brown fox jumps over the lazy dog'
    send(src_data)  # "Immediate" return.
    time.sleep(1)
    print(n)
    n += 1
