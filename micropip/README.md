# 0. Contents

 1. [Installing MicroPython library modules](./README.md#1-installing-micropython-library-modules)  
 2. [micropip](./README.md#2-micropip) upip alternative runs on a PC under CPython  
 3. [Overriding built in library modules](./README.md#3-overriding-built-in-library-modules)  

# 1. Installing MicroPython library modules

There are various forks of MicroPython, consequently libraries on
[PyPi](https://pypi.org/) may or may not be compatible with official firmware.
This is resolved by official `upip` (and its `micropip` derivative). These
first search the official library. Only if no match is found do they install
from PyPi. For this and other reasons, `pip` and `pip3` should not be used to
install MicroPython libraries. Use of `upip` is detailed in the
[official docs](http://docs.micropython.org/en/latest/reference/packages.html).

Users of non-networked hardware such as the Pyboard 1.x can use `upip` with the
Unix build of MicroPython to install a library module to an arbitrary directory
on a PC, from where the files and directories can be copied to the target
hardware. `upip` and its dependency `upip_utarfile` may be found in the `tools`
directory of the source tree. This approach has the drawback of requiring the
Unix build, which must be built from source. This may be avoided by using
`micropip.py` in this repo which runs under CPython.

Alternatively libraries may be installed by copying files from the MicroPython
[library repository](https://github.com/micropython/micropython-lib) to the
target device. However this requires some attention to detail where there are
dependencies. Where modules are organised as Python packages the directory
structure must be maintained.

## 1.1 Installing unofficial packages

PyPi hosts a wide variety of packages targeted at MicroPython. There is no
guarantee of their compatibility with the official MicroPython codebase and it
seems that some cannot even be downloaded by `upip`: e.g.
[this issue](https://github.com/peterhinch/micropython-samples/issues/27)

## 1.2 What micropip is and is not

Official `upip` cannot run under CPython. The purpose of `micropip` is to be a
straight port of `upip` for those who do not have access to the Unix build of
MicroPython. It aims to replicate the functinality of `upip`. Hence requests
for enhancements will be rejected. If `upip` is enhanced, I will port those
changes to `micropip`. Secondly, if I receive a report that `micropip` cannot
download a given unofficial package, I will check whether `upip` succceeds. If
`upip` also fails, either the package is faulty or there is a bug in `upip`.

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
