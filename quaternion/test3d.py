# test3d.py 3D objects created using quaternions

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

from math import pi
import gc
from quat import Rotator
import graph3d as g3d
from setup3d import *  # Hardware setup and colors

# Dict of display objects, each comprises a Shape
dobj = g3d.DisplayDict(setup(), pi/6, 5)  # Camera angle and z distance

dobj['axes'] = g3d.Axes(WHITE)  # Draw axes

def demo():
    dobj['cone'] = g3d.Cone(GREEN) * 0.7
    # Draw rectangle to check camera perspective
    square = (g3d.Square(YELLOW) -(0.5, 0.5, 0)) * 1.3
    rot = Rotator(pi/12, 1, 0, 0)
    dobj['perspective'] = square
    for _ in range(24):
        dobj['perspective'] @= rot
        dobj.show()
    rot = Rotator(pi/12, 0, 1, 0)
    for _ in range(24):
        dobj['perspective'] @= rot
        dobj.show()
    rot = Rotator(pi/12, 0, 0, 1)
    for _ in range(24):
        dobj['perspective'] @= rot
        dobj.show()
    dobj['perspective'] = g3d.Circle(RED) * 0.7 @ Rotator(pi/24, 0, 0, 1) # (1, 1, 0.5) for ellipse
    for _ in range(24):
        dobj['perspective'] @= rot
        dobj.show()
    del dobj['cone']
    del dobj['perspective']
    gc.collect()
    print('RAM free {} alloc {}'.format(gc.mem_free(), gc.mem_alloc()))
    dobj['perspective'] = g3d.Sphere(CYAN) * 0.5 - (0.5, 0.5, 0)
    rot = Rotator(pi/96, 1, 0, 0)
    gc.collect()
    print('RAM free {} alloc {}'.format(gc.mem_free(), gc.mem_alloc()))
    for _ in range(20):
        dobj['perspective'] += (0.025, 0.025, 0) # @= rot
        dobj.show()
    del dobj['perspective']

demo()
