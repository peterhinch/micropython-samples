# micropython-samples
A place for assorted code ideas for MicroPython. Most are targeted at the
Pyboard variants.

# Fastbuild

Scripts for building MicroPython for various target hardware types and for
updating your local source. See [docs](./fastbuild/README.md)

# ssd1306

A means of rendering multiple larger fonts to the SSD1306 OLED display. See
[docs](./SSD1306/README.md).

# mutex

A class providing mutual exclusion enabling interrupt handlers and the main
program to access shared data in a manner which ensures data integrity.

# watchdog

Access the simpler of the Pyboard's watchdog timers.

# reverse

Fast reverse a bytearray in Arm Thumb assembler.  
Python code to bit-reverse (fast-ish) 8, 16 and 32 bit words.

# DS3231

This is a low cost precision battery backed real time clock (RTC) accurate to
+-2 minutes/year. Two drivers are provided, one portable across platforms and
one which is Pyboard specific.

The Pyboard-specific driver provides a facility to calibrate the Pyboard's RTC
from the DS3231. Calibration to high precision may be achieved in five minutes.

The drivers are [documented here](./DS3231/README.md).

# Buildcheck

Raise an exception if a firmware build is earlier than a given date.

# timed_function

Time a function's execution using a decorator.

# ESP8266 (MQTT benchmark)

benchmark.py Tests the performance of MQTT by periodically publishing while
subscribed to the same topic. Measures the round-trip delay. Adapt to suit your
server address and desired QOS (quality of service, 0 and 1 are supported).
After 100 messages reports maximum and minimum delays.

`conn.py` Connect in station mode using saved connection details where possible.

# Rotary Incremental Encoder

Classes for handling incremental rotary position encoders. Note that the Pyboard
timers can do this in hardware. These samples cater for cases where that
solution can't be used. The `encoder_timed.py` sample provides rate information by
timing successive edges. In practice this is likely to need filtering to reduce
jitter caused by imperfections in the encoder geometry.

There are other algorithms but this is the simplest and fastest I've encountered.

These were written for encoders producing TTL outputs. For switches, adapt the
pull definition to provide a pull up or pull down as required.

The `encoder.portable.py` version should work on all MicroPython platforms.
Tested on ESP8266. Note that interrupt latency on the ESP8266 limits
performance. ESP32 has similar limitations.

# A pseudo random number generator

On the Pyboard V1.1, true random numbers may be generated rapidly with pyb.rng()
which uses a hardware random number generator on the microcontroller.

There are two use cases for the pseudo random number generator. Firstly on
platforms lacking a hardware generator (e.g. the Pyboard Lite). And secondly
where repeatable results are required, for example in testing. A pseudo random
number generator is seeded with an arbitrary initial value. On each call to the
function it will return a random number, but (given the same seed) the sequence
of numbers following initialisation will always be the same.

See the code for usage and timing documentation.

# micropip

This is a version of upip which runs under Python 3.2 or above. It is intended
for users of hardware which is not network enabled. Libraries may be installed
to the PC for transfer to the target. Usage is the same as for the official
`upip.py` and help may be accessed with

```
micropip.py --help
```
or

```
python3 -m micropip --help
```

Its advantage over running `upip.py` on a PC is that it avoids the need for a
Linux installation and having to compile the Unix build of MicroPython.

# Measurement of relative timing and phase of fast analog signals

This describes ways of using the Pyboard to perform precision measurements of
analog signals of up to around 50KHz. It is documented [here](./phase/README.md).

# A design for a hardware power meter

This uses a Pyboard to measure the power consumption of mains powered devices. 
Unlike simple commercial devices it performs a true vector (phasor) measurement
enabling it to provide information on power factor and to work with devices
which generate as well as consume power. It uses the official LCD160CR display
as a touch GUI interface. It is documented [here](./power/README.md).

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
