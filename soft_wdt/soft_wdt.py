# soft_wdt.py A software watchdog timer
# Supports fixed or variable time period.
# Supports temporary suspension and permanent cancellation.

# Copyright (c) Peter Hinch 2019
# Released under the MIT licence.

from machine import Timer, reset
from micropython import const
WDT_SUSPEND = const(-1)
WDT_CANCEL = const(-2)
WDT_CB = const(-3)

def wdt(secs=0):
    timer = Timer(-1)
    timer.init(period=1000, mode=Timer.PERIODIC, callback=lambda t:wdt_feed())
    cnt = secs
    run = False  # Disable until 1st feed
    def inner(feed=WDT_CB):
        nonlocal cnt, run, timer
        if feed > 0:  # Call with variable timeout
            cnt = feed
            run = True
        elif feed == 0:  # Fixed timeout
            cnt = secs
            run = True
        elif feed < 0:  # WDT control/callback
            if feed == WDT_SUSPEND:
                run = False  # Temporary suspension
            elif feed == WDT_CANCEL:
                timer.deinit()  # Permanent cancellation
            elif feed == WDT_CB and run:  # Timer callback and is running.
                cnt -= 1
                if cnt <= 0:
                    reset()
    return inner

wdt_feed = wdt(2)  # Modify this for preferred default period (secs)
