# The rshell macro fork

These notes describe one of a number of possible ways to use the macro
facility.

The aim was to provide a set of generic macros, along with a project specific
set. The starting point is an alias, run before work is started on a given
project. The aliases are created in `~/.bashrc`. The example below is for two
projects, `mqtt` and `asyn`.
```bash
alias asyn='export PROJECT=ASYN;cd /MicroPython/micropython-async/'
alias mqtt='export PROJECT=MQTT; cd /MicroPython/micropython-mqtt'
```
The `PROJECT` environment variable is examined by the file `rshell_macros.py`
located in the `rshell` directory. An example is presented here:
```python
import os
proj = None
try:
    proj = os.environ['PROJECT']
except KeyError:
    print('Environment var PROJECT not found: only generic macros loaded.')

macros = {}
macros['..'] = 'cd ..'
macros['...'] = 'cd ../..'
macros['ll'] = 'ls -al {}', 'List any directory'
macros['lf'] = 'ls -al /flash/{}'
macros['lsd'] = 'ls -al /sd/{}'
macros['lpb'] = 'ls -al /pyboard/{}'
macros['mv'] = 'cp {0} {1}; rm {0}', 'Move/rename'
macros['repl'] = 'repl ~ import machine ~ machine.soft_reset()', 'Clean REPL'
macros['up'] = 'cd /MicroPython'
macros['asyn'] = 'cd /MicroPython/micropython-async'
macros['primitives'] = 'cd /MicroPython/micropython-async/v3; rsync primitives/ {}/primitives; cd -', 'Copy V3 primitives to dest'

if proj == 'MQTT':
    print('Importing macros for MQTT')
    macros['home'] = 'cd /MicroPython/micropython-mqtt/mqtt_as'
elif proj == 'ASYN':
    print('Importing macros for ASYN')
    macros['home'] = 'cd /MicroPython/micropython-async'
    macros['v3'] = 'cd /MicroPython/micropython-async/v3'
    macros['off'] = 'cd /MicroPython/micropython-async/official', 'official uasyncio'
    macros['sync'] = 'cd /MicroPython/micropython-async/v3; rsync primitives/ {}/primitives', 'Copy V3 primitives to dest'
    macros['demos'] = 'cd /MicroPython/micropython-async/v3; rsync as_demos/ {}/as_demos', 'Copy V3 demos to dest'
    macros['drivers'] = 'cd /MicroPython/micropython-async/v3; rsync as_drivers/ {}/as_drivers', 'Copy V3 drivers to dest'
```
The first part of the script defines generic macros such as `ll` and `lsd`
available to any project, and if no project is defined.

Project specific macros are added in response to the environment variable.
Note the way args are passed: to update the SD card on a Pyboard the macro
`primitives` would be called with:
```
MicroPython > m primitives /sd
```
The `mv` macro, called with
```
MicroPython > m mv source_path dest_path
```
expands to
```
cp source_path dest_path; rm source_path
```
