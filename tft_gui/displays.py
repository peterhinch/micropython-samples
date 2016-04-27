# displays.py Non touch sensitive display elements for Pyboard TFT GUI

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

from ui import print_centered, NoTouch, BLACK, RED
import math
import TFT_io

class Label(NoTouch):
    def __init__(self, tft, location, *, font, border=None, width, fgcolor=None, bgcolor=None, fontcolor=None, text=''):
        super().__init__(tft, location, font, None, width, fgcolor, bgcolor, fontcolor, border)
        self.height = self.font.bits_vert
        self.height += 2 * self.border  # Height determined by font and border
        self.draw_border() # Must explicitly draw because ctor did not have height
        self.show(text)

    def show(self, text):
        tft = self.tft
        bw = self.border
        if text:
            x = self.location[0]
            y = self.location[1]
            self.set_color(self.bgcolor)
            tft.fillRectangle(x + bw, y + bw, x + self.width - bw, y + self.height - bw)
            tft.setTextStyle(self.fontcolor, None, 2, self.font)
            tft.setTextPos(x + bw, y + bw, clip = self.width - 2 * bw, scroll = False)
            tft.printString(text)
            self.restore_color() # restore fg color

# class displays angles
class Dial(NoTouch):
    def __init__(self, tft, location, *, height=100, fgcolor=None, bgcolor=None, border=None, pointers=(0.9,), ticks=4):
        NoTouch.__init__(self, tft, location, None, height, height, fgcolor, bgcolor, None, border) # __super__ provoked Python bug
        border = self.border # border width
        radius = height / 2 - border
        self.radius = radius
        self.xorigin = location[0] + border + radius
        self.yorigin = location[1] + border + radius
        self.pointers = tuple(z * self.radius for z in pointers) # Pointer lengths
        self.angles = [None for _ in pointers]
        self.set_color() # set fg color
        ticklen = 0.1 * radius
        for tick in range(ticks):
            theta = 2 * tick * math.pi / ticks
            x_start = int(self.xorigin + radius * math.sin(theta))
            y_start = int(self.yorigin - radius * math.cos(theta))
            x_end = int(self.xorigin + (radius - ticklen) * math.sin(theta))
            y_end = int(self.yorigin - (radius - ticklen) * math.cos(theta))
            self.tft.drawLine(x_start, y_start, x_end, y_end)
        tft.drawCircle(self.xorigin, self.yorigin, radius)
        self.restore_color()

    def show(self, angle, pointer=0):
        tft = self.tft
        if self.angles[pointer] is not None:
            self.set_color(self.bgcolor)
            self.drawpointer(self.angles[pointer], pointer) # erase old
        self.set_color()
        self.drawpointer(angle, pointer) # draw new
        self.angles[pointer] = angle # update old
        self.restore_color()

    def drawpointer(self, radians, pointer):
        length = self.pointers[pointer]
        x_end = int(self.xorigin + length * math.sin(radians))
        y_end = int(self.yorigin - length * math.cos(radians))
        self.tft.drawLine(int(self.xorigin), int(self.yorigin), x_end, y_end)

class LED(NoTouch):
    def __init__(self, tft, location, *, border=None, height=30, fgcolor=None, bgcolor=None, color=RED):
        super().__init__(tft, location, None, height, height, fgcolor, bgcolor, None, border)
        self.radius = (self.height - 2 * self.border) / 2
        self.x = location[0] + self.radius + self.border
        self.y = location[1] + self.radius + self.border
        self.color = color
        self.off()

    def _show(self, color): # Light the LED 
        self.set_color(color)
        self.tft.fillCircle(int(self.x), int(self.y), int(self.radius))
        self.set_color()
        self.tft.drawCircle(int(self.x), int(self.y), int(self.radius))
        self.restore_color()

    def on(self, color=None): # Light in current color
        if color is not None:
            self.color = color
        self._show(self.color)

    def off(self):
        self._show(BLACK)

class Meter(NoTouch):
    def __init__(self, tft, location, *, font=None, height=200, width=30,
                 fgcolor=None, bgcolor=None, pointercolor=None, fontcolor=None,
                 divisions=10, legends=None, value=0):
        border = 5 if font is None else 1 + font.bits_vert / 2
        NoTouch.__init__(self, tft, location, font, height, width, fgcolor, bgcolor, fontcolor, border) # __super__ provoked Python bug
        border = self.border # border width
        self.ptrbytes = 3 * (self.width + 1) # 3 bytes per pixel
        self.ptrbuf = bytearray(self.ptrbytes) #???
        self.x0 = self.location[0]
        self.x1 = self.location[0] + self.width
        self.y0 = self.location[1] + border + 2
        self.y1 = self.location[1] + self.height - border
        self.divisions = divisions
        self.legends = legends
        self.pointercolor = pointercolor if pointercolor is not None else fgcolor
        self._value = value
        self._old_value = -1 # invalidate
        self.ptr_y = -1 # Invalidate old position
        self.show()

    def show(self):
        tft = self.tft
        bw = self.draw_border() # and background if required. Result is width of border
        width = self.width
        dx = 5
        self.set_color()
        x0 = self.x0
        x1 = self.x1
        y0 = self.y0
        y1 = self.y1
        height = y1 - y0
        if self.divisions > 0:
            dy = height / (self.divisions) # Tick marks
            for tick in range(self.divisions + 1):
                ypos = int(y0 + dy * tick)
                tft.drawHLine(x0, ypos, dx)
                tft.drawHLine(x1 - dx, ypos, dx)

        if self.legends is not None and self.font is not None: # Legends
            tft.setTextStyle(self.fontcolor, None, 2, self.font)
            if len(self.legends) <= 1:
                dy = 0
            else:
                dy = height / (len(self.legends) -1)
            yl = self.y1 # Start at bottom
            for legend in self.legends:
                print_centered(tft, int(self.x0 + self.width /2), int(yl), legend, self.fontcolor, self.font)
                yl -= dy

        y0 = self.ptr_y
        y1 = y0
        if self.ptr_y >= 0: # Restore background
            tft.setXY(x0, y0, x1, y1)
            TFT_io.tft_write_data_AS(self.ptrbuf, self.ptrbytes)
        ptrpos = int(self.y1 - self._value * height)
        y0 = ptrpos
        y1 = ptrpos
        tft.setXY(x0, y0, x1, y1) # Read background
        TFT_io.tft_read_cmd_data_AS(0x2e, self.ptrbuf, self.ptrbytes)
        self.ptr_y = y0
        self.set_color(self.pointercolor)
        tft.drawHLine(x0, y0, width) # Draw pointer
        self.restore_color()

    def value(self, val=None):
        if val is None:
            return self._value
        self._value = min(max(val, 0.0), 1.0)
        if self._value != self._old_value:
            self._old_value = self._value
            self.show()
