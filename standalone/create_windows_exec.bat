:: probably wiser to paste the lines one by one

python -m venv virt_env
virt_env/Scripts/activate.bat
python -m pip install galaxy-jukebox-gui nuitka ordered-set zstandard
python -m nuitka --onefile --enable-plugin=pyqt5 --include-package-data=galaxy_jukebox_gui --output-filename=galaxy-jukebox-gui.exe --disable-console standalone.py
deactivate
