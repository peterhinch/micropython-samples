# The DS3231 real time clock chip

This is a remarkably inexpensive and easily interfaced battery-backed RTC. It
is an ideal way rapidly to calibrate the Pyboard's RTC which can then achieve
similar levels of accuracy (+- ~2 mins/year). The chip can also provide
accurate time to platforms lacking a good RTC (notably the ESP8266).

Three drivers are provided:
 1. `ds3231_gen.py` General purpose portable driver supporting alarms.
 2. `ds3231_port.py` Portable driver: main purpose is to test accuracy of a
 platform's RTC.
 3. `ds3231_pb.py` A Pyboard-specific driver with RTC calibration facility. For
 Pyboard 1.x and Pyboard D.

Breakout boards are widely available. The interface is I2C. Pullups to 3.3V
(typically 10KΩ) should be provided on the `SCL` and `SDA` lines if these are
not supplied on the breakout board.

Drivers 2 and 3 use edge detection to achieve millisecond-level precision from
the DS3231. This enables relatively rapid accuracy testing of the platform's
RTC, and fast calibration of the Pyboard's RTC. To quantify this, a
sufficiently precise value of calibration may be acquired in 5-10 minutes.

###### [Main README](../README.md)

# 1. General purpose driver ds3231_gen.py

This uses datetime tuples to set and read time values. These are of form  
(year, month, day, hour, minute, second, weekday, yearday)  
as used by [time.localtime](http://docs.micropython.org/en/latest/library/time.html#time.localtime).

## 1.1 The DS3231 class

#### Constructor:  
This takes one mandatory argument, an initialised I2C bus.

#### Public methods:
 1. `get_time(set_rtc=False)`. If `set_rtc` is `True` it sets the platform's
 RTC from the DS3231. Returns the DS3231 time as a datetime tuple with
 `yearday=0`.
 On ports/platforms which don't support an RTC, if `set_rtc` is  `True`, the
 system time will be set from the DS3231. If setting the RTC, for accuracy the
 method will pause until a seconds transition occurs on the DS3231.
 2. `set_time(tt=None)`. Sets the DS3231 time. By default it uses the
 platform's syatem time, otherwise the passed `datetime` tuple. If passing a
 tuple, see the note below.
 3. `__str__()` Returns a dump of the device's registers for debug in a "pretty
 print" format.
 4. `temperature()` A float, temperature in °C. Datasheet specifies +-3°C
 accuracy. It really is that bad.

#### Public bound variables:

 1. `alarm1` `Alarm` instances (see below). Can be set to 1s precision.
 2. `alarm2` Can be set to 1min precision.

#### Alarm Public methods

 1. `set(when, day=0, hr=0, min=0, sec=0)` Arg `when` is one of the module
 constants listed below. Alarm operation is started.
 2. `clear()` Clears the alarm status and releases the alarm pin. The alarm
 will occur again the next time the parameters match.
 3. `__call__()` No args. Return `True` if alarm has occurred.
 4. `enable(run)` If `run` is `False` the alarm is cleared and will enter a
 stopped state; in that state the alarm will not occur again. If `True` a
 stopped alarm is restarted and will occur on the next match.

#### Alarm bound variables

 1. `alno` Alarm no. (1 or 2).

#### Module constants

These are the allowable options for the alarm's `when` arg, along with the
relevant `Alarm.set()` args:
`EVERY_SECOND` Only supported by alarm1.  
`EVERY_MINUTE` `sec`  
`EVERY_HOUR` `min`, `sec`  
`EVERY_DAY` `hr`, `min`, `sec`  
`EVERY_WEEK` `day` (weekday 0..6), `hr`, `min`, `sec`  
`EVERY_MONTH` `day` (month day 1..month end), `hr`, `min`, `sec`  

In all cases `sec` values are ignored by alarm2: alarms occur on minute
boundaries. This is a hardware restriction.

#### Setting DS3231 time

Where this is to be set using a datetime tuple rather than from system time, it
is necessary to pass the correct value of weekday. This can be acquired with
this function. It can be passed a tuple with `dt[6] == 0` and will return a
corrected tuple:
```python
import time
def dt_tuple(dt):
    return time.localtime(time.mktime(dt))  # Populate weekday field
```

#### Alarms

Comments assume that a backup battery is in use.

The battery ensures that alarm settings are stored through a power outage. If
an alarm occurs during an outage the pin will be driven low and will stay low
until power is restored and `clear` or `disable` are issued.

If an alarm is set and a power outage occurs, when power is restored the alarm
will continue to operate at the specified frequency. Setting an alarm:
```python
from machine import SoftI2C, Pin
from ds3231_gen import *
i2c = SoftI2C(scl=Pin(16, Pin.OPEN_DRAIN, value=1), sda=Pin(17, Pin.OPEN_DRAIN, value=1))
d = DS3231(i2c)
dt.alarm1.set(EVERY_MINUTE, sec=30)
```
If a power outage occurs here the following code will ensure alarms continue to
occur at one minute intervals:
```python
from machine import SoftI2C, Pin
from ds3231_gen import *
i2c = SoftI2C(scl=Pin(16, Pin.OPEN_DRAIN, value=1), sda=Pin(17, Pin.OPEN_DRAIN, value=1))
d = DS3231(i2c)
while True:
    d.alarm1.clear()  # Clear pending alarm
    while not d.alarm1():  # Wait for alarm
        pass
    time.sleep(0.3)  # Pin stays low for 300ms
```
Note that the DS3231 alarm2 does not have a seconds register: `sec` values will
be ignored and `EVERY_SECOND` is unsupported.

Re the `INT\` (alarm) pin the datasheet (P9) states "The pullup voltage can be
up to 5.5V, regardless of the voltage on Vcc". Note that some breakout boards
have a pullup resistor between this pin and Vcc.

# 2. Portable driver ds3231_port

This can use soft I2C so any pins may be used.

It uses the `RTC.datetime()` method to set and to query the platform RTC. The
meaning of the subseconds field is hardware dependent so this is ignored. The
RTC is checked against the DS3231 by timing the transition of the seconds field
of each clock (using system time to measure the relative timing of the edges).

This example ran on a WeMos D1 Mini ESP8266 board, also a generic ESP32.
```python
from ds3231_port import DS3231
from machine import Pin, SoftI2C
# Pins with pullups on ESP8266: clk=WeMos D3(P0) data=WeMos D4(P2)
i2c = SoftI2C(Pin(0, Pin.OPEN_DRAIN), Pin(2, Pin.OPEN_DRAIN))
ds3231 = DS3231(i2c)
ds3231.get_time()
```
Testing the onboard RTC:
```
ds3231.rtc_test()  # Takes 10 minutes
```
In my testing the ESP8266 RTC was out by 5%. The ESP32 was out by 6.7ppm or
about 12 minutes/yr. A PiPico was out by 1.7ppm, 3.2mins/yr. Hardware samples
will vary.

## 2.1 The DS3231 class

Constructor:  
This takes one mandatory argument, an initialised I2C bus.

Public methods:
 1. `get_time(set_rtc=False)`. If `set_rtc` is `True` it sets the platform's
 RTC from the DS3231. It returns the DS3231 time as a tuple in the same format
 as `utime.localtime()` except that yday (day of year) is 0. So the format is
 (year, month, day, hour, minute, second, wday, 0).  
 Note that on ports/platforms which don't support an RTC, if `set_rtc` is
 `True`, the local time will be set from the DS3231.
 2. `save_time()` No args. Sets the DS3231 time from the platform's local time.
 3. `rtc_test(runtime=600, ppm=False, verbose=True)`. This tests the platform's
 RTC time against the DS3231 returning the error in parts per million (if `ppm`
 is `True`) or seconds per year. A positive value indicates that the  DS3231
 clock leads the platform RTC.  
 The `runtime` value in seconds defines the duration of the test. The default
 of 10 minutes provides high accuracy but shorter durations will suffice on
 devices with poor RTC's (e.g. ESP8266).  
 If `machine.RTC` is unsupported a `RuntimeError` will be thrown.

# 3. The Pyboard driver

The principal reason to use this driver is to calibrate the Pyboard's RTC. This
supports the Pyboard 1.x and Pyboard D. Note that the RTC on the Pyboard D is
much more accurate than that on the Pyboard 1.x but can still be in error by up
to 20ppm. It can benefit from calibration. For this to work reliably on the D a
firmware build later than V1.12 is required: use a daily build if a later
release is not yet available.

Note that, while the code will run on the Pyboard Lite, this device cannot be
calibrated. This is because its RTC uses an inaccurate RC oscillator whose
frequency is usually beyond the range of the chip's calibration capability.
Even if this is not the case, the lack of stability of RC oscillators makes
calibration a pointless exercise.

The sample below assumes that the DS3231 is connected to the hardware I2C port
via I2C(2) but any I2C may be used including soft I2C. Ensure that the Pyboard
RTC is set to the correct time and date.

Usage to calibrate the Pyboard's RTC. Takes 5 minutes.

```python
from ds3231_pb import DS3231
import machine
i2c = machine.I2C(2)  # Connected on 'Y' side Y9 clk Y10 data
ds3231 = DS3231(i2c)
ds3231.save_time()  # Set DS3231 to match Pyboard RTC
ds3231.calibrate()
```

Calibration data is stored in battery-backed memory. So if a backup cell is
used the RTC will run accurately in the event of a power outage.

## 3.1 The DS3231 class

Constructor:  
This takes one mandatory argument, an I2C bus instantiated using the `machine`
library.

Public methods:
 1. `get_time(set_rtc=False)`. If `set_rtc` is `True` it sets the Pyboard's RTC
 from the DS3231. It returns the DS3231 time as a tuple in the same format as
 `utime.localtime()` except that yday (day of year) is 0.  
 Namely (year, month, day, hour, minute, second, wday, 0).
 2. `save_time()` No args. Sets the DS3231 time from the Pyboard's RTC.
 3. `calibrate(minutes=5)`. The time to run. This calculates the calibration
 factor and applies it to the Pyboard. It returns the calibration factor which
 may be stored in a file if the calibration needs to survive an outage of all
 power sources.
 4. `getcal(minutes=5, cal=0, verbose=True)` Measures the performance of the
 Pyboard RTC against the DS3231. If `cal` is specified, the calibration factor
 is applied before the test is run. The default is to zero the calibration and
 return the required factor.
