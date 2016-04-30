# vst.py Demo/test program for vertical slider class for Pyboard TFT GUI

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

from font10 import font10
from tft import TFT, LANDSCAPE
from usched import Sched
from touch import TOUCH
from ugui import Slider, Button, Dial, Label, CLIPPED_RECT, WHITE, BLACK, RED, GREEN, BLUE, YELLOW, GREY
from math import pi

# CALLBACKS
# cb_end occurs when user stops touching the control
def callback(slider, device):
    print('{} returned {}'.format(device, slider.value()))

def to_string(val):
    return '{:3.1f} ohms'.format(val * 10)

def master_moved(slider, slave1, slave2, label):
    val = slider.value()
    slave1.value(val)
    slave2.value(val)
    label.show(to_string(val))

# Either slave has had its slider moved (by user or by having value altered)
def slave_moved(slider, label):
    val = slider.value()
    label.show(to_string(val))

def doquit(button):
    button.objsched.stop()

# THREADS
def mainthread(slider, dial):
    angle = 0
    yield
    while True:
        yield 0.1
        delta = slider.value()
        angle += pi * 2 * delta / 10
        dial.show(angle)
        dial.show(angle /10, 1)

# DATA
# Common args for the labels
labels = { 'width' : 70,
          'fontcolor' : WHITE,
          'border' : 2,
          'fgcolor' : RED,
          'bgcolor' : (0, 40, 0),
          }

# '0', '1','2','3','4','5','6','7','8','9','10'
# Common arguments for all three sliders
table = {'fontcolor' : WHITE,
         'legends' : ('0', '5', '10'),
         'cb_end' : callback,
         }
#          'border' : 2,

def test():
    print('Test TFT panel...')
    objsched = Sched()                                      # Instantiate the scheduler
    mytft = TFT("SSD1963", "LB04301", LANDSCAPE)
    mytouch = TOUCH("XPT2046", objsched, confidence=50, margin = 50)
    mytft.backlight(100) # light on
    Button(objsched, mytft, mytouch, (400, 240), font = font10, callback = doquit, fgcolor = RED,
           height = 30, text = 'Quit', shape = CLIPPED_RECT)
    dial1 = Dial(mytft, (350, 10), fgcolor = YELLOW, border = 2, pointers = (0.9, 0.7))
    dial2 = Dial(mytft, (350, 120), fgcolor = YELLOW, bgcolor = GREY, border = 2,  pointers = (0.9, 0.7))
    lstlbl = []
    for n in range(3):
        lstlbl.append(Label(mytft, (80 * n, 240), font = font10, **labels))
    y = 5
    slave1 = Slider(objsched, mytft, mytouch, (80, y), font10,
           fgcolor = GREEN, cbe_args = ('Slave1',), cb_move = slave_moved, cbm_args = [lstlbl[1]], **table)
    slave2 = Slider(objsched, mytft, mytouch, (160, y), font10,
           fgcolor = GREEN, cbe_args = ('Slave2',), cb_move = slave_moved, cbm_args = [lstlbl[2]], **table)
    master = Slider(objsched, mytft, mytouch, (0, y), font10,
           fgcolor = YELLOW, cbe_args = ('Master',), cb_move = master_moved, cbm_args = (slave1, slave2, lstlbl[0]), value=0.5, **table)
    objsched.add_thread(mainthread(slave1, dial1))
    objsched.add_thread(mainthread(slave2, dial2))
    objsched.run()                                          # Run it!

test()
