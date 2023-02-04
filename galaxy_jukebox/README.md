# Galaxy Jukebox

Schematic exporter for Minecraft Note Block Studio, making a galaxy-shaped redstone jukebox, that plays the song.

Works with old and new versions of the nbs format, and outputs version 2 of Sponge schematic (it works with WorldEdit e.g.).

See [Galaxy Jukebox GUI](https://pypi.org/project/galaxy-jukebox-gui/) for the graphical interface.

## Installation

The project is available on [PyPI](https://pypi.org/project/galaxy-jukebox/), so you can install it via pip, if you have Python3 installed:

```sh
pip3 install galaxy-jukebox
```

## Usage

### From command line

You can convert a single file with:

```sh
python3 -m galaxy_jukebox input.nbs output.schem
```

or by using the dedicated command:

```sh
galaxy_jukebox input.nbs output.schem
```

### From script

I'll show you how to use it with an example: this script batch converts all the nbs files from the current directory:

```py
#!/usr/bin/env python3

from galaxy_jukebox import convert
from os import listdir

for filename in listdir():
    if filename[-4:] == ".nbs":
        convert(filename, filename[:-4] + ".schem")
```
This is the header for the convert function:

```py
convert(song, out_path, use_redstone_lamp=True, sides_mode=-1)
```

Song is either pynbs.File, or a string (input path).

Output path is string.

Use redstone lamp: whether or not to place redstone lamp next to the note block (it looks cooler with lamp, but playback performance may be compromised).

Sides mode is how many sides the noteblocks should have (-1, or between 1 and 3):

- -1 (automatic): using one of the following 3 based on noteblock count
- 1: 2n wide, n high rectangle in front
- 2: 2n×n rectangle to the right, and another in front
- 3: 2n×n rectangles on all 3 sides

## Feedback

Be sure to tell me if something ain't right, e.g. by opening an [issue](https://github.com/4321ba/Galaxy_Jukebox/issues)!

## How it works

If you're interested in how it works, you can read the documentation [locally](documentation.md) (or on [GitHub](https://github.com/4321ba/Galaxy_Jukebox/blob/main/galaxy_jukebox/documentation.md)), where I try to describe the ideas behind the conversion.

## Minecraft version

The program currently needs 1.14 for:

- scaffolding (for the 1gt delay, there are [other designs too](https://www.youtube.com/watch?v=O0xOAOM_R0Y), but this seems the best)
- smooth granite/andesite slab (aesthetics)
- birch sign (because we need 1.14, the sign has to have a woodtype)
- all the noteblock sounds (there isn't any check present, whether they are available)
- 1.13 is maybe needed for the .schem support (and blockstates) in WorldEdit/etc., idk
- 1.13 for jungle wood

## Performance

It is fine in my opinion, it takes 12 seconds to convert the 10 minute version of Genesis of the End on my machine (not a beast).

## Huge thanks to these projects!
- [OpenNBS](https://github.com/OpenNBS/OpenNoteBlockStudio), the program for creating note block music
- [PyNBS](https://github.com/vberlier/pynbs), the library for interacting with NBS files
- [MCSchematic](https://github.com/Sloimayyy/mcschematic), for creating the output schematic file
- [Lithium](https://www.curseforge.com/minecraft/mc-mods/lithium), [Sodium](https://www.curseforge.com/minecraft/mc-mods/sodium) and [Phosphor](https://www.curseforge.com/minecraft/mc-mods/phosphor) for optimizing the game enough for it to be able to play more complex pieces

## Related links

- [Open Noteblock Studio issue](https://github.com/OpenNBS/OpenNoteBlockStudio/issues/310)
- [ONBS schematic export rework project](https://github.com/OpenNBS/OpenNoteBlockStudio/projects/1)
- [Noteblock instruments on MC wiki](https://minecraft.fandom.com/wiki/Note_Block#Instruments)
