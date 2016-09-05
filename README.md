# micropython-samples
A place for assorted code ideas for MicroPython. Most are targeted at the Pyboard variants.

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

## fastbuild - Pyboard use under Linux
Build MicroPython with your frozen bytecode, put the Pyboard into DFU mode, and deploy the build to
the board with a single command. Takes just over 60 seconds on a fast PC. Note the use of make's j
argument to use mutliple cores. Empirically 8 gave the fastest build on my core i7 4/8 core laptop:
adjust to suit your PC.

Includes udev rules to avoid jumps from /dev/ttyACM0 to /dev/ttyACM1: ensures Pyboards of all types
appear as /dev/pyboard. Also rules for USB connected WiPy and FTDI USB/serial adaptor.

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
Copyright (c) 2015 Peter Hinch  
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
