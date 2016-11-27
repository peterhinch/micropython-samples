# micropython-samples
A place for assorted code ideas for MicroPython. Most are targeted at the Pyboard variants.

## fastbuild - Pull and build Pyboard firmware under Linux
These scripts are intended to speed and simplify rebuilding firmware from
source notably where pyboards of different types are in use, or when
frozen bytecode necessitates repeated compilation and deployment. In
particular ``buildpyb`` will detect the attached Pyboard type, build the
appropriate firmware, put the board into DFU mode and deploy it, before
launching ``rshell``. The latter step may be removed if ``rshell`` is not
in use.

Includes udev rules to avoid jumps from ``/dev/ttyACM0`` to ``/dev/ttyACM1``
by ensuring Pyboards of all types appear as ``/dev/pyboard``. Rules are also
offered for USB connected WiPy (V1.0) and FTDI USB/serial adaptors.

These scripts use Python scripts ``pyb_boot`` to put the Pyboard into DFU mode
and ``pyb_check`` to determine the type of attached board. These use the
``pyboard.py`` module in the source tree to execute scripts on the attached
board.

### Edits

``buildnew`` and ``buildpyb`` will need editing to point to your micropython
directory.

In the ``buildpyb`` script you may wish to edit the ``-j 8`` argument to ``make``.
This radically speeds build on a multi core PC. Empirically 8 gave the fastest
build on my core i7 4/8 core laptop: adjust to suit your PC. You may also want
to alter the call to ``rshell``.

The script assumes a frozen modules directory ``stmhal/modules``. You may wish
to change this. A recent update enabled the directory for frozen to be located
anywhere in the filesystem.

In ``buildpyb`` you may wish to delete the unix make commands.

### Dependencies

Python3.x  
pyserial ``apt-get install python3-serial``.  
Verify that ``pyboard.py`` in the tools directory of the source tree works
(tests in comments at the start of the code).  
Copy ``49-micropython.rules`` to (on most distros) ``/etc/udev/rules.d``.

### Build script: ``buildpyb``  
This checks the attached pyboard. If it's a V1.0, V1.1 or Lite it builds the
correct firmware and deploys it. Otherwise it produces an error message.

Optional argument ``--clean`` - if supplied does a ``make clean`` to delete
all files produced by the previous build before proceeding.

### Update source: ``buildnew``

Report state of master branch, update sources and issue ``make clean`` for cross
compiler, Pyboard variants, and ESP8266. Builds cross compiler and unix port.

### ESP8266 Build

``buildesp`` A script to build and deploy ESP8266 firmware. Accepts optional
``--clean`` argument.

## ssd1306

A means of rendering multiple larger fonts to the SSD1306 OLED display

## mutex
A class providing mutal exclusion enabling interrupt handlers and the main program to access shared
data in a manner which ensures data integrity.

## watchdog
Access the simpler of the Pyboard's watchdog timers.

## reverse
Fast reverse a bytearray.

## font
Convert a C file produced by GLCD Font Creator to Python for storage as persistent byte code.

## ds3231_pb
Driver for the DS3231 low cost precison RTC, including a facility to calibrate the Pyboard's RTC
from the DS3231.

## Buildcheck
Raise an exception if a firmware build is earlier than a given date.

## timed_function
Time a function's execution using a decorator

## ESP8266
benchmark.py Tests the performance of MQTT by periodically publishing while subscribed to
the same topic. Measures the round-trip delay. Adapt to suit your server address and desired
QOS (quality of service, 0 and 1 are supported). After 100 messages reports maximum and
minimum delays.

conn.py Connect in station mode using saved connection details where possible

## Rotary Incremental Encoder

Classes for handling incremental rotary position encoders. Note that the Pyboard timers can
do this in hardware. These samples cater for cases where that solution can't be used. The
encoder_timed.py sample provides rate information by timing successive edges. In practice this
is likely to need filtering to reduce jitter caused by imperfections in the encoder geometry.

There are other algorithms but this is the simplest and fastest I've encountered.

These were written for encoders producing TTL outputs. For switches, adapt the pull definition
to provide a pull up or pull down as required.

# License

Any code placed here is released under the MIT License (MIT).  
The MIT License (MIT)  
Copyright (c) 2016 Peter Hinch  
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
