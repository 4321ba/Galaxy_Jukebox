#!/usr/bin/env python3

from warnings import warn
import nbtlib as nbt

# can create a sponge schematic file
class Schematic:
    
    def __init__(self):
        self._palette = {"minecraft:air": nbt.Int(0)}
        self._palette_index = 1
        self._blocks = {}
        
    # block is string in format minecraft:redstone_wire[east=side,north=none,power=0,south=none,west=side]
    # "minecraft:" is appended if not present, and blockstates will be ordered alphabetically
    # there is no format check, block is assumed to be correct
    def setblock(self, x, y, z, block):
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
        coords = (x, y, z)
        if coords in self._blocks:
            warn(f"Replacing a perviously set block at {coords} with {block}!")
        self._blocks[coords] = self._palette[block];
    
    # path's extension should be ".schem"
    # sponge schematic version 2 specification:
    # https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-2.md
    def save(self, path, data_version=1952): # 1952 = Minecraft 1.14.0, 2225 = Minecraft 1.15.0
        if not self._blocks:
            raise ValueError("You shouldn't save an empty schematic, use setblock first!")
        
        min_x, min_y, min_z = next(iter(self._blocks)) # first block
        max_x, max_y, max_z = min_x, min_y, min_z
        #print(max_x, max_y, max_z, min_x, min_y, min_z)#TODO
        for coords in self._blocks:
            min_x = min(min_x, coords[0])#TODO with if-s and separate function maybe
            max_x = max(max_x, coords[0])
            min_y = min(min_y, coords[1])
            max_y = max(max_y, coords[1])
            min_z = min(min_z, coords[2])
            max_z = max(max_z, coords[2])
        #print(max_x, max_y, max_z, min_x, min_y, min_z)
        
        block_data = []
        # BlockData is of type varint, see specification; code is copied from:
        # https://github.com/SpongePowered/Sponge/blob/aa2c8c53b4f9f40297e6a4ee281bee4f4ce7707b/src/main/java/org/spongepowered/common/data/persistence/SchematicTranslator.java#L230-L251
        # in short: int 0x00-0x0F becomes the same byte, 0x00-0x0F
        # int 0b010101_0010111 becomes bytes 1_0010111 0_0010101
        # int 0bxxxxxxxyyyyyyyzzzzzzz becomes bytes 1zzzzzzz 1yyyyyyy 0xxxxxxx
        for y in range(min_y, max_y + 1):
            for z in range(min_z, max_z + 1):
                for x in range(min_x, max_x + 1):
                    palette_id = self._blocks.get((x, y, z), 0) # 0 if idx wasn't found
                    while (palette_id & -128) != 0: # if id is more than 7 digits in binary
                        block_data.append(palette_id & 127 | 128) # append the last 7 digits, with 1 as the 8th digit
                        palette_id = palette_id >> 7 # shift the 7 digits we just stored away
                    block_data.append(palette_id) # if it's less than 7 digits in binary, just store it
        
        new_file = nbt.File({
            "Version": nbt.Int(2), # format version
            "DataVersion": nbt.Int(data_version), # Minecraft version
            "Width": nbt.Short(max_x - min_x + 1),
            "Height": nbt.Short(max_y - min_y + 1),
            "Length": nbt.Short(max_z - min_z + 1),
            "Palette": nbt.Compound(self._palette),
            "BlockData": nbt.ByteArray(block_data),
        }, gzipped=True, root_name="Schematic")
        new_file.save(path)

# usage:
"""
schem = Schematic() # you can place blocks on negative coordinates too, and you don't need to give width/height/length
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
