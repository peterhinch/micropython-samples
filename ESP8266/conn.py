# Connect in station mode. Use saved parameters if possible to save flash wear

import network
import utime

use_default = True
ssid = 'my_ssid'
pw = 'my_password'

sta_if = network.WLAN(network.STA_IF)
if use_default:
    secs = 5
    while secs >= 0 and not sta_if.isconnected():
        utime.sleep(1)
        secs -= 1

# If can't use default, use specified LAN
if not sta_if.isconnected():
    sta_if.active(True)
    sta_if.connect(ssid, pw)
    while not sta_if.isconnected():
        utime.sleep(1)

