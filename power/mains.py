# mains.py Data collection and processing module for the power meter.

# The MIT License (MIT)
#
# Copyright (c) 2017 Peter Hinch
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from pyb import SPI, Pin, ADC
from array import array
from micropython import const
from math import sin, cos, asin, pi, radians, sqrt
import uasyncio as asyncio
import gc
gc.collect()

# PINOUT
# vadc X19
# iadc X20
# MOSI X8
# MISO X7
# SCK X6
# CSN0 X5  First PGA
# CSN1 X4  Second PGA

# SAMPLING
NSAMPLES = const(400)
def arr_gen(n):
    for _ in range(n):
        yield 0

isamples = array('h', arr_gen(NSAMPLES))
vsamples = array('h', arr_gen(NSAMPLES))
gc.collect()

# HARDWARE
vadc = ADC(Pin.board.X19)
iadc = ADC(Pin.board.X20)

spi = SPI(1)
spi.init(SPI.MASTER, polarity = 0, phase = 0)

# ************* Programmable Gain Amplifier *************

class MCP6S91():
    CHANNEL_ADDR = 0x41
    GAIN_ADDR = 0x40
    GAINVALS = (1, 2, 4, 5, 8, 10, 16, 32)
    PINS = ('X5', 'X4')
    def __init__(self, devno):
        try:
            self.csn = Pin(MCP6S91.PINS[devno], mode = Pin.OUT_PP)
        except IndexError:
            raise ValueError('MCP6S91 device no. must be 0 or 1.')
        self.csn.value(1)
        self.csn.value(0)
        self.csn.value(1)  # Set state machine to known state
        self.gain(1)

    def gain(self, value):
        try:
            gainval = MCP6S91.GAINVALS.index(value)
        except ValueError:
            raise ValueError('MCP6S91 invalid gain {}'.format(value))
        self.csn.value(0)
        spi.send(MCP6S91.GAIN_ADDR)
        spi.send(gainval)
        self.csn.value(1)

# Two cascaded MCP6S91 devices provide gains 1, 2, 5, 10, 20, 50, 100
class PGA():
    gvals = { 1 : (1, 1), 2 : (2, 1), 5 : (5, 1), 10 : (10, 1),
             20 : (10, 2), 50 : (10, 5), 100 : (10, 10) }

    def __init__(self):
        self.amp0 = MCP6S91(0)
        self.amp1 = MCP6S91(1)

    def gain(self, value):
        try:
            g0, g1 = PGA.gvals[value]
        except KeyError:
            raise ValueError('PGA invalid gain {}'.format(value))
        self.amp0.gain(g0)
        self.amp1.gain(g1)

# ************* Data Acquisition *************

# Integer sample data put into vsamples and isamples global arrays.
# Results are in range +-2047

# SIMULATION PARAMETERS
VPEAK = 0.545  # Relative to ADC FSD
IPEAK = 0.6
VPHASE = 0
IPHASE = radians(45)

def sample(simulate=False):
    # Acquire just over 2 full cycles of AC
    if simulate:
        for n in range(NSAMPLES):
            isamples[n] = int(2047 + IPEAK * 2047 * sin(4.2 * pi * n / NSAMPLES + IPHASE))
            vsamples[n] = int(2047 + VPEAK * 2047 * sin(4.2 * pi * n / NSAMPLES + VPHASE))
    else:
        for n in range(NSAMPLES):
            isamples[n] = iadc.read()
            vsamples[n] = vadc.read()
    for n in range(NSAMPLES):  # Normalise to -2047 to +2048
        vsamples[n] -= 2047
        if simulate:
            isamples[n] -= 2047
        else:
            isamples[n] = 2047 - isamples[n]  # Sod's law. That's the way I wired the CT.

# ************* Preprocessing *************

# Filter data. Produce a single cycle of floating point data in two datasets.
# Both are scaled -1.0 to +1.0.
# Plot data is scaled such that the data exactly fits the range.
# Output data is scaled such that DAC FS fits the range.

class Preprocessor():
    arraysize = const(NSAMPLES // 2)  # We acquire > 2 cycles
    plotsize = const(50)
    vplot = array('f', arr_gen(plotsize))  # Plot data
    iplot = array('f', arr_gen(plotsize))
    vscale = array('f', arr_gen(arraysize))  # Output data
    iscale = array('f', arr_gen(arraysize))
    def __init__(self, simulate, verbose):
        self.avg_len = 4
        self.avg_half = self.avg_len // 2
        gc.collect()
        self.simulate = simulate
        self.verbose = verbose
        self.overrange = False
        self.threshold = 1997

    def vprint(self, *args):
        if self.verbose:
            print(*args)

    async def run(self):
        self.overrange = False
        sample(self.simulate)
        return await self.analyse()

    # Calculate average of avg_len + 1 numbers around a centre value. avg_len must be divisible by 2.
    # This guarantees symmetry around the centre index.
    def avg(self, arr, centre):
        return sum(arr[centre - self.avg_half : centre + 1 + self.avg_half]) / (self.avg_len + 1)

    # Filter a set of samples around a centre index in an array
    def filt(self, arr, centre):
        avg0 = self.avg(arr, centre - self.avg_half)
        avg1 = self.avg(arr, centre + self.avg_half)
        return avg0, avg1

    async def analyse(self):
        # Determine the first and second rising edge of voltage
        self.overrange = False
        nfirst = -1  # Index of 1st upward voltage transition
        lastv = 0  # previous max
        ovr = self.threshold  # Overrange threshold
        for n in range(self.avg_len, NSAMPLES - self.avg_len + 1):
            vavg0, vavg1 = self.filt(vsamples, n)
            iavg0, iavg1 = self.filt(isamples, n)
            vmax = max(vavg0, vavg1)
            vmin = min(vavg0, vavg1)
            imax = max(iavg0, iavg1)
            imin = min(iavg0, iavg1)
            if vmax > ovr or vmin < -ovr or imax > ovr or imin < -ovr:
                self.overrange = True
                self.vprint('overrange', vmax, vmin, imax, imin)
            if nfirst == -1:
                if vavg0 < 0 and vavg1 > 0 and abs(vmin) < lastv:
                    nfirst = n if err > abs(abs(vmin) - lastv) else n - 1
                    irising = iavg0 < iavg1  # Save current rising state for phase calculation
            elif n > nfirst + NSAMPLES // 6:
                if vavg0 < 0 and vavg1 > 0 and abs(vmin) < lastv:
                    nsecond = n if err > abs(abs(vmin) - lastv) else n - 1
                    break
            lastv = vmax
            err = abs(abs(vmin) - lastv)
            yield
        else:  # Should never occur because voltage should be present.
            raise OSError('Failed to find a complete cycle.')
        self.vprint(nfirst, nsecond, vsamples[nfirst], vsamples[nsecond], isamples[nfirst], isamples[nsecond])

        # Produce datasets for a single cycle of V.
        # Scale ADC FSD [-FSD 0 FSD] -> [-1.0 0 +1.0]
        nelems = nsecond - nfirst + 1  # No. of samples in current cycle
        p = 0
        for n in range(nfirst, nsecond + 1):
            self.vscale[p] = vsamples[n] / 2047
            self.iscale[p] = isamples[n] / 2047
            p += 1

        # Remove DC offsets
        sumv = 0.0
        sumi = 0.0
        for p in range(nelems):
            sumv += self.vscale[p]
            sumi += self.iscale[p]
        meanv = sumv / nelems
        meani = sumi / nelems
        maxv = 0.0
        maxi = 0.0
        yield
        for p in range(nelems):
            self.vscale[p] -= meanv
            self.iscale[p] -= meani
            maxv = max(maxv, abs(self.vscale[p]))  # Scaling for plot
            maxi = max(maxi, abs(self.iscale[p]))
        yield
        # Produce plot datasets. vplot scaled to avoid exact overlay of iplot
        maxv = max(maxv * 1.1, 0.01)  # Cope with "no signal" conditions
        maxi = max(maxi, 0.01)
        offs = 0
        delta = nelems / (self.plotsize -1)
        for p in range(self.plotsize):
            idx = min(round(offs), nelems -1)
            self.vplot[p] = self.vscale[idx] / maxv
            self.iplot[p] = self.iscale[idx] / maxi
            offs += delta

        if self.verbose:
            for p in range(nelems):
                print('{:7.3f} {:7.3f} {:7.3f} {:7.3f}'.format(
                    self.vscale[p], self.iscale[p],
                    self.vplot[round(p / delta)], self.iplot[round(p / delta)]))

        phase = asin(self.iplot[0]) if irising else pi - asin(self.iplot[0])
        yield
        # calculate power, vrms, irms etc prior to scaling
        us_vrms = 0
        us_pwr = 0
        us_irms = 0
        for p in range(nelems):
            us_vrms += self.vscale[p] * self.vscale[p]  # More noise-immune than calcuating from vmax * sqrt(2)
            us_irms += self.iscale[p] * self.iscale[p]
            us_pwr += self.iscale[p] * self.vscale[p]
        us_vrms = sqrt(us_vrms / nelems)
        us_irms = sqrt(us_irms / nelems)
        us_pwr /= nelems
        return phase, us_vrms, us_irms, us_pwr, nelems

# Testing. Current provided to CT by 100ohm in series with secondary. Vsec = 7.8Vrms so i = 78mArms == 18W at 230Vrms.
# Calculated current scaling:
# FSD 3.3Vpp out = 1.167Vrms.
# Secondary current Isec = 1.167/180ohm = 6.5mArms.
# Ratio = 2000. Primary current = 12.96Arms.
# At FSD iscale is +-1 = 0.707rms
# Imeasured = us_irms * 12.96/(0.707  * self.pga_gain) = us_irms * 18.331 / self.pga_gain

# Voltage scaling. Measured ADC I/P = 1.8Vpp == 0.545fsd pp == 0.386fsd rms
# so vscale = 230/0.386 = 596

class Scaling():
    # FS Watts to PGA gain
    valid_gains = (3000, 1500, 600, 300, 150, 60, 30)
    vscale = 679  # These were re-measured with the new build. Zero load.
    iscale = 18.0  # Based on measurement with 2.5KW resistive load (kettle)

    def __init__(self, simulate=False, verbose=False):
        self.cb = None
        self.preprocessor = Preprocessor(simulate, verbose)
        self.pga = PGA()
        self.set_range(3000)
        loop = asyncio.get_event_loop()
        loop.create_task(self._run())

    async def _run(self):
        while True:
            if self.cb is not None:
                phase, us_vrms, us_irms, us_pwr, nelems = await self.preprocessor.run()  # Get unscaled values. Takes 360ms.
                if self.cb is not None:  # May have changed during await
                    vrms = us_vrms * self.vscale
                    irms = us_irms * self.iscale / self.pga_gain
                    pwr = us_pwr * self.iscale * self.vscale / self.pga_gain
                    self.cb(phase, vrms, irms, pwr, nelems, self.preprocessor.overrange)
            yield

    def set_callback(self, cb=None):
        self.cb = cb  # Set to None to pause acquisition

    def set_range(self, val):
        if val in self.valid_gains:
            self.pga_gain = 3000 // val
            self.pga.gain(self.pga_gain)
        else:
            raise ValueError('Invalid range. Valid ranges (W) {}'.format(self.valid_gains))

    @property
    def vplot(self):
        return self.preprocessor.vplot

    @property
    def iplot(self):
        return self.preprocessor.iplot

def test():
    def cb(phase, vrms, irms, pwr, nelems, ovr):
        print('Phase {:5.1f}rad {:5.0f}Vrms {:6.3f}Arms {:6.1f}W Nsamples = {:3d}'.format(phase, vrms, irms, pwr, nelems))
        if ovr:
            print('Overrange')
    s = Scaling(True, True)
    s.set_range(300)
    s.set_callback(cb)
    loop = asyncio.get_event_loop()
    loop.run_forever()
