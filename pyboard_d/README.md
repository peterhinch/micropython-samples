# Unofficial guide to the Pybaord D

I'll update this with contributed ideas (issues, PR's and forum comments). I
expect to delete it when official docs emerge.

## LED's

The board has one RGB led. Each colour is addressed as pyb.LED(n) where n is in
range 1 to 3.

## Accel

These boards do not have an accelerometer.

## WiFi

After a power cycle a connection must be established with explicit credentials:
the board behaves more like ESP32 than ESP8266. If a WiFi outage occurs it will
attempt automatically to reconnect. The following code fragments may be used.

```python
[code]wl = network.WLAN()
wl.connect(my_ssid, my_password)
wl.active(1)
print(wl)
```
It can be in state `down`, `join` or `up`. `down` means that it's not trying to
connect. `join` means it's trying to connect and get an IP address, and `up`
means it's connected with an IP address and ready to send/receive.  If the AP
disappears then it goes from `up` to `join`, and will go back to `up` if the AP
reappears. `wl.status()` will give numeric values of these states:  
0=`down`, 1 and 2 mean `join` (different variants of it), 3=``up`.

You can also debug the wlan using tracing:
```python
wl = network.WLAN()
wl.config(trace=`value`)
```
`value` can be a bit-wise or of 1=async-events, 2=eth-tx, 4=eth-rx. So:
```python
wl = network.WLAN()
wl.config(trace=7)  # To see everything.
wl.config(trace=0)  # To stop
```
This will work on both STA and AP interfaces, so you can watch how two PYBD's
connect to each other.

Setting antenna type and TX power
```python
wl = network.WLAN()
wl.config(antenna=value)  # 0 internal 1 external
wl.config(txpower=value)  # In dbm
```

## Variants

I am aware of two variants distinguished by the sticker on top of the CPU.  
 1. SF2W (blue). This has about 178K of free RAM and 2MB of Flash.
 2. SF6W (red). This has 432K of free RAM. Also has 2MB Flash.

## Bootloader

To put the board in booloader mode, either execute pyb.bootloader(), or hold
down USR during reset and letting go of USR when the LED shines white.
- you're in bootloader mode when the red LED flashes once a second
- then upload the DFU as usual: tools/pydfu.py -u `firmware`
