# Galaxy Jukebox

Schematic exporter for Minecraft Noteblock Studio, making a galaxy-shaped jukebox that plays the song.

## Current state

The program is feature complete, but there are some some more things I may want to do.

## Minecraft version

The program currently needs 1.14 for:

- scaffolding (for the 1gt delay, there are [other designs too](https://www.youtube.com/watch?v=O0xOAOM_R0Y), but this seems the best)
- smooth granite/andesite slab (aesthetics)
- birch sign (because we need 1.14, the sign has to have a woodtype)
- all the noteblock sounds (there isn't any check present whether they are available)
- 1.13 is maybe needed for the .schem support (and blockstates) in WorldEdit/etc., idk
- 1.13 for jungle wood

## Performance

It is bad, though not as terrible as it used to be. It takes 2-30 seconds for one song, depending on the song complexity. Much improvement could be made by rewriting `builder.get_delay_length` to use raw math instead of building the whole thing with `builder.build_delay` and then throwing it away.
