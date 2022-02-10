#!/usr/bin/env python3

# represents the noteblocks of a certain instrument and pitch
# may need to be split (further), because it may contain more than one of the same note playing at once
# or for other reasons
class UnsplitLine:
    
    def __init__(self, key, instrument):
        self.key = key
        self.instrument = instrument
        self.ticks = {} # indexed with tick, value >0 is noteblock count at that tick
    
    def __repr__(self):
        return f"[UnprocessedLine i,k:{self.instrument},{self.key} ticks:{self.ticks}]"
    
    # tps is already supposed to be 20 here, tick=20 means 1 sec
    def add_note(self, tick, count=1):
        if not tick in self.ticks:
            self.ticks[tick] = 0
        self.ticks[tick] += count
    
    def is_empty(self):
        return not self.ticks
    
    # splits this line into 2 lines, one with even and one with odd (game)tick values
    def _split_even(self):
        new_line = UnsplitLine(self.key, self.instrument)
        evenness = next(iter(self.ticks)) % 2 # first key in dict
        for tick in list(self.ticks): # list of keys, so that we can safely remove elements
            if tick % 2 != evenness:
                new_line.add_note(tick, count=self.ticks[tick])
                self.ticks.pop(tick)
        return [self] if new_line.is_empty() else [self, new_line]
    
    # splits off one line, that is returned, that is fully split and can be converted to a SplitLine later
    # self's ticks have to have the same parity already
    def _split_further(self):
        new_line = UnsplitLine(self.key, self.instrument)
        previous = -42 # there can't be 2 notes closer to each other than 4 gameticks
        for tick in sorted(self.ticks): # this creates a list, we can safely remove elements from ticks
            if previous + 4 <= tick:
                previous = tick
                new_line.add_note(tick)
                if self.ticks[tick] > 1:
                    self.ticks[tick] -= 1
                else:
                    self.ticks.pop(tick)
        return new_line
    
    # we need to split this line if
    # 1) there are both odd and even tick delays (_split_even) or
    # 2) there are more than 1 notes playing at the same time (_split_further) or
    # 3) there is a 2 tick delay somewhere (_split_further)
    def split(self):
        assert not self.is_empty(), f"Empty {self} cannot be split!" # assert: true is good, false is bad
        lines_halfsplit = self._split_even()
        processed_lines = []
        for line in lines_halfsplit:
            assert len(set(k % 2 for k in line.ticks)) == 1, f"All keys should have the same parity, but they don't: {line}"
            while not line.is_empty():
                new_line = line._split_further()
                assert all(count == 1 for count in new_line.ticks.values()), f"All values should be one (the line should be fully split), but they aren't: {line}"
                processed_lines.append(new_line)
        return processed_lines

# needs a pynbs.File song and
# gives back a list of UnsplitLines that are ready to be converted to SplitLines
def lines_from_song(song, override_tempo=-1):
    # this is hardcoded as in NBS there isn't a 6.67 tps option, so
    # 6.75 almost always wants to mean every 3 gameticks
    if song.header.tempo == 6.75:
        song.header.tempo = 20/3
    # this is where we fix the tps to 20, so we multiply tick by this:
    multiplier = 20 / (song.header.tempo if override_tempo == -1 else override_tempo)
    lines = {} # indexed with (key, instrument)
    for tick, chord in song:
        for note in chord:
            code = (note.key, note.instrument)
            if code not in lines:
                lines[code] = UnsplitLine(note.key, note.instrument)
            lines[code].add_note(int(0.5 + tick * multiplier)) # rounding
    split_lines = []
    for line in lines.values():
        split_lines += line.split()
    return split_lines


