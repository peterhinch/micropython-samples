# ui.py Base classes and utilities for TFT GUI

CIRCLE = 1
RECTANGLE = 2
CLIPPED_RECT = 3

def get_stringsize(s, font):
    hor = 0
    for c in s:
        _, vert, cols = font.get_ch(ord(c))
        hor += cols
    return hor, vert

def print_centered(tft, x, y, s, color, font):
    length, height = get_stringsize(s, font)
    tft.setTextStyle(color, None, 2, font)
    tft.setTextPos(x - length // 2, y - height // 2)
    tft.printString(s)

# Base class for touch-enabled classes.
class touchable(object):
    touchlist = []
    objtouch = None

    @classmethod
    def touchtest(cls): # Singleton thread tests all touchable instances
        mytouch = cls.objtouch
        while True:
            yield
            if mytouch.ready:
                x, y = mytouch.get_touch()
                for obj in cls.touchlist:
                    if obj.enabled:
                        obj.touched(x, y)
            elif not mytouch.touched:
                for obj in cls.touchlist:
                    obj.untouched()

    def __init__(self, objsched, objtouch):
        touchable.touchlist.append(self)
        self.enabled = True # Available to user/subclass
        if touchable.objtouch is None: # Initialising class and thread
            touchable.objtouch = objtouch
            objsched.add_thread(self.touchtest()) # One thread only
