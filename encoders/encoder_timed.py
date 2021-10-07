# encoder_timed.py

# Copyright (c) 2016-2021 Peter Hinch
# Released under the MIT License (MIT) - see LICENSE file

import utime
from machine import Pin, disable_irq, enable_irq

class EncoderTimed:
    def __init__(self, pin_a, pin_b, scale=1):
        self.scale = scale  # Optionally scale encoder rate to distance/angle
        self.tprev = 0
        self.tlast = 0
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

    def x_callback(self, line):
        self.forward = self.pin_a.value() ^ self.pin_b.value()
        self._pos += 1 if self.forward else -1
        self.tprev = self.tlast
        self.tlast = utime.ticks_us()

    def y_callback(self, line):
        self.forward = self.pin_a.value() ^ self.pin_b.value() ^ 1
        self._pos += 1 if self.forward else -1
        self.tprev = self.tlast
        self.tlast = utime.ticks_us()

    def rate(self):  # Return rate in signed distance/angle per second
        state = disable_irq()
        tlast = self.tlast  # Cache current values
        tprev = self.tprev
        enable_irq(state)
        if utime.ticks_diff(utime.ticks_us(), tlast) > 2_000_000: # It's stopped
            result = 0.0
        else:
            result = 1000000.0/(utime.ticks_diff(tlast, tprev))
        result *= self.scale
        return result if self.forward else -result

    def position(self):
        return self._pos * self.scale

    def reset(self):
        self._pos = 0

