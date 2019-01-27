# swdt_tests Test/demo scripts for soft_wdt

# Copyright (c) Peter Hinch 2019
# Released under the MIT licence.
import utime
from soft_wdt import wdt_feed, WDT_CANCEL, WDT_SUSPEND

# Exception trapping and cancellation are invaluable when debugging code: put
# cancellation in the finally block of a try statement so that the hardware
# doesn't reset when code terminates either naturally or in response to an
# error or ctrl-c interrupt.

# Normal operation. Illustrates exception trapping. You can interrupt this with
# ctrl-c
def normal():
    try:
        for x in range(10, 0, -1):
            print('nunning', x)
            utime.sleep(0.5)
            wdt_feed(5)  # Hold off for 5s

        print('Should reset in 5s')
        utime.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        wdt_feed(WDT_CANCEL)  # Should never execute

# Suspend and resume

def suspend():
    for x in range(10, 0, -1):
        print('nunning', x)
        utime.sleep(0.5)
        wdt_feed(5)  # Hold off for 5s

    wdt_feed(WDT_SUSPEND)
    for x in range(5, 0, -1):
        print('suspended', x)
        utime.sleep(0.5)

    for x in range(5, 0, -1):
        print('nunning', x)
        utime.sleep(0.5)
        wdt_feed(5)  # Hold off for 5s

    print('Should reset in 5s')
    utime.sleep(10)
    wdt_feed(WDT_CANCEL)  # Should never execute

# Default period

def default():
    for x in range(10, 0, -1):
        print('nunning', x)
        utime.sleep(0.5)
        wdt_feed(5)  # Hold off for 5s

    wdt_feed(0)  # Use default period
    print('Should reset in 2s')
    utime.sleep(10)
    wdt_feed(WDT_CANCEL)  # Should never execute

# Cancellation
def cancel():
    for x in range(10, 0, -1):
        print('nunning', x)
        utime.sleep(0.5)
        wdt_feed(5)  # Hold off for 5s

    wdt_feed(WDT_CANCEL)

    print('Pause 10s: should not reset in 5s')
    utime.sleep(10)
    print('WDT is permanently cancelled.')
