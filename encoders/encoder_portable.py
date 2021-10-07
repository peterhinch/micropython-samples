# encoder_portable.py

# Encoder Support: this version should be portable between MicroPython platforms
# Thanks to Evan Widloski for the adaptation to use the machine module

# Copyright (c) 2017-2021 Peter Hinch
# Released under the MIT License (MIT) - see LICENSE file

from machine import Pin

class Encoder:
    def __init__(self, pin_a, pin_b, scale=1):
        self.scale = scale
        self.forward = True
        self.pin_a = pin_a
        self.pin_b = pin_b
        self._pos = 0
        try:
            self.a_interrupt = pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.a_callback, hard=True)
            self.b_interrupt = pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.b_callback, hard=True)
        except TypeError:
            self.a_interrupt = pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.a_callback)
            self.b_interrupt = pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.b_callback)

    def x_callback(self, pin):
        self.forward = pin() ^ self.pin_b()
        self._pos += 1 if self.forward else -1

    def y_callback(self, pin):
        self.forward = self.pin_a() ^ pin() ^ 1
        self._pos += 1 if self.forward else -1

    def position(self, value=None):
        if value is not None:
            self._pos = value // self.scale
        return self._pos * self.scale
