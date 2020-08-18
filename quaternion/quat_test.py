# quat_test.py Test for quat.py

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2020 Peter Hinch

from math import sin, cos, isclose, pi, sqrt
from quat import *

print('Properties')
q1 = Quaternion(1, 2, 3, 4)
q1.w = 5
q1.x = 6
q1.y = 7
q1.z = 8
assert q1 == Quaternion(5, 6, 7, 8)
assert (q1.w, q1.x, q1.y, q1.z) == (5, 6, 7, 8)

# Numpy demo at https://quaternion.readthedocs.io/en/latest/README.html
print('Hamilton product')
q1 = Quaternion(1, 2, 3, 4)
q2 = Quaternion(5, 6, 7, 8)
q3 = Quaternion(-60, 12, 30, 24)
assert q3 == q1 * q2

print('Iterator protocol')
assert Quaternion(*q1) == q1
assert list(q1[1:]) == [2,3,4]
foo = iter(q1)
assert next(foo) == 1

print('Assign from tuple')
q1[1:] = (9, 10, 11)
assert list(q1[1:]) == [9, 10, 11]
q1[:] = (8, 9, 10, 99)
assert list(q1[:]) == [8, 9, 10, 99]

print('Assign from scalar')
q1[0] = 88
assert list(q1[:]) == [88, 9, 10, 99]

print('Negation')
q1 = Quaternion(1, 2, 3, 4)
q2 = Quaternion(-1, -2, -3, -4)
assert -q1 == q2

print('Comparison operators and unary +')
assert (q1 is +q1) == False
assert q1 == +q1
assert (q1 is q1.copy()) == False
assert q1 == q1.copy()
assert q1 >= q1.copy()
assert q1 <= q1.copy()
assert (q1 < q1.copy()) == False
assert (q1 > q1.copy()) == False

q2 = Quaternion(1, 2.1, 3, 4)
assert q2 > q1
assert q1 < q2
assert q2 >= q1
assert q1 <= q2
assert (q1 == q2) == False
assert q1 != q2

print('Scalar add')
q2 = Quaternion(5, 2, 3, 4)
assert q2 == q1 + 4

print('Scalar subtract')
q2 = Quaternion(-3, 2, 3, 4)
assert q2 == q1 - 4

print('Scalar multiply')
q2 = Quaternion(2, 4, 6, 8)
assert q2 == q1 * 2

print('Scalar divide')
q2 = Quaternion(0.5, 1, 1.5, 2)
assert q2 == q1/2

print('Conjugate')
assert q1.conjugate() == Quaternion(1, -2, -3, -4)

print('Inverse')
assert q1.inverse() * q1 == Quaternion(1, 0, 0, 0)

print('Multiply by tuple')
assert q1*(2,3,4) == Quaternion(0, 4, 9, 16)
assert q1*(4,5,6,7) == Quaternion(4, 10, 18, 28)

print('Add tuple')
assert q1 + (2,3,4) == Quaternion(0, 4, 6, 8)
assert q1 + (4,5,6,7) == Quaternion(5, 7, 9, 11)

print('abs(), len(), str()')
assert abs(Quaternion(2,2,2,2)) == 4
assert len(q1) == 4
assert str(q1) == 'w = 1.00 x = 2.00 y = 3.00 z = 4.00'

print('Rotation')
p = Vector(0, 1, 0)
r = Rotator(pi/4, 0, 0, 1)
rv = p @ r  # Anticlockwise about z axis
assert isclose(rv.w, 0, abs_tol=mdelta)
assert isclose(rv.x, -sin(pi/4), rel_tol=mdelta)
assert isclose(rv.y, sin(pi/4), rel_tol=mdelta)
assert isclose(rv.z, 0, abs_tol=mdelta)


p = Vector(1, 0, 0)
r = Rotator(-pi/4, 0, 0, 1)
rv = p @ r  # Clockwise about z axis
assert isclose(rv.w, 0, abs_tol=mdelta)
assert isclose(rv.x, sin(pi/4), rel_tol=mdelta)
assert isclose(rv.y, -sin(pi/4), rel_tol=mdelta)
assert isclose(rv.z, 0, abs_tol=mdelta)

p = Vector(0, 1, 0)
r = Rotator(-pi/4, 1, 0, 0)
rv = p @ r  # Clockwise about x axis
assert isclose(rv.w, 0, abs_tol=mdelta)
assert isclose(rv.x, 0, abs_tol=mdelta)
assert isclose(rv.y, sin(pi/4), rel_tol=mdelta)
assert isclose(rv.z, -sin(pi/4), rel_tol=mdelta)

print('Rotation using Euler angles')
# Tait-Brian angles DIN9300: I thought z axis is down towards ground.
# However https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
# and this implementation implies z is towards sky.
# https://github.com/moble/quaternion/wiki/Euler-angles-are-horrible

# Test heading
# Yaw/Heading: a +ve value is counter clockwise
p = Vector(1, 0, 0)  # x is direction of motion
r = Euler(pi/4, 0, 0)  # Heading 45°.
rv = p @ r
assert isclose(rv.w, 0, abs_tol=mdelta)
assert isclose(rv.x, sin(pi/4), rel_tol=mdelta)
assert isclose(rv.y, sin(pi/4), rel_tol=mdelta)
assert isclose(rv.z, 0, abs_tol=mdelta)

# Test pitch
# A +ve value is aircraft nose down i.e. z +ve
p = Vector(1, 0, 0)  # x is direction of motion
r = Euler(0, pi/4, 0)  # Pitch 45°.
rv = p @ r
assert isclose(rv.w, 0, abs_tol=mdelta)
assert isclose(rv.x, sin(pi/4), rel_tol=mdelta)
assert isclose(rv.y, 0, abs_tol=mdelta)
assert isclose(rv.z, -sin(pi/4), rel_tol=mdelta)  # Implies z is towards sky

# Test roll
# A +ve value is y +ve
p = Vector(0, 1, 0)  # x is direction of motion. Vector is aircraft wing
r = Euler(0, 0, pi/4)  # Roll 45°.
rv = p @ r
assert isclose(rv.w, 0, abs_tol=mdelta)
assert isclose(rv.x, 0, abs_tol=mdelta)
assert isclose(rv.y, sin(pi/4), rel_tol=mdelta)
assert isclose(rv.z, sin(pi/4), rel_tol=mdelta)  # Implies z is towards sky

print('euler() test')
r = Euler(pi/4, 0, 0)
assert isclose(euler(r)[0], pi/4, rel_tol=mdelta)
r = Euler(0, pi/4, 0)
assert isclose(euler(r)[1], pi/4, rel_tol=mdelta)
r = Euler(0, 0, pi/4)
assert isclose(euler(r)[2], pi/4, rel_tol=mdelta)

print('isrot() and isvec()')
assert Quaternion(0, 1, 2, 3).isvec()
assert not Quaternion(0, 1, 2, 3).isrot()
assert not Quaternion(1, 2, 3, 4).isvec()
q = Rotator(1, 1, 1, 1)
assert q.isrot()

print('to_angle_axis()')
t = Rotator(1, 1, 1, 1).to_angle_axis()
assert isclose(t[0], 1, rel_tol=mdelta)
for v in t[1:]:
    assert isclose(v, sqrt(1/3), rel_tol=mdelta)

s = '''
*** Standard tests PASSED. ***

The following test of reflected arithmetic operators will fail unless the
firmware was compiled with MICROPY_PY_REVERSE_SPECIAL_METHODS.
Runs on the Unix build.'''
print(s)

q1 = Quaternion(1, 2, 3, 4)
assert 10 + Quaternion(1, 2, 3, 4) == Quaternion(11, 2, 3, 4)
assert 1/q1 == q1.inverse()
assert 2 * q1 == q1 + q1
assert 1 - q1 == -q1 + 1

s = '''
Reverse/reflected operators OK.

*** All tests PASSED. ***
'''
print(s)
