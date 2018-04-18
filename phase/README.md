# 1. Introduction

The principal purpose of this application note is to describe a technique for
measuring the relative phase of a pair of sinsusoidal signals over the full
range of 2π radians (360°). This is known as quadrature detection; while
ancient history to radio engineers the method may be unfamiliar to those from
a programming background.

## 1.1 Measurement of relative timing and phase of analog signals

As of 11th April 2018 the Pyboard firmware has been enhanced to enable multiple
ADC channels to be read in response to a timer tick. At each tick a reading is
taken from each ADC in quick succession. This enables the relative timing or
phase of signals to be measured. This is facilitated by the static method
`ADC.read_timed_multi` which is documented
[here](http://docs.micropython.org/en/latest/pyboard/library/pyb.ADC.html).

The ability to perform such measurements substantially increases the potential
application areas of the Pyboard, supporting precision measurements of signals
into the ultrasonic range. Applications such as ultrasonic rangefinders may be
practicable. With two or more microphones it may be feasible to produce an
ultrasonic active sonar capable of providing directional and distance
information for multiple targets.

I have used it to build an electrical network analyser which yields accurate
gain and phase (+-3°) plots of signals up to 40KHz.

# 2 Applications

## 2.1 Measurements of relative timing

In practice `ADC.read_timed_multi` reads each ADC in turn. This implies a delay
between each reading. This was estimated at 1.8μs on a Pyboard V1.1. This value
can be used to compensate any readings taken.

## 2.2 Phase measurements

### 2.2.1 The quadrature detector

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

Where the frequency is known the filtering may be achieved simply by averaging
over an integer number of cycles.

For the above to produce accurate phase measurements the amplitudes of the two
signals must be normalised to 1. Alternatively the amplitudes may be measured
and the DC phase value divided by their product.

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

For small angles (i.e. at lower frequencies) this approximates to

α ~= λ(1 - jθ)

### 2.2.2 A MicroPython implementation

The example below, taken from an application, uses quadrature detection to
accurately measure the phase difference between an outgoing sinewave produced
by `DAC.write_timed` and an incoming response signal. For application reasons
`DAC.write_timed` runs continuously. Its output feeds one ADC and the incoming
signal feeds another. The ADC's are fed from matched hardware anti-aliasing
filters; the matched characteristic ensures that any phase shift in the filters
cancels out.

Because the frequency is known the ADC sampling rate is chosen so that an
integer number of cycles are captured. Thus averaging is used to remove the
double frequency component.

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
    # Apply phase compensation measured at 1.8μs
    theta = 2 * pi * freq * 1.8e-6
    c *= cos(theta) - 1j * sin(theta)
    return cmath.phase(c)
```
