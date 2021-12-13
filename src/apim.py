import sys

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")
if sys.version_info[1] < 4:
    raise Exception("Must be using Python 3.4 or up")
# QT Imports
try:
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QGroupBox, QMessageBox, QComboBox, QScrollArea, QSizePolicy, QTabWidget, QLineEdit, QStatusBar
    from PyQt5.QtGui import QDoubleValidator, QRegExpValidator
    from PyQt5.QtCore import QRegExp, Qt
    from functools import partial
except:
    raise Exception("PyQt5 required")

# Specific imports
from binascii import unhexlify, hexlify

# local imports
from asbuilt import AsBuilt
from encoder import print_bits_known_de07_08, ItemEncoder, print_duplicates
from statics import JumpTables, Fields, ThemeConfig
# global imports
import argparse

def calc_change(block, loc, cfield, fields):
    x = []
    x.append(0x07)
    x.append(0xD0)
    x.append(block)
    x.append(loc)
    for f in fields:
        x.append(int(f.text(), 16))

    cfield.setText("%02X" % (sum(x) & 0x00FF))

class QtApp(object):

    app = None
    main_layout = None
    main_window = None
    button_open = None
    button_exit = None
    button_save = None
    button_save_as = None

    current_window = None

    picker_window = None
    picker_layout = None

    selected_file = None
    asbuilt = None
    encoder = None

    blockdata = None

    block = 1

    textblocks = []

    def open_file(self):
        window = self.current_window
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileName(window, "Select ASBuilt file...", "","ForScan files (*.abt);;Ford ASBuilt XML (*.ab);;UCDS XML files (*.xml);;All Files (*)", options=options)
        if files:
            self.selected_file = files

        if self.selected_file is not None:
            try:
                self.asbuilt = AsBuilt(self.selected_file)
                self.encoder = ItemEncoder(self.asbuilt)
                self.launch_picker()
            except ValueError as e:
                QMessageBox.critical(self.current_window, "Error opening file", str(e))
                self.selected_file = None
                self.current_window.show()


    def save_file_as(self, window=None):
        window = self.current_window
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, things = QFileDialog.getSaveFileName(window, "Save file to ...", "","ForScan files (*.abt)", options=options)
        if files:
            self.selected_file = files
        if self.selected_file.endswith(".ab"):
            self.selected_file = self.selected_file[:-3]
        if not self.selected_file.endswith(".abt"):
            self.selected_file = self.selected_file + ".abt"

        if self.selected_file is not None and files is not None and len(files) > 0:
            self.save(overwrite=True)

    def save(self, overwrite=False):
        for x in range(0, self.asbuilt.block_size()):
            block = list(self.asbuilt.blocks[x])
            for b in range(0, len(self.textblocks[x])):
                block[b] = int(self.textblocks[x][b].text(), 16)
            self.asbuilt.blocks[x] = bytes(block)
        string = self.asbuilt.save()

        print("Saving to %s" % self.selected_file)
        print(string)
        item = False
        if not overwrite:
            item = QMessageBox.question(self.current_window, "Save...", "Do you want to overwrite %s?" % (self.selected_file), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if item == QMessageBox.Yes or overwrite:
            print("saving")
            try:
                with open(self.selected_file, "w") as f:
                    f.write(string)
                    f.flush()
                    f.close()
            except Exception as e:
                QMessageBox.critical(self.current_window, "Error saving to file", str(e))
                pass




    def block_change(self):
        print("Selected item %d" % (self.block_combo_box.currentIndex()))
        self.block = self.block_combo_box.currentIndex() + 1
        self.add_blockitems()


    def launch_picker(self):
        self.main_window.hide()
        if self.picker_window is not None:
            self.picker_window.hide()

        self.picker_window = QWidget()
        self.picker_window.resize(1024, 800)

        self.picker_layout = QVBoxLayout()

        ## main group
        self.button_group = QGroupBox("Main things")
        self.button_group_layout = QHBoxLayout()
        self.button_save = QPushButton("Save") if self.button_save is None else self.button_save
        self.button_save_as = QPushButton("Save as ...") if self.button_save_as is None else self.button_save_as
        self.button_save_as.clicked.connect(self.save_file_as)
        self.button_save.clicked.connect(self.save)
        self.syncversion = QComboBox()
        if self.asbuilt.s4:
            self.syncversion.addItems(["4"])
            self.syncversion.setEnabled(False)
        else:
            self.syncversion.addItems(["3.0-3.2", "3.4"])
            self.syncversion.setCurrentIndex(1)

        self.button_group_layout.addWidget(self.button_open)
        self.button_group_layout.addWidget(self.button_save)
        self.button_group_layout.addWidget(self.button_save_as)
        self.button_group_layout.addWidget(self.button_exit)
        self.button_group_layout.addWidget(self.syncversion)
        self.button_group.setLayout(self.button_group_layout)

        ## Block group
        self.block_group = QGroupBox("Select block")
        self.block_group_layout = QVBoxLayout()

        #self.block_combo_box = QComboBox()

        #self.block_combo_box.addItems(["7D0-%02X or DE%02X" % (x, x-1) for x in range(1, self.asbuilt.size()+1)])
        #self.block_combo_box.currentIndexChanged.connect(self.block_change)

        self.tabs = QTabWidget()
        self.tab = []
        self.textblocks = []
        for x in range(1, self.asbuilt.block_size() + 1):
            block_items_group = QGroupBox()
            block_items_layout = QVBoxLayout()
            block_items_group.setLayout(block_items_layout)

            setup = QWidget()

            scroll_area = QScrollArea()
            scroll_area.setWidget(block_items_group)
            scroll_area.setWidgetResizable(True)

            blockview = QGroupBox("Binary")
            blockview_layout = QHBoxLayout()
            blockview.setLayout(blockview_layout)
            self.textblocks.append([])
            bt = 0
            for byte in self.asbuilt.block(x-1):
                text = QLineEdit()
                text.setValidator(QRegExpValidator(QRegExp("[0-9A-F][0-9A-F]")))
                text.setText("%02X" % (byte))
                text.setMaximumWidth(22)
                text.setReadOnly(True)
                if (bt % 5) == 0:
                    label = QLabel()
                    label.setText("7D0-%02X-%02X" % (x, (bt//5)+1))
                    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    blockview_layout.addWidget(label, stretch=0)
                    blockview_layout.addWidget(text, stretch=1)
                else:
                    blockview_layout.addWidget(text, stretch=0)
                    if bt % 5 == 1 or bt % 5 == 3:
                        label2 = QLabel()
                        label2.setText(" ")
                        label2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        label2.adjustSize()
                        blockview_layout.addWidget(label2, stretch=0)



                bt += 1
                self.textblocks[x-1].append(text)

                if bt % 5 == 0:
                    text = QLineEdit()
                    text.setValidator(QRegExpValidator(QRegExp("[0-9A-F][0-9A-F]")))
                    calc_change(x, ((bt-1) // 5) + 1, text, self.textblocks[x-1][bt-5:bt])
                    text.setMaximumWidth(22)
                    text.setReadOnly(True)
                    for n in self.textblocks[x-1][bt-5:bt]:
                        n.textChanged.connect(partial(calc_change, x, ((bt-1) // 5) + 1, text, self.textblocks[x-1][bt-5:bt]))
                    blockview_layout.addWidget(text)
                    blockview_layout.addStretch(1)
            if bt % 5 != 0:
                text = QLineEdit()
                text.setValidator(QRegExpValidator(QRegExp("[0-9A-F][0-9A-F]")))
                calc_change(x, ((bt-1) // 5) + 1, text, self.textblocks[x-1][bt-(bt % 5):bt])
                text.setMaximumWidth(22)
                text.setReadOnly(True)
                for n in self.textblocks[x-1][bt-(bt % 5):bt]:
                    n.textChanged.connect(partial(calc_change, x, ((bt-1) // 5) + 1, text, self.textblocks[x-1][bt-(bt % 5):bt]))
                blockview_layout.addWidget(text)
                blockview_layout.addStretch(1)

            setup = QWidget()
            setup_layout = QVBoxLayout()
            setup_layout.addWidget(blockview)
            setup_layout.addWidget(scroll_area)
            setup.setLayout(setup_layout)

            items = self.encoder.QtItemList(x, self.asbuilt, self.textblocks[x-1], self.themechange)
            for item in items:
                block_items_layout.addLayout(item)
            self.tab.append(setup)
            self.tabs.addTab(self.tab[x - 1], "7D0-%02X" % (x))



        #self.block_group_layout.addWidget(self.block_combo_box)
        self.block_group_layout.addWidget(self.tabs)
        self.block_group.setLayout(self.block_group_layout)

        self.picker_layout.addWidget(self.button_group)
        self.picker_layout.addWidget(self.block_group)

        self.picker_window.setLayout(self.picker_layout)
        self.current_window = self.picker_window
        #self.picker_window.setSizePolicy(QSizePolicy.Expanding)
        self.statusBar = QStatusBar()
        self.picker_layout.addWidget(self.statusBar)
        self.statusBar.showMessage("")
        self.picker_window.show()

    def themechange(self):

        animation = int(self.textblocks[1][2].text(), 16)
        theme = int(self.textblocks[2][2].text(), 16)
        brand = (int(self.textblocks[0][5].text(), 16) & 0b11100000) >> 5

        #print(theme, animation, brand, self.syncversion.currentText())
        matches = ThemeConfig.validate(brand, theme, animation, version=self.syncversion.currentText())

        message = "No themes found matching configuration!" if len(matches) == 0 else matches[0] if len(matches) == 1 else "Found %d themes: %s" % (len(matches), "".join(matches))
        self.statusBar.showMessage(message)
        #print(matches)
        #f = ThemeConfig.validate()


    def launch_qt(self):
        self.app = QApplication([])
        self.app.setStyle('Fusion')

        self.main_window = QWidget()
        self.main_layout = QVBoxLayout()

        self.button_open = QPushButton("Open File ...")
        self.button_open.clicked.connect(self.open_file)
        self.button_exit = QPushButton("Exit")
        self.button_exit.clicked.connect(sys.exit)


        self.main_layout.addWidget(self.button_open)
        self.main_layout.addWidget(self.button_exit)

        self.main_window.setLayout(self.main_layout)
        self.current_window = self.main_window
        self.main_window.show()
        self.app.exec_()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
            Open and compare asbuilt files or use the GUI to edit them. The debug options should notmally not be used as they provide no useful information to non developers.

            Run without arguments to start the GUI.
            """
)

    parser.add_argument("abtfile", help="ForScan abt filename of 7D0 region, ford asbuilt xml or ucds asbuilt xml file. \nSupported for two filenames which can be compared. First file is marked with 1>, second with 2>.\nIf no filename is given the GUI will start.", type=str, nargs='*')
    parser.add_argument("--debug", help="print debug info", action="store_true")
    parser.add_argument("--noprint", help="don't print data, use with debug", action="store_true")
    parser.add_argument("--save", help="save data to forscan abt file (e.g. in case you want to fix the checksums)", action="store_true")
    args = parser.parse_args()

    abtfile = args.abtfile
    debug = args.debug

    asbuilt1 = AsBuilt(abtfile[0]) if len(abtfile) > 0 else None
    asbuilt2 = AsBuilt(abtfile[1]) if len(abtfile) > 1 else None
    if asbuilt1 is not None and len(abtfile) > 0 and not debug:

        if not args.noprint:
            try:
                print(ItemEncoder(asbuilt1).format_all(asbuilt1, asbuilt2))
            except Exception as e:
                print(asbuilt1.filename, asbuilt1.blocks)
                raise
    elif not debug:
        app = QtApp()
        app.launch_qt()
    elif debug:
        print_bits_known_de07_08()
        print_duplicates()
        print(asbuilt1.filename, str(asbuilt1), sep="\n") if asbuilt1 is not None else ""
        print(asbuilt2.filename, str(asbuilt2), sep="\n") if asbuilt2 is not None else ""



