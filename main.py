#!/usr/bin/env python3

from pynbs import read
from unsplit_lines import lines_from_song
from split_lines import SplitLine, build_contraption
from math import sqrt, ceil
from sponge_schematic import Schematic

"""
song is either pynbs.File or string (= input path)
sides_mode is how many sides the noteblocks should have (-1, or between 1 and 3)
-1: using the best
1: 2n wide, n high rectangle in front
2: 2n×n rectangle to the right and another in front
3: 2n×n rectangles on all 3 sides
"""
def convert(song, out_path, sides_mode=-1):
    if type(song) == str:
        song = read(song)
    
    unsplit_lines = lines_from_song(song)
    lines = []
    # converting from UnsplitLine to SplitLine
    # note that the actual splitting has already happened in lines_from_song
    for line in unsplit_lines:
        lines.append(SplitLine(line.key, line.instrument, line.ticks))
    lines.sort(key=lambda l: l.note + 100 * l.instrument)
        
    count = len(lines)
    assert count > 0, "There is no line to convert!"
    if sides_mode == -1:
        if count <= 128:
            sides_mode = 1
        elif count <= 256:
            sides_mode = 2
        else:
            sides_mode = 3
    height = int(0.5 + ceil(sqrt( count / (2 * sides_mode) )))
    
    schem = Schematic()
    
    if sides_mode == 1:
        build_contraption(schem, lines, 0, (count - 1) // height + 1, 0, height)
    elif sides_mode == 2:
        build_contraption(schem, lines, height * 2, height * 2, 0, height)
    else:
        build_contraption(schem, lines, height * 2, height * 2, height * 2, height) # TODO maybe even out the missing lines so its not that abrupt
    
    schem.save(out_path)


if __name__ == '__main__':
    from sys import argv
    convert(argv[1], argv[2])

#TODO all asserts should have explanation
#TODO: custom instruments
#TODO render distance recommendation sign
# maybe fix the corners of the noteblock sides
# maybe some more explanation for methods
