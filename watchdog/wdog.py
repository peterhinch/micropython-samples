# Class for pybord watchdog timer
import stm, pyb

@micropython.asm_thumb
def clz(r0):
    clz(r0, r0) # return no. of leading zeros in passed integer

class wdog(object):
    def start(self, ms):
        assert ms <= 32768 and ms >= 1, "Time value must be from 1 to 32768mS"
        prescaler = 23 - clz(ms -1)
        div_value = ((ms << 3) -1) >> prescaler
        stm.mem16[stm.IWDG + stm.IWDG_KR] = 0x5555
        stm.mem16[stm.IWDG + stm.IWDG_PR] = (stm.mem16[stm.IWDG + stm.IWDG_PR] & 0xfff8) | prescaler
        stm.mem16[stm.IWDG + stm.IWDG_RLR] = (stm.mem16[stm.IWDG + stm.IWDG_RLR] & 0xf000) | div_value
        stm.mem16[stm.IWDG + stm.IWDG_KR] = 0xcccc
    def feed(self):
        stm.mem16[stm.IWDG + stm.IWDG_KR] = 0xaaaa

def test():
    led = pyb.LED(2)
    led1 = pyb.LED(3)
    dog = wdog()
    dog.start(1000)
    for x in range(10):
        led.toggle()
        pyb.delay(500)
        dog.feed()
    dog.start(4000)
    for x in range(20):
        led1.toggle()
        pyb.delay(500)
