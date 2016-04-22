
import gc
from font10 import font10
from tft import TFT, LANDSCAPE
from usched import Sched
from asynctouch import TOUCH
from slider import Slider
from button import Button
from ui import CLIPPED_RECT
import math
#gc.collect()

class Dial(object):
    def __init__(self, objsched, tft, x, y, r, l):
        self.objsched = objsched
        self.tft = tft
        self.xorigin = x
        self.yorigin = y
        self.radius = r
        self.pointerlen = l
        self.angle = None
        self.delta = 1
        tft.drawCircle(x, y, r)
        objsched.add_thread(self.mainthread())

    def update(self, angle):
        tft = self.tft
        fgcolor = tft.getColor()  # save old colors
        bgcolor = tft.getBGColor()
        if self.angle is not None:
            tft.setColor(bgcolor)
            self.drawpointer(self.angle) # erase old
        tft.setColor(fgcolor)
        self.drawpointer(angle) # draw new
        self.angle = angle # update old
        tft.setColor(fgcolor) # restore them
        tft.setBGColor(bgcolor)

    def drawpointer(self, radians):
        x_end = int(self.xorigin + self.pointerlen * math.sin(radians))
        y_end = int(self.yorigin - self.pointerlen * math.cos(radians))
        self.tft.drawLine(self.xorigin, self.yorigin, x_end, y_end)

    def mainthread(self):
        while True:
            yield 0.1
            angle = self.angle if self.angle is not None else 0
            angle += math.pi * 2 * self.delta / 10
            self.update(angle)

# CALLBACKS
# cb_end occurs when user stops touching the control
def callback(slider, args):
    print('{} returned {}'.format(args[0], slider.value()))

def to_string(val):
    return '{:4.1f}ohms'.format(val * 10)

def master_moved(slider, args):
    val = slider.value()
    slave1 = args[0]
    slave1.value(val)
    slave2 = args[1]
    slave2.value(val)

# Either slave has had its slider moved (by user or by having value altered)
def slave_moved(slider, args):
    dial = args[0]
    dial.delta = slider.value()

def doquit(button, args):
    button.objsched.stop()

# USER TEST FUNCTION
# '0', '1','2','3','4','5','6','7','8','9','10'
# Common arguments for all three sliders
table = {'fontcolor' : (255, 255, 255),
         'legends' : ('0', '5', '10'),
         'to_string' : to_string,
         'cb_end' : callback,
         'value' : 0.5}

def test(duration = 0):
    print('Test TFT panel...')
    objsched = Sched()                                      # Instantiate the scheduler
    mytft = TFT("SSD1963", "LB04301", LANDSCAPE)
    mytouch = TOUCH(objsched, "XPT2046")
    mytft.backlight(100) # light on
    Button(objsched, mytft, mytouch, (400, 240), font = font10, callback = doquit, fgcolor = (255, 0, 0),
           height = 30, text = 'Quit', shape = CLIPPED_RECT)
    dial1 = Dial(objsched, mytft, 350, 60, 50, 48)
    dial2 = Dial(objsched, mytft, 350, 170, 50, 48)
    y = 5
    slave1 = Slider(objsched, mytft, mytouch, (80, y), font10,
           fgcolor = (0, 255, 0), cbe_args = ('Slave1',), cb_move = slave_moved, cbm_args = (dial1,), **table)
    slave2 = Slider(objsched, mytft, mytouch, (160, y), font10,
           fgcolor = (0, 255, 0), cbe_args = ('Slave2',), cb_move = slave_moved, cbm_args = (dial2,), **table)
    Slider(objsched, mytft, mytouch, (0, y), font10,
           fgcolor = (255, 255, 0), cbe_args = ('Master',), cb_move = master_moved, cbm_args = (slave1, slave2), **table)
    objsched.run()                                          # Run it!

test()
