# Documentation

Here I'll try to describe the main ideas, and how the NBS file becomes a SCHEM file.

First: a line is one noteblock in front of the player, plus the redstone wire line behind it.

## Getting the data we need from the NBS file

So first we get our NBS file into `unsplit_lines.lines_from_song`, where we separate the different notes based on instrument and pitch. Quantizing it to 20tps also happens here. We know that notes with different instrument and pitch needs to be for sure on a different line. After that, this function also splits the same instrument-pitch lines a bit further if needed: there could be multiple reasons (even/odd, same note same time twice, or too small delay between 2 notes). After this, we know that these lines can theoretically be built.

## Even and odd lines

There's an important distinction between even and odd lines: there are 20 gameticks in a second, but redstone only ticks 10 times / sec. You can get an odd number of gametick delays with redstone, but it's not that easy (that scaffolding thing after the diorite line does that). So after we create the odd delay, we'll be playing solely "even" or solely "odd" notes on a single line (that's why we separate them early on).

## Main idea for the line

The main idea of the line is that on the top there's one redstone pulse going away from the player, and if needed, it "loops back" to the bottom (as well as continuing on the top), so in the end, at the bottom we get back as many pulses with as much delay as we want.

## Building the area in front of the player

Now that we know what noteblocks we need to place, and what delays are needed, we create `SplitLine`s, that has the methods to build the contraption. `split_lines.build_contraption` commands the building. There's some janky math going on to calculate the positions, but all the lines get a coordinate, where they can start building their own stuff. First they place the noteblock (`build_noteblock`), then the turn if they are on the left or right side (`build_side_turn`), then the redstone staircase up/down (`build_vertical_adjustment`), then they organize themselves into a nice grid horizontally as well (`build_horizontal_adjustment`). `build_junction` is needed for both even (andesite) and odd (granite) start-lines to be able to pass through from left to right, while exactly one of them powers this particular line (the top part), all this while the redstone from the front (at the bottom) can come back to power the noteblock.

## Delay compensation

During these, there are extra repeaters needed on some lines (for getting the signal strength back to 15), which would ruin the syncronization between lines. Compensation happens by adding some delay for the first note on lines that would be too fast (`self._delays[0] += ...`). Here the delays are already relative to the previous one, so adding it to the first one shifts the whole thing.

## Different minimum delays, and line design

Now comes the jankiest part: we differentiate between minimum delays, so there are 8 similar, but different designs (md 2-9) to build one loopback (`builder.build_delay`). This whole thing is needed, because naturally we want to use repeaters with big delays, so that the machine is compact. However, what happens if you place a 4 tick repeater and power it in quick succession? It stays on (vs. a one tick one could flicker faster). So we can e.g. only use 2 tick repeaters (and not 3 tick ones), if this line after this loopback has 4 tick delays (md, minimum delay = 4). This is needed, because the 2 tick repeater cannot be powered/depowered for 1 tick only (this is different from the fact that it creates a delay of 2 ticks!); so we need 2 tick for the repeater to power up, and then to power down, for it to be able to forward the 4 tick delay that exists somewhere afterwards on this line (so a 3 tick repeater is too slow for this!). There's more to it, see comments in `builder.py` if you're interested.

## Turning the line

So now we can build one loopback, but we also need to exactly control where the line turns. I won't comment much on that, but that's what `split_lines.SplitLine.build_delays` tries to do, with quite a few edge cases and whatnot. It uses binary search to find where to cut the delay in half, if needed; as well as sometimes it puts 1-2 dots of redstone as a filler too.

## Building stuff not closely related to lines

The other building functions are also in `split_lines.py`, such as `build_vertical_connection` for the andesite/granite column on the left for the vertical connection, `build_1gt_delayer` for the scaffolding thing, as well as `build_glass_walkway` for where the player stands and for the diorite line with the button.