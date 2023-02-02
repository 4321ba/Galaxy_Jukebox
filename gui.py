#!/usr/bin/env python3

# based on 
# https://realpython.com/python-pyqt-gui-calculator/
# https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QFileDialog.html

from sys import argv
from os.path import join, basename, splitext
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QPushButton, QFileDialog, QGridLayout, QLabel, QWidget, QComboBox, QCheckBox

from main import convert

def set_label_texts(bottom_text = ""):
    text = f"{len(input_files)} input files are chosen.\n"
    for infile in input_files[:10]:
        text += infile + "\n"
    if len(input_files) > 10:
        text += f"and {len(input_files) - 10} more...\n"
    if output_path != "":
        text += "\nOutput path:\n" + output_path + "\n"
    if bottom_text != "":
        text += "\n" + bottom_text + "\n"
    if text[-1] == "\n": # deleting ending line break if present
        text = text[:-1]
    right_label.setText(text)

def update_screenshot():
    # https://www.pythonguis.com/faq/adding-images-to-pyqt5-applications/
    pixmap = QPixmap(f"gui_icons/{side_combobox.currentIndex()}side_{'' if lamp_checkbox.isChecked() else 'no'}lamp.png")
    screenshot.setPixmap(pixmap)
    
def get_input_files():
    global input_files 
    global output_path
    prev_file = "" if input_files == [] else input_files[0]
    # index 0 because it returns the chosen file extension as well, but we don't care about that:
    input_files = QFileDialog.getOpenFileNames(window, "Choose input files", prev_file, "Noteblock Studio Files (*.nbs)")[0]
    output_path = ""
    set_label_texts()

def get_output_files():
    if input_files == []:
        set_label_texts("No input provided!")
        return
    global output_path
    prev_file = input_files[0] if output_path == "" else output_path
    if len(input_files) == 1:
        # index 0 because it returns the chosen file extension as well, but we don't care about that:
        output_path = QFileDialog.getSaveFileName(window, "Choose output file", prev_file, "Sponge Schematic Files (*.schem)")[0]
    else:
        output_path = QFileDialog.getExistingDirectory(window, "Choose output folder", prev_file)
    set_label_texts()

def convert_files():
    
    def convert_one(input, output, place_redstone_lamp, sides_mode):
        # adding extension if not present (only for the gui text, library would add it anyway)
        if output[-6:] != ".schem":
            output += ".schem"
        set_label_texts("Converting\n" + input + "\ninto\n" + output)
        # https://pythonassets.com/posts/background-tasks-with-pyqt/
        QCoreApplication.processEvents() # so that the text is updated
        convert(input, output, place_redstone_lamp, sides_mode)
        set_label_texts("Conversion done!")

    if input_files == []:
        set_label_texts("No input provided!")
        return
    if output_path == "":
        set_label_texts("No output provided!")
        return

    # disabling buttons, and saving states, so the user can't break anything while the conversion is done
    input_button.setDisabled(True)
    output_button.setDisabled(True)
    place_redstone_lamp = lamp_checkbox.isChecked()
    sides_mode = side_combobox.currentIndex()
    if sides_mode == 0:
        sides_mode = -1

    if len(input_files) == 1:
        convert_one(input_files[0], output_path, place_redstone_lamp, sides_mode)
    else:
        for infile in input_files:
            convert_one(infile, join(output_path, splitext(basename(infile))[0]), place_redstone_lamp, sides_mode)

    input_button.setDisabled(False)
    output_button.setDisabled(False)


input_files = []
output_path = "" # directory if len(input_files) >1, file if =1, "" if not yet chosen

app = QApplication(argv)

# creating window
window = QWidget()
window.setWindowTitle("Galaxy Jukebox GUI")
layout = QGridLayout()
window.setLayout(layout)


# creating left side

input_button = QPushButton("Choose input file(s)")
layout.addWidget(input_button, 0, 0)
input_button.pressed.connect(get_input_files)

output_button = QPushButton("Choose output file/folder")
layout.addWidget(output_button, 1, 0)
output_button.pressed.connect(get_output_files)

lamp_checkbox = QCheckBox("Place redstone lamp")
layout.addWidget(lamp_checkbox, 3, 0)
lamp_checkbox.setChecked(True)
lamp_checkbox.stateChanged.connect(update_screenshot)

side_combobox = QComboBox()
layout.addWidget(side_combobox, 4, 0)
side_combobox.addItem("Sides: Automatic")
side_combobox.addItem("Sides: 1")
side_combobox.addItem("Sides: 2")
side_combobox.addItem("Sides: 3")
side_combobox.currentIndexChanged.connect(update_screenshot)

screenshot = QLabel()
layout.addWidget(screenshot, 5, 0)
screenshot.setMinimumHeight(180)
screenshot.setMinimumWidth(320)
screenshot.setMaximumHeight(180)
screenshot.setMaximumWidth(320)
screenshot.setScaledContents(True)
update_screenshot()

convert_button = QPushButton("Convert")
layout.addWidget(convert_button, 6, 0)
convert_button.pressed.connect(convert_files)


# creating right side
right_label = QLabel()
layout.addWidget(right_label, 0, 1, 7, 1)
layout.setAlignment(right_label, Qt.AlignTop)
set_label_texts()

window.show()
app.exec()
