#!/bin/bash

# probably wiser to paste the lines one by one

rm -r standalone.build
rm -r standalone.dist
rm -r standalone.onefile-build
rm -r virt_env
python3 -m venv virt_env
source virt_env/bin/activate
python3 -m pip install galaxy-jukebox-gui nuitka ordered-set zstandard
python3 -m nuitka --onefile --enable-plugin=pyqt5 --include-package-data=galaxy_jukebox_gui --output-filename=galaxy-jukebox-gui.bin standalone.py
deactivate
