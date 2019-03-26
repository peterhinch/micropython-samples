# 0. Installing MicroPython library modules

Paul Sokolovsky, the author of most of the micropython library and major
contributor to MicroPython, has forked the MicroPython project. This is the
[pycopy fork](https://github.com/pfalcon/pycopy).

Official firmware may be found [on micropython.org](https://micropython.org/).
Each firmware build has its own library. Some modules in the Pycopy library are
incompatible with the official firmware.

Libraries may be installed by copying files from the appropriate library
repository to the target device. However this requires some attention to detail
where there are dependencies or where modules are organised as Python packages.

Each fork has means of installing library and user contributed modules modelled
on Python's `pip`. These handle dependencies and build the correct directory
structure on the target.

Note that `pip` and `pip3` cannot be used for MicroPython modules. This is
because the file format is nonstandard. The file format was chosen to enable
the installer to run on targets with minimal resources.

# 1. Contents

 0. [Installing MicroPython library modules](./README.md#0-installing-micropython-library-modules)  
 1. [Contents](./README.md#1-contents)  
 2. [Users of Pycopy firmware](./README.md#2-users-of-pycopy-firmware)  
 3. [Users of official MicroPython](./README.md#3-users-of-official-micropython)  
  3.1 [The installers](./README.md#31-the-installers)  
   3.1.1 [upip_m](./README.md#311-upip_m)  
   3.1.2 [micropip](./README.md#312-micropip)  
 4. [Overriding built in library modules](./README.md#4-overriding-built-in-library-modules)  

###### [Main README](../README.md)

# 2. Users of Pycopy firmware

The library for the `pycopy` fork may be found [here](https://github.com/pfalcon/micropython-lib).
Library modules located on [PyPi](https://pypi.org/) are correct for the
`pycopy` firmware.

The preferred installation tool is `upip.py` which may be found in the `tools`
directory of MicroPython. It is installed by default on network enabled
hardware such as Pyboard D, ESP8266 and ESP32.

For hardware which is not network enabled, `upip` may be run under the Unix
build of MicroPython to install to an arbitrary directory on a PC. The
resultant directory structure is then copied to the target using a utility such
as [rshell](https://github.com/dhylands/rshell).

Usage of `upip` is documented in the
[official docs](http://docs.micropython.org/en/latest/reference/packages.html).

# 3. Users of official MicroPython

The library at [micropython-lib](https://github.com/micropython/micropython-lib)
is compatible with the official firmware. Unfortunately for users of official
firmware its README is misleading, not least because the advocated `upip`
module may produce an incorrect result. This is because some library modules on
[PyPi](https://pypi.org/) require the `pycopy` firmware.

Two (unofficial) utilities are provided for users of the official firmware.
Where a library module is to be installed, these will locate a compatible
version. User contributed modules located on PyPi will be handled as normal.
 * `upip_m.py` A modified version of `upip.py`. For network enabled targets.
 * `micropip.py` Installs modules to a PC for copying to the target device.
 For non-networked targets and for targets with too little RAM to run
 `upip_m.py`. Requires CPython 3.2 or later.

## 3.1 The installers

These have the same invocation details as `upip` and the
[official docs](http://docs.micropython.org/en/latest/reference/packages.html)
should be consulted for usage information.

### 3.1.1 upip_m

The file `upip_m.py` should be copied to the target device. If `upip` is not
available on the target `upip_utarfile.py` must also be copied.

Alternatively and more efficiently these files may be frozen as bytecode. The
method of doing this is [documented here](http://docs.micropython.org/en/latest/reference/packages.html).

Users of the ESP8266 are unlikely to be able to use `upip_m` unless it is
frozen as bytecode. An alternative is to use `micropip.py` to install to a PC
and then to use [rshell](https://github.com/dhylands/rshell) or other utility
to copy the directory structure to the device.

### 3.1.2 micropip

This is a version of `upip_m` which runs under Python 3.2 or above. Library and
user modules are installed to the PC for transfer to the target. It is cross
platform and has been tested under Linux, Windows and OSX.

Help may be accessed with

```
micropip.py --help
```
or

```
python3 -m micropip --help
```

###### [Contents](./README.md#1-contents)

# 4. Overriding built in library modules

Some firmware builds include library modules as frozen bytecode. On occasion it
may be necessary to replace such a module with an updated or modified
alternative. The most RAM-efficient solution is to rebuild the firmware with
the replacement implemented as frozen bytecode.

For users not wishing to recompile there is an alternative. The module search
order is defined in `sys.path`.

```
>>> import sys
>>> sys.path
['', '/flash', '/flash/lib']
```
The `''` entry indicates that frozen modules will be found before those in the
filesystem. This may be overridden by issuing:
```
>>> import sys
>>> sys.path.append(sys.path.pop(0))
```
This has the following outcome:
```
>>> sys.path
['/flash', '/flash/lib', '']
```
Now modules in the filesystem will be compiled and executed in preference to
those frozen as bytecode.

###### [Contents](./README.md#1-contents)

###### [Main README](../README.md)
