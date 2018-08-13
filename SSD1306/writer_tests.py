# ssd1306_test.py Demo pogram for rendering arbitrary fonts to an SSD1306 OLED display.

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

# V0.3 12th Aug 2018

import machine
import utime
from ssd1306_setup import WIDTH, HEIGHT, setup
from writer import Writer, CWriter

# Fonts
import freesans20
import courier20 as fixed

def inverse(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    rhs = WIDTH -1
    ssd.line(rhs - 20, 0, rhs, 20, 1)
    square_side = 10
    ssd.fill_rect(rhs - square_side, 0, square_side, square_side, 1)

    Writer.set_textpos(0, 0)  # In case previous tests have altered it
    Writer.set_clip(False, False, False)  # Char wrap
    wri = Writer(ssd, freesans20, verbose=False)
    wri.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am', True)  # Inverse text
    ssd.show()

def scroll(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    rhs = WIDTH -1
    ssd.line(rhs - 20, 0, rhs, 20, 1)
    square_side = 10
    ssd.fill_rect(rhs - square_side, 0, square_side, square_side, 1)

    Writer.set_textpos(0, 0)  # In case previous tests have altered it
    Writer.set_clip(False, False, False)  # Char wrap
    wri = Writer(ssd, freesans20, verbose=False)
    wri.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am')
    for x in range(5):
        ssd.show()
        utime.sleep(2)
        wri.printstring('\nCount = {:2d}'.format(x))
    ssd.show()
    utime.sleep(2)
    wri.printstring('\nDone.')
    ssd.show()

def usd_scroll(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    # Only CWriter can do usd
    CWriter.invert_display()
    CWriter.set_textpos(HEIGHT - 1, WIDTH - 1)
    CWriter.set_clip(False, False, False)  # Char wrap
    wri = CWriter(ssd, freesans20, verbose=False)

    wri.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am')
    for x in range(5):
        ssd.show()
        utime.sleep(2)
        wri.printstring('\nCount = {:2d}'.format(x))
    ssd.show()
    utime.sleep(2)
    wri.printstring('\nDone.')
    ssd.show()
    CWriter.invert_display(False)  # For subsequent tests

def usd(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    # Only CWriter can do usd
    CWriter.invert_display()
    CWriter.set_textpos(HEIGHT - 1, WIDTH - 1)
    CWriter.set_clip(False, False, False)  # Char wrap
    wri = CWriter(ssd, freesans20, verbose=False)
    wri.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am')
    ssd.show()
    CWriter.invert_display(False)  # For subsequent tests

def rjust(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    Writer.set_textpos(0, 0)  # Previous tests may have altered it
    Writer.set_clip(False, False, False)  # Char wrap
    wri = Writer(ssd, freesans20, verbose=False)

    my_str = 'Sunday\n'
    l = wri.stringlen(my_str)
    Writer.set_textpos(col = WIDTH - l)
    wri.printstring(my_str)

    my_str = '12 Aug 2018\n'
    l = wri.stringlen(my_str)
    Writer.set_textpos(col = WIDTH - l)
    wri.printstring(my_str)

    my_str = '10.30am'
    l = wri.stringlen(my_str)
    Writer.set_textpos(col = WIDTH - l)
    wri.printstring(my_str)
    ssd.show()

def fonts(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    Writer.set_textpos(0, 0)  # In case previous tests have altered it
    Writer.set_clip(False, False, False)  # Char wrap
    wri = Writer(ssd, freesans20, verbose=False)
    wri_f = Writer(ssd, fixed, verbose=False)
    wri_f.printstring('Sunday\n')
    wri.printstring('12 Aug 2018\n')
    wri.printstring('10.30am')
    ssd.show()

def tabs(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    CWriter.set_textpos(0, 0)  # In case previous tests have altered it
    CWriter.set_clip(False, False, False)  # Char wrap
    wri = CWriter(ssd, fixed, verbose=False)
    wri.printstring('1\t2\n')
    wri.printstring('111\t22\n')
    wri.printstring('1111\t1')
    ssd.show()

def usd_tabs(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    CWriter.invert_display()
    CWriter.set_textpos(HEIGHT - 1, WIDTH - 1)
    CWriter.set_clip(False, False, False)  # Char wrap
    wri = CWriter(ssd, fixed, verbose=False)
    wri.printstring('1\t2\n')
    wri.printstring('111\t22\n')
    wri.printstring('1111\t1')
    ssd.show()
    CWriter.invert_display(False)  # For subsequent tests

def wrap(use_spi=False, soft=True):
    ssd = setup(use_spi, soft)  # Create a display instance
    CWriter.set_textpos(0, 0)  # In case previous tests have altered it
    CWriter.set_clip(False, False, True)  # Word wrap
    wri = CWriter(ssd, freesans20, verbose=False)
    wri.printstring('the quick brown fox jumps over')
    ssd.show()

tstr = '''Test assumes a 128*64 (w*h) display. Edit WIDTH and HEIGHT in ssd1306_setup.py for others.
Device pinouts are comments in ssd1306_setup.py.
All tests take two boolean args:
use_spi = False. Set True for SPI connected device
soft=True set False to use hardware I2C/SPI. Hardware option currently fails with official SSD1306 driver.

Available tests:
inverse() Show black on white text.
scroll() Illustrate scrolling
usd() Upside-down display.
usd_scroll() Upside-down scroll test.
rjust() Right justification.
fonts() Two fonts.
tabs() Tab stops.
usd_tabs() Upside-down tabs.
wrap() Word wrapping'''

print(tstr)
