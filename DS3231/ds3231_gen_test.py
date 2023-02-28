# ds3231_gen_test.py Test script for ds3231_gen.oy.

# Author: Peter Hinch
# Copyright Peter Hinch 2023 Released under the MIT license.

from machine import SoftI2C, Pin
from ds3231_gen import *
import time
import uasyncio as asyncio

def dt_tuple(dt):
    return time.localtime(time.mktime(dt))  # Populate weekday field

i2c = SoftI2C(scl=Pin(16, Pin.OPEN_DRAIN, value=1), sda=Pin(17, Pin.OPEN_DRAIN, value=1))
d = DS3231(i2c)

async def wait_for_alarm(alarm, t, target):  # Wait for n seconds for an alarm, check time of occurrence
    print(f"Wait {t} secs for alarm...")
    if alarm.alno == 2:
        target = 0  # Alarm 2 does not support secs
    while t:
        if alarm():
            return target - 1 <= d.get_time()[5] <= target + 1
        await asyncio.sleep(1)
        t -= 1
    return False

async def test_alarm(alarm):
    print("Test weekly alarm")
    result = True
    dt = dt_tuple((2023, 2, 28, 23, 59, 50, 0, 0))
    d.set_time(dt)  # day is 1
    alarm.set(EVERY_WEEK, day=2, sec=5)  # Weekday
    alarm.clear()
    if await wait_for_alarm(alarm, 20, 5):  # Should alarm on rollover from day 1 to 2
        print("\x1b[32mWeek test 1 pass\x1b[39m")
    else:
        print("\x1b[91mWeek test 1 fail\x1b[39m")
        result = False

    dt = dt_tuple((2023, 2, 27, 23, 59, 50, 0, 0))
    d.set_time(dt)  # day is 0
    alarm.set(EVERY_WEEK, day=2, sec=5)
    alarm.clear()
    if await wait_for_alarm(alarm, 20, 5):  # Should not alarm on rollover from day 0 to 1
        print("\x1b[91mWeek test 2 fail\x1b[39m")
        result = False
    else:
        print("\x1b[32mWeek test 2 pass\x1b[39m")

    print("Test monthly alarm")
    dt = dt_tuple((2023, 2, 28, 23, 59, 50, 0, 0))
    d.set_time(dt)  # day is 1
    alarm.set(EVERY_MONTH, day=1, sec=5)  # Day of month
    alarm.clear()
    if await wait_for_alarm(alarm, 20, 5):  # Should alarm on rollover from 28th to 1st
        print("\x1b[32mMonth test 1 pass\x1b[39m")
    else:
        print("\x1b[91mMonth test 1 fail\x1b[39m")
        result = False

    dt = dt_tuple((2023, 2, 27, 23, 59, 50, 0, 0))
    d.set_time(dt)  # day is 0
    alarm.set(EVERY_MONTH, day=1, sec=5)
    alarm.clear()
    if await wait_for_alarm(alarm, 20, 5):  # Should not alarm on rollover from day 27 to 28
        print("\x1b[91mMonth test 2 fail\x1b[39m")
        result = False
    else:
        print("\x1b[32mMonth test 2 pass\x1b[39m")

    print("Test daily alarm")
    dt = dt_tuple((2023, 2, 1, 23, 59, 50, 0, 0))
    d.set_time(dt)  # 23:59:50
    alarm.set(EVERY_DAY, hr=0, sec=5)
    alarm.clear()
    if await wait_for_alarm(alarm, 20, 5):  # Should alarm at 00:00:05
        print("\x1b[32mDaily test 1 pass\x1b[39m")
    else:
        print("\x1b[91mDaily test 1 fail\x1b[39m")
        result = False

    dt = dt_tuple((2023, 2, 1, 22, 59, 50, 0, 0))
    d.set_time(dt)  # 22:59:50
    alarm.set(EVERY_DAY, hr=0, sec=5)
    alarm.clear()
    if await wait_for_alarm(alarm, 20, 5):  # Should not alarm at 22:00:05
        print("\x1b[91mDaily test 2 fail\x1b[39m")
        result = False
    else:
        print("\x1b[32mDaily test 2 pass\x1b[39m")

    print("Test hourly alarm")
    dt = dt_tuple((2023, 2, 1, 20, 9, 50, 0, 0))
    d.set_time(dt)  # 20:09:50
    alarm.set(EVERY_HOUR, min=10, sec=5)
    alarm.clear()
    if await wait_for_alarm(alarm, 20, 5):  # Should alarm at xx:10:05
        print("\x1b[32mDaily test 1 pass\x1b[39m")
    else:
        print("\x1b[91mDaily test 1 fail\x1b[39m")
        result = False

    dt = dt_tuple((2023, 2, 1, 20, 29, 50, 0, 0))
    d.set_time(dt)  # 20:29:50
    alarm.set(EVERY_HOUR, min=10, sec=5)
    alarm.clear()
    if await wait_for_alarm(alarm, 20, 5):  # Should not alarm at xx:30:05
        print("\x1b[91mDaily test 2 fail\x1b[39m")
        result = False
    else:
        print("\x1b[32mDaily test 2 pass\x1b[39m")

    print("Test minute alarm")
    dt = dt_tuple((2023, 2, 1, 20, 9, 50, 0, 0))
    d.set_time(dt)  # 20:09:50
    alarm.set(EVERY_MINUTE, sec=5)
    alarm.clear()
    if await wait_for_alarm(alarm, 20, 5):  # Should alarm at xx:xx:05
        print("\x1b[32mMinute test 1 pass\x1b[39m")
    else:
        print("\x1b[91mMinute test 1 fail\x1b[39m")
        result = False

    if alarm.alno == 2:
        print("Skipping minute test 2: requires seconds resolution unsupported by alarm2.")
    else:
        dt = dt_tuple((2023, 2, 1, 20, 29, 50, 0, 0))
        d.set_time(dt)  # 20:29:50
        alarm.set(EVERY_MINUTE, sec=30)
        alarm.clear()
        if await wait_for_alarm(alarm, 20, 5):  # Should not alarm at xx:xx:05
            print("\x1b[91mMinute test 2 fail\x1b[39m")
            result = False
        else:
            print("\x1b[32mMinute test 2 pass\x1b[39m")

    if alarm.alno == 2:
        print("Skipping seconds test: unsupported by alarm2.")
    else:
        print("Test seconds alarm (test takes 1 minute)")
        dt = dt_tuple((2023, 2, 1, 20, 9, 20, 0, 0))
        d.set_time(dt)  # 20:09:20
        alarm.set(EVERY_SECOND)
        alarm_count = 0
        t = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t) < 60_000:
            alarm.clear()
            while not d.alarm1():
                await asyncio.sleep(0)
            alarm_count += 1
        if 59 <= alarm_count <= 61:
            print("\x1b[32mSeconds test 1 pass\x1b[39m")
        else:
            print("\x1b[91mSeconds test 2 fail\x1b[39m")
            result = False
    alarm.enable(False)
    return result
        

async def main():
    print("Testing alarm 1")
    result = await test_alarm(d.alarm1)
    print("Teting alarm 2")
    result |= await test_alarm(d.alarm2)
    if result:
        print("\x1b[32mAll tests passed\x1b[39m")
    else:
        print("\x1b[91mSome tests failed\x1b[39m")

asyncio.run(main())


    
