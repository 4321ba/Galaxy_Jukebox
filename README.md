# Galaxy Jukebox

Schematic exporter for Minecraft Noteblock Studio, making a galaxy-shaped jukebox that plays the song.

Works with old and new versions of the nbs format, and outputs version 2 of Sponge schematic (it works with WorldEdit e.g.).

## Usage

### Installing dependencies

You'll need to install Python3. (Don't forget to add it to path!)

This program also requires `nbtlib` and `pynbs` to be installed:

```sh
pip3 install nbtlib pynbs
```

### Batch converting

There is a quick little script included for converting one or more files: you can paste the `.nbs` files inside the root folder (`Galaxy_Jukebox` or `Galaxy_Jukebox-main` probably), and double click `batch_convert.py` there.

If everything is setup correctly, soon you should see the output files in the same directory (it takes a couple of seconds for the conversion).

If it doesn't work, you'll probably see nothing, in that case you should try it through the command line to see the error:

```sh
python3 batch_convert.py
```

### Converting one file from command line

If you want to specify the input and output file, you should be able to use this command (the paths are relative to where you opened the terminal):

```sh
python3 main.py input.nbs output.schem
```

Be sure to tell me if something ain't right, e.g. by opening an [issue](https://github.com/4321ba/Galaxy_Jukebox/issues)!

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

## Related

- [Open Noteblock Studio issue](https://github.com/OpenNBS/OpenNoteBlockStudio/issues/310)
- [ONBS schematic export rework project](https://github.com/OpenNBS/OpenNoteBlockStudio/projects/1)
- [Noteblock instruments on MC wiki](https://minecraft.fandom.com/wiki/Note_Block#Instruments)
- [PyNBS, the library for interacting with NBS files](https://github.com/vberlier/pynbs)
- [NBTLib for the output file](https://github.com/vberlier/nbtlib)
- [Sponge schematic, output file specification](https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-2.md)
