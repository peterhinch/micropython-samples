# micropython-samples
The first part of this repo contains assorted code ideas for MicroPython. Many
are targeted at Pyboard variants. Some are intended as pointers to programmers
rather than being complete. Egregious bugs will be fixed but I may not accept
feature requests.

[Section 5](./README.md#5-module-index) is an index to complete applications
and modules which are documented and supported.

# 0. Index

 1. [Installation guides](./README.md#1-installation-guides)  
  1.1 [Installing MicroPython libraries](./README.md#11-installing-micropython-libraries)  
  1.2 [Fastbuild](./README.md#12-fastbuild) Build scripts and udev rules  
  1.3 [Installing PicoWeb](./README.md#13-installing-picoweb) For users of official firmware  
  1.4 [Buildcheck](./README.md#14-buildcheck) Check firmware build date  
  1.5 [Pyboard USB pitfall](./README.md#15-pyboard-usb-pitfall) Read this if you're new to Pyboards  
 2. [Hardware information and drivers](./README.md#2-hardware-information-and-drivers)  
  2.1 [ESP32](./README.md#21-esp32) Pinout and notes on the reference board  
  2.2 [SSD1306](./README.md#22-ssd1306) Write large fonts to the SSD1306.  
  2.3 [Pyboard D](./README.md#23-pyboard-d) Some information remains absent or hard to find in the docs.  
  2.4 [DS3231 precision RTC](./README.md#24-ds3231-precision-rtc) Use cheap hardware to calibrate Pyboard RTC.  
 3. [Essays](./README.md#3-essays) General thoughts.  
  3.1 [Resilient](./README.md#31-resilient) A guide to writing resilient WiFi code  
  3.2 [Serialisation](./README.md#32-serialisation) Review of MicroPython's four serialisation libraries  
  3.3 [Measurement of relative timing and phase of fast analog signals](./README.md#33-measurement-of-relative-timing-and-phase-of-fast-analog-signals) For Pyboard.  
 4. [Code samples](./README.md#4-code-samples) Samples prefixed Pyboard are Pyboard specific  
  4.1 [Pyboard Mutex](./README.md#41-pyboard-mutex) Share data between threads and ISR's.  
  4.2 [Pyboard watchdog](./README.md#42-pyboard-watchdog) Access a Pyboard hardware WDT.  
  4.3 [Software Watchdog](./README.md#43-software-watchdog) Cross-platform soft WDT.  
  4.4 [Reverse](./README.md#44-reverse) Reversal algorithms for bytearrays.  
  4.5 [Timed function](./README.md#45-timed-function) Time execution with a decorator.  
  4.6 [ESP8266 MQTT benchmark](./README.md#46-esp8266-mqtt-benchmark) Test performance of MQTT with official library.  
  4.7 [Rotary incremental encoder](./README.md#47-rotary-incremental-encoder) Fast, simple, proven algorithm.  
  4.8 [Pseudo random number generators](./README.md#48-pseudo-random-number-generators)  
  4.9 [Verifying incrementing sequences](./README.md#49-verifying-incrementing-sequences) Test communications drivers.  
  4.10 [Bitmaps](./README.md#410-bitmaps) Non-allocating ways to access bitmaps.  
  4.11 [Functors and singletons](./README.md#411-functors-and-singletons) Useful decorators.  
  4.12 [Quaternions](./README.md#412-quaternions) Scale, move and rotate 3D objects with minimal mathematics.  
  4.13 [A Pyboard power meter](./README.md#413-a-pyboard-power-meter) One of my own projects.  
 5. [Module Index](./README.md#5-module-index) Supported code. Device drivers, GUI's, utilities.  
  5.1 [uasyncio](./README.md#51-uasyncio) Tutorial and drivers for asynchronous coding.  
  5.2 [Memory Device Drivers](./README.md#52-memory-device-drivers) Drivers for nonvolatile memory devices.  
  5.3 [Inertial Measurement Units](./README.md#53-inertial-measurement-units) Gravity, gyro and magnetic sensors.  
  5.4 [Other hardware drivers](./README.md#54-other-hardware-drivers)  
  5.5.[Communications](./README.md#55-communications)  
  5.6 [Displays](./README.md#56-displays) Fonts, graphics, GUIs and display drivers  
  5.7 [Pyboard micropower](./README.md#57-pyboard-micropower)  
  5.8 [Pyboard DSP](./README.md#58-pyboard-dsp) Fourier transforms and filters.  
  5.9 [rshell](./README.md#59-rshell) Fork of rshell with text macros.  
  5.10 [Hard to categorise](./README.md#510-hard-to-categorise) Other modules.  

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

## 1.5 Pyboard USB pitfall

By default the Pyboard's `/flash/boot.py` enables MSC (mass storage) mode. This
makes the Pyboard look like a USB stick, making its filesystem visible to the
PC. This helpful feature ignores a fundamental flaw which leads to filesystem
corruption. This is because the USB standard requires mass storage devices to
behave like disks with static content. By contrast a Pyboard can independently
modify the "disk" contents causing chaos.

To fix this, edit `/flash/boot.py` so that the `usb_mode` line reads:
```python
pyb.usb_mode('VCP')
```
On reboot the Pyboard will no longer appear as a mass storage device on the PC.
Various tools are available to manage the device's storage via USB. I use
[rshell](https://github.com/dhylands/rshell).

# 2. Hardware information and drivers

## 2.1 ESP32

Pinout diagram for the reference board with notes and warnings about reserved
pins etc. See [this doc](./ESP32/ESP32-Devkit-C-pinout.pdf). See also this
excellent [resource](https://randomnerdtutorials.com/esp32-pinout-reference-gpios/).

## 2.2 SSD1306

A means of rendering multiple larger fonts to the SSD1306 OLED display. The
`Writer` class which performs this has been substantially improved and may now
be found as part of [this repository](https://github.com/peterhinch/micropython-font-to-py).

## 2.3 Pyboard D

Assorted [information](./pyboard_d/README.md) not yet in the official docs or
hard to find.

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

Fast [reverse](./reverse/reverse.py) a bytearray in Arm Thumb assembler: this
reverses the byte order of the array so `[1,2,3,4]` becomes `[4,3,2,1]`.  

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

The [encoder_portable.py](./encoders/encoder_portable.py) version should work on
all MicroPython platforms. Tested on ESP8266. Note that interrupt latency on
the ESP8266 limits performance. ESP32 has similar limitations.

## 4.8 Pseudo random number generators

On the Pyboard V1.1, true random numbers may be generated rapidly with
`pyb.rng()` which uses a hardware random number generator on the
microcontroller.

There are a few use-cases for pseudo random number generators. Some platforms
lack a hardware generator (e.g. the Pyboard Lite) and some ports don't support
`uos.urandom`. There is also a case for running a RNG in an interrupt service
routine.

Pseudo random number generators provide repeatable sequences of numbers which
can be an advantage, for example in testing. The RNG is seeded with an initial
value. On each call to the function it will return a random number, but (given
the same seed) the sequence of numbers following initialisation will always be
the same.

See [random.py](./random/random.py) for usage and timing documentation. The
[yasmarang generator](./random/yasmarang.py) is also included, along with my
own [cheap random](./random/cheap_rand.py). The latter constrains calculations
to 30 bits, allowing its use in an ISR. It comes with no guarantees of random
quality and the only statistical test is that the mean converges on the right
value. None of these generators are suitable for cryptography.

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
boolean array. So the set will be capable of storing integers from 0 to 255,
and the array will accept indices in the same range.

These classes are lightweight. For example the `IntSet` class does not include
all the dunder (magic) methods required to match the native `set` class. These
may readily be added as required.

## 4.11 Functors and singletons

Two simple class decorators for objects useful in hardware interfacing.
Documented [here](./functor_singleton/README.md).

Singletons denote classes for which only a single instance can ever occur.
They can be useful for hardware interface classes. Their use avoids the need
for a global instance: the sole instance may be retrieved efficiently from
anywhere in the code.

A functor is a class which is accessed via function call syntax. There is only
one instance, like a singleton. Initial access calls the constructor, with
subsequent accesses being via `__call__`. As an object it can retain state. As
an example, a functor might have a continuously running task: successive calls
modify the behaviour of the task.

## 4.12 Quaternions

Quaternions have a reputation for being mathematically difficult. Surely true
if you intend using them to write Maxwell's equations (as per Maxwell). If your
ambitions are limited to manipulating three dimensional objects or processing
IMU data they can be remarkably simple.

The `Quaternion` class lets you create, move, transform and rotate 3D objects.
They assume no maths beyond familiarity with an `xyz` coordinate system.
Includes a demo where a wireframe cube rotates in response to movements of a
BNo055 IMU, plus a demo of moving wireframe graphics. Neither demo uses trig
functions. See [the docs](./QUATERNIONS.md).

## 4.13 A pyboard power meter

This uses a Pyboard to measure the power consumption of mains powered devices. 
Unlike simple commercial devices it performs a true vector (phasor) measurement
enabling it to provide information on power factor and to work with devices
which generate as well as consume power. It uses the official LCD160CR display
as a touch GUI interface. It is documented [here](./power/README.md).

##### [Index](./README.md#0-index)

# 5. Module index

This index references applications and device drivers that I have developed, in
some cases as collaborations. This is acknowledged in their respective docs.

Unlike the code samples these are fully documented and supported.

## 5.1 uasyncio

[Tutorial](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/TUTORIAL.md)  
[Drivers](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/DRIVERS.md)
Asynchronous device drivers for switches, pushbuttons and ADC's. Also has
information on interfacing interrupts to uasyncio.  
[Schedule](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/SCHEDULE.md)
Schedule events at specified times and dates.  
[HTU21D](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/HTU21D.md)
Asynchronous driver for this temperature and humidity sensor.  
[I2C Slave](https://github.com/peterhinch/micropython-async/tree/master/v3/docs)
Uses the Pyboard's I2C slave mode to implement a full duplex asynchronous
link. Principal use case is for ESP8266 which has only one UART.  
[GPS](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/GPS.md)
See [section 5.4](./README.md#54-other-hardware-drivers).  

## 5.2 Memory device drivers

[EEPROM](https://github.com/peterhinch/micropython_eeprom) Support for EEPROM,
FRAM and Flash chips and modules. In all cases devices or sets of devices can
be configured as a single memory array supporting access either as an array of
bytes or as a filesystem.  

## 5.3 Inertial Measurement Units

[BNo055](https://github.com/micropython-IMU/micropython-bno055) In my view the
best IMU as it performs internal sensor fusion.  
[MPU9x50](https://github.com/micropython-IMU/micropython-mpu9x50) Driver for
the popular InvenSense MPU9250, MPU9150, MPU6050 devices.  
[BMP180](https://github.com/micropython-IMU/micropython-bmp180) Driver for the
Bosch BMP180 pressure/temperature sensor.  
[Fusion](https://github.com/micropython-IMU/micropython-fusion) Sensor fusion:
combine IMU readings to produce heading, pitch and roll or Quaternion data.  
[Quaternions](./README.md#412-quaternions) The proper way to deal with 3D
rotations. Amazingly requires less maths than Euler angles.  

## 5.4 Other hardware drivers

[Asynchronous GPS driver](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/GPS.md)  
[Thermal IR](https://github.com/peterhinch/micropython-amg88xx) Support for the
Adafruit 3538 thermal camera. Includes optional bicubic interpolation.  
[Audio](https://github.com/peterhinch/micropython-vs1053) High quality audio
I/O with the Adafruit VS1053 board. Synchronous and asynchronous options.  
[IR remotes](https://github.com/peterhinch/micropython_ir) Support for various
infra red protocols in receiver or transmitter ('blaster') applications.  
[433MHz remote](https://github.com/peterhinch/micropython_remote) Supports
433MHz remote controlled wall sockets. Captures the signal enabling replay so
that mains devices may safely be controlled at low cost.  
[BME280](https://github.com/peterhinch/mpy_bme280_esp8266) A bugfix fork of an
abandoned project. Supports the BME280 combined temperature, pressure and
humidity sensor on ESP8266.  

## 5.5 Communications

[Asynchronous MQTT](https://github.com/peterhinch/micropython-mqtt/blob/master/mqtt_as/README.md)
This improves on official MQTT drivers by recovering from WiFi outages and
offering asynchronous operation.  
[IOT](https://github.com/peterhinch/micropython-iot) An IOT solution. Provides
a socket-like interface between WiFi clients and a server with wired ethernet.
The interface is resilient in the presence of WiFi outages. The server (e.g.
Raspberry Pi) does any internet work, improving security.  
[Radio](https://github.com/peterhinch/micropython-radio) Simplify use of the
officially supported NRF24l01 radio.  

## 5.6 Displays

Fonts, graphics, GUIs and display drivers.

All GUIs except e-paper are based on uasyncio. Where input is supported a
callback-based interface is povided.

[font-to-py](https://github.com/peterhinch/micropython-font-to-py) Converts
industry standard font files to Python source which may be frozen as bytecode.
Files use minimal RAM when frozen.  
[writer](https://github.com/peterhinch/micropython-font-to-py/blob/master/writer/WRITER.md)
A simple way to render text to displays where the driver is subclassed from
`framebuf`.  
[nano-gui](https://github.com/peterhinch/micropython-nano-gui) Simple output
only GUI for displays where the driver is subclassed from `framebuf`. Repo
includes display drivers for various displays including TFT, OLED, ePaper and
Sharp. Supports a range of hosts with low RAM usage.  
[micro-gui](https://github.com/peterhinch/micropython-micro-gui) Derived from
nano-gui and supporting the same displays and hosts, this provides for user
input via pushbuttons or a navigation joystick.  
[LCD160CR](https://github.com/peterhinch/micropython-lcd160cr-gui) Touch GUI
for the official display module.  
[TFT-GUI](https://github.com/peterhinch/micropython-tft-gui) A fast touch GUI
for large displays based on SSD1963 controller with XPT2046 touch controller.  
[RA8875-GUI](https://github.com/peterhinch/micropython_ra8875) Touch GUI for
large displays based on the RA8875 controller (e.g. from Adafruit).  
[e-paper](https://github.com/peterhinch/micropython-epaper) GUI for the
Embedded Artists 2.7 inch e-paper display. Pyboard only. Sadly these displays
are now obsolete.  

## 5.7 Pyboard micropower

[micropower](https://github.com/peterhinch/micropython-micropower) Support for
low power applications on Pyboard 1.x and Pyboard D.  

## 5.8 Pyboard DSP

[fourier](https://github.com/peterhinch/micropython-fourier) DFT using Arm
Thumb assembler. Primarily for processing data received on an ADC.  
[Filters](https://github.com/peterhinch/micropython-filters) FIR filters
using ARM Thumb assembler. Using an online utility you can go from a graph
of required frequency response to a filter implementation.  

## 5.9 rshell

[rshell](https://github.com/peterhinch/rshell) is a fork of Dave Hylands'
excellent utility. My fork adds text macros to improve its power and
usability, notably when maintaining complex Python packages. The fork includes
documentation, but [these notes](./RSHELL_MACROS.md) provide a usage example
where each project has its own set of automatically loaded macros.__

## 5.10 Hard to categorise

[data to py](https://github.com/peterhinch/micropython_data_to_py) Convert
arbitrary objects to Python files which may be frozen as bytecode. Can be
used to freeze images for display.  

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
