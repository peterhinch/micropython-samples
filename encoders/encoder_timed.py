# encoder_timed.py

# Copyright (c) 2016-2021 Peter Hinch
# Released under the MIT License (MIT) - see LICENSE file
# Improvements provided by IhorNehrutsa

import utime
from machine import Pin, disable_irq, enable_irq

class EncoderTimed:
    def __init__(self, pin_x, pin_y, scale=1):
        self.scale = scale  # Optionally scale encoder rate to distance/angle
        self.tprev = -1
        self.tlast = -1
        self.forward = True
        self.pin_x = pin_x
        self.pin_y = pin_y
        self._pos = 0
        try:
            self.x_interrupt = pin_x.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.x_callback, hard=True)
            self.y_interrupt = pin_y.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.y_callback, hard=True)
        except TypeError:
            self.x_interrupt = pin_x.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.x_callback)
            self.y_interrupt = pin_y.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.y_callback)

    def x_callback(self, line):
        self.forward = self.pin_x.value() ^ self.pin_y.value()
        self._pos += 1 if self.forward else -1
        self.tprev = self.tlast
        self.tlast = utime.ticks_us()

    def y_callback(self, line):
        self.forward = self.pin_x.value() ^ self.pin_y.value() ^ 1
        self._pos += 1 if self.forward else -1
        self.tprev = self.tlast
        self.tlast = utime.ticks_us()

    def rate(self):  # Return rate in signed distance/angle per second
        state = disable_irq()
        tlast = self.tlast  # Cache current values
        tprev = self.tprev
        enable_irq(state)
        if self.tprev == -1:  # No valid times yet
            return 0.0
        dt = utime.ticks_diff(utime.ticks_us(), tlast)
        if dt > 2_000_000: # Stopped
            return 0.0
        dt = utime.ticks_diff(tlast, tprev)
        if dt == 0:  # Could happen on future rapid hardware
            return 0.0
        result = self.scale * 1_000_000.0/dt
        return result if self.forward else -result

    def position(self, value=None):
        if value is not None:
            self._pos = round(value / self.scale)
        return self._pos * self.scale

    def reset(self):
        self._pos = 0

    def value(self, value=None):
        if value is not None:
            self._pos = value
        return self._pos
