# Pyboard driver for DS3231 precison real time clock.
# Adapted from WiPy driver at https://github.com/scudderfish/uDS3231
# Includes routine to calibrate the Pyboard's RTC from the DS3231
# Adapted by Peter Hinch, Jan 2016

import utime, pyb
DS3231_I2C_ADDR = 104

class DS3231Exception(OSError):
    pass

rtc = pyb.RTC()

def now():  # Return the current time from the RTC in secs and millisecs from year 2000
    secs = utime.time()
    ms = 1000 * (255 -rtc.datetime()[7]) >> 8
    if ms < 50:                                 # Might have just rolled over
        secs = utime.time()
    return secs, ms

# Driver for DS3231 accurate RTC module (+- 1 min/yr) needs adapting for Pyboard
# source https://github.com/scudderfish/uDS3231
def bcd2dec(bcd):
    return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))

def dec2bcd(dec):
    t = dec // 10
    o = dec - t * 10
    return (t << 4) + o

class DS3231:
    def __init__(self, side = 'X'):
        side = side.lower()
        if side == 'x':
            bus = 1
        elif side == 'y':
            bus = 2
        else:
            raise ValueError('Side must be "X" or "Y"')
        self.ds3231 = pyb.I2C(bus, mode=pyb.I2C.MASTER, baudrate=400000)
        if DS3231_I2C_ADDR not in self.ds3231.scan():
            raise DS3231Exception("DS3231 not found on I2C bus at %d" % DS3231_I2C_ADDR)

    def get_time(self, set_rtc = False):
        if set_rtc:
            data = self.await_transition() # For accuracy set RTC immediately after a seconds transition
        else:
            data = self.ds3231.mem_read(7, DS3231_I2C_ADDR, 0) # don't wait
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
        (YY, MM, DD, wday, hh, mm, ss, subsecs) = rtc.datetime()
        self.ds3231.mem_write(dec2bcd(ss), DS3231_I2C_ADDR, 0)
        self.ds3231.mem_write(dec2bcd(mm), DS3231_I2C_ADDR, 1)
        self.ds3231.mem_write(dec2bcd(hh), DS3231_I2C_ADDR, 2)      # Sets to 24hr mode
        self.ds3231.mem_write(dec2bcd(wday), DS3231_I2C_ADDR, 3)    # 1 == Monday, 7 == Sunday
        self.ds3231.mem_write(dec2bcd(DD), DS3231_I2C_ADDR, 4)
        if YY >= 2000:
            self.ds3231.mem_write(dec2bcd(MM) | 0b10000000, DS3231_I2C_ADDR, 5)
            self.ds3231.mem_write(dec2bcd(YY-2000), DS3231_I2C_ADDR, 6)
        else:
            self.ds3231.mem_write(dec2bcd(MM), DS3231_I2C_ADDR, 5)
            self.ds3231.mem_write(dec2bcd(YY-1900), DS3231_I2C_ADDR, 6)

    def delta(self):
        return utime.time() - utime.mktime(self.get_time())         # No. of secs RTC leads DS3231

    def await_transition(self):
        data = self.ds3231.mem_read(7, DS3231_I2C_ADDR, 0)
        ss = data[0]
        while ss == data[0]:
            data = self.ds3231.mem_read(7, DS3231_I2C_ADDR, 0)      # Await a seconds transition
        return data

# Get calibration factor for Pyboard RTC. Note that the DS3231 doesn't have millisecond resolution so we
# wait for a seconds transition to emulate it.
# This function returns the required calibration factor for the RTC (approximately the no. of ppm the
# RTC lags the DS3231).
# For accurate results the delay should be at least 120 seconds. Longer is better.
# Note calibration factor is not saved on power down unless an RTC backup battery is used. An option is
# to store the calibration factor on disk and issue rtc.calibration(factor) on boot.

    def getcal(self, seconds):
        self.save_time()                        # Set DS3231 from RTC
        self.await_transition()
        rtcstart = now()
        dsstart = utime.mktime(self.get_time())
        pyb.delay(seconds * 1000)
        self.await_transition()
        rtcend = now()
        dsend = utime.mktime(self.get_time())
        dsdelta = (dsend - dsstart) *1000
        rtcdelta = rtcend[0] * 1000 + rtcend[1] - rtcstart[0] * 1000 - rtcstart[1]
        ppm = (1000000* (rtcdelta - dsdelta))/dsdelta
        return -ppm/0.954

    def calibrate(self, seconds):
        rtc.calibration(self.getcal(seconds))
