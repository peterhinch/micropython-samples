# setup3d_lcd160cr.py
# Hardware specific setup for 3D demos

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

from machine import I2C, SPI, Pin
import framebuf
import gc
from lcd160cr import LCD160CR as SSD
from lcd160cr import LANDSCAPE
# IMU driver for test_imu only. With other IMU's the fusion module
# may be used for quaternion output.
# https://github.com/micropython-IMU/micropython-fusion
#from bno055 import BNO055
## Initialise IMU
#i2c = I2C(1)
#imu = BNO055(i2c)

# Export color constants
WHITE = SSD.rgb(255, 255, 255)
GREY = SSD.rgb(100, 100, 100)
GREEN = SSD.rgb(0, 255, 0)
BLUE = SSD.rgb(0, 0, 255)
RED = SSD.rgb(255, 0, 0)
YELLOW = SSD.rgb(255, 255, 0)
CYAN = SSD.rgb(0, 255, 255)
BLACK = SSD.rgb(0, 0, 0)

# DIMENSION No. of pixels for a change of 1.0
# Viewing area is 128*128
DIMENSION = 64

gc.collect()
_buf = bytearray(160*128*2)  # 40KiB
_fb = framebuf.FrameBuffer(_buf, 160, 128, framebuf.RGB565)
_lcd = SSD('Y')
_lcd.set_orient(LANDSCAPE)
_lcd.set_spi_win(0, 0, 160, 128)
# Standard functions
line = _fb.line
fill = _fb.fill

def show():
    gc.collect()
    _lcd.show_framebuf(_fb)

def setup():
    return _lcd
