# 1. 3D Rotation (quaternions without the maths)

This repo contains a `Quaternion` class and a rudimentary 3D vector graphics
module. The aim is to present quaternions as an efficient way to manipulate 3d
objects and data from inertial measurement units (IMUs). As such they have
applications in 3D graphics and robotics.

Quaternions have a reputation for being mathematically difficult. This repo
aims to make them usable with no mathematics beyond a basic grasp of Cartesian
(x, y, z) coordinates. They are actually easier to use than the traditional
Euler angles (heading, pitch and roll), and avoid the mathematical problems
associated with Euler angles.

The following fragment shows a classic demo where a wireframe cube rotates to
match rotations of an IMU:

```python
# dobj is a display list, imu is a BNo055
# Create a unit cube, scale to 0.8 and move to centre on origin
cube = Cube(RED, BLUE, GREEN) * ( 0.8, 0.8, 0.8) - (0.4, 0.4, 0.4)
rot = Rotator()  # Rotation quaternion
while True:
    rot[:] = imu.quaternion()  # Read IMU and assign to Rotator
    dobj['cube'] = cube @ rot  # Rotate cube to match IMU
    dobj.show()  # Display on screen
    time.sleep(0.1)
```
In this instance the IMU (a Bosch BNO055) produces quaternion data. Similar
data may be computed from other IMUs by means of the
[sensor fusion module](https://github.com/micropython-IMU/micropython-fusion).

Section 2 of this doc aims to describe basic usage of the repo with an absolute
minimum of mathematics. Section 3 provides more detail for those wishing to
expand the usage of quaternions beyond basic 3D transformations.

The 3D graphics is of demo quality: it is not a serious attempt at a graphics
library. Its speed demonstrates that a 3D graphics library should be written in
C for adequate performance. It also has known limitations and shortcomings. Its
purpose is to prove and demonstrate the quaternion handling: all graphics
elements use quaternions in their definitions.

# 2 Introduction

The graphics module enables various wireframe objects to be rendered from a
"camera" view with an illusion of perspective. Objects may be moved, scaled,
distorted and rotated using arithmetic operators. Thus if `cube` is an instance
of a `Cube`,  
`cube + (0, 0.2, 0)` will move it along the Y axis.  
`cube * (1, 0.2, 0.2)` will turn it into a cuboid.  
`cube @ Rotator(0.1, 1, 0, 0)` will rotate it around the X axis by 0.1 radians.
Any axis may be specified.

I wrote this to experiment with and test `quat.py` rather than as a serious
attempt at 3D graphics. It is written in Python so speed is an issue. Realtime
display of orientation is feasible. Playable games aren't. A C port would be
awesome.

## 2.1 Files

The library provides the following files which should be copied to the target's
filesystem.  
Core files:  
 1. `quat.py` Provides classes for creating and rotating points.
 2. `graph3d.py` Provides wireframe 3D graphics classes.

Setup files. There should be a file `setup3d.py` defining graphics and
(optionally) IMU hardware:
 1. `setup3d.py` Assumes an SSD1351 OLED display and BNo055 IMU.
 2. `setup3d_lcd160cr` Setup file for the official LCD. On the target rename to
 `setup3d.py` to use. Uncomment the BNo055 code if required.

Demo scripts:  
 1. `test3d.py` Test script displays various moving objects.
 2. `test_imu.py` Wireframe cube moves to match IMU data.

Test:
 1. `quat_test.py` Unit test for `quat.py`. Run under Unix build.

## 2.2 Display hardware

The `setup3d.py` script assumes an SSD1351 128*128 bit display such as
[this one](https://www.adafruit.com/product/1431) - it may be adapted for other
displays. The driver is [here](https://github.com/peterhinch/micropython-nano-gui/blob/master/drivers/ssd1351/ssd1351_16bit.py)

The setup file must define the following data values:  
 1. Color values in a format suitable for its `line` and `fill` functions (see
 below).
 2. `DIMENSION = 64` This defines the number of pixels moved by a value of 1.0.
 By default a 128*128 pixel space represents values defined by -1.0 <= v <= 1.0.
 3. `imu` Required for `test_imu`. An inertial measuring unit. It must have a
 `quaternion` method returning `w`, `x`, `y`, `z`. It may also have an `euler`
 method returning `heading`, `roll`, `pitch`. If `euler` is unsupported comment
 out the line in the test script that reports on those values.

The setup file must define these functions:  
 1. `fill(color)` Clear the display when called with `BLACK`.
 2. `line(xs, ys, xe, ye, color)` Draw a line with args specified in absolute
 pixels.
 3. `show()` Display all lines.

By default the `imu` object is a BNo055 however it can be created for other IMU
types by means of the
[sensor fusion module](https://github.com/micropython-IMU/micropython-fusion)
which provides access to quaternion, heading, pitch and roll.

The `test_imu` rotating cube demo uses the
[Adafruit BNO055 breakout](https://www.adafruit.com/product/2472). The driver
comprises these files:
[bno055.py](https://github.com/micropython-IMU/micropython-bno055/blob/master/bno055.py)
and [bno055_base.py](https://github.com/micropython-IMU/micropython-bno055/blob/master/bno055_base.py).

The `test3d.py` script ends by drawing a moving sphere. This is RAM-intensive
and will cause a memory error unless run on a Pyboard D.

## 2.3 Getting started

The module `quat.py` provides functions producing two types of object:
 1. A `Point` representing a point (x, y, z) in 3D space.
 2. A `Rotator` representing an axis and an angle of rotation.

The following fragment instantiates a point and rotates it 45° around the X
axis:
```python
from quat import Point, Rotator
from math import pi
point = Point(0, 0, 1)
rot = Rotator(pi/4, 1, 0, 0)  # Rotate 45° around x axis
point @= rot  # perform the rotation in-place
```
This can be extended to wireframe shapes, which can also be moved and scaled.
Moving is done by adding a 3-tuple representing `(dx, dy, dz)` distances to
move. Scaling may be done by multiplying by a value to make the object larger
or smaller while preserving its shape. Alternatively the object can be
multiplied by a 3-tuple to scale it differently along each axis:
```python
from quat import Rotator
from math import pi
from graph3d import Cube, DisplayDict, Axes
from setup3d import *  # Hardware setup and colors

# Objects for display are put in a `DisplayDict` which specifies the camera
# location and distance for the perspective view
dobj = DisplayDict(setup(), pi/6, 5)
dobj['axes'] = Axes(WHITE)  # Show x, y, z axes
# By default the cube is from the origin to (1.0, 1.0, 1.0). Scale it
# to length of side 0.8 and centre it at origin
cube = Cube(RED, BLUE, GREEN) * (0.8, 0.8, 0.8) - (0.4, 0.4, 0.4)
# Rotate 45° around an axis from (0, 0, 0) to (1, 1, 1)
rot = Rotator(pi/4, 1, 1, 1)
dobj['cube'] = cube @ rot
dobj.show()  # Update the physical display
```

## 2.4 The quat module

This provides the following:
 1. `Point` Represents a point in space. Constructor takes `x`, `y` and `z`
 floating point args where `-1.0 <= arg <= 1.0`.
 2. `Rotator` An object which can rotate `Point` instances around an axis. The
 axis is defined by a line from the origin to a point. Constructor args:
 `theta=0, x=0, y=0, z=0` where `theta` is the amount of rotation in radians.
 3. `Euler` Returns a `Rotator` defined by Euler angles. Constructor args:
 `heading, pitch, roll` specified in radians.

## 2.5 The 3D graphics module

Code in this module uses `Point` and `Rotator` instances to create graphics
primitives. Constructors create unit sized objects at a fixed location: objects
may be scaled, distorted, moved or rotated prior to display.

In all cases `color` is a color value defined in `setup3d.py`.

The module provides the following objects:
 1. `Line` Constructor args: `p0, p1, color` where `p0` and `p1` are `Point`
 instances.
 2. `Axes` Draws the three axes. Constructor arg: `color`.
 3. `Square` Draws a unit square located in the +ve quadrant. Arg: `color`.
 4. `Circle` Unit circle centred on origin. Args: `color`, `segments=12`.
 5. `Sphere` Unit sphere centred on origin. Args: `color`, `segments=12`.
 6. `Cone` Unit cone with apex at origin. Args: `color`, `segments=12`.
 7. `Cube` Unit cube in +ve quadrant. Args: `color, front=None, sides=None`.
 These represent color values. If color values are passed it allows front, back
 and sides to have different colors enabling orientation to readily be seen.
 8. `DisplayDict` A dictionary of objects for display.

The `Sphere` object is demanding of RAM. I have only succeeded in displaying it
on Pyboard D hosts (SF2 and SF6).

### 2.5.1 The DisplayDict class

This enables objects to be transformed or deleted at run time, and provides for
display refresh.

Constructor:
This takes the following args: `ssd, angle, distance`. `ssd` is the display
instance. The other args specify the camera angle and distance. Typical values
are pi/6 and 5.

Method:
 1. `show` Clears and refreshes the display.

# 3. Quaternions

The mathematics of quaternions are interesting. I don't propose to elaborate on
it here as there are many excellent online texts and demonstrations. The ones I
found helpful are listed [below](./quaternions.md#Appendix 1: references). The
following summarises the maths necessary to read the rest of this section; it
uses Python notation rather than trying to represent mathematical equations.

A quaternion comprises four numbers `w, x, y, z`. These define an instance  
`q = w + x*i + y*j + z*k` where `i, j, k` are square roots of -1 as per
Hamilton's equation:  
`i**2 == j**2 == k**2 == i*j*k == -1`

A quaternion's `w` value is its scalar part, with `x`, `y` and `z` defining its
vector part. A quaternion with `w == 0` is a vector quaternion and is created
by the `Vector` or `Point` constructors in the code. It may be regarded as a
point in space or a vector between the origin and that point, depending on
context.

Quaternions have a magnitude represented by  
`magnitude = sqrt(sum((w*w + x*x + y*y + z*z)))` This may be accessed by
issuing `magnitude = abs(q)`.

A quaternion whose vector part is 0 (i.e. x, y, z are 0) is a scalar. If w is 1
it is known as a unit quaternion.

A quaternion with a nonzero vector part and a magnitude of 1 is a rotation
quaternion. These may be produced by the `Rotator` constructor. If its `x y z`
values are considered as a vector starting at the origin, `w` represents the
amount of rotation about that axis.

Multiplication of quaternions is not commutative: in general  
`q1 * q2 != q2 * q1`  
Multiplication of quaternions produces a Hamilton product.

Quaternions have a conjugate analogous to the conjugate of a complex. If `q` is
a quaternion its conjugate may be found with:  
`conj = Quaternion(q.w, -q.x, -q.y, -q.z)` In code `conj = q.conjugate()`.

A `Point` (vector quaternion) `P` may be rotated around an arbitrary axis by
defining a rotation quaternion `R` and performing the following  
`P = R * P * conjugate(P)`  
This is performed using the matmul `@` operator, e.g.:
`P @= R`
The use of this operator allows rotations to be used in arithmetic expressions.

Division of quaternions is covered in [section 3.9](./QUATERNION.md#39-division).

## 3.1 The Quaternion class

This uses Python special ("dunder" or magic) methods to enable arithmetic and
comparison operators and to support the iterator protocol.

```python
q = Quaternion(5, 6, 7, 8)
q2 = q * 2
q2 = 2 * q  # See NOTE on operand ordering
print(q * 2 + (20, 30, 40))
```
Special constructors are provided to produce vector and rotation quaternions,
with the class constructor enabling arbitrary quaternions to be created.

NOTE: Unless firmware is compiled with `MICROPY_PY_REVERSE_SPECIAL_METHODS`
arithmetic expressions should have the quaternion on the left hand side. Thus
`q * 2` will work, but `2 * q` will throw an exception on such builds. See
[build notes](./QUATERNION.md#313-build-notes).

## 3.2 Quaternion constructors

There are constructors producing vector and rotation quaternions. In addition
the actual class constructor enables any quaternion to be instantiated.

### 3.2.1 Vector or Point

These take 3 args `x, y, z`. The constructor returns a vector quaternion with
`w == 0`.

### 3.2.2 Rotator

This takes 4 args `theta=0, x=0, y=0, z=0`. It returns a rotation quaternion
with magnitude 1. The vector from the origin to `x, y, z` is the axis of
rotation and `theta` is the angle in radians.

### 3.2.3 Euler

This takes 3 args `heading, pitch, roll` and returns a rotation quaternion. It
aims to be based on Tait-Bryan angles, however this implementation assumes that
positive `z` is upwards: some assume it is downwards. Euler angles have more
standards than you can shake a stick at:
[Euler angles are horrible](https://github.com/moble/quaternion/wiki/Euler-angles-are-horrible).

### 3.2.4 The Quaternion constructor

This takes four args `w=1, x=0, y=0, z=0`. The default is the unit quaternion.

## 3.3 Quaternion properties

Quaternion instances support `w, x, y, z` read/write properties.

## 3.4 Iterator protocol

Quaternion instances support this. Thus
```python
q = Quaternion(5, 6, 7, 8)
print(q[1:])  # Prints the vector part array('f', [6.0, 7.0, 8.0])
q[1:] = (9, 10, 11)
print(q[1:])  # array('f', [9.0, 10.0, 11.0])
for x in q:
    print(x)  # It is possible to iterate over the elements
```

## 3.5 abs() len() and str()

```python
q = Quaternion(5, 6, 7, 8)
abs(q)  # Returns its magnitude 13.19090595827292
len(q)  # Always 4
str(q)  # 'w = 5.00 x = 6.00 y = 7.00 z = 8.00'
```

## 3.6 Comparison operators

Two `Quaternion` instances are equal if all their `w, x, y, z` values match.
Otherwise their maginitudes are compared. Thus `q1 == q2` tests for exact
equality. `q1 >= q2` will return `True` if they are exactly equal or if 
`abs(q1) > abs(q2)`.

The test for "exact" equality is subject to the issues around comparison of
floating point numbers. The `math.isclose` method is used with a value of 0.001
(0.1%). This may be adjusted (`mdelta` and `adelta` variables).

## 3.7 Addition and subtraction

A `Quaternion` instance may have the following types added to it or subtracted
from it, resulting in a new `Quaternion` instance being returned.
 1. Another Quaternion.
 2. A scalar. This modifies the `w` value.
 3. A 4-tuple or list: modifies `w, x, y, z`.
 4. A 3-tuple or list: modifies the vector part `x, y, z` and sets the scalar
 part `w` to zero returning a vector quaternion. Intended for moving `Point`
 instances.

The typical application of addition of a 3-tuple is the movement of a `Point`.

## 3.8 Multiplication

A `Quaternion` instance may be mutliplied by the following types resulting in a
new `Quaternion` instance being returned.
 1. Another Quaternion. Returns the Hamilton product. Multiplication is not
 commutative.
 2. A scalar. This multiplies `w, x, y, z`.
 3. A 4-tuple or list: multiplies `w, x, y, z` by each element.
 4. A 3-tuple or list: multiplies the vector part `x, y, z` by each element and
 sets the scalar part `w` to zero returning a vector quaternion. Intended for
 scaling `Point` instances.

Multiplication by a scalar or a tuple is commutative. If a list of points
comprises a shape, multiplication by a scalar can be used to resize the shape.
Multiplication by a 3-tuple can transform a shape, for example changing a cube
to a cuboid.

## 3.9 Division

It is possible to divide a scalar by a quaternion: `1/q` produces the inverse
of quaternion `q`. This may also be acquired by issuing `q.inverse()`. The
following statements are equivalent:
```python
q1 = (1, 2, 3) / Quaternion(4, 5, 6, 7)
q2 = Quaternion(4, 5, 6, 7).inverse() * (1, 2, 3)
```
Note that multiplication of a quaternion by a scalar or by a tuple is
commutative, while multiplication of quaternions is not. Consequently the
notation `p/q` where `p` and `q` are quaternions is ambiguous because it is
unclear whether it corresponds to `p*q.inverse()` or `q.inverse()*p`. The
`Quaternion` class disallows this, raising a `ValueError`.

See [build notes](./QUATERNION.md#313-build-notes).

## 3.10 Rotation

Rotations are not commutative. Place two books side by side. Rotate one 90°
clockwise, then flip it 180° about an axis facing away from you. Repeat with
the other book in the opposite order.

Rotation is implemented using the matmul `@` operator. This is normally applied
with a `Point` or `Vector` quaternion on the LHS and a `Rotator` (rotation
quaternion) on the RHS.
```python
point = Point(1, 0, 0)
rot = Rotator(pi/6, 0, 1, 0)
new_point = point @ rot
point @= rot  # Rotate in place
```
There is an `rrot` method performing order-reversed rotation:
```
    def __matmul__(self, rot):
        return rot * self * rot.conjugate()

    def rrot(self, rot):
        return rot.conjugate() * self * rot
```

### 3.10.1 Rotation direction

Consider these `Rotator` instances:
```python
rotx = Rotator(0.1, 1, 0, 0)  # About X
roty = Rotator(0.1, 0, 1, 0)  # Y
rotz = Rotator(0.1, 0, 0, 1)  # Z
point = Point(1, 1, 1)
```
Applying a rotator with a positive angle to a point will cause anticlockwise
rotation as seen from a positive location on the relevant axis looking towards
the origin. This is analogous to 2d rotation on the complex plane where
multiplying by (say) 1 + 1j will produce an anticlockwise rotation.

## 3.11 Other methods

 1. `conjugate` No args, returns a new `Quaternion` being its conjugate.
 2. `inverse` No args, returns a new `Quaternion` being its inverse.
 3. `to_angle_axis` No args. Intended for rotation quaternions. Returns
 `[theta, x, y, z]` where `theta` is the rotation angle and the vector from the
 origin to `x, y, z` is the axis.
 4. `copy` No args. Returns a copy of the instance.
 5. `normalise` Aims to produce a rotation quaternion: returns a new quaternion
 instance whose maginitude is 1. Intended to compensate for any accumulation of
 errors in a rotation quaternion.
 6. `isvec` No args. Returns `True` if it is a vector quaternion i.e. `w == 0`.
 7. `isrot` No args. Returns `True` if it is a rotation quaternion i.e.
 `abs(q) == 1`.

## 3.12 The euler function

This takes a `Quaternion` instance as an arg. Returns `heading, pitch, roll`.
See [section 3.2.3](./quaternions.md#323-euler).

## 3.13 Build notes

Not all ports provide `math.isclose` and the reverse special methods. To some
extent the lack of reverse special methods can be worked around by changing the
operand order in expressions to ensure that the left hand side of a binary
operator is a `Quaternion` instance. This cannot be applied to division and the
`.inverse()` method must be used.

Bettrr, edit `ports/port/mpconfigport.h` to ensure these lines are included:
```C
#define MICROPY_PY_MATH_ISCLOSE     (1)

#define MICROPY_PY_ALL_SPECIAL_METHODS (1)  // May already be present
#define MICROPY_PY_REVERSE_SPECIAL_METHODS (1)  // Add this line
```
and rebuild the firmware.

# Appendix 1: references

[Visalising quaternions](https://www.youtube.com/watch?v=d4EgbgTm0Bg)
[Visalising quaternions - interactive](https://eater.net/quaternions/video/doublecover)
[Using Quaternion to Perform 3D rotations](https://www.cprogramming.com/tutorial/3d/uses.html)
The Wikipedia article is maths-heavy.
[Wikpedia](https://en.wikipedia.org/wiki/Quaternion)
The following ref is good, but its formula for multiplication reverses the
order of its arguments compared to the other sources. The q1*q2 from
other sources corresponds to q2*q1 from this paper.
[Rotation Quaternions, and How to Use Them](http://danceswithcode.net/engineeringnotes/quaternions/quaternions.html)

From the youtube video: p -> (q2(q1pq1**-1)q2**-1)

Why to use quaternions rather than [Euler angles](https://github.com/moble/quaternion/wiki/Euler-angles-are-horrible).
