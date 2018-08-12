# writer.py Implements the Writer class.
# V0.3 Peter Hinch 11th Aug 2018
# Handles colour and upside down diplays

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

# A Writer supports rendering text to a Display instance in a given font.
# Multiple Writer instances may be created, each rendering a font to the
# same Display object.

import framebuf


# Basic Writer class for monochrome displays
class Writer():
    text_row = 0  # attributes common to all Writer instances sharing a display.
    text_col = 0
    row_clip = False  # Clip or scroll when screen full
    col_clip = False  # Clip or new line when row is full

    @classmethod
    def set_textpos(cls, row=None, col=None):
        if row is not None:
            Writer.text_row = row
        if col is not None:
            Writer.text_col = col
        return  Writer.text_row,  Writer.text_col

    @classmethod
    def set_clip(cls, row_clip=None, col_clip=None):
        if row_clip is not None:
            Writer.row_clip = row_clip
        if col_clip is not None:
            Writer.col_clip = col_clip
        return Writer.row_clip, Writer.col_clip

    def __init__(self, device, font, verbose=True):
        self.device = device
        self.font = font
        # Allow to work with reverse or normal font mapping
        if font.hmap():
            self.map = framebuf.MONO_HMSB if font.reverse() else framebuf.MONO_HLSB
        else:
            raise ValueError('Font must be horizontally mapped.')
        if verbose:
            fstr = 'Orientation: Horizontal. Reversal: {}. Width: {}. Height: {}.'
            print(fstr.format(font.reverse(), device.width, device.height))
            print('Start row = {} col = {}'.format(Writer.text_row, Writer.text_col))
        self.screenwidth = device.width  # In pixels
        self.screenheight = device.height
        self.usd = hasattr(self, 'usd') and self.usd  # upside down display (CWriter).
        self.bgcolor = 0
        self.glyph = None  # Current char
        self.char_height = 0
        self.char_width = 0

    def _newline(self):
        height = self.font.height()
        if self.usd:
            Writer.text_row -= height
            Writer.text_col = self.screenwidth - 1
            margin = Writer.text_row - height
            y = 0
        else:
            Writer.text_row += height
            Writer.text_col = 0
            margin = self.screenheight - (Writer.text_row + height)
            y = self.screenheight + margin
        if margin < 0:
            if not Writer.row_clip:
                if self.usd:
                    margin = -margin
                self.device.scroll(0, margin)
                self.device.fill_rect(0, y, self.screenwidth, abs(margin), self.bgcolor)
                Writer.text_row += margin
                #print('newline', margin, Writer.text_row)

    def height(self):
        return self.font.height()

    def printstring(self, string, invert=False):
        #print('Writer.text_row = ', Writer.text_row)
        for char in string:
            self._printchar(char, invert)

    def stringlen(self, string):
        l = 0
        for char in string:
            l += self._charlen(char)
        return l

    def _charlen(self, char):
        if char == '\n':
            char_width = 0
        else:
            _, _, char_width = self.font.get_ch(char)
        return char_width

    def _get_char(self, char):
        self.glyph = None  # Assume all done
        if char == '\n':
            self._newline()
            return
        glyph, char_height, char_width = self.font.get_ch(char)
        if self.usd:
            if Writer.text_row - char_height < 0:
                if Writer.row_clip:
                    return
                self._newline()
            if Writer.text_col - char_width < 0:
                if Writer.col_clip:
                    return
                else:
                    self._newline()
        else:
            if Writer.text_row + char_height > self.screenheight:
                if Writer.row_clip:
                    return
                self._newline()
            if Writer.text_col + char_width > self.screenwidth:
                if Writer.col_clip:
                    return
                else:
                    self._newline()
        self.glyph = glyph
        self.char_height = char_height
        self.char_width = char_width
        
    # Method using blitting. Efficient rendering for monochrome displays.
    # Tested on SSD1306. Invert is for black-on-white rendering.
    def _printchar(self, char, invert=False):
        self._get_char(char)  # Handle row/col clipping, wrapping, scrolling
        if self.glyph is None:
            return
        buf = bytearray(self.glyph)
        if invert:
            for i, v in enumerate(buf):
                buf[i] = 0xFF & ~ v
        fbc = framebuf.FrameBuffer(buf, self.char_width, self.char_height, self.map)
        self.device.blit(fbc, Writer.text_col, Writer.text_row)
        Writer.text_col += self.char_width


# Writer for colour displays or upside down rendering
class CWriter(Writer):
    usd = False  # Upside down display.

    @classmethod
    def invert_display(cls, value=True):
        cls.usd = value

    def __init__(self,device, font, verbose=True):
        super().__init__(device, font, verbose)
        self.fgcolor = 1

    def setcolor(fgcolor, bgcolor):
        self.fgcolor = fgcolor
        self.bgcolor = bgcolor

    def _printchar(self, char, invert=False):
        #print('Writer.text_row 1 = ', Writer.text_row)
        self._get_char(char)
        #print('Writer.text_row 2 = ', Writer.text_row)
        if self.glyph is None:
            return  # All done
        char_height = self.char_height
        char_width = self.char_width

        div, mod = divmod(char_width, 8)
        gbytes = div + 1 if mod else div  # No. of bytes per row of glyph
        device = self.device
        fgcolor = self.bgcolor if invert else self.fgcolor
        bgcolor = self.fgcolor if invert else self.bgcolor
        usd = self.usd
        drow = Writer.text_row  # Destination row
        wcol = Writer.text_col  # Destination column of character start
        #print('drow = ',drow)
        for srow in range(char_height):  # Source row
            for scol in range(char_width):  # Source column
                # Destination column: add/subtract writer column
                if usd:
                    dcol = wcol - scol
                else:
                    dcol = wcol + scol
                gbyte, gbit = divmod(scol, 8)
                if gbit == 0:  # Next glyph byte
                    #print(scol, gbyte, gbytes, srow * gbytes, char_height, char_width)
                    data = self.glyph[srow * gbytes + gbyte]
                pixel = fgcolor if data & (1 << (7 - gbit)) else bgcolor
                device.pixel(dcol, drow, pixel)
            drow += -1 if usd else 1
            if drow >= self.screenheight or drow < 0:
                break
        Writer.text_col += -char_width if usd else char_width
