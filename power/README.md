# A phasor power meter

This measures the AC mains power consumed by a device. Unlike many cheap power
meters it performs a vector measurement and can display true power, VA and
phase. It can also plot snapshots of voltage and current waveforms. It can
calculate average power consumption of devices whose consumption varies with
time such as freezers and washing machines, and will work with devices capable
of sourcing power into the grid. It supports full scale ranges of 30W to 3KW.

[Images of device](./images/IMAGES.md)

###### [Main README](../README.md)

## Warning

This project includes mains voltage wiring. Please don't attempt it unless you
have the necessary skills and experience to do this safely.

# Hardware Overview

The file `SignalConditioner.fzz` includes the schematic and PCB layout for the
device's input circuit. The Fritzing utility required to view and edit this is
available (free) from [here](http://fritzing.org/download/).

The unit includes a transformer with two 6VAC secondaries. One is used to power
the device, the other to measure the line voltage. Current is measured by means
of a current transformer SEN-11005 from SparkFun. The current output from this
is converted to a voltage by means of an op-amp configured as a transconductance
amplifier. This passes through a variable gain amplifier comprising two cascaded
MCP6S91 programmable gain amplifiers, then to a two pole Butterworth low pass
anti-aliasing filter. The resultant signal is presented to one of the Pyboard's
shielded ADC's. The transconductance amplifier also acts as a single pole low
pass filter.

The voltage signal is similarly filtered with three matched poles to ensure
that correct relative phase is maintained. The voltage channel has fixed gain.

## PCB

The PCB and schematic have an error in that the inputs of the half of opamp U4
which handles the current signal are transposed.

# Firmware Overview

## Dependencies

1. The `uasyncio` library.
2. The official lcd160 driver `lcd160cr.py`.

Also from the [lcd160cr GUI library](https://github.com/peterhinch/micropython-lcd160cr-gui.git)
the following files:

1. `lcd160_gui.py`.
2. `font10.py`.
3. `lcd_local.py`
4. `constants.py`
5. `lplot.py`

## Configuration

In my build the above plus `mains.py` are implemented as frozen bytecode. There
is no SD card, the flash filesystem containing `main.py` and `mt.py`.

If `mt.py` is deleted from flash and located on an SD card the code will create
simulated sinewave samples for testing.

## Design

The code has not been optimised for performance, which in my view is adequate
for the application.

The module `mains.py` contains two classes, `Preprocessor` and `Scaling` which
perform the data capture and analysis. The former acquires the data, normalises
it and calculates normalised values of RMS voltage and current along with power
and phase. `Scaling` controls the PGA according to the selected range and
modifies the Vrms, Irms and P values to be in conventional units.

The `Scaling` instance created in `mt.py` has a continuously running coroutine
(`._run()`) which reads a set of samples, processes them, and executes a
callback. Note that the callback function is changed at runtime by the GUI code
(by `mains_device.set_callback()`). The iteration rate of `._run()` is about
1Hz.

The code is intended to offer a degree of noise immunity, in particular in the
detection of voltage zero crossings. It operates by acquiring a set of 400
sample pairs (voltage and current) as fast as standard MicroPython can achieve.
On the Pyboard with 50Hz mains this captures two full cycles, so guaranteeing
two positive going voltage zero crossings. The code uses an averaging algorithm
to detect these (`Preprocessor.analyse()`) and populates four arrays of floats
with precisely one complete cycle of data. The arrays comprise two pairs of
current and voltage values, one scaled for plotting and the other scaled for
measurement.

Both pairs are scaled to a range of +-1.0 with any DC bias removed (owing to
the presence of transformers this can only arise due to offsets in the
circuitry and/or ADC's). DC removal facilitates long term integration.

Plot data is further normalised so that current values exactly fill the +-1.0
range. In other words plots are scaled so that the current waveform fills the
Y axis with the X axis containing one full cycle. The voltage plot is made 10%
smaller to avoid the visually confusing situation with a resistive load where
the two plots coincide exactly.

## Calibration

This is defined by `Scaling.vscale` and `Scaling.iscale`. These values were
initially calculated, then adjusted by comparing voltage and current readings
with measurements from a calibrated meter. Voltage calibration in particular
will probably need adjusting depending on the transformer characteristics.
