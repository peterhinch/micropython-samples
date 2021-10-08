# encoder_state.py

# Copyright (c) 2021 Ihor Nehrutsa
# Released under the MIT License (MIT) - see LICENSE file


class Encoder:
    def __init__(self, pin_a, pin_b, scale=1, x124=2):
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.scale = scale  # Optionally scale encoder rate to distance/angle
        self.x124 = x124

        self._pos = 0  # raw counter value

        self._state = 0  # encoder state transitions
        if x124 == 1:
            self._x = (0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0)
        elif x124 == 2:
            self._x = (0, 0, 1, 0, 0, 0, 0, -1, -1, 0, 0, 0, 0, 1, 0, 0)
        elif x124 == 4:
            self._x = (0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0)
        else:
            raise ValueError("x124 must be from [1, 2, 4]")

        try:
            self.pin_a.irq(self.callback, hard=True)
            self.pin_b.irq(self.callback, hard=True)
        except TypeError:
            self.pin_a.irq(self.callback)
            self.pin_b.irq(self.callback)

    def deinit(self):
        try:
            self.pin_a.irq(None)
        except:
            pass
        try:
            self.pin_b.irq(None)
        except:
            pass

    def __del__(self):
        self.deinit()

    def __repr__(self):
        return 'Encoder(A={}, B={}, scale={}, x124={})'.format(
            self.pin_a, self.pin_b, self.scale, self.x124)

    def callback(self, pin):
        self._state = ((self._state << 2) + (self.pin_a() << 1) + self.pin_b()) & 0xF
        self._pos += self._x[self._state]

    def position(self, value=None):
        if value is not None:
            self._pos = round(value / self.scale)
        return self._pos * self.scale

    def value(self):
        return self._pos

    def set_value(self, value):
        self._pos = value
