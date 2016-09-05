import pyb, utime

class EncoderTimed(object):
    def __init__(self, pin_x, pin_y, reverse, scale):
        self.reverse = reverse
        self.scale = scale
        self.tprev = 0
        self.tlast = 0
        self.forward = True
        self.pin_x = pin_x
        self.pin_y = pin_y
        self._pos = 0
        self.x_interrupt = pyb.ExtInt(pin_x, pyb.ExtInt.IRQ_RISING_FALLING, pyb.Pin.PULL_NONE, self.x_callback)
        self.y_interrupt = pyb.ExtInt(pin_y, pyb.ExtInt.IRQ_RISING_FALLING, pyb.Pin.PULL_NONE, self.y_callback)

    def x_callback(self, line):
        self.forward = self.pin_x.value() ^ self.pin_y.value() ^ self.reverse
        self._pos += 1 if self.forward else -1
        self.tprev = self.tlast
        self.tlast = utime.ticks_us()

    def y_callback(self, line):
        self.forward = self.pin_x.value() ^ self.pin_y.value() ^ self.reverse ^ 1
        self._pos += 1 if self.forward else -1
        self.tprev = self.tlast
        self.tlast = utime.ticks_us()

    @property
    def rate(self):                                         # Return rate in edges per second
        self.x_interrupt.disable()
        self.y_interrupt.disable()
        if utime.ticks_diff(self.tlast, utime.ticks_us) > 2000000: # It's stopped
            result = 0.0
        else:
            result = 1000000.0/(utime.ticks_diff(self.tprev, self.tlast))
        self.x_interrupt.enable()
        self.y_interrupt.enable()
        result *= self.scale
        return result if self.forward else -result

    @property
    def position(self):
        return self._pos*self.scale

    def reset(self):
        self._pos = 0

