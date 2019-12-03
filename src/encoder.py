from statics import JumpTables, Fields
from asbuilt import AsBuilt

import struct
class HmiData(object):
    data = None
    items = [] # block 0-3
    high_items = [] # block 5-7
    index_locations_high = [ # offset to DE04, includes DE05 and DE06 (7D0-05-07), format [byte start, byte end, bitvalue (first bit is 1)]
        [0, 2], [2, 2], [4, 2], [6, 1, 1], [6, 1, 2], [7, 1], [8, 1], [9, 1], [10, 1], [11, 1], [12, 2], [14, 2], [16, 2], [18, 1], [19, 1], [20, 1], [21, 2]
    ]


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
        return (self.items[index]['items'] - 1).bit_length()

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
        string = "#   -bits-loc  - %-96s   - Field      Location     Msk&Val = Res\n" % ("Name")
        if ab1.start_byte(8) == -1 and ab2.start_byte(8) == -1 or ab1.start_byte(8) == -1:
            return string
        for item in Fields.de07:
            bit = 7 - item['bit']
            bitloc = ab1.start_bit(8) + ((item['byte']) * 8) + bit
            value1 = ab1.bit(bitloc, item['size'].bit_length())
            value2 = ab2.bit(bitloc, item['size'].bit_length()) if ab2 is not None else None
            byte1 = ab1.byte(ab1.start_byte(8) + item['byte'])
            byte2 = ab2.byte(ab1.start_byte(8) + item['byte']) if ab2 is not None else None
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




def print_bits_known_de07_08():
    items = Fields()
    de7 = [0] * (10*8)
    de8 = [0] * (20*8)

    for i in items.items_de07:
        if i['size'] == 1:
            de7[(i['byte'] * 8) + 7 - i['bit']] = 1
        else:
            x = (i['byte'] * 8) + 7 - i['bit']
            de7 = de7[:x] + [1] * i['size'].bit_length() + de7[x+i['size'].bit_length():]
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
    for i in items.items_de08:
        if i['size'] == 1:
            loc = ((i['byte']) * 8) + 7 - i['bit']
            if de8[loc] == 1:
                print("duplicate: ", i['index'])
            de8[loc] = 1
        else:
            x = ((i['byte']) * 8) + 7 - i['bit']
            if de8[x] == 1:
                print("duplicate: %d", i['index'])
            de8 = de8[:x - i['size'].bit_length() + 1] + [1] * i['size'].bit_length() + de8[x+1:]
    c = 0
    for x in de8:
        if c % 8 == 0 and c > 0:
            print(" ", end="")
        if c % 40 == 0 and c > 0:
            print("")
        print("%d"%x, end="")
        c += 1
    print("")

