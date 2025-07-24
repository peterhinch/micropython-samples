# measure_pulse.py Measure a pulse train with PIO

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2025 Peter Hinch

# Link GPIO16-GPIO17 to test

from machine import Pin, PWM
import rp2
import time


@rp2.asm_pio(set_init=rp2.PIO.IN_LOW, autopush=True, push_thresh=32)
def period():
    wrap_target()
    set(x, 0)
    wait(0, pin, 0)  # Wait for pin to go low
    wait(1, pin, 0)  # Low to high transition
    label("low_high")
    jmp(x_dec, "next")[1]  # unconditional
    label("next")
    jmp(pin, "low_high")  # while pin is high
    label("low")  # pin is low
    jmp(x_dec, "nxt")
    label("nxt")
    jmp(pin, "done")  # pin has gone high: all done
    jmp("low")
    label("done")
    in_(x, 32)  # Auto push: SM stalls if FIFO full
    wrap()


@rp2.asm_pio(set_init=rp2.PIO.IN_LOW, autopush=True, push_thresh=32)
def mark():
    wrap_target()
    set(x, 0)
    wait(0, pin, 0)  # Wait for pin to go low
    wait(1, pin, 0)  # Low to high transition
    label("low_high")
    jmp(x_dec, "next")[1]  # unconditional
    label("next")
    jmp(pin, "low_high")  # while pin is high
    in_(x, 32)  # Auto push: SM stalls if FIFO full
    wrap()


ck = 100_000_000  # Clock rate in Hz.
pin16 = Pin(16, Pin.IN, Pin.PULL_UP)
sm0 = rp2.StateMachine(0, period, in_base=pin16, jmp_pin=pin16, freq=ck)
sm0.active(1)
sm1 = rp2.StateMachine(1, mark, in_base=pin16, jmp_pin=pin16, freq=ck)
sm1.active(1)

# Clock is 100MHz. 3 cycles per iteration, so unit is 30.0ns
def scale(v):
    return (1 + (v ^ 0xFFFFFFFF)) * 3000 / ck  # Scale to ms


# ***** TEST WITH PWM *****
pwm = PWM(Pin(17))
pwm.freq(1000)
pwm.duty_u16(0xFFFF // 3)

while True:
    period = scale(sm0.get())
    mark = scale(sm1.get())
    print(f"Period {period}ms Mark {mark}ms  m/s {100*mark / (period - mark):5.2f}%")
    time.sleep(0.2)
