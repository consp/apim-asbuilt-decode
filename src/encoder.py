from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLayout, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QGroupBox, QMessageBox, QComboBox, QScrollArea, QLineEdit, QSizePolicy, QFrame, QLabel
from PyQt5.QtGui import QDoubleValidator, QRegExpValidator
from PyQt5.QtCore import QRegExp, Qt

from functools import partial
from statics import JumpTables, Fields
from asbuilt import AsBuilt


DEBUG=False

import struct
class HmiData(object):
    data = None
    items = [] # block 0-3
    high_items = [] # block 5-7
    index_locations_high = [ # offset to DE04, includes DE05 and DE06 (7D0-05-07), format [byte start, byte end, bitvalue (first bit is 1)]
        [0, 2], [2, 2], [4, 2], [6, 1, 1], [6, 1, 2], [7, 1], [8, 1], [9, 1], [10, 1], [11, 1], [12, 2], [14, 2], [16, 2], [18, 1], [19, 1], [20, 1], [21, 2]
    ]

    def output_stuff(self, ab):
        for x in range(1, 5):
            print("    de%02X = [" % (x-1))
            for item in self.items:
                l =  self.bit(item['index'])//8
                if l < ab.start_byte(x+1) and l >= ab.start_byte(x):
                    print("        {")
                    print("            'name': '%s'," % item['name'])
                    print("            'index': %d," % (item['index'] + 1))
                    print("            'byte': %d," % (self.byte(item['index']) - ab.start_byte(x)))
                    print("            'bit': %d," % (self.bit(item['index']) % 8)) # reverse
                    print("            'size': %d," % (item['items']))
                    if item['items'] >= 255 or '255' in item:
                        print("            'type': 'table',")
                        try:
                            print("            'table': '%s'," % (item['255']))
                        except:
                            print(item)
                            raise
                        continue
                    print("            'items':", item['items'], ",")
                    print("            'type': 'mask',")
                    for z in range(0, item['items']):
                        print("            '%d': '%s'," % (z, item['%d'%z]))
                    print("        },")
            print("    ]\n\n")

        for x in range(5, 8):
            print("    de%02X = [" % (x))
            for item in self.high_items:
                l = ab.start_byte(5) + self.index_locations_high[item['index']][0]
                if l < ab.start_byte(x+1) and l >= ab.start_byte(x):
                    print("        {")
                    print("            'name': '%s'," % item['name'])
                    print("            'index': %d," % (item['index'] + 135))
                    print("            'byte': %d," % ((ab.start_byte(x) - ab.start_byte(5)) + self.index_locations_high[item['index']][0]))
                    print("            'size': %d," % (2**(self.index_locations_high[item['index']][1]*8) - 1))
                    if len(self.index_locations_high[item['index']]) == 2:
                        print("            'bit': %d," % (0))
                        print("            'type': 'mul',")
                        print("            'min': %s," % (item['min']))
                        print("            'max': %s," % (item['max']))
                        print("            'offset': %s," % (item['offset']))
                        print("            'multiplier': %s," % (item['multiplier']))
                        print("            'unit': '%s'," % (item['255']))
                    else:
                        print("            'bit': %d," % (self.index_locations_high[item['index']][2]-1))
                        for z in range(0, item['items']):
                            print("            '%d': '%s'," % (z, item['%d'%z]))
                        print("            'items':", item['items'], ",")
                    print("        },")
            print("    ]\n\n")

    def __init__(self, filename):
        """
        The fields are as follows:
            [index][minor index][127 * name][\0][index][minor index][255 * value][\0]
            for a total of 378 bytes per item
            The index is the number of the setting, the minor index is the option (e.g. 0, 1, 2, 3 for a 4 bit field)
        """
        try:
            with open(filename, "rb") as f:
                inp = f.read()
                try:
                    rawdata = unhexlify(inp.replace(b"\n", b"").replace(b" ", b""))
                except:
                    rawdata = inp
        except:
            print("Requires hmi file to be present. Expecting %s but not found" % hmifile)
            exit(1)

        data = rawdata[rawdata.find(b"Smart DSP")-2:]
        self.data = b""
        item = {}
        items = [] # de00-03
        try:
            for i in range(0, len(data), 128 + 256 + 4):
                index = data[i]
                itemindex = data[i+1]
                name = data[i+2:i+130].replace(b"\x00", b"")

                if len(items) < index + 1:
                    items.append({})
                    items[index]['name'] = name.decode()
                    items[index]['index'] = index
                valueindex = data[i+129]
                valueindex_minor = data[i+130]
                value = data[i+131:i+131+257].replace(b"\x00", b"")
                if "%d" % valueindex_minor not in items[index]:
                    items[index]["%d" % valueindex_minor] = value.decode()
                    if 'items' not in items[index]:
                        items[index]['items'] = 1
                    else:
                        items[index]['items'] = items[index]['items'] + 1
                    if valueindex_minor == 255:
                        if value.decode() == "_BPT":
                            items[index]['items'] = 1048575 # replaced by Sync Connect settings
                        elif value.decode() == "BAPI":
                            items[index]['items'] = 65535 # double block
                        elif value.decode() == "___C":
                            items[index]['items'] = 31
                        else:
                            items[index]['items'] = 255
                    elif valueindex_minor == 254:
                        items[index]['items'] = 254
                self.data = self.data + data[i:i+128 + 256 + 4]
                if index == 133: # there are 134 categorized items out 178 in total which this data blob contains, 135 for sync 3.4 but one is unencoded
                    break
                #print("%d %d %s %d %d %s" % (index, itemindex, name, valueindex, valueindex_minor, value))
        except Exception as e:
            raise
        high_items = [] # de04-07
        try:
            data = rawdata[rawdata.find(b"Front Track") - 2:]
            for i in range(0, len(data), 212):
                if i > 0x12 * 212:
                    break
                item = {}
                index = data[i]
                name = data[i+2:i+2+128].replace(b"\x00", b"")
                mul = struct.unpack("<f", data[i+4+128:i+4+128+4])[0]
                off = struct.unpack("<I", data[i+4+128+4:i+4+128+8])[0]
                min = struct.unpack("<f", data[i+4+128+8:i+4+128+12])[0]
                max = struct.unpack("<f", data[i+4+128+12:i+4+128+16])[0]
                m = data[i+4+128+16:i+4+128+16+32].replace(b"\x00", b"")
                item['name'] = name.decode()
                item['index'] = index
                minor = 255
                if struct.unpack("<I", data[i+180:i+184])[0] != 0xFFFFFFFF:
                    m = data[i+184:i+184+28].replace(b"\x00", b"")
                    minor = data[i+180]
                else:
                    item['min'] = min
                    item['max'] = max
                    item['offset'] = off
                    item['multiplier'] = mul
                    item['unit'] = m.decode()
                if len(high_items) < index + 1:
                    if minor is not None:
                        item['%d' % minor] = m.decode()
                        item['items'] = 1
                    high_items.append(item)
                else:
                    high_items[index]['%d' % minor] = m.decode()
                    high_items[index]['items'] = high_items[index]['items'] + 1
                self.data = self.data + data[i:i+212]
        except Exception as e:
            raise

        self.items = items
        self.high_items = high_items

    def bits(self, index):
        if index < 135:
            return (self.items[index]['items'] - 1).bit_length()
        else:
            return -1

    def bit(self, index):
        return sum([(x['items'] - 1).bit_length() for x in self.items[:index]])

    def byte(self, index):
        return self.bit(index) // 8

    def size(self):
        return len(self.items)

    def index(self, index):
        return self.items[index]['index'] if index < self.size() else -1

    def name(self, index):
        return self.items[index]['name'] if index < self.size() else "NaN"

    def calc_field(self, asbuilt, index):
        bitstart = self.bit(index)
        bitend = self.bit(index + 1)
        return asbuilt.mask_string(bitstart, bitend)

    def is_table(self, index):
        return ('255' in self.items[index])

    def value(self, index):
        try:
            if self.is_table(index):
                return self.items[index]['255']
            else:
                return [self.items[index]["%d" % z] for z in range(0, self.items[index]['items'])]
        except:
            print(index)
            print(self.items[index])


    def format_de0_3(self, ab1, ab2):
        marker1 = ">>" if ab2 is None else "1>"
        marker2 = "" if ab2 is None else "2>"

        string = "#   -bits-loc- %-96s - Field      Location     Msk&Val = Res\n" % ("Name")
        for i in range(self.size()):
            mask = (2**((self.bit(i)+self.bits(i) - self.bit(i)) - 1)) << (7-((self.bit(i) + self.bits(i) - 1) % 8))
            value = int.from_bytes(ab2.bytes(self.bit(i), self.bit(i)+self.bits(i)), byteorder='big') if ab2 is not None else None
            string = string + "%-03s - %-02d - %-d  %-s %-s %-s %s\n" % (
                self.index(i)+1,
                self.bits(i),
                self.bit(i),
                self.name(i),
                "." * (98 - len(self.name(i))),
                self.calc_field(ab1, i),
                "vs %02X & %02X = %02X" % (value, mask, value & mask) if value is not None else ""
                )
            if self.is_table(i):
                string = string + "\t\t\t   Identifier type: %s -> %02X\n" % (self.value(i), ab1.byte(self.byte(i)))
                if hasattr(JumpTables, self.value(i).replace("___", "_").replace("__", "_")):
                    table = getattr(JumpTables, self.value(i).replace("___", "_").replace("__", "_"))
                    for x in range(0, len(table)):
                        string = string + ("\t\t     %2s %2s %02X:\t%s\n" % (marker1 if x == ab1.bit(self.bit(i), self.bits(i)) else "", marker2 if ab2 is not None and x == ab2.bit(self.bit(i), self.bits(i)) else "",  x, table[x]))
                else:
                    string = string + ("Attribute %s not found\n" % (self.value(i)))
                continue
            for x in range(0, len(self.value(i))):
                string = string + "\t\t     %2s %2s %d:\t%s\n" % (
                    marker1 if ab1.bit(self.bit(i), self.bits(i)) == int(x) else "",
                    marker2 if ab2 is not None and ab2.bit(self.bit(i), self.bits(i)) == int(x) else "",
                    x,
                    self.value(i)[x]
                    )
        return string

    def format_de4_6(self, ab1, ab2=None):
        """
        Blocks 4 to 6 are mostly offset, multiplier values. Thet are located in the .rodata of the HMI
        as well but not included and manually decoded.
        The function reading them has the following fields for each item:
            [32bit float multiplier][32bit usigned int offset][32bit float min][32bit float max][24 char unit]
            If the unit equals "unitless" (yes a string compare is present) nothing is displayed

        """
        string = ""
        start = ab1.start_byte(5)
        num = 135
        for i in range(0, len(self.high_items)):
            if '255' in self.high_items[i]:
                a1v = (ab1.int(start + self.index_locations_high[i][0], start + self.index_locations_high[i][0]+self.index_locations_high[i][1]))
                a2v = (ab2.int(start + self.index_locations_high[i][0], start + self.index_locations_high[i][0]+self.index_locations_high[i][1])) if ab2 is not None else None
                val1 = (self.high_items[i]['multiplier'] * a1v) + self.high_items[i]['offset']
                val2 = (self.high_items[i]['multiplier'] * a2v) + self.high_items[i]['offset'] if ab2 is not None else None
                string = string + "%-3s - %-48s%-32s\t%s%s\t%-16s%-16s\tMin: %0.1f\tMax: %0.1f\n" %(
                    num,
                    self.high_items[i]['name'],
                    ab1.mask_string((start + self.index_locations_high[i][0])*8, (start + self.index_locations_high[i][0]+self.index_locations_high[i][1])*8),
                    "%04X" % a1v,
                    " vs %04X" % a2v if a2v is not None else "",
                    "%0.1f %s%s" % (val1, self.high_items[i]['unit'], " (%0.1f cm)" % (val1 * 2.54) if self.high_items[i]['unit'] == "In" else ""),
                    " vs %0.1f %s%s" % (val2, self.high_items[i]['unit'], " (%0.1f cm)" % (val2 * 2.54) if self.high_items[i]['unit'] == "In" else "") if val2 is not None else "",
                    self.high_items[i]['min'],
                    self.high_items[i]['max']
                )
            else:
                a1byte = (ab1.int(start + self.index_locations_high[i][0], start + self.index_locations_high[i][0]+self.index_locations_high[i][1]))
                a2byte = (ab2.int(start + self.index_locations_high[i][0], start + self.index_locations_high[i][0]+self.index_locations_high[i][1])) if ab2 is not None else None
                a1v =  0x1 & (a1byte >> (8 - self.index_locations_high[i][2]))
                a2v =  0x1 & (a2byte >> (7 - self.index_locations_high[i][2])) if ab2 is not None else None

                string = string + "%-3s - %-48s%-32s: %s%s\n" %(
                    num,
                    self.high_items[i]['name'],
                    ab1.mask_string(((start + self.index_locations_high[i][0])*8) + (self.index_locations_high[i][2])-1, ((start + self.index_locations_high[i][0])*8) + (self.index_locations_high[i][2])),
                    "%02X" % a1byte,
                    "" if a2v is None else "vs %02X" % a2byte
                )
                for x in range(0, self.high_items[i]['items']):
                    string = string + "%-24s%-2s %-2s %02X: %s\n" % (
                        "",
                        "1>" if a1v == x and a2v is not None else ">>" if a1v == x else "",
                        "2>" if a2v is not None and a2v == x else "",
                        x,
                        self.high_items[i]["%d"%x]
                    )
            num += 1
        return string

    def format_de07(self, ab1, ab2=None):
        """


        {     'name': 'INTELLIGENT_ACCESS',
            'index': 289,
            'byte': 6,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        """
        string = "#%s%-96s   - Field      Location     Msk&Val = Res\n" % ("   -bits-loc  - " if DEBUG else "", "Name")
        if ab1.start_byte(8) == -1 and ab2.start_byte(8) == -1 or ab1.start_byte(8) == -1:
            return string
        for item in Fields.de07:
            bit = 7 - item['bit']
            bitloc = ab1.start_bit(8) + ((item['byte']) * 8) + bit
            value1 = ab1.bit(bitloc, item['size'].bit_length())
            value2 = ab2.bit(bitloc, item['size'].bit_length()) if ab2 is not None else None
            byte1 = ab1.byte(ab1.start_byte(8) + item['byte'])
            byte2 = ab2.byte(ab1.start_byte(8) + item['byte']) if ab2 is not None else None
            string = string + "%s%-s: %s %s // %s %s\n" % ("%d - %d  - %d\t " if DEBUG else "",
                        item['index'],
                        item['size'].bit_length(),
                        bitloc,
                        item['name'],
                        "." * (98 - len(item['name'])),
                        ab1.mask_string(bitloc, bitloc + item['size'].bit_length()),
                        "0x%02X" % byte1,
                        "" if byte2 is None else "0x%02X" % byte2
                    )
            # for now assume enable // disable if one bit or multi bit strategy
            for x in range(0, item['size']+1):
                string = string + "\t\t     %2s %2s %s:\t%s\n" % (
                        ">>" if ab2 is None and x == value1 else "1>" if x == value1 else "",
                        "2>" if ab2 is not None and x == value2 else "",
                        "%02X" % x,
                        "" # no known values
                        )

        return string

    def format_de08(self, ab1, ab2=None):
        string = "#   -bits-loc  - %-96s   - Field      Location     Msk&Val = Res\n" % ("Name")
        if ab1.start_byte(9) == -1 and ab2.start_byte(9) == -1 or ab1.start_byte(9) == -1:
            return string
        for item in Fields.de08:
            bit = 7 - item['bit']
            bitloc = ab1.start_bit(9) + ((item['byte']) * 8) + bit
            value1 = ab1.bit(bitloc, item['size'].bit_length())
            value2 = ab2.bit(bitloc, item['size'].bit_length()) if ab2 is not None else None
            byte1 = ab1.byte(ab1.start_byte(9) + item['byte'])
            byte2 = ab2.byte(ab1.start_byte(9) + item['byte']) if ab2 is not None else None
            string = string + "%d - %d  - %d\t %-s: %s %s // %s %s\n" % (
                        item['index'],
                        item['size'].bit_length(),
                        bitloc,
                        item['name'],
                        "." * (98 - len(item['name'])),
                        ab1.mask_string(bitloc, bitloc + item['size'].bit_length()),
                        "0x%02X" % byte1,
                        "" if byte2 is None else "0x%02X" % byte2
                    )
            # for now assume enable // disable if one bit or multi bit strategy
            for x in range(0, item['size']+1):
                string = string + "\t\t     %2s %2s %s:\t%s\n" % (
                        ">>" if ab2 is None and x == value1 else "1>" if x == value1 else "",
                        "2>" if ab2 is not None and x == value2 else "",
                        "%02X" % x,
                        "" # no known values
                        )

        return string



    def format(self, ab1, ab2=None):
        string = self.format_de0_3(ab1, ab2)
        string = string + self.format_de4_6(ab1, ab2)
        string = string + self.format_de07(ab1, ab2)
        string = string + self.format_de08(ab1, ab2)
        return string

def combo_change(box, item, bitfieldblock, *args, **kwargs):
    value = box.currentIndex()
    data = int(bitfieldblock.text(), 16)
    bitdata = '{0:08b}'.format(data)
    bitdata = bitdata[:item['bit']] + ("{0:0%db}" % (item['size'])).format(value) + bitdata[item['bit']+item['size']:]
    data = int(bitdata, 2)

    bitfieldblock.setText("%02X" % (data))
    
def value_change(box, item, bitfieldblock, *args, **kwargs):
    value = float(box.text())

        
    if value > item['max']:
        value = item['max']
    elif value < item['min']:
        value = item['min']
    v = ((value - item['offset']) / item['multiplier'])
    box.setText("%.2f" % value)
    data = int(bitfieldblock[0].text(), 16) if len(bitfieldblock) == 1 else int(bitfieldblock[0].text() + bitfieldblock[1].text(), 16)
    bitdata = ('{0:0%db}' % (item['size'])).format(data)
    bitdata = bitdata[:item['bit']] + ("{0:0%db}" % (item['size'])).format(int(v)) + bitdata[item['bit']+item['size']:]
    data = int(bitdata, 2)
    string = "%04X" % (data)
    if item['size'] > 8:
        bitfieldblock[0].setText(string[:2])
        bitfieldblock[1].setText(string[2:])
    else:
        bitfieldblock[0].setText(string[2:])
    
    
def ascii_change(box, item, bitfieldblock, *args, **kwargs):
    value = box.text()
    #bitdata = bitdata[:item['bit']] + ("{0:0%db}" % (item['size'])).format(value) + bitdata[item['bit']+item['size']:]
    bitfieldblock.setText("%02X" % (ord(value[0])))
    
class ItemEncoder(object):
    items = []

    def byte_loc_string(self, i, bits):
        if i == 0:
            if bits <= 8:
                return "NNxx xxxx xxcc"
            else:
                return "NNNN xxxx xxcc"
        elif i == 1:
            if bits <= 8:
                return "xxNN xxxx xxcc"
            else:
                return "xxNN NNxx xxcc"
        elif i == 2:
            if bits <= 8:
                return "xxxx NNxx xxcc"
            else:
                return "xxxx NNNN xxcc"
        elif i == 3:
            if bits <= 8:
                return "xxxx xxNN xxcc"
            else:
                return "xxxx xxNN NNcc"
        if bits <= 8:
            return "xxxx xxxx NNcc"
        else:
            return "xxxx xxxx NNcc + NNxx xxxx xxcc"

    def __init__(self):
        self.items = [Fields.block(block) for block in range(1, 10)]
        
    def QtItemList(self, block, asbuilt, bitfields):
        qtitems = []
        prevbyte = -1
        for item in Fields.block(block):
            if prevbyte != item['byte']:
                layout = QHBoxLayout()
                label = QLabel()
                label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
                label.setText("7D0-%02X-%02X %s" % (block, (item['byte'] // 5) + 1, self.byte_loc_string(item['byte'] % 5, item['size'])))
                label.adjustSize()
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                layout.addWidget(label)
                layout.addWidget(line, stretch=1)
                qtitems.append(layout)
                prevbyte = item['byte']
            bitloc = asbuilt.start_bit(block) + ((item['byte']) * 8) + item['bit']
            layout = QHBoxLayout()
            label = QLabel(item['name'])
            option = QComboBox()
            unit = None
            value = asbuilt.bit(bitloc, item['size'])
            if item['type'] == 'mul':
                # inputfield
                value = (asbuilt.bit(bitloc, item['size']) * item['multiplier']) + item['offset']
                option = QLineEdit()
                option.setValidator(QDoubleValidator())
                option.setText("%.02f" % (value))
                option.setMaximumWidth(50)
                option.editingFinished.connect(partial(value_change, option, item, bitfields[item['byte']:item['byte']+2 if item['size'] > 8 else item['byte']+1]))
                unit = QLabel(item['unit'])
                unit.setMaximumWidth(50)
                unit.setMinimumWidth(50)
            elif item['type'] == 'mask':
                # combobox
                for x in range(0, item['items']):
                    option.addItem("" if '%d' % x not in item else item['%d' % x], x)
                option.setMaximumWidth(400)
                option.setCurrentIndex(value)
                #print(item['byte'])
                #print(bitfields)
                option.currentIndexChanged.connect(partial(combo_change, option, item, bitfields[item['byte']]))

            elif item['type'] == 'ascii':
                option = QLineEdit()
                option.setValidator(QRegExpValidator(QRegExp("[A-Z]")))
                option.setText("%s" % (chr(value)))
                option.editingFinished.connect(partial(ascii_change, option, item, bitfields[item['byte']]))
                option.setMaximumWidth(50)
            elif item['type'] == 'table':
                table = JumpTables.table(item['table'])
                for x in range(0, len(table)):
                    option.addItem(table[x], x)
                option.setMaximumWidth(400)
                option.setCurrentIndex(value)
                option.currentIndexChanged.connect(partial(combo_change, option, item, bitfields[item['byte']]))
            layout.addWidget(label)
            layout.addWidget(option)
            if unit is not None:
                layout.addWidget(unit)
            option.abitem = item
            qtitems.append(layout)
            
            
        return qtitems

    def format_all(self, ab1, ab2):
        if ab2 is not None and len(ab1) < len(ab2):
            ab3 = ab1
            ab1 = ab2
            ab2 = ab3

        string = ""
        for block in range(1, len(ab1.blocks) + 1):
            string = string + self.format(block, ab1, ab2)

        return string

    def format(self, block, ab1, ab2):
        if not ab1.hasblock(block) or (ab2 is not None and not ab2.hasblock(block)):
            return "Block %d not present in %s\n" % (block, "%s and %s" % (ab1.filename, ab2.filename) if not ab1.hasblock(block) and ab2 is not None and not ab2.hasblock(block) else ab1.filename if not ab1.hasblock(block) else ab2.filename)
        string = "Block %d (7D0-%02X or DE%02X)\n" % (block, block, block - 1)
        if block in [1, 2, 3, 4, 6, 8, 9]:
            string = string + "#%s%-96s  - Field     Loc Byte     Loc bit  Val1 %s\n" % ("   - bit - loc - " if DEBUG else "", "Name", "Val2" if ab2 is not None else "")
        else:
            string = string + "Block contains multiplier/offset values:\n"

        # Parking Assistance: ................................................................................ 7D0-04-02 nnXX nnnn nn 01 & FF = 01
        # Front Track                                     7D0-05-01 XXXX nnnn nn 169B & FFFF = 169B     169B5.8 In (14.7    cm)                 Min: 0.0Max: 655.4
        try:
            for item in self.items[block-1]:
                bitloc = ab1.start_bit(block) + ((item['byte']) * 8) + item['bit']
                mask = ((2**item['size'])-1) << (((7 - item['bit']) - (item['size'] - 1)) % 8)
                value1 = ab1.bit(bitloc, item['size'])
                value2 = ab2.bit(bitloc, item['size']) if ab2 is not None else None
                byte1 = ab1.int(ab1.start_byte(block) + item['byte'], 1 + ab1.start_byte(block) + item['byte'] + (item['size'] // 8) if item['size'] % 8 != 0 else ab1.start_byte(block) + item['byte'] + (item['size'] // 8))
                byte2 = ab2.int(ab1.start_byte(block) + item['byte'], 1 + ab1.start_byte(block) + item['byte'] + (item['size'] // 8) if item['size'] % 8 != 0 else ab1.start_byte(block) + item['byte'] + (item['size'] // 8)) if ab2 is not None else None

                if mask < 256:
                    bitmask = "{:.>8b}".format(mask)
                    bitmask = bitmask.replace("0", ".")
                    bitmask = bitmask[:bitmask.find("1")] + ("{:0%db}" % bitmask.count("1")).format(value1) + bitmask[bitmask.find("1")+bitmask.count("1"):]
                else:
                    bitmask = "too big "
                if item['type'] == 'mul':
                    # multiplier type
                    value1 = (ab1.bit(bitloc, item['size']) * item['multiplier']) + item['offset']
                    value2 = (ab2.bit(bitloc, item['size']) * item['multiplier']) + item['offset'] if ab2 is not None else None
                    string = string + "%s%-48s%-44s\t%s%s\t%-16s%-16s\tMin: %0.1f\tMax: %0.1f\n" %(
                        "%-3s - " % item['index'] if DEBUG else "",
                        item['name'],
                        ab1.mask_string(bitloc, bitloc + item['size']),
                        "%04X" % byte1,
                        " vs %04X" % byte2 if byte2 is not None else "",
                        "%0.1f %s%s" % (value1, item['unit'] if item['unit'] is not 'unitless' else "", " (%0.1f cm)" % (value1 * 2.54) if item['unit'] == "In" else ""),
                        " vs %0.1f %s%s" % (value2, item['unit'] if item['unit'] is not 'unitless' else "", " (%0.1f cm)" % (value2 * 2.54) if item['unit'] == "In" else "") if value2 is not None else "",
                        item['min'],
                        item['max']
                    )
                elif item['type'] == 'mask':
                    # bitmask typebit = 7 - item['bit']
                    string = string + "%s%-s: %s %s %s %s\n" % (
                                "%-4s- %-3s - %-3s\t " % (item['index'], item['size'], bitloc) if DEBUG else "",
                                item['name'],
                                "." * (98 - len(item['name'])),
                                ab1.mask_string(bitloc, bitloc + item['size']),
                                bitmask,
                                "%02X" % byte1 if ab2 is None else " %02X   %02X" % (byte1, byte2)
                                #"vs %02X & %02X = %02X" % (value2, mask, value2 & mask) if value2 is not None else ""
                            )
                    # for now assume enable // disable if one bit or multi bit strategy
                    for x in range(0, item['items']):
                        string = string + "%s     %2s %2s %s:\t%s\n" % ("\t\t" if DEBUG else "",
                                ">>" if ab2 is None and x == value1 else "1>" if x == value1 else "",
                                "2>" if ab2 is not None and x == value2 else "",
                                "%02X" % x,
                                "" if '%d' % x not in item else item['%d' % x]
                                )
                elif item['type'] == 'ascii':
                    letterstring = " %02X: %s %s" % (value1, chr(value1), "vs %02X: %s" % (value2, chr(value2)) if value2 is not None else "")
                    string = string + "%s%-s: %s %s %s\n" % ("%-4s- %-3s - %-3s\t " % (item['index'], item['size'], bitloc) if DEBUG else "",
                                item['name'],
                                letterstring + "." * (98 - len(item['name']) - len(letterstring)),
                                ab1.mask_string(bitloc, bitloc + item['size']),
                                "vs %02X & %02X = %02X" % (value2, mask, value2 & mask) if value2 is not None else ""
                            )
                elif item['type'] == 'table':
                    string = string + "%s%-s: %s %s %s %s\n" % ("%-4s- %-3s - %-3s\t " % (item['index'], item['size'], bitloc) if DEBUG else "",
                                item['name'],
                                "." * (98 - len(item['name'])),
                                ab1.mask_string(bitloc, bitloc + item['size']),
                                bitmask,
                                "%02X" % byte1 if ab2 is None else " %02X   %02X" % (byte1, byte2)
                                #"vs %02X & %02X = %02X" % (value2, mask, value2 & mask) if value2 is not None else ""
                            )
                    # for now assume enable // disable if one bit or multi bit strategy
                    table = JumpTables.table(item['table'])
                    for x in range(0, len(table)):
                        string = string + "%s     %2s %2s %s:\t%s\n" % ("\t\t" if DEBUG else "",
                                ">>" if ab2 is None and x == value1 else "1>" if x == value1 else "",
                                "2>" if ab2 is not None and x == value2 else "",
                                "%02X" % x,
                                "" if len(table) < x not in item else table[x]
                                )
                    # table type
                    pass
        except Exception as e:
            print(item)
            print(block)
            raise e
        return string + "\n"


def print_bits_known_de07_08():
    de7 = [0] * (10*8)
    de8 = [0] * (20*8)

    for i in Fields.de07:
        if i['size'] == 1:
            de7[(i['byte'] * 8) + i['bit']] = 1
        else:
            x = (i['byte'] * 8) + i['bit']
            de7 = de7[:x] + [1] * i['size'] + de7[x+i['size']:]
    c = 0
    print("Known bits in DE07 // 7D0-08-xx")
    for x in de7:
        if c % 8 == 0 and c > 0:
            print(" ", end="")
        if c % 40 == 0 and c > 0:
            print("")
        print("%d"%x, end="")
        c += 1
    print("")

    print("Known bits in DE08 // 7D0-09-xx")
    for i in Fields.de08:
        if i['size'] == 1:
            loc = ((i['byte']) * 8) + i['bit']
            if de8[loc] == 1:
                print("duplicate: ", i['index'])
            de8[loc] = 1
        else:
            x = ((i['byte']) * 8) + i['bit']
            if de8[x] == 1:
                print("duplicate: %d", i['index'])
            de8 = de8[:x] + [1] * i['size'] + de8[x+i['size']:]
    c = 0
    for x in de8:
        if c % 8 == 0 and c > 0:
            print(" ", end="")
        if c % 40 == 0 and c > 0:
            print("")
        print("%d"%x, end="")
        c += 1
    print("")

def print_duplicates():
    indexes = []
    for i in range(1, 10):
        block = Fields.block(i)
        for item in block:
            if item['index'] in indexes:
                print("Duplicate: %d", item['index'])
            else:
                indexes.append(item['index'])
