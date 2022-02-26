#!/usr/bin/env python3

from main import convert
from os import listdir

for filename in listdir():
    if filename[-4:] == ".nbs":
        convert(filename, filename[:-4] + ".schem")
