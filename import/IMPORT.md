# MicroPython's import statement

I seldom write tutorials on elementary Python coding; there are plenty online.
However there are implications specific to low RAM environments.

# 1. The import process

When a module comprising Python source is imported, the compiler runs on the
target and emits bytecode. The bytecode resides in RAM for later execution.
Further, the compiler requires RAM, although this is reclaimed by the garbage
collector after compilation is complete. The compilation stage may be skipped
by precompiling the module to an `.mpy` file, but the only way to save on the
RAM used by the bytecode is to use
[frozen bytecode](http://docs.micropython.org/en/latest/reference/manifest.html).

This doc addresses the case where code is not frozen, discussing ways to ensure
that only necessary bytecode is loaded.

# 2. Python packages and the lazy loader

Python packages provide an excellent way to split a module into individual
files to be loaded on demand. The drawback is that the user needs to know which
file to import to access a particular item:
```python
from my_library.foo import FooClass  # It's in my_library/foo.py
```
This may be simplified using Damien's "lazy loader". This allows the user to
write
```python
import my_library
foo = my_library.FooClass()  # No need to know which file holds this class
```
The file `my_library/foo.py` is only loaded when it becomes clear that
`FooClass` is required. Further, the structure of the package is hidden from
the user and may be changed without affecting its API.

The "lazy loader" is employed in
[uasyncio](https://github.com/micropython/micropython/tree/master/extmod/uasyncio)
making it possible to write
```python
import uasyncio as asyncio
e = asyncio.Event()  # The file event.py is loaded now
```
Files are loaded as required. The source code is in `__init__.py`: 
[the lazy loader](https://github.com/micropython/micropython/blob/master/extmod/uasyncio/__init__.py).

# 3. Wildcard imports

The use of
```python
from my_module import *
```
needs to be treated with caution for two reasons. It can populate the program's
namespace with unexpected objects causing name conflicts. Secondly all these
objects occupy RAM. In general wildcard imports should be avoided unless the
module is designed to be imported in this way. For example issuing
```python
from uasyncio import *
```
would defeat the lazy loader forcing all the files to be loaded.

## 3.1 Designing for wildcard import

There are cases where wildcard import makes sense. For example a module might
declare a number of constants. This module 
[colors.py](https://github.com/peterhinch/micropython-nano-gui/blob/master/gui/core/colors.py)
computes a set of 13 colors for use in an interface. This is the module's only
purpose so it is intended to be imported with
```python
from gui.core.colors import *
```
This saves having to name each color explicitly.

In larger modules it is wise to avoid populating the caller's namespace with
cruft. This is achieved by ensuring that all private names begin with a `_`
character. In a wildcard import, Python does not import such names.
```python
_LOCAL_CONSTANT = const(42)
def _foo():
    print("foo")  # A local function
```
Note that declaring a constant with a leading underscore saves RAM: no
variable is created. The compiler substitues 42 when it sees `_LOCAL_CONSTANT`.
Where there is no underscore the compiler still performs the same substitution,
but a variable is created. This is because the module might be imported with a
wildcard import.

# 4. Reload

Users coming from a PC background often query the lack of a `reload` command.
In practice on a microcontroller it is usually best to issue a soft reset
(`ctrl-d`) before re-importing an updated module. This is because a soft reset
clears all retained state. However a `reload` function can be defined thus:
```python
import gc
import sys
def reload(mod):
    mod_name = mod.__name__
    del sys.modules[mod_name]
    gc.collect()
    __import__(mod_name)
```
## 4.1 Indirect import

The above code sample illustrates the method of importing a module where the
module name is stored in a variable:
```python
def run_test(module_name):
    mod = __import__(module_name)
    mod.test()  # Run a self test
```
