#!/usr/bin/env python3

from builder import get_delay_length

for md in range(2, 10):
    for delay in range(md, 100):
        print(f"{md} md, {delay} delay: {get_delay_length(delay, md)} length")
