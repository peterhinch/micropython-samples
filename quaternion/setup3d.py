# setup3d.py
# Hardware specific setup for 3D demos

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

from machine import I2C, SPI, Pin
import gc

# This module must export the following functions
# fill(color)  Fill the buffer with a color
# line(xs, ys, xe, ye, color)  Draw a line to the buffer
# show() Display result
# Also dimension bound variable.

from ssd1351_16bit import SSD1351 as SSD
_HEIGHT = const(128)  # SSD1351 variant in use

# IMU driver for test_imu only. With other IMU's the fusion module
# may be used for quaternion output.
# https://github.com/micropython-IMU/micropython-fusion
from bno055 import BNO055
# Initialise IMU
i2c = I2C(2)
imu = BNO055(i2c)

# Export color constants
WHITE = SSD.rgb(255, 255, 255)
GREY = SSD.rgb(100, 100, 100)
GREEN = SSD.rgb(0, 255, 0)
BLUE = SSD.rgb(0, 0, 255)
RED = SSD.rgb(255, 0, 0)
YELLOW = SSD.rgb(255, 255, 0)
CYAN = SSD.rgb(0, 255, 255)


# Initialise display
# Monkey patch size of square viewing area. No. of pixels for a change of 1.0
# Viewing area is 128*128
DIMENSION = 64

gc.collect()
_pdc = Pin('X1', Pin.OUT_PP, value=0)  # Pins are for Pyboard
_pcs = Pin('X2', Pin.OUT_PP, value=1)
_prst = Pin('X3', Pin.OUT_PP, value=1)
_spi = SPI(2)  # scl Y9 sda Y10
_ssd = SSD(_spi, _pcs, _pdc, _prst, height=_HEIGHT)  # Create a display instance

line = _ssd.line
fill = _ssd.fill
show = _ssd.show

def setup():
    return _ssd
