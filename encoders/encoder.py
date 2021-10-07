# encoder.py

# Copyright (c) 2016-2021 Peter Hinch
# Released under the MIT License (MIT) - see LICENSE file

import pyb

class Encoder:
    def __init__(self, pin_a, pin_b, reverse=0, scale=1):
        self.reverse = reverse
        self.scale = scale  # Optionally scale encoder rate to distance/angle
        self.forward = True
        self.pin_a = pin_a
        self.pin_b = pin_b
        self._pos = 0
        self.a_interrupt = pyb.ExtInt(pin_a, pyb.ExtInt.IRQ_RISING_FALLING, pyb.Pin.PULL_NONE, self.a_callback)
        self.b_interrupt = pyb.ExtInt(pin_b, pyb.ExtInt.IRQ_RISING_FALLING, pyb.Pin.PULL_NONE, self.b_callback)

    def x_callback(self, line):
        self.forward = self.pin_a.value() ^ self.pin_b.value() ^ self.reverse
        self._pos += 1 if self.forward else -1

    def y_callback(self, line):
        self.forward = self.pin_a.value() ^ self.pin_b.value() ^ self.reverse ^ 1
        self._pos += 1 if self.forward else -1

    def position(self, value=None):
        if value is not None:
            self._pos = round(value / self.scale)
        return self._pos*self.scale

    def value(self):
        return self._pos

    def set_value(self, value):
        self._pos = value

    def reset(self):
        self._pos = 0
