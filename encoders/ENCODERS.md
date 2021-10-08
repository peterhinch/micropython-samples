# Incremental encoders

There are three technologies that I am aware of:
 1. Optical.
 2. Magnetic.
 3. Mechanical (using switch contacts).

All produce quadrature signals looking like this:
![Image](./quadrature.jpg)
consequently the same code may be used regardless of encoder type.

They have two primary applications:
 1. Shaft position and speed measurements on machines.
 2. Control knobs for user input. For user input a mechanical device, being
 inexpensive, usually suffices.
 ![image](https://user-images.githubusercontent.com/70886343/100070110-34979280-2e42-11eb-95c3-d9f93ccd2d2d.png)
 ![image](https://user-images.githubusercontent.com/70886343/136481028-a9066ee9-d531-4393-8799-ae64ae83eddf.png)

In applications such as NC machines longevity and reliability are paramount:
this normally rules out mechanical devices. Rotational speed is also likely to
be too high. In machine tools it is vital to maintain perfect accuracy over
very long periods. This may impact the electronic design of the interface
between the encoder and the host. High precision comes at no cost in code, but
there may be issues in devices with high interrupt latency such as ESP32,
especially with SPIRAM.

The ideal host, especially for precison applications, is a Pyboard. This is
because Pyboard timers can decode in hardware, as shown
[in this script](https://github.com/dhylands/upy-examples/blob/master/encoder.py)
from Dave Hylands. Hardware decoding eliminates all concerns over interrupt
latency or input pulse rates.

# Basic encoder script

This comes from `encoder_portable.py` in this repo. It uses the simplest and
fastest algorithm I know. It should run on any MicrPython platform, but please
read the following notes as there are potential issues.

```python
from machine import Pin

class Encoder:
    def __init__(self, pin_a, pin_b, scale=1):
        self.scale = scale
        self.pin_a = pin_a
        self.pin_b = pin_b
        self._pos = 0
        try:
            pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.a_callback, hard=True)
            pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.b_callback, hard=True)
        except TypeError:
            pin_a.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.a_callback)
            pin_b.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.b_callback)

    def a_callback(self, pin):
        self._pos += 1 if (pin() ^ self.pin_b()) else -1

    def b_callback(self, pin):
        self._pos += 1 if (self.pin_a() ^ pin() ^ 1) else -1

    def position(self, value=None):
        if value is not None:
            self._pos = round(value / self.scale)
        return self._pos * self.scale
```
If the direction is incorrect, transpose the X and Y pins in the constructor
call.

# Problem 1: Interrupt latency

By default, pin interrupts defined using the `machine` module are soft. This
introduces latency if a line changes state when a garbage collection is in
progress. The above script attempts to use hard IRQ's, but not all platforms
support them (notably ESP8266 and ESP32).

Hard IRQ's present their own issues documented
[here](https://docs.micropython.org/en/latest/reference/isr_rules.html) but
the above script conforms with these rules.

# Problem 2: Jitter

The picture above is idealised. In practice it is possible to receive a
succession of edges on one input line, with no transitions on the other. On
mechanical encoders this may be caused by
[contact bounce](http://www.ganssle.com/debouncing.htm). On any type it can
result from vibration, where the encoder happens to stop at an angle exactly
matching an edge. Code must be designed to accommodate this. The above sample
does this. It is possible that the above latency issue may cause pulses to be
missed, notably on platforms which don't support hard IRQ's. In such cases
hardware may need to be adapted to limit the rate at which signals can change,
possibly with a CR low pass filter and a schmitt trigger. This clearly won't
work if the pulse rate from actual shaft rotation exceeds this limit.

In a careful test on a Pyboard 1.1 with an optical encoder pulses were
occasionally missed. My guess is that, on rare occasions, pulses can arrive too
fast for even hard IRQ's to keep track. For machine tool applications, the
conclusion would seem to be that hardware decoding or possibly a rate limiting
circuit is required.

# Problem 3: Concurrency

The presented code samples use interrupts in order to handle the potentially
high rate at which transitions can occur. The above script maintains a
position value `._pos` which can be queried at any time. This does not present
concurrency issues. However some applications, notably in user interface
designs, may require an encoder action to trigger complex behaviour. The
obvious solution would be to adapt the script to do this by having the two ISR
methods call a function. However the function would run in an interrupt context
which (even with soft IRQ's) presents concurrency issues where an application's
data can change at any point in the application's execution. Further, a complex
function would cause the ISR to block for a long period with the potential for
data loss.

A solution to this is an interface between the ISR's and `uasyncio` whereby the
ISR's set a `ThreadSafeFlag`. This is awaited by a `uasyncio` `Task` which runs
a user supplied callback. The latter runs in a `uasyncio` context: the state of
any `Task` can only change at times when it has yielded to the scheduler in
accordance with `uasyncio` rules. This is implemented in
[this asynchronous driver](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/DRIVERS.md#6-quadrature-encoders).
This also handles the case where a mechanical encoder has a large number of
states per revolution. The driver has the option to divide these down, reducing
the rate at which callbacks occur.

# Code samples

 1. `encoder_portable.py` Suitable for most purposes.
 2. `encoder_timed.py` Provides rate information by timing successive edges. In
 practice this is likely to need filtering to reduce jitter caused by
 imperfections in the encoder geometry. With a mechanical knob turned by an
 anthropoid ape it's debatable whether it produces anything useful :)
 3. `encoder.py` An old Pyboard-specific version.
 4. `encoder_state.py` Interrupt based quadrature incremental encoder.
 Allows to select the clock multiplier as x1, x2 or x4.
 It uses encoder state transitions and rejects contact bounces - jitters.
 The Encoder.value() is much more accurate.
 Perfect work on ESP32 board, a deviation is 0 or ±1 or ±2 per revolution.
 5. `encoders_test.py` Try to test the above encoders.
 Needs to be tested on other MicroPython boards.

These were written for encoders producing logic outputs. For switches, adapt
the pull definition to provide a pull up or pull down as required, or provide
physical resistors. This is my preferred solution as the internal resistors on
most platforms have a rather high value.
