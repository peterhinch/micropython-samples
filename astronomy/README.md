# Astronomical calculations in MicroPython

This module enables sun and moon rise and set times to be determined at any
geographical location. Times are in seconds from midnight and refer to any
event in a 24 hour period starting at midnight. The midnight datum is defined in
local time. The start is a day being the current day plus an offset in days.

A `moonphase` function is also provided enabling the moon phase to be determined
for any date.


Caveat. I am not an astronomer. If there are errors in the fundamental
algorithms I am unlikely to be able to offer an opinion, still less a fix.

The code is currently under development: the API may change.

## Licensing and acknowledgements

The code was ported from C/C++ as presented in "Astronomy on the Personal
Computer" by Montenbruck and Pfleger, with mathematical improvements contributed
by Raul Kompaß and Marcus Mendenhall. The sourcecode exists in the book and also
on an accompanying CD-R. The file `CDR_license.txt` contains a copy of the
license file on the CD-R. I am not a lawyer; I have no idea of the legal status
of code translated from that in a published work.

# The RiSet class

## Constructor

Args (float):
* `lat=LAT` Latitude in degrees (-ve is South). Defaults are my location. :)
* `long=LONG` Longitude in degrees (-ve is West).
* `lto=0` Local time offset in hours to UTC (-ve is West).

Methods:
* `set_day(day: int = 0, relative=True)` `day` is the offset from the current
system date if `relative` is `True` otherwise it is the offset from the platform
epoch. If `day` is changed the rise and set times are updated.
* `sunrise(variant: int = 0)` See below for details and the `variant` arg.
* `sunset(variant: int = 0)`
* `moonrise(variant: int = 0)`
* `moonset(variant: int = 0)`
* `moonphase()` Return current phase as a float: 0.0 <= result < 1.0. 0.0 is new
moon, 0.5 is full.
* `set_lto(t)` Update localtime offset to UTC (for daylight saving time). Rise
and set times are updated if the lto is changed.

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

# The moonphase function

This is a simple function whose provenance is uncertain. I have a lunar clock
which uses a C version of this which has run for 14 years without issue, but I
can't vouch for its absolute accuracy over long time intervals. The Montenbruck
and Pfleger version is very much more involved but they claim accuracy over
centuries.

Args:
* `year: int` 4-digit year
* `month: int` 1..12
* `day: int` Day of month 1..31
* `hour: int` 0..23

Return value:  
A float in range 0.0 <= result < 1.0, 0 being new moon, 0.5 being full moon.
