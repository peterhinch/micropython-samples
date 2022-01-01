# encoder_rp2.py Uses the PIO for rapid response on RP2 chips (Pico)

# Copyright (c) 2022 Peter Hinch
# Released under the MIT License (MIT) - see LICENSE file

# PIO and SM code written by Sandor Attila Gerendi (@sanyi)
# https://github.com/micropython/micropython/pull/6894

from machine import Pin
from array import array
import rp2

# Test with encoder on pins 2 and 3:
#e = Encoder(0, Pin(2))

#while True:    
    #time.sleep(1)
    #print(e.value())

# Closure enables Viper to retain state. Currently (V1.17) nonlocal doesn't
# work: https://github.com/micropython/micropython/issues/8086
# so using arrays.
def make_isr(pos):
    old_x = array('i', (0,))
    @micropython.viper
    def isr(sm):
        i = ptr32(pos)
        p = ptr32(old_x)
        while sm.rx_fifo():
            v : int = int(sm.get()) & 3
            x : int = v & 1
            y : int = v >> 1
            s : int = 1 if (x ^ y) else -1
            i[0] = i[0] + (s if (x ^ p[0]) else (0 - s))
            p[0] = x
    return isr

# Args:
# StateMachine no. (0-7): each instance must have a different sm_no.
# An initialised input Pin: this and the next pin are the encoder interface.
class Encoder:
    def __init__(self, sm_no, base_pin, scale=1):
        self.scale = scale
        self._pos = array("i", (0,))  # [pos]
        self.sm = rp2.StateMachine(sm_no, self.pio_quadrature, in_base=base_pin)
        self.sm.irq(make_isr(self._pos))  # Instantiate the closure
        self.sm.exec("set(y, 99)")  # Initialise y: guarantee different to the input
        self.sm.active(1)

    @rp2.asm_pio()
    def pio_quadrature(in_init=rp2.PIO.IN_LOW):
        wrap_target()
        label("again")
        in_(pins, 2)
        mov(x, isr)
        jmp(x_not_y, "push_data")
        mov(isr, null)
        jmp("again")
        label("push_data")
        push()
        irq(block, rel(0))
        mov(y, x)
        wrap()

    def position(self, value=None):
        if value is not None:
            self._pos[0] = round(value / self.scale)
        return self._pos[0] * self.scale

    def value(self, value=None):
        if value is not None:
            self._pos[0] = value
        return self._pos[0]
