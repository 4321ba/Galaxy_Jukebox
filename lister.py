#!/usr/bin/env python3

import sys
import nbtlib

# schematic version
# https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-2.md

nbt_file = nbtlib.load(sys.argv[1])
print(nbt_file)
