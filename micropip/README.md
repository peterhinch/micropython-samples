# Overriding built in library modules

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
