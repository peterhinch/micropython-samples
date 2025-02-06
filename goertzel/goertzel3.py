# Tone detection using Goertzel algorithm.
# Requires Pyboard 1.x with X4 and X5 linked.

from array import array
import math
import cmath
from pyb import ADC, DAC, Pin, Timer
import time
import micropython
import gc
micropython.alloc_emergency_exception_buf(100)

# When searching for a specific signal tone the Goertzel algorithm can be more efficient than fft.
# This routine returns magnitude of a single fft bin, which contains the target frequency.

# Constructor args:
# freq (Hz) Target centre frequency
# nsamples (int) Number of samples
# spc (int) No. of samples per cycle of target frequency: sampling freq = freq * spc
# Filter bandwidth as a proportion of target frequency is spc/nsamples
# so 1KHz with 100 samples and 10 samples per cycle bw = 1KHz * 10/100 = 100Hz

# .calc() computes magnitude of one DFT bin, then fires off a nonblocking acquisition of more data.
# Depending on size of sample set, blocks for a few ms.

class Goertzel:
    def __init__(self, adc, nsamples, freq, spc, verbose=False):
        if verbose:
            print('Freq {}Hz +- {}Hz'.format(freq, freq * spc / (2 * nsamples)))
        self.sampling_freq = freq * spc
        self.buf = array('H', (0 for _ in range(nsamples)))
        self.idx = 0
        self.nsamples = nsamples
        self.adc = adc
        self.scaling_factor = nsamples / 2.0
        omega = 2.0 * math.pi / spc
        self.coeff = 2.0 * math.cos(omega)
        self.fac = -math.cos(omega) + 1j * math.sin(omega)
        self.busy = False
        self.acquire()

    def acquire(self):
        self.busy = True
        self.idx = 0
        self.tim = Timer(6, freq=self.sampling_freq, callback=self.tcb)

    def tcb(self, _):
        buf = self.buf
        buf[self.idx] = self.adc.read()
        self.idx += 1
        if self.idx >= self.nsamples:
            self.tim.deinit()
            self.busy = False

    def calc(self):
        if self.busy:
            return False  # Still acquiring data
        coeff = self.coeff
        buf = self.buf
        q0 = q1 = q2 = 0
        for s in buf:  # Loop over 200 samples takes 3.2ms on Pyboard 1.x
            q0 = coeff * q1 - q2 + s
            q2 = q1
            q1 = q0
        self.acquire()  # Start background acquisition
        return cmath.polar(q1 + q2 * self.fac)[0] / self.scaling_factor

# Create a sinewave on pin X5
def x5_test_signal(amplitude, freq):
    dac = DAC(1, bits=12)  # X5
    buf = array('H', 2048 + int(amplitude * math.sin(2 * math.pi * i / 128)) for i in range(128))
    tim = Timer(2, freq=freq * len(buf))
    dac.write_timed(buf, tim, mode=DAC.CIRCULAR)
    return buf  # Prevent deallocation

def test(amplitude=2047):
    freq = 1000
    buf = x5_test_signal(amplitude, freq)
    adc = ADC(Pin.board.X4)
    g = Goertzel(adc, nsamples=100, freq=freq, spc=10, verbose=True)
    while True:
        time.sleep(0.5)
        print(g.calc())
