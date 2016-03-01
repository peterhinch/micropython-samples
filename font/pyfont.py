
class PyFont(object):
    def __init__(self, font, vert, horiz, nchars):
        self.bits_horiz = horiz
        self.bits_vert = vert
        div, mod = divmod(self.bits_vert, 8)
        self.bytes_vert = div if mod == 0 else div +1
        self.bytes_per_ch = self.bytes_vert * self.bits_horiz +1
        self.nchars = nchars
        self.font = font
        self.monospaced = False

    def render(self, ch): # enter with ord(ch)
        relch = ch -32
        if relch > self.nchars:
            raise ValueError('Illegal character')
        offset = relch * self.bytes_per_ch
        bv = self.bits_vert
        bh = self.bits_horiz if self.monospaced else self.font[offset] # Char width
        offset += 1
        for bit_vert in range(bv):   # for each vertical line
            bytenum = bit_vert >> 3
            bit = 1 << (bit_vert & 0x07)        # Faster than divmod
            for bit_horiz in range(bh): #  horizontal line
                fontbyte = self.font[offset + self.bytes_vert * bit_horiz + bytenum]
                z = '*' if fontbyte & bit else ' '
                print(z, end='')
#                self.setpixelfast(self.char_x +bit_horiz, self.char_y +bit_vert, (fontbyte & bit) > 0)
            print()
#        self.char_x += bh                       # Somehow account for width of current char

    def test(self, s):
        for c in s:
            self.render(ord(c))
