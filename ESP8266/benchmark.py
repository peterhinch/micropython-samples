# benchmark.py Simple benchmark for umqtt.simple
# Assumes simple.py (from micropython-lib) is copied to ESP8266
# Outcome with mosquitto running on a Raspberry Pi on wired network,
# Wemos D1 Mini running on WiFi: echo received in max 154 ms min 27 ms

import ubinascii
from simple import MQTTClient
from machine import unique_id
from utime import sleep, ticks_ms, ticks_diff

def tdiff():
    new_semantics = ticks_diff(2, 1) == 1
    def func(old, new):
        nonlocal new_semantics
        if new_semantics:
            return ticks_diff(new, old)
        return ticks_diff(old, new)
    return func

ticksdiff = tdiff()

SERVER = "192.168.0.23"
CLIENT_ID = ubinascii.hexlify(unique_id())
TOPIC = b"led"
QOS = 1

t = 0
maxt = 0
mint = 5000


def sub_cb(topic, msg):
    global t, maxt, mint
    dt = ticksdiff(t, ticks_ms())
    print('echo received in {} ms'.format(dt))
    print((topic, msg))
    maxt = max(maxt, dt)
    mint = min(mint, dt)


def main(quit=True):
    global t
    c = MQTTClient(CLIENT_ID, SERVER)
    # Subscribed messages will be delivered to this callback
    c.set_callback(sub_cb)
    c.connect()
    c.subscribe(TOPIC, qos = QOS)
    print("Connected to %s, subscribed to %s topic" % (SERVER, TOPIC))
    n = 0
    pubs = 0
    try:
        while 1:
            n += 1
            if not n % 100:
                t = ticks_ms()
                c.publish(TOPIC, str(pubs).encode('UTF8'), retain = False, qos = QOS)
                c.wait_msg()
                pubs += 1
                if not pubs % 100:
                    print('echo received in max {} ms min {} ms'.
                          format(maxt, mint))
                    if quit:
                        return
            sleep(0.05)
            c.check_msg()
    finally:
        c.disconnect()
