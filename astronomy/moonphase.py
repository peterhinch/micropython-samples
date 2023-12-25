# moonphase.py Calculate lunar phases

# Source Tech\ Notes/Astronomy/astro_references/moontool.c
# The information for this was drawn from public domain sources including C code
# written by John Walker and Ron Hitchens in 1987-88 and released with the "licence"
# Do what thou wilt shall be the whole of the law".

# Uses Python arbitrary length integers to maintain accuracy on platforms with
# 32-bit floating point.
# Copyright (c) Peter Hinch 2023  Released under the MIT license.


# Exports calc_phases()

from math import radians, sin, cos, floor
import time
import array

SYNMONTH = 29.53058868  # Synodic month (new Moon to new Moon)


# MEANPHASE  --  Calculates time of the mean new Moon for a given base date.
# This argument K to this function is the precomputed synodic month index, given by:
# K = (year - 1900) * 12.3685
# where year is expressed as a year and fractional year.
# sdate is days from 1900 January 0.5. Returns days from 1900 January 0.5


def meanphase(sdate: float, k: int) -> float:
    # Time in Julian centuries from 1900 January 0.5
    t = sdate / 36525
    t2 = t * t  # Square for frequent use
    t3 = t2 * t  # Cube for frequent use
    nt1 = 0.75933 + SYNMONTH * k + 0.0001178 * t2 - 0.000000155 * t3
    return nt1 + 0.00033 * sin(radians(166.56 + 132.87 * t - 0.009173 * t2))


# TRUEPHASE  --  Given a K value used to determine the mean phase of the new moon,
# and a phase no.  (0..3), return the true, corrected phase time
# as integer Julian seconds.


def truephase(k: int, phi: int) -> int:
    k += (0, 0.25, 0.5, 0.75)[phi]  # Add phase to new moon time
    t = k / 1236.85  # Time in Julian centuries from 1900 January 0.5
    t2 = t * t  # Square for frequent use
    t3 = t2 * t  # Cube for frequent use
    # Sun's mean anomaly
    m = 359.2242 + 29.10535608 * k - 0.0000333 * t2 - 0.00000347 * t3
    # Moon's mean anomaly
    mprime = 306.0253 + 385.81691806 * k + 0.0107306 * t2 + 0.00001236 * t3
    # Moon's argument of latitude
    f = 21.2964 + 390.67050646 * k - 0.0016528 * t2 - 0.00000239 * t3
    if phi in (0, 2):  # Corrections for New and Full Moon
        pt = (0.1734 - 0.000393 * t) * sin(radians(m))
        pt += 0.0021 * sin(radians(2 * m))
        pt -= 0.4068 * sin(radians(mprime))
        pt += 0.0161 * sin(radians(2 * mprime))
        pt -= 0.0004 * sin(radians(3 * mprime))
        pt += 0.0104 * sin(radians(2 * f))
        pt -= 0.0051 * sin(radians(m + mprime))
        pt -= 0.0074 * sin(radians(m - mprime))
        pt += 0.0004 * sin(radians(2 * f + m))
        pt -= 0.0004 * sin(radians(2 * f - m))
        pt -= 0.0006 * sin(radians(2 * f + mprime))
        pt += 0.0010 * sin(radians(2 * f - mprime))
        pt += 0.0005 * sin(radians(m + 2 * mprime))
    else:  # First or last quarter
        pt = (0.1721 - 0.0004 * t) * sin(radians(m))
        pt += 0.0021 * sin(radians(2 * m))
        pt -= 0.6280 * sin(radians(mprime))
        pt += 0.0089 * sin(radians(2 * mprime))
        pt -= 0.0004 * sin(radians(3 * mprime))
        pt += 0.0079 * sin(radians(2 * f))
        pt -= 0.0119 * sin(radians(m + mprime))
        pt -= 0.0047 * sin(radians(m - mprime))
        pt += 0.0003 * sin(radians(2 * f + m))
        pt -= 0.0004 * sin(radians(2 * f - m))
        pt -= 0.0006 * sin(radians(2 * f + mprime))
        pt += 0.0021 * sin(radians(2 * f - mprime))
        pt += 0.0003 * sin(radians(m + 2 * mprime))
        pt += 0.0004 * sin(radians(m - 2 * mprime))
        pt -= 0.0003 * sin(radians(2 * m + mprime))
        if phi < 2:  # First quarter correction
            pt += 0.0028 - 0.0004 * cos(radians(m)) + 0.0003 * cos(radians(mprime))
        else:  # Last quarter correction
            pt += -0.0028 + 0.0004 * cos(radians(m)) - 0.0003 * cos(radians(mprime))
    pt = round(pt * 86400)  # Integer seconds from here
    pt += round(2_953_058_868 * 864 * k) // 1000_000  # round(SYNMONTH * k * 86400)
    qq = 0.0001178 * t2 - 0.000000155 * t3
    qq += 0.00033 * sin(radians(166.56 + 132.87 * t - 0.009173 * t2))
    pt += round(qq * 86400)  # qq amounts to 2s
    return pt + 208_657_793_606


def dt_to_text(tim):  # Convert a time to text
    t = time.localtime(tim)
    return f"{t[2]:02}/{t[1]:02}/{t[0]:4} {t[3]:02}:{t[4]:02}:{t[5]:02}"


class MoonPhase:
    verbose = True

    def __init__(self, lto: float = 0, dst=lambda x: x):
        self.lto_s = self._check_lto(lto)  # -15 < lto < 15
        # local time = UTC + lto .lto_s = offset in secs
        self.dst = dst
        # Datetimes in secs since hardware epoch based on UTC
        # With epoch 1970 this could need long ints.
        self.phases = array.array("q", (0,) * 5)
        # Calculate Julian date of machine epoch
        # Multiply by 100 to avoid fraction
        jepoch = 244058750  # Julian date of Unix epoch (1st Jan 1970) * 100
        if time.gmtime(0)[0] == 2000:  # Machine epoch
            jepoch += 1095700
        jepoch *= 864  # Seconds from epoch
        self.jepoch = jepoch
        self.secs = 0  # Time of calling .set_day in secs UTC
        self.set_day()  # Populate array and .secs
        if MoonPhase.verbose:
            print(f"Machine time: {dt_to_text(time.time())}")
            MoonPhase.verbose = False

    # Take offset in days from today, return time of last midnight in secs from machine epoch
    # Take time of last midnight machine time in secs since machine epoch. Add a
    # passed offset in days. Convert to UTC using LTO. The returned value is as
    # if the hardware clock were running UTC.
    def _midnight(self, doff: float = 0):  # Midnight last night + days offset (UTC)
        tl = round((time.time() // 86400 + doff) * 86400)  # Target in local time
        return tl - self.lto_s

    def set_lto(self, t: float):  # Update the offset from UTC
        self.lto_s = self._check_lto(t)  # Localtime offset in secs

    def set_day(self, doff: float = 0):
        self.secs = round(time.time() + doff * 86400 - self.lto_s)
        start = self._midnight(doff)  # Phases are calculated around this time (UTC)
        self._populate(start)  # Immediate return if .phases already OK

    def datum(self, text: bool = True):
        t = self.secs + self.lto_s
        return dt_to_text(t) if text else t

    def quarter(self, q: int, text: bool = True):
        if not 0 <= q <= 4:
            raise ValueError("Quarter nos must be from 0 to 4.")
        tutc = self.phases[q]  # Time of phase in secs UTC
        # Adjust time: t is machine time in secs since machine epoch
        t = self.dst(tutc + self.lto_s)  # UTC secs from hardware epoch -> local time
        return dt_to_text(t) if text else t  # Secs since machine epoch

    # Return moon  phase as 0.0 <= n < 1.0 by defaut for current datetime.
    def phase(self) -> float:  # doff: days offset with optional fraction
        t = self.secs  # As set by .set_day()
        if not (self.phases[0] <= t <= self.phases[4]):  # set_day was not called
            self.set_day()  # Assume today
        prev = self.phases[0]
        for n, phi in enumerate(self.phases):
            if phi > t:
                break  # phi is upcoming phase time
            prev = phi  # Last phase before now
        if prev == phi:  # Day is day of new moon: use synodic month/4
            r = (t - prev) * 0.25 / 637860.715488
            if r < 0:
                r = 1 - r
        else:
            r = (n - 1) * 0.25 + (t - prev) * 0.25 / (phi - prev)
        return min(r, 0.999999)  # Rare pathological results where r slightly > 1.0

    def _next_lunation(self):  # Use approx time of next full moon to advance
        self._populate(round(self.phases[2] + SYNMONTH * 86400))

    # toff: days offset with optional fraction
    def nextphase(self, text: bool = True):
        n = 0
        lun = 0  # Skip historic quarters
        while True:
            yield n, lun, self.quarter(n, text)
            n += 1
            n %= 4
            if n == 0:
                self._next_lunation()
                lun += 1

    def _check_lto(self, lto: float) -> int:
        if not -15 < lto < 15:
            raise ValueError("Invalid local time offset.")
        return round(lto * 3600)

    # Populate the phase array. Fast return if phases are alrady correct.
    # Find time of phases of the moon which surround the passed datetime.
    # Five phases are found, starting and ending with the new moons which bound
    # the specified lunation.
    # Passed time, and the result in .phases, are seconds since hardware epoch
    # adjusted for UTC: i.e. as if the RTC were running UTC rather than local time.
    def _populate(self, t: int):
        if self.phases[0] < t < self.phases[4]:
            return  # Nothing to do
        # Return days since Jan 0.5 1900 as a float. Returns same value on 32 and 64 bits
        def jd1900(t: int) -> float:
            y, m, mday = time.localtime(t)[:3]
            if m <= 2:
                m += 12
                y -= 1
            b = round(y / 400 - y / 100 + y / 4)
            mjm = 365 * y - 679004 + b + int(30.6001 * (m + 1)) + mday
            return mjm - 15019.5

        sdate: float = jd1900(t)  # Days since 1900 January 0.5
        adate: float = sdate - 45
        yy, mm, dd = time.localtime(t)[:3]
        k1: int = floor((yy + ((mm - 1) * (1.0 / 12.0)) - 1900) * 12.3685)  # 365.25/SYNMONTH
        adate = meanphase(adate, k1)  # Find new moon well before current date
        nt1: float = adate
        while True:
            adate += SYNMONTH  # For each lunar month
            k2: int = k1 + 1
            nt2: float = meanphase(adate, k2)
            if nt1 <= sdate and nt2 > sdate:
                break
            nt1 = nt2
            k1 = k2
        # k is integer days since start of 1900, being the lunation number
        # 1533, 1534 on both platforms.
        for n, k in enumerate((k1, k1, k1, k1, k2)):
            phi: int = truephase(k, n % 4)  # Args lunation no., phase no. 0..3
            self.phases[n] = phi - self.jepoch  # Julian datetime to secs since hardware epoch
            # Datetimes in secs since hardware epoch based on UTC
