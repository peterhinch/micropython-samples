#! /usr/bin/python3

# Convert a font C source file to Python source.

# Copyright Peter Hinch 2016
# Released under the MIT licence
# Files created by GLCD Font Creator http://www.mikroe.com/glcd-font-creator/
# The code attempts two ways of deducing font height and width in pixels.
# Files produced by the GLCD Font Creator have a '//GLCD FontSize'  comment line which species these.
# This is used if it exists. However some files on the website lack this and have an initial record
# written into the data: this is used if necessary.

# Usage:
# ./cfonts_to_py Arial16x16.c timesroman.c
# puts files into a single Python file defaulting to fonts.py (-o name can override default)
# with a dictionary 'fonts.fonts' indexed by name and the value being a PyFont instance.
# The name index is the font filename less path and extension

import argparse, os

def getname(sourcefile):
    return os.path.basename(os.path.splitext(sourcefile)[0])

def halfword_to_str(n):
    return '\\x{:02x}\\x{:02x}'.format(n & 0xff, n >> 8)

def rbits(n): # reverse bits in a byte
    res = 0
    dm = 7
    if n > 0:
        for dm in range(7, -1, -1):
            res |= (n & 1) << dm
            n >>= 1
    return res

# Given a string 0f form '0x23' representing a byte, return a string of form 'xc4' with the bits
# comprising the byte reversed
def rbits_text(string):
    return 'x{:02x}'.format(rbits(int(string, 16)))

def writestart(outfile, name):
    print('{}: header found'.format(name))
    outfile.write('_{} = '.format(name))

def write_index(outfile, name, index):
    outfile.write("_{:}_index = ".format(name))
    count = 0
    for val in index:
        if count == 0:
            outfile.write("b'")
        outfile.write(halfword_to_str(val))
        count += 1
        count %= 8
        if count == 0:
            outfile.write("'\\\n")
    if count > 0:
        outfile.write("'")
    outfile.write("\n\n")

def process(infile, outfile, sourcefile):
    chars_processed = 0
    horiz, vert = 0, 0
    name = getname(sourcefile)
    phase = 0
    header_done = False
    offset = 0
    index = [offset]
    bytes_vert = 0
    for line in infile:
        if phase == 0:
            start = line.find('//GLCD FontSize')
            if start >= 0:                          # Found the font size: parse line
                start = line.find(':')
                line = line[start +1:]
                operator = line.find('x')
                if operator > 0 :
                    horiz = int(line[ : operator])
                    vert = int(line[operator +1 :])
                    writestart(outfile, name)
                    header_done = True
                    phase = 1
            elif line.find('{') >= 0:
                phase = 1
        if phase == 1:                           # Skip to 1st data after '{'
            start = line.find('{')
            if start >= 0:
                line = line[start +1:]
                phase = 2
        if phase == 2:
            if not (line == '' or line.isspace()):
                comment = line.find('//')
                if comment > 0 :
                    line = line[:comment]
                hexnums = line.split(',')
                if header_done:              # Ignore manually entered header data
                    if len(hexnums) > 5:
                        phase = 3               # Real font data will have many more fields per line
                else:
                    if len(hexnums) <= 5:
                        nums = [x for x in hexnums if not x.isspace()]
                        h = nums[1]
                        v = nums[2]
                        horiz, vert = int(h, 16), int(v, 16)
                        writestart(outfile, name)
                        header_done = True
                    else:
                        break                   # No header data
        if phase == 3:                          # Process data until '}'
            bytes_vert = (vert + 7)//8
            comment = line.find('//')
            if comment > 0 :
                line = line[:comment]
            end = line.find('}')
            if end > 0 :
                line = line[:end]
                phase = 4
            hexnums = line.split(',')
            if hexnums[0] != '':
                width = int(''.join(('0',hexnums[0].strip()[1:4])), 16) # in horizontal bits
                hbit_bytes = width * bytes_vert # Bytes per horiz bit
                offset += hbit_bytes
                index.append(offset)
                nums = [x for x in hexnums[1:] if not x.isspace()]
                if nums:
                    outfile.write("b'")
                    for hexnum in nums:
                        outfile.write('\\')
#                        outfile.write(hexnum.strip()[1:4]) # Don't reverse bits
                        outfile.write(rbits_text(hexnum.strip()[0:4])) # reverse bits
                        hbit_bytes -= 1
                        if hbit_bytes == 0:
                            break
                    outfile.write("'")
                    chars_processed += 1
                    outfile.write("\\\n") # each char line ends with \
    if phase == 4 :
        outfile.write("\n")
        write_index(outfile, name, index)
        outfile.write('{:} = TFTfont.TFTFont(_{:}, _{:}_index, {}, {}, {})\n\n'.format(name, name, name, vert, horiz, chars_processed))
        print('{}: Characters in font: {} width: {} height: {}'.format(name, chars_processed, horiz, vert))
    else:
        print(''.join(("File: '", sourcefile, "' is not a valid C font file")))

def write_header(outfile):
    outfile.write('# Code generated by cfonts_to_py.py\n')
    outfile.write('import TFTfont\n')
  
def write_trailer(sourcefiles, outfile):
    outfile.write('fonts = {')
    for sourcefile in sourcefiles:
        name = getname(sourcefile)
        outfile.write('"{}":{},\n'.format(name, name))
    outfile.write('}\n\n')

def load_c(sourcefiles, destfile):
    try:
        with open(destfile, 'w') as outfile:
            write_header(outfile)
            for sourcefile in sourcefiles:
                with open(sourcefile, 'r') as f:
                    process(f, outfile, sourcefile)
            write_trailer(sourcefiles, outfile)
    except OSError as err:
        print(err)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(__file__, description =
       "Utility for producing a fonts file for the tft module.\nConvers C fonts generated by GLCD font creator to Python.\nSample usage:\n./cfonts_to_py.py Arial16x16.c Ubuntu_Medium17x19.c\nProduces fonts.py",
       formatter_class = argparse.RawDescriptionHelpFormatter)
    parser.add_argument('infiles', metavar ='N', type = str, nargs = '+', help = 'input file paths')
    parser.add_argument("--outfile", "-o", default = 'fonts.py', help = "Path and name of output file", required = False)
    args = parser.parse_args()
    errlist = [f for f in args.infiles if not f[0].isalpha()]
    if len(errlist):
        print('Font filenames must be valid Python variable names:')
        for f in errlist:
            print(f)
    if len(errlist) == 0:
        errlist = [f for f in args.infiles if not os.path.isfile(f)]
        if len(errlist):
            print("These font filenames don't exist:")
            for f in errlist:
                print(f)
    if len(errlist) == 0:
        errlist = [f for f in args.infiles if os.path.splitext(f)[1].upper() != '.C']
        if len(errlist):
            print("These font filenames don't appear to be C files:")
            for f in errlist:
                print(f)
    if len(errlist) == 0:
        load_c(args.infiles, args.outfile)
