#!/usr/bin/env python3

from os.path import basename
from pynbs import read
from unsplit_lines import lines_from_song
from split_lines import SplitLine, build_contraption
from math import sqrt, ceil
#from mcschematic_safe import MCSchematic, Version # mcschematic_safe has a warning if we're replacing an already set block with setblock, helping us find bugs/obvious problems in our algorithm
from mcschematic import MCSchematic, Version

# filename can be empty string
def get_title(song, filename):
    title = song.header.song_name
    if title == "" and filename != "":
        title = basename(filename)
    if title == "" and song.header.song_origin != "":
        title = "From " + song.header.song_origin
    if title == "":
        title = "Unnamed song"
    if song.header.song_author != "":
        title += " by " + song.header.song_author
    if song.header.original_author != "":
        title += " orig.: " + song.header.original_author
    return title

"""
song is either pynbs.File or string (= input path)
use_redstone_lamp: whether or not to place redstone lamp next to the noteblock
sides_mode is how many sides the noteblocks should have (-1, or between 1 and 3)
-1: using one of the 3 based on noteblock count
1: 2n wide, n high rectangle in front
2: 2n×n rectangle to the right and another in front
3: 2n×n rectangles on all 3 sides
"""
def convert(song, out_path, use_redstone_lamp=True, sides_mode=-1):
    filename = ""
    if type(song) == str:
        filename = song
        song = read(song)
    
    title = get_title(song, filename)

    unsplit_lines = lines_from_song(song)
    lines = []
    # converting from UnsplitLine to SplitLine
    # note that the actual splitting has already happened in lines_from_song
    for line in unsplit_lines:
        lines.append(SplitLine(line.key, line.instrument, line.ticks))
    lines.sort(key=lambda l: l.note + 100 * l.instrument)
        
    count = len(lines)
    assert count > 0, "There is no line to convert, I need notes!"
    if count <= 0: # if assertions are excluded, we just silently exit
        return
    
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
    
    # edge case if there's a single note block line (we do this so the redstone lamp doesn't collide with glass):
    if whole_width == 1:
        whole_width += 1

    schem = MCSchematic()
    
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
    
    build_contraption(schem, lines, left_width, middle_width, right_width, height, title, use_redstone_lamp)
    
    if out_path[-6:] == ".schem": # library adds extension even if present
        out_path = out_path[:-6]
    schem.save("", out_path, Version.JE_1_14)


if __name__ == '__main__':
    from sys import argv
    convert(argv[1], argv[2])

# TODO-s:

# upload to pip, and gui 

# maybe support for custom instruments (command block playsound and bool option for including it or not)
# support for different volumes, panning (position of the noteblock, dummy splitline), and maybe pitch fine tuning (command block playsound)