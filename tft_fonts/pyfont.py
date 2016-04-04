
class PyFont(object):
    def __init__(self, font, index, vert, horiz, nchars):
        self.firstchar = 32         # ord(first_character) Future use: absent from C file.
        self.nchars = nchars        # No. of chars in font
        self.bits_horiz = horiz     # Width in pixels of char if rendered as monospaced
        self.bits_vert = vert       # Height in pixels
        self.bytes_vert = (self.bits_vert + 7) // 8     # Height in bytes
        self.bytes_per_ch = self.bytes_vert * horiz     # Total bytes per monospaced character
        self.monospaced = False
        self.char = bytearray(self.bytes_per_ch)
        self.mv = memoryview(self.char)

        self._index = index
        self._font = font
        self._zero = bytearray(self.bytes_per_ch)
        self._mvzero = memoryview(self._zero)

    def get_idx(self, relch):
        offset = relch * 2            # index is 2 bytes/char
        return self._index[offset] + (self._index[offset + 1] << 8)

    def get_ch(self, ch):
        relch = max(0, ch - self.firstchar) # This is the behaviour you requested. In my view it should throw a ValueError.
        if relch > self.nchars:
            relch = 0
        offset = self.get_idx(relch)
        delta = self.get_idx(relch + 1) - offset
        bv = self.bits_vert
        mv = self.mv
        if self.monospaced:
            bh = self.bits_horiz # Char width in bits
            mv[: delta] = self._font[offset : offset + delta]
            mv[delta : self.bytes_per_ch] = self._mvzero[delta : self.bytes_per_ch]
            bh = self.bits_horiz
        else:
            mv[: delta] = self._font[offset : offset + delta]
            bh = delta // self.bytes_vert
        return bh # horizontal increment for character location

# Demo/test of rendering to the REPL
    def render(self, ch): # enter with ord(ch)
        bh = self.get_ch(ch)
        bv = self.bits_vert # Cache for speed
        mv = self.mv
        for bit_vert in range(bv):   # for each vertical line
            bytenum, bitnum = divmod(bit_vert, 8)
            bit = 1 << bitnum
            for bit_horiz in range(bh): #  horizontal line
                fontbyte = self.mv[self.bytes_vert * bit_horiz + bytenum]
                print('*' if fontbyte & bit else ' ', end = '')
            print('|')
        return bh # Caller accounts for horzontal increment
