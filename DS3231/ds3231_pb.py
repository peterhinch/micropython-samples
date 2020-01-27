# Pyboard driver for DS3231 precison real time clock.
# Adapted from WiPy driver at https://github.com/scudderfish/uDS3231
# Includes routine to calibrate the Pyboard's RTC from the DS3231
# precison of calibration further improved by timing Pyboard RTC transition
# Adapted by Peter Hinch, Jan 2016, Jan 2020 for Pyboard D

# Pyboard D rtc.datetime()[7] counts microseconds. See end of page on
# https://pybd.io/hw/pybd_sfxw.htm
# Note docs for machine.RTC are wrong for Pyboard. The undocumented datetime
# method seems to be the only way to set the RTC and it follows the same
# convention as the pyb RTC's datetime method.

import utime
import machine
import os

d_series = os.uname().machine.split(' ')[0][:4] == 'PYBD'
if d_series:
    machine.Pin.board.EN_3V3.value(1)

DS3231_I2C_ADDR = 104

class DS3231Exception(OSError):
    pass

rtc = machine.RTC()

def get_ms(s):  # Pyboard 1.x datetime to ms. Caller handles rollover.
    return (1000 * (255 - s[7]) >> 8) + s[6] * 1000 + s[5] * 60_000 + s[4] * 3_600_000

def get_us(s):  # For Pyboard D: convert datetime to μs. Caller handles rollover
    return s[7] + s[6] * 1_000_000 + s[5] * 60_000_000 + s[4] * 3_600_000_000

def bcd2dec(bcd):
    return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))

def dec2bcd(dec):
    tens, units = divmod(dec, 10)
    return (tens << 4) + units

def tobytes(num):
    return num.to_bytes(1, 'little')

class DS3231:
    def __init__(self, i2c):
        self.ds3231 = i2c
        self.timebuf = bytearray(7)
        if DS3231_I2C_ADDR not in self.ds3231.scan():
            raise DS3231Exception("DS3231 not found on I2C bus at %d" % DS3231_I2C_ADDR)

    def get_time(self, set_rtc=False):
        if set_rtc:
            self.await_transition()  # For accuracy set RTC immediately after a seconds transition
        else:
            self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.timebuf) # don't wait
        return self.convert(set_rtc)

    def convert(self, set_rtc=False):
        data = self.timebuf
        ss = bcd2dec(data[0])
        mm = bcd2dec(data[1])
        if data[2] & 0x40:
            hh = bcd2dec(data[2] & 0x1f)
            if data[2] & 0x20:
                hh += 12
        else:
            hh = bcd2dec(data[2])
        wday = data[3]
        DD = bcd2dec(data[4])
        MM = bcd2dec(data[5] & 0x1f)
        YY = bcd2dec(data[6])
        if data[5] & 0x80:
            YY += 2000
        else:
            YY += 1900
        if set_rtc:
            rtc.datetime((YY, MM, DD, wday, hh, mm, ss, 0))
        return (YY, MM, DD, hh, mm, ss, wday -1, 0) # Time from DS3231 in time.time() format (less yday)

    def save_time(self):
        (YY, MM, mday, hh, mm, ss, wday, yday) = utime.localtime()  # Based on RTC
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 0, tobytes(dec2bcd(ss)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 1, tobytes(dec2bcd(mm)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 2, tobytes(dec2bcd(hh)))  # Sets to 24hr mode
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 3, tobytes(dec2bcd(wday + 1)))  # 1 == Monday, 7 == Sunday
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 4, tobytes(dec2bcd(mday)))  # Day of month
        if YY >= 2000:
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 5, tobytes(dec2bcd(MM) | 0b10000000))  # Century bit
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 6, tobytes(dec2bcd(YY-2000)))
        else:
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 5, tobytes(dec2bcd(MM)))
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 6, tobytes(dec2bcd(YY-1900)))

    def await_transition(self):  # Wait until DS3231 seconds value changes
        self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.timebuf)
        ss = self.timebuf[0]
        while ss == self.timebuf[0]:
            self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.timebuf)
        return self.timebuf

# Get calibration factor for Pyboard RTC. Note that the DS3231 doesn't have millisecond resolution so we
# wait for a seconds transition to emulate it.
# This function returns the required calibration factor for the RTC (approximately the no. of ppm the
# RTC lags the DS3231).
# Delay(min) Outcome (successive runs). Note 1min/yr ~= 2ppm
#   5 173 169 173 173 173
#  10 171 173 171
#  20 172 172 174
#  40 173 172 173 Mean: 172.3 
# Note calibration factor is not saved on power down unless an RTC backup battery is used. An option is
# to store the calibration factor on disk and issue rtc.calibration(factor) on boot.

    def getcal(self, minutes=5, cal=0, verbose=True):
        if d_series:
            return self._getcal_d(minutes, cal, verbose)
        verbose and print('Pyboard 1.x. Waiting {} minutes for calibration factor.'.format(minutes))
        rtc.calibration(cal)  # Clear existing cal
        self.save_time()  # Set DS3231 from RTC
        self.await_transition()  # Wait for DS3231 to change: on a 1 second boundary
        tus = utime.ticks_us()
        st = rtc.datetime()[7]
        while rtc.datetime()[7] == st:  # Wait for RTC to change
            pass
        t1 = utime.ticks_diff(utime.ticks_us(), tus)  # t1 is duration (μs) between DS and RTC change (start)
        rtcstart = get_ms(rtc.datetime())  # RTC start time in mS
        dsstart = utime.mktime(self.convert())  # DS start time in secs as recorded by await_transition

        utime.sleep(minutes * 60)

        self.await_transition()  # DS second boundary
        tus = utime.ticks_us()
        st = rtc.datetime()[7]
        while rtc.datetime()[7] == st:
            pass
        t2 = utime.ticks_diff(utime.ticks_us(), tus)  # t2 is duration (μs) between DS and RTC change (end)
        rtcend = get_ms(rtc.datetime())
        dsend = utime.mktime(self.convert())
        dsdelta = (dsend - dsstart) * 1000000  # Duration (μs) between DS edges as measured by DS3231
        if rtcend < rtcstart:  # It's run past midnight. Assumption: run time < 1 day!
            rtcend += 24 * 3_600_000
        rtcdelta = (rtcend - rtcstart) * 1000 + t1 - t2  # Duration (μs) between DS edges as measured by RTC and corrected
        ppm = (1000000* (rtcdelta - dsdelta))/dsdelta
        if cal:
            verbose and print('Error {:4.1f}ppm {:4.1f}mins/year.'.format(ppm, ppm * 1.903))
            return 0
        cal = int(-ppm / 0.954)
        verbose and print('Error {:4.1f}ppm {:4.1f}mins/year. Cal factor {}'.format(ppm, ppm * 1.903, cal))
        return cal

    # Version for Pyboard D. This has μs resolution.
    def _getcal_d(self, minutes, cal, verbose):
        verbose and print('Pyboard D. Waiting {} minutes for calibration factor.'.format(minutes))
        rtc.calibration(cal)  # Clear existing cal
        self.save_time()  # Set DS3231 from RTC
        self.await_transition()  # Wait for DS3231 to change: on a 1 second boundary
        t = rtc.datetime()  # Get RTC time
        # Time of DS3231 transition measured by RTC in μs since start of day
        rtc_start_us = get_us(t)
        dsstart = utime.mktime(self.convert())  # DS start time in secs

        utime.sleep(minutes * 60)

        self.await_transition()  # Wait for DS second boundary
        t = rtc.datetime()
        # Time of DS3231 transition measured by RTC in μs since start of day
        rtc_end_us = get_us(t)
        dsend = utime.mktime(self.convert()) # DS end time in secs
        if rtc_end_us < rtc_start_us:  # It's run past midnight. Assumption: run time < 1 day!
            rtc_end_us += 24 * 3_600_000_000

        dsdelta = (dsend - dsstart) * 1_000_000   # Duration (μs) between DS3231 edges as measured by DS3231
        rtcdelta = rtc_end_us - rtc_start_us  # Duration (μs) between DS edges as measured by RTC
        ppm = (1_000_000 * (rtcdelta - dsdelta)) / dsdelta
        if cal:  # We've already calibrated. Just report results.
            verbose and print('Error {:4.1f}ppm {:4.1f}mins/year.'.format(ppm, ppm * 1.903))
            return 0
        cal = int(-ppm / 0.954)
        verbose and print('Error {:4.1f}ppm {:4.1f}mins/year. Cal factor {}'.format(ppm, ppm * 1.903, cal))
        return cal

    def calibrate(self, minutes=5):
        cal = self.getcal(minutes)
        rtc.calibration(cal)
        print('Pyboard RTC is calibrated. Factor is {}.'.format(cal))
        return cal
