#!/usr/bin/env python3

from pynbs import read
from unsplit_lines import lines_from_song
from split_lines import SplitLine, build_contraption
from math import sqrt, ceil
from sponge_schematic import Schematic

"""
song is either pynbs.File or string (= input path)
sides_mode is how many sides the noteblocks should have (-1, or between 1 and 3)
-1: using one of the 3 based on noteblock count
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
        if count <= 128: # 16*8
            sides_mode = 1
        elif count <= 256: # 2 * 16*8
            sides_mode = 2
        else:
            sides_mode = 3
    
    # imagining every side as a 2:1 rectangle, but we need to round to whole numbers:
    height = int(0.5 + ceil(sqrt( count / (2 * sides_mode) )))
    whole_width = int(0.5 + ceil(count / height))
    
    schem = Schematic()
    
    if sides_mode == 1:
        left_width = 0
        middle_width = whole_width
        right_width = 0
    elif sides_mode == 2:
        left_width = whole_width // 2
        middle_width = whole_width - left_width
        right_width = 0
    else:
        left_width = whole_width // 3
        middle_width = whole_width - 2 * left_width
        right_width = left_width
    
    build_contraption(schem, lines, left_width, middle_width, right_width, height)
    
    schem.save(out_path)


if __name__ == '__main__':
    from sys import argv
    convert(argv[1], argv[2])

#TODO: custom instruments
#TODO render distance recommendation sign
# TODO nbt data to schematic + sign text
# maybe fix the corners of the noteblock sides
# maybe some more explanation for methods
# TODO thank lithium+sodium dev
# fix get_delay_length performance
# TODO: todo-s in sponge_schematic and split_lines
# bool redstonelamp or tripwire, to reduce lag bc of lighting updates
