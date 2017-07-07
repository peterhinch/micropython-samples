# Encoder Support: this version should be portable between MicroPython platforms
# Thanks to Evan Widloski for the adaptation to the machine module

from machine import Pin

class Encoder(object):
    def __init__(self, pin_x, pin_y, reverse, scale):
        self.reverse = reverse
        self.scale = scale
        self.forward = True
        self.pin_x = pin_x
        self.pin_y = pin_y
        self._pos = 0
        self.x_interrupt = pin_x.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.x_callback)
        self.y_interrupt = pin_y.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.y_callback)

    def x_callback(self, line):
        self.forward = self.pin_x.value() ^ self.pin_y.value() ^ self.reverse
        self._pos += 1 if self.forward else -1

    def y_callback(self, line):
        self.forward = self.pin_x.value() ^ self.pin_y.value() ^ self.reverse ^ 1
        self._pos += 1 if self.forward else -1

    @property
    def position(self):
        return self._pos * self.scale

    @position.setter
    def position(self, value):
        self._pos = value // self.scale

