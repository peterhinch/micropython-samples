# check_mid.py Check a sequence of incrementing message ID's.

# Released under the MIT licence. See LICENSE.
# Copyright (C) Peter Hinch 2020

# For use in test scripts: message ID's increment without bound rather
# than modulo N. Assumes message ID's start with 0 or 1.

# Missing and duplicate message counter. Handles out-of-order messages.
# Out of order messages will initially be missing to arrive later.
# The most recent n message ID's are therefore not checked. If a
# message is missing after n have been received, it is assumed lost.

class CheckMid:
    def __init__(self, buff=5):
        self._buff = buff
        self._mids = set()
        self.miss = 0  # Count missing message ID's
        self.dupe = 0  # Duplicates
        self.oord = 0  # Received out of order
        self.bcnt = 0  # Reboot count

    def __call__(self, mid):
        mids = self._mids
        if mid <= 1 and len(mids) > 1:  # Target has rebooted
            self._mids.clear()
            self.miss = 0
            self.dupe = 0
            self.oord = 0
            self.bcnt += 1
        if mid in mids:
            self.dupe += 1
        elif mids and mid < max(mids):
            self.oord += 1
        mids.add(mid)
        if len(mids) > self._buff:
            oldest = min(mids)
            mids.remove(oldest)
            self.miss += min(mids) - oldest - 1

# Usage/demo
#cm = CheckMid()
#s1 = (1,2,3,4,5,8,9,10,11,12,13,17,17,16,18,19,20,21,22,23,24,29,28,27,26,30,31,32,33,34,35,36)
#for x in s1:
    #cm(x)
    #print(cm.dupe, cm.miss, cm.oord, cm.bcnt)
