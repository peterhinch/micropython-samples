# test_imu.py Demo of cube being rotated by IMU data.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

from math import pi
from time import sleep
import gc
from quat import Rotator, euler
import graph3d as g3d
from setup3d import *  # Hardware setup and colors


def imu_demo():
    # Dict of display objects, each comprises a Shape
    dobj = g3d.DisplayDict(setup(), pi/6, 5)  # Camera angle and z distance
    dobj['axes'] = g3d.Axes(WHITE)  # Draw axes
    # Create a reference cube. Don't display.
    cube = g3d.Cube(RED, BLUE, GREEN) * (0.8, 0.8, 0.8) - (0.4, 0.4, 0.4)
    imuquat = Rotator()
    x = 0
    while True:
        dobj.show()
        sleep(0.1)
        imuquat[:] = imu.quaternion()  # Assign IMU data to Quaternion instance
        # imuquat.normalise() No need: BNo055 data is a rotation quaternion
        dobj['cube'] = cube @ imuquat
        x += 1
        if x == 10:
            x = 0
            print('Quat heading {0:5.2f} roll {2:5.2f} pitch {1:5.2f}'.format(*euler(imuquat)))
            print('IMU  heading {:5.2f} roll {:5.2f} pitch {:5.2f}'.format(*[x * pi/180 for x in imu.euler()]))
            gc.collect()
            print(gc.mem_free(), gc.mem_alloc())
    del dobj['cube']

imu_demo()

