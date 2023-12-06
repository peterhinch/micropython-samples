# sun_moon.py MicroPython Port of lunarmath.c
# Calculate sun and moon rise and set times for any date and location

# Licensing and copyright: see README.md

# Source "Astronomy on the Personal Computer" by Montenbruck and Pfleger
# ISBN 978-3-540-67221-0
# Also contributions from Raul Kompaß and Marcus Mendenhall: see
# https://github.com/orgs/micropython/discussions/13075
# Raul Kompaß perfomed major simplification of the maths for deriving rise and set_times.


import time
from math import sin, cos, sqrt, fabs, atan, radians, floor, pi

LAT = 53.29756504536339  # Local defaults
LONG = -2.102811634540558

# MicroPython wanton epochs:
# time.gmtime(0)[0] = 1970 or 2000 depending on platform.
# On CPython:
# (date(2000, 1, 1) - date(1970, 1, 1)).days * 24*60*60 = 946684800
# (date(2000, 1, 1) - date(1970, 1, 1)).days = 10957

# Return time now in days relative to platform epoch.
# System time is set to local time, and MP has no concept of this. Hence
# time.time() returns secs since epoch 00:00:00 local time. If lto is local time
# offset to UTC, provided -12 < lto < 12, the effect of rounding ensures the
# right number of days for platform epoch at UTC.
def now_days() -> int:
    secs_per_day = 86400  # 24 * 3600
    t = time.time()
    t -= t % secs_per_day  # Previous Midnight
    return round(t / secs_per_day)  # Days since datum


# Convert number of days relative to the Unix epoch (1970,1,1) to a number of
# days relative to the current date. e.g. 19695 = 4th Dec 2023
# Platform independent.
def abs_to_rel_days(days: int) -> int:
    secs_per_day = 86400  # 24 * 3600
    now = now_days()  # Days since platform epoch
    if time.gmtime(0)[0] == 2000:  # Machine epoch
        now += 10957
    return days - now


def quad(ym, yz, yp):
    # See Astronomy on the PC P48-49, plus contribution from Marcus Mendenhall
    # finds the parabola throuh the three points (-1,ym), (0,yz), (1, yp)
    # and returns the values of x where the parabola crosses zero
    # (roots of the quadratic)
    # and the number of roots (0, 1 or 2) within the interval [-1, 1]
    nz = 0
    a = 0.5 * (ym + yp) - yz
    b = 0.5 * (yp - ym)
    c = yz
    xe = -b / (2 * a)
    ye = (a * xe + b) * xe + c
    dis = b * b - 4.0 * a * c  # discriminant of y=a*x^2 +bx +c
    if dis > 0:  # parabola has roots
        if b < 0:
            z2 = (-b + sqrt(dis)) / (2 * a)  # z2 is larger root in magnitude
        else:
            z2 = (-b - sqrt(dis)) / (2 * a)
        z1 = (c / a) / z2  # z1 is always closer to zero
        if fabs(z1) <= 1.0:
            nz += 1
        if fabs(z2) <= 1.0:
            nz += 1
        if z1 < -1.0:
            z1 = z2
        return nz, z1, z2, ye
    return 0, 0, 0, 0  # No roots


# **** GET MODIFIED JULIAN DATE FOR DAY RELATIVE TO TODAY ****

# Returns modified julian day number defined as mjd = jd - 2400000.5
# Deals only in integer MJD's: the JD of just after midnight will always end in 0.5
# hence the MJD of an integer day number will always be an integer

# Re platform comparisons get_mjd returns the same value regardless of
# the platform's epoch: integer days since 00:00 UTC on 17 November 1858.
def get_mjd(ndays: int = 0) -> int:
    secs_per_day = 86400  # 24 * 3600
    days_from_epoch = now_days() + ndays  # Days since platform epoch
    mjepoch = 40587  # Modified Julian date of C epoch (1 Jan 70)
    if time.gmtime(0)[0] == 2000:
        mjepoch += 10957
    return mjepoch + days_from_epoch  # Convert days from 1 Jan 70 to MJD


def frac(x):
    return x % 1


# Convert rise or set time to int. These can be None (no event).
def to_int(x):
    return None if x is None else round(x)


# Approximate moon phase in range 0.0..1.0 0.0 is new moon, 0.5 full moon
# Provenance of this cde is uncertain.
def moonphase(year, month, day, hour):
    fty = year - floor((12.0 - month) / 10.0)
    itm = month + 9
    if itm >= 12:
        itm -= 12
    term1 = floor(365.25 * (fty + 4712))
    term2 = floor(30.6 * itm + 0.5)
    term3 = floor(floor((fty / 100) + 49) * 0.75) - 38
    tmp = term1 + term2 + day + 59 + hour / 24.0
    if tmp > 2299160.0:
        tmp = tmp - term3
    phi = (tmp - 2451550.1) / 29.530588853  # 29.530588853 is length of lunar cycle (days)
    return phi % 1


def minisun(t):
    # Output sin(dec), cos(dec), ra
    # returns the ra and dec of the Sun
    # in decimal hours, degs referred to the equinox of date and using
    # obliquity of the ecliptic at J2000.0 (small error for +- 100 yrs)
    # takes t centuries since J2000.0. Claimed good to 1 arcmin
    coseps = 0.9174805004
    sineps = 0.397780757938

    m = 2 * pi * frac(0.993133 + 99.997361 * t)
    dl = 6893.0 * sin(m) + 72.0 * sin(2 * m)
    l = 2 * pi * frac(0.7859453 + m / (2 * pi) + (6191.2 * t + dl) / 1296000)
    sl = sin(l)
    x = cos(l)
    y = coseps * sl
    z = sineps * sl
    # rho = sqrt(1 - z * z)
    # dec = (360.0 / 2 * pi) * atan(z / rho)
    # ra = ((48.0 / (2 * pi)) * atan(y / (x + rho))) % 24
    return x, y, z


def minimoon(t):
    # takes t and returns the geocentric ra and dec
    # claimed good to 5' (angle) in ra and 1' in dec
    # tallies with another approximate method and with ICE for a couple of dates
    arc = 206264.8062
    coseps = 0.9174805004
    sineps = 0.397780757938

    l0 = frac(0.606433 + 1336.855225 * t)  # mean longitude of moon
    l = 2 * pi * frac(0.374897 + 1325.552410 * t)  # mean anomaly of Moon
    ls = 2 * pi * frac(0.993133 + 99.997361 * t)  # mean anomaly of Sun
    d = 2 * pi * frac(0.827361 + 1236.853086 * t)  # difference in longitude of moon and sun
    f = 2 * pi * frac(0.259086 + 1342.227825 * t)  # mean argument of latitude

    # corrections to mean longitude in arcsec
    dl = 22640 * sin(l)
    dl += -4586 * sin(l - 2 * d)
    dl += +2370 * sin(2 * d)
    dl += +769 * sin(2 * l)
    dl += -668 * sin(ls)
    dl += -412 * sin(2 * f)
    dl += -212 * sin(2 * l - 2 * d)
    dl += -206 * sin(l + ls - 2 * d)
    dl += +192 * sin(l + 2 * d)
    dl += -165 * sin(ls - 2 * d)
    dl += -125 * sin(d)
    dl += -110 * sin(l + ls)
    dl += +148 * sin(l - ls)
    dl += -55 * sin(2 * f - 2 * d)

    # simplified form of the latitude terms
    s = f + (dl + 412 * sin(2 * f) + 541 * sin(ls)) / arc
    h = f - 2 * d
    n = -526 * sin(h)
    n += +44 * sin(l + h)
    n += -31 * sin(-l + h)
    n += -23 * sin(ls + h)
    n += +11 * sin(-ls + h)
    n += -25 * sin(-2 * l + f)
    n += +21 * sin(-l + f)

    # ecliptic long and lat of Moon in rads
    l_moon = 2 * pi * frac(l0 + dl / 1296000)
    b_moon = (18520.0 * sin(s) + n) / arc

    # equatorial coord conversion - note fixed obliquity
    cb = cos(b_moon)
    x = cb * cos(l_moon)
    v = cb * sin(l_moon)
    w = sin(b_moon)
    y = coseps * v - sineps * w
    z = sineps * v + coseps * w
    # rho = sqrt(1.0 - z * z)
    # dec = (360.0 / 2 * pi) * atan(z / rho)
    # ra = ((48.0 / (2 * pi)) * atan(y / (x + rho))) % 24
    return x, y, z


class RiSet:
    def __init__(self, lat=LAT, long=LONG, lto=0):  # Local defaults
        self.sglat = sin(radians(lat))
        self.cglat = cos(radians(lat))
        self.long = long
        if not -12 < lto < 12:
            raise ValueError("Invalid local time offset.")
        self.lto = round(lto * 3600)  # Localtime offset in secs
        self.mjd = None  # Current integer MJD
        # Times in integer secs from midnight on current day (in local time)
        # [sunrise, sunset, moonrise, moonset]
        self._times = [None] * 4
        self.set_day()  # Initialise to today's date

    # ***** API start *****
    # Examine Julian dates either side of current one to cope with localtime.
    # 707μs on RP2040 at standard clock and with local time == UTC
    def set_day(self, day: int = 0):
        mjd = get_mjd(day)
        if self.mjd is None or self.mjd != mjd:
            spd = 86400  # Secs per day
            # ._t0 is time of midnight (local time) in secs since MicroPython epoch
            # time.time() assumes MicroPython clock is set to local time
            self._t0 = ((round(time.time()) + day * spd) // spd) * spd
            t = time.gmtime(time.time() + day * spd)
            self._phase = moonphase(*t[:4])
            self.update(mjd)  # Recalculate rise and set times
        return self  # Allow r.set_day().sunrise()

    # variants: 0 secs since 00:00:00 localtime. 1 secs since MicroPython epoch
    # (relies on system being set to localtime). 2 human-readable text.
    def sunrise(self, variant: int = 0):
        return self._format(self._times[0], variant)

    def sunset(self, variant: int = 0):
        return self._format(self._times[1], variant)

    def moonrise(self, variant: int = 0):
        return self._format(self._times[2], variant)

    def moonset(self, variant: int = 0):
        return self._format(self._times[3], variant)

    def moonphase(self) -> float:
        return self._phase

    def set_lto(self, t):  # Update the offset from UTC
        if not -12 < t < 12:
            raise ValueError("Invalid local time offset.")
        lto = round(t * 3600)  # Localtime offset in secs
        if self.lto != lto:  # changed
            self.lto = lto
            self.update(self.mjd)

    def is_up(self, sun: bool):  # Return current state of sun or moon
        self.set_day()  # Ensure today's date
        now = round(time.time()) + self.lto  # UTC
        rt = self.sunrise(1) if sun else self.moonrise(1)
        st = self.sunset(1) if sun else self.moonset(1)
        if rt is None:
            if st is None:
                t = (now % 86400) / 3600  # Time as UTC hours (float)
                return self.sin_alt(t, sun) > 0
            return st > now
        if st is None:
            return rt < now
        print(rt, now, st)
        return rt < now < st

    # This is in error by ~12 minutes: sin_alt() produces incorrect values
    # unless t corresponds to an exact hour. Odd.
    # def is_up(self, sun: bool):
    #     t = time.time() + self.lto  # UTC
    #     t %= 86400
    #     t /= 3600  # UTC Hour of day
    #     self.set_day()  # Ensure today's date
    #     return self.sin_alt(t, sun) > 0

    # ***** API end *****
    # Re-calculate rise and set times
    def update(self, mjd):
        self._times = [None] * 4
        days = (1, 2) if self.lto < 0 else (1,) if self.lto == 0 else (0, 1)
        for day in days:
            self.mjd = mjd + day - 1
            sr, ss = self.rise_set(True)  # Sun
            mr, ms = self.rise_set(False)  # Moon
            # Adjust for local time. Store in ._times if value is in 24-hour
            # local time window
            self.adjust((sr, ss, mr, ms), day)
        self.mjd = mjd

    def adjust(self, times, day):
        for idx, n in enumerate(times):
            if n is not None:
                n += self.lto + (day - 1) * 86400
                h = n // 3600
                if 0 <= h < 24:
                    self._times[idx] = n

    def _format(self, n, variant):
        if variant == 0:  # Default: secs since Midnight (local time)
            return n
        elif variant == 1:  # Secs since epoch of MicroPython platform
            return None if n is None else n + self._t0
        # variant == 3
        if n is None:
            return "--:--:--"
        else:
            hr, tmp = divmod(n, 3600)
            mi, sec = divmod(tmp, 60)
            return f"{hr:02d}:{mi:02d}:{sec:02d}"

    # See https://github.com/orgs/micropython/discussions/13075
    def lstt(self, t):
        # Takes the mjd and the longitude (west negative) and then returns
        # the local sidereal time in degrees. Im using Meeus formula 11.4
        # instead of messing about with UTo and so on
        # modified to use the pre-computed 't' value from sin_alt
        d = t * 36525
        df = frac(d)
        c1 = 360
        c2 = 0.98564736629
        dsum = c1 * df + c2 * d  # no large integer * 360 here
        lst = 280.46061837 + dsum + 0.000387933 * t * t - t * t * t / 38710000
        return lst % 360

    def sin_alt(self, hour, sun):
        # Returns the sine of the altitude of the object (moon or sun)
        # at an hour relative to the current date (mjd)
        func = minisun if sun else minimoon
        mjd = (self.mjd - 51544.5) + hour / 24.0
        # mjd = self.mjd + hour / 24.0
        t = mjd / 36525.0
        x, y, z = func(t)
        tl = self.lstt(t) + self.long  # Local mean sidereal time adjusted for logitude
        return self.sglat * z + self.cglat * (x * cos(radians(tl)) + y * sin(radians(tl)))

    # Modified to find sunrise and sunset only, not twilight events.
    # Calculate rise and set times of sun or moon for the current MJD. Times are
    # relative to that 24 hour period.
    def rise_set(self, sun):
        t_rise = None  # Rise and set times in secs from midnight
        t_set = None
        sinho = sin(radians(-0.833)) if sun else sin(radians(8 / 60))
        # moonrise taken as centre of moon at +8 arcmin
        # sunset upper limb simple refraction
        # The loop finds the sin(alt) for sets of three consecutive
        # hours, and then tests for a single zero crossing in the interval
        # or for two zero crossings in an interval for for a grazing event
        yp = self.sin_alt(0, sun) - sinho
        for hour in range(1, 24, 2):
            ym = yp
            yz = self.sin_alt(hour, sun) - sinho
            yp = self.sin_alt(hour + 1, sun) - sinho
            nz, z1, z2, ye = quad(ym, yz, yp)  # Find horizon crossings
            if nz == 1:  # One crossing found
                if ym < 0.0:
                    t_rise = 3600 * (hour + z1)
                else:
                    t_set = 3600 * (hour + z1)
            # case where two events are found in this interval
            # (rare but whole reason we are not using simple iteration)
            elif nz == 2:
                if ye < 0.0:
                    t_rise = 3600 * (hour + z2)
                    t_set = 3600 * (hour + z1)
                else:
                    t_rise = 3600 * (hour + z1)
                    t_set = 3600 * (hour + z2)

            if t_rise is not None and t_set is not None:
                break  # All done
        return to_int(t_rise), to_int(t_set)  # Convert to int preserving None values
