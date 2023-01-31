#!/usr/bin/env python3

from vector import Vector
import builder as bld

# represents a redstone wire line corresponding to a single instrument/pitch noteblock
# it is split enough to be actually created with redstone, and has the methods to do so
class SplitLine:
    
    # key and instrument are from pynbs, ticks is a dictionary (or list) of ints, in gameticks, when the noteblock needs to sound
    def __init__(self, key, instrument, ticks):
        key -= 33
        while key < 0:
            key += 12
        while key > 24:
            key -= 12
        self.note = key
        self.instrument = instrument
        ticks = sorted(ticks) # sorted list, count (it was the value of the dict) is no longer needed
        assert ticks, "SplitLine shouldn't be initialized with empty ticks!"
        self._is_even = ticks[0] % 2 == 0
        # adding 4gt to the first delay value (as if the 0th note was at gametick -4), to make it behave like the rest of the delays
        # //2: from gametick to redstone tick, _is_even remembers if this is an odd line
        self._delays = [(4 + ticks[0]) // 2] + [(ticks[i+1] - ticks[i]) // 2 for i in range(len(ticks) - 1)]
        assert min(self._delays) >= 2, f"SplitLine needs a minimum delay of at least 2, got {min(self._delays)} instead!"
    
    def __repr__(self):
        return f"[ProcessedLine i,k:{self.instrument},{self.note} delays:{self._delays}]"
    
    # serves as a post-initialization, where it gets its position, and other attributes
    def begin_circuit(self, schem, pos, forward, side, dist_to_middle, row, max_row, col, side_col, max_col):
        self._schem = schem
        pos.y -= 1 # pos.y is where the noteblock is, but it's better to store the block below
        self._pos = pos
        self._forward = forward
        self._side = side # either "left" "middle" or "right"
        # the blocks this line needs to go sideways and forward to be aligned with the side "middle"
        # it correlates with the column it is in
        self._dist_to_middle = dist_to_middle
        self._buildblock = bld.building_material[self.instrument]

        assert side_col < max_col and row < max_row, "Given row or col is out of bounds!"
        self.row = row # the odd rows are 1 block to the right compared to the even rows
        self._max_row = max_row # the height of the thing
        # the column, absolute, and every column has the same height (the checkerboard pattern): every row×col has exactly one noteblock (if inside the range)
        self.col = col # goes from 0, and up everytime
        self._side_col = side_col # goes from 0 up, but goes back to 0 when on the next side (there are 1, 2 or 3 sides)
        self._max_col = max_col # the max number of columns *on the same side* that the line is on (left/middle/right width)
    
    def get_pos(self):
        return self._pos
    
    def build_noteblock(self, use_redstone_lamp):

        def conditional_patch_above_below(vec):
            # patching above the 2nd row so it has the same height as the neighbors
            if self.row == 1:
                bld.setblock(self._schem, vec + up * 3, self._buildblock)
                bld.setblock(self._schem, vec + up * 4, self._buildblock)
            # below the 2nd to last row as well
            # we also want an extra row of blocks under the wall, so it looks better 
            if self.row == self._max_row - 2:
                bld.setblock(self._schem, vec - up * 4, self._buildblock)
                bld.setblock(self._schem, vec - up * 3, self._buildblock)
                bld.setblock(self._schem, vec - up * 2, self._buildblock)
            elif self.row == self._max_row - 1:
                bld.setblock(self._schem, vec - up * 2, self._buildblock)

        v = self._pos
        up = Vector(0, 1, 0)
        # tripwire is needed for sand/concrete powder, so that it doesn't fall off
        if use_redstone_lamp or bld.instrument_name[self.instrument] == "snare":
            bld.setblock(self._schem, v - up, "redstone_lamp" if use_redstone_lamp else "tripwire")
        bld.setblock(self._schem, v, bld.instrument_material[self.instrument])
        bld.setblock(self._schem, v + up, f"note_block[note={self.note},instrument={bld.instrument_name[self.instrument]}]")
        v += self._forward
        bld.block_and_redstone(self._schem, v - up, self._buildblock)
        bld.setblock(self._schem, v + up * 1, self._buildblock)
        bld.setblock(self._schem, v + up * 2, self._buildblock)

        conditional_patch_above_below(v)
        # we also patch next to the first and the last column
        # for the first and the last col of every side, we add one more continuous pile of blocks to the left/right
        if self._side_col == 0 and self.row % 2 == 0:
            left = self._forward.rotated()
            bld.setblock(self._schem, v + left + up * 2, self._buildblock)
            bld.setblock(self._schem, v + left + up * 1, self._buildblock)
            bld.setblock(self._schem, v + left + up * 0, self._buildblock)
            bld.setblock(self._schem, v + left - up * 1, self._buildblock)
            conditional_patch_above_below(v + left)
        if self._side_col == self._max_col - 1 and self.row % 2 == 1:
            right = self._forward.rotated(positive_direction=False)
            bld.setblock(self._schem, v + right + up * 2, self._buildblock)
            bld.setblock(self._schem, v + right + up * 1, self._buildblock)
            bld.setblock(self._schem, v + right + up * 0, self._buildblock)
            bld.setblock(self._schem, v + right - up * 1, self._buildblock)
            conditional_patch_above_below(v + right)

        v += self._forward
        bld.block_and_repeater(self._schem, v, self._buildblock, -self._forward)
        v += self._forward
    
    def build_side_turn(self, max_delay):
        if self._side == "middle":
            self._delays[0] += max_delay # we just add the difference in timing to the other notes to the delay of the first note
            return
        v = self._pos
        
        # rc: redstone count, before the repeater, max 15
        rc = 0
        placed_delay = 0
        for rotation in [True, False]:
            for i in range(self._dist_to_middle):
                if rc == 15 or (rc == 14 and i+2 == self._dist_to_middle):
                    bld.block_and_repeater(self._schem, v, self._buildblock, -self._forward)
                    placed_delay += 1
                    rc = 0
                else:
                    bld.block_and_redstone(self._schem, v, self._buildblock)
                    rc += 1
                v += self._forward
            
            if rotation:
                v -= self._forward
                self._forward.rotate(positive_direction = (self._side=="right"))
                v += self._forward
        
        # here we know that we didn't end with a repeater, because if the last block had been a repeater,
        # then the 2nd to last block was rc==14 and i+2==loopmax, so we put a repeater there instead
        # this means that we are safe to place a repeater here (see builder.py and "md" for details)
        # so ending with 1 repeater everywhere, so that in the next step we can rely on that
        bld.block_and_repeater(self._schem, v, self._buildblock, -self._forward)
        v += self._forward
        placed_delay += 1
        assert rc <= 15, f"Redstone count is >15 where the lines turn towards the jukebox, it is {rc} (in col {self.col} row {self.row})!"
        assert placed_delay <= max_delay, f"Somehow we placed more delay then allowed, when turning, placed {placed_delay}, allowed {delay} (in col {self.col} row {self.row})!"
        self._delays[0] += max_delay - placed_delay # adding the remaining needed delay, to be in sync with the others
        
    def build_vertical_adjustment(self):
        v = self._pos
        max_needed_diff = self._max_row - 1
        needed_diff = max_needed_diff - 2 * self.row
        for i in range(max_needed_diff + 1):
            if i + abs(needed_diff) > max_needed_diff:
                v += Vector(0, -1 if needed_diff < 0 else 1, 0)
            bld.block_and_redstone(self._schem, v, self._buildblock)
            v += self._forward
            if (i+1) % 14 == 0:
                bld.block_and_repeater(self._schem, v, self._buildblock, -self._forward)
                v += self._forward
                bld.block_and_redstone(self._schem, v, self._buildblock)
                v += self._forward
        # ending with a repeater again:
        bld.block_and_repeater(self._schem, v, self._buildblock, -self._forward)
        v += self._forward
    
    # horizontal adjustment both for left/right sides and for odd rows
    def build_horizontal_adjustment(self):
        v = self._pos
        bld.block_and_redstone(self._schem, v, self._buildblock)
        v += self._forward
        vertical_offset = Vector(0, -1 if self.col % 2 == 0 else 1, 0)
        if self._side != "middle":
            v += vertical_offset
            sideways = self._forward.rotated(positive_direction = (self._side=="right"))
        for i in range(3):
            bld.block_and_redstone(self._schem, v, self._buildblock)
            v += self._forward
            if self._side != "middle":
                bld.block_and_redstone(self._schem, v, self._buildblock)
                v += sideways
        bld.block_and_redstone(self._schem, v, self._buildblock)
        v += self._forward
        if self._side != "middle":
            v -= vertical_offset
        bld.block_and_redstone(self._schem, v, self._buildblock)
        v += self._forward
        
        if self.row % 2 == 0:
            bld.block_and_redstone(self._schem, v, self._buildblock)
            v += self._forward
        else:
            v += vertical_offset
            sideways = self._forward.rotated()
            bld.block_and_redstone(self._schem, v, self._buildblock)
            v += sideways
            bld.block_and_redstone(self._schem, v, self._buildblock)
            v += self._forward
            v -= vertical_offset
        bld.block_and_redstone(self._schem, v, self._buildblock)
        v += self._forward
            
    def build_junction(self, max_delay):
        v = self._pos
        left = self._forward.rotated()
        up = Vector(0, 1, 0)
        if self.col % 2 == 0:
            bld.block_and_repeater(self._schem, v + left + up * 2, bld.even_delay_buildblock, -left)
        else:
            bld.block_and_redstone(self._schem, v + left + up * 2, bld.even_delay_buildblock)
        bld.block_and_redstone(self._schem, v, self._buildblock)
        bld.block_and_redstone(self._schem, v + up * 2, bld.even_delay_buildblock)
        v += self._forward
        
        bld.block_and_repeater(self._schem, v, self._buildblock, -self._forward)
        if self._is_even:
            bld.block_and_redstone(self._schem, v + up * 2, bld.even_delay_buildblock)
        v += self._forward
        
        if self.col % 2 == 0:
            bld.block_and_repeater(self._schem, v + left + up * 3, bld.odd_delay_buildblock, -left)
        else:
            bld.block_and_redstone(self._schem, v + left + up * 3, bld.odd_delay_buildblock)
        bld.setblock(self._schem, v + up, self._buildblock)
        if self._is_even:
            bld.setblock(self._schem, v + up * 3, bld.even_delay_buildblock)
            bld.setblock(self._schem, v + up * 4, bld.odd_delay_buildblock)
        else:
            bld.block_and_redstone(self._schem, v + up * 3, bld.odd_delay_buildblock)
        v += self._forward
        
        bld.block_and_redstone(self._schem, v, self._buildblock)
        bld.block_and_repeater(self._schem, v + up * 2, self._buildblock, self._forward)
        v += self._forward
        assert max_delay >= self.col // 2, f"Max delay ({max_delay}) given is too low, we'd need a delay of {needed_delay}!"
        # adding to before the first note, it needs delay because of the repeaters of where the signal comes from
        self._delays[0] += max_delay - self.col // 2
    
    # this is the delay needed to build the vertical connection (15 block limit), above this line, as compensation
    def add_delay_for_vertical_connection(self):
        self._delays[0] += self.row // 3
    
    
    """
    <> : repeater
    -  : redstone
    ≤≥ : repeater or redstone
    █  : block
    ?  : something
    one delay looks like this from the side:
    
    >>>>>>█  a  t  o
    ██████-  n  h  n
    ≤????<█  o  e  e
    █????█   -  r
    
    the actual design and length depends on the delay and md, but
    - the upper row must start with a repeater and end with a repeater
    - the lower row must end with a repeater or a redstone, and start with a repeater
    however: we can put redstone on the left side like this just fine:
    -->>>>>>█  a  t  o
    ████████-  n  h  n
    --≤????<█  o  e  e
    ███????█   -  r
    and that will help with spacing the turns properly
    
    this function builds the entire spiral thing for this particular line, taking self._delays and turns into account
    turns is [10, 22, 15] e.g., meaning it needs to turn left after 10 blocks, and again after 22,... relative to the previous turn
    corner blocks count towards the previous count
    """
    def build_delays(self, turns):
        v = self._pos
        up = Vector(0, 1, 0)
        placed_blocks = 0 # blocks placed since the previous turn
        for delay_index, delay in enumerate(self._delays):
            # md = minimum delay, needed for how much delay can be put onto repeaters, and for more too
            md = min(self._delays[delay_index:]) # could be optimized: only recalculate this if previous delay==md
            
            run_again = True
            while run_again:
                run_again = False
                next_length = bld.get_delay_length(delay, md)
                
                # if turns is empty or there's enough space:
                if not turns or placed_blocks + next_length + 1 < turns[0]:
                    bld.build_delay(self._schem, self._buildblock, v, self._forward, delay, md)
                    placed_blocks += next_length
                # if there isn't enough space to just place the delay and move on, and we have to turn somewhere
                else:
                    # if we strech it out one more block, it will fit perfectly
                    if placed_blocks + next_length + 1 == turns[0]:
                        bld.block_and_redstone(self._schem, v, self._buildblock)
                        bld.block_and_redstone(self._schem, v + up * 2, self._buildblock)
                        v += self._forward
                        placed_blocks += 1
                    # if it fits perfectly (also including the previous case)
                    if placed_blocks + next_length == turns[0]:
                        bld.build_delay(self._schem, self._buildblock, v, self._forward, delay, md)
                    # we need to cut the delay in half, or more, because it is larger than the blocks left until the turn
                    else:
                        run_again = True # we need to keep placing the delay, while staying at the current index of self._delays
                        mind = min(md, 9)
                        remaining_blocks = turns[0] - placed_blocks
                        # if we can't split it into two pieces and have to put redstone as spacer, before the turn
                        # delay should be at least minimum delay (md) when placing
                        if delay < 2 * mind or remaining_blocks < bld.get_delay_length(mind, mind):
                            """
                            for md in range(2,10): # looping through every possible mind
                                print(md, bld.get_delay_length(md, md), md*2-1, bld.get_delay_length(md*2-1, md))
                            out:
                            2 2  3 3
                            3 3  5 4
                            4 2  7 3
                            5 3  9 4
                            6 2 11 3
                            7 3 13 4
                            8 2 15 3
                            9 3 17 4
                            
                            there should be less than 4 remaining blocks, because otherwise it should have been placed
                            previously, seeing that with every md the biggest delay that can't be split (md*2-1)
                            fits into the 4 blocks
                            there should be more than 1 remaining block, because otherwise the previous delay would have been streched out
                            also the redstone wouldn't be able to connect with the block if it was only 1 block remaining
                            """
                            assert remaining_blocks in [2, 3], f"Remaining blocks should be 2 or 3, but it is {remaining_blocks}!"
                            for i in range(remaining_blocks):
                                bld.block_and_redstone(self._schem, v, self._buildblock)
                                bld.block_and_redstone(self._schem, v + up * 2, self._buildblock)
                                v += self._forward
                        # now we are sure that we can somehow split the delay into >=2 pieces, but how
                        else:
                            delay_before_turn = bisect_delay_halving_point(remaining_blocks, delay, mind)
                            delay -= delay_before_turn # for next iteration
                            blocks_for_delay = bld.get_delay_length(delay_before_turn, md)
                            remaining_blocks -= blocks_for_delay
                            """
                            here ideally we find a way to get a perfectly fitting delay before the turn, but it is not guaranteed:
                            if delay=md fits in before the turn (which it does if we are here),
                            that means that there exists a delay that fits in perfectly just before the turn
                            however: if the remaining delay after the turn is less than md, that means we need to give up the perfectness
                            to save some delay for after the turn, so that it can be placed with md (delay should always be >= md)
                            dunno if remaining_blocks==3 is actually possible, but remaining_blocks==4 for sure shouldn't be
                            because every md with delay=md fits into 3 blocks, so if we subtract 3 blocks here,
                            there should be plenty of delay remaining after the turn for it to be >=md
                            """
                            assert remaining_blocks in [0, 1, 2, 3], f"Remaining blocks should be 0, 1, 2 or 3, but it is {remaining_blocks}!"
                            for i in range(remaining_blocks):
                                bld.block_and_redstone(self._schem, v, self._buildblock)
                                bld.block_and_redstone(self._schem, v + up * 2, self._buildblock)
                                v += self._forward
                            bld.build_delay(self._schem, self._buildblock, v, self._forward, delay_before_turn, md, loopback=False)
                    # and turning, in case we need to:
                    v -= self._forward
                    self._forward.rotate()
                    v += self._forward
                    placed_blocks = 0
                    turns.pop(0)

# mind <= 9
# with binary search!
# for the history of this function, see:
# https://github.com/4321ba/Galaxy_Jukebox/blob/fb43d9307477052ae2116b9a90e35f7e8167b977/split_lines.py#L312-L359
def bisect_delay_halving_point(remaining_blocks, delay, mind):
    # remotely based on: https://www.javatpoint.com/binary-search-in-python
    low = mind
    high = delay - mind
    while low <= high:
        mid = (low + high) // 2
        delay_before_turn = mid
        delay_after_turn = delay - delay_before_turn
        almost_too_long = bld.get_delay_length(delay_before_turn + 1, mind) > remaining_blocks or delay_after_turn == mind
        too_long = bld.get_delay_length(delay_before_turn, mind) > remaining_blocks
        if almost_too_long and too_long:
            high = mid - 1
        elif not almost_too_long and not too_long:
            low = mid + 1
        elif almost_too_long and not too_long:
            return delay_before_turn
        else: # not almost_too_long and too_long
            assert False, "Impossible! almost_too_long is false while too_long is true, this would mean that a bigger delay takes less blocks than a smaller one or something like that."
    assert False, "Impossible! No delay halving point found, this function is only meant to be called if there is a solution."


# begin_v is the coordinate of the even (andesite) connector of the very first (upper left) noteblock line
# delay compensation for extra added repeaters is in line.add_delay_for_vertical_connection()
def build_vertical_connection(schem, begin_v, height):
    
    def double_block_and_redstone(schem, andesite_v, rel_granite_v):
        bld.block_and_redstone(schem, andesite_v, bld.even_delay_buildblock)
        bld.block_and_redstone(schem, andesite_v + rel_granite_v, bld.odd_delay_buildblock)
        
    def double_block_and_repeater(schem, andesite_v, rel_granite_v, direction):
        bld.block_and_repeater(schem, andesite_v, bld.even_delay_buildblock, direction)
        bld.block_and_repeater(schem, andesite_v + rel_granite_v, bld.odd_delay_buildblock, direction)
        
    forward = Vector(1, 0, 0)
    for h in range(height - 1):
        v = begin_v - Vector(0, 4 * h, 0)
        double_block_and_redstone(schem, v, Vector(0, 0, 2))
        v += forward
        bld.block_and_redstone(schem, v + Vector(0, -3, 0), bld.even_delay_buildblock_slab)
        bld.block_and_redstone(schem, v + Vector(0, -3, 2), bld.odd_delay_buildblock_slab)
        bld.block_and_redstone(schem, v + Vector(0, -1, 0), bld.even_delay_buildblock_slab)
        bld.block_and_redstone(schem, v + Vector(0, -1, 2), bld.odd_delay_buildblock_slab)
        v += forward
        if (h+1) % 3 == 0:
            double_block_and_repeater(schem, v + Vector(0, -3, 0), Vector(0, 0, 2), forward)
            double_block_and_redstone(schem, v + Vector(0, -1, 0), Vector(0, 0, 2))
            v += forward
        double_block_and_redstone(schem, v + Vector(0, -2, 0), Vector(0, 0, 2))
    
    # last one separately
    v = begin_v - Vector(0, 4 * (height - 1), 0)
    double_block_and_redstone(schem, v, Vector(0, 0, 2))
    v += forward
    v += Vector(0, -1, 0)
    double_block_and_repeater(schem, v, Vector(0, 0, 2), -forward)
    v += forward
    double_block_and_redstone(schem, v, Vector(0, 0, 2))
    v += forward
    double_block_and_redstone(schem, v, Vector(0, 0, 2))
    # corner:
    bld.block_and_redstone(schem, v + Vector(1, 0, 2), bld.odd_delay_buildblock)
    bld.block_and_redstone(schem, v + Vector(2, 0, 2), bld.odd_delay_buildblock)
    bld.block_and_redstone(schem, v + Vector(2, 0, 1), bld.odd_delay_buildblock)
    bld.block_and_redstone(schem, v + Vector(2, 0, 0), bld.odd_delay_buildblock)
    
    forward.rotate()
    v += forward
    return v

# v is the coordinate of the block before the andesite/even gt repeater, at the bottom
# v + Vector(2, 0, 0) is the block before the granite/odd gt repeater
def build_1gt_delayer(schem, v, forward):
    right = forward.rotated(positive_direction=False)
    up = Vector(0, 1, 0)
    bld.block_and_redstone(schem, v, bld.even_delay_buildblock)
    bld.block_and_redstone(schem, v + right * 2, bld.odd_delay_buildblock)
    v += forward
    bld.block_and_redstone(schem, v - up, bld.even_delay_buildblock)
    bld.block_and_redstone(schem, v + right * 2, bld.odd_delay_buildblock)
    v += forward
    bld.block_and_repeater(schem, v - up, bld.even_delay_buildblock, -forward)
    bld.block_and_redstone(schem, v + up, bld.start_line_buildblock, powered=True)
    bld.block_and_repeater(schem, v + right, bld.start_line_buildblock, right, powered=True)
    bld.block_and_repeater(schem, v + right * 2, bld.even_delay_buildblock, -forward, locked=True)
    v += forward
    bld.block_and_repeater(schem, v - up, bld.even_delay_buildblock, -forward)
    bld.block_and_redstone(schem, v + up, bld.start_line_buildblock, powered=True)
    bld.setblock(schem, v + up + right * 2, f"observer[facing={bld.cardinal_direction(forward)}]")
    v += forward
    bld.block_and_redstone(schem, v - up, bld.even_delay_buildblock)
    bld.block_and_redstone(schem, v + up, bld.start_line_buildblock, powered=True)
    bld.setblock(schem, v + right * 2, f"oak_trapdoor[facing={bld.cardinal_direction(-forward)},half=top]")
    bld.setblock(schem, v + right * 2 + up, "scaffolding")
    v += forward
    bld.block_and_redstone(schem, v - up, bld.even_delay_buildblock)
    bld.block_and_redstone(schem, v + up, bld.start_line_buildblock, powered=True)
    bld.block_and_redstone(schem, v + right - up, bld.even_delay_buildblock)
    bld.setblock(schem, v + right * 2, bld.even_delay_buildblock)
    bld.setblock(schem, v + right * 2 + up, "scaffolding")
    v += forward
    bld.block_and_redstone(schem, v, bld.start_line_buildblock, powered=True)
    bld.block_and_repeater(schem, v + right - up, bld.start_line_buildblock, right, powered=True)
    bld.block_and_repeater(schem, v + right * 2 - up, bld.start_line_buildblock, -forward, locked=True)
    v += forward
    bld.setblock(schem, v, bld.start_line_buildblock)
    bld.setblock(schem, v + up, "redstone_torch")
    bld.block_and_repeater(schem, v + right, bld.start_line_buildblock, right, powered=True)
    bld.block_and_redstone(schem, v + right * 2, bld.start_line_buildblock, powered=True)
    v += forward
    v -= up
    return v

def build_glass_walkway(schem, player_pos, forward, one_gt_delayer_pos, length, depth, title, min_render_dist):
    right = forward.rotated(positive_direction=False)
    up = Vector(0, 1, 0)
    v = player_pos - up - forward
    for i in range(length + 2):
        bld.setblock(schem, v, "glass")
        bld.setblock(schem, v + right, "glass")
        v += forward

    bld.setblock(schem, v + up - forward + right,
        "birch_sign[rotation=8]{"
        "Text1: '{\"text\":\"Created with\"}', "
        "Text2: '{\"text\":\"Note Block Studio\"}', "
        "Text3: '{\"text\":\"Render distance\"}', "
        "Text4: '{\"text\":\"must be >= " + str(min_render_dist) + " !\"}'}")
    # 15 characters for sure fit onto one row of the sign
    title_1 = title[0:15]
    title_2 = title[15:30]
    title_3 = title[30:45]
    title_4 = title[45:60]
    bld.setblock(schem, v + up - forward,
        "birch_sign[rotation=8]{"
        "Text1: '{\"text\":\"" + title_1 + "\"}', "
        "Text2: '{\"text\":\"" + title_2 + "\"}', "
        "Text3: '{\"text\":\"" + title_3 + "\"}', "
        "Text4: '{\"text\":\"" + title_4 + "\"}'}")

    save_v = v.copy()
    for i in range(depth):
        bld.setblock(schem, v, "glass")
        bld.setblock(schem, v + right, "glass")
        bld.setblock(schem, v + forward, "ladder")
        bld.setblock(schem, v + forward + right, "ladder")
        v -= up
    
    v = save_v + right * 2
    forward = right
    goal = one_gt_delayer_pos
    bld.setblock(schem, v, bld.start_line_buildblock)
    bld.setblock(schem, v + up, f"stone_button[face=floor,facing={bld.cardinal_direction(forward)}]")
    v += forward
    v -= up
    # rc: redstone count, before the repeater, max 15
    rc = 0
    
    for rotation in [True, False]:
    
        diff_forward = goal.get_coord(forward) - v.get_coord(forward) + 1
        for i in range(diff_forward):
            if rc == 15 or (rc == 14 and i+2 == diff_forward):
                bld.block_and_repeater(schem, v, bld.start_line_buildblock, forward)
                rc = 0
            else:
                bld.block_and_redstone(schem, v, bld.start_line_buildblock)
                rc += 1
                if v.y > goal.y:
                    v -= up
                elif v.y < goal.y:
                    v += up
            v += forward
        
        if rotation:
            v -= forward
            forward.rotate(positive_direction=False)
            v += forward

    assert v.y == goal.y, "Somehow the diorite line is not aligned well vertically!"


# should be called after the majority of the building is done
def calculate_min_render_distance_needed(schem):
    schem_bounds = schem.getStructure().getBounds()
    # assuming player is at 0,0,0 (that's the middle of the contraption)
    max_distance = max(-schem_bounds[0][0], -schem_bounds[0][2], schem_bounds[1][0], schem_bounds[1][2])
    # https://minecraft.fandom.com/wiki/Chunk#Level_and_load_type
    # a render distance of 5 e.g. means ■□□□■ that if I'm standing in the right white chunk, the
    # redstone in the left white chunk is just barely loaded (tested with 1.17.1 Singleplayer)
    # so if there's a distance of 50 e.g. between me and my redstone, we'd recommend a render distance of
    # at least 3+2
    return max_distance // 16 + 2


def build_contraption(schem, lines, left_width, middle_width, right_width, height, title, use_redstone_lamp):
    width = left_width + middle_width + right_width
    assert 1 <= len(lines) <= width * height, f"There are {len(lines)} lines, but only {width * height} places for them!"
    view_distance = max(left_width, right_width, middle_width) # this is the space between player pos and middle side
    
    def begin_lines(upper_left_corner, prev_width, width, height, forward, lines, index, side):
        line_count = len(lines)
        # we place one column in 2 separate passes, skipping the zip-zagging, we need this in order to place the lines in the correct order
        for col in range(2 * width):
            v = upper_left_corner + forward * col
            # every 2nd column starts deeper because of the zig-zag
            if col % 2 == 1:
                v.y -= 2
            # if height is even then max_row=height//2 everytime, if height is odd then every 2nd time we leave one out (zig-zag)
            for row in range((height + (1 - col % 2)) // 2):
                # if there aren't any more lines:
                if index >= line_count:
                    return index
                # this is needed for the turn:
                dist_to_middle = 0 if side == "middle" else (2 * width - col if side == "left" else col + 1)
                real_col = prev_width + col // 2 # not taking the zig-zagging into account, meaning one column here is 2 blocks wide
                lines[index].begin_circuit(schem, v - Vector(0, 4 * row, 0), forward.rotated(), side, dist_to_middle, 2*row + col%2, height, real_col, col//2, width)
                index += 1
        return index
    
    # approx. ideal position for listening is the middle of a 2×2×2 cube, which ranges from player_pos to player_pos+v(1,1,1)
    # thus the 2×2 glass below the player is at player_pos+v(0,-1,0) to player_pos+v(1,-1,1)
    player_pos = Vector(0, 0, 0)
    middle_side_z = player_pos.z + view_distance
    left_side_x = player_pos.x + middle_width + 1
    right_side_x = player_pos.x - middle_width
    
    left_side_upper_left_corner = Vector(left_side_x, player_pos.y + height, middle_side_z - 2 * left_width + 1)
    index = begin_lines(left_side_upper_left_corner, 0, left_width, height, Vector(0, 0, 1), lines, 0, "left")
    middle_side_upper_left_corner = Vector(left_side_x - 1, player_pos.y + height, middle_side_z)
    index = begin_lines(middle_side_upper_left_corner, left_width, middle_width, height, Vector(-1, 0, 0), lines, index, "middle")
    right_side_upper_left_corner = Vector(right_side_x, player_pos.y + height, middle_side_z)
    index = begin_lines(right_side_upper_left_corner, left_width + middle_width, right_width, height, Vector(0, 0, -1), lines, index, "right")
    assert index == len(lines), f"Something went wrong with beginning the lines, index until built is {index} but the amount of lines is {len(lines)}"
    
    shallow_depth = max(left_width, right_width)
    # the 2*2 * shallow_depth is the max amount of blocks the signal needs to travel,
    # but at the 2 ends they may place the repeater 1 block sooner, hence +2
    turn_max_delay = (2*2 * shallow_depth + 2) // 16 + 1 # +1 for the extra repeater at the end
    for line in lines:
        line.build_noteblock(use_redstone_lamp)
        line.build_side_turn(turn_max_delay)
        line.build_vertical_adjustment()
        line.build_horizontal_adjustment()
        line.add_delay_for_vertical_connection()
    
    bottom_connection_pos = build_vertical_connection(schem, lines[0].get_pos() + Vector(2, 3, 0), height)
    bottom_connection_pos = build_1gt_delayer(schem, bottom_connection_pos, Vector(0, 0, -1))
    # glass walkway length, at least one block, otherwise just enough to go around the left side:
    walkway_length = max(1, left_width * 2 - view_distance)
    
    # there will be a repeater every 4th block on the horizontal line that gives the signal to the whole thing
    junction_delay = (width - 1) // 2 
    for line in lines:
        line.build_junction(junction_delay)
    
    # 2, because the start button redstone line needs to have space
    begin_z = player_pos.z - max(right_width * 2 - view_distance, 2 + walkway_length)
    current_z = lines[0].get_pos().z
    # this much spacing will be applied behind the player, >=0, there will be 3 blocks of space with =0 (for the start signal):
    additional_spacing = 8
    for line in lines:
        # finding out where each line needs to turn:
        turns = []
        # 2 because it is needed before the first turn
        z_difference = current_z - begin_z + 2 + additional_spacing
        turns.append(2 + 2 * line.col)
        # these values are because of the horizontal adjustment, and to make space for the vertical connection and 1gt delay maker
        x_difference = 2 * width + 13
        turns.append(9 + 4 * line.col)
        for i in range(15):#idk, should be long enough TODO
            turns.append(z_difference + 4 * line.col)
            z_difference += 2 * width
            turns.append(x_difference + 4 * line.col)
            x_difference += 2 * width
        line.build_delays(turns)

    min_render_dist = calculate_min_render_distance_needed(schem)
    build_glass_walkway(schem, player_pos, Vector(0, 0, -1), bottom_connection_pos, walkway_length, 10, title, min_render_dist)# TODO 10 deep ladder
