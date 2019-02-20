# bitmap.py
# Ideas for non-allocating classes based around a bitmap. Three classes are
# presented:
# IntSet: this is a set which is constrained to accept only integers in
# a range 0 <= i <= maxval. Provides a minimal set of methods which can readily
# be expanded.
# SetByte: an even more minimal version of IntSet where the range is
# 0 <= i <=255.
# BoolList: A list of booleans. The list index is constrained to lie in range
# 0 <= i <= maxval.

class BitMap:
    def __init__(self, maxval):
        d, m = divmod(maxval, 8)
        self._ba = bytearray(d + int(m > 0))
        self._size = maxval

    def _check(self, i):
        if i < 0 or i >= self._size:
            raise ValueError('Index out of range')

    def _val(self, i):
        self._check(i)
        return (self._ba[i >> 3] & 1 << (i & 7)) > 0

    def _set(self, i):
        self._check(i)
        self._ba[i >> 3] |= 1 << (i & 7)

    def _clear(self, i):
        self._check(i)
        self._ba[i >> 3] &= ~(1 << (i &7))

    # Iterate through an IntSet returning members
    # Iterate through an IntList returning index value of True members
    def __iter__(self):
        for i in range(self._size):
            if self._val(i):
                yield i

    # if MyIntSet:  True unless set is empty
    # if MyBoolList: True if any element is True
    def __bool__(self):
        for x in self._ba:
            if x:
                return True
        return False


class IntSet(BitMap):
    def __init__(self, maxval=256):
        super().__init__(maxval)

    # if n in MyIntSet:
    def __contains__(self, i):
        self._check(i)
        return self._val(i)

    # MyIntSet.discard(n)
    def discard(self, i):
        self._clear(i)

    # MyIntSet.remove(n)
    def remove(self, i):
        if i in self:
            self.discard(i)
        else:
            raise KeyError(i)

    # MyIntSet.add(n)
    def add(self, i):
        self._set(i)

    # Generator iterates through set intersection. Avoids allocation.
    def intersec(self, other):
        for i in other:
            if i in self:
                yield i

class BoolList(BitMap):
    def __init__(self, maxval=256):
        super().__init__(maxval)

    # MyBoolList[n] = True
    def __setitem__(self, bit, val):
        self._set(bit) if val else self._clear(bit)

    # if MyBoolList[n]:
    def __getitem__(self, bit):
        return self._val(bit)

    # if False in MyBoolList:
    def __contains__(self, i):
        if i:
            for b in self._ba:
                if b:
                    return True
        else:
            for b in self._ba:
                if not b:
                    return True
        return False


# Minimal implementation of set for 0-255
class SetByte:
    def __init__(self):
        self._ba = bytearray(32)

    def __bool__(self):
        for x in self._ba:
            if x:
                return True
        return False

    def __contains__(self, i):
        return (self._ba[i >> 3] & 1 << (i & 7)) > 0

    def discard(self, i):
        self._ba[i >> 3] &= ~(1 << (i &7))

    def add(self, i):
        self._ba[i >> 3] |= 1 << (i & 7)

# Test for set intersection
bs = IntSet()
bs.add(1)
bs.add(2)
1 in bs
c = IntSet()
c.add(1)
c.add(4)
c.add(5)
g = bs.intersec(c)
next(g)
next(g)

