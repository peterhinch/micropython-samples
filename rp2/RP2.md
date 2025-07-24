# Code samples for RP2040 and RP2350 (Pico and Pico 2)

These are intended to demonstrate the use of Pico-specific hardware.

1. [Nonblocking SPI master](./RP2.md#1-nonblocking-spi-master) High speed bulk data output.  
 1.1 [Class RP2_SPI_DMA_MASTER](./RP2.md#11-rp2_spi_dma_master)  
 1.2 [Constructor](./RP2.md#12-constructor)  
 1.3 [Methods](./RP2.md#13-methods)  
 1.4 [CS](./RP2.md#14-cs) How to control the CS/ pin.  
2. [Nonblocking SPI slave](./RP2.md#2-nonblocking-spi-slave) High speed bulk data input.  
 2.1 [Introduction](./RP2.md#21-introduction)  
 2.2 [SpiSlave class](./RP2.md#22-spislave-class)  
 2.3 [Constructor](./RP2.md#23-constructor)  
 2.4 [Synchronous Interface](./RP2.md#24-synchronous-interface)  
 2.5 [Asynchronous Interface](./RP2.md#25-asynchronous-interface)  
 2.6 [operation](./RP2.md#26-operation)  
3. [Pulse Measurement](./RP2.md#3-pulse-Measurement) Measure incoming pulses.  
4. [Pulse train output](./RP2.md#4-pulse-train-output) Output arbitrary pulse trains as per ESP32 RMT.  
 4.1 [The RP2_RMT class](./RP2.md#41-the-rp2_rmt-class)  
 4.2 [Constructor](./RP2.md#42-constructor)  
 4.3 [Methods](./RP2.md#43-methods)  
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;4.3.1 [send](./RP2.md#431-send)  
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;4.3.2 [busy](./RP2.md#432-busy)  
 4.4 [Design](./RP2.md#44-design)  
 4.5 [Limitations](./RP2.md#45-limitations)  

# 1. Nonblocking SPI master

The module `spi_master` provides a class `RP2_SPI_DMA_MASTER` which uses DMA to
perform fast SPI output. A typical use case is to transfer the contents of a
frame buffer to a display as a background task. The following files are provided
in the `spi` directory:
* `spi_master.py` The main module.
* `master_test.py` Test script - requires a scope or LA to check SPI output.
* `master_slave_test.py` Full test of master linked to slave, with the latter
printing results.

This module supports the most common SPI case, being the `machine.SPI` default:
polarity=0, phase=0, bits=8, firstbit=SPI.MSB. Benefits over the official
`machine.SPI` are the nonblocking write and the fact that baudrates are precise;
those on the official class are highly quantised, with (for example) 20MHz
manifesting as 12MHz. The module has been tested to 30MHz, but higher rates
should be possible.

To run the full test, the following pins should be linked:
* 0-19 MOSI
* 1-18 SCK
* 2-17 CSN

To run a test issue (e.g.):
```py
>>> import spi.master_slave_test
```

## 1.1 Class RP2_SPI_DMA_MASTER

## 1.2 Constructor

This takes the following positional args:
* `sm_num` State machine no. (0..7 on RP2040, 0..11 on RP2350)
* `freq` SPI clock frequency in Hz.
* `sck` A `Pin` instance for `sck`. Pins are arbitrary.
* `mosi` A `Pin` instance for `mosi`.
* `callback` A callback to run when DMA is complete. This is run in a hard IRQ
context. Typical use is to set a `ThreadSafeFlag`. Note that the DMA completes
before transmission ends due to bytes stored in the SM FIFO. This is unlikely to
have practical consequences because of MicroPython latency: in particular
response to a `ThreadSafeFlag` typically takes >200μs.

## 1.3 Methods

* `write(data : bytes)` arg a `bytes` or `bytearray` of data to transmit. Return
is rapid with transmission running in the background. Returns `None`.
* `deinit()` Disables the DMA and the SM. Returns `None`.

## 1.4 CS/

The application should assert CS/ (set to 0) prior to transmission and deassert
it after transmission is complete.

# 2. Nonblocking SPI slave

This module requires incoming data to conform to the most common SPI case, being
the `machine.SPI` default: polarity=0, phase=0, bits=8, firstbit=SPI.MSB.

It has been tested at a clock rate of 24MHz on an RP2040 running at 250MHz.

The following files may be found in the `spi` directory:
* `spi_slave.py` Main module.
* `slave_sync_test` Test using synchronous code.
* `slave_async_test` Test using asynchronous code.
* `master_slave_test.py` Full test of master linked to slave, with the latter
printing results.

Tests operate by using the official SPI library to transmit with the module
receiving (`master_slave_test` uses the nonblocking master). To run the tests
the following pins should be linked:
* 0-19 MOSI
* 1-18 SCK
* 2-17 CSN

Tests are run by issuing (e.g.):
```py
>>> import spi.master_slave_test
```

# 2.1 Introduction

This uses a PIO state machine (SM) with DMA to enable an RP2 to receive SPI
transfers from a host. Reception is non-blocking, enabling code to run while a
transfer is in progress. The principal application area is for fast transfer of
large messages.

# 2.2 SpiSlave class

The class presents synchronous and asynchronous APIs. In use the class is set
up to read data. The master sets `CS/` low, transmits data, then sets `CS/`
high, terminating the transfer.

## 2.3 Constructor

This takes the following positional args:
* `buf=None` Optional `bytearray` for incoming data. This is required if using
the asynchronous iterator interface, otherwise it is unused.
* `callback=None` Optional callback for use with the synchronous API. It takes
a single arg, being the number of bytes received.
* `sm_num=0` State machine number.

Keyword args: Pin instances, initialised as input. GPIO nos. must be consecutive
starting from `mosi`.
* `mosi` Pin for MOSI.
* `sck` SCK Pin.
* `csn` CSN Pin.

# 2.4 Synchronous Interface

This is via `SpiSlave.read_into(buffer)` where `buffer` is a user supplied
`bytearray`. This must be large enough for the expected message. The method
returns immediately. When a message arrives and reception is complete, the
callback runs. Its integer arg is the number of bytes received.

If a message is too long to fit the buffer, when the buffer fills, subsequent
characters are lost.

# 2.5 Asynchronous Interface

There are two ways to use this. The simplest uses a single buffer passed to the
constructor. This should be sized to accommodate the longest expected message.
Reception is via an asynchronous iterator:
```py
async def receive(piospi):  # Arg is an SpiSlave instantiated with a buffer
    async for msg in piospi:  # msg is a memoryview of the buffer
        print(bytes(msg))
```
This prints incoming messages as they arrive.

An alternative approach enables the use of multiple buffers (for example two
phase "ping pong" buffering). Reception is via an asynchronous method
`SpiSlave.as_read_into(buffer)`:
```py
    rbuf = bytearray(200)
    nbytes = await piospi.as_read_into(rbuf)  # Wait for a message, get no. of received bytes
    print(bytes(rbuf[:nbytes]))
```
As with all asynchronous code, this task pauses while others continue to run.

# 2.6 Operation

The slave will ignore all interface activity until CS/ is driven low. It then
receives data with the end of message identified by a low to high transition on
CS/.

# 3. Pulse Measurement

The file `measure_pulse.py` is a simple demo of using the PIO to measure a pulse
waveform. As written it runs a PWM to provide a signal. To run the demo link
pins GPIO16 and GPIO17. It measures period/frequency and mark (hence space and
mark/space can readily be derived).

As written the native clock rate is used (125MHz on Pico).

# 4. Pulse train output

The `RP2_RMT` class provides functionality similar to that of the ESP32 `RMT`
class. It enables pulse trains to be output using a non-blocking driver. By
default the train occurs once. Alternatively it can repeat a defined number of
times, or can be repeated continuously.

The class was designed for my [IR blaster](https://github.com/peterhinch/micropython_ir)
and [433MHz remote](https://github.com/peterhinch/micropython_remote)
libraries. It supports an optional carrier frequency, where each high pulse can
appear as a burst of a defined carrier frequency. The class can support both
forms concurrently on a pair of pins: one pin produces pulses while a second
produces carrier bursts.

Pulse trains are specified as arrays with each element being a duration in μs.
Arrays may be of integers or half-words depending on the range of times to be
covered. The duration of a "tick" is 1μs by default, but this can be changed.

To run the test issue:
```py
>>> import rmt.rp2_rmt_test
```
Output is on pins 16 and/or 17: see below and test source.

# 4.1 The RP2_RMT class

## 4.2 Constructor

This takes the following args:
 1. `pin_pulse=None` If an output `Pin` instance is provided, pulses will be
 output on it.
 2. `carrier=None` To output a carrier, a 3-tuple should be provided comprising
 `(pin, freq, duty)` where `pin` is an output pin instance, `freq` is the
 carrier frequency in Hz and `duty` is the duty ratio in %.
 3. `sm_no=0` State machine no.
 4. `sm_freq=1_000_000` Clock frequency for SM. Defines the unit for pulse
 durations.

## 4.3 Methods

### 4.3.1 send

This returns "immediately" with a pulse train being emitted as a background
process. Args:
 1. `ar` A zero terminated array of pulse durations in μs. See notes below.
 2. `reps=1` No. of repetions. 0 indicates continuous output.
 3. `check=True` By default ensures that the pulse train ends in the inactive
 state.

In normal operation, between pulse trains, the pulse pin is low and the carrier
is off. A pulse train ends when a 0 pulse width is encountered: this allows
pulse trains to be shorter than the array length, for example where a
pre-allocated array stores pulse trains of varying lengths. In RF transmitter
applications ensuring the carrier is off between pulse trains may be a legal
requirement, so by default the `send` method enforces this.

The first element of the array defines the duration of the first high going
pulse, with the second being the duration of the first `off` period. If there
are an even number of elements prior to the terminating 0, the signal will end
in the `off` state. If the `check` arg is `True`, `.send()` will check for an
odd number of elements; in this case it will overwrite the last element with 0
to enforce a final `off` state.

This check may be skipped by setting `check=False`. This provides a means of
inverting the normal sense of the driver: if the first pulse train has an odd
number of elements and `check=False` the pin will be left high (and the carrier
on). Subsequent normal pulsetrains will start and end in the high state.

### 4.3.2 busy

No args. Returns `True` if a pulse train is being emitted.

### 4.3.3 cancel

No args. If a pulse train is being emitted it will continue to the end but no
further repetitions will take place.

# 4.4 Design

The class constructor installs one of two PIO scripts depending on whether a
`pin_pulse` is specified. If it is, the `pulsetrain` script is loaded which
drives the pin directly from the PIO. If no `pin_pulse` is required, the
`irqtrain` script is loaded. Both scripts cause an IRQ to be raised at times
when a pulse would start or end.

The `send` method loads the transmit FIFO with initial pulse durations and
starts the state machine. The `._cb` ISR keeps the FIFO loaded with data until
a 0 entry is encountered. It also turns the carrier on and off (using a PWM
instance). This means that there is some latency between the pulse and the
carrier. However latencies at start and end are effectively identical, so the
duration of a carrier burst is correct.

# 4.5 Limitations

While the tick interval can be reduced to provide timing precision better than
1μs, the design of this class will not support very high pulse repetition
frequencies. This is because each pulse causes an interrupt: MicroPython is
unable to support high IRQ rates.
[This library](https://github.com/robert-hh/RP2040-Examples/tree/master/pulses)
is more capable in this regard.
