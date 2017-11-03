# mt.py Display module for the power meter

# The MIT License (MIT)
#
# Copyright (c) 2017 Peter Hinch
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

import uasyncio as asyncio
from mains import Scaling
from constants import *
from lcd160_gui import Button, Label, Screen, Dropdown, Dial, LED, ButtonList
from lplot import CartesianGraph, Curve
import font10
from lcd_local import setup
from utime import ticks_ms, ticks_diff
from os import listdir

if 'mt.py' in listdir('/flash'):
    mains_device = Scaling() # Real
#    mains_device = Scaling(True, False)  # Simulate
else:  # Running on SD card - test setup
    mains_device = Scaling(True, False)  # Simulate

# STANDARD BUTTONS
def fwdbutton(y, screen, text, color):
    def fwd(button, screen):
        Screen.change(screen)
    return Button((109, y), font = font10, fontcolor = BLACK, callback = fwd,
                  args = [screen], fgcolor = color, text = text)

def backbutton():
    def back(button):
        Screen.back()
    return Button((139, 0), font = font10, fontcolor = BLACK, callback = back,
           fgcolor = RED,  text = 'X', height = 20, width = 20)

def plotbutton(y, screen, color):
    def fwd(button, screen):
        Screen.change(screen)
    return Button((139, y), font = font10, fontcolor = BLACK, callback = fwd,
           args = [screen], fgcolor = color,  text = '~', height = 20, width = 20)

# **** BASE SCREEN ****

class BaseScreen(Screen):
    def __init__(self):
        super().__init__()
        self.pwr_range = 3000
# Buttons
        fwdbutton(57, IntegScreen, 'Integ', CYAN)
        fwdbutton(82, PlotScreen, 'Plot', YELLOW)
# Labels
        self.lbl_pf = Label((0, 31), font = font10, width = 75, border = 2, bgcolor = DARKGREEN, fgcolor = RED)
        self.lbl_v = Label((0, 56), font = font10, width = 75, border = 2, bgcolor = DARKGREEN, fgcolor = RED)
        self.lbl_i = Label((0, 81), font = font10, width = 75, border = 2, bgcolor = DARKGREEN, fgcolor = RED)
        self.lbl_p = Label((0,106), font = font10, width = 75, border = 2, bgcolor = DARKGREEN, fgcolor = RED)
        self.lbl_va = Label((80,106), font = font10, width = 79, border = 2, bgcolor = DARKGREEN, fgcolor = RED)
# Dial
        self.dial = Dial((109, 0), fgcolor = YELLOW, border = 2)
# Dropdown
        self.dropdown = Dropdown((0, 0), font = font10, width = 80, callback = self.cbdb,
                                 elements = ('3000W', '600W', '150W', '60W', '30W'))
        self.led = LED((84, 0), color = GREEN)
        self.led.value(True)
# Dropdown callback: set range
    def cbdb(self, dropdown):
        self.pwr_range = int(dropdown.textvalue()[: -1])  # String of form 'nnnW'
        mains_device.set_range(self.pwr_range)
#        print('Range set to', self.pwr_range, dropdown.value())

    def reading(self, phase, vrms, irms, pwr, nelems, ovr):
#        print(phase, vrms, irms, pwr, nelems)
        self.lbl_v.value('{:5.1f}V'.format(vrms))
        if ovr:
            self.lbl_i.value('----')
            self.lbl_p.value('----')
            self.lbl_pf.value('----')
            self.lbl_va.value('----')
        else:
            self.lbl_i.value('{:6.3f}A'.format(irms))
            self.lbl_p.value('{:5.1f}W'.format(pwr))
            self.lbl_pf.value('PF:{:4.2f}'.format(pwr /(vrms * irms)))
            self.lbl_va.value('{:5.1f}VA'.format(vrms * irms))
        self.dial.value(phase + 1.5708)  # Conventional phasor orientation.
        if ovr:
            self.led.color(RED)  # Overrange
        elif abs(pwr) < abs(self.pwr_range) / 5:
            self.led.color(YELLOW)  # Underrange
        else:
            self.led.color(GREEN)  # OK

    def on_hide(self):
        mains_device.set_callback(None)  # Stop readings

    def after_open(self):
        mains_device.set_callback(self.reading)

# **** PLOT SCREEN ****

class PlotScreen(Screen):
    @staticmethod
    def populate(curve, data):
        xinc = 1 / len(data)
        x = 0
        for y in data:
            curve.point(x, y)
            x += xinc

    def __init__(self):
        super().__init__()
        backbutton()
        Label((142, 45), font = font10, fontcolor = YELLOW, value = 'V')
        Label((145, 70), font = font10, fontcolor = RED, value = 'I')
        g = CartesianGraph((0, 0), height = 127, width = 135, xorigin = 0) # x >= 0
        Curve(g, self.populate, args = (mains_device.vplot,))
        Curve(g, self.populate, args = (mains_device.iplot,), color = RED)

# **** INTEGRATOR SCREEN ****

class IntegScreen(Screen):
    def __init__(self):
        super().__init__()
# Buttons
        backbutton()
        plotbutton(80, PlotScreen, YELLOW)
# Labels
        self.lbl_p = Label((0, 0), font = font10, width = 78, border = 2, bgcolor = DARKGREEN, fgcolor = RED)
        Label((90, 4), font = font10, value = 'Power')
        self.lbl_pmax = Label((0, 30), font = font10, width = 78, border = 2, bgcolor = DARKGREEN, fgcolor = RED)
        Label((90, 34), font = font10, value = 'Max')
        self.lbl_pin = Label((0, 55), font = font10, width = 78, border = 2, bgcolor = DARKGREEN, fgcolor = RED)
        self.lbl_pmin = Label((0, 80), font = font10, width = 78, border = 2, bgcolor = DARKGREEN, fgcolor = RED)
        Label((90, 84), font = font10, value = 'Min')
        self.lbl_w_hr = Label((0,105), font = font10, width = 78, border = 2, bgcolor = DARKGREEN, fgcolor = RED)
        self.lbl_t = Label((88, 105), font = font10, width = 70, border = 2, bgcolor = DARKGREEN, fgcolor = RED)

        table = [
            {'fgcolor' : GREEN, 'text' : 'Max Gen', 'args' : (True,)},
            {'fgcolor' : BLUE, 'text' : 'Mean', 'args' : (False,)},
        ]
        bl = ButtonList(self.buttonlist_cb)
        for t in table: # Buttons overlay each other at same location
            bl.add_button((90, 56), width = 70, font = font10, fontcolor = BLACK, **t)
        self.showmean = False
        self.t_reading = None  # Time of last reading
        self.t_start = None  # Time of 1st reading
        self.joules = 0  # Cumulative energy
        self.overrange = False
        self.wmax = 0  # Max power out
        self.wmin = 0  # Max power in
        self.pwr_min = 10000 # Power corresponding to minimum absolute value

    def reading(self, phase, vrms, irms, pwr, nelems, ovr):
        self.wmax = max(self.wmax, pwr)
        self.wmin = min(self.wmin, pwr)
        if abs(pwr) < abs(self.pwr_min):
            self.pwr_min = pwr
        if ovr:
            self.overrange = True
        t_last = self.t_reading # Time of last reading (ms)
        self.t_reading = ticks_ms()
        if self.t_start is None:  # 1st reading
            self.t_start = self.t_reading  # Time of 1st reading
        else:
            self.joules += pwr * ticks_diff(self.t_reading, t_last) / 1000

        secs_since_start = ticks_diff(self.t_reading, self.t_start) / 1000  # Runtime
        mins, secs = divmod(int(secs_since_start), 60)
        hrs, mins = divmod(mins, 60)
        self.lbl_t.value('{:02d}:{:02d}:{:02d}'.format(hrs, mins, secs))
        if ovr:
            self.lbl_p.value('----')
        else:
            self.lbl_p.value('{:5.1f}W'.format(pwr))

        if self.showmean:
            self.lbl_pin.value('{:5.1f}W'.format(self.joules / max(secs_since_start, 1)))
        else:
            self.lbl_pin.value('{:5.1f}W'.format(self.wmin))

        self.lbl_pmin.value('{:5.1f}W'.format(self.pwr_min))
        if self.overrange:  # An overrange occurred during the measurement
            self.lbl_w_hr.value('----')
            self.lbl_pmax.value('----')
        else:
            self.lbl_pmax.value('{:5.1f}W'.format(self.wmax))
            units = self.joules / 3600
            if units < 1000:
                self.lbl_w_hr.value('{:6.0f}Wh'.format(units))
            else:
                self.lbl_w_hr.value('{:6.2f}KWh'.format(units / 1000))

    def buttonlist_cb(self, button, arg):
        self.showmean = arg

    def on_hide(self):
        mains_device.set_callback(None)  # Stop readings

    def after_open(self):
        mains_device.set_callback(self.reading)

def test():
    print('Running...')
    setup()
    Screen.change(BaseScreen)

test()
