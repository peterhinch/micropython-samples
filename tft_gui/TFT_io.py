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
# Class supporting TFT LC-displays with a parallel Interface
# First example: Controller SSD1963
# It uses X1..X8 for data and Y3, Y9, Y10, Y11 and Y12 for control signals.
# The minimal connection just for writes is X1..X8 for data, Y9 for /Reset. Y11 for /WR and Y12 for /RS
# Then LED and /CS must be hard tied to Vcc and GND, and /RD is not used.
#
#  Some parts of the software are a port of code provided by Rinky-Dink Electronics, Henning Karlsen,
#  with the following copyright notice:
## Copyright (C)2015 Rinky-Dink Electronics, Henning Karlsen. All right reserved
##  This library is free software; you can redistribute it and/or
##  modify it under the terms of the CC BY-NC-SA 3.0 license.
##  Please see the included documents for further information.
#

import pyb, stm
from uctypes import addressof

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

class TFT_io:
#
# display bitmap
#
    @staticmethod
    @micropython.viper        
    def displaySCR_bitmap(bits: ptr8, size: int, control: ptr8, bg_buf: ptr8):
        gpioa = ptr8(stm.GPIOA)
        gpiob = ptr16(stm.GPIOB + stm.GPIO_BSRRL)
        gpioam = ptr16(stm.GPIOA + stm.GPIO_MODER)
#
        transparency = control[6]
        bm_ptr = 0
        bg_ptr = 0
        mask   = 0x80
#        rd_command = 0x2e  ## start read
        while size:
#           if False: # transparency: # read back data
#               gpioa[stm.GPIO_ODR] = rd_command         # start/continue read command
#               gpiob[1] = D_C | WR     # set C/D and WR low
#               gpiob[0] = D_C | WR     # set C/D and WR high

#               gpioam[0] = 0       # configure X1..X8 as Input

#               gpiob[1] = RD       # set RD low. C/D still high
#               rd_command = 0x3e      # continue read
#               bg_red = gpioa[stm.GPIO_IDR]  # get data from port A
#               gpiob[0] = RD       # set RD high again

#               gpiob[1] = RD       # set RD low. C/D still high
#               delay = 1
#               bg_green = gpioa[stm.GPIO_IDR]  # get data from port A
#               gpiob[0] = RD       # set RD high again

#               gpiob[1] = RD       # set RD low. C/D still high
#               delay = 1
#               bg_blue = gpioa[stm.GPIO_IDR]  # get data from port A
#               gpiob[0] = RD       # set RD high again

#               gpioam[0] = 0x5555  # configure X1..X8 as Output

#               gpioa[stm.GPIO_ODR] = 0x3c         # continue write command
#               gpiob[1] = D_C | WR     # set C/D and WR low
#               gpiob[0] = D_C | WR     # set C/D and WR high

            if bits[bm_ptr] & mask:
                if transparency & 8: # Invert bg color as foreground
                    gpioa[stm.GPIO_ODR] = 255 - bg_buf[bg_ptr] # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = 255 - bg_buf[bg_ptr + 1]  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = 255 - bg_buf[bg_ptr + 2]  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again
                else: # not invert
                    gpioa[stm.GPIO_ODR] = control[3]     # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = control[4]      # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = control[5]      # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again
            else:
                if transparency & 1: # Dim background
                    gpioa[stm.GPIO_ODR] = bg_buf[bg_ptr] >> 1  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = bg_buf[bg_ptr + 1] >> 1  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = bg_buf[bg_ptr + 2] >> 1  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again
                elif transparency & 2: # keep Background
                    gpioa[stm.GPIO_ODR] = bg_buf[bg_ptr] # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = bg_buf[bg_ptr + 1]  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = bg_buf[bg_ptr + 2]  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again
                elif transparency & 4: # invert Background
                    gpioa[stm.GPIO_ODR] = 255 - bg_buf[bg_ptr] # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = 255 - bg_buf[bg_ptr + 1]  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = 255 - bg_buf[bg_ptr + 2]  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again
                else: # not transparent
                    gpioa[stm.GPIO_ODR] = control[0]  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = control[1]  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again

                    gpioa[stm.GPIO_ODR] = control[2]  # set data on port A
                    gpiob[1] = WR       # set WR low. C/D still high
                    gpiob[0] = WR       # set WR high again
            mask >>= 1
            if mask == 0: # map ptr advance on byte exhaust
                mask = 0x80
                bm_ptr += 1
            size -= 1
            bg_ptr += 3
#
# Set the address range for various draw commands and set the TFT for expecting data
#
    @staticmethod
    @micropython.viper        
    def setXY_P(x1: int, y1: int, x2: int, y2: int): ## set the adress range, Portrait
# set column address
        gpioa = ptr8(stm.GPIOA + stm.GPIO_ODR)
        gpiob = ptr16(stm.GPIOB + stm.GPIO_BSRRL)
        gpioa[0] = 0x2b         # command
        gpiob[1] = D_C | WR     # set C/D and WR low
        gpiob[0] = D_C | WR     # set C/D and WR high

        gpioa[0] = x1 >> 8  # high byte of x1
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = x1 & 0xff# low byte of x1
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = x2 >> 8  # high byte of x2
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = x2 & 0xff# low byte of x2
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again
# set row address            
        gpioa[0] = 0x2a         # command
        gpiob[1] = D_C | WR     # set C/D and WR low
        gpiob[0] = D_C | WR     # set C/D and WR high

        gpioa[0] = y1 >> 8  # high byte of x1
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = y1 & 0xff# low byte of x1
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = y2 >> 8  # high byte of x2
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = y2 & 0xff# low byte of x2
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = 0x2c         # Start data entry
        gpiob[1] = D_C | WR     # set C/D and WR low
        gpiob[0] = D_C | WR     # set C/D and WR high

    @staticmethod
    @micropython.viper        
    def setXY_L(x1: int, y1: int, x2: int, y2: int): ## set the adress range, Landscape
# set column address
        gpioa = ptr8(stm.GPIOA + stm.GPIO_ODR)
        gpiob = ptr16(stm.GPIOB + stm.GPIO_BSRRL)
        gpioa[0] = 0x2a         # command
        gpiob[1] = D_C | WR     # set C/D and WR low
        gpiob[0] = D_C | WR     # set C/D and WR high

        gpioa[0] = x1 >> 8  # high byte of x1
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = x1 & 0xff# low byte of x1
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = x2 >> 8  # high byte of x2
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = x2 & 0xff# low byte of x2
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again
# set row address            
        gpioa[0] = 0x2b         # command
        gpiob[1] = D_C | WR     # set C/D and WR low
        gpiob[0] = D_C | WR     # set C/D and WR high

        gpioa[0] = y1 >> 8  # high byte of x1
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = y1 & 0xff# low byte of x1
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = y2 >> 8  # high byte of x2
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = y2 & 0xff# low byte of x2
        gpiob[1] = WR       # set WR low. C/D still high
        gpiob[0] = WR       # set WR high again

        gpioa[0] = 0x2c         # Start data entry
        gpiob[1] = D_C | WR     # set C/D and WR low
        gpiob[0] = D_C | WR     # set C/D and WR high
#
# Assembler version of 
# Fill screen by writing size pixels with the color given in data
# data must be 3 bytes of red, green, blue
# The area to be filled has to be set in advance by setXY
# The speed is about 214 ns/pixel
#
    @staticmethod
    @micropython.asm_thumb
    def fillSCR_AS(r0, r1):  # r0: ptr to data, r1: number of pixels (3 bytes/pixel)
# set up pointers to GPIO
# r5: bit mask for control lines
# r6: GPIOA OODR register ptr
# r7: GPIOB BSSRL register ptr
        mov(r5, WR)
        movwt(r6, stm.GPIOA) # target
        add (r6, stm.GPIO_ODR)
        movwt(r7, stm.GPIOB)
        add (r7, stm.GPIO_BSRRL)
        ldrb(r2, [r0, 0])  # red   
        ldrb(r3, [r0, 1])  # green
        ldrb(r4, [r0, 2])  # blue
        b(loopend)

        label(loopstart)
        strb(r2, [r6, 0])  # Store red
        strb(r5, [r7, 2])  # WR low
#        nop()
        strb(r5, [r7, 0])  # WR high

        strb(r3, [r6, 0])  # store blue
        strb(r5, [r7, 2])  # WR low
        nop()
        strb(r5, [r7, 0])  # WR high
        
        strb(r4, [r6, 0])  # store blue
        strb(r5, [r7, 2])  # WR low
#        nop()
        strb(r5, [r7, 0])  # WR high

        label(loopend)
        sub (r1, 1)  # End of loop?
        bpl(loopstart)
#
# Assembler version of:
# Fill screen by writing size pixels with the data
# data must contains size triplets of red, green and blue data values
# The area to be filled has to be set in advance by setXY
# the speed is 266 ns for a byte triple 
#
    @staticmethod
    @micropython.asm_thumb
    def displaySCR_AS(r0, r1):  # r0: ptr to data, r1: is number of pixels (3 bytes/pixel)
# set up pointers to GPIO
# r5: bit mask for control lines
# r6: GPIOA OODR register ptr
# r7: GPIOB BSSRL register ptr
        mov(r5, WR)
        movwt(r6, stm.GPIOA) # target
        add (r6, stm.GPIO_ODR)
        movwt(r7, stm.GPIOB)
        add (r7, stm.GPIO_BSRRL)
        b(loopend)

        label(loopstart)
        ldrb(r2, [r0, 0])  # red   
        strb(r2, [r6, 0])  # Store red
        strb(r5, [r7, 2])  # WR low
        strb(r5, [r7, 0])  # WR high

        ldrb(r2, [r0, 1])  # pre green
        strb(r2, [r6, 0])  # store greem
        strb(r5, [r7, 2])  # WR low
        strb(r5, [r7, 0])  # WR high
        
        ldrb(r2, [r0, 2])  # blue
        strb(r2, [r6, 0])  # store blue
        strb(r5, [r7, 2])  # WR low
        strb(r5, [r7, 0])  # WR high

        add (r0, 3)  # advance data ptr

        label(loopend)
        sub (r1, 1)  # End of loop?
        bpl(loopstart)
# Assembler version of:
# Fill screen by writing size pixels with the data
# data must contains size packed duplets of red, green and blue data values
# The area to be filled has to be set in advance by setXY
# the speed is 266 ns for a byte pixel 
#
    @staticmethod
    @micropython.asm_thumb
    def displaySCR565_AS(r0, r1):  # r0: ptr to data, r1: is number of pixels (3 bytes/pixel)
# set up pointers to GPIO
# r5: bit mask for control lines
# r6: GPIOA OODR register ptr
# r7: GPIOB BSSRL register ptr
        mov(r5, WR)
        movwt(r6, stm.GPIOA) # target
        add (r6, stm.GPIO_ODR)
        movwt(r7, stm.GPIOB)
        add (r7, stm.GPIO_BSRRL)
        b(loopend)

        label(loopstart)

        ldrb(r2, [r0, 0])  # red   
        mov (r3, 0xf8)     # mask out lower 3 bits
        and_(r2, r3)        
        strb(r2, [r6, 0])  # Store red
        strb(r5, [r7, 2])  # WR low
        strb(r5, [r7, 0])  # WR high

        ldrb(r2, [r0, 0])  # pre green
        mov (r3, 5)        # shift 5 bits up to 
        lsl(r2, r3)
        ldrb(r4, [r0, 1])  # get the next 3 bits
        mov (r3, 3)        # shift 3 to the right
        lsr(r4, r3)
        orr(r2, r4)        # add them to the first bits
        mov(r3, 0xfc)      # mask off the lower two bits
        and_(r2, r3)
        strb(r2, [r6, 0])  # store green
        strb(r5, [r7, 2])  # WR low
        strb(r5, [r7, 0])  # WR high
        
        ldrb(r2, [r0, 1])  # blue
        mov (r3, 3)
        lsl(r2, r3)
        strb(r2, [r6, 0])  # store blue
        strb(r5, [r7, 2])  # WR low
        strb(r5, [r7, 0])  # WR high
        
        add (r0, 2)  # advance data ptr

        label(loopend)

        sub (r1, 1)  # End of loop?
        bpl(loopstart)
#
# Send a command and data to the TFT controller
# cmd is the command byte, data must be a bytearray object with the command payload,
# int is the size of the data
# For the startup-phase use this function.
#
    @staticmethod
    @micropython.viper        
    def tft_cmd_data(cmd: int, data: ptr8, size: int):
        gpioa = ptr8(stm.GPIOA + stm.GPIO_ODR)
        gpiob = ptr16(stm.GPIOB + stm.GPIO_BSRRL)
        gpioa[0] = cmd          # set data on port A
        gpiob[1] = D_C | WR     # set C/D and WR low
        gpiob[0] = D_C | WR     # set C/D and WR high
        for i in range(size):
            gpioa[0] = data[i]  # set data on port A
            gpiob[1] = WR       # set WR low. C/D still high
            gpiob[0] = WR       # set WR high again
#
# Assembler version of send command & data to the TFT controller
# data must be a bytearray object, int is the size of the data.
# The speed is about 120 ns/byte
#
    @staticmethod
    @micropython.asm_thumb
    def tft_cmd_data_AS(r0, r1, r2):  # r0: command, r1: ptr to data, r2 is size in bytes
# set up pointers to GPIO
# r5: bit mask for control lines
# r6: GPIOA OODR register ptr
# r7: GPIOB BSSRL register ptr
        movwt(r6, stm.GPIOA) # target
        add (r6, stm.GPIO_ODR)
        movwt(r7, stm.GPIOB)
        add (r7, stm.GPIO_BSRRL)
# Emit command byte
        mov(r5, WR | D_C)
        strb(r0, [r6, 0])  # set command byte
        strh(r5, [r7, 2])  # WR and D_C low
        strh(r5, [r7, 0])  # WR and D_C high
# now loop though data
        mov(r5, WR)
        b(loopend)

        label(loopstart)
        ldrb(r4, [r1, 0])  # load data   
        strb(r4, [r6, 0])  # Store data
        strh(r5, [r7, 2])  # WR low
        strh(r5, [r7, 0])  # WR high
        add (r1, 1)  # advance data ptr

        label(loopend)
        sub (r2, 1)  # End of loop?
        bpl(loopstart)
#
# Send a command to the TFT controller
#
    @staticmethod
    @micropython.viper        
    def tft_cmd(cmd: int):
        gpioa = ptr8(stm.GPIOA + stm.GPIO_ODR)
        gpiob = ptr16(stm.GPIOB + stm.GPIO_BSRRL)
        gpioa[0] = cmd          # set data on port A
        gpiob[1] = D_C | WR     # set C/D and WR low
        gpiob[0] = D_C | WR     # set C/D and WR high
#
# Assembler version of send data to the TFT controller
# data must be a bytearray object, int is the size of the data.
# The speed is about 120 ns/byte
#
    @staticmethod
    @micropython.asm_thumb
    def tft_write_data_AS(r0, r1):  # r0: ptr to data, r1: is size in Bytes
# set up pointers to GPIO
# r5: bit mask for control lines
# r6: GPIOA OODR register ptr
# r7: GPIOB BSSRL register ptr
        movwt(r6, stm.GPIOA) # target
        add (r6, stm.GPIO_ODR)
        movwt(r7, stm.GPIOB)
        add (r7, stm.GPIO_BSRRL)
        mov(r5, WR)
# and go, first test size for 0
        b(loopend)
 
        label(loopstart)
        ldrb(r3, [r0, 0])  # load data   
        strb(r3, [r6, 0])  # Store data
        strh(r5, [r7, 2])  # WR low
        strh(r5, [r7, 0])  # WR high
       
        add (r0, 1)  # advance data ptr
        label(loopend)
        sub (r1, 1)  # End of loop?
        bpl(loopstart)
#
# Assembler version of send a command byte and read data from to the TFT controller
# data must be a bytearray object, int is the size of the data.
# The speed is about 130 ns/byte
#
    @staticmethod
    @micropython.asm_thumb
    def tft_read_cmd_data_AS(r0, r1, r2):  
# r0: command, r1: ptr to data buffer, r2 is expected size in bytes
# set up pointers to GPIO
# r5: bit mask for control lines
# r6: GPIOA base register ptr
# r7: GPIOB BSSRL register ptr
        movwt(r6, stm.GPIOA) # target
        movwt(r7, stm.GPIOB)
        add (r7, stm.GPIO_BSRRL)
# Emit command byte
        movw(r5, WR | D_C)
        strb(r0, [r6, stm.GPIO_ODR])  # set command byte
        strh(r5, [r7, 2])  # WR and D_C low
        strh(r5, [r7, 0])  # WR and D_C high
# now switch gpioaa to input
        movw(r0, 0)
        strh(r0, [r6, stm.GPIO_MODER])
# now loop though data
        movw(r5, RD)
        b(loopend)

        label(loopstart)
        strh(r5, [r7, 2])  # RD low
        nop()              # short delay
        nop()
        ldrb(r4, [r6, stm.GPIO_IDR])  # load data   
        strh(r5, [r7, 0])  # RD high
        strb(r4, [r1, 0])  # Store data
        add (r1, 1)  # advance data ptr

        label(loopend)
        sub (r2, 1)  # End of loop?
        bpl(loopstart)
# now switch gpioaa back to input
        movw(r0, 0x5555)
        strh(r0, [r6, stm.GPIO_MODER])
#
# swap byte pairs in a buffer
# sometimes needed for picture data
#
    @staticmethod
    @micropython.asm_thumb
    def swapbytes(r0, r1):               # bytearray, len(bytearray)
        mov(r2, 1)  # divide loop count by 2
        lsr(r1, r2) # to avoid odd valued counter
        b(loopend)

        label(loopstart)
        ldrb(r2, [r0, 0])
        ldrb(r3, [r0, 1])
        strb(r3, [r0, 0])
        strb(r2, [r0, 1])
        add(r0, 2)

        label(loopend)
        sub (r1, 1)  # End of loop?
        bpl(loopstart)

#
# swap colors red/blue in the buffer
#
    @staticmethod
    @micropython.asm_thumb
    def swapcolors(r0, r1):               # bytearray, len(bytearray)
        mov(r2, 3)
        udiv(r1, r1, r2)  # 3 bytes per triple
        b(loopend)

        label(loopstart)
        ldrb(r2, [r0, 0])
        ldrb(r3, [r0, 2])
        strb(r3, [r0, 0])
        strb(r2, [r0, 2])
        add(r0, 3)

        label(loopend)
        sub (r1, 1)  # End of loop?
        bpl(loopstart)

