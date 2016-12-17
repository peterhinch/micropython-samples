# writer.py Implements the Writer class.
# V0.2 Peter Hinch Dec 2016: supports updated framebuf module.

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


class Writer(object):
    text_row = 0        # attributes common to all Writer instances
    text_col = 0
    row_clip = False    # Clip or scroll when screen full
    col_clip = False    # Clip or new line when row is full

    @classmethod
    def set_textpos(cls, row, col):
        cls.text_row = row
        cls.text_col = col

    @classmethod
    def set_clip(cls, row_clip, col_clip):
        cls.row_clip = row_clip
        cls.col_clip = col_clip

    def __init__(self, device, font):
        super().__init__()
        self.device = device
        self.font = font
        if font.hmap():
            raise OSError('Font must be vertically mapped')
        self.screenwidth = device.width  # In pixels
        self.screenheight = device.height

    def _newline(self):
        height = self.font.height()
        Writer.text_row += height
        Writer.text_col = 0
        margin = self.screenheight - (Writer.text_row + height)
        if margin < 0:
            if not Writer.row_clip:
                self.device.scroll(0, margin)
                Writer.text_row += margin

    def printstring(self, string):
        for char in string:
            self._printchar(char)

    def _printchar(self, char):
        if char == '\n':
            self._newline()
            return
        glyph, char_height, char_width = self.font.get_ch(char)
        if Writer.text_row + char_height > self.screenheight:
            if Writer.row_clip:
                return
            self._newline()
        if Writer.text_col + char_width > self.screenwidth:
            if Writer.col_clip:
                return
            else:
                self._newline()

        div, mod = divmod(char_height, 8)
        gbytes = div + 1 if mod else div    # No. of bytes per column of glyph
        device = self.device
        for scol in range(char_width):      # Source column
            dcol = scol + Writer.text_col   # Destination column
            drow = Writer.text_row          # Destination row
            for srow in range(char_height): # Source row
                gbyte, gbit = divmod(srow, 8)
                if drow >= self.screenheight:
                    break
                if gbit == 0:               # Next glyph byte
                    data = glyph[scol * gbytes + gbyte]
                device.pixel(dcol, drow, data & (1 << gbit))
                drow += 1
        Writer.text_col += char_width
