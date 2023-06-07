# demo_parse2d.py Parse args for item access dunder methods for a 2D array.

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023 Peter Hinch

from parse2d import do_args

class int2D:
    def __init__(self, nrows, ncols):
        self.nrows = nrows
        self.ncols = ncols
        self.cells = [0] * nrows * ncols

    def __getitem__(self, *args):
        indices = do_args(args, self.nrows, self.ncols)
        for i in indices:
            yield self.cells[i]

    def __setitem__(self, *args):
        x = args[1]  # Value
        indices = do_args(args[: -1], self.nrows, self.ncols)
        for i in indices:
            if isinstance(x, int):
                self.cells[i] = x
            else:
                try:
                    z = next(x)  # Will throw if not an iterator or generator
                except StopIteration:
                    pass  # Repeat last value
                self.cells[i] = z

demo = int2D(10, 10)
demo[0, 1:5] = iter(range(10, 20))
print(next(demo[0, 0:]))
demo[0:, 0] = iter((66,77,88))
print(next(demo[0:, 0]))
demo[8, 8] = 42
#demo[8, 10] = 9999  # Index out of range
demo[2:5, 2:5] = iter(range(50, 60))
for row in range(10):
    print(*demo[row, 0:])


# 1D addressing
# g = do_args((30,), 10, 10)  # 30
# g = do_args((slice(30, 34),), 10, 10)  # 30 31 32 33
# 2D addressing
# g = do_args(((1, slice(0, 9)),), 10, 10)  # 10 11 12 ... 18
# g = do_args(((1, 2),), 10, 10)  # 10
