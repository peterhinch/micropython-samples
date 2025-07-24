# rp2_rmt_test.py Demo for rp2_rmt

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2021 Peter Hinch


from time import sleep_ms
import array
from machine import Pin
from .rp2_rmt import RP2_RMT


def test():
    ar = array.array("H", [800, 400, 800, 400, 800, 400, 800, 400, 0])
    # Pulse and carrier
    rmt = RP2_RMT(Pin(16, Pin.OUT), (Pin(17), 38000, 33))
    # Pulse only
    # rmt = RP2_RMT(Pin(16, Pin.OUT))
    # Carrier only
    # rmt = RP2_RMT(None, (Pin(17), 38000, 33))
    rmt.send(ar, 0)
    sleep_ms(10_000)
    rmt.cancel()
    while rmt.busy():
        sleep_ms(10)

    while True:
        sleep_ms(400)
        rmt.send(ar, 1)


test()

# Format of IR array: on/off times (μs). Realistic minimum 440/440
# ar = array.array("H", [400 if x & 1 else 800 for x in range(9)])
# ar[-1] = 0  # STOP
# Fastest IRQ rate ~444μs (Philips RC6)
