# fastbuild - Pull and build Pyboard firmware under Linux

These scripts are intended to speed and simplify rebuilding firmware from
source notably where pyboards of different types are in use, or when
frozen bytecode necessitates repeated compilation and deployment. In
particular `buildpyb` will detect the attached Pyboard type, build the
appropriate firmware, put the board into DFU mode and deploy it, before
launching `rshell`. The latter step may be removed if `rshell` is not in
use.

The scripts should be run as your normal user and can proceed without user
interaction.

Includes udev rules to avoid jumps from `/dev/ttyACM0` to `/dev/ttyACM1`
and ensuring Pyboards of all types appear as `/dev/pyboard`. Rules are also
offered for USB connected WiPy (V1.0) and FTDI USB/serial adaptors.

These scripts use Python scripts `pyb_boot` to put the Pyboard into DFU mode
and `pyb_check` to determine the type of attached board. These use the
`pyboard.py` module in the source tree to execute scripts on the attached
board.

###### [Main README](../README.md)

### Optional Edits

In the `buildpyb` script you may wish to edit the `-j 8` argument to `make`.
This radically speeds build on a multi core PC. Empirically 8 gave the fastest
build on my Core i7 4/8 core laptop: adjust to suit your PC. You may also want
to remove the call to `rshell` if you don't plan on using it.

This script defaults to a frozen modules directory `stmhal/modules`. This may
be overridden by creating an environment variable FROZEN_DIR: a recent update
enabled the directory for frozen to be located anywhere in the filesystem,
allowing project specific directories.

In `buildnew` you may wish to delete the unix make commands.

### Dependencies and setup (on PC)

Python3  
The following Bash code installs pyserial, copies `49-micropython.rules` to
(on most distros) `/etc/udev/rules.d`. It installs `rshell` if you plan to
use it (recommended).

As root:
```
apt-get install python3-serial
pip install pyserial
cp 49-micropython.rules /etc/udev/rules.d
pip3 install rshell
```

Verify that `pyboard.py` works. To do this, close and restart the terminal
session. Run Python3, paste the following and check that the red LED lights:

```python
import os
mp = os.getenv('MPDIR')
sys.path.append(''.join((mp, '/tools')))
import pyboard
pyb = pyboard.Pyboard('/dev/pyboard')
pyb.enter_raw_repl()
pyb.exec('pyb.LED(1).on()')
pyb.exit_raw_repl()
```

The build scripts expect an environment variable MPDIR holding the path to the
MicroPython source tree. To set this up, as normal user issue (edited for your
path to the MicroPython source tree):

```
cd ~
echo export MPDIR='/mnt/qnap2/data/Projects/MicroPython/micropython' >> .bashrc
echo >> .bashrc
```

Close and restart the terminal session before running the scripts.

### Build script: `buildpyb`  

This checks the attached pyboard. If it's a V1.0, V1.1 or Lite it builds the
correct firmware and deploys it. Otherwise it produces an error message.

Optional argument `--clean` - if supplied does a `make clean` to delete
all files produced by the previous build before proceeding.

### Update source: `buildnew`

Report state of master branch, update sources and issue `make clean` for
Pyboard variants and ESP8266. Builds cross compiler and unix port.

### ESP8266 Build

`buildesp` A script to build and deploy ESP8266 firmware. Accepts optional
`--clean` argument.
