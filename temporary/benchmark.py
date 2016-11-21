import framebuf
from writer import Writer
import utime
import courier_virt_25 as font

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(utime.ticks_us(), t)  # Argument order new, old
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

class VirtualDisplay(object):
    def __init__(self):
        self.width = 256  # 16K framebuf
        self.height = 512
        self.pages = self.height // 8
        self.size = self.pages * self.width
        self.buffer = bytearray(self.size)
        self.framebuf = framebuf.FrameBuffer1(self.buffer, self.width, self.height)

    def show(self):
        pass

    def fill(self, col):
        val = 0xff if col else 0
        for x in range(self.size):
            self.buffer[x] = val

class SlowWriter(Writer):
    def __init__(self, device, font):
        super().__init__(device, font)

    def _printchar(self, char):
        bmap = Writer.bmap # Buffer mapping
        if char == '\n':
            self._newline()
            return
        device = self.device
        fbuff = device.framebuf
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
        for scol in range(0, char_width):  # Source column
            dcol = scol + Writer.text_col  # Destination column
            drow = Writer.text_row
            for row_offset in range(char_height):
                gbyte = row_offset >> 3  # Glyph byte in column
                gbit = row_offset & 7
                data_byte = glyph[scol * gbytes + gbyte]
                fbuff.pixel(dcol, drow + row_offset, data_byte & (1 << gbit))
        Writer.text_col += char_width

def check():
    x = len(device.buffer) -1
    while device.buffer[x] == 0:
        x -= 1
    print('x = ', x)
    print(device.buffer[x -16:x])

def setup():
    device.fill(0)
    Writer.set_textpos(0,0)

device = VirtualDisplay()
mystr = 'The quick brown fox\n'

wri = Writer(device, font)
wrislow = SlowWriter(device, font)

@timed_function
def test(writer):
    for _ in range(5):
        writer.printstring(mystr)

setup()
test(wri)  # Bytewise output
check()

setup()
test(wrislow)  # Bitwise output
check()
