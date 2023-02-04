#!/usr/bin/env python3

from sys import argv
from .main import convert
from . import __version__

def cli_main():
    if not 3 <= len(argv) <= 5:
        print(f"Version {__version__}\nUsage: {argv[0]} input.nbs output.schem [use_redstone_lamp: True or False] [sides: -1, 1, 2 or 3]\n(Where [...] is optional)")
    else:
        lamp = True
        sides = -1
        if len(argv) >= 4:
            assert argv[3] == "True" or argv[3] == "False", "Use redstone lamp's value should be True or False!"
            lamp = argv[3] == "True"
        if len(argv) == 5:
            sides = int(argv[4])
            assert sides == -1 or sides == 1 or sides == 2 or sides == 3, "Sides mode's value should be -1, 1, 2 or 3!"
        convert(argv[1], argv[2], use_redstone_lamp=lamp, sides_mode=sides)


if __name__ == '__main__':
    cli_main()