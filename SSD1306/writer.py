# writer.py Implements the Writer class.
# V0.1 Peter Hinch Nov 2016

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
# Currently supports vertical mapping and the SSD1306 "pseudo-horizontal" map
# only
# Multiple Writer instances may be created, each rendering a font to the
# same Display object.

VERT = 0
HORIZ = 1
WEIRD = 2

class Writer(object):
    text_row = 0  # attributes common to all Writer instances
    text_col = 0
    row_clip = False  # Clip or scroll when screen full
    col_clip = False  # Clip or new line when row is full
    bmap = WEIRD  # SSD1306 pseudo-horizontal

    @classmethod
    def set_textpos(cls, row, col):
        cls.text_row = row
        cls.text_col = col

    @classmethod
    def set_clip(cls, row_clip, col_clip):
        cls.row_clip = row_clip
        cls.col_clip = col_clip

    @classmethod
    def mapping(cls, bmap):
        if bmap in (VERT, HORIZ):
            cls.bmap = bmap
        else:
            raise ValueError('Unsupported mapping')

    def __init__(self, device, font):
        super().__init__()
        self.device = device
        self.font = font
        if font.hmap():
            raise OSError('Font must be vertically mapped')
        self.screenwidth = device.width  # In pixels
        self.screenheight = device.height
        div, mod = divmod(device.height, 8)
        self.bytes_per_col = div + 1 if mod else div

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
        bmap = Writer.bmap # Buffer mapping
        if char == '\n':
            self._newline()
            return
        fbuff = self.device.buffer
        glyph, char_height, char_width = self.font.get_ch(char)
        if Writer.text_row+char_height > self.screenheight and Writer.row_clip:
            return
        if Writer.text_col + char_width > self.screenwidth:
            if Writer.col_clip:
                return
            else:
                self._newline()
        div, mod = divmod(char_height, 8)
        gbytes = div + 1 if mod else div  # No. of bytes per column of glyph
        start_row, align = divmod(Writer.text_row, 8)
        for scol in range(0, char_width):  # Source column
            dcol = scol + Writer.text_col  # Destination column
            dest_row_byte = start_row
            for gbyte in range(gbytes):  # Each glyph byte in column
                if bmap == VERT:
                    dest = dcol * self.bytes_per_col + dest_row_byte
                elif bmap == WEIRD:
                    dest = dcol + dest_row_byte * self.screenwidth
                source = scol * gbytes + gbyte
                data = fbuff[dest] & (0xff >> (8 - align))
                fbuff[dest] = data | glyph[source] << align
                if align and (dest_row_byte + 1) < self.bytes_per_col:
                    if bmap == VERT:
                        dest += 1
                    elif bmap == WEIRD:
                        dest += self.screenwidth
                    data = fbuff[dest] & (0xff << align)
                    fbuff[dest] = data | glyph[source] >> (8 - align)
                dest_row_byte += 1
                if dest_row_byte >= self.bytes_per_col:
                    break
        Writer.text_col += char_width
