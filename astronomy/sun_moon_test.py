# sun_moon_test.py


from .sun_moon import RiSet, abs_to_rel_days


def show(rs):
    print(f"Sun rise {rs.sunrise(3)} set {rs.sunset(3)}")
    print(f"Moon rise {rs.moonrise(3)} set {rs.moonset(3)}")


print("4th Dec 2023: Seattle UTC-8")
rs = RiSet(lat=47.61, long=-122.35, lto=-8)  # Seattle 47°36′35″N 122°19′59″W
rs.set_day(abs_to_rel_days(19695))  # 4th Dec 2023
show(rs)
print()

print("4th Dec 2023: Sydney UTC+11")
rs = RiSet(lat=-33.86, long=151.21, lto=11)  # Sydney 33°52′04″S 151°12′36″E
rs.set_day(abs_to_rel_days(19695))  # 4th Dec 2023
show(rs)
print()

print("From 4th Dec 2023: UK, UTC")
rs = RiSet()
for day in range(7):
    rs.set_day(abs_to_rel_days(19695 + day))  # Start 4th Dec 2023
    print(f"Day: {day}")
    show(rs)

# Times from timeanddate.com
# Seattle
# Sunrise 7:40 sunset 16:18 Moonrise 23:37 Moonset 12:53
# Sydney
# Sunrise 5:37 sunset 19:53 Moonrise 00:45 Moonset 11:28
# UK
# Sunrise 8:04 sunset 15:52 Moonrise 23:02 Moonset 13:01
