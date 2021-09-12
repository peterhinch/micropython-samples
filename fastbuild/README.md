# fastbuild - Pull and build Pyboard firmware under Linux

These scripts are intended to speed and simplify rebuilding firmware from
source notably where pyboards of different types are in use, or when
frozen bytecode necessitates repeated compilation and deployment. In
particular `buildpyb` will detect the attached Pyboard type, build the
appropriate firmware, put the board into DFU mode and deploy it.

The scripts should be run as your normal user and can proceed without user
interaction.

Includes udev rules to avoid jumps from `/dev/ttyACM0` to `/dev/ttyACM1`
and ensuring Pyboards of all types appear as `/dev/pyboard`. Rules are also
offered for USB connected WiPy (V1.0) and FTDI USB/serial adaptors.

These scripts use Python scripts `pyb_boot` to put the Pyboard into DFU mode
and `pyb_check` to determine the type of attached board. These use the
`pyboard.py` module in the source tree to execute scripts on the attached
board.

The scripts will require minor edits to reflect your directory structure.

Scripts updated 12 Sep 2021 to fix handling of submodules.

###### [Main README](../README.md)

# Frozen modules and manifests

The method of specifying modules to be frozen has changed (as of Oct 2019).
The files and directories to be frozen are now specified in a file with the
default name `manifest.py`. This may be found in `/ports/stm32/boards` or the
eqivalent for other ports.

In practice it can be advantageous to override the default. You might want to
freeze a different set of files depending on the specific board or project.
This is done by issuing
```
make BOARD=$BOARD FROZEN_MANIFEST=$MANIFEST
```
where `BOARD` specifies the target (e.g. 'PYBV11') and `MANIFEST` specifies the
path to the manifest file (e.g. '~/my_manifest.py').

A manifest file comprises `include` and `freeze` statements. The latter have
one or two args. The first is a directory specifier. If the second exists it
can specify a single file or more, by passing an iterable. Consider the
following manifest file:
```python
include("$(MPY_DIR)/ports/stm32/boards/PYBD_SF2/manifest.py")
freeze('$(MPY_DIR)/drivers/dht', 'dht.py')
freeze('$(MPY_DIR)/tools', ('upip.py', 'upip_utarfile.py'))
freeze('/path/to/pyb_d_modules')
```
Taking the lines in order:
 1. This includes another manifest file located in the source tree.
 2. The single file argument freezes the file 'dht.py' found in the MicroPython
 source tree `drivers` directory.
 3. Passing an iterable causes the two specified files to be frozen.
 4. Passing a directory without arguments causes all files and subdirectories
 to be frozen. Assume '../pyb_d_modules' contains a file `rats.py` and a
 subdirectory `foo` containing `bar.py`. Then `help('modules')` will show
 `rats` and `foo/bar`. This means that Python packages are frozen correctly.

On Linux symlinks are handled as you would expect.

# The build scripts

### Optional Edit (all scripts)

In these scripts you may wish to edit the `-j 8` argument to `make`. This
radically speeds build on a multi core PC. Empirically 8 gave the fastest build
on my Core i7 4/8 core laptop: adjust to suit your PC.

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

The build scripts expect an environment variable MPDIR holding the path to the
MicroPython source tree. To set this up, as normal user issue (edited for your
path to the MicroPython source tree):

```
cd ~
echo export MPDIR='/mnt/qnap2/data/Projects/MicroPython/micropython' >> .bashrc
echo >> .bashrc
```

Close and restart the terminal session before proceding.

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

### Build script: `buildpyb`  

This checks the attached pyboard. If it's a V1.0, V1.1 or Lite it or a Pyboard
D series it builds the correct firmware and deploys it. Otherwise it produces
an error message.

It freezes a different set of files depending on whether the board is a Pyboard
V1.x or a Pyboard D. It can readily be adapted for finer-grain control or to
produce project-specific builds.

You will need to change the `MANIFESTS` variable which is the directory
specifier for my manifest files.

Optional argument `--clean` - if supplied does a `make clean` to delete
all files produced by the previous build before proceeding.

### Update source: `buildnew`

Report state of master branch, update sources and issue `make clean` for
Pyboard variants and ESP8266. Builds cross compiler and unix port.

If you don't use the Unix build you may wish to delete the unix make commands.

### ESP8266 Build

`buildesp` A script to build and deploy ESP8266 firmware. Accepts optional
`--clean` or `--erase` arguments. Both perform a `make clean` but the second
also erases the ESP8266 flash.

You will need to change the `MANIFEST` variable which is the directory
specifier for my esp8266 manifest file.

