# The DS3231 real time clock chip

This is a remarkably inexpensive and easily interfaced battery-backed RTC. It
is an ideal way rapidly to calibrate the Pyboard's RTC which can then achieve
similar levels of accuracy (+- ~2 mins/year). The chip can also provide
accurate time to platforms lacking a good RTC (notably the ESP8266).

Two drivers are provided:
 1. `ds3231_port.py` A multi-platform driver.
 2. `ds3231_pb.py` A Pyboard-specific driver with RTC calibration facility. For
 Pyboard 1.x and Pyboard D.

Breakout boards are widely available. The interface is I2C. Pullups to 3.3V
(typically 10KΩ) should be provided on the `SCL` and `SDA` lines if these are
not supplied on the breakout board.

Both divers use edge detection to achieve millisecond-level precision from the
DS3231. This enables relatively rapid accuracy testing of the platform's RTC,
and fast calibration of the Pyboard's RTC. To quantify this, a sufficiently
precise value of calibration may be acquired in 5-10 minutes.

###### [Main README](../README.md)

# 1. The multi-platform driver

This can use soft I2C so any pins may be used.

It uses the currently undocumented `RTC.datetime()` method to set and to query
the platform RTC. This appears to be the only cross-platform way to do this.
The meaning of the subseconds field is hardware dependent so this is ignored.
The RTC is checked against the DS3231 by timing the transition of the seconds
field of each clock (using system time to measure the relative timing of the
edges).

This example ran on a WeMos D1 Mini ESP8266 board, also a generic ESP32.
```python
from ds3231_port import DS3231
from machine import Pin, I2C
# Pins with pullups on ESP8266: clk=WeMos D3(P0) data=WeMos D4(P2)
i2c = I2C(-1, Pin(0, Pin.OPEN_DRAIN), Pin(2, Pin.OPEN_DRAIN))
ds3231 = DS3231(i2c)
ds3231.get_time()
```
Testing the onboard RTC:
```
ds3231.rtc_test()  # Takes 10 minutes
```
In my testing the ESP8266 RTC was out by 5%. The ESP32 was out by 6.7ppm or
about 12 minutes/yr. Hardware samples will vary.

## 1.1 The DS3231 class

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

# 2. The Pyboard driver

The principal reason to use this driver is to calibrate the Pyboard's RTC. This
supports the Pyboard 1.x and Pyboard D. Note that the RTC on the Pyboard D is
much more accurate than that on the Pyboard 1.x but can still be in error by up
to 20ppm. It can benefit from calibration. For this to work reliably on the D a
firmware build later than V1.12 is required: use a daily build if a later
release is not yet available.

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

## 2.1 The DS3231 class

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
