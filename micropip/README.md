# 0. Contents

 1. [Installing MicroPython library modules](./README.md#1-installing-micropython-library-modules)  
 2. [micropip](./README.md#2-micropip) upip alternative runs on a PC under CPython  
 3. [Overriding built in library modules](./README.md#3-overriding-built-in-library-modules)  

# 1. Installing MicroPython library modules

Paul Sokolovsky has forked the MicroPython project. This is the
[pycopy fork](https://github.com/pfalcon/pycopy). The library for the `pycopy`
fork may be found [here](https://github.com/pfalcon/micropython-lib).

This guide is for users of official MicroPython firmware as found on
[micropython.org](https://micropython.org/). The library at
[micropython-lib](https://github.com/micropython/micropython-lib) is compatible
with the official firmware. Users of pycopy should consult that project's
documentation.

Libraries on [PyPi](https://pypi.org/) may or may not be compatible with
official firmware. This is resolved by official `upip` (and its `micropip`
derivative). These first search the official library. Only if no match is found
do they install from PyPi. For this and other reasons, `pip` and `pip3` should
not be used to install MicroPython libraries. Use of `upip` is detailed in the
[official docs](http://docs.micropython.org/en/latest/reference/packages.html).

Users of non-networked hardware such as the Pyboard 1.x can use `upip` with the
Unix build of MicroPython to install a library module to an arbitrary directory
on a PC, from where the files and directories can be copied to the target
hardware. `upip` and its dependency `upip_utarfile` may be found in the `tools`
directory of the source tree. This approach has the drawback of requiring the
Unix build, which must be built from source. This may be avoided by using
`micropip.py` in this repo which runs under CPython.

Alternatively libraries may be installed by copying files from the MicroPython
library repository to the target device. However this requires some attention
to detail where there are dependencies. Where modules are organised as Python
packages the directory structure must be maintained.

###### [Main README](../README.md)

## 2. micropip

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
Example invocation line to install the `copy` module to a PC:
```
$ micropip.py install -p ~/rats micropython-copy
```

###### [Contents](./README.md#0-contents)

# 3. Overriding built in library modules

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

###### [Contents](./README.md#0-contents)

###### [Main README](../README.md)
