#!/usr/bin/env python3

import nbtlib as nbt

# can create a sponge schematic file
class Schematic:
    
    def __init__(self, width, height, length):
        self._palette = {"minecraft:air": nbt.Int(0)}
        self._palette_index = 1
        self._blocks = {}
        self._width = width
        self._height = height
        self._length = length
        
    # block is string in format minecraft:redstone_wire[east=side,north=none,power=0,south=none,west=side]
    # "minecraft:" is appended if not present, and blockstates will be ordered alphabetically
    # there is no format check, block is assumed to be correct
    def setblock(self, x, y, z, block):
        if x<0 or y<0 or z<0 or x>=self._width or y>=self._height or z>=self._length:
            raise ValueError(f"input position x={x} y={y} z={z} for block {block} doesn't fit inside "
                             f"width={self._width} height={self._height} length={self._length}")
        if ":" not in block:
            block = "minecraft:" + block
        if "[" in block:
            splitted = block.split("[")
            blockstates = splitted[1][:-1].split(",")
            blockstates.sort()
            block = splitted[0] + "[" + ",".join(blockstates) + "]"
        if block not in self._palette:
            self._palette[block] = nbt.Int(self._palette_index)
            self._palette_index += 1
        idx = x + self._width * (z + self._length * y)
        self._blocks[idx] = self._palette[block];
    
    # path's extension should be ".schem"
    # sponge schematic version 2 specification:
    # https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-2.md
    def save(self, path, data_version=2225): # 2225 = Minecraft 1.15.0
        block_data = []
        # BlockData is of type varint, see specification; code is copied from:
        # https://github.com/SpongePowered/Sponge/blob/aa2c8c53b4f9f40297e6a4ee281bee4f4ce7707b/src/main/java/org/spongepowered/common/data/persistence/SchematicTranslator.java#L230-L251
        # in short: int 0x00-0x0F becomes the same byte, 0x00-0x0F
        # int 0b010101_0010111 becomes bytes 1_0010111 0_0010101
        # int 0bxxxxxxxyyyyyyyzzzzzzz becomes bytes 1zzzzzzz 1yyyyyyy 0xxxxxxx
        for idx in range(self._width * self._height * self._length):
            #palette_id = 0 if not idx in self._blocks else self._blocks[idx] TODO remove this if below works
            palette_id = self._blocks.get(idx, 0) # 0 if idx wasn't found
            while (palette_id & -128) != 0: # if id is more than 7 digits in binary
                block_data.append(palette_id & 127 | 128) # append the last 7 digits, with 1 as the 8th digit
                palette_id = palette_id >> 7 # shift the 7 digits we just stored away
            block_data.append(palette_id) # if it's less than 7 digits in binary, just store it
        
        new_file = nbt.File({
            "Schematic": nbt.Compound({
                "Version": nbt.Int(2), # format version
                "DataVersion": nbt.Int(data_version), # Minecraft version
                "Width": nbt.Short(self._width),
                "Height": nbt.Short(self._height),
                "Length": nbt.Short(self._length),
                "Palette": nbt.Compound(self._palette),
                "BlockData": nbt.ByteArray(block_data),
            })
        }, gzipped=True)
        new_file.save(path)

# usage:
"""
schem = Schematic(4, 3, 2) # width, height, length
schem.setblock(0, 1, 0, "minecraft:redstone_wire[east=side,north=none,power=0,south=none,west=side]")
schem.setblock(0, 0, 0, "polished_andesite_slab[type=top]")
schem.setblock(2, 1, 0, "redstone_wall_torch")
schem.setblock(2, 1, 1, "polished_andesite")
schem.setblock(1, 1, 0, "redstone_wire")
schem.setblock(1, 0, 0, "polished_granite")
schem.setblock(3, 1, 0, "minecraft:repeater[delay=4]")
schem.setblock(3, 0, 0, "blue_wool")
schem.save("my_test_from_spongeschematic.schem")
"""
