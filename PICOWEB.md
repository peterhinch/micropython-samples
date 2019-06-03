# Running Picoweb on hardware devices

This has regularly caused dificulty on the forum.

The target hardware is assumed to be running official MicroPython firmware.

This repo aims to clarify the installation process. Paul Sokolovsky's Picoweb
code is unchanged. The demos are trivially changed to use IP '0.0.0.0' and port
80.

Two ways of installing Picoweb are available: copying this directory to the
target or using `upip`. To use `upip` you should ensure your firmware is V1.11
or later; your target will also require an internet connection. Both methods
require the following preliminaries.

## Preliminary steps

### Clone this repo to your PC.

From a suitable destination directory issue
```
git clone https://github.com/peterhinch/micropython-samples
```

### Establish uasyncio status

Determine whether your target has `uasyncio` already installed. At the REPL
issue:
```
>>> import uasyncio
>>>
```
If this throws an `ImportError`, `uasyncio` is not installed.

## Installing using upip

Copy the `picoweb` subdirectory of this repo's `PicoWeb` directory, with its
contents, to the target. If using `rshell` to connect to a Pyboard D this would
be done from the `PicoWeb` directory with:
```
/my/tree/PicoWeb> cp -r picoweb/ /flash
```

Ensure your target is connected to the internet. Then perform the following
steps. The first step may be omitted if `uasyncio` is already installed.
```
upip.install('micropython-uasyncio')
upip.install('micropython-ulogging')
upip.install('micropython-pkg_resources')
upip.install('utemplate')
```

## Installing by copying this archive

Copy the contents of the `PicoWeb` directory (including subdirectories) to the
target. If using `rshell` on an ESP32 change to this directory, at the `rshell`
prompt issue
```
/my/tree/PicoWeb> rsync . /pyboard
```
This may take some time: 1 minute here on ESP32.

If `uasyncio` was already installed, the corrsponding directory on the target
may be removed.

# Running Picoweb

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

Note that to run these demos on platforms other than the Unix build you may
want to change IP and port as above.
