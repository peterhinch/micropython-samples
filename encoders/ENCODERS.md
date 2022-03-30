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
 inexpensive, usually suffices. See [this Adafruit product](https://www.adafruit.com/product/377).

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
    def __init__(self, pin_x, pin_y, scale=1):
        self.scale = scale
        self.forward = True
        self.pin_x = pin_x
        self.pin_y = pin_y
        self._pos = 0
        try:
            self.x_interrupt = pin_x.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.x_callback, hard=True)
            self.y_interrupt = pin_y.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.y_callback, hard=True)
        except TypeError:
            self.x_interrupt = pin_x.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.x_callback)
            self.y_interrupt = pin_y.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.y_callback)

    def x_callback(self, pin):
        self.forward = pin() ^ self.pin_y()
        self._pos += 1 if self.forward else -1

    def y_callback(self, pin):
        self.forward = self.pin_x() ^ pin() ^ 1
        self._pos += 1 if self.forward else -1

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
matching an edge. An arbitrarily long sequence of pulses on one line is the
result; the frequency may be arbitrarily high. A correct algorithm must be
able to cope with this: the outcome will be one digit of jitter in the output
count but no systematic drift.

Contrary to common opinion a state table is not necessary to produce a correct
algorithm: see the above sample for an example.

# Problem 3: Synchronisation

Decoders of all types including hardware implementations can fail if edges
on one line occur at too high a rate: transitions can be missed leading to a
gradual drift of measured count compared to actual position. The only solution
to this is to limit the rate by pre-synchronising the digital signals to a
clock.

For mechanical encoders there can also be an issue with invalid logic levels
caused by contact bounce: conditioning with a CR networks and a Schmitt trigger
should be considered.

For bit-perfect results a single level of clock synchronisation is inadequate
because of metastability. Typically two levels are used. See
[this Wikipedia article](url=https://en.wikipedia.org/wiki/Incremental_encoder#Clock_synchronization).

The clock rate of a synchroniser for a software decoder must be chosen with
regard to the worst-case latency of the host. The clock rate will then
determine the maximum permissible rotation speed of the encoder.

In practice bit-perfect results are often not required and simple software
solutions are fine. In particular encoders used for user controls normally have
some form of user feedback. The occasional missed pulse caused by fast contact
bounce will not be noticed.

Where bit-perfect results are required the simplest approach is to use a target
which supports hardware decoding and which pre-synchronises the signals. STM32
meets these criteria.

In a careful test of a software decoder on a Pyboard 1.1 with an optical
encoder pulses were occasionally missed. This suggests that on rare occasions
pulses can arrive too fast for even hard IRQ's to keep track.

# Problem 4: Concurrency

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
 3. `encoder_rp2.py` Version specific to Raspberry Pico RP2 chip. This uses the
 PIO and Viper code to achieve fast response - upto ~10K transitions/s.
 4. `encoder.py` An old Pyboard-specific version.

These were written for encoders producing logic outputs. For switches, adapt
the pull definition to provide a pull up or pull down as required, or provide
physical resistors. This is my preferred solution as the internal resistors on
most platforms have a rather high value.
