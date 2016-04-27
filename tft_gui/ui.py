# ui.py Constants, base classes and utilities for Pybboard TFT GUI

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

CIRCLE = 1
RECTANGLE = 2
CLIPPED_RECT = 3
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREY = (100, 100, 100)

def get_stringsize(s, font):
    hor = 0
    for c in s:
        _, vert, cols = font.get_ch(ord(c))
        hor += cols
    return hor, vert

def print_centered(tft, x, y, s, color, font):
    length, height = get_stringsize(s, font)
    tft.setTextStyle(color, None, 2, font)
    tft.setTextPos(x - length // 2, y - height // 2)
    tft.printString(s)

# Base class for all displayable objects
class NoTouch(object):
    old_color = None
    def __init__(self, tft, location, font, height, width, fgcolor, bgcolor, fontcolor, border):
        self.tft = tft
        self.location = location
        self.font = font
        self.height = height
        self.width = width
        self.fill = bgcolor is not None
        self.fgcolor = fgcolor if fgcolor is not None else tft.getColor()
        self.bgcolor = bgcolor if bgcolor is not None else tft.getBGColor()
        self.fontcolor = fontcolor if fontcolor is not None else tft.getColor()
        self.hasborder = border is not None
        self.border = 0 if border is None else border
        if NoTouch.old_color is None:
            NoTouch.old_color = tft.getColor()
        if height is not None and width is not None: # beware special cases where height and width not yet known
            self.draw_border()

    def draw_border(self): # Draw background and bounding box if required
        tft = self.tft
        fgcolor = tft.getColor()
        x = self.location[0]
        y = self.location[1]
        if self.fill:
            tft.setColor(self.bgcolor)
            tft.fillRectangle(x, y, x + self.width, y + self.height)
        bw = 0 # border width
        if self.hasborder: # Draw a bounding box
            bw = self.border
            tft.setColor(self.fgcolor)
            tft.drawRectangle(x, y, x + self.width, y + self.height)
        tft.setColor(fgcolor)
        return bw # Actual width (may be 0)

    def set_color(self, color=None):
        new = self.fgcolor if color is None else color
        self.tft.setColor(new)

    def restore_color(self): # Restore to system default
        self.tft.setColor(NoTouch.old_color)

# Base class for touch-enabled classes.
class Touchable(NoTouch):
    touchlist = []
    objtouch = None

    @classmethod
    def touchtest(cls): # Singleton thread tests all touchable instances
        mytouch = cls.objtouch
        while True:
            yield
            if mytouch.ready:
                x, y = mytouch.get_touch_async()
                for obj in cls.touchlist:
                    if obj.enabled:
                        obj.touched(x, y)
            elif not mytouch.touched:
                for obj in cls.touchlist:
                    obj.untouched()

    def __init__(self, objsched, tft, objtouch, location, font, height, width, fgcolor, bgcolor, fontcolor, border):
        super().__init__(tft, location, font, height, width, fgcolor, bgcolor, fontcolor, border)
        Touchable.touchlist.append(self)
        self.enabled = True # Available to user/subclass
        self.objsched = objsched
        if Touchable.objtouch is None: # Initialising class and thread
            Touchable.objtouch = objtouch
            objsched.add_thread(self.touchtest()) # One thread only
