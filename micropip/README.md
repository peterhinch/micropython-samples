# 0. Installing MicroPython library modules

Paul Sokolovsky, the author of most of the micropython library and major
contributor to MicroPython, has forked the MicroPython project. This is the
[pycopy fork](https://github.com/pfalcon/pycopy).

Official firmware may be found on [micropython.org](https://micropython.org/).
Each firmware build has its own library. Some modules in the Pycopy library are
incompatible with the official firmware.

Libraries may be installed by copying files from the appropriate library
repository to the target device. However this requires some attention to detail
where there are dependencies or where modules are organised as Python packages.

Each version has a tool known as `upip` for installing library and user
contributed modules modelled on Python's `pip`. This handles dependencies and
builds the correct directory structure on the target.

Note that `pip` and `pip3` cannot be used for MicroPython modules. This is
because the file format is nonstandard. The file format was chosen to enable
the installer to run on targets with minimal resources.

# 1. Contents

 0. [Installing MicroPython library modules](./README.md#0-installing-micropython-library-modules)  
 1. [Contents](./README.md#1-contents)  
 2. [Users of Pycopy firmware](./README.md#2-users-of-pycopy-firmware)  
 3. [Users of official MicroPython](./README.md#3-users-of-official-micropython)  
  3.1 [micropip](./README.md#31-micropip) Runs on a PC  
 4. [Overriding built in library modules](./README.md#4-overriding-built-in-library-modules)  

###### [Main README](../README.md)

# 2. Users of Pycopy firmware

The library for the `pycopy` fork may be found [here](https://github.com/pfalcon/micropython-lib).
Library modules located on [PyPi](https://pypi.org/) are correct for the
`pycopy` firmware.

The `upip` tool may be found in the `tools` directory of `pycopy`. This version
should be used as it installs exclusively from PyPi.

For hardware which is not network enabled, `upip` may be run under the Unix
build of MicroPython to install to an arbitrary directory on a PC. The
resultant directory structure is then copied to the target using a utility such
as [rshell](https://github.com/dhylands/rshell).

Usage of `upip` is documented in the
[official docs](http://docs.micropython.org/en/latest/reference/packages.html).

# 3. Users of official MicroPython

The library at [micropython-lib](https://github.com/micropython/micropython-lib)
is compatible with the official firmware. As of version 1.11 the included
version of `upip` will install the correct library module for use with this
firmware, searching for modules in the official library before searching
[PyPi](https://pypi.org/).

Users of non-networked hardware such as the Pyboard 1.x can use `upip` with the
Unix build of MicroPython to install a library module to an arbitrary directory
on a PC, from where the files and directories can be copied to the target
hardware. This approach has the drawback of requiring the Unix build, which has
to be built from source.

For those unable or unwilling to do this, `micropip.py` in this repo may be
employed.

## 3.1 micropip

This runs under Python 3.2 or above. Library and user modules are installed to
the PC for transfer to the target. It is cross-platform and has been tested
under Linux, Windows and OSX.

Help may be accessed with

```
micropip.py --help
```
or

```
python3 -m micropip --help
```
Example invocation line:
```
$ micropip.py install -p ~/rats micropython-uasyncio
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
