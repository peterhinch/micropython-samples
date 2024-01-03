# sun_moon_test.py Test script for sun_moon.py

# Copyright (c) Peter Hinch 2023
# Released under the MIT license (see LICENSE)

# On mip-installed host:
# import sched.sun_moon_test
# On PC in astronomy directory:
# import sun_moon_test

try:
    from .sun_moon import RiSet
except ImportError:  # Running on PC in astronomy directory
    from sun_moon import RiSet
import time


def mtime(h, m, t=None):
    if t is None:
        t = round(time.time())
    tm = (t // 86400) * 86400 + h * 3600 + m * 60
    print(time.gmtime(tm))
    return tm


nresults = []  # Times in seconds from local midnight


def show(rs):
    print(f"Sun rise {rs.sunrise(3)} set {rs.sunset(3)}")
    print(f"Moon rise {rs.moonrise(3)} set {rs.moonset(3)}")
    nresults.extend([rs.sunrise(), rs.sunset(), rs.moonrise(), rs.moonset()])
    print()


print("4th Dec 2023: Seattle UTC-8")
rs = RiSet(lat=47.61, long=-122.35, lto=-8)  # Seattle 47°36′35″N 122°19′59″W
RiSet.set_time(19695 * 86400)
rs.set_day()
show(rs)

print("4th Dec 2023: Sydney UTC+11")
rs = RiSet(lat=-33.86, long=151.21, lto=11)  # Sydney 33°52′04″S 151°12′36″E
RiSet.set_time(19695 * 86400)
rs.set_day()
show(rs)

print("From 4th Dec 2023: UK, UTC")
rs = RiSet()
for day in range(7):
    RiSet.set_time(19695 * 86400)
    rs.set_day(day)
    # rs.set_day(abs_to_rel_days(19695 + day))  # Start 4th Dec 2023
    print(f"Day: {day}")
    show(rs)


print("4th Dec 2023: Sydney UTC+11 - test DST")
# Sydney 33°52′04″S 151°12′36″E
rs = RiSet(lat=-33.86, long=151.21, lto=11, dst=lambda x: x + 3600)
RiSet.set_time(19695 * 86400 + 86400 / 2)
rs.set_day()
# rs.set_day(abs_to_rel_days(19695))  # 4th Dec 2023
show(rs)


# Expected results as computed on Unix build (64-bit FPU)
exp = [
    27628,
    58714,
    85091,
    46417,
    20212,
    71598,
    2747,
    41257,
    29049,
    57158,
    82965,
    46892,
    29130,
    57126,
    None,
    47460,
    29209,
    57097,
    892,
    47958,
    29285,
    57072,
    5244,
    48441,
    29359,
    57051,
    9625,
    48960,
    29430,
    57033,
    14228,
    49577,
    29499,
    57019,
    19082,
    50384,
    20212 + 3600,
    71598 + 3600,
    2747 + 3600,
    41257 + 3600,
]
print()
max_error = 0
for act, requirement in zip(nresults, exp):
    if act is not None and requirement is not None:
        err = abs(requirement - act)
        max_error = max(max_error, err)
        if err > 30:
            print(f"Error {requirement - act}")

print(f"Maximum error {max_error}. Expect 0 on 64-bit platform, 30s on 32-bit")

# Times from timeanddate.com
# Seattle
# Sunrise 7:40 sunset 16:18 Moonrise 23:37 Moonset 12:53
# Sydney
# Sunrise 5:37 sunset 19:53 Moonrise 00:45 Moonset 11:28
# UK
# Sunrise 8:04 sunset 15:52 Moonrise 23:02 Moonset 13:01


def testup(t):  # Time in secs since machine epoch
    t = round((t // 86400) * 86400 + 60)  # 1 minute past midnight
    rs = RiSet()
    RiSet.set_time(t)
    rs.set_day()
    tr = rs.moonrise()
    ts = rs.moonset()
    print(f"testup rise {rs.moonrise(2)} set {rs.moonset(2)}")
    if tr is None and ts is None:
        print(time.gmtime(t), "No moon events")
        print(
            f"Is up {rs.is_up(False)} Has risen {rs.has_risen(False)} has set {rs.has_set(False)}"
        )
        return
    # Initial state: not risen or set
    assert not rs.has_set(False)
    assert not rs.has_risen(False)
    if tr is not None and (ts is None or ts > tr):
        assert not rs.is_up(False)
        rs.set_time(t + tr)
        assert rs.has_risen(False)
        assert rs.is_up(False)
        assert not rs.has_set(False)
        if ts is not None:
            rs.set_time(t + ts)
            assert rs.has_risen(False)
            assert not rs.is_up(False)
            assert rs.has_set(False)
        return
    if ts is not None:
        assert rs.is_up(False)
        rs.set_time(t + ts)
        assert not rs.has_risen(False)
        assert not rs.is_up(False)
        assert rs.has_set(False)
        if tr is not None:
            rs.set_time(t + tr)
            assert rs.has_risen(False)
            assert rs.is_up(False)
            assert rs.has_set(False)
        return
    print(f"Untested state tr {tr} ts {ts}")


# t = time.time()
# for d in range(365):
#     testup(t + d * 86400)
