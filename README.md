# micropython-samples
A place for assorted code ideas for MicroPython. Most are targeted at the
Pyboard variants.

# 0. Index

 1. [Installation guides](./README.md#1-installation-guides)  
  1.1 [Installing MicroPython libraries](./README.md#11-installing-micropython-libraries)  
  1.2 [Fastbuild](./README.md#12-fastbuild) Build scripts and udev rules  
  1.3 [Installing PicoWeb](./README.md#13-installing-picoweb) For users of official firmware  
  1.4 [Buildcheck](./README.md#14-buildcheck) Check firmware build date  
 2. [Hardware information and drivers](./README.md#2-hardware-information-and-drivers)  
  2.1 [ESP32](./README.md#21-esp32) Pinout and notes on the reference board  
  2.2 [SSD1306](./README.md#22-ssd1306) Write large fonts to the SSD1306  
  2.3 [Pyboard D](./README.md#23-pyboard-d) Assorted scraps of information  
  2.4 [DS3231 precision RTC](./README.md#24-ds3231-precision-rtc) Use cheap hardware to calibrate Pyboard RTC  
 3. [Essays](./README.md#3-essays) General thoughts  
  3.1 [Resilient](./README.md#31-resilient) A guide to writing resilient WiFi code  
  3.2 [Serialisation](./README.md#32-serialisation) Review of MicroPython's four serialisation libraries  
  3.3 [Measurement of relative timing and phase of fast analog signals](./README.md#33-measurement-of-relative-timing-and-phase-of-fast-analog-signals) For Pyboard.  
 4. [Code samples](./README.md#4-code-samples) Samples prefixed Pyboard are Pyboard specific  
  4.1 [Pyboard Mutex](./README.md#41-pyboard-mutex) Share data between threads and ISR's.  
  4.2 [Pyboard watchdog](./README.md#42-pyboard-watchdog) Access a Pyboard hardware WDT  
  4.3 [Software Watchdog](./README.md#43-software-watchdog) Cross-platform soft WDT  
  4.4 [Reverse](./README.md#44-reverse) Reversal algorithms for bytearrays  
  4.5 [Timed function](./README.md#45-timed-function) Time execution with a decorator  
  4.6 [ESP8266 MQTT benchmark](./README.md#46-esp8266-mqtt-benchmark) Test performance of MQTT with official library  
  4.7 [Rotary incremental encoder](./README.md#47-rotary-incremental-encoder) Fast, simple, proven algorithm  
  4.8 [A pseudo random number generator](./README.md#48-a-pseudo-random-number-generator)  
  4.9 [Verifying incrementing sequences](./README.md#49-verifying-incrementing-sequences) Test communications drivers  
  4.10 [Bitmaps](./README.md#410-bitmaps) Non-allocating ways to access bitmaps  
  4.11 [Functors and singletons](./README.md#411-functors-and-singletons) Useful decorators  
  4.12 [A Pyboard power meter](./README.md#412-a-pyboard-power-meter) One of my own projects  

# 1. Installation guides

## 1.1 Installing MicroPython libraries

This is more involved since the advent of the pycopy fork of MicroPython.
[This doc](./micropip/README.md) describes the issues and provides a utility
to simplify installation for users of official MicroPython firmware.

## 1.2 Fastbuild

Scripts for building MicroPython for various target hardware types and for
updating your local source. Now detects and builds for Pyboard D. See
[docs](./fastbuild/README.md)

## 1.3 Installing PicoWeb

Paul Sokolovsk's [PicoWeb](https://github.com/pfalcon/picoweb) requires his
fork of MicroPython.

Some time ago I was asked what was involved to install it on official firmware.
Changes were minor. However it should be stressed that while the version here
works, it is not up to date. See the [Easy installation](./PICOWEB.md) guide.

PR's with updated versions of PicoWeb are welcome.

## 1.4 Buildcheck

Raise an [exception](./buildcheck/buildcheck.py) if a firmware build is earlier
than a given date.

# 2. Hardware information and drivers

## 2.1 ESP32

Pinout diagram for the reference board with notes and warnings about reserved
pins etc. See [this doc](./ESP32/ESP32-Devkit-C-pinout.pdf).

## 2.2 SSD1306

A means of rendering multiple larger fonts to the SSD1306 OLED display. The
`Writer` class which performs this has been substantially improved and may now
be found as part of [this repository](https://github.com/peterhinch/micropython-font-to-py).

## 2.3 Pyboard D

Assorted [information](./pyboard_d/README.md) not yet in the official docs).

## 2.4 DS3231 precision RTC

This is a low cost precision battery backed real time clock (RTC) accurate to
+-2 minutes/year. Two drivers are provided, one portable across platforms and
one which is Pyboard specific.

The Pyboard-specific driver provides a facility to calibrate the Pyboard's RTC
from the DS3231. Calibration to high precision may be achieved in five minutes.

The drivers are [documented here](./DS3231/README.md).

##### [Index](./README.md#0-index)

# 3. Essays

## 3.1 Resilient

A [guide](./resilient/README.md) to writing reliable ESP8266 networking code.
Probably applies to other WiFi connected MicroPython devices.

## 3.2 Serialisation

[A discussion](./SERIALISATION.md) of the need for serialisation and of the
relative characteristics of four libraries available to MicroPython. Includes a
tutorial on a Protocol Buffer library.

## 3.3 Measurement of relative timing and phase of fast analog signals

This describes ways of using the Pyboard to perform precision measurements of
analog signals of up to around 50KHz. It is documented [here](./phase/README.md).

##### [Index](./README.md#0-index)

# 4. Code samples

## 4.1 Pyboard mutex

A [class](./mutex/README.md) providing mutual exclusion enabling hard interrupt
handlers and the main program to access shared data in a manner which ensures
data integrity.

## 4.2 Pyboard watchdog

[Access](./watchdog/wdog.py) the simpler of the Pyboard's watchdog timers.

## 4.3 Software watchdog

A [software watchdog](./soft_wdt/soft_wdt.py) timer with a fixed or variable
timeout. Supports temporary suspension and permanent cancellation. The latter
can be useful when debugging code to prevent a machine reboot when the
application fails, terminates or is interrupted with ctrl-c. See code and
comments in [the test script](./soft_wdt/swdt_tests.py).

## 4.4 Reverse

Fast [reverse](./reverse/reverse.py) a bytearray in Arm Thumb assembler.  
Also includes cross-platform Python code to bit-reverse (fast-ish) 8, 16 and 32
bit words.

## 4.5 Timed function

Time a function's execution using a [decorator](./timed_function/timed_func.py)
and implement timeouts using a [closure](./timed_function/timeout.py).

##### [Index](./README.md#0-index)

## 4.6 ESP8266 MQTT benchmark

[This benchmark](./ESP8266/benchmark.py) tests the performance of MQTT by
periodically publishing while subscribed to the same topic. Measures the
round-trip delay. Uses the official `umqtt.simple` library. Adapt to suit your
server address and desired QOS (quality of service, 0 and 1 are supported).
After 100 messages reports maximum and minimum delays.

[This connect utility](./esp32/conn.py) connects in station mode using saved
connection details where possible.

## 4.7 Rotary Incremental Encoder

Classes for handling incremental rotary position encoders. Note Pyboard timers
can do this in hardware. These samples cater for cases where that solution
can't be used. The [encoder_timed.py](./encoders/encoder_timed.py) sample
provides rate information by timing successive edges. In practice this is
likely to need filtering to reduce jitter caused by imperfections in the
encoder geometry.

There are other algorithms but this is the simplest and fastest I've
encountered.

These were written for encoders producing TTL outputs. For switches, adapt the
pull definition to provide a pull up or pull down as required.

The [encoder_portable.py](./encoders/encoder_portable) version should work on
all MicroPython platforms. Tested on ESP8266. Note that interrupt latency on
the ESP8266 limits performance. ESP32 has similar limitations.

## 4.8 A pseudo random number generator

On the Pyboard V1.1, true random numbers may be generated rapidly with
`pyb.rng()` which uses a hardware random number generator on the
microcontroller.

There are two use cases for the pseudo random number generator. Firstly on
platforms lacking a hardware generator (e.g. the Pyboard Lite). And secondly
where repeatable results are required, for example in testing. A pseudo random
number generator is seeded with an arbitrary initial value. On each call to the
function it will return a random number, but (given the same seed) the sequence
of numbers following initialisation will always be the same.

See [random.py](./random/random.py) for usage and timing documentation.

## 4.9 Verifying incrementing sequences

When testing communications applications it is often necessary to check for
missing, duplicated, or out-of-order messages. To do this, the transmitter test
script ensures that messages include an incrementing message number. The
receiver script verifies the sequence. [The CheckMid class](./sequence/check_mid.py)
does this, also detecting transmitter reboots

##### [Index](./README.md#0-index)

## 4.10 Bitmaps

A bitmap stored in a pre-allocated, fixed size bytearray may be viewed in two
ways:
 1. As a set of positive integers whose values are constrained within limits.
 2. As a fixed size one dimensional array of booleans.

These views provide a Pythonic interface while retaining the non-allocating
performance advantage relative to native sets and lists.

The file [bitmap.py](./bitmap/bitmap.py) offers classes supporting these views.

The constraint `0 <= value <= max_value` applies where `max_value` is a
constructor arg. The `max_value` arg defines the size of the underlying
bytearray. For example if `max_value` is 255, the bytearray will use 32 bytes.
The constraint applies to member values of a set, and to index values of a
boolean array.

These classes are lightweight. For example the `IntSet` class does not include
all the dunder (magic) methods required to match the native `set` class. These
may readily be added as required.

## 4.11 Functors and singletons

Two simple class decorators for objects useful in hardware interfacing.
Documented [here](./functor_singleton/README.md).

Singletons denote classes for which only a single instance will ever occur.
They are contentious in some circles, on the grounds that the single instance
guarantee may be violated in a specification change. They can be useful in
hardware contexts where a chip design is unlikely suddenly to change.
Singletons denoting hardware interfaces avoid globals and the need to pass
references around.

A functor is a class which is accessed via function call syntax. There is only
one instance, like a singleton. Initial access calls the constructor, with
subsequent accesses being via `__call__`. As an object it can retain state. As
an example, a functor might have a continuously running task: successive calls
modify the behaviour of the task.

# 4.12 A pyboard power meter

This uses a Pyboard to measure the power consumption of mains powered devices. 
Unlike simple commercial devices it performs a true vector (phasor) measurement
enabling it to provide information on power factor and to work with devices
which generate as well as consume power. It uses the official LCD160CR display
as a touch GUI interface. It is documented [here](./power/README.md).

##### [Index](./README.md#0-index)

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
