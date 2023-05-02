# ds3231_gen.py General purpose driver for DS3231 precison real time clock.

# Author: Peter Hinch
# Copyright Peter Hinch 2023 Released under the MIT license.

# Rewritten from datasheet to support alarms. Sources studied:
# WiPy driver at https://github.com/scudderfish/uDS3231
# https://github.com/notUnique/DS3231micro

# Assumes date > Y2K and 24 hour clock.

import time
import machine


_ADDR = const(104)

EVERY_SECOND = 0x0F  # Exported flags
EVERY_MINUTE = 0x0E
EVERY_HOUR = 0x0C
EVERY_DAY = 0x80
EVERY_WEEK = 0x40
EVERY_MONTH = 0

try:
    rtc = machine.RTC()
except:
    print("Warning: machine module does not support the RTC.")
    rtc = None


class Alarm:
    def __init__(self, device, n):
        self._device = device
        self._i2c = device.ds3231
        self.alno = n  # Alarm no.
        self.offs = 7 if self.alno == 1 else 0x0B  # Offset into address map
        self.mask = 0

    def _reg(self, offs : int, buf = bytearray(1)) -> int:  # Read a register
        self._i2c.readfrom_mem_into(_ADDR, offs, buf)
        return buf[0]

    def enable(self, run):
        flags = self._reg(0x0E) | 4  # Disable square wave
        flags = (flags | self.alno) if run else (flags & ~self.alno & 0xFF)
        self._i2c.writeto_mem(_ADDR, 0x0E, flags.to_bytes(1, "little"))

    def __call__(self):  # Return True if alarm is set
        return bool(self._reg(0x0F) & self.alno)

    def clear(self):
        flags = (self._reg(0x0F) & ~self.alno) & 0xFF
        self._i2c.writeto_mem(_ADDR, 0x0F, flags.to_bytes(1, "little"))

    def set(self, when, day=0, hr=0, min=0, sec=0):
        if when not in (0x0F, 0x0E, 0x0C, 0x80, 0x40, 0):
            raise ValueError("Invalid alarm specifier.")
        self.mask = when
        if when == EVERY_WEEK:
            day += 1  # Setting a day of week
        self._device.set_time((0, 0, day, hr, min, sec, 0, 0), self)
        self.enable(True)


class DS3231:
    def __init__(self, i2c):
        self.ds3231 = i2c
        self.alarm1 = Alarm(self, 1)
        self.alarm2 = Alarm(self, 2)
        if _ADDR not in self.ds3231.scan():
            raise RuntimeError(f"DS3231 not found on I2C bus at {_ADDR}")

    def get_time(self, data=bytearray(7)):
        def bcd2dec(bcd):  # Strip MSB
            return ((bcd & 0x70) >> 4) * 10 + (bcd & 0x0F)

        self.ds3231.readfrom_mem_into(_ADDR, 0, data)
        ss, mm, hh, wday, DD, MM, YY = [bcd2dec(x) for x in data]
        YY += 2000
        # Time from DS3231 in time.localtime() format (less yday)
        result = YY, MM, DD, hh, mm, ss, wday - 1, 0
        return result

    # Output time or alarm data to device
    # args: tt A datetime tuple. If absent uses localtime.
    # alarm: An Alarm instance or None if setting time
    def set_time(self, tt=None, alarm=None):
        # Given BCD value return a binary byte. Modifier:
        # Set MSB if any of bit(1..4) or bit 7 set, set b6 if mod[6]
        def gbyte(dec, mod=0):
            tens, units = divmod(dec, 10)
            n = (tens << 4) + units
            n |= 0x80 if mod & 0x0F else mod & 0xC0
            return n.to_bytes(1, "little")

        YY, MM, mday, hh, mm, ss, wday, yday = time.localtime() if tt is None else tt
        mask = 0 if alarm is None else alarm.mask
        offs = 0 if alarm is None else alarm.offs
        if alarm is None or alarm.alno == 1:  # Has a seconds register
            self.ds3231.writeto_mem(_ADDR, offs, gbyte(ss, mask & 1))
            offs += 1
        self.ds3231.writeto_mem(_ADDR, offs, gbyte(mm, mask & 2))
        offs += 1
        self.ds3231.writeto_mem(_ADDR, offs, gbyte(hh, mask & 4))  # Sets to 24hr mode
        offs += 1
        if alarm is not None:  # Setting an alarm - mask holds MS 2 bits
            self.ds3231.writeto_mem(_ADDR, offs, gbyte(mday, mask))
        else:  # Setting time
            self.ds3231.writeto_mem(_ADDR, offs, gbyte(wday + 1))  # 1 == Monday, 7 == Sunday
            offs += 1
            self.ds3231.writeto_mem(_ADDR, offs, gbyte(mday))  # Day of month
            offs += 1
            self.ds3231.writeto_mem(_ADDR, offs, gbyte(MM, 0x80))  # Century bit (>Y2K)
            offs += 1
            self.ds3231.writeto_mem(_ADDR, offs, gbyte(YY - 2000))

    def temperature(self):
        def twos_complement(input_value: int, num_bits: int) -> int:
            mask = 2 ** (num_bits - 1)
            return -(input_value & mask) + (input_value & ~mask)

        t = self.ds3231.readfrom_mem(_ADDR, 0x11, 2)
        i = t[0] << 8 | t[1]
        return twos_complement(i >> 6, 10) * 0.25

    def __str__(self, buf=bytearray(0x13)):  # Debug dump of device registers
        self.ds3231.readfrom_mem_into(_ADDR, 0, buf)
        s = ""
        for n, v in enumerate(buf):
            s = f"{s}0x{n:02x} 0x{v:02x} {v >> 4:04b} {v & 0xF :04b}\n"
            if not (n + 1) % 4:
                s = f"{s}\n"
        return s
