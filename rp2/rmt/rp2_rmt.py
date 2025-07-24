# rp2_rmt.py A RMT-like class for the RP2.

# Released under the MIT License (MIT). See LICENSE.

# Copyright (c) 2021 Peter Hinch

from machine import Pin, PWM
import rp2


@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, autopull=True, pull_thresh=32)
def pulsetrain():
    wrap_target()
    out(x, 32)  # No of 1MHz ticks. Block if FIFO MT at end.
    irq(rel(0))
    set(pins, 1)  # Set pin high
    label("loop")
    jmp(x_dec, "loop")
    irq(rel(0))
    set(pins, 0)  # Set pin low
    out(y, 32)  # Low time.
    label("loop_lo")
    jmp(y_dec, "loop_lo")
    wrap()


@rp2.asm_pio(autopull=True, pull_thresh=32)
def irqtrain():
    wrap_target()
    out(x, 32)  # No of 1MHz ticks. Block if FIFO MT at end.
    irq(rel(0))
    label("loop")
    jmp(x_dec, "loop")
    wrap()


class DummyPWM:
    def duty_u16(self, _):
        pass


class RP2_RMT:
    def __init__(self, pin_pulse=None, carrier=None, sm_no=0, sm_freq=1_000_000):
        if carrier is None:
            self.pwm = DummyPWM()
            self.duty = (0, 0)
        else:
            pin_car, freq, duty = carrier
            self.pwm = PWM(pin_car)  # Set up PWM with carrier off.
            self.pwm.freq(freq)
            self.pwm.duty_u16(0)
            self.duty = (int(0xFFFF * duty // 100), 0)
        if pin_pulse is None:
            self.sm = rp2.StateMachine(sm_no, irqtrain, freq=sm_freq)
        else:
            self.sm = rp2.StateMachine(sm_no, pulsetrain, freq=sm_freq, set_base=pin_pulse)
        self.apt = 0  # Array index
        self.arr = None  # Array
        self.ict = None  # Current IRQ count
        self.icm = 0  # End IRQ count
        self.reps = 0  # 0 == forever n == no. of reps
        rp2.PIO(0).irq(self._cb)

    # IRQ callback. Because of FIFO IRQ's keep arriving after STOP.
    def _cb(self, pio):
        self.pwm.duty_u16(self.duty[self.ict & 1])
        self.ict += 1
        if d := self.arr[self.apt]:  # If data available feed FIFO
            self.sm.put(d)
            self.apt += 1
        else:
            if r := self.reps != 1:  # All done if reps == 1
                if r:  # 0 == run forever
                    self.reps -= 1
                self.sm.put(self.arr[0])
                self.apt = 1  # Set pointer and count to state
                self.ict = 1  # after 1st IRQ

    # Arg is an array of times in μs terminated by 0.
    def send(self, ar, reps=1, check=True):
        self.sm.active(0)
        self.reps = reps
        ar[-1] = 0  # Ensure at least one STOP
        for x, d in enumerate(ar):  # Find 1st STOP
            if d == 0:
                break
        if check:
            # Discard any trailing mark which would leave carrier on.
            if x & 1:
                x -= 1
                ar[x] = 0
        self.icm = x  # index of 1st STOP
        mv = memoryview(ar)
        n = min(x, 4)  # Fill FIFO if there are enough data points.
        self.sm.put(mv[0:n])
        self.arr = ar  # Initial conditions for ISR
        self.apt = n  # Point to next data value
        self.ict = 0  # IRQ count
        self.sm.active(1)

    def busy(self):
        if self.ict is None:
            return False  # Just instantiated
        return self.ict < self.icm

    def cancel(self):
        self.reps = 1
