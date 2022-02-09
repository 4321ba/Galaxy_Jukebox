#!/usr/bin/env python3

from note_lines import convert
from sys import argv

convert(argv[1], argv[2])

"""
lines = note_lines_from_nbs_file(pynbs_read("082_City_in_the_Sky_Ahmsord.nbs"))

#schem = Schematic(len(lines) // 4 + 2, 33, 2000)
#for i, line in enumerate(lines):
    #line.create_circuit(schem, Vector(i//8 * 2, (i%8)*4+1, 0))

schem = Schematic()#TODO
import note_lines
note_lines.build_lines(schem, lines, 5, 5, 5, 7)


lines = note_lines_from_nbs_file(pynbs_read("126_Countdown_to_Corruption_Boss_Battle_11.nbs"))
schem = Schematic()
import note_lines
note_lines.build_lines(schem, lines, 11, 21, 11, 10)


lines = note_lines_from_nbs_file(pynbs_read("026_Yearning_for_the_Days_of_Glory_Ancient_Nemract.nbs"))
schem = Schematic()
import note_lines
note_lines.build_lines(schem, lines, 5, 7, 5, 2)


schem.save("...")
"""
#TODO: custom instruments
#TODO render distance recommendation sign
