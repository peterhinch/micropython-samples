# Measurement of relative timing and phase of fast analog signals

As of 11th April 2018 the Pyboard firmware has been enhanced to enable multiple
ADC channels to be read in a similar way to the existing `read_timed` method.
At each timer tick a reading is taken from each ADC in very quick succession.
This enables the relative timing or phase of relatively fast signals to be
measured.

The ability to perform such measurements substantially increases the potential
application areas of the Pyboard, supporting precision measurements of signals
into the ultrasonic range. Applications such as ultrasonic rangefinders come to
mind. With two or more microphones it may be feasible to produce an ultrasonic
active sonar capable of providing directional and distance information for
multiple targets.

I have used it to build an electrical network analyser which yields accurate
gain and phase plots of signals up to 36KHz.

# 1. Staticmethod ADC.read_timed_multi

The following is based on the documentation changes in the above PR.

Call pattern:  
```python
from pyb import ADC
ok = ADC.read_timed_multi((adcx, adcy, ...), (bufx, bufy, ...), timer)
```

This is a static method. It can be used to extract relative timing or phase
data from multiple ADC's.

It reads analog values from multiple ADCs into buffers at a rate set by the
`timer` object. Each time the timer triggers a sample is rapidly read from each
ADC in turn.

ADC and buffer instances are passed in tuples with each ADC having an
associated buffer. All buffers must be of the same type and length and the
number of buffers must equal the number of ADC's.

Buffers must be `bytearray` or `array.array` instances. The ADC values have
12-bit resolution and are stored directly into the buffer if its element size
is 16 bits or greater.  If buffers have only 8-bit elements (i.e. a bytearray)
then the sample resolution will be reduced to 8 bits.

`timer` must be a Timer object. The timer must already be initialised and
running at the desired sampling frequency.

Example reading 3 ADC's:

```python
    import pyb
    import array
    adc0 = pyb.ADC(pyb.Pin.board.X1)    # Create ADC's
    adc1 = pyb.ADC(pyb.Pin.board.X2)
    adc2 = pyb.ADC(pyb.Pin.board.X3)
    tim = pyb.Timer(8, freq=100)        # Create timer
    rx0 = array.array('H', (0 for i in range(100)))  # ADC buffers of
    rx1 = array.array('H', (0 for i in range(100)))  # 100 16-bit words
    rx2 = array.array('H', (0 for i in range(100)))
        # read analog values into buffers at 100Hz (takes one second)
    pyb.ADC.read_timed_multi((adc0, adc1, adc2), (rx0, rx1, rx2), tim)
    for n in range(len(rx0)):
        print(rx0[n], rx1[n], rx2[n])
```

This function does not allocate any memory. It has blocking behaviour: it does
not return to the calling program until the buffers are full.

The function returns `True` if all samples were acquired with correct timing.
At high sample rates the time taken to acquire a set of samples can exceed the
timer period. In this case the function returns `False`, indicating a loss of
precision in the sample interval. In extreme cases samples may be missed.

The maximum rate depends on factors including the data width and the number of
ADC's being read. In testing two ADC's were sampled at 12 bit precision and at
a timer rate of 210KHz without overrun. At high sample rates disabling
interrupts for the duration can reduce the risk of sporadic data loss.

# 2 Applications

## 2.1 Measurements of relative timing

In practice `ADC.read_timed_multi` reads each ADC in turn. This implies a delay
between each reading. This was measured at 3.236μs on a Pyboard V1.1 and can be
used to compensate any measurements taken.

## 2.2 Phase measurements

### 2.2.1 The phase sensitive detector

The principle of a phase sensitive detector (applicable to linear and sampled
data systems) is based on multiplying the two signals and low pass filtering
the result. This derives from the prosthaphaeresis formula:

sin a sin b = (cos(a-b) - cos(a+b))/2

If  
ω = angular frequency in rad/sec  
t = time  
ϕ = phase  
this can be written:

sin ωt sin(ωt + ϕ) = 0.5(cos(-ϕ) - cos(2ωt + ϕ))  

The first term on the right hand side is a DC component related to the relative
phase of the two signals. The second is an AC component at twice the incoming
frequency. So if the product signal is passed through a low pass filter the
right hand term disappears leaving only 0.5cos(-ϕ).

Where the frequency is known ideal filtering may be achieved simply, by
averaging over an integer number of cycles.

For the above to produce accurate phase measurements the amplitudes of the two
signals must be normalised to 1. Alternatively the amplitudes should be
measured and the resultant DC value divided by their product.

Because cos ϕ = cos -ϕ this can only detect phase angles over a range of π
radians. To achieve detection over the full 2π range a second product detector
is used with one signal phase-shifted by π/2. This allows a complex phasor
(phase vector) to be derived, with one detector providing the real part and the
other the imaginary one.

In a sampled data system where the frequency is known, the phase shifted signal
may be derived by indexing into one of the sample arrays. To achieve this the
signals must be sampled at a rate of 4Nf where f is the frequency and N is an
integer >= 1. In the limiting case where N == 1 the index offset is 1; this
sampling rate is double the Nyquist rate.

In practice phase compensation may be required to allow for a time delay
between sampling the two signals. If the delay is T and the frequency is f, the
phase shift θ is given by

θ = 2πfT

Conventionally phasors rotate anticlockwise for leading phase. A time delay
implies a phase lag i.e. a negative phase or a clockwise rotation. If λ is the
phasor derived above, the adjusted phase α is given by multiplying by a phasor
of unit magnitude and phase -θ:

α = λ(cos θ - jsin θ)

For small angles this approximates to

α ~= λ(1 - jθ)

### 2.2.2 A MicroPython implementation

The example below, taken from an application, uses quadrature detection to
accurately measure the phase difference between an outgoing sinewave produced
by `DAC.write_timed` and an incoming response signal. For application reasons
`DAC.write_timed` runs continuously. Its output feeds one ADC and the incoming
signal feeds another. The ADC's are fed from matched hardware anti-aliasing
filters.

Because the frequency is known the ADC sampling rate is chosen so that an
integer number of cycles are captured. This enables simple averaging to be used
to remove the double frequency component.

The function `demod()` returns the phase difference in radians. The sample
arrays are globals `bufout` and `bufin`. The `freq` arg is the frequency and is
used to provide phase compensation for the delay mentioned in section 2.1.

The arg `nsamples` is the number of samples per cycle of the sinewave. As
described above it can be any integer multiple of 4.

```python
from math import sqrt, pi
import cmath
_ROOT2 = sqrt(2)

 # Return RMS value of a buffer, removing DC.
def amplitude(buf):
    buflen = len(buf)
    meanin = sum(buf)/buflen
    return sqrt(sum((x - meanin)**2 for x in buf)/buflen)

def demod(freq, nsamples):
    sum_norm = 0
    sum_quad = 0  # quadrature pi/2 phase shift
    buflen = len(bufin)
    assert len(bufout) == buflen, 'buffer lengths must match'
    meanout = sum(bufout)/buflen  # ADC samples are DC-shifted
    meanin = sum(bufin)/buflen
    # Remove DC offset, calculate RMS and convert to peak value (sine assumption)
    # Aim: produce sum_norm and sum_quad in range -1 <= v <= +1
    peakout = amplitude(bufout) * _ROOT2
    peakin = amplitude(bufin) * _ROOT2
    # Calculate phase
    delta = int(nsamples // 4)  # offset for pi/2
    for x in range(buflen):
        v0 = (bufout[x] - meanout) / peakout
        v1 = (bufin[x] - meanin) / peakin
        s = (x + delta) % buflen  # + pi/2
        v2 = (bufout[s] - meanout) / peakout
        sum_norm += v0 * v1  # Normal
        sum_quad += v2 * v1  # Quadrature

    sum_norm /= (buflen * 0.5)  # Factor of 0.5 from the trig formula
    sum_quad /= (buflen * 0.5)
    c = sum_norm + 1j * sum_quad  # Create the complex phasor
    # Apply phase compensation measured at 3.236μs
    c *= 1 - 2j * pi * freq * 3.236e-6  # very close approximation
    return cmath.phase(c)
```
