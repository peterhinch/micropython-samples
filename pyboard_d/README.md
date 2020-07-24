# Unofficial guide to the Pyboard D

Note: official docs may now be found [here](https://pybd.io/hw/pybd_sfxw.html)
so I expect to remove this guide soon.

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
wl = network.WLAN()
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
wl.config(trace=value)
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

## Flash memory

The SF2W and SF3W have 512KiB of internal flash, the SF6W has 2048KiB. All
have two external 2048KiB flash chips, one for the filesystem and the other for
executable code (it can be memory mapped). On SF2W and SF3W, if you freeze a
lot of code the firmware can become too big for the internal flash. To put
frozen code in external flash, edit the file
`ports/stm32/boards/PYBD_SF2/f722_qspi.ld` (or the corresponding one for
`PYBD_SF3` to add the line `*frozen_content.o(.text* .rodata*)`:
```
     .text_ext :
     {
         . = ALIGN(4);
         *frozen_content.o(.text* .rodata*)
         *lib/btstack/*(.text* .rodata*)
         *lib/mbedtls/*(.text* .rodata*)
         . = ALIGN(512);
         *(.big_const*)

```

There is a [small performance penalty](https://forum.micropython.org/viewtopic.php?f=16&t=8767#p49507)
in doing this of around 10%.

## Bootloader

To put the board in booloader mode, either execute pyb.bootloader(), or hold
down USR during reset and letting go of USR when the LED shines white.
The red LED then flashes once a second indicating bootloader mode.
- then upload the DFU as usual: tools/pydfu.py -u `firmware`

## Code emitters

Based on quick tests the Native, Viper and inline Arm Thumb assembler features
are supported.
