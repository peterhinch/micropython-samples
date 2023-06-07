# Access a list or array as a 2D array

The `parse2d` module provides a generator function `do_args`. This enables a
generator to be instantiated which maps one or two dimensional address args
onto index values. These can be used to address any object which can be
represented as a one dimensional array including arrays, bytearrays, lists or
random access files. The aim is to simplify writing classes that implement 2D
arrays of objects - specifically writing `__getitem__` and `__setitem__`
methods whose addressing modes conform with Python conventions.

Addressing modes include slice objects; sets of elements can be accessed or
populated without explicit iteration. Thus, if `demo` is an instance of a user
defined class, the following access modes might be permitted:
```python
demo = MyClass(10, 10)  # Create an object that can be viewed as 10 rows * 10 cols
demo[8, 8] = 42  # Populate a single cell
demo[0:, 0] = iter((66, 77, 88))  # Populate a column
demo[2:5, 2:5] = iter(range(50, 60))  # Populate a rectangular region.
print(sum(demo[0, 0:]))  # Sum a row
for row, _ in enumerate(demo[0:, 0]):
    print(*demo[row, 0:])  # Size- and shape-agnostic print
```
The object can also be accessed as a 1D list. An application can mix and match
1D and 2D addressing as required:
```python
demo[-1] = 999  # Set last element
demo[-10: -1] = 7  # Set previous 9 elements
```
The focus of this module is convenience, minimising iteration and avoiding
error-prone address calculations. It is not a high performance solution. The
module resulted from guidance provided in
[this discussion](https://github.com/orgs/micropython/discussions/11611).

# The do_args generator function

This takes the following args:
 * `args` A 1- or 2-tuple. In the case of a 1-tuple (1D access) the element is
 an int or slice object. In the 2-tuple (2D) case each element can be an int or
 a slice.
 * `nrows` No. of rows in the array.
 * `ncols` No. of columns.

This facilitates the design of `__getitem__` and `__setitem__`, e.g.
```python
    def __getitem__(self, *args):
        indices = do_args(args, self.nrows, self.ncols)
        for i in indices:
            yield self.cells[i]
```
The generator is agnostic of the meaning of the first and second args: the
mathematical `[x, y]` or the graphics `[row, col]` conventions may be applied.
Index values are `row * ncols + col` or `x * ncols + y` as shown by the
following which must be run on CPython:
```python
>>> g = do_args(((1, slice(0, 9)),), 10, 10)
>>> for index in g: print(f"{index}  ", end = "")
10  11  12  13  14  15  16  17  18  >>> 
```
Three argument slices are supported:
```python
>>> g = do_args(((1, slice(8, 0, -2)),), 10, 10)
>>> for index in g: print(f"{index}  ", end = "")
... 
18  16  14  12  >>> 
```
# Addressing

The module aims to conform with Python rules. Thus, if `demo` is an instance of
a class representing a 10x10 array,
```python
print(demo[0, 10])
```
will produce an `IndexError: Index out of range`. By contrast
```python
print(demo[0, 0:100])
```
will print row 0 (columns 0-9)without error. This is analogous to Python's
behaviour with list addressing:
```python
>>> l = [0] * 10
>>> l[10]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
IndexError: list index out of range
>>> l[0:100]
[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
>>> 
```
# Class design

## __getitem__()

RAM usage can be minimised by having this return an iterator. This enables
usage such as `sum(arr[0:, 1])` and minimises RAM allocation.

## __setitem__()

The semantics of the right hand side of assignment expressions is defined in
the user class. The following uses a `list` as the addressable object.
```python
from parse2d import do_args

class MyIntegerArray:
    def __init__(self, nrows, ncols):
        self.nrows = nrows
        self.ncols = ncols
        self.cells = [0] * nrows * ncols

    def __getitem__(self, *args):
        indices = do_args(args, self.nrows, self.ncols)
        for i in indices:
            yield self.cells[i]

    def __setitem__(self, *args):
        value = args[1]
        indices = do_args(args[: -1], self.nrows, self.ncols)
        for i in indices:
            self.cells[i] = value
```
The `__setitem__` method is minimal. In a practical class `value` might be a
`list`, `tuple` or an object supporting the iterator protocol.

# The int2D demo

RHS semantics differ from Python `list` practice in that you can populate an
entire row with
```python
demo[0:, 0] = iter((66, 77, 88))
```
If the iterator runs out of data, the last item is repeated. Equally you could
have
```python
demo[0:, 0] = 4
```
The demo also illustrates the case where `__getitem__` returns an iterator.
