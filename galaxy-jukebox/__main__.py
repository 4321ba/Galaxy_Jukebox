#!/usr/bin/env python3

from sys import argv
from .main import convert

if __name__ == '__main__':
    if len(argv) != 3:
        print(f"Usage: {argv[0]} input.nbs output.schem")
    else:
        convert(argv[1], argv[2])
