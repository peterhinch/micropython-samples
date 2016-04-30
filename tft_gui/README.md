# micropython-gui

Provides a simple touch driven event based GUI interface for the Pyboard when used with a TFT
display. The latter should be based on SSD1963 controller with XPT2046 touch controller. Such
displays are available in electronics stores and on eBay. The software is based on drivers for the
TFT and touch controller from Robert Hammelrath together with a cooperative scheduler of my own
design.

It is targeted at hardware control and display applications.

# Pre requisites

[TFT driver](https://github.com/robert-hh/SSD1963-TFT-Library-for-PyBoard.git)
[XPT2046 driver](https://github.com/robert-hh/XPT2046-touch-pad-driver-for-PyBoard.git)
[Scheduler](https://github.com/peterhinch/Micropython-scheduler.git)

Core files:
 1. TFT_io.py Low level TFT driver *
 2. touch.py Touch controller driver *
 3. tft.py TFT driver
 4. usched.py Scheduler
 5. delay.py Used with the scheduler for watchdog type delays.
 6. ugui.py The micro GUI library.

Optional files:
 1. font10.py Font used by the test programs.
 2. font14.py Font used by the test programs.

Test/demo programs:
 1. vst.py A test program for vertical linear sliders.
 2. hst.py Tests horizontal slider controls, meters and LED.
 3. buttontest.py Pushbuttons and checkboxes.
 4. knobtest.py Rotary control test.

It should be noted that by the standards of the Pyboard this is a large library. Attempts to use it
in the normal way are likely to provoke memory errors owing to heap fragmentation. It is
recommended that the core and optional files are included with the firmware as persistent bytecode.
You may also want to include any other fonts you plan to use. The first two core files listed above
cannot be included as they use inline assembler. Instructions on how to do this may be found
[here](http://forum.micropython.org/viewtopic.php?f=6&t=1776).

It is also wise to issue ctrl-D to soft reset the Pyboard before importing a module which uses the
library. The test programs require a ctrl-D before import.

Instructions on creating font files may be found in the README for the TFT driver listed above.

# Concepts

### Coordinates

In common with most displays, the top left hand corner of the display is (0, 0) with increasing
values of x to the right, and increasing values of y downward. Display objects exist within a
rectangular bounding box; in the case of touch sensitive controls this corresponds to the sensitive
region. The location of the object is defined as the coordinates of the top left hand corner of the
bounding box. Locations are defined as a 2-tuple (x, y).

### Colours

These are defined as a 3-tuple (r, g, b) with values of red, green and blue in range 0 to 255. The
interface uses the American spelling (color) throughout for consistency with the TFT library.

### Callbacks

The interface is event driven. Optional callbacks may be provided which will be executed when a
given event occurs. A callback function receives positional arguments. The first is a reference to
the object raising the callback. Subsequent arguments are user defined, and are specified as a list
of items. Note that a list rather than a tuple should be used.

# Initialisation Code

# Displays

These classes provide ways to display data and are not touch sensitive.

## Class Label

Displays text in a fixed length field. Constructor mandatory positional arguments:
 1. ``tft`` The TFT object.
 2. ``location`` 2-tuple defining position.
Keyword only arguments:
 1. ``font`` Mandatory. Font object to use.
 2. ``width`` Mandatory. The width of the object in pixels.
 3. ``border`` Border width in pixels - typically 2. If omitted, no border will be drawn.
 4. ``fgcolor`` Color of border. Defaults to system color.
 5. ``bgcolor`` Background color of object. Defaults to system background.
 6. ``fontcolor`` Text color. Defaults to system text color.
 7. ``text`` Initial text. Defaults to ''.
Method:
 1. ``show`` Argument: ``text``. Displays the string in the label.

## Class Dial

Displays angles in a circular dial. Angles are in radians with zero represented by a vertical
pointer. Positive angles appear as clockwise rotation of the pointer. The object can display
multiple angles using pointers of differing lengths (e.g. clock face). Constructor mandatory
positional arguments:
 1. ``tft`` The TFT object.
 2. ``location`` 2-tuple defining position.
Keyword only arguments (all 
 1. ``height`` Dimension of the square bounding box. Default 100 pixels.
 2. ``fgcolor`` Color of border. Defaults to system color.
 3. ``bgcolor`` Background color of object. Defaults to system background.
 4. ``border`` Border width in pixels - typically 2. If omitted, no border will be drawn.
 5. ``pointers`` Tuple of floats in range 0 to 0.9. Defines the length of each pointer as a
 proportion of the dial diameter. Default (0.9,) i.e. one pointer.
 6. ``ticks`` Defines the number of graduations around the dial. Default 4.
Method:
 1. ``show`` Displays an angle. Arguments: ``angle`` (mandatory), ``pointer`` the pointer index
 (default 0).

## Class LED

Displays a boolean state. Can display other information by varying the color. Constructor mandatory
positional arguments:
 1. ``tft`` The TFT object.
 2. ``location`` 2-tuple defining position.
Keyword only arguments:
 1. ``height`` Dimension of the square bounding box. Default 30 pixels.
 2. ``fgcolor`` Color of border. Defaults to system color.
 3. ``bgcolor`` Background color of object. Defaults to system background.
 4. ``border`` Border width in pixels - typically 2. If omitted, no border will be drawn.
 5. ``color`` The color of the LED.
Methods:
 1. ``off`` No arguments. Turns the LED off.
 2. ``on`` Optional arguemnt ``color``. Turns the LED on. By default it will use the ``color``
 specified in the constructor.

## Class Meter

This displays a single value in range 0.0 to 1.0 on a vertical linear meter. Constructor mandatory
positional arguments:
 1. ``tft`` The TFT object.
 2. ``location`` 2-tuple defining position.
Keyword only arguments:
 1. ``height`` Dimension of the bounding box. Default 200 pixels.
 2. ``width`` Dimension of the bounding box. Default 30 pixels.
 3. ``font`` Font to use in any legends. Default: ``None`` No legends will be displayed.
 4. ``legends`` A tuple of strings to display on the centreline of the meter. These should be
 short to physically fit. They will be displayed equidistantly along the vertical scale, with
 string 0 at the bottom. Default ``None``: no legends will be shown.
 5. ``divisions`` Count of graduations on the meter scale. Default 10.
 6. ``fgcolor`` Color of border. Defaults to system color.
 7. ``bgcolor`` Background color of object. Defaults to system background.
 8. ``fontcolor`` Text color. Defaults to system text color.
 9. ``pointercolor`` Color of meter pointer. Defaults to ``fgcolor``.
 10. ``value`` Initial value to display. Default 0.
Methods:
 1.``value`` Optional argument ``val``. If set, refreshes the meter display with a new value,
 otherwise returns its current value.

