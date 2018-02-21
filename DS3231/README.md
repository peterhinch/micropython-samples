# The DS3231 real time clock chip

This is a remarkably inexpensive and easily interfaced battery-backed RTC. It
is an ideal way to rapidly calibrate the Pyboard's RTC which can then achieve
similar levels of accuracy (+- ~2 mins/year). The chip can also provide
accurate time to platforms lacking a good RTC (notably the ESP8266).

Two drivers are provided:
 1. `ds3231_port.py` A multi-platform driver.
 2. `ds3231_pb.py` A Pyboard-specific driver with RTC calibration facility.

Breakout boards are widely available. The interface is I2C. Pullups to 3.3V
(typically 10KΩ) should be provided on the `SCL` and `SDA` lines if these are
not supplied on the breakout board.

Both divers use edge detection to achieve millisecond-level precision from the
DS3231. This enables relatively rapid accuracy testing of the platform's RTC,
and fast calibration of the Pyboard's RTC.

###### [Main README](../README.md)

# 1. The multi-platform driver

This can use soft I2C so any pins may be used.

It is based on the assumption that, where a hardware RTC exists, MicroPython's
local time (`utime.localtime()`) is based on the RTC time. Changes to local
time don't propagate to the RTC which must explicitly be set. This holds for
the Pyboard, ESP8266 and ESP32.

The official ESP32 port currently lacks support for the RTC so the Loboris port
should be used for this purpose. The driver supports both but if the official
port is used only the local time can be updated from the DS3231.

## 1.1 The DS3231 class

Constructor:  
This takes one mandatory argument, an initialised I2C bus.

Public methods:
 1. `get_time` Optional boolean arg `set_rtc=False`. If `set_rtc` is `True` it
 sets the platform's RTC from the DS3231. It returns the DS3231 time as a tuple
 in the same format as `utime.localtime()` except that yday (day of year) is 0.
 So the format is (year, month, day, hour, minute, second, wday, 0).  
 Note that on ports/platforms which don't support an RTC, if `set_rtc` is
 `True`, the local time will be set from the DS3231.
 2. `save_time` No args. Sets the DS3231 time from the platform's local time.
 3. `rtc_test` Optional args: `runtime=600`, `ppm=False`. This tests the
 platform's local time against the DS3231 returning the error in parts per
 million (if `ppm` is `True`) or seconds per year. A positive value indicates
 that the  DS3231 clock leads the platform local time. 
 The `runtime` value in seconds defines the duration of the test. The default
 of 10 minutes provides high accuracy but shorter durations will suffice on
 devices with poor RTC's (e.g. ESP8266).  

# 2. The Pyboard driver

The principal reason to use this driver is to calibrate the Pyboard's RTC. 

This assumes that the DS3231 is connected to the hardware I2C port on the `X`
or `Y` side of the board, and that the Pyboard's RTC is set to the correct time
and date.

Usage to calibrate the Pyboard's RTC. Takes 5 minutes.

```python
from ds3231_pb import DS3231
ds3231 = DS3231('X')
ds3231.save_time()  # Set DS3231 to match Pyboard RTC
ds3231.calibrate()
```

Calibration data is stored in battery-backed memory. So if a backup cell is
used the RTC will run accurately in the event of a power outage.

## 2.1 The DS3231 class

Constructor:  
This takes one mandatory argument, a string identifying the Pyboard side in use
('X' or 'Y').

Public methods:
 1. `get_time` Optional boolean arg `set_rtc=False`. If `set_rtc` is True it
 sets the Pyboard's RTC from the DS3231. It returns the DS3231 time as a tuple
 in the same format as `utime.localtime()` except that yday (day of year) is 0.
 namely (year, month, day, hour, minute, second, wday, 0).
 2. `save_time` No args. Sets the DS3231 time from the Pyboard's RTC.
 3. `calibrate` Optional arg `minutes=5`. The time to run. This calculates the
 calibration factor and applies it to the Pyboard. It returns the calibration
 factor which may be stored in a file if the calibration needs to survive an
 outage of all power sources.
