from machine import Pin, SPI
from time import sleep_ms


cs = Pin(17, Pin.OUT, value=1)  # Ensure CS/ is False before we try to receive.
pin_miso = Pin(16, Pin.IN)  # Not used: keep driver happy
pin_sck = Pin(18, Pin.OUT, value=0)
pin_mosi = Pin(19, Pin.OUT, value=0)

spi = SPI(0, baudrate=10_000_000, sck=pin_sck, mosi=pin_mosi, miso=pin_miso)


def send(obuf):
    cs(0)
    spi.write(obuf)
    # sleep_ms(10)
    cs(1)
    # print("sent", obuf)
    sleep_ms(1000)


while True:
    send("The quick brown fox")
    send("jumps over the lazy dog.")
