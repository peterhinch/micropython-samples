# slider.py
# A slider's text items lie outside its bounding box (area sensitive to touch)

from ui import touchable
from TFT_io import TFT_io
class Slider(touchable):
    def __init__(self, objsched, tft, objtouch, location, font, *, height=200, width=30, divisions=10, legends=None,
                 fgcolor=None, bgcolor=None, fontcolor=None, slidecolor=None, cb_end=lambda x, y : None,
                 cbe_args=[], cb_move=lambda x, y : None, cbm_args=[], to_string=lambda x : str(x), value=0.0):
        super().__init__(objsched, objtouch)
        self.objsched = objsched
        self.tft = tft
        self.location = location
        self.height = height
        self.width = width
        self.divisions = divisions
        self.legends = legends
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor
        self.fontcolor = fontcolor if fontcolor is not None else tft.getColor()
        self.font = font
        self.slidecolor = slidecolor
        self.cb_end = cb_end
        self.cbe_args = cbe_args
        self.cb_move = cb_move
        self.cbm_args = cbm_args
        self.to_string = to_string # Applied to display at bottom: user converts 0-1.0 to string with any scaling applied
        self.was_touched = False
        self.old_text_end = False
        self.slidewidth = int(width / 1.3)
        self.slidewidth += self.slidewidth % 2 # Ensure divisible by 2
        self.slideheight = 6 # must be divisible by 2
                             # We draw an odd number of pixels:
        self.slidebytes = (self.slideheight + 1) * (self.slidewidth + 1) * 3
        self.slidebuf = bytearray(self.slidebytes)
        self.slide_x = -1
        self.slide_y = -1 # Invalidate old position
        self.border_y = min(self.slideheight // 2, 10) # Allow space above and below slot

        self._value = min(max(value, 0.0), 1.0) # User supplies 0-1.0
        self.show()
        objsched.add_thread(self.mainthread())

    def show(self):
        tft = self.tft
        fgcolor = tft.getColor()  # save old colors
        bgcolor = tft.getBGColor()
        mybgcolor = bgcolor
        x = self.location[0]
        y = self.location[1] + self.border_y
        if self.bgcolor is not None:
            tft.setColor(self.bgcolor)
        else:
            tft.setColor(bgcolor)
        tft.setTextStyle(self.fontcolor, None, 2, self.font)
        if self.fgcolor is not None:
            tft.setColor(self.fgcolor)
        else:
            tft.setColor(fgcolor)
        if self.bgcolor is not None:
            mybgcolor = self.bgcolor
            tft.setBGColor(mybgcolor)
        height = self.height
        width = self.width
        dx = width // 3
        xcentre = x + width // 2
        tft.drawRectangle(x + dx, y, x + 2 * dx, y + height)

        if self.divisions > 0:
            dy = height // self.divisions # Tick marks
            ytick = y
            fhdelta = self.font.bits_vert // 2
            for tick in range(self.divisions + 1):
                tft.drawHLine(x, ytick, dx)
                tft.drawHLine(x + 2 * dx, ytick, dx)
                ytick += dy

        if self.legends is not None: # Legends
            if len(self.legends) <= 1:
                dy = 0
            else:
                dy = height // (len(self.legends) -1)
            yl = y + height # Start at bottom
            for legend in self.legends:
                tft.setTextPos(x + width, yl - fhdelta)
                tft.printString(legend)
                yl -= dy

        sw = self.slidewidth # Handle slider
        sh = self.slideheight
        sliderpos = int(y + height - self._value * height)
        if self.slidecolor is not None:
            tft.setColor(self.slidecolor)
        if self.slide_x >= 0: # Restore background
            tft.setXY(self.slide_x, self.slide_y, self.slide_x + sw, self.slide_y + sh)
            TFT_io.tft_write_data_AS(self.slidebuf, self.slidebytes)
        x0 = xcentre - sw // 2
        y0 = sliderpos - sh // 2
        x1 = xcentre + sw // 2
        y1 = sliderpos + sh // 2
        tft.setXY(x0, y0, x1, y1) # Read background
        TFT_io.tft_read_cmd_data_AS(0x2e, self.slidebuf, self.slidebytes)
        self.slide_x = x0
        self.slide_y = y0
        tft.fillRectangle(x0, y0, x1, y1) # Draw slider

        textx = x
        texty = y + height + 2 * self.border_y
        tft.setTextPos(textx, texty)
        if self.old_text_end:
            tft.setColor(mybgcolor)
            tft.fillRectangle(textx, texty, self.old_text_end, texty + self.font.bits_vert)
        tft.printString(self.to_string(self._value))
        self.old_text_end = tft.getTextPos()[0]
        tft.setColor(fgcolor) # restore them
        tft.setBGColor(bgcolor)

    def value(self, val=None):
        if val is None:
            return self._value
        self._value = min(max(val, 0.0), 1.0)
        self.show()

    def touched(self, x, y): # If touched in bounding box, process it otherwise do nothing
        x0 = self.location[0]
        x1 = self.location[0] + self.width
        y0 = self.location[1]
        y1 = self.location[1]  + self.height
        if x0 <= x <= x1 and y0 <= y <= y1:
            self.was_touched = True
            self._value = (y1 - y) / self.height

    def untouched(self): # User has released touchpad or touched elsewhere
        if self.was_touched:
            self.cb_end(self, self.cbe_args) # Callback not a bound method so pass self
            self.was_touched = False

    def mainthread(self):
        old_value = self._value
        while True:
            yield
            val = self._value
            if val != old_value:
                old_value = val
                self.cb_move(self, self.cbm_args) # Callback not a bound method so pass self
                self.show()
