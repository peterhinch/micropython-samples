# encoder_portable.py

# Encoder Support: this version should be portable between MicroPython platforms
# Thanks to Evan Widloski for the adaptation to use the machine module

# Copyright (c) 2017-2021 Peter Hinch
# Released under the MIT License (MIT) - see LICENSE file

from machine import Pin


class Encoder:
    def __init__(self, pin_a, pin_b, scale=1):
        self.scale = scale  # Optionally scale encoder rate to distance/angle
        self.pin_a = pin_a
        self.pin_b = pin_b
        self._pos = 0
        try:
            self.a_interrupt = pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.a_callback, hard=True)
            self.b_interrupt = pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.b_callback, hard=True)
        except TypeError:
            self.a_interrupt = pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.a_callback)
            self.b_interrupt = pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.b_callback)

    def a_callback(self, pin):
        self._pos += 1 if (pin() ^ self.pin_b()) else -1

    def b_callback(self, pin):
        self._pos += 1 if (self.pin_a() ^ pin() ^ 1) else -1

    def position(self, value=None):
        if value is not None:
            self._pos = round(value / self.scale)
        return self._pos * self.scale

    def value(self):
        return self._pos

    def set_value(self, value):
        self._pos = value
