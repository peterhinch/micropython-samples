# encoders_test.py

from time import sleep
from machine import Pin

# YOU MAY TEST
#from machine import Encoder  # encoder based on hardware counters from ESP32, mimxrt, STM32 ports
#OR
from encoder_state import Encoder
# OR
#from encoder_portable import Encoder
# OR
#from encoder_timed import EncoderTimed as Encoder
# OR
#from encoder import Encoder  # suitable for old Pyboard-specific version

#Encoder pins
ENCODER_DATA = 16  # as input A
ENCODER_CLK = 17  # as input B
ENCODER_SW = 18  # as "index" input, typically labeled Z

PPR = 30  # pulses per revolution of the encoder shaft

try:
    data = Pin(ENCODER_DATA, mode=Pin.IN, pull=Pin.PULL_UP)
    clk = Pin(ENCODER_CLK, mode=Pin.IN, pull=Pin.PULL_UP)
    sw = Pin(ENCODER_SW, mode=Pin.IN, pull=Pin.PULL_UP)
    print('data as A', data, data.value())
    print('clk as B', clk, clk.value())
    print('sw as Z', sw, sw.value())

    enc = Encoder(data, clk, scale=360 / PPR)  # degreses
    #enc = Encoder(data, clk, scale=2*3.141592/PPR)  # radians
    #enc = Encoder(data, clk, scale=1/PPR)  # rotations
    print(enc)

    _data = None
    _clk = None
    _sw = None
    _value = None

    while True:
        __data = data.value()
        __clk = clk.value()
        __sw = sw.value()
        __value = enc.value()
        _position = enc.position()

        if (_data != __data) or (_clk != __clk) or (_sw != __sw) or (_value != __value):
            _data = __data
            _clk = __clk
            _sw = __sw
            _value = __value

            if _sw == 0:
                enc.set_value(PPR * round(enc.value() / PPR))
                # enc.set_value(0)
                # enc.position(0)

            print("data={}, clk={}, sw={}, value={:10}, position={:13.2f}".format(_data, _clk, _sw, _value, _position), end='        \r')
            # enc.rate(),

        sleep(0.1)

finally:
    try:
        enc.deinit()
    except:
        pass
