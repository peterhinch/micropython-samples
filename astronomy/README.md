# Astronomical calculations in MicroPython

1. [Overview](./README.md#1-overview)  
 1.1 [Applications](./README.md#11-applications)  
 1.2 [Licensing and acknowledgements](./README.md#12-licensing-and-acknowledgements)  
 1.3 [Installation](./README.md#13-installation)  
 1.4 [Definitions](./README.md#14-definitions) Local and universal time.  
2. [The RiSet class](./README.md#2-the-riset-class)  
 2.1 [Constructor](./README.md#21-constructor)  
 2.2 [Methods](./README.md#22-methods)  
 2.3 [Effect of local time](./README.md#23-effect-of-local-time)  
 2.4 [Continuously running applications](./README.md#24-continuously-running-applications)  
3. [Utility functions](./README.md#3-utility-functions)  
4. [Demo script](./README.md#4-demo-script)  
5. [Scheduling events](./README.md#5-scheduling-events)  
6. [The moonphase module](./README.md#6-the-moonphase-module)  
 6.1 [Constructor](./README.md#61-constructor)  
 6.2 [Methods](./README.md#62-methods)  
 6.3 [Usage examples](./README.md#63-usage-examples)  
 6.4 [DST](./README.md#64-dst) Daylight savings time.  
7. [Performance and accuracy](./README.md#7-performance-and-accuracy)  
 7.1 [RiSet class](./README.md#71-riset-class)  
 7.2 [moonphase class](./README.md#72-moonphase-class)  

# 1. Overview

The `sun_moon` module enables sun and moon rise and set times to be determined
at any geographical location. Times are in seconds from midnight and refer to
any event in a 24 hour period starting at midnight. The midnight datum is
defined in local time. The start is a day specified as the current day plus an
offset in days. It can also compute Civil, Nautical or Astronomical twilight
times.

The `moonphase` module enables the moon phase to be determined for any date, and
the dates and times of lunar quarters to be calculated.

Caveat. I am not an astronomer. If there are errors in the fundamental
algorithms I am unlikely to be able to offer an opinion, still less a fix.

Moon phase options have been removed from `sun_moon` because accuracy was poor.

## 1.1 Applications

There are two application areas. Firstly timing of events relative to sun or
moon rise and set times, discussed later in this doc. Secondly constructing
lunar clocks such as this one - the "lunartick":
![Image](./lunartick.jpg)

## 1.2 Licensing and acknowledgements

#### sun_moon.py

Some code was ported from C/C++ as presented in "Astronomy on the Personal
Computer" by Montenbruck and Pfleger, with mathematical improvements contributed
by Marcus Mendenhall and Raul Kompaß. I (Peter Hinch) performed the port and
enabled support for timezones. Raul Kompaß substantially improved the accuracy
when run on hardware with 32-bit floating point.

The sourcecode exists in the book and also on an accompanying CD-R. The file
`CDR_license.txt` contains a copy of the license file on the disk, which
contains source, executable code, and databases. This module only references the
source. I have not spotted any restrictions on use in the book. I am not a
lawyer; I have no idea of the legal status of code based on sourcecode in a
published work.

#### moonphase.py

This was derived from unrestricted public sources and is released under the MIT
licence.

## 1.3 Installation

Installation copies files from the `astronomy` directory to a directory
`\lib\sched` on the target. This directory eases optional use with the
[schedule module](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/SCHEDULE.md).
Installation may be done with the official
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
Clone the repo and move to `micropython-samples` on the PC, run `rshell` and
issue:
```
> rsync astronomy /sd/sched
```
`mip` installs the following files in the `sched` directory.
* `sun_moon.py`
* `sun_moon_test.py` A test/demo script for the above.
* `moonphase.py` Determine lunar quarters and phase.
After installation the `RiSet` class may be accessed with
```python
from sched.sun_moon import RiSet
```
## 1.4 Definitions

Time is a slippery concept when applied to global locations. This document uses
the following conventions:
* `UTC` The international time standard based on the Greenwich meridian.
* `LT (Local time)` Time on a clock at the device's location. May include
daylight saving time (`DST`).
* `MT (Machine time)` Time defined by the platform's hardware clock.
* `LTO (Local time offset)` A `RiSet` instance contains a user supplied `LTO`
intended for timezone support. The class computes rise and set times in UTC,
using `LTO` to compute results using  `RESULT = UTC + LTO`. For output in `LT`
there are two options: periodically adjust `LTO` to handle DST or (better)
provide a `dst` function so that conversion is automatic.

# 2. The RiSet class

This holds the local geographic coordinates and the local time offset (`LTO`).
An instance is initialised to the current date (defined by `MT`) and can provide
the times of rise and set events occurring within a 24 hour window starting at
00:00:00 `LT`. A `RiSet` instance's date may be changed allowing rise and set
times to be retrieved for other 24 hour windows. Continuously running
applications should detect machine time (`MT`) date rollover and cause `RiSet`
instances to re-calculate rise and set times for the new day. This is done by
issuing `.set_day()`.

Rise and set times may be retrieved in various formats including seconds from
local midnight: this may be used to enable the timing of actions relative to a
rise or set event.

## 2.1 Constructor

Args (float):
* `lat=LAT` Latitude in degrees (-ve is South). Defaults are my location. :)
* `long=LONG` Longitude in degrees (-ve is West).
* `lto=0` Local time offset in hours to UTC (-ve is West); the value is checked
to ensure `-15 < lto < 15`. See [section 2.3](./README.md#23-effect-of-local-time).
The constructor sets the object's date to the system date as defined by machine
time (`MT`).
* `tl=None` If provided, set an offset in degrees for the definition of twilight
(6 is Civil, 12 is Nautical, 18 is Astronomical). By default twilight times are
not computed, saving some processor time. Offsets are positive numbers
representing degrees below the horizon where twilight is deemed to start and end.
* `dst=lambda x: x` This is an optional user defined function for Daylight
Saving Time (DST). The assumption is that machine time is not changed, typically
permanently in winter time. A `dst` function handles seasonal changes. The
default assumes no DST is applicable. For how to write a DST function for a
given country see [section 6.4](./README.md#64-dst).

By default when an application instantiates `RiSet` for the first time the
constructor prints the system date and time. This can be inhibited by setting
the class variable `verbose` to `False`. The purpose is to alert the user to a
common source of error where machine time is not set.

## 2.2 Methods

* `set_day(day: int = 0)` `day` is an offset in days from the current system
date. If the passed day differs from that stored in the instance, rise and set
times are updated - otherwise return is "immediate". Returns the `RiSet`
instance.
* `sunrise(variant: int = 0)` See below for details and the `variant` arg.
* `sunset(variant: int = 0)`
* `moonrise(variant: int = 0)`
* `moonset(variant: int = 0)`
* `tstart(variant: int = 0)` Twilight start, Sun about to rise.
* `tend(variant: int = 0)` Twilight end, (Sun has set).
* `is_up(sun: bool)-> bool` Returns `True` if the selected object is above the
horizon.
* `has_risen(sun: bool)->bool` Returns `True` if the selected object has risen.
* `has_set(sun: bool)->bool` Returns `True` if the selected object has set.
* `set_lto(t)` Set local time offset `LTO` in hours relative to UTC. Primarily
intended for timezone support, but this function can be used to support DST. The
value is checked to ensure `-15.0 < lto < 15.0`. See
[section 2.3](./README.md#23-effect-of-local-time).

The return value of the rise and set method is determined by the `variant` arg.
In all cases rise and set events are identified which occur in the current 24
hour period. Note that a given event may be absent in the period: this can occur
with the moon at most locations, and with the sun in polar regions.

Variants:
* 0 Return integer seconds since midnight `LT` (or `None` if no event).
* 1 Return integer seconds since since epoch of the MicroPython platform
 (or `None`). This allows comparisons with machine time (`MT`) as per
 `time.time()`.
* 2 Return text of form hh:mm:ss (or --:--:--) being local time (`LT`).

If bit 2 of `variant` is set and a `dst` constructor arg has been passed, the
`dst` function will be applied to the result. This caters for the case where the
machine clock runs winter time and a dst-adjusted result is required. It should
be noted that applying dst adjustment to a time close to midnight can result in
rollover, i.e. a time > 24:00. Handling this case is the responsibility of the
application.

Example constructor invocations:
```python
r = RiSet()  # UK near Manchester
r = RiSet(lat=47.609722, long=-122.3306, lto=-8)  # Seattle 47°36′35″N 122°19′59″W
r = RiSet(lat=-33.87667, long=151.21, lto=11)  # Sydney 33°52′04″S 151°12′36″E
```
## 2.3 Effect of local time

MicroPython has no concept of timezones. The hardware platform has a clock
which reports machine time (`MT`): this might be set to local winter time or
summer time.  The `RiSet` instances' `LTO` should be set to represent the
difference between `MT` and `UTC`. In continuously running applications it is
best to avoid changing the hardware clock (`MT`) for reasons discussed below.
Daylight savings time may be implemented in one of two ways:
* By changing the `RiSet` instances' `LTO` accordingly.
* Or by providing a `dst` function as discussed in
[section 6.4](./README.md#64-dst). This is the preferred solution as DST is then
handled automatically.

Rise and set times are computed relative to UTC and then adjusted using the
`RiSet` instance's `LTO` before being returned  (see `.adjust()`). This means
that the accuracy of the hardware clock is not critical: only the date portion
is used in determining rise and set times.

The `.has_risen()`, `.has_set()` and `.is_up()` methods do use machine time
(`MT`) and rely on `MT == UTC + LTO`: if `MT` has drifted, precision will be
lost at times close to rise and set events.

The constructor and the `set_day()` method set the instance's date relative to
`MT`. They use only the date component of `MT`, hence they may be run at any
time of day and are not reliant on `MT` accuracy.

## 2.4 Continuously running applications

Where an application runs continuously there is usually a need for `RiSet`
instances to track the current date. One approach is this:
```python
async def tomorrow(offs):
    now = round(time.time())
    tw = 86400 + 60 - (now % 86400)  # Time from now to one minute past next midnight
    await asyncio.sleep(tw)

rs = RiSet()  # May need args

async def keep_updated(rs):  # Keep a RiSet instance updated
    while True:
        await tomorrow()  # Wait until 1 minute past midnight
        rs.set_day()  # Update to new day
```
It is important that, at the time when `.set_day()` is called, the system time
has a date which is correct. Most hardware uses crystal controlled clocks so
drift is minimal. However with long run times it will accumulate. Care must be
taken if periodically synchronising system time to a time source: the resultant
sudden jumps in system time can cause havoc with `uasyncio` timing. If
synchronisation is required it is best done frequently to minimise the size of
jumps.

For this reason changing system time to accommodate daylight saving time is a
bad idea. It is usually best to run winter time all year round and to use the
`dst` constructor arg to handle time changes.

# 3. Utility functions

`now_days() -> int` Returns the current time as days since the platform epoch.

# 4. Demo script

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

The script includes some commented out code at the end. This tests `is_up`,
`has_risen` and `has_set` over 365 days. It is commented out to reduce printed
output.

# 5. Scheduling events

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
# 6. The moonphase module

This contains a single class `MoonPhase`. The term "machine time" below refers
to the time reported by the MicroPython `time` module. The "local time offset"
(LTO) passed to the constructor specifies the difference between machine time
and UTC based on system longitude. "Daylight saving time" (DST) allows reported
times to be offset to compensate for DST. Internally phases are calculated in
UTC, but where times are output they are adjusted for LTO and DST.

It is recommended that the machine clock is not adjusted for DST because large
changes can play havoc with program timing as described above. To accommodate
DST, a `dst` function can be provided to the constructor. The module uses this
to adjust reported times.

A `MoonPhase` instance has a time `datum`, which defaults to the instantiation
time. Phases are calculated with respect to this datum. It may be changed using
`.set_day` to enable future and past phases to be determined or to enable long
running applications to track time.

The module is imported as follows:
```python
from sched.moonphase import MoonPhase
```

## 6.1 Constructor

* `lto:float=0, dst = lambda x: x` Local time offset in hours to UTC (-ve is
West); the value is checked to ensure `-15 < lto < 15`. `dst` is an optional
user defined function for Daylight Saving Time (DST). See
[section 6.4](./README.md#64-dst)

## 6.2 Methods

* `quarter(q: int, text: bool = True)` Return the time of a given quarter. Five
quarters are calculated around the instance datum. By default the time
is last midnight machine time with an optional offset in days `doff` added. The
`quarter` arg specifies the quarter with 0 and 4 being new moons and quarter 2
being full. The `text` arg determines how the value is returned: as text or as
`int` is secs from the machine epoch. Results are adjusted for DST if a `dst`
function is provided to the constructor.
* `phase() -> float)` Returns moon phase where 0.0 <= phase < 1.0 with 0.5 being
full moon. The phase is that pertaining to the datum.
* `nextphase(text: bool = True)` This is a generator function. Each iteration
of the generator returns three values: the phase number, the lunation number and
the datetime of the phase. The `text` arg is as per `.quarter()`, defining the
format of the datetime.
* `set_day(doff: float = 0)` Set the `MoonPhase` datum time to machine time plus
an offset in days: this may include a fractional part if `.phase()` is required
to produce a time-precise value. The five quarters are calculated for the
lunation including the midnight at the start of the specified day.
* `set_lto(t:float)` Redefine the local time offset, `t` being in hours as
per the constructor arg.
* `datum(text: bool = True)` Returns the current datum in secs since local epoch
or in human-readable text form.

## 6.3 Usage examples

```python
from sched.moonphase import MoonPhase
mp = MoonPhase()  # datum is midnight last night
print(f"Full moon, current lunation {mp.quarter(2)}")
mp.set_day(0.5)  # Adjust datum to noon today machine time
print(f"Phase at Noon {mp.phase()}")
mp.set_day(182)  # Set datum ahead 6 months
print(f"Lunation 1st new moon: {mp.quarter(0)}, 2nd new moon: {mp.quarter(4)}")
mp.set_day(0)  # Reset datum to today
n = mp.nextphase()  # Instantiate generator
for _ in range(8):
    print(next(n))
```

## 6.4 DST

Daylight saving time depends on country and geographic location, and there is no
built-in MicroPython support. The moonphase module supports DST via an optional
user supplied function. DST does not affect the calculation of quarters or phase
which is based on the machine clock. If the machine clock runs at a fixed offset
to UTC (which is recommended), a DST function can be used to enable reported
results to reflect local time.

A DST function takes as input a datetime measured in seconds since the machine
epoch (as returned by `time.time()`) and returns that number adjusted for local
time. The following example is for UK time, which adds one hour at 2:00 on the
last Sunday in March, reverting to winter time at 2:00 on the last Sunday in
October.

```python
def uk_dst(secs_epoch: int):  # Change in March (3) and Oct (10)
    t = time.gmtime(secs_epoch)
    month = t[1]
    mday = t[2]
    wday = t[6]
    winter = secs_epoch
    summer = secs_epoch + 3600  # +1hr
    if month in (1, 2, 11, 12):  # Simple cases: depend only on month
        return winter
    if not month in (3, 10):
        return summer  # +1 hr
    # We are in March or October. Find the day in month of last Sunday.
    ld = (wday + 31 - mday) % 7  # weekday of 31st.
    lsun = 31 - (1 + ld) % 7  # Monthday of last Sunday
    thresh = time.mktime((t[0], month, lsun, 2, 0, 0, 6, 0))  # 2am last Sunday in month
    return summer if ((secs_epoch >= thresh) ^ (month == 10)) else winter
```

# 7. Performance and accuracy

## 7.1 RiSet class

A recalculation is triggered whenever the 24 hour local time window is changed,
such as calling `.set_day()` where the stored date changes. Normally two days of
data are calculated, except where the local time is UTC where only one day is
required. The time to derive one day's data on RP2040 was 707μs (no twilight
calculation, standard clock).

The accuracy of rise and set times was checked against online sources for
several geographic locations. The online data had 1 minute resolution and the
checked values corresponded with data computed on a platform with 64 bit
floating point unit. The loss of precision from using a 32 bit FPU was no more
than 3s.

## 7.2 MoonPhase class

This uses Python's arbitrary precision integers to overcome the limitations of
32-bit floating point units. Results on 32 bit platforms match those on 64-bits
to within ~1 minute. Results match those on `timeanddate.com` within ~3 minutes.
