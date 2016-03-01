# Fonts

This code sample demonstrates a way to get from a system font or other font file to Python code
which may be used normally or stored as frozen bytecode. The latter enables major savings in
scarce RAM.

Alas this process uses a closed source Windows program. It is available
[here](http://www.mikroe.com/glcd-font-creator/) but it is free (as in beer) and it will run
under Wine.

To convert a system font to Python follow these steps.  
Start the Font Creator. Select File - New Font - Import an Existing System Font and select a font.
Accept the defaults. Assuming you have no desire to modify it click on the button "Export for GLCD".
Select the microC tab and press Save, following the usual file creation routine.

On a PC with Python 3 installed issue (to convert a file Ubuntu_Medium17x19.c to Python ubuntu.py)
```
python3 CfontToPython.py -i Ubuntu_Medium17x19.c -o ubuntu.py
```
To test issue
```python
import ubuntu
ubuntu.font.test('ghi')
```

The machine generated Python file can be run under cPython, copied to the Pyboard and run, or
copied to the scripts directory and used to build firmware with the file as a frozen module.

This assumes Linux but CfontToBinary.py is plain Python3 and should run on other platforms. 

# The font matrix

In the C file each character is stored as a fixed size array of bytes, the first byte being
the character width. When rendering a font to a device, fonts designed as variable pitch
should use this byte as the width. Monospaced fonts should be rendered using the font's
width (see pyfont.py).

# Note

If anyone knows a Python way of converting a font file (a.g. ttf) to a bitmap, please let me
know. My own efforts were not good enough hence my reluctant advocacy of the above closed source
program.

