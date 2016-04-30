# 
# The MIT License (MIT)
# 
# Copyright (c) 2016 Robert Hammelrath
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
#
# Some parts of the software are a port of code provided by Rinky-Dink Electronics, Henning Karlsen,
# with the following copyright notice:
# 
## Copyright (C)2015 Rinky-Dink Electronics, Henning Karlsen. All right reserved
## This library is free software; you can redistribute it and/or
## modify it under the terms of the CC BY-NC-SA 3.0 license.
## Please see the included documents for further information.
#
# Class supporting TFT LC-displays with a parallel Interface
# First example: Controller SSD1963 with a 4.3" or 7" display
#
# The minimal connection is:
# X1..X8 for data, Y9 for /Reset, Y10 for /RD, Y11 for /WR and Y12 for /RS
# Then LED must be hard tied to Vcc and /CS to GND.
#

import pyb, stm
from uctypes import addressof
import TFT_io

# define constants
#
RESET  = const(1 << 10)  ## Y9
RD     = const(1 << 11)  ## Y10
WR     = const(0x01)  ## Y11
D_C    = const(0x02)  ## Y12

LED    = const(1 << 8) ## Y3
POWER  = const(1 << 9) ## Y4

## CS is not used and must be hard tied to GND

PORTRAIT = const(1)
LANDSCAPE = const(0)

class TFT:
    
    def __init__(self, controller = "SSD1963", lcd_type = "LB04301", orientation = LANDSCAPE,  v_flip = False, h_flip = False):
        self.tft_init(controller, lcd_type, orientation, v_flip, h_flip)
    
    def tft_init(self, controller = "SSD1963", lcd_type = "LB04301", orientation = LANDSCAPE,  v_flip = False, h_flip = False):
#
# For convenience, define X1..X1 and Y9..Y12 as output port using thy python functions.
# X1..X8 will be redefind on the fly as Input by accessing the MODER control registers 
# when needed. Y9 is treate seperately, since it is used for Reset, which is done at python level
# since it need long delays anyhow, 5 and 15 ms vs. 10 µs.
#
# Set TFT general defaults
        self.controller = controller
        self.lcd_type = lcd_type
        self.orientation = orientation
        self.v_flip = v_flip # flip vertical
        self.h_flip = h_flip # flip horizontal
        self.c_flip = 0 # flip blue/red
        self.rc_flip = 0 # flip row/column
        
        self.setColor((255, 255, 255)) # set FG color to white as can be.
        self.setBGColor((0, 0, 0))     # set BG to black
# special treat for BG LED
        self.pin_led = pyb.Pin("Y3", pyb.Pin.OUT_PP)
        self.led_tim = pyb.Timer(4, freq=500)
        self.led_ch = self.led_tim.channel(3, pyb.Timer.PWM, pin=self.pin_led)
        self.led_ch.pulse_width_percent(0)  # led off
        self.pin_led.value(0)  ## switch BG LED off
# special treat for Power Pin
        self.pin_power = pyb.Pin("Y4", pyb.Pin.OUT_PP)
        self.pin_power.value(1)  ## switch Power on
        pyb.delay(10)
# this may have to be moved to the controller specific section
        if orientation == PORTRAIT:
            self.setXY = TFT_io.setXY_P
            self.drawPixel = TFT_io.drawPixel_P
        else:
            self.setXY = TFT_io.setXY_L
            self.drawPixel = TFT_io.drawPixel_L
        self.swapbytes = TFT_io.swapbytes
        self.swapcolors = TFT_io.swapcolors
#  ----------        
        for pin_name in ["X1", "X2", "X3", "X4", "X5", "X6", "X7", "X8", 
                   "Y10", "Y11", "Y12"]:
            pin = pyb.Pin(pin_name, pyb.Pin.OUT_PP) # set as output
            pin.value(1)  ## set high as default
# special treat for Reset
        self.pin_reset = pyb.Pin("Y9", pyb.Pin.OUT_PP)
# Reset the device
        self.pin_reset.value(1)  ## do a hard reset
        pyb.delay(10)
        self.pin_reset.value(0)  ## Low
        pyb.delay(20)
        self.pin_reset.value(1)  ## set high again
        pyb.delay(20)
#
# Now initialiize the LCD
# This is for the SSD1963 controller and two specific LCDs. More may follow.
# Data taken from the SSD1963 data sheet, SSD1963 Application Note and the LCD Data sheets
#
        if controller == "SSD1963":           # 1st approach for 480 x 272
            TFT_io.tft_cmd_data(0xe2, bytearray(b'\x1d\x02\x54'), 3) # PLL multiplier, set PLL clock to 100M
              # N=0x2D for 6.5MHz, 0x1D for 10MHz crystal 
              # PLLClock = Crystal * (Mult + 1) / (Div + 1)
              # The intermediate value Crystal * (Mult + 1) must be between 250MHz and 750 MHz
            TFT_io.tft_cmd_data(0xe0, bytearray(b'\x01'), 1) # PLL Enable
            pyb.delay(10)
            TFT_io.tft_cmd_data(0xe0, bytearray(b'\x03'), 1)
            pyb.delay(10)
            TFT_io.tft_cmd(0x01)                     # software reset
            pyb.delay(10)
#
# Settings for the LCD
# 
# The LCDC_FPR depends on PLL clock and the reccomended LCD Dot clock DCLK
#
# LCDC_FPR = (DCLK * 1048576 / PLLClock) - 1 
# 
# The other settings are less obvious, since the definitions of the SSD1963 data sheet and the 
# LCD data sheets differ. So what' common, even if the names may differ:
# HDP  Horizontal Panel width (also called HDISP, Thd). The value store in the register is HDP - 1
# VDP  Vertical Panel Width (also called VDISP, Tvd). The value stored in the register is VDP - 1
# HT   Total Horizontal Period, also called HP, th... The exact value does not matter
# VT   Total Vertical Period, alco called VT, tv, ..  The exact value does not matter
# HPW  Width of the Horizontal sync pulse, also called HS, thpw. 
# VPW  Width of the Vertical sync pulse, also called VS, tvpw
# Front Porch (HFP and VFP) Time between the end of display data and the sync pulse
# Back Porch (HBP  and VBP Time between the start of the sync pulse and the start of display data.
#      HT = FP + HDP + BP  and VT = VFP + VDP + VBP (sometimes plus sync pulse width)
# Unfortunately, the controller does not use these front/back porch times, instead it uses an starting time
# in the front porch area and defines (see also figures in chapter 13.3 of the SSD1963 data sheet)
# HPS  Time from that horiz. starting point to the start of the horzontal display area
# LPS  Time from that horiz. starting point to the horizontal sync pulse
# VPS  Time from the vert. starting point to the first line
# FPS  Time from the vert. starting point to the vertical sync pulse
#
# So the following relations must be held:
#
# HT >  HDP + HPS
# HPS >= HPW + LPS 
# HPS = Back Porch - LPS, or HPS = Horizontal back Porch
# VT > VDP + VPS
# VPS >= VPW + FPS
# VPS = Back Porch - FPS, or VPS = Vertical back Porch
#
# LPS or FPS may have a value of zero, since the length of the front porch is detemined by the 
# other figures
#
# The best is to start with the recomendations of the lCD data sheet for Back porch, grab a
# sync pulse with and the determine the other, such that they meet the relations. Typically, these
# values allow for some ambuigity. 
# 
            if lcd_type == "LB04301":  # Size 480x272, 4.3", 24 Bit, 4.3"
                #
                # Value            Min    Typical   Max
                # DotClock        5 MHZ    9 MHz    12 MHz
                # HT (Hor. Total   490     531      612
                # HDP (Hor. Disp)          480
                # HBP (back porch)  8      43
                # HFP (Fr. porch)   2       8
                # HPW (Hor. sync)   1
                # VT (Vert. Total) 275     288      335
                # VDP (Vert. Disp)         272
                # VBP (back porch)  2       12
                # VFP (fr. porch)   1       4
                # VPW (vert. sync)  1       10
                #
                # This table in combination with the relation above leads to the settings:
                # HPS = 43, HPW = 8, LPS = 0, HT = 531
                # VPS = 14, VPW = 10, FPS = 0, VT = 288
                #
                self.disp_x_size = 479
                self.disp_y_size = 271
                TFT_io.tft_cmd_data_AS(0xe6, bytearray(b'\x01\x70\xa3'), 3) # PLL setting for PCLK
                    # (9MHz * 1048576 / 100MHz) - 1 = 94371 = 0x170a3
                TFT_io.tft_cmd_data_AS(0xb0, bytearray(  # # LCD SPECIFICATION
                    [0x20,                # 24 Color bits, HSync/VSync low, No Dithering
                     0x00,                # TFT mode
                     self.disp_x_size >> 8, self.disp_x_size & 0xff, # physical Width of TFT
                     self.disp_y_size >> 8, self.disp_y_size & 0xff, # physical Height of TFT
                     0x00]), 7)  # Last byte only required for a serial TFT
                TFT_io.tft_cmd_data_AS(0xb4, bytearray(b'\x02\x13\x00\x2b\x08\x00\x00\x00'), 8) 
                        # HSYNC,  Set HT 531  HPS 43   HPW=Sync pulse 8 LPS 0
                TFT_io.tft_cmd_data_AS(0xb6, bytearray(b'\x01\x20\x00\x0e\x0a\x00\x00'), 7) 
                        # VSYNC,  Set VT 288  VPS 14 VPW 10 FPS 0
                TFT_io.tft_cmd_data_AS(0x36, bytearray([(orientation & 1) << 5 | (h_flip & 1) << 1 | (v_flip) & 1]), 1) 
                        # rotation/ flip, etc., t.b.d. 
            elif lcd_type == "AT070TN92": # Size 800x480, 7", 18 Bit, lower color bits ignored
                #
                # Value            Min     Typical   Max
                # DotClock       26.4 MHz 33.3 MHz  46.8 MHz
                # HT (Hor. Total   862     1056     1200
                # HDP (Hor. Disp)          800
                # HBP (back porch)  46      46       46
                # HFP (Fr. porch)   16     210      254
                # HPW (Hor. sync)   1                40
                # VT (Vert. Total) 510     525      650
                # VDP (Vert. Disp)         480
                # VBP (back porch)  23      23       23
                # VFP (fr. porch)   7       22      147
                # VPW (vert. sync)  1                20
                #
                # This table in combination with the relation above leads to the settings:
                # HPS = 46, HPW = 8,  LPS = 0, HT = 1056
                # VPS = 23, VPW = 10, VPS = 0, VT = 525
                #
                self.disp_x_size = 799
                self.disp_y_size = 479
                TFT_io.tft_cmd_data_AS(0xe6, bytearray(b'\x05\x53\xf6'), 3) # PLL setting for PCLK
                    # (33.3MHz * 1048576 / 100MHz) - 1 = 349174 = 0x553f6
                TFT_io.tft_cmd_data_AS(0xb0, bytearray(  # # LCD SPECIFICATION
                    [0x00,                # 18 Color bits, HSync/VSync low, No Dithering/FRC
                     0x00,                # TFT mode
                     self.disp_x_size >> 8, self.disp_x_size & 0xff, # physical Width of TFT
                     self.disp_y_size >> 8, self.disp_y_size & 0xff, # physical Height of TFT
                     0x00]), 7)  # Last byte only required for a serial TFT
                TFT_io.tft_cmd_data_AS(0xb4, bytearray(b'\x04\x1f\x00\x2e\x08\x00\x00\x00'), 8) 
                        # HSYNC,      Set HT 1056  HPS 46  HPW 8 LPS 0
                TFT_io.tft_cmd_data_AS(0xb6, bytearray(b'\x02\x0c\x00\x17\x08\x00\x00'), 7) 
                        # VSYNC,   Set VT 525  VPS 23 VPW 08 FPS 0
                TFT_io.tft_cmd_data_AS(0x36, bytearray([(orientation & 1) << 5 | (h_flip & 1) << 1 | (v_flip) & 1]), 1) 
                        # rotation/ flip, etc., t.b.d. 
            else:
                print("Wrong Parameter lcd_type: ", lcd_type)
                return
            TFT_io.tft_cmd_data_AS(0xBA, bytearray(b'\x0f'), 1) # GPIO[3:0] out 1
            TFT_io.tft_cmd_data_AS(0xB8, bytearray(b'\x07\x01'), 1) # GPIO3=input, GPIO[2:0]=output

            TFT_io.tft_cmd_data_AS(0xf0, bytearray(b'\x00'), 1) # Pixel data Interface 8 Bit

            TFT_io.tft_cmd(0x29)             # Display on
            TFT_io.tft_cmd_data_AS(0xbe, bytearray(b'\x06\xf0\x01\xf0\x00\x00'), 6) 
                    # Set PWM for B/L
            TFT_io.tft_cmd_data_AS(0xd0, bytearray(b'\x0d'), 1) # Set DBC: enable, agressive
        else:
            print("Wrong Parameter controller: ", controller)
            return
#
# Set character printing defaults
#
        self.text_font = None
        self.setTextStyle(self.color, self.BGcolor, 0, None, 0)
#
# Init done. clear Screen and switch BG LED on
#
        self.text_x = self.text_y = self.text_yabs = 0
        self.clrSCR()           # clear the display
#        self.backlight(100)  ## switch BG LED on
#
# Return screen dimensions
#
    def getScreensize(self):
        if self.orientation == LANDSCAPE:
            return (self.disp_x_size + 1, self.disp_y_size + 1)
        else:
            return (self.disp_y_size + 1, self.disp_x_size + 1)
#
# set backlight brightness
#            
    def backlight(self, percent):
        percent = max(0, min(percent, 100))
        self.led_ch.pulse_width_percent(percent)  # set LED
#
# switch power on/off
#            
    def power(self, onoff):
        if onoff:
            self.pin_power.value(True)  ## switch power on or off
        else:
            self.pin_power.value(False)

#
# set the tft flip modes
#            
    def set_tft_mode(self, v_flip = False, h_flip = False, c_flip = False, orientation = LANDSCAPE):
        self.v_flip = v_flip # flip vertical
        self.h_flip = h_flip # flip horizontal
        self.c_flip = c_flip # flip blue/red
        self.orientation = orientation # LANDSCAPE/PORTRAIT
        TFT_io.tft_cmd_data_AS(0x36, 
            bytearray([(self.orientation << 5) |(self.c_flip << 3) | (self.h_flip & 1) << 1 | (self.v_flip) & 1]), 1) 
                        # rotation/ flip, etc., t.b.d. 
#
# get the tft flip modes
#            
    def get_tft_mode(self):
        return (self.v_flip, self.h_flip, self.c_flip, self.orientation) # 
#
# set the color used for the draw commands
#            
    def setColor(self, fgcolor):
        self.color = fgcolor
        self.colorvect = bytearray(self.color)  # prepare byte array
#
# Set BG color used for the draw commands
# 
    def setBGColor(self, bgcolor):
        self.BGcolor = bgcolor
        self.BGcolorvect = bytearray(self.BGcolor)  # prepare byte array
        self.BMPcolortable = bytearray([self.BGcolorvect[2], # create colortable
            self.BGcolorvect[1], self.BGcolorvect[0],0,
            self.colorvect[2], self.colorvect[1], self.colorvect[0],0])
#
# get the color used for the draw commands
#            
    def getColor(self):
        return self.color
#
# get BG color used for 
# 
    def getBGColor(self):
        return self.BGcolor
#
# Draw a single pixel at location x, y with color 
# Rather slow at 40µs/Pixel
#        
    def drawPixel_py(self, x, y, color):
        self.setXY(x, y, x, y)
        TFT_io.displaySCR_AS(color, 1)  # 
#
# clear screen, set it to BG color.
#             
    def clrSCR(self, color = None):
        if color is None:
            colorvect = self.BGcolorvect
        else:
            colorvect = bytearray(color)
        self.clrXY()
        TFT_io.fillSCR_AS(colorvect, (self.disp_x_size + 1) * (self.disp_y_size + 1))
        self.setScrollArea(0, self.disp_y_size + 1, 0)
        self.setScrollStart(0)
        self.setTextPos(0,0)
#
# reset the address range to fullscreen
#       
    def clrXY(self):
        if self.orientation == LANDSCAPE:
            self.setXY(0, 0, self.disp_x_size, self.disp_y_size)
        else:
            self.setXY(0, 0, self.disp_y_size, self.disp_x_size)
#
# Draw a line from x1, y1 to x2, y2 with the color set by setColor()
# Straight port from the UTFT Library at Rinky-Dink Electronics
# 
    def drawLine(self, x1, y1, x2, y2, color = None): 
        if y1 == y2:
            self.drawHLine(x1, y1, x2 - x1 + 1, color)
        elif x1 == x2:
            self.drawVLine(x1, y1, y2 - y1 + 1, color)
        else:
            if color is None:
                colorvect = self.colorvect
            else:
                colorvect = bytearray(color)
            dx, xstep  = (x2 - x1, 1) if x2 > x1 else (x1 - x2, -1)
            dy, ystep  = (y2 - y1, 1) if y2 > y1 else (y1 - y2, -1)
            col, row = x1, y1
            if dx < dy:
                t = - (dy >> 1)
                while True:
                    self.drawPixel(col, row, colorvect)
                    if row == y2:
                        return
                    row += ystep
                    t += dx
                    if t >= 0:
                        col += xstep
                        t -= dy
            else:
                t = - (dx >> 1)
                while True:
                    self.drawPixel(col, row, colorvect)
                    if col == x2:
                        return
                    col += xstep
                    t += dy
                    if t >= 0:
                        row += ystep
                        t -= dx
#
# Draw a horizontal line with 1 Pixel width, from x,y to x + l - 1, y
# Straight port from the UTFT Library at Rinky-Dink Electronics
# 
    def drawHLine(self, x, y, l, color = None): # draw horiontal Line
        if color is None:
            colorvect = self.colorvect
        else:
            colorvect = bytearray(color)
        if l < 0:  # negative length, swap parameters
            l = -l
            x -= l
        self.setXY(x, y, x + l - 1, y) # set display window
        TFT_io.fillSCR_AS(colorvect, l)
#
# Draw a vertical line with 1 Pixel width, from x,y to x, y + l - 1
# Straight port from the UTFT Library at Rinky-Dink Electronics
# 
    def drawVLine(self, x, y, l, color = None): # draw horiontal Line
        if color is None:
            colorvect = self.colorvect
        else:
            colorvect = bytearray(color)
        if l < 0:  # negative length, swap parameters
            l = -l
            y -= l
        self.setXY(x, y, x, y + l - 1) # set display window
        TFT_io.fillSCR_AS(colorvect, l)
#
# Draw rectangle from x1, y1, to x2, y2
# Straight port from the UTFT Library at Rinky-Dink Electronics
#
    def drawRectangle(self, x1, y1, x2, y2, color = None):
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
    	self.drawHLine(x1, y1, x2 - x1 + 1, color)
        self.drawHLine(x1, y2, x2 - x1 + 1, color)
        self.drawVLine(x1, y1, y2 - y1 + 1, color)
        self.drawVLine(x2, y1, y2 - y1 + 1, color)
#
# Fill rectangle
# Almost straight port from the UTFT Library at Rinky-Dink Electronics
#
    def fillRectangle(self, x1, y1, x2, y2, color=None):
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        self.setXY(x1, y1, x2, y2) # set display window
        if color:
            TFT_io.fillSCR_AS(bytearray(color), (x2 - x1 + 1) * (y2 - y1 + 1))
        else:
            TFT_io.fillSCR_AS(self.colorvect, (x2 - x1 + 1) * (y2 - y1 + 1))

#
# Draw smooth rectangle from x1, y1, to x2, y2
# Straight port from the UTFT Library at Rinky-Dink Electronics
#
    def drawClippedRectangle(self, x1, y1, x2, y2, color = None):
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        if (x2-x1) > 4 and (y2-y1) > 4:
            if color is None:
                colorvect = self.colorvect
            else:
                colorvect = bytearray(color)
            self.drawPixel(x1 + 2,y1 + 1, colorvect)
            self.drawPixel(x1 + 1,y1 + 2, colorvect)
            self.drawPixel(x2 - 2,y1 + 1, colorvect)
            self.drawPixel(x2 - 1,y1 + 2, colorvect)
            self.drawPixel(x1 + 2,y2 - 1, colorvect)
            self.drawPixel(x1 + 1,y2 - 2, colorvect)
            self.drawPixel(x2 - 2,y2 - 1, colorvect)
            self.drawPixel(x2 - 1,y2 - 2, colorvect)
            self.drawHLine(x1 + 3, y1, x2 - x1 - 5, colorvect)
            self.drawHLine(x1 + 3, y2, x2 - x1 - 5, colorvect)
            self.drawVLine(x1, y1 + 3, y2 - y1 - 5, colorvect)
            self.drawVLine(x2, y1 + 3, y2 - y1 - 5, colorvect)
#
# Fill smooth rectangle from x1, y1, to x2, y2
# Straight port from the UTFT Library at Rinky-Dink Electronics
#
    def fillClippedRectangle(self, x1, y1, x2, y2, color = None):
        if x1 > x2:
            t = x1; x1 = x2; x2 = t
        if y1 > y2:
            t = y1; y1 = y2; y2 = t
        if (x2-x1) > 4 and (y2-y1) > 4:
            for i in range(((y2 - y1) // 2) + 1):
                if i == 0:
                    self.drawHLine(x1 + 3, y1 + i, x2 - x1 - 5, color)
                    self.drawHLine(x1 + 3, y2 - i, x2 - x1 - 5, color)
                elif i == 1:
                    self.drawHLine(x1 + 2, y1 + i, x2 - x1 - 3, color)
                    self.drawHLine(x1 + 2, y2 - i, x2 - x1 - 3, color)
                elif i == 2:
                    self.drawHLine(x1 + 1, y1 + i, x2 - x1 - 1, color)
                    self.drawHLine(x1 + 1, y2 - i, x2 - x1 - 1, color)
                else:
                    self.drawHLine(x1, y1 + i, x2 - x1 + 1, color)
                    self.drawHLine(x1, y2 - i, x2 - x1 + 1, color)
#
# draw a circle at x, y with radius
# Straight port from the UTFT Library at Rinky-Dink Electronics
#
    def drawCircle(self, x, y, radius, color = None):

        if color is None:
            colorvect = self.colorvect
        else:
            colorvect = bytearray(color)
    
        f = 1 - radius
        ddF_x = 1
        ddF_y = -2 * radius
        x1 = 0
        y1 = radius

        self.drawPixel(x, y + radius, colorvect)
        self.drawPixel(x, y - radius, colorvect)
        self.drawPixel(x + radius, y, colorvect)
        self.drawPixel(x - radius, y, colorvect)

        while x1 < y1:
            if f >= 0:
	            y1 -= 1
	            ddF_y += 2
	            f += ddF_y
            x1 += 1
            ddF_x += 2
            f += ddF_x
            self.drawPixel(x + x1, y + y1, colorvect)
            self.drawPixel(x - x1, y + y1, colorvect)
            self.drawPixel(x + x1, y - y1, colorvect)
            self.drawPixel(x - x1, y - y1, colorvect)
            self.drawPixel(x + y1, y + x1, colorvect)
            self.drawPixel(x - y1, y + x1, colorvect)
            self.drawPixel(x + y1, y - x1, colorvect)
            self.drawPixel(x - y1, y - x1, colorvect)
#
# fill a circle at x, y with radius
# Straight port from the UTFT Library at Rinky-Dink Electronics
# Instead of calculating x = sqrt(r*r - y*y), it searches the x
# for r*r = x*x + x*x
#
    def fillCircle(self, x, y, radius, color = None):
        r_square = radius * radius * 4
        for y1 in range (-(radius * 2), 1): 
            y_square = y1 * y1
            for x1 in range (-(radius * 2), 1):
                if x1*x1+y_square <= r_square: 
                    x1i = x1 // 2
                    y1i = y1 // 2
                    self.drawHLine(x + x1i, y + y1i, 2 * (-x1i), color)
                    self.drawHLine(x + x1i, y - y1i, 2 * (-x1i), color)
                    break;
#
# Draw a bitmap at x,y with size sx, sy
# mode determines the type of expected data
# mode = 1: The data contains 1 bit per pixel, mapped to fg/bg color 
#           unless a colortable is provided
# mode = 2: The data contains 2 bit per pixel; a colortable with 4 entries must be provided
# mode = 4: The data contains 4 bit per pixel; 
#           a colortable with 16 entries must be provided
# mode = 8: The data contains 8 bit per pixel; 
#           a colortable with 256 entries must be provided
# mode = 16: The data must contain 2 packed bytes/pixel red/green/blue in 565 format
# mode = 24: The data must contain 3 bytes/pixel red/green/blue
#
    def drawBitmap(self, x, y, sx, sy, data, mode = 24, colortable = None):
        self.setXY(x, y, x + sx - 1, y + sy - 1)
        if mode == 24:
            TFT_io.displaySCR_AS(data, sx * sy)
        elif mode == 16:
            TFT_io.displaySCR565_AS(data, sx * sy)
        elif mode == 1:
            if colortable is None:
                colortable = self.BMPcolortable # create colortable
            TFT_io.displaySCR_bmp(data, sx*sy, 1, colortable)
        elif mode == 2:
            if colortable is None:
                return 
            TFT_io.displaySCR_bmp(data, sx*sy, 2, colortable)
        elif mode == 4:
            if colortable is None:
                return 
            TFT_io.displaySCR_bmp(data, sx*sy, 4, colortable)
        elif mode == 8:
            if colortable is None:
                return 
            TFT_io.displaySCR_bmp(data, sx*sy, 8, colortable)

#
# set scroll area to the region between the first and last line
#
    def setScrollArea(self, tfa, vsa, bfa):
        TFT_io.tft_cmd_data_AS(0x33, bytearray(  #set scrolling range
                    [(tfa >> 8) & 0xff, tfa & 0xff, 
                     (vsa >> 8) & 0xff, vsa & 0xff,
                     (bfa >> 8) & 0xff, bfa & 0xff]), 6)
        self.scroll_tfa = tfa
        self.scroll_vsa = vsa
        self.scroll_bfa = bfa
        self.setScrollStart(self.scroll_tfa)
        x, y = self.getTextPos()
        self.setTextPos(x, y) # realign pointers
#
# get scroll area of the region between the first and last line
#
    def getScrollArea(self):
        return self.scroll_tfa, self.scroll_vsa, self.scroll_bfa
#
# set the line which is displayed first
#
    def setScrollStart(self, lline):
        self.scroll_start = lline # store the logical first line
        TFT_io.tft_cmd_data_AS(0x37, bytearray([(lline >> 8) & 0xff, lline & 0xff]), 2)
#
# get the line which is displayed first
#
    def getScrollStart(self):
        return self.scroll_start # get the logical first line

#
# Scroll vsa up/down by a number of pixels
#
    def scroll(self, pixels):
        line = ((self.scroll_start - self.scroll_tfa + pixels) % self.scroll_vsa
                + self.scroll_tfa)
        self.setScrollStart(line) # set the new line
#
# Set text position
#
    def setTextPos(self, x, y, clip = False, scroll = True):
        self.text_width, self.text_height = self.getScreensize()  ## height possibly wrong
        self.text_x = x
        if self.scroll_tfa <= y < (self.scroll_tfa + self.scroll_vsa):  # in scroll area ? check later for < or <=
        # correct position relative to scroll start
            self.text_y = (y + self.scroll_start - self.scroll_tfa)
            if self.text_y >= (self.scroll_tfa + self.scroll_vsa):
                self.text_y -= self.scroll_vsa
        else: # absolute
            self.text_y = y
        self.text_yabs = y
        # Hint: self.text_yabs = self.text_y - self.scroll_start) % self.scroll_vsa + self.scroll_tfa)
        if clip and (self.text_x + clip) < self.text_width:
            self.text_width = self.text_x + clip
        self.text_scroll = scroll
#
# Get text position
#
    def getTextPos(self):
        return (self.text_x, self.text_yabs)
#
# Set Text Style
#
    def setTextStyle(self, fgcolor=None, bgcolor=None, transparency=None, font=None, gap=None):
        if font is not None:
            self.text_font = font 
            self.text_rows, self.text_cols, nchar, first = font.get_properties() # 
        if transparency is not None:
            self.transparency = transparency
        if gap is not None:
            self.text_gap = gap
        self.text_color = bytearray(0)
        if bgcolor is not None:
            self.text_bgcolor = bgcolor
        if fgcolor is not None:
            self.text_fgcolor = fgcolor
        if transparency is not None:
            self.transparency = transparency
        self.text_color = (bytearray(self.text_bgcolor) 
                           + bytearray(self.text_fgcolor) 
                           + bytearray([self.transparency]))
        if gap is not None:
            self.text_gap = gap
#
# Get Text Style: return (color, bgcolor, font, transpareny, gap)
#
    def getTextStyle(self):
        return (self.text_color[3:6], self.text_color[0:3], 
                self.transparency, self.text_font, self.text_gap)
        
#
# Check, if a new line is to be opened
# if yes, advance, including scrolling, and clear line, if flags is set
# Obsolete?
#
    def printNewline(self, clear = False):
        if  (self.text_yabs + self.text_rows) >= (self.scroll_tfa + self.scroll_vsa): # does the line fit?
            self.scroll(self.text_rows) # no. scroll
        else: # Yes, just advance pointers
            self.text_yabs += self.text_rows
        self.setTextPos(self.text_x, self.text_yabs)
        if clear: 
            self.printClrLine(2) # clear actual line
#
# Carriage Return
#
    def printCR(self): # clear to end of line
        self.text_x = 0
#
# clear line modes
#
    def printClrLine(self, mode = 0): # clear to end of line/bol/line
        if mode == 0:
            self.setXY(self.text_x, self.text_y, 
                       self.text_width - 1, self.text_y + self.text_rows - 1) # set display window
            TFT_io.fillSCR_AS(self.text_color, (self.text_width - self.text_x + 1) * self.text_rows)
        elif mode == 1 and self.text_x > 0:
            self.setXY(0, self.text_y, 
                    self.text_x - 1, self.text_y + self.text_rows - 1) # set display window
            TFT_io.fillSCR_AS(self.text_color, (self.text_x - 1) * self.text_rows)
        elif mode == 2:
            self.setXY(0, self.text_y, 
                    self.text_width - 1, self.text_y + self.text_rows - 1) # set display window
            TFT_io.fillSCR_AS(self.text_color, self.text_width * self.text_rows)
#
# clear sreen modes
#
    def printClrSCR(self): # clear Area set by setScrollArea
        self.setXY(0, self.scroll_tfa, 
            self.text_width - 1, self.scroll_tfa + self.scroll_vsa) # set display window
        TFT_io.fillSCR_AS(self.text_color, self.text_width * self.scroll_vsa)
        self.setScrollStart(self.scroll_tfa)
        self.setTextPos(0, self.scroll_tfa)
#
# Print string s, returning the length of the printed string in pixels
# 
    def printString(self, s, bg_buf=None):
        len = 0
        for c in s:
            cols = self.printChar(c, bg_buf)
            if cols == 0: # could not print (any more)
                break
            len += cols
        return len
#
# Print string c using the given char bitmap at location x, y, returning the width of the printed char in pixels
# 
    def printChar(self, c, bg_buf=None):
# get the charactes pixel bitmap and dimensions
        if self.text_font: 
            fontptr, rows, cols = self.text_font.get_ch(ord(c))
        else:
            raise AttributeError('No font selected')
        pix_count = cols * rows   # number of bits in the char
# test char fit
        if self.text_x + cols > self.text_width:  # does the char fit on the screen?
            if self.text_scroll:
                self.printCR()      # No, then CR
                self.printNewline(True) # NL: advance to the next line
            else:
                return 0
# Retrieve Background data if transparency is required
        if self.transparency: # in case of transpareny, the frame buffer content is needed
            if not bg_buf:    # buffer allocation needed?
                bg_buf = bytearray(pix_count * 3) # sigh...
            self.setXY(self.text_x, self.text_y, self.text_x + cols - 1, self.text_y + rows - 1) # set area
            TFT_io.tft_read_cmd_data_AS(0x2e, bg_buf, pix_count * 3) # read background data
        else:
            bg_buf = 0 # dummy assignment, since None is not accepted
# Set XY range & print char
        self.setXY(self.text_x, self.text_y, self.text_x + cols - 1, self.text_y + rows - 1) # set area
        TFT_io.displaySCR_charbitmap(fontptr, pix_count, self.text_color, bg_buf) # display char!
#advance pointer
        self.text_x += (cols + self.text_gap)
        return cols + self.text_gap


