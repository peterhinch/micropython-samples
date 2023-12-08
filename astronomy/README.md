# Astronomical calculations in MicroPython

1. [Overview](./README.md#1-overview)  
 1.1 [Applications](./README.md#11-applications)  
 1.2 [Licensing and acknowledgements](./README.md#12-licensing-and-acknowledgements)  
 1.3 [Installation](./README.md#13-installation)  
2. [The RiSet class](./README.md#2-the-riset-class)  
 2.1 [Constructor](./README.md#21-constructor)  
 2.2 [Methods](./README.md#22-methods)  
 2.3 [Effect of local time](./README.md#23-effect-of-local-time)  
 2.4 [Continuously running applications](./README.md#24-continuously-running-applications)  
3. [The moonphase function](./README.md#3-the-moonphase-function)  
4. [Utility functions](./README.md#4-utility-functions)  
5. [Demo script](./README.md#5-demo-script)  
6. [Scheduling events](./README.md#6-scheduling-events)  
7. [Performance and accuracy](./README.md#7-performance-and-accuracy)  

# 1. Overview

This module enables sun and moon rise and set times to be determined at any
geographical location. Times are in seconds from midnight and refer to any
event in a 24 hour period starting at midnight. The midnight datum is defined in
local time. The start is a day being the current day plus an offset in days.

A `moonphase` function is also provided enabling the moon phase to be determined
for any date.

Caveat. I am not an astronomer. If there are errors in the fundamental
algorithms I am unlikely to be able to offer an opinion, still less a fix.

The code is currently under development: the API may change.

## 1.1 Applications

There are two application areas. Firstly timing of events relative to sun or
moon rise and set times, discussed later in this doc. Secondly constructing
lunar clocks such as this one - the "lunartick":
![Image](./lunartick.jpg)

## 1.2 Licensing and acknowledgements

The code was ported from C/C++ as presented in "Astronomy on the Personal
Computer" by Montenbruck and Pfleger, with mathematical improvements contributed
by Raul Kompaß and Marcus Mendenhall. The sourcecode exists in the book and also
on an accompanying CD-R. The file `CDR_license.txt` contains a copy of the
license file on the disk, which contains source, executable code, and databases.
This module (obviously) only references the source. I am not a lawyer; I have no
idea of the legal status of code translated from sourcecode in a published work.

## 1.3 Installation

Installation copies files from the `astronomy` directory to a directory
`\lib\sched` on the target. This is for optional use with the
[schedule module](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/SCHEDULE.md).
This may be done with the official
[mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html):
```bash
$ mpremote mip install "github:peterhinch/micropython-samples/astronomy"
```
On networked platforms it may alternatively be installed with
[mip](https://docs.micropython.org/en/latest/reference/packages.html).
```py
>>> mip.install("github:peterhinch/micropython-samples/astronomy")
```
Currently these tools install to `/lib` on the built-in Flash memory. To install
to a Pyboard's SD card [rshell](https://github.com/dhylands/rshell) may be used.
Move to `micropython-samples` on the PC, run `rshell` and issue:
```
> rsync astronomy /sd/sched
```
`mip` installs the following files in the `sched` directory.
* `sun_moon.py`
* `sun_moon_test.py` A test/demo script.
After installation the `RiSet` class may be accessed with
```python
from sched.sun_moon import RiSet
```

# 2. The RiSet class

This holds the local geographic coordinates and the localtime offset relative to
UTC. It is initialised to the current date and can provide the times of rise and
set events occurring within a 24 hour window starting at 00:00:00 local time.
The `RiSet` instance's date may be changed allowing rise and set times to be
retrieved for other 24 hour windows. In continuously running applications which
must access current rise and set times the application should re-calculate (by
issuing `.set_day()`) prior to retrieving that day's data.

Rise and set times may be retrieved in various formats including seconds from
local midnight: this may be used to enable the timing of actions relative to a
rise or set event.

## 2.1 Constructor

Args (float):
* `lat=LAT` Latitude in degrees (-ve is South). Defaults are my location. :)
* `long=LONG` Longitude in degrees (-ve is West).
* `lto=0` Local time offset in hours to UTC (-ve is West); the value is checked
to ensure `-12 < lto < 12`. See [section 2.3](./README.md#23-effect-of-local-time).
The constructor sets the object's date to the system date: this does require
that the system clock is set to local time. Precision is not required so long as
the date component is correct.

## 2.2 Methods

* `set_day(day: int = 0)` `day` is an offset in days from the current system
date. The number of days from the specified day to a fixed epoch is calculated
and compared to that stored in the instance. If there is a change the new value
is stored and the rise and set times are updated - otherwise return is
"immediate". Returns the `RiSet` instance. See the note above re system clock.
* `sunrise(variant: int = 0)` See below for details and the `variant` arg.
* `sunset(variant: int = 0)`
* `moonrise(variant: int = 0)`
* `moonset(variant: int = 0)`
* `is_up(sun: bool)` Returns `True` if the selected object is above the horizon.
The caller should ensure that the `RiSet` instance is set to the current day.
* `moonphase()` Return current phase as a float: 0.0 <= result < 1.0. 0.0 is new
moon, 0.5 is full. See [section 3](./README.md#3-the-moonphase-function) for
observations about this.
* `set_lto(t)` Set localtime offset in hours relative to UTC. Primarily intended
for daylight saving time. The value is checked to ensure `-12.0 < lto < 12.0`.
See [section 2.3](./README.md#23-effect-of-local-time).

The return value of the rise and set method is determined by the `variant` arg.
In all cases rise and set events are identified which occur in the current 24
hour period. Note that a given event may be absent in the period: this can occur
with the moon at most locations, and with the sun in polar regions.

Variants:
* 0 Return integer seconds since midnight local time (or `None` if no event).
* 1 Return integer seconds since since epoch of the MicroPython platform
 (or `None`).
* 2 Return text of form hh:mm:ss (or --:--:--) being local time.

Example constructor invocations:
```python
r = RiSet()  # UK near Manchester
r = RiSet(lat=47.609722, long=-122.3306, lto=-8)  # Seattle 47°36′35″N 122°19′59″W
r = RiSet(lat=-33.87667, long=151.21, lto=11)  # Sydney 33°52′04″S 151°12′36″E
```
## 2.3 Effect of local time

MicroPython has no concept of local time. A hardware platform has a clock;
depending on application this might be permanently set to local winter time, or
it might be adjusted twice per year for local daylight saving time. It is the
responsibility of the application to do this if it is considered necessary.

Rise and set times are computed relative to UTC and then adjusted using the
`RiSet` instance's local time offset before being returned  (see `.adjust()`).
This applies to all variants - note that the local platform epoch is on a fixed
date at 00:00:00 local time.

If the machine clock has a fixed relationship to UTC, `RiSet` instances should
have a corresponding fixed local time offset: rise and set times will be
relative to that time. If the application implements daylight saving time, the
local time offsets should be adjusted accordingly (remembering that offsets are
relative to UTC).

The constructor and the `set_day()` method set the instance's date relative to
the machine clock. They use only the date component of system time, hence they
may be run at any time of day. In continuously-running applications, `set_day()`
may be run each day just after midnight to keep a `RiSet` instance up to date.

## 2.4 Continuously running applications

Where an application runs continuously there is usually a need for `RiSet`
instances to track the current date. One approach is this:
```python
async def tomorrow(offs):  # Offset compensates for possible clock drift
    now = round(time.time())
    tw = 86400 + 60 * offs - (now % 86400)  # Time from now to one minute past next midnight
    await asyncio.sleep(tw)

async def keep_updated():
    rs = RiSet()  # May need args
    while True:
        await tomorrow(1)  # Wait until 1 minute past midnight
        rs.set_day()  # Update to new day
```
It is important that, at the time when `.set_day()` is called, the system time
has a date which is correct. Most hardware uses crystal controlled clocks so
drift is minimal. However with long run times it will accumulate. The
`tomorrow()` coroutine has an offset value in minutes: this should be chosen
such that the date value will remain correct.

# 3. The moonphase function

This is a simple function whose provenance is uncertain. It appears to produce
valid results but I plan to implement a better solution.

Args:
* `year: int` 4-digit year
* `month: int` 1..12
* `day: int` Day of month 1..31
* `hour: int` 0..23

Return value:  
A float in range 0.0 <= result < 1.0, 0 being new moon, 0.5 being full moon.

# 4. Utility functions

`now_days() -> int` Returns the current time as days since the platform epoch.
`abs_to_rel_days(days: int) -> int` Takes a number of days since the Unix epoch
(1970,1,1) and returns a number of days relative to the current date. Platform
independent. This facilitates testing with pre-determined target dates.

# 5. Demo script

This produces output for the fixed date 4th Dec 2023 at three geographical
locations. It can therefore be run on platforms where the system time is wrong.
To run issue:
```python
import sched.sun_moon_test
```
Expected output:
```python
>>> import sched.sun_moon_test
4th Dec 2023: Seattle UTC-8
Sun rise 07:40:09 set 16:18:15
Moon rise 23:38:11 set 12:53:40

4th Dec 2023: Sydney UTC+11
Sun rise 05:36:24 set 19:53:21
Moon rise 00:45:55 set 11:27:14

From 4th Dec 2023: UK, UTC
Day: 0
Sun rise 08:04:34 set 15:52:13
Moon rise 23:03:15 set 13:01:04
Day: 1
Sun rise 08:05:54 set 15:51:42
Moon rise --:--:-- set 13:10:35
Day: 2
Sun rise 08:07:13 set 15:51:13
Moon rise 00:14:40 set 13:18:59
Day: 3
Sun rise 08:08:28 set 15:50:49
Moon rise 01:27:12 set 13:27:08
Day: 4
Sun rise 08:09:42 set 15:50:28
Moon rise 02:40:34 set 13:35:56
Day: 5
Sun rise 08:10:53 set 15:50:10
Moon rise 03:56:44 set 13:46:27
Day: 6
Sun rise 08:12:01 set 15:49:56
Moon rise 05:18:32 set 14:00:11
Maximum error 0. Expect 0 on 64-bit platform, 30s on 32-bit
>>>
```
Code comments show times retrieved from `timeanddate.com`.

# 6. Scheduling events

A likely use case is to enable events to be timed relative to sunrise and set.
In simple cases this can be done with `asyncio`. This will execute a payload at
sunrise, and another at sunset, every day.
```python
import uasyncio as asyncio
import time
from sched.sun_moon import RiSet

async def tomorrow(offs):  # Offset compensates for possible clock drift
    now = round(time.time())
    tw = 86400 + 60 * offs - (now % 86400)  # Time from now to one minute past next midnight
    await asyncio.sleep(tw)

async def do_sunrise():
    rs = RiSet()  # May need args
    while True:
        if (delay := rs.sunrise(1) - round(time.time())) > 0:  # Sun has not yet risen
            await asyncio.sleep(delay)  # Wait for it to rise
            # Sun has risen, execute payload e.g. turn off light
        await tomorrow(1)  # Wait until 1 minute past midnight
        rs.set_day()  # Update to new day

async def do_sunset():
    rs = RiSet()  # May need args
    while True:
        if (delay := rs.sunset(1) - round(time.time())) > 0:  # Sun has not yet set
            await asyncio.sleep(delay)  # Wait for it to set
            # Sun has risen, execute payload e.g. turn on light
        await tomorrow(1)  # Wait until 1 minute past midnight
        rs.set_day()  # Update to new day

async def main():
    sr = asyncio.create_task(do_sunrise())
    ss = asyncio.create_task(do_sunset())
    ayncio.gather(sr, ss)
try:
    asyncio.run(main())
finally:
    _ = asyncio.new_event_loop()
```
This code assumes that `.sunrise()` will never return `None`. At polar latitudes
waiting for sunrise in winter would require changes - and patience.

Code may be simplified by using the
[schedule module](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/SCHEDULE.md).
This may be installed with
```bash
$ mpremote mip install "github:peterhinch/micropython-async/v3/as_drivers/sched"
```
The following is a minimal example:
```python
import uasyncio as asyncio
from sched.sched import schedule
from sched.sun_moon import RiSet

async def turn_off_lights(rs):  # Runs every day at 00:01:00
    rs.set_day()  # Re-calculate for new daylight
    await asyncio.sleep(rs.sunrise() - 60)
    # Actually turn them off

async def main():
    rs = RiSet()  # May need args for your location
    await schedule(turn_off_lights, rs, hrs=0, mins=1)  # Never terminates

try:
    asyncio.run(main())
finally:
    _ = asyncio.new_event_loop()
```
This approach lends itself to additional triggers and events:
```python
import uasyncio as asyncio
from sched.sched import schedule, Sequence
from sched.sun_moon import RiSet

async def turn_off_lights(t):
    await asyncio.sleep(t)
    # Actually turn them off

async def main():
    rs = RiSet()  # May need args for your location
    seq = Sequence()  # A Sequence comprises one or more schedule instances
    asyncio.create_task(schedule(seq, "off", hrs=0, mins=1))
    # Can schedule other events here
    async for args in seq:
        if args[0] == "off":  # Triggered at 00:01 hrs (there might be other triggers)
            rs.set_day()  # Re-calculate for new day
            asyncio.create_task(turn_off_lights(rs.sunrise() - 60))

try:
    asyncio.run(main())
finally:
    _ = asyncio.new_event_loop()
```

# 7. Performance and accuracy

A recalculation is triggered whenever the 24 hour local time window is changed,
such as calling `.set_day()` where the stored date changes. Normally two days of
data are calculated, except where the local time is UTC where only one day is
required. The time to derive one day's data on RP2040 was 707μs.

The accuracy of rise and set times was checked against online sources for
several geographic locations. The online data had 1 minute resolution and the
checked values corresponded with data computed on a platform with 64 bit
floating point unit. The loss of precision from using a 32 bit FPU was no more
than 30s.

For reasons which are unclear, the `is_up()` method is less precise, showing
incorrect results when within a few minutes of the rise or set time.
