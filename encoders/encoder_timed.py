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
            pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.a_callback, hard=True)
            pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.b_callback, hard=True)
        except TypeError:
            pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.a_callback)
            pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.b_callback)

    def a_callback(self, pin):
        self.forward = pin() ^ self.pin_b()
        self._pos += 1 if self.forward else -1
        self.tprev = self.tlast
        self.tlast = utime.ticks_us()

    def b_callback(self, pin):
        self.forward = self.pin_a() ^ pin() ^ 1
        self._pos += 1 if self.forward else -1
        self.tprev = self.tlast
        self.tlast = utime.ticks_us()

    def rate(self):  # Return rate in signed distance/angle per second
        state = disable_irq()
        tlast = self.tlast  # Cache current values
        tprev = self.tprev
        enable_irq(state)
        if utime.ticks_diff(utime.ticks_us(), tlast) > 2_000_000:  # It's stopped
            result = 0.0
        else:
            try:
                result = 1000000.0 / (utime.ticks_diff(tlast, tprev))
            except ZeroDivisionError:
                result = 0.0
        result *= self.scale
        return result if self.forward else -result

    def position(self, value=None):
        if value is not None:
            self._pos = round(value / self.scale)
        return self._pos * self.scale

    def value(self):
        return self._pos

    def set_value(self, value):
        self._pos = value

    def reset(self):
        self._pos = 0
