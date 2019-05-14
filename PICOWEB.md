# Running Picoweb on hardware devices

This has regularly caused dificulty on the forum.

The target hardware is assumed to be running official MicroPython firmware.

This repo aims to clarify the installation process. Paul Sokolovsky's Picoweb
code is unchanged except for the name of the logging library. The demos are
trivially changed to use IP '0.0.0.0' and port 80.

To install on a hardware platform such as ESP32 or Pyboard D it is necessary to
copy this directory and its contents (including subdirectories) to the target.
If using `rshell` on an ESP32 change to this directory, at the `rshell` prompt
issue

```
/my/tree/PicoWeb> rsync . /pyboard
```
This may take some time.

At the REPL connect to the network and determine your IP address
```
>>> import network
>>> w = network.WLAN()
>>> w.ifconfig()
```

issue
```
>>> from picoweb import example_webapp
```

or
```
>>> from picoweb import example_webapp2
```

Then point your browser at the IP address determined above.

Note that some platforms will have `uasyncio` installed as frozen bytecode: in
such cases there is no need to copy the `uasyncio` subdirectory (if you do, it
will be ignored).

# ESP8266

RAM limitations require the use of frozen bytecode, and getting the examples
running is a little more involved. Create a directory on your PC and copy the
contents of this directory to it. Then add the files `inisetup.py`, `_boot.py`
and `flashbdev.py` which may be found in the MicroPython source tree under
`ports/esp8266/modules`. You may also want to add a custom connect module to
simplify connection to your WiFi. Then build the firmware. The script I used
was
```bash
#! /bin/bash

# Test picoweb on ESP8266

DIRECTORY='/home/adminpete/temp/picoweb'

cd /mnt/qnap2/data/Projects/MicroPython/micropython/ports/esp8266

make clean
esptool.py  --port /dev/ttyUSB0 erase_flash

if make -j 8 FROZEN_MPY_DIR=$DIRECTORY
then
    sleep 1
    esptool.py --port /dev/ttyUSB0 --baud 115200 write_flash --flash_size=detect -fm dio 0 build/firmware-combined.bin
    sleep 4
    rshell -p /dev/ttyUSB0 --buffer-size=30 --editor nano
else
    echo Build failure
fi
```
For the demos you will need to make the `example_webapp.py` source file and
`squares.tpl` accessible in the filesystem. The following `rshell` commands,
executed from this directory or the one created above, will make these
available.
```
path/to/repo> mkdir /pyboard/picoweb
path/to/repo> mkdir /pyboard/picoweb/templates
path/to/repo> cp picoweb/example_webapp.py /pyboard/picoweb/
path/to/repo> cp picoweb/templates/squares.tpl /pyboard/picoweb/templates/
```


# Documentation and further examples

See [the PicoWeb docs](https://github.com/pfalcon/picoweb)

Note that to run under official MicroPython, references to `ulogging` in these
demos must be changed to `logging`. You may also want to change IP and port as
above.

