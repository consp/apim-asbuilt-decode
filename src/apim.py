import sys

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")
if sys.version_info[1] < 4:
    raise Exception("Must be using Python 3.4 or up")
# QT Imports
try:
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QGroupBox, QMessageBox, QComboBox, QScrollArea, QSizePolicy, QTabWidget, QLineEdit
    from PyQt5.QtGui import QDoubleValidator, QRegExpValidator
    from PyQt5.QtCore import QRegExp
except:
    raise Exception("PyQt5 required")

# Specific imports
from binascii import unhexlify, hexlify

# local imports
from asbuilt import AsBuilt
from encoder import HmiData, print_bits_known_de07_08, ItemEncoder, print_duplicates
from statics import JumpTables, Fields
# global imports
import argparse

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
        files, _ = QFileDialog.getOpenFileName(window, "Select ASBuilt file...", "","ForScan files (*.abt);;Ford ASBuilt XML (*.ab);;All Files (*)", options=options)
        if files:
            self.selected_file = files
            
        if self.selected_file is not None:
            try:
                self.asbuilt = AsBuilt(self.selected_file)
                self.encoder = ItemEncoder()
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
        
        self.button_group_layout.addWidget(self.button_open)
        self.button_group_layout.addWidget(self.button_save)
        self.button_group_layout.addWidget(self.button_save_as)
        self.button_group_layout.addWidget(self.button_exit)
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
            for byte in self.asbuilt.block(x-1):
                text = QLineEdit()
                text.setValidator(QRegExpValidator(QRegExp("[0-9A-F][0-9A-F]")))
                text.setText("%02X" % (byte))
                text.setMaximumWidth(22)
                text.setEnabled(False)
                blockview_layout.addWidget(text)
                self.textblocks[x-1].append(text)

            setup = QWidget()
            setup_layout = QVBoxLayout()
            setup_layout.addWidget(blockview)
            setup_layout.addWidget(scroll_area)
            setup.setLayout(setup_layout)
            
            items = self.encoder.QtItemList(x, self.asbuilt, self.textblocks[x-1])
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
        self.picker_window.show()
                
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
    parser = argparse.ArgumentParser(description="""These are the options from the options list in the HMI_AL code. Most of them I verified in code (e.g. by studieing the related log messages by decompiling the file). They match the inputs for de DE00-DE03 (7D0-01-xx to 7D0-03-xx).

Options are bit fields. So if the item as 4 options, the bitmask is 0x3, and 0x7 for 8. Most items are boolean (e.g. 0 disabled, 1 enabled)

Option 1-133 are bitfields
Option 134 and up (DE04-DE06, 7D0-05 to 7D0-07) are either lookup tables or offset/value calculation based on values in the calibration files. The higher ones are combination of options."
"""
)

    parser.add_argument("abtfile", help="ForScan abt filename of 7D0 region. Supported for two filenames which can be compared. First file is marked with 1>, second with 2>.", type=str, nargs='*')
    parser.add_argument("--hmifile", help="File to load hmi strings from", type=str, default="bin/data.bin")
    parser.add_argument("--debug", help="print debug info", action="store_true")
    parser.add_argument("--noprint", help="don't print data", action="store_true")
    parser.add_argument("--save", help="save data to forscan abt file (e.g. in case you want to fix the checksums)", action="store_true")
    parser.add_argument("--export-hmidata", help="Export the imported data to file", type=str)
    args = parser.parse_args()

    abtfile = args.abtfile
    debug = args.debug

    asbuilt1 = AsBuilt(abtfile[0]) if len(abtfile) > 0 else None
    asbuilt2 = AsBuilt(abtfile[1]) if len(abtfile) > 1 else None
    if asbuilt1 is not None and len(abtfile) > 0 and not debug:

        if not args.noprint:
            try:
                print(ItemEncoder().format_all(asbuilt1, asbuilt2))
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



