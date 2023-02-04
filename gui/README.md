# Galaxy Jukebox GUI

Graphical user interface for Galaxy Jukebox, which is a schematic exporter for Minecraft Note Block Studio.

The actual conversion happens by [Galaxy Jukebox](https://pypi.org/project/galaxy-jukebox/).

## Installation

The project is available on [PyPI](https://pypi.org/project/galaxy-jukebox-gui/), so you can install it via pip, if you have Python3 installed:

```sh
pip3 install galaxy-jukebox-gui
```

Alternatively, (hopefully) you will be able to download an executable from [GitHub Releases](https://github.com/4321ba/Galaxy_Jukebox/releases), if you don't have Python.

## Usage

If you downloaded the pip version, you can launch it by entering the command `python3 -m galaxy_jukebox_gui` or `galaxy-jukebox-gui`. If you downloaded the executable, then e.g. double click the executable to execute it (you may need to give it permission).

You should see something similar to this (theming may be different):

<!---Github absolute link, so it works on PyPI at least--->
![See the PyPI page for the screenshot!](https://raw.githubusercontent.com/4321ba/Galaxy_Jukebox/main/gui/gui_screenshot.png)

(It's qt, isn't it :D?)

You can choose a single, or multiple input files, and an output file (if you chose a single input file) or an output path (if you chose multiple input files). The chosen files/path will be printed on the right. The 2 options available are the same as for the command line program (and choosing different options should change the image):

Use redstone lamp: whether or not to place redstone lamp next to the note block (it looks cooler with lamp, but playback performance may be compromised).

Sides mode is how many sides the noteblocks should have (-1, or between 1 and 3):

- -1 (automatic): using one of the following 3 based on noteblock count
- 1: 2n wide, n high rectangle in front
- 2: 2n×n rectangle to the right, and another in front
- 3: 2n×n rectangles on all 3 sides

## Feedback

Be sure to tell me if something ain't right, e.g. by opening an [issue](https://github.com/4321ba/Galaxy_Jukebox/issues)!

## Used libraries

The project uses PyQt5 for the GUI.