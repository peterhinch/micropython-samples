# sun_moon.py MicroPython Port of lunarmath.c
# Calculate sun and moon rise and set times for any date and location

# Copyright (c) 2023 Peter Hinch
# Released under the MIT License (MIT) - see LICENSE file

# Source "Astronomy on the Personal Computer" by Montenbruck and Pfleger
# ISBN 978-3-540-67221-0

import time
from math import sin, cos, sqrt, fabs, atan, radians, floor

LAT = 53.29756504536339  # Local defaults
LONG = -2.102811634540558
MOON_PHASE_LENGTH = 29.530588853


def quad(ym, yz, yp):
    # See Astronomy on the PC P48-49
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
        dx = 0.5 * sqrt(dis) / fabs(a)
        z1 = xe - dx
        z2 = xe + dx
        if fabs(z1) <= 1.0:
            nz += 1
        if fabs(z2) <= 1.0:
            nz += 1
        if z1 < -1.0:
            z1 = z2
    return nz, z1, z2, ye


# **** GET MODIFIED JULIAN DATE FOR DAY RELATIVE TO TODAY ****

# Takes the system time in seconds from 1 Jan 70 & returns
# modified julian day number defined as mjd = jd - 2400000.5
# Deals only in integer MJD's: the JD of just after midnight will always end in 0.5
# hence the MJD of an integer day number will always be an integer

# MicroPython wanton epochs:
# time.gmtime(0)[0] = 1970 or 2000 depending on platform.
# (date(2000, 1, 1) - date(1970, 1, 1)).days * 24*60*60 = 946684800
# (date(2000, 1, 1) - date(1970, 1, 1)).days = 10957

# Re platform comparisons get_mjd does integer arithmetic and returns the same
# value regardless of the platform's epoch
def get_mjd(ndays: int = 0) -> int:  # Days offset from today
    secs_per_day = 86400  # 24 * 3600
    tsecs = time.time()  # Time now in secs since epoch
    tsecs -= tsecs % secs_per_day  # Time last midnight
    tsecs += secs_per_day * ndays  # Specified day
    days_from_epoch = round(tsecs / secs_per_day)  # Days from 1 Jan 70
    # tsecs += secs_per_day # 2  # Noon
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
    phi = (tmp - 2451550.1) / MOON_PHASE_LENGTH
    return phi % 1


def minisun(t):
    # Output dec, ra
    # returns the ra and dec of the Sun
    # in decimal hours, degs referred to the equinox of date and using
    # obliquity of the ecliptic at J2000.0 (small error for +- 100 yrs)
    # takes t centuries since J2000.0. Claimed good to 1 arcmin
    p2 = 6.283185307
    coseps = 0.91748
    sineps = 0.39778

    M = p2 * frac(0.993133 + 99.997361 * t)
    DL = 6893.0 * sin(M) + 72.0 * sin(2 * M)
    L = p2 * frac(0.7859453 + M / p2 + (6191.2 * t + DL) / 1296000)
    SL = sin(L)
    X = cos(L)
    Y = coseps * SL
    Z = sineps * SL
    RHO = sqrt(1 - Z * Z)
    dec = (360.0 / p2) * atan(Z / RHO)
    ra = (48.0 / p2) * atan(Y / (X + RHO))
    if ra < 0:
        ra += 24
    return dec, ra


def minimoon(t):
    # takes t and returns the geocentric ra and dec
    # claimed good to 5' (angle) in ra and 1' in dec
    # tallies with another approximate method and with ICE for a couple of dates

    p2 = 6.283185307
    arc = 206264.8062
    coseps = 0.91748
    sineps = 0.39778

    L0 = frac(0.606433 + 1336.855225 * t)  # mean longitude of moon
    L = p2 * frac(0.374897 + 1325.552410 * t)  # mean anomaly of Moon
    LS = p2 * frac(0.993133 + 99.997361 * t)  # mean anomaly of Sun
    D = p2 * frac(0.827361 + 1236.853086 * t)  # difference in longitude of moon and sun
    F = p2 * frac(0.259086 + 1342.227825 * t)  # mean argument of latitude

    # corrections to mean longitude in arcsec
    DL = 22640 * sin(L)
    DL += -4586 * sin(L - 2 * D)
    DL += +2370 * sin(2 * D)
    DL += +769 * sin(2 * L)
    DL += -668 * sin(LS)
    DL += -412 * sin(2 * F)
    DL += -212 * sin(2 * L - 2 * D)
    DL += -206 * sin(L + LS - 2 * D)
    DL += +192 * sin(L + 2 * D)
    DL += -165 * sin(LS - 2 * D)
    DL += -125 * sin(D)
    DL += -110 * sin(L + LS)
    DL += +148 * sin(L - LS)
    DL += -55 * sin(2 * F - 2 * D)

    # simplified form of the latitude terms
    S = F + (DL + 412 * sin(2 * F) + 541 * sin(LS)) / arc
    H = F - 2 * D
    N = -526 * sin(H)
    N += +44 * sin(L + H)
    N += -31 * sin(-L + H)
    N += -23 * sin(LS + H)
    N += +11 * sin(-LS + H)
    N += -25 * sin(-2 * L + F)
    N += +21 * sin(-L + F)

    # ecliptic long and lat of Moon in rads
    L_moon = p2 * frac(L0 + DL / 1296000)
    B_moon = (18520.0 * sin(S) + N) / arc

    # equatorial coord conversion - note fixed obliquity
    CB = cos(B_moon)
    X = CB * cos(L_moon)
    V = CB * sin(L_moon)
    W = sin(B_moon)
    Y = coseps * V - sineps * W
    Z = sineps * V + coseps * W
    RHO = sqrt(1.0 - Z * Z)
    dec = (360.0 / p2) * atan(Z / RHO)
    ra = (48.0 / p2) * atan(Y / (X + RHO))
    if ra < 0:
        ra += 24
    return dec, ra


class RiSet:
    def __init__(self, lat=LAT, long=LONG):  # Local defaults
        self.sglat = sin(radians(lat))
        self.cglat = cos(radians(lat))
        self.long = long
        self.mjd = None  # Current integer MJD
        # Times in integer secs from midnight on current day
        self._sr = None  # Sunrise
        self._ss = None  # Sunset
        self._mr = None  # Moonrise
        self._ms = None  # Moon set
        self.set_day()  # Initialise to today's date

    # ***** API start *****
    # 109μs on PBD-SF2W 166μs on ESP32-S3 394μs on RP2 (standard clocks)
    def set_day(self, day=0):
        mjd = get_mjd(day)
        if self.mjd is None or self.mjd != mjd:
            spd = 86400  # Secs per day
            self._t0 = ((round(time.time()) + day * spd) // spd) * spd  # Midnight on target day
            self.mjd = mjd
            self._sr, self._ss = self.rise_set(True)  # Sun
            self._mr, self._ms = self.rise_set(False)  # Moon
            t = time.gmtime(time.time() + day * 86400)
            self._phase = moonphase(*t[:4])

    def sunrise(self, to=0):
        return self._format(self._sr, to)

    def sunset(self, to=0):
        return self._format(self._ss, to)

    def moonrise(self, to=0):
        return self._format(self._mr, to)

    def moonset(self, to=0):
        return self._format(self._ms, to)

    def moonphase(self):
        return self._phase

    # ***** API end *****
    def _format(self, n, to):
        if to == 0:  # Default: secs since Midnight
            return n
        elif to == 1:  # Secs since epoch
            return None if n is None else n + self._t0
        # to == 3
        if n is None:
            return "--:--:--"
        else:
            hr, tmp = divmod(n, 3600)
            mi, sec = divmod(tmp, 60)
            return f"{hr:02d}:{mi:02d}:{sec:02d}"

    def lmst(self, mjd):
        # Takes the mjd and the longitude (west negative) and then returns
        # the local sidereal time in hours. Im using Meeus formula 11.4
        # instead of messing about with UTo and so on
        d = mjd - 51544.5
        t = d / 36525.0
        lst = 280.46061837 + 360.98564736629 * d + 0.000387933 * t * t - t * t * t / 38710000
        return (lst % 360) / 15.0 + self.long / 15

    def sin_alt(self, hour, func):
        # Returns the sine of the altitude of the object (moon or sun)
        # at an hour relative to the current date (mjd)
        mjd = self.mjd + hour / 24.0
        t = (mjd - 51544.5) / 36525.0
        dec, ra = func(t)
        # hour angle of object: one hour = 15 degrees. Note lmst() uses longitude
        tau = 15.0 * (self.lmst(mjd) - ra)
        # sin(alt) of object using the conversion formulas
        salt = self.sglat * sin(radians(dec)) + self.cglat * cos(radians(dec)) * cos(radians(tau))
        return salt

    # Modified to find sunrise and sunset only, not twilight events.
    def rise_set(self, sun):
        # this is my attempt to encapsulate most of the program in a function
        # then this function can be generalised to find all the Sun events.
        t_rise = None  # Rise and set times in secs from midnight
        t_set = None
        sinho = sin(radians(-0.833)) if sun else sin(radians(8 / 60))
        # moonrise taken as centre of moon at +8 arcmin
        # sunset upper limb simple refraction
        # The loop finds the sin(alt) for sets of three consecutive
        # hours, and then tests for a single zero crossing in the interval
        # or for two zero crossings in an interval for for a grazing event
        func = minisun if sun else minimoon
        yp = self.sin_alt(0, func) - sinho
        for hour in range(1, 24, 2):
            ym = yp
            yz = self.sin_alt(hour, func) - sinho
            yp = self.sin_alt(hour + 1, func) - sinho
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


r = RiSet()
t = time.ticks_us()
r.set_day()
print("Elapsed us", time.ticks_diff(time.ticks_us(), t))
for d in range(7):
    print(f"Day {d}")
    r.set_day(d)
    print(f"Sun rise {r.sunrise(3)} set {r.sunset(3)}")
    print(f"Moon rise {r.moonrise(3)} set {r.moonset(3)}")

print(r.sunrise(1))
for d in range(30):
    r.set_day(d)
    print(round(r.moonphase() * 1000))
