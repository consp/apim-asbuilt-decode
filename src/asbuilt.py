from binascii import unhexlify, hexlify

import xml.etree.ElementTree as ET
import struct

class AsBuilt(object):
    fieldsizes_s1 = [8, 6, 5]
    fieldsizes_s3 = [10, 12, 5, 7, 6, 1, 16, 10, 20, 20]
    fieldsizes_s4 = [20, 15, 15, 5, 15, 6, 16, 10, 25, 25]
    blocks = [] # 3.2 and up and later 3.0 models have 8, 9 for 3.4 from late 2019 and my20
    filename = ""

    sync_version = 0
    s4 = False
    fieldsizes = None

    def __init__(self, filename):
        bits = ""
        print("Loading", filename)
        if filename.lower().endswith(".abt"):
            # file from ForScan
            print("Forscan ABT format")
            with open(filename, "r") as f:
                data = f.read()
                if "G" in data:
                    print("New forscan format")
                data.replace("G", "0") # fix new format
                data = data.split("\n")
            bits = ""
            for line in data:
                if len(line) == 0 or line[0] == ";":
                    continue
                bits = bits + line[7:-2]
        elif filename.lower().endswith(".ab"):
            print("Loading Ford XML file")
            # ab file from motorcraft site / ford
            tree = ET.parse(filename)
            root = tree.getroot()
            data = root.find(".//BCE_MODULE")
            for child in list(data):
                block = child.attrib['LABEL']
                if block.startswith('7D0'):
                    #b = int(block[4:6], 16)
                    for code in child.findall(".//CODE"):
                        if code.text is not None:
                            bits = bits + code.text
                    bits = bits[:-2]
        elif filename.lower().endswith(".xml"):
            print("Loading UCDS Direct configuration XML file")
            # ab file from motorcraft site / ford
            tree = ET.parse(filename)
            root = tree.getroot()
            data = root.find(".//VEHICLE")
            for child in list(data):
                block = child.attrib['ID']
                if block.startswith('DE'):
                    bits = bits + child.text
        else:
            raise ValueError("File type not supported")
        self.filename = filename
        # detect actual length
        length = len(unhexlify(bits.encode()))
        # detect s4
        s1_len = [sum(self.fieldsizes_s1[0:i]) for i in range(1, len(self.fieldsizes_s1) + 1)]
        s3_len = [sum(self.fieldsizes_s3[0:i]) for i in range(1, len(self.fieldsizes_s3) + 1)]
        s4_len = [sum(self.fieldsizes_s4[0:i]) for i in range(1, len(self.fieldsizes_s4) + 1)]
        print(s4_len)
        if length in s1_len and length not in s3_len and length not in s4_len:
            self.s4 = False
            self.fieldsizes = self.fieldsizes_s1
            self.sync_version = 1
        elif length in s3_len and length not in s1_len and length not in s4_len:
            self.s4 = False
            self.fieldsizes = self.fieldsizes_s3
            self.sync_version = 3
        elif length in s4_len and length not in s1_len and length not in s3_len:
            self.s4 = True
            self.fieldsizes = self.fieldsizes_s4
            self.sync_version = 4
        else:
            print("Unknown sync version or block count: %d bytes detected" % length)

        print("Device is Sync %d" % self.sync_version)
        if self.sync_version < 3:
            print("Sync %d is unfortunately not supported" % self.sync_version)
        else:
            self.decode_bytes(unhexlify(bits.encode()))
            print("Loaded %d blocks, %d bytes" % (len(self.blocks), len(bytes(self))))


    def decode_bytes(self, data):
        if len(self.blocks) > 0:
            self.blocks = []
        i = 0

        while len(data) > 0:
            try:
                if self.s4:
                    self.blocks.append(data[:self.fieldsizes_s4[i]])
                    data = data[self.fieldsizes_s4[i]:]
                else:
                    self.blocks.append(data[:self.fieldsizes_s4[i]])
                    data = data[self.fieldsizes[i]:]
                i += 1
            except:
                print(len(data))
                print(hexlify(data).decode())
                print(i)
                if self.s4:
                    print(self.fieldsizes_s4[i])
                else:
                    print(self.fieldsizes[i])

    def checksum(self, major, minor):
        return (0x07 + 0xD0 + major + minor + sum(self.blocks[major - 1][(minor-1) * 5:minor * 5])) & 0x00FF

    def save(self):
        string = "; Created with apim.py, https://github.com/consp/apim-asbuilt-decode\n"
        for x in range(1, self.block_size() + 1):
            # 7D0G5G1169B1674263E
            string = string + "; Block %d \n" % (x)
            for z in range(0, len(self.blocks[x - 1]),5):
                string = string + "7D0G%dG%d" % (x, (z // 5) + 1)
                for d in self.blocks[x - 1][z:z+5]:
                    string = string + "%02X" % (d)
                string = string + "%02X" % (self.checksum(x, (z // 5) + 1)) + "\n"
        return string

    def byte(self, byte):
        if byte > sum(self.fieldsizes) or byte > (self.size() // 8) - 1:
            return None
        return bytes(self)[byte]

    def bytes(self, start, stop):
        return bytes(self)[start // 8:((stop-1) // 8)+1]

    def word(self, index):
        if index+1 > sum(self.fieldsizes):
            return None
        return ((bytes(self)[index]) << 8) + (bytes(self)[index+1])

    def int(self, start, end):
        if end > sum(self.fieldsizes):
            return None
        return int(hexlify(bytes(self)[start:end]), 16)

    def size(self):
        return len(bytes(self) * 8)

    def bit(self, start, stop=-1):
        if stop == -1:
            stop = start + 1
        else:
            stop = start + stop
        if start > self.size():
            return -1
        bitdata = "".join([format(x, "08b")  for x in bytes(self)])
        return int(bitdata[start:stop], 2)

    def start_byte(self, block):
        return sum(self.fieldsizes[:block-1]) if len(self.blocks) >= block else 0 if block <= 0 else -1

    def start_bit(self, block):
        return self.start_byte(block) * 8

    def block(self, block):
        return self.blocks[block]

    def block_size(self):
        return len(self.blocks)

    def hasblock(self, block):
        return block <= len(self.blocks)

    def mask_string(self, start, stop, values=False):
        i = 1
        value = int.from_bytes(self.bytes(start, stop), byteorder="big")
        for f in self.fieldsizes:
            if f * 8 > start:
                break
            start -= f * 8
            stop -= f * 8
            i += 1
        l = (start // 40) + 1
        string = ""
        cnt = 0
        fin = 40
        string = string + "7D0-%02X-%02X"% (i, l)
        for n in range((start // 40) * 40, stop, 40):
            string = string + " -" if cnt > 0 else string
            y = start % 40
            z = stop % 40
            if (stop > n and z < y and cnt == 0) or stop % 40 == 0:
                z = 40
            if y > z and cnt > 0:
                y = 0
            if cnt > 0:
                fin = z
            #string = string + " %d %d %d " % (z, y, fin)
            for x in range(0, y - (y % 4), 4):
                if x % 16 == 0:
                    string = string + " "
                string = string + "n"
            for x in range(y - (y % 4), (z + (4 - (z % 4))), 4):
                if x % 16 == 0:
                    string = string + " "
                if x == z and z != fin:
                    string = string + "n"
                    continue
                if x != fin:
                    string = string + "X"
            for x in range(max(z + (4 - (z % 4)), y), fin, 4):
                if x % 16 == 0:
                    string = string + " "
                string = string + "n"
            l += 1
            cnt += 1
        mask = ((2**(stop - start)) - 1) << (7-((stop-1) % 8))
        string = string + " %02X & %02X = %02X" % (value, mask, value & mask) if values else string

        return string

    def __len__(self):
        return len(bytes(self))

    def __bytes__(self):
        return b"".join(self.blocks)

    def __str__(self):
        string = ""
        major = 0
        for item in self.blocks:
            major += 1
            minor = 0
            for block in [item[x:x+5] for x in range(0, len(item), 5)]:
                minor += 1
                string = string + "7D0-%02X-%02X " % (major, minor)
                for field in [block[x:x+2] if x < 4 else block[x:x+1] for x in range(0, len(block), 2) if x < 5]:
                     string = string + "%02X%02X " % (field[0], field[1]) if len(field) > 1 else string + "%02X" % field[0]
                string = string + "%02X\n" % self.checksum(major, minor)
        return string
