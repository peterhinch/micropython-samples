# slider.py Vertical and horizontal slider control classes for Pyboard TFT GUI

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

# A slider's text items lie outside its bounding box (area sensitive to touch)

from ui import Touchable, get_stringsize
import TFT_io

class Slider(Touchable):
    def __init__(self, objsched, tft, objtouch, location, font, *, height=200, width=30, divisions=10, legends=None,
                 fgcolor=None, bgcolor=None, fontcolor=None, slidecolor=None, border=None, 
                 cb_end=lambda x, y : None, cbe_args=[], cb_move=lambda x, y : None, cbm_args=[], value=0.0):
        super().__init__(objsched, tft, objtouch, location, font, height, width, fgcolor, bgcolor, fontcolor, border)
        self.divisions = divisions
        self.legends = legends
        self.slidecolor = slidecolor
        self.cb_end = cb_end
        self.cbe_args = cbe_args
        self.cb_move = cb_move
        self.cbm_args = cbm_args
        self.was_touched = False
        slidewidth = int(width / 1.3) & 0xfe # Ensure divisible by 2
        self.slideheight = 6 # must be divisible by 2
                             # We draw an odd number of pixels:
        self.slidebytes = (self.slideheight + 1) * (slidewidth + 1) * 3
        self.slidebuf = bytearray(self.slidebytes)
        self._old_value = -1 # Invalidate
        b = self.border
        self.pot_dimension = self.height - 2 * (b + self.slideheight // 2)
        width = self.width - 2 * b
        xcentre = self.location[0] + b + width // 2
        self.slide_x0 = xcentre - slidewidth // 2
        self.slide_x1 = xcentre + slidewidth // 2 # slide X coordinates
        self.slide_y = -1 # Invalidate old position
        self.value(value)

    def show(self):
        tft = self.tft
        bw = self.draw_border() # and background if required. Result is width of border
        x = self.location[0] + bw
        y = self.location[1] + bw + self.slideheight // 2 # Allow space above and below slot
        width = self.width - 2 * bw
        self.set_color()
        height = self.pot_dimension # Height of slot
        dx = width / 3
        tft.drawRectangle(x + dx, y, x + 2 * dx, y + height)

        if self.divisions > 0:
            dy = height / (self.divisions) # Tick marks
            for tick in range(self.divisions + 1):
                ypos = int(y + dy * tick)
                tft.drawHLine(x + 1, ypos, dx)
                tft.drawHLine(x + 1 + 2 * dx, ypos, dx)

        if self.legends is not None: # Legends
            tft.setTextStyle(self.fontcolor, None, 2, self.font)
            if len(self.legends) <= 1:
                dy = 0
            else:
                dy = height / (len(self.legends) -1)
            yl = y + height # Start at bottom
            fhdelta = self.font.bits_vert / 2
            for legend in self.legends:
                tft.setTextPos(x + self.width, int(yl - fhdelta))
                tft.printString(legend)
                yl -= dy

        sh = self.slideheight # Handle slider
        x0 = self.slide_x0
        y0 = self.slide_y
        x1 = self.slide_x1
        y1 = y0 + sh
        if self.slide_y >= 0: # Restore background
            tft.setXY(x0, y0, x1, y1)
            TFT_io.tft_write_data_AS(self.slidebuf, self.slidebytes)
        sliderpos = int(y + height - self._value * height)
        y0 = sliderpos - sh // 2
        y1 = sliderpos + sh // 2
        tft.setXY(x0, y0, x1, y1) # Read background
        TFT_io.tft_read_cmd_data_AS(0x2e, self.slidebuf, self.slidebytes)
        self.slide_y = y0
        if self.slidecolor is not None:
            self.set_color(self.slidecolor)
        tft.fillRectangle(x0, y0, x1, y1) # Draw slider
        self.restore_color()

    def value(self, val=None):
        if val is None:
            return self._value
        self._value = min(max(val, 0.0), 1.0)
        if self._value != self._old_value:
            self._old_value = self._value
            self.cb_move(self, self.cbm_args) # Callback not a bound method so pass self
            self.show()

    def touched(self, x, y): # If touched in bounding box, process it otherwise do nothing
        x0 = self.location[0]
        x1 = self.location[0] + self.width
        y0 = self.location[1]
        y1 = self.location[1] + self.height
        if x0 <= x <= x1 and y0 <= y <= y1:
            self.was_touched = True
            self.value((y1 - y) / self.pot_dimension)

    def untouched(self): # User has released touchpad or touched elsewhere
        if self.was_touched:
            self.cb_end(self, self.cbe_args) # Callback not a bound method so pass self
            self.was_touched = False

class HorizSlider(Touchable):
    def __init__(self, objsched, tft, objtouch, location, font, *, height=30, width=200, divisions=10, legends=None,
                 fgcolor=None, bgcolor=None, fontcolor=None, slidecolor=None, border=None, 
                 cb_end=lambda x, y : None, cbe_args=[], cb_move=lambda x, y : None, cbm_args=[], value=0.0):
        super().__init__(objsched, tft, objtouch, location, font, height, width, fgcolor, bgcolor, fontcolor, border)
        self.divisions = divisions
        self.legends = legends
        self.slidecolor = slidecolor
        self.cb_end = cb_end
        self.cbe_args = cbe_args
        self.cb_move = cb_move
        self.cbm_args = cbm_args
        self.was_touched = False
        slideheight = int(height / 1.3) & 0xfe # Ensure divisible by 2
        self.slidewidth = 6 # must be divisible by 2
                             # We draw an odd number of pixels:
        self.slidebytes = (slideheight + 1) * (self.slidewidth + 1) * 3
        self.slidebuf = bytearray(self.slidebytes)
        self._old_value = -1 # Invalidate
        b = self.border
        self.pot_dimension = self.width - 2 * (b + self.slidewidth // 2)
        height = self.height - 2 * b
        ycentre = self.location[1] + b + height // 2
        self.slide_y0 = ycentre - slideheight // 2
        self.slide_y1 = ycentre + slideheight // 2 # slide Y coordinates
        self.slide_x = -1 # Invalidate old position
        self.value(value)

    def show(self):
        tft = self.tft
        bw = self.draw_border() # and background if required. Result is width of border
        x = self.location[0] + bw + self.slidewidth // 2 # Allow space left and right slot for slider at extremes
        y = self.location[1] + bw
        height = self.height - 2 * bw
        self.set_color()
        width = self.pot_dimension # Length of slot
        dy = height / 3
        ycentre = y + height // 2
        tft.drawRectangle(x, y + dy, x + width, y + 2 * dy)

        if self.divisions > 0:
            dx = width / (self.divisions) # Tick marks
            for tick in range(self.divisions + 1):
                xpos = int(x + dx * tick)
                tft.drawVLine(xpos, y + 1, dy) # TODO Why is +1 fiddle required here?
                tft.drawVLine(xpos, y + 1 + 2 * dy,  dy) # and here

        if self.legends is not None: # Legends
            tft.setTextStyle(self.fontcolor, None, 2, self.font)
            if len(self.legends) <= 1:
                dx = 0
            else:
                dx = width / (len(self.legends) -1)
            xl = x
            for legend in self.legends:
                offset = get_stringsize(legend, self.font)[0] / 2
                tft.setTextPos(int(xl - offset), y - self.font.bits_vert) # Arbitrary left shift should be char width /2
                tft.printString(legend)
                xl += dx

        sw = self.slidewidth # Handle slider
        x0 = self.slide_x
        y0 = self.slide_y0
        x1 = x0 + sw
        y1 = self.slide_y1
        if self.slide_x >= 0: # Restore background
            tft.setXY(x0, y0, x1, y1)
            TFT_io.tft_write_data_AS(self.slidebuf, self.slidebytes)
        sliderpos = int(x + self._value * width)
        x0 = sliderpos - sw // 2
        x1 = sliderpos + sw // 2
        tft.setXY(x0, y0, x1, y1) # Read background
        TFT_io.tft_read_cmd_data_AS(0x2e, self.slidebuf, self.slidebytes)
        self.slide_x = x0
        if self.slidecolor is not None:
            self.set_color(self.slidecolor)
        tft.fillRectangle(x0, y0, x1, y1) # Draw slider
        self.restore_color()

    def value(self, val=None):
        if val is None:
            return self._value
        self._value = min(max(val, 0.0), 1.0)
        if self._value != self._old_value:
            self._old_value = self._value
            self.cb_move(self, self.cbm_args) # Callback not a bound method so pass self
            self.show()

    def touched(self, x, y): # If touched in bounding box, process it otherwise do nothing
        x0 = self.location[0]
        x1 = self.location[0] + self.width
        y0 = self.location[1]
        y1 = self.location[1] + self.height
        if x0 <= x <= x1 and y0 <= y <= y1:
            self.was_touched = True
            self.value((x - x0) / self.pot_dimension)

    def untouched(self): # User has released touchpad or touched elsewhere
        if self.was_touched:
            self.cb_end(self, self.cbe_args) # Callback not a bound method so pass self
            self.was_touched = False
