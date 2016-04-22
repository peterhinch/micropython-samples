
import gc
from font14 import font14
from tft import TFT, LANDSCAPE
from usched import Sched
from asynctouch import TOUCH
from button import Button, Buttonset, RadioButtons
from ui import CIRCLE, RECTANGLE, CLIPPED_RECT
#gc.collect()

def callback(button, args):
    arg = args[0]
    print('Returned: ', arg)
    tft = button.tft
    tft.setTextPos(0, 240)
    tft.setTextStyle(None, None, 0, font14)
    tft.printString('Button argument zero: {}  '.format(arg))
    if arg == 'Q':
        button.objsched.stop()

#gc.collect()
# These tables contain args that differ between members of a set of related buttons
table = [
    {'fgcolor' : (0, 128, 0), 'litcolor' : (0, 255, 0), 'text' : 'Yes', 'args' : ('A'), 'fontcolor' : (0, 0, 0)},
    {'fgcolor' : (255, 0, 0), 'text' : 'No', 'args' : ('B')},
    {'fgcolor' : (0, 0, 255), 'text' : '???', 'args' : ('C'), 'fill': False},
    {'fgcolor' : (128, 128, 128), 'text' : 'Quit', 'args' : ('Q'), 'shape' : CLIPPED_RECT},
]

# similar buttons: only tabulate data that varies
table2 = [
    {'text' : 'P', 'args' : ('p')},
    {'text' : 'Q', 'args' : ('q')},
    {'text' : 'R', 'args' : ('r')},
    {'text' : 'S', 'args' : ('s')},
]

# A Buttonset with two entries
# If buttons to be used in a buttonset, Use list rather than tuple for args because buttonset appends.

table3 = [
     {'fgcolor' : (0, 255, 0), 'shape' : CLIPPED_RECT, 'text' : 'Start', 'args' : ['Live']},
     {'fgcolor' : (255, 0, 0), 'shape' : CLIPPED_RECT, 'text' : 'Stop', 'args' : ['Die']},
]

table4 = [
    {'text' : '1', 'args' : ('1')},
    {'text' : '2', 'args' : ('2')},
    {'text' : '3', 'args' : ('3')},
    {'text' : '4', 'args' : ('4')},
]

#gc.collect()
# THREADS

def stop(fTim, objsched):                                     # Stop the scheduler after fTim seconds
    yield fTim
    objsched.stop()

# USER TEST FUNCTION

def test(duration = 0):
    if duration:
        print("Test TFT panel for {:3d} seconds".format(duration))
    else:
        print('Testing TFT...')
    objsched = Sched()                                      # Instantiate the scheduler
    mytft = TFT("SSD1963", "LB04301", LANDSCAPE)
    mytouch = TOUCH(objsched, "XPT2046")
    mytft.backlight(100) # light on

# Button assortment
    x = 50
    for t in table:
        Button(objsched, mytft, mytouch, (x, 0), font = font14, callback = callback, **t)
        x += 70

# Highlighting buttons
    x = 50
    for t in table2:
        Button(objsched, mytft, mytouch, (x, 60), font = font14, fgcolor = (128, 128, 128),
               fontcolor = (0, 0, 0), litcolor = (255, 255, 255), callback = callback, **t)
        x += 70

# On/Off toggle
    x = 50
    bs = Buttonset(callback)
    for t in table3: # Buttons overlay each other at same location
        bs.add_button(objsched, mytft, mytouch, (x, 120), font = font14, fontcolor = (0, 0, 0), **t)
    bs.run()

# Radio buttons
    x = 50
    rb = RadioButtons(callback, (0, 0, 255)) # color of selected button
    for t in table4:
        rb.add_button(objsched, mytft, mytouch, (x, 180), font = font14, fontcolor = (255, 255, 255),
                      fgcolor = (0, 0, 90), height = 30, **t)
        x += 40
    rb.run()

# Start scheduler
    if duration:
        objsched.add_thread(stop(duration, objsched))       # Commit suicide after specified no. of seconds
    objsched.run()                                          # Run it!

test() # Forever: we have a Quit button!
