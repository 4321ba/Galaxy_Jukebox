#!/usr/bin/env python3

from vector import Vector

instrument_name = [
    "harp",
    "bass",
    "basedrum",
    "snare",
    "hat",
    "guitar",
    "flute",
    "bell",
    "chime",
    "xylophone",
    "iron_xylophone",
    "cow_bell",
    "didgeridoo",
    "bit",
    "banjo",
    "pling",
]

instrument_material = [
    "lapis_block",
    "jungle_wood",
    "black_concrete",
    "pink_concrete_powder",
    "purple_stained_glass",
    "magenta_wool",
    "clay",
    "gold_block",
    "packed_ice",
    "bone_block",
    "iron_block",
    "soul_sand",
    "pumpkin",
    "emerald_block",
    "hay_block",
    "glowstone", 
]

building_material = [
    "blue_concrete",
    "green_concrete",
    "black_concrete",
    "pink_concrete",
    "purple_concrete",
    "magenta_concrete",
    "light_gray_concrete",
    "yellow_concrete",
    "light_blue_concrete",
    "white_concrete",
    "cyan_concrete",
    "brown_concrete",
    "orange_concrete",
    "lime_concrete",
    "red_concrete",
    "gray_concrete", 
]

even_delay_buildblock = "polished_andesite"
even_delay_buildblock_slab = "polished_andesite_slab[type=top]"
odd_delay_buildblock = "polished_granite"
odd_delay_buildblock_slab = "polished_granite_slab[type=top]"
start_line_buildblock = "polished_diorite"
start_line_buildblock_slab = "polished_diorite_slab[type=top]"

def cardinal_direction(v):
    assert v.y==0 and ((abs(v.x)==1 and v.z==0) or (v.x==0 and abs(v.z)==1))
    if v.x == 1:
        return "east"
    if v.x == -1:
        return "west"
    if v.z == 1:
        return "south"
    if v.z == -1:
        return "north"


# these 3 functions are used throughout split_lines and here in build_delay, exclusively, to create blocks:

def setblock(schem, v, block):
    schem.setBlock((v.x, v.y, v.z), block)

def block_and_redstone(schem, v, buildblock, powered=False):
    schem.setBlock((v.x, v.y+0, v.z), buildblock)
    schem.setBlock((v.x, v.y+1, v.z), f"redstone_wire[east=side,north=side,power={15 if powered else 0},south=side,west=side]")
    
def block_and_repeater(schem, v, buildblock, facing_direction, delay=1, locked=False, powered=False):
    assert delay in [1, 2, 3, 4], f"Cannot create a repeater with a delay of {delay}!"
    schem.setBlock((v.x, v.y+0, v.z), buildblock)
    schem.setBlock((v.x, v.y+1, v.z), f"repeater[delay={delay},facing={cardinal_direction(-facing_direction)},locked={locked},powered={powered}]")


# return the space/blocks needed for the delay and md pair
def get_delay_length(delay, md):
    
    class DummySchematic:
        def setBlock(self, coords, block):
          pass
    
    schem = DummySchematic()
    v = Vector(0, 0, 0)
    forward = Vector(0, 0, 1)
    build_delay(schem, "", v, forward, delay, md)
    return v.z

"""
creates the delay in the form:

<> : repeater
-  : redstone
≤≥ : repeater or redstone
█  : block
?  : something

from the side:
>>>>>>█
██████-
≤????<█
█????█ 

the signal goes in on the top, and after delay time, it comes back at the bottom
these can be stacked one after another, creating the heart of the whole contraption

if loopback is false, the redstone at the end won't get placed, making it useful for turning sideway
v is modified to represent the actual position!
"""
def build_delay(schem, buildblock, v, forward, delay, md, loopback=True):
    
    
    # helper functions for e.g.: placing a redstone down and a repeater up
    # these additionally move v forward, as it is always needed after placing these

    def d_redstone_u_repeater(schem, buildblock, v, forward, u_delay):
        block_and_redstone(schem, v, buildblock)
        block_and_repeater(schem, v + Vector(0, 2, 0), buildblock, forward, delay=u_delay)
        v += forward

    def d_repeater_u_repeater(schem, buildblock, v, forward, d_delay, u_delay):
        block_and_repeater(schem, v, buildblock, -forward, delay=d_delay)
        block_and_repeater(schem, v + Vector(0, 2, 0), buildblock, forward, delay=u_delay)
        v += forward

    def d_block_u_repeater(schem, buildblock, v, forward, u_delay):
        setblock(schem, v + Vector(0, 1, 0), buildblock)
        block_and_repeater(schem, v + Vector(0, 2, 0), buildblock, forward, delay=u_delay)
        v += forward

    def d_loopback_u_block(schem, buildblock, v, forward, loopback):
        if loopback:
            block_and_redstone(schem, v + Vector(0, 1, 0), buildblock)
        else:
            setblock(schem, v + Vector(0, 1, 0), buildblock)
        setblock(schem, v + Vector(0, 3, 0), buildblock)
        v += forward


    # md: minimum of the delays in the entire line afterwards, determines how much delay we can put onto the repeaters
    # we can't put 2 repeaters after one another on the bottom line with md=2 because of this bug:
    # https://bugs.mojang.com/browse/MC-54711
    # because of this, with even md, we can't end with a repeater with delay=md//2 on the bottom 
    # also related is that with md6 e.g.:
    # a 3 tick repeater can only go after a 1 tick one if the pulse is already 3 tick long, it doesn't work if the pulse is shorter

    # 1 tick repeaters everywhere, repeater chaining only at the top
    def create_delay_md2(schem, buildblock, v, forward, delay, loopback):
        if delay % 3 != 2: # 0 or 1 is the remainder
            delay -= 1
            d_redstone_u_repeater(schem, buildblock, v, forward, 1)
        if delay % 3 == 2: # 0 or 2 was the remainder originally
            delay -= 2
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 1)
        while delay > 0:
            delay -= 3
            d_block_u_repeater(schem, buildblock, v, forward, 1)
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 1)
        assert delay == 0, f"There shouldn't be any delay remaining, but it is {delay}!"
        d_loopback_u_block(schem, buildblock, v, forward, loopback)

    # 1 tick repeaters everywhere, repeater chaining at the bottom and the top too
    def create_delay_md3(schem, buildblock, v, forward, delay, loopback):
        if delay % 2 == 1:
            delay -= 1
            d_redstone_u_repeater(schem, buildblock, v, forward, 1)
        while delay > 0:
            delay -= 2
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 1)
        assert delay == 0, f"There shouldn't be any delay remaining, but it is {delay}!"
        d_loopback_u_block(schem, buildblock, v, forward, loopback)

    # 2 tick repeaters everywhere, repeater chaining at the bottom needs to end with a 1 tick repeater
    # this is becoming a bit of a pattern, but here it still may be better written out explicit
    # I'll generalize with md6
    def create_delay_md4(schem, buildblock, v, forward, delay, loopback):
        if delay == 4:
            delay -= 4
            d_repeater_u_repeater(schem, buildblock, v, forward, 2, 2)
        elif delay % 4 == 0:
            delay -= 4
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 1)
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 1)
        elif delay % 4 == 1:
            delay -= 5
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 1)
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 2)
        elif delay % 4 == 2:
            delay -= 2
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 1)
        elif delay % 4 == 3:
            delay -= 3
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 2)
        while delay > 0:
            delay -= 4
            d_repeater_u_repeater(schem, buildblock, v, forward, 2, 2)
        assert delay == 0, f"There shouldn't be any delay remaining, but it is {delay}!"
        d_loopback_u_block(schem, buildblock, v, forward, loopback)

    # same as md4, except we can chain 2 tick repeaters everywhere
    def create_delay_md5(schem, buildblock, v, forward, delay, loopback):
        if delay % 4 == 0:
            while delay > 0:
                delay -= 4
                d_repeater_u_repeater(schem, buildblock, v, forward, 2, 2)
            assert delay == 0, f"There shouldn't be any delay remaining, but it is {delay}!"
            d_loopback_u_block(schem, buildblock, v, forward, loopback)
        else:
            create_delay_md4(schem, buildblock, v, forward, delay, loopback)

    # 3 tick repeaters everywhere, repeater chaining at the bottom needs to end with a 2 or 1 tick repeater
    def create_delay_md6(schem, buildblock, v, forward, delay, loopback):
        if delay == 6:
            delay -= 6
            d_repeater_u_repeater(schem, buildblock, v, forward, 3, 3)
        elif delay % 6 in [0, 1]:
            rem = delay % 6
            delay -= (6 + rem)
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 1)
            d_repeater_u_repeater(schem, buildblock, v, forward, 1 + rem, 3)
        elif delay % 6 in [2, 3, 4, 5]:
            rem = delay % 6
            delay -= rem
            d_delay = 2 if rem == 5 else 1
            d_repeater_u_repeater(schem, buildblock, v, forward, d_delay, rem - d_delay)
        while delay > 0:
            delay -= 6
            d_repeater_u_repeater(schem, buildblock, v, forward, 3, 3)
        assert delay == 0, f"There shouldn't be any delay remaining, but it is {delay}!"
        d_loopback_u_block(schem, buildblock, v, forward, loopback)

    # same as md6, except we can chain 3 tick repeaters everywhere
    def create_delay_md7(schem, buildblock, v, forward, delay, loopback):
        if delay % 6 == 0:
            while delay > 0:
                delay -= 6
                d_repeater_u_repeater(schem, buildblock, v, forward, 3, 3)
            assert delay == 0, f"There shouldn't be any delay remaining, but it is {delay}!"
            d_loopback_u_block(schem, buildblock, v, forward, loopback)
        else:
            create_delay_md6(schem, buildblock, v, forward, delay, loopback)

    # 4 tick repeaters everywhere, repeater chaining at the bottom needs to end with a <4 tick repeater
    def create_delay_md8(schem, buildblock, v, forward, delay, loopback):
        if delay == 8:
            delay -= 8
            d_repeater_u_repeater(schem, buildblock, v, forward, 4, 4)
        elif delay % 8 in [0, 1]:
            rem = delay % 8
            delay -= (8 + rem)
            d_repeater_u_repeater(schem, buildblock, v, forward, 1, 1)
            d_repeater_u_repeater(schem, buildblock, v, forward, 2 + rem, 4)
        elif delay % 8 in [2, 3, 4, 5, 6, 7]:
            rem = delay % 8
            delay -= rem
            d_delay = rem - 4 if rem in [6, 7] else 1
            d_repeater_u_repeater(schem, buildblock, v, forward, d_delay, rem - d_delay)
        while delay > 0:
            delay -= 8
            d_repeater_u_repeater(schem, buildblock, v, forward, 4, 4)
        assert delay == 0, f"There shouldn't be any delay remaining, but it is {delay}!"
        d_loopback_u_block(schem, buildblock, v, forward, loopback)

    # same as md8, except we can chain 4 tick repeaters everywhere
    def create_delay_md9_or_above(schem, buildblock, v, forward, delay, loopback):
        if delay % 8 == 0:
            while delay > 0:
                delay -= 8
                d_repeater_u_repeater(schem, buildblock, v, forward, 4, 4)
            assert delay == 0, f"There shouldn't be any delay remaining, but it is {delay}!"
            d_loopback_u_block(schem, buildblock, v, forward, loopback)
        else:
            create_delay_md8(schem, buildblock, v, forward, delay, loopback)

    delay_functions = {
        2: create_delay_md2,
        3: create_delay_md3,
        4: create_delay_md4,
        5: create_delay_md5,
        6: create_delay_md6,
        7: create_delay_md7,
        8: create_delay_md8,
        9: create_delay_md9_or_above
    }
    
    # actually executing the needed thing:
    delay_functions[min(md, 9)](schem, buildblock, v, forward, delay, loopback)
