# hst.py Demo/test for Horizontal Slider class for Pyboard TFT GUI

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
from slider import HorizSlider
from button import Button
from displays import Dial, Label, LED, Meter
from ui import CLIPPED_RECT, GREEN, RED, YELLOW, WHITE, BLUE
import pyb
# CALLBACKS
# cb_end occurs when user stops touching the control
def callback(slider, args):
    print('{} returned {}'.format(args[0], slider.value()))

def to_string(val):
    return '{:3.1f} ohms'.format(val * 10)

def master_moved(slider, args):
    val = slider.value()
    slave1 = args[0]
    slave1.value(val)
    slave2 = args[1]
    slave2.value(val)
    label = args[2]
    label.show(to_string(val))
    led = args[3]
    if val > 0.8:
        led.on()
    else:
        led.off()

# Either slave has had its slider moved (by user or by having value altered)
def slave_moved(slider, args):
    val = slider.value()
    if val > 0.8:
        slider.fgcolor = RED
    else:
        slider.fgcolor = GREEN
    label = args[0]
    label.show(to_string(val))

def doquit(button, args):
    button.objsched.stop()

# USER TEST FUNCTION
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

def testmeter(meter):
    oldvalue = 0
    yield
    while True:
        val = pyb.rng()/2**30
        steps = 20
        delta = (val - oldvalue) / steps
        for _ in range(steps):
            oldvalue += delta
            meter.value(oldvalue)
            yield 0.05

def test(duration = 0):
    print('Test TFT panel...')
    objsched = Sched()                                      # Instantiate the scheduler
    mytft = TFT("SSD1963", "LB04301", LANDSCAPE)
    mytouch = TOUCH("XPT2046", objsched, confidence = 50) #, calibration = (-3886,-0.1287,-3812,-0.132,-3797,-0.07685,-3798,-0.07681))
    mytft.backlight(100) # light on
    led = LED(mytft, (420, 0), border = 2)
    meter1 = Meter(mytft, (320, 0), font=font10, legends=('0','5','10'), pointercolor = YELLOW, fgcolor = GREEN)
    meter2 = Meter(mytft, (360, 0), font=font10, legends=('0','5','10'), pointercolor = YELLOW)
    Button(objsched, mytft, mytouch, (420, 240), font = font10, callback = doquit, fgcolor = RED,
           height = 30, text = 'Quit', shape = CLIPPED_RECT)
    x = 230
    lstlbl = []
    for n in range(3):
        lstlbl.append(Label(mytft, (x, 40 + 60 * n), font = font10, **labels))
    x = 0
    slave1 = HorizSlider(objsched, mytft, mytouch, (x, 100), font10,
           fgcolor = GREEN, cbe_args = ('Slave1',), cb_move = slave_moved, cbm_args = (lstlbl[1],), **table)
    slave2 = HorizSlider(objsched, mytft, mytouch, (x, 160), font10,
           fgcolor = GREEN, cbe_args = ('Slave2',), cb_move = slave_moved, cbm_args = (lstlbl[2],), **table)
    master = HorizSlider(objsched, mytft, mytouch, (x, 40), font10,
           fgcolor = YELLOW, cbe_args = ('Master',), cb_move = master_moved, slidecolor=RED, cbm_args = (slave1, slave2, lstlbl[0], led), value=0.5, **table)
    objsched.add_thread(testmeter(meter1))
    objsched.add_thread(testmeter(meter2))
    objsched.run()                                          # Run it!

test()
