# ssd1306_test.py Demo pogram for rendering arbitrary fonts to an SSD1306 OLED display

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


# https://learn.adafruit.com/monochrome-oled-breakouts/wiring-128x32-spi-oled-display
# https://www.proto-pic.co.uk/monochrome-128x32-oled-graphic-display.html

# V0.2 Dec 17th 2016 Now supports updated framebuf module.

import machine
from ssd1306 import SSD1306_SPI, SSD1306_I2C
from writer import Writer

# Fonts
import freesans20
#import freeserif19
#import inconsolata16

WIDTH = const(128)
SPI = False

if SPI:
    # Pyb   SSD
    # 3v3   Vin
    # Gnd   Gnd
    # X1    DC
    # X2    CS
    # X3    Rst
    # X6    CLK
    # X8    DATA
    HEIGHT = 32
    pdc = machine.Pin('X1', machine.Pin.OUT_PP)
    pcs = machine.Pin('X2', machine.Pin.OUT_PP)
    prst = machine.Pin('X3', machine.Pin.OUT_PP)
    spi = machine.SPI(1)
    ssd = SSD1306_SPI(WIDTH, HEIGHT, spi, pdc, prst, pcs)
else:  # I2C
    # Pyb   SSD
    # 3v3   Vin
    # Gnd   Gnd
    # Y9    CLK
    # Y10   DATA
    HEIGHT = 64
    pscl = machine.Pin('Y9', machine.Pin.OUT_PP)
    psda = machine.Pin('Y10', machine.Pin.OUT_PP)
    i2c = machine.I2C(scl=pscl, sda=psda)
    ssd = SSD1306_I2C(WIDTH, HEIGHT, i2c)

#wri = Writer(ssd, freeserif19)
wri2 = Writer(ssd, freesans20)
Writer.set_clip(True, True)
#Writer.set_textpos(20, 20)
#wri2.printstring('Tues')
wri2.printstring('Tuesday\n')
wri2.printstring('8 Nov 2016\n')
wri2.printstring('10.30am')

ssd.show()
