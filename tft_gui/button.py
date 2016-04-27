# button.py Pushbutton classes for Pybboard TFT GUI

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

from delay import Delay
from ui import get_stringsize, print_centered, Touchable, CIRCLE, RECTANGLE, CLIPPED_RECT

# Button coordinates relate to bounding box (BB). x, y are of BB top left corner.
# likewise width and height refer to BB, regardless of button shape
# If font is None button will be rendered without text

class Button(Touchable):
    def __init__(self, objsched, tft, objtouch, location, *, font, shape=CIRCLE, height=50, width=50, fill=True,
                 fgcolor=None, bgcolor=None, fontcolor=None, litcolor=None, text='', show=True, callback=lambda x, y : None,
                 args=[]):
        super().__init__(objsched, tft, objtouch, location, font, height, width, fgcolor, bgcolor, fontcolor, None)
        self.shape = shape
        self.radius = height // 2
        self.fill = fill
        self.litcolor = litcolor
        self.text = text
        self.callback = callback
        self.callback_args = args
        self.orig_fgcolor = fgcolor
        if self.litcolor is not None:
            self.delay = Delay(objsched, self.shownormal)
        self.visible = True # ditto
        self.litcolor = litcolor if self.fgcolor is not None else None
        self.busy = False
        if show:
            self.show()

    def show(self):
        tft = self.tft
        x = self.location[0]
        y = self.location[1]
        if not self.visible:   # erase the button
            self.set_color(self.bgcolor)
            tft.fillRectangle(x, y, x + self.width, y + self.height)
            self.restore_color()
            return
        self.set_color() # to foreground
        if self.shape == CIRCLE:  # Button coords are of top left corner of bounding box
            x += self.radius
            y += self.radius
            if self.fill:
                tft.fillCircle(x, y, self.radius)
            else:
                tft.drawCircle(x, y, self.radius)
            if self.font is not None and len(self.text):
                print_centered(tft, x, y, self.text, self.fontcolor, self.font)
        else:
            x1 = x + self.width
            y1 = y + self.height
            if self.shape == RECTANGLE: # rectangle
                if self.fill:
                    tft.fillRectangle(x, y, x1, y1)
                else:
                    tft.drawRectangle(x, y, x1, y1)
                if self.font  is not None and len(self.text):
                    print_centered(tft, (x + x1) // 2, (y + y1) // 2, self.text, self.fontcolor, self.font)
            elif self.shape == CLIPPED_RECT: # clipped rectangle
                if self.fill:
                    tft.fillClippedRectangle(x, y, x1, y1)
                else:
                    tft.drawClippedRectangle(x, y, x1, y1)
                if self.font  is not None and len(self.text):
                    print_centered(tft, (x + x1) // 2, (y + y1) // 2, self.text, self.fontcolor, self.font)
        self.restore_color()

    def shownormal(self):
        self.fgcolor = self.orig_fgcolor
        self.show()

    def touched(self, x, y): # If touched, process it otherwise do nothing
        is_touched = False
        if self.shape == CIRCLE:
            r = self.radius
            dx = r - (x - self.location[0])
            dy = r - (y - self.location[1])
            if (dx * dx + dy * dy) < (r * r):  # Pythagoras is alive!
                is_touched = True
        elif self.shape in (RECTANGLE, CLIPPED_RECT):  # rectangle
            x0 = self.location[0]
            x1 = self.location[0] + self.width
            y0 = self.location[1]
            y1 = self.location[1] + self.height
            if x0 <= x <= x1 and y0 <= y <= y1:
                is_touched = True
        if is_touched and self.litcolor is not None:
            self.fgcolor = self.litcolor
            self.show()
            self.delay.trigger(1)
        if is_touched and not self.busy:     # Respond once to a press
            self.callback(self, self.callback_args) # Callback not a bound method so pass self
            self.busy = True  # Ensure no response to continued press

    def untouched(self): # User has released touchpad or touched elsewhere
        self.busy = False

class Buttons(object):
    def __init__(self, user_callback):
        self.user_callback = user_callback
        self.lstbuttons = []

    def add_button(self, *args, **kwargs):
        kwargs['show'] = False
        self.lstbuttons.append(Button(*args, **kwargs))

# Group of buttons, typically at same location, where pressing one shows
# the next e.g. start/stop toggle or sequential select from short list
class Buttonset(Buttons):
    def __init__(self, user_callback):
        super().__init__(user_callback)

    def run(self):
        for idx, button in enumerate(self.lstbuttons):
            if idx:
                button.visible = False # Only button zero visible and sensitive
                button.enabled = False
            button.callback_args.append(idx)
            button.callback = self.callback
        self.lstbuttons[0].show()

    def callback(self, button, args):
        button_no = args[-1]
        old = self.lstbuttons[button_no]
        new = self.lstbuttons[(button_no + 1) % len(self.lstbuttons)]
        old.enabled = False
        old.visible = False
        old.show()
        new.enabled = True
        new.visible = True
        new.busy = True # Don't respond to continued press
        new.show()
        self.user_callback(new, args[:-1]) # user gets button with args they specified

# Group of buttons at different locations, where pressing one shows
# only current button highlighted and oes callback from current one
class RadioButtons(Buttons):
    def __init__(self, user_callback, highlight, selected=0):
        super().__init__(user_callback)
        self.highlight = highlight
        self.selected = selected

    def run(self):
        for idx, button in enumerate(self.lstbuttons):
            if idx == self.selected: # Initial selection
                button.fgcolor = self.highlight
            else:
                button.fgcolor = button.orig_fgcolor
            button.show()
            button.callback = self.callback

    def callback(self, button, args):
        for but in self.lstbuttons:
            if but is button:
                but.fgcolor = self.highlight
            else:
                but.fgcolor = but.orig_fgcolor
            but.show()
        self.user_callback(button, args) # user gets button with args they specified


class Checkbox(Touchable):
    def __init__(self, objsched, tft, objtouch, location, *, height=30, fillcolor=None,
                 fgcolor=None, bgcolor=None, callback=lambda x, y : None, args=[], value=False, border=None):
        super().__init__(objsched, tft, objtouch, location, None, height, height, fgcolor, bgcolor, None, border)
        self.callback = callback
        self.callback_args = args
        self.fillcolor = fillcolor
        self.busy = False
        self.value = value
        self.show()

    def show(self):
        tft = self.tft
        bw = self.draw_border() # and background if required. Result is width of border
        x = self.location[0] + bw
        y = self.location[1] + bw
        height = self.height - 2 * bw
        x1 = x + height
        y1 = y + height
        if self.fillcolor is None or not self.value:
            self.set_color(self.bgcolor) # blank
        tft.fillRectangle(x, y, x1, y1)
        if self.fillcolor is not None and self.value:
            self.set_color(self.fillcolor)
            tft.fillRectangle(x, y, x1, y1)
        self.set_color()
        tft.drawRectangle(x, y, x1, y1)
        if self.fillcolor is None and self.value:
            tft.drawLine(x, y, x1, y1)
            tft.drawLine(x, y1, x1, y)

    def touched(self, x, y): # If touched, process it otherwise do nothing
        is_touched = False
        x0 = self.location[0]
        x1 = self.location[0] + self.width
        y0 = self.location[1]
        y1 = self.location[1] + self.height
        if x0 <= x <= x1 and y0 <= y <= y1:
            is_touched = True
        if is_touched and not self.busy:     # Respond once to a press
            self.value = not self.value
            self.callback(self, self.callback_args) # Callback not a bound method so pass self
            self.busy = True  # Ensure no response to continued press
            self.show()

    def untouched(self): # User has released touchpad or touched elsewhere
        self.busy = False
