#!/usr/bin/env python3

from sys import argv
from .main import convert
from . import __version__

def cli_main():
    if len(argv) != 3:
        print(f"Version {__version__}\nUsage: {argv[0]} input.nbs output.schem")
    else:
        convert(argv[1], argv[2])


if __name__ == '__main__':
    cli_main()