#!/usr/bin/env python3

from warnings import warn
from vector import Vector
import block_placer
from math import sqrt, ceil

from pynbs import read as pynbs_read
from sponge_schematic import Schematic

# represents a redstone wire line corresponding to a single instrument/pitch noteblock
# may need to be split further, may contain more than one of the same note playing at once
class UnprocessedLine:
    
    def __init__(self, key, instrument):
        self._key = key
        self._instrument = instrument
        self._ticks = {} # indexed with tick, value is noteblock count at that tick
    
    def __repr__(self):
        return f"[UnprocessedLine i,k:{self._instrument},{self._key} ticks:{self._ticks}]"
    
    # tps is supposed to be 20 here
    def add_note(self, tick, count=1):
        if not tick in self._ticks:
            self._ticks[tick] = 0
        self._ticks[tick] += count
    
    def is_empty(self):
        return not self._ticks
    
    def _pass_notes_to(self, other, tick, leave_one=False):
        other.add_note(tick, count=self._ticks[tick] - (1 if leave_one else 0))
        if leave_one:
            self._ticks[tick] = 1
        else:
            self._ticks.pop(tick)
    
    def _split_even(self):
        new_line = UnprocessedLine(self._key, self._instrument)
        evenness = next(iter(self._ticks)) % 2 # first key in dict
        for tick in list(self._ticks): # list of keys, so that we can safely remove elements
            if tick % 2 != evenness:
                self._pass_notes_to(new_line, tick)
        return [self] if new_line.is_empty() else [self, new_line]
    
    # called from split, may be called from another instance too
    # TODO: swap self and the new_line before return (it makes more sense that way)
    def _split_further(self):
        new_line = UnprocessedLine(self._key, self._instrument)
        previous = -42
        for tick in sorted(self._ticks): # this creates a list, we can safely remove elements from _ticks
            if previous + 4 > tick:
                self._pass_notes_to(new_line, tick)
            else:
                previous = tick
                if self._ticks[tick] > 1:
                    self._pass_notes_to(new_line, tick, leave_one=True)
        assert all(count == 1 for count in self._ticks.values())
        return new_line
    
    # we need to split this line if
    # 1) there are more than 1 notes playing at the same time or
    # 2) there are both odd and even tick delays or
    # 3) there is a 2 tick delay somewhere
    def split(self):
        assert not self.is_empty() # assert: true is good, false is bad
        lines_halfsplit = self._split_even()
        processed_lines = []
        for line in lines_halfsplit:
            assert len(set(k%2 for k in line._ticks)) == 1 # all keys have the same parity
            while not line.is_empty():
                new_line = line._split_further()
                processed_lines.append(line.to_processed_line())
                line = new_line
        return processed_lines
    
    def to_processed_line(self):
        return ProcessedLine(self._key, self._instrument, self._ticks) # ticks will become list!


# represents a redstone wire line corresponding to a single instrument/pitch noteblock
# it is split enough to be actually created with redstone
class ProcessedLine:
    
    def __init__(self, key, instrument, ticks):
        key -= 33
        while key < 0:
            key += 12
        while key > 24:
            key -= 12
        self._note = key
        self._instrument = instrument
        ticks = sorted(ticks) # sorted list, count (it was the value of the dict) is no longer needed
        assert ticks # not empty
        self._is_even = ticks[0] % 2 == 0
        # adding 4gt to the first delay value (as if the 0th note was at gametick -4), to make it behave like the rest of the delays
        self._delays = [(4 + ticks[0]) // 2] + [(ticks[i+1] - ticks[i]) // 2 for i in range(len(ticks) - 1)] # from gametick to redstone tick
        assert min(self._delays) >= 2
    
    def __repr__(self):
        return f"[ProcessedLine i,k:{self._instrument},{self._note} delays:{self._delays}]"
    
    def begin_circuit(self, schem, pos, forward, side, dist_to_middle, col, row, max_row):
        self._schem = schem
        pos.y -= 1 # pos.y is where the noteblock is, but it's better to store the block below
        self._pos = pos
        self._forward = forward
        self._side = side # either "left" "middle" or "right"
        # the blocks this line needs to go sideways and forward to be aligned with the side "middle"
        # it correlates with the column it is in
        self._dist_to_middle = dist_to_middle
        self._col = col # the column, absolute, and every column has the same height (the checkerboard pattern): every row×col has a noteblock
        self._row = row
        self._max_row = max_row #TODO parameter to the actual function
        self._buildblock = block_placer.building_material[self._instrument]
        #print(pos, forward, side, dist_to_middle, row, max_row)
        self.build_noteblock()
        
    def get_pos(self):
        return self._pos
    
    def build_noteblock(self):
        v = self._pos
        self._schem.setblock(v.x, v.y-1, v.z, "redstone_lamp")
        self._schem.setblock(v.x, v.y+0, v.z, block_placer.instrument_material[self._instrument])
        self._schem.setblock(v.x, v.y+1, v.z, f"note_block[note={self._note},instrument={block_placer.instrument_name[self._instrument]}]")
        v += self._forward
        self._schem.setblock(v.x, v.y-1, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+0, v.z, block_placer.redstone)
        self._schem.setblock(v.x, v.y+1, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+2, v.z, self._buildblock)
        if self._row == 1:
            self._schem.setblock(v.x, v.y+3, v.z, self._buildblock)
            self._schem.setblock(v.x, v.y+4, v.z, self._buildblock)
        if self._row == self._max_row - 2:
            self._schem.setblock(v.x, v.y-3, v.z, self._buildblock)
            self._schem.setblock(v.x, v.y-2, v.z, self._buildblock)
        v += self._forward
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.repeater(-self._forward, 1))
        v += self._forward
    
    def build_side_turn(self, delay):
        v = self._pos
        if self._side == "middle":
            for i in range(delay + 1): # +1 for the just to make sure repeater
                self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
                self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
                v += self._forward
                self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
                self._schem.setblock(v.x, v.y+1, v.z, block_placer.repeater(-self._forward, 1))
                v += self._forward
            return
        
        # rc: redstone count, before the repeater, max 15
        rc = 0
        placed_delay = 0
        for rotation in [True, False]:
            for i in range(self._dist_to_middle):
                self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
                to_place = block_placer.redstone
                if rc == 15 or (rc == 14 and i+2 == self._dist_to_middle):
                    to_place = block_placer.repeater(-self._forward, 1)
                    assert rc <= 15
                    rc = 0
                    placed_delay += 1
                else:
                    rc += 1
                self._schem.setblock(v.x, v.y+1, v.z, to_place)
                v += self._forward
            
            if rotation:
                v -= self._forward
                self._forward.rotate(positive_direction = (self._side=="right"))
                v += self._forward
        
        modulo = (1 + 2*delay) // (delay - placed_delay) if placed_delay != delay else 42
        for i in range(1 + 2*delay):
            self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
            to_place = block_placer.redstone
            if i % modulo == 0 and placed_delay != delay:
                to_place = block_placer.repeater(-self._forward, 1)
                assert rc <= 15
                rc = 0
                placed_delay += 1
            else:
                rc += 1
            self._schem.setblock(v.x, v.y+1, v.z, to_place)
            v += self._forward
                
        # ending with 1 repeater everywhere, so that in the next step we can rely on that
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
        rc += 1
        assert rc <= 15
        assert placed_delay == delay
        v += self._forward
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.repeater(-self._forward, 1))
        v += self._forward
        
    def build_vertical_adjustment(self):
        v = self._pos
        max_needed_diff = self._max_row - 1
        needed_diff = max_needed_diff - 2 * self._row
        for i in range(max_needed_diff + 1):
            if i + abs(needed_diff) > max_needed_diff:
                v += Vector(0, -1 if needed_diff < 0 else 1, 0)
            self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
            self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
            v += self._forward
            if (i+1) % 15 == 0:
                self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
                self._schem.setblock(v.x, v.y+1, v.z, block_placer.repeater(-self._forward, 1))
                v += self._forward
                self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
                self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
                v += self._forward
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.repeater(-self._forward, 1))
        v += self._forward
    
    def build_horizontal_adjustment(self):
        v = self._pos
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
        v += self._forward
        vertical_offset = Vector(0, -1 if self._col % 2 == 0 else 1, 0)
        if self._side != "middle":
            v += vertical_offset
            sideways = self._forward.rotated(positive_direction = (self._side=="right"))
        for i in range(3):
            self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
            self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
            v += self._forward
            if self._side != "middle":
                self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
                self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
                v += sideways
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
        v += self._forward
        if self._side != "middle":
            v -= vertical_offset
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
        v += self._forward
        
        if self._row % 2 == 0:
            self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
            self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
            v += self._forward
        else:
            v += vertical_offset
            sideways = self._forward.rotated()
            self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
            self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
            v += sideways
            self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
            self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
            v += self._forward
            v -= vertical_offset
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
        v += self._forward
            
    def build_junction(self, max_delay):
        v = self._pos
        left = self._forward.rotated()
        side = v + left
        self._schem.setblock(side.x, side.y+2, side.z, "polished_andesite")
        self._schem.setblock(side.x, side.y+3, side.z, block_placer.repeater(-left, 1) if self._col % 2 == 0 else block_placer.redstone)
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
        self._schem.setblock(v.x, v.y+2, v.z, "polished_andesite")
        self._schem.setblock(v.x, v.y+3, v.z, block_placer.redstone)
        v += self._forward
        
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.repeater(-self._forward, 1))
        if self._is_even:
            self._schem.setblock(v.x, v.y+2, v.z, "polished_andesite")
            self._schem.setblock(v.x, v.y+3, v.z, block_placer.redstone)
            #if self._row == 0:
                #self._schem.setblock(v.x, v.y+4, v.z, "polished_andesite")
        v += self._forward
        
        side = v + left
        self._schem.setblock(side.x, side.y+3, side.z, "polished_granite")
        self._schem.setblock(side.x, side.y+4, side.z, block_placer.repeater(-left, 1) if self._col % 2 == 0 else block_placer.redstone)
        self._schem.setblock(v.x, v.y+1, v.z, self._buildblock)
        if self._is_even:
            self._schem.setblock(v.x, v.y+3, v.z, "polished_andesite")
            self._schem.setblock(v.x, v.y+4, v.z, "polished_granite")
        else:
            self._schem.setblock(v.x, v.y+3, v.z, "polished_granite")
            self._schem.setblock(v.x, v.y+4, v.z, block_placer.redstone)
        v += self._forward
        
        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
        self._schem.setblock(v.x, v.y+2, v.z, self._buildblock)
        self._schem.setblock(v.x, v.y+3, v.z, block_placer.repeater(self._forward, 1))
        v += self._forward
        #TODO: ezt eltüntetni és beépíteni _delays-be
        needed_delay = max_delay - (self._col * 2) // 4
        #for i in range(max_delay):
            #if (i+2) % 16 == 0:#TODO here place some other block for aesthetics and to see that this is different, and in other places too maybe
                #self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
                #self._schem.setblock(v.x, v.y+1, v.z, block_placer.repeater(-self._forward, 1))
                #self._schem.setblock(v.x, v.y+2, v.z, self._buildblock)
                #self._schem.setblock(v.x, v.y+3, v.z, block_placer.repeater(self._forward, 1))
                #v += self._forward
            #self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
            #self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
            #self._schem.setblock(v.x, v.y+2, v.z, self._buildblock)
            #self._schem.setblock(v.x, v.y+3, v.z, block_placer.repeater(self._forward, 1) if i < needed_delay else block_placer.redstone)
            #v += self._forward
        self._delays[0] += needed_delay
    
    # turns is [10, 22, 15] e.g., meaning it needs to turn left after 10 blocks, and again after 22,... relative to the previous turn
    # corner blocks count towards the previous count
    def create_delays(self, turns):
        v = self._pos
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
        and that will help with the turns
        """
        placed_blocks = 0 # since the previous turn
        for i, delay in enumerate(self._delays):
            md = min(self._delays[i:]) # could be optimized: only recalculate this if delay==md
            run_again = True
            while run_again:
                run_again = False
                next_length = block_placer.get_delay_length(delay, md)
                #print(delay, md, next_length)
                if not turns or placed_blocks + next_length + 1 < turns[0]: # if turns is empty or there's enough space
                    block_placer.create_delay(self._schem, self._buildblock, self._pos, self._forward, delay, md)
                    placed_blocks += next_length
                else:
                    if placed_blocks + next_length + 1 == turns[0]:
                        self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
                        self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
                        self._schem.setblock(v.x, v.y+2, v.z, self._buildblock)
                        self._schem.setblock(v.x, v.y+3, v.z, block_placer.redstone)
                        v += self._forward
                        placed_blocks += 1
                    if placed_blocks + next_length == turns[0]:
                        block_placer.create_delay(self._schem, self._buildblock, self._pos, self._forward, delay, md)
                        v -= self._forward
                        self._forward.rotate()
                        v += self._forward
                        placed_blocks = 0
                        turns.pop(0)
                    else:
                        mind = min(md, 9)
                        leftout_delay = 0
                        # while delay is good AND (we need less of delay OR there's too little leftout_delay)
                        # this could be much improved with a binary search e.g.
                        #print(f"delay:{delay}, mind:{mind}, turn:{turns[0]}, ")
                        while delay >= mind and (placed_blocks + block_placer.get_delay_length(delay, md) > turns[0] or leftout_delay < mind):
                            delay -= 1
                            leftout_delay += 1
                        #print(block_placer.get_delay_length(delay, md), " delay length")
                        if delay < mind or leftout_delay < mind:
                            spacer = turns[0] - placed_blocks
                            assert spacer <= 13, f"1STCASE delays {delay} or {leftout_delay} aren't big enough with md {mind}, {spacer} is too big to fill in the gap with redstone; placed blocks are {placed_blocks}, and the turn is in {turns[0] - placed_blocks} blocks" # redstone shouldn't run out
                            assert spacer <= 2, f"I dont think this should be possible"
                            for i in range(spacer):
                                self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
                                self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
                                self._schem.setblock(v.x, v.y+2, v.z, self._buildblock)
                                self._schem.setblock(v.x, v.y+3, v.z, block_placer.redstone)
                                v += self._forward
                            delay += leftout_delay
                        elif placed_blocks + block_placer.get_delay_length(delay, md) < turns[0]:
                            placed_blocks += block_placer.get_delay_length(delay, md) # created later
                            
                            spacer = turns[0] - placed_blocks
                            assert spacer <= 13, f"2NDCASE delays {delay} or {leftout_delay} aren't big enough with md {mind}, {spacer} is too big to fill in the gap with redstone; placed blocks are {placed_blocks}, and the turn is in {turns[0] - placed_blocks} blocks" # redstone shouldn't run out
                            if spacer != 1:
                                block_placer.create_delay(self._schem, self._buildblock, self._pos, self._forward, delay, md, loopback=False)
                            for i in range(spacer):
                                self._schem.setblock(v.x, v.y+0, v.z, self._buildblock)
                                self._schem.setblock(v.x, v.y+1, v.z, block_placer.redstone)
                                self._schem.setblock(v.x, v.y+2, v.z, self._buildblock)
                                self._schem.setblock(v.x, v.y+3, v.z, block_placer.redstone)
                                v += self._forward
                            if spacer == 1:#TODO cleanup, why wont the redstone run out?
                                block_placer.create_delay(self._schem, self._buildblock, self._pos, self._forward, delay, md, loopback=False)
                            delay = leftout_delay
                        else:#this could be merged with the previous case
                            assert placed_blocks + block_placer.get_delay_length(delay, md) == turns[0]
                            block_placer.create_delay(self._schem, self._buildblock, self._pos, self._forward, delay, md, loopback=False)
                            delay = leftout_delay
                        v -= self._forward
                        self._forward.rotate()
                        v += self._forward
                        placed_blocks = 0
                        turns.pop(0)
                        run_again = True
                
            
    

def build_lines(schem, lines, left_width, middle_width, right_width, height):
    lines.sort(key=lambda l: l._note + 100 * l._instrument)#TODO problem: private vars, solution: public function
    width = left_width + middle_width + right_width
    assert 1 <= len(lines) <= width * height, f"there are {len(lines)} lines, but only {width * height} places for them"
    #TODO add more explanation to assertions
    
    def build_nbs(upper_left_corner, prev_width, width, height, forward, lines, index, side):
        line_count = len(lines)
        for col in range(2 * width):
            v = upper_left_corner + forward * col
            if col%2 == 1:
                v.y -= 2
            # if height is even then height/2 everytime, else every 2nd time we leave one out
            for row in range((height + 1-col%2) // 2):
                if index >= line_count:
                    return index
                dist_to_middle = (2*width - col if side == "left" else col + 1) if side != "middle" else 0
                passed_col = prev_width + col // 2
                lines[index].begin_circuit(schem, v - Vector(0, 4*row, 0), forward.rotated(), side, dist_to_middle, passed_col, 2*row + col%2, height)
                index += 1
        return index
    
    # ideal position for listening is the middle of a 2×2×2 cube, which ranges from player_pos to player_pos+v(1,1,1)
    player_pos = Vector(0, 0, 0)
    #schem.setblock(player_pos.x+0, player_pos.y-1, player_pos.z+0, "glass")
    #schem.setblock(player_pos.x+1, player_pos.y-1, player_pos.z+0, "glass")
    #schem.setblock(player_pos.x+0, player_pos.y-1, player_pos.z+1, "glass")
    #schem.setblock(player_pos.x+1, player_pos.y-1, player_pos.z+1, "glass")
    # nbs here: noteblocks
    middle_nbs_z = player_pos.z + max(left_width, right_width)
    left_nbs_x = player_pos.x + middle_width + 1
    right_nbs_x = player_pos.x - middle_width
    
    left_nbs_upper_left_corner = Vector(left_nbs_x, player_pos.y + height, middle_nbs_z - 2*left_width + 1)
    index = build_nbs(left_nbs_upper_left_corner, 0, left_width, height, Vector(0, 0, 1), lines, 0, "left")
    middle_nbs_upper_left_corner = Vector(left_nbs_x - 1, player_pos.y + height, middle_nbs_z)
    index = build_nbs(middle_nbs_upper_left_corner, left_width, middle_width, height, Vector(-1, 0, 0), lines, index, "middle")
    right_nbs_upper_left_corner = Vector(right_nbs_x, player_pos.y + height, middle_nbs_z)
    index = build_nbs(right_nbs_upper_left_corner, left_width + middle_width, right_width, height, Vector(0, 0, -1), lines, index, "right")
    assert index == len(lines)
    
    #begin_z = min(lines[0].get_pos().z, lines[-1].get_pos().z)# TODO we need smthng better, test e.g. middle_nbs_z - 2*max(left_width, right_width) may work
    begin_z = player_pos.z - max(left_width, right_width) # TODO
    
    #TODO because at left_width=0 right_width=5 e.g. without having nbs actually on the right (for sides_mode=1)
    # delay = (4 * max(left_width, right_width) + 2 + 2 * delay) // 15
    # 15*delay + remainder = 4 * max(left_width, right_width) + 2 + 2 * delay
    # 13*delay = 4 * max(left_width, right_width) + 2 - remainder
    # delay <= (4 * max(left_width, right_width) + 2) // 13 + 1
    turn_delay = (4 * max(left_width, right_width) + 2) // 13 + 1 # +1 may not be needed
    for line in lines:
        line.build_side_turn(turn_delay)
        line.build_vertical_adjustment()
        line.build_horizontal_adjustment()
    
    bottom_connection_pos = build_vertical_connection(schem, lines[0].get_pos() + Vector(2, 3, 0), height)
    bottom_connection_pos = build_1gt_delayer(schem, bottom_connection_pos, Vector(0, 0, -1))
    junction_delay = (width - 1) // 2 # there will be a repeater every 4th block
    for line in lines:
        line.build_junction(junction_delay)
        
    current_z = lines[0].get_pos().z
    additional_spacing = 20 # this much spacing will be applied behind the player, >=0, there will be 3 blocks of space with =0
    for line in lines:
        col = line._col#TODO
        turns = []
        z_difference = current_z - begin_z + 6 + additional_spacing
        turns.append(3 + 2 * col)
        x_difference = 2 * width + 13
        turns.append(9 + 4 * col)
        for i in range(15):#idk, should be long enough TODO
            turns.append(z_difference + 4 * col)
            z_difference += 2 * width
            turns.append(x_difference + 4 * col)
            x_difference += 2 * width
        line.create_delays(turns)
    
    build_glass_walkway(schem, player_pos, Vector(0, 0, -1), bottom_connection_pos, max(left_width, right_width), 10)


# begin_v is the coordinate of the even (andesite) connector of the very first (upper left) noteblock line
def build_vertical_connection(schem, begin_v, height):
    
    def double_block_and_redstone(schem, andesite_v, rel_granite_v):
        block_and_redstone(schem, andesite_v, "polished_andesite")
        block_and_redstone(schem, andesite_v + rel_granite_v, "polished_granite")
        
    def double_block_and_repeater(schem, andesite_v, rel_granite_v, direction):
        block_and_repeater(schem, andesite_v, "polished_andesite", direction)
        block_and_repeater(schem, andesite_v + rel_granite_v, "polished_granite", direction)
        
    max_delay = (height - 1) // 3
    for h in range(height):
        v = begin_v - Vector(0, 4 * h, 0)
        forward = Vector(1, 0, 0)
        for i in range(4):
            double_block_and_redstone(schem, v, Vector(0, 0, 2))
            v += forward
        v -= forward
        # corner:
        block_and_redstone(schem, v + Vector(1, 0, 2), "polished_granite")
        block_and_redstone(schem, v + Vector(2, 0, 2), "polished_granite")
        block_and_redstone(schem, v + Vector(2, 0, 1), "polished_granite")
        block_and_redstone(schem, v + Vector(2, 0, 0), "polished_granite")
        
        forward.rotate()
        v += forward
        
        needed_delay = h // 3
        for i in range(max_delay):
            if (i+9) % 16 == 0:
                double_block_and_repeater(schem, v, Vector(2, 0, 0), -forward)
                v += forward
            if i < needed_delay:
                double_block_and_repeater(schem, v, Vector(2, 0, 0), -forward)
            else:
                double_block_and_redstone(schem, v, Vector(2, 0, 0))
            v += forward
            
        double_block_and_repeater(schem, v, Vector(2, 0, 0), -forward)
        v += forward
        double_block_and_redstone(schem, v, Vector(2, 0, 0))
        v += forward
        if h != height - 1: # we skip the last one
            block_and_redstone(schem, v + Vector(0, -3, 0), "polished_andesite_slab[type=top]")
            block_and_redstone(schem, v + Vector(2, -3, 0), "polished_granite_slab[type=top]")
            block_and_redstone(schem, v + Vector(0, -1, 0), "polished_andesite_slab[type=top]")
            block_and_redstone(schem, v + Vector(2, -1, 0), "polished_granite_slab[type=top]")
            v += forward
            if (h+1) % 3 == 0:
                double_block_and_repeater(schem, v + Vector(0, -3, 0), Vector(2, 0, 0), forward)
                double_block_and_redstone(schem, v + Vector(0, -1, 0), Vector(2, 0, 0))
                v += forward
            double_block_and_redstone(schem, v + Vector(0, -2, 0), Vector(2, 0, 0))
            v += forward
        else:
            v += Vector(0, -1, 0)
            double_block_and_repeater(schem, v, Vector(2, 0, 0), -forward)
            v += forward
            end_v = v
    return end_v

# v is the coordinate of the block before the andesite/even gt repeater, at the bottom
# v + Vector(2, 0, 0) is the block before the granite/odd gt repeater
def build_1gt_delayer(schem, v, forward):
    right = forward.rotated(positive_direction=False)
    up = Vector(0, 1, 0)
    block_and_redstone(schem, v, "polished_andesite")
    block_and_redstone(schem, v + right * 2, "polished_granite")
    v += forward
    block_and_redstone(schem, v - up, "polished_andesite")
    block_and_redstone(schem, v + right * 2, "polished_granite")
    v += forward
    block_and_repeater(schem, v - up, "polished_andesite", -forward)
    block_and_redstone(schem, v + up, "polished_diorite", powered=True)
    block_and_repeater(schem, v + right, "polished_diorite", right, powered=True)
    block_and_repeater(schem, v + right * 2, "polished_andesite", -forward, locked=True)
    v += forward
    block_and_repeater(schem, v - up, "polished_andesite", -forward)
    block_and_redstone(schem, v + up, "polished_diorite", powered=True)
    setblock(schem, v + up + right * 2, f"observer[facing={block_placer.cardinal_direction(forward)}]")
    v += forward
    block_and_redstone(schem, v - up, "polished_andesite")
    block_and_redstone(schem, v + up, "polished_diorite", powered=True)
    setblock(schem, v + right * 2, f"oak_trapdoor[facing={block_placer.cardinal_direction(-forward)},half=top]")
    setblock(schem, v + right * 2 + up, "scaffolding")
    v += forward
    block_and_redstone(schem, v - up, "polished_andesite")
    block_and_redstone(schem, v + up, "polished_diorite", powered=True)
    block_and_redstone(schem, v + right - up, "polished_andesite")
    setblock(schem, v + right * 2, "polished_andesite")
    setblock(schem, v + right * 2 + up, "scaffolding")
    v += forward
    block_and_redstone(schem, v, "polished_diorite", powered=True)
    block_and_repeater(schem, v + right - up, "polished_diorite", right, powered=True)
    block_and_repeater(schem, v + right * 2 - up, "polished_diorite", -forward, locked=True)
    v += forward
    setblock(schem, v, "polished_diorite")
    setblock(schem, v + up, "redstone_torch")
    block_and_repeater(schem, v + right, "polished_diorite", right, powered=True)
    block_and_redstone(schem, v + right * 2, "polished_diorite", powered=True)
    v += forward
    v -= up
    return v

def build_glass_walkway(schem, player_pos, forward, one_gt_delayer_pos, length, depth):
    right = forward.rotated(positive_direction=False)
    up = Vector(0, 1, 0)
    v = player_pos - up - forward
    for i in range(length + 2):
        setblock(schem, v, "glass")
        setblock(schem, v + right, "glass")
        v += forward
    setblock(schem, v + up - forward, "birch_sign[rotation=8]")
    setblock(schem, v + up - forward + right, "birch_sign[rotation=8]")#TODO no blockentity yet
    save_v = v.copy()
    for i in range(depth):
        setblock(schem, v, "glass")
        setblock(schem, v + right, "glass")
        setblock(schem, v + forward, "ladder")
        setblock(schem, v + forward + right, "ladder")
        v -= up
    
    v = save_v + right * 2
    forward = right
    goal = one_gt_delayer_pos
    setblock(schem, v, "polished_diorite")
    setblock(schem, v + up, f"stone_button[face=floor,facing={block_placer.cardinal_direction(forward)}]")
    v += forward
    v -= up
    # rc: redstone count, before the repeater, max 15
    rc = 0
    diff_forward = goal.get_coord(forward) - v.get_coord(forward) + 1
    for i in range(diff_forward):
        if rc == 15 or (rc == 14 and i+2 == diff_forward):
            block_and_repeater(schem, v, "polished_diorite", forward)
            rc = 0
        else:
            block_and_redstone(schem, v, "polished_diorite")
            rc += 1
            if v.y > goal.y:
                v -= up
            elif v.y < goal.y:
                v += up
        v += forward
    
    v -= forward
    forward.rotate(positive_direction=False)
    v += forward
    
    diff_forward = goal.get_coord(forward) - v.get_coord(forward) + 1
    for i in range(diff_forward):
        if rc == 15 or (rc == 14 and i+2 == diff_forward):
            block_and_repeater(schem, v, "polished_diorite", forward)
            rc = 0
        else:
            block_and_redstone(schem, v, "polished_diorite")
            rc += 1
            if v.y > goal.y:
                v -= up
            elif v.y < goal.y:
                v += up
        v += forward

    if v.y != goal.y:
        warn("Somehow the diorite line is not aligned well vertically.")
        
        
#TODO ezek a block_placerbe és átnevezés
def setblock(schem, v, block):
    schem.setblock(v.x, v.y, v.z, block)

def block_and_redstone(schem, v, buildblock, powered=False):
    schem.setblock(v.x, v.y+0, v.z, buildblock)
    schem.setblock(v.x, v.y+1, v.z, f"redstone_wire[east=side,north=side,power={15 if powered else 0},south=side,west=side]")
    
def block_and_repeater(schem, v, buildblock, facing_direction, delay=1, locked=False, powered=False):
    assert delay in [1, 2, 3, 4]
    schem.setblock(v.x, v.y+0, v.z, buildblock)
    schem.setblock(v.x, v.y+1, v.z, f"repeater[delay={delay},facing={block_placer.cardinal_direction(-facing_direction)},locked={locked},powered={powered}]")


def from_nbs_file(song, override_tempo=-1):
    # this is hardcoded as in NBS there isn't a 6.67 tps option, so
    # 6.75 almost always wants to mean every 3 gameticks
    if song.header.tempo == 6.75:
        song.header.tempo = 20/3
    # this function also fixes the tps to 20, so we multiply tick by this:
    multiplier = 20 / (song.header.tempo if override_tempo == -1 else override_tempo)
    lines = {} # indexed with key+100*instrument
    for tick, chord in song:
        for note in chord:
            code = note.key + 100 * note.instrument
            if code not in lines:
                lines[code] = UnprocessedLine(note.key, note.instrument)
            lines[code].add_note(int(0.5 + tick * multiplier))
    split_lines = []
    for line in lines.values():
        split_lines += line.split()
    return split_lines


"""
song is either pynbs.File or string (= input path)
sides_mode is how many sides the noteblocks should have (-1, or between 1 and 3)
-1: using the best
1: 2n wide, n high rectangle in front
2: 2n×n rectangle to the right and another in front
3: 2n×n rectangles on all 3 sides
"""
def convert(song, out_path, sides_mode=-1):
    if type(song) == str:
        song = pynbs_read(song)
    lines = from_nbs_file(song)
    schem = Schematic()
    count = len(lines)
    if sides_mode == -1:
        if count <= 128:
            sides_mode = 1
        elif count <= 256:
            sides_mode = 2
        else:
            sides_mode = 3
    count /= 2 * sides_mode
    count = int(0.5 + ceil(sqrt(count)))
    if sides_mode == 1:
        build_lines(schem, lines, 0, count * 2, count * 2, count)#TODO bad cuz of the lines that don't need to actually be there, we need a better way to create space
    elif sides_mode == 2:
        build_lines(schem, lines, count * 2, count * 2, 0, count)
    else:
        build_lines(schem, lines, count * 2, count * 2, count * 2, count)
    schem.save(out_path)
