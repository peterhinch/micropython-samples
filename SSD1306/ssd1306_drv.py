# ssd1306_drv.py An implementation of a Display class for SSD1306 based displays
# V0.1 Peter Hinch Nov 2016

# https://learn.adafruit.com/monochrome-oled-breakouts/wiring-128x32-spi-oled-display
# https://www.proto-pic.co.uk/monochrome-128x32-oled-graphic-display.html

# Version supports vertical and "horizontal" modes.

# The MIT License (MIT)
#
# Copyright (c) 2016 Peter Hinch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# SSD1306 classes to fix the official one whose scroll method is broken
# This also demonstrates a way to do scrolling for devices with true vertical
# mapping (the official driver sets the device into its "horizontal" mode).
# This is a hybrid mode where bytes are aligned vertically but arranged
# horizontally

import ssd1306

class SSD1306(object):
    def __init__(self, device):
        self.width = device.width  # In pixels
        self.height = device.height
        self.bpc = (self.height + 7) >> 3
        self.device = device
        self.vmap = False  # Currently the official driver uses "horizontal"

    @property
    def buffer(self):  # property emulates underlying device
        return self.device.buffer

    def show(self):
        self.device.show()

    # Return map-independent offset into buffer
    def _offset(self, x, y):
        if self.vmap:
            return y + x * self.bpc
        else:
            return y * self.width + x

    def scroll(self, x, y):
        dy = abs(y)
        if dy:
            self._scrolly(dy, y > 0)
        dx = abs(x)
        if dx:
            self._scrollx(dx, x > 0)

    def _scrolly(self, ystep, down):
        buf = self.device.buffer
        bpc = self.bpc
        ystep_bytes = (ystep >> 3) + 1
        ystep_bits = ystep & 7
        if down:
            for x in range(self.width):
                for ydest in range(bpc - 1, -1, -1):
                    ysource = ydest - ystep_bytes
                    data = 0
                    if ysource + 1 >= 0:
                        data = buf[self._offset(x, ysource + 1)] << ystep_bits
                    if ysource >= 0:
                        data |= buf[self._offset(x, ysource)] >> 8 - ystep_bits
                    buf[self._offset(x, ydest)] = data
        else:
            for x in range(self.width):
                for ydest in range(bpc):
                    ysource = ydest + ystep_bytes
                    data = 0
                    if ysource < bpc:
                        data = buf[self._offset(x, ysource)] << (8-ystep_bits)
                    if ysource - 1 < bpc:
                        data |= buf[self._offset(x, ysource - 1)] >> ystep_bits
                    buf[self._offset(x, ydest)] = data

    def _scrollx(self, xstep, right):  # scroll x
        buf = self.device.buffer
        bpc = self.bpc
        for y in range(bpc):
            if right:  # Scroll right
                for xdest in range(self.width - 1, -1, -1):
                    data = 0
                    xsource = xdest - xstep
                    if xsource >= 0:
                        data = buf[self._offset(xsource, y)]
                    buf[self._offset(xdest, y)] = data
            else:
                for xdest in range(0, self.width):
                    data = 0
                    xsource = xdest + xstep
                    if xsource < self.width:
                        data = buf[self._offset(xsource, y)]
                    buf[self._offset(xdest, y)] = data

class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3c, external_vcc=False):
        device = ssd1306.SSD1306_I2C(width, height, i2c, addr, external_vcc)
        super().__init__(device)

class SSD1306_SPI(SSD1306):
    def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
        device = ssd1306.SSD1306_SPI(width, height, spi, dc, res, cs, external_vcc)
        super().__init__(device)
