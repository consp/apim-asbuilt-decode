from binascii import unhexlify, hexlify
import xml.etree.ElementTree as ET

import sys
import argparse
import array
import struct



# fields size

class JumpTables(object):
    BVNI = [
            "SYNC",
            "Ford Fiesta",
            "Ford Focus",
            "Ford Fusion",
            "Ford C-Max",
            "Ford Taurus",
            "Ford Mustang",
            "Ford Ecosport",
            "Ford Escape",
            "Ford Edge",
            "Ford Flex",
            "Ford Explorer",
            "Foprd Expedition",
            "Ford Ranger",
            "Ford F150",
            "Ford F250",
            "Ford F350",
            "Ford F450",
            "Ford F550",
            "Ford Transit Connect",
            "Ford Transit",
            "Ford E150",
            "Ford E250",
            "Ford E650",
            "Ford E750",
            "Lincoln MKZ",
            "Lincoln MKX",
            "Lincoln MKC",
            "Lincoln MKS",
            "Lincoln MKT",
            "Lincoln Navigator",
            "Ford Ka",
            "Ford Transit Courier",
            "Ford B-Max",
            "Ford Grand C-Max",
            "Ford Mondeo",
            "Ford Kuga",
            "Ford S-Max",
            "Ford Galaxy",
            "Ford Figo",
            "Ford Escort",
            "Ford Falcon",
            "Ford Everest",
            "Ford Terrirory",
            "Ford Raptor",
    ]

    _WDC = []

    _SS = [ # case splashscreen, no lookup table present in program
            "Unknown",
            "Unknown",
            "Unknown",
            "Unknown",
            "Lincoln Black",
            "Lincoln Presidential",
            "Mustang",
            "GT350",
            "Vignale",
            "GT350",
            "Unknown",
            "Ford Performance ST",
            "Ford Performance RS",
            "Ford Performance GT",
            "Continental",
            ]

    _VS = [
            "Undefined",
            "Sedan",
            "Coupe/Convertable",
            "Pickup Truck",
            "SUV/CUV",
            "VAN",
            "Hatchback"
            ]

    _DT = [
            "FWD",
            "RWD",
            "AWD",
            "4WD",
            "Dually 2WD",
            "Dually 4WD",
            "Reserved",
            "Reserved"
            ]
    _AP = [
            "No media",
            "CD/MP3",
            "CD Changer MP3",
            "DVD MP3",
            "CD Harddrive",
            "Reserved",
            "Reserved",
            "Reserved"
            ]

    __GpsPatchType = [
            "Harada",
            "Laird",
            "reserved",
            ]

    _C = [ # case climate
            "Enable Climate Control Repeater for Dual Climate Control",
            "Disable Climate Control Repeater",
            "Enable Climate Control Repeater for Single Climate Control",
            "Disable Climate Control Repeater",
            "E8"
            ]

    _PA = [ # case Parkin_assistance
            "No PDC/PSM/SAPP (Non or Configuration C5)",
            "Rear PDC (Configuration C1 or C3)",
            "Rear/Front PDC (Configuration C6 or C7)",
            "Rear/Front PDC/SAPP (Configuration C2 or C4) (NA HMI)",
            "Rear/SAPP (NA HMI)",
            "Rear/Front PDC/SAPP (Configuration C2 or C4) (EU HMI)",
            "Rear/SAPP (EU HMI)",
            "Rear/Front PDC with APA",
            "APA Lite",
            "APA Lite Plus (SAPP/POA - 10 Channel)",
            "Unknkown / Reserved"
            ]
    _BPT = [ # case bluetooth pairing timeout
            "?"
            ]

    _V = [ # case vehicle type
            "Non HEV, BEV, PHEV",
            "C344",
            "C346",
            "CD391",
            "CD533",
            ]

    _VDV = [ # case visual design variant
            "Ford Classic",
            "Ford Timeless",
            "Lincoln Timeless",
            "Lincoln Next",
            ]

    _KC = [ # case KEY combination
            "Volume Down + F1",
            "Volume Down + Home",
            "SWC Down Volume + Center Previous Track",
            "Volume Down + Right OK",
            ]

    BAPI = [ # Bluetooth audi profile index
            "Profile %d"
            ]
    _AFL = [ # Electronic horizon"
            "Electronic Horizon Off",
            "Electronic Horizon for Informational Use Only",
            "Electronic Horizon for Non Active + Curve/Slope",
            "Electronic Horizon for Active (less Curve/Slope)",
            "Electronic Horizon for Active (with Curve/Slope)",
            ]


class AsBuilt(object):
    fieldsizes = [10, 12, 5, 7, 6, 1, 16, 10, 20]
    blocks = [] # 3.2 and up and later 3.0 models have 8, 9 for 3.4 from late 2019 and my20
    filename = ""

    def __init__(self, filename):
        bits = ""
        print("Loading", filename)
        if filename.endswith(".abt"):
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
        elif filename.endswith(".ab"):
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
        else:
            raise ValueError("File type not supported")
        self.filename = filename
        self.decode_bytes(unhexlify(bits.encode()))
        print("Loaded %d blocks, %d bytes" % (len(self.blocks), len(bytes(self))))


    def decode_bytes(self, data):
        if len(self.blocks) > 0:
            self.blocks = []
        i = 0

        while len(data) > 0:
            try:
                self.blocks.append(data[:self.fieldsizes[i]])
                data = data[self.fieldsizes[i]:]
                i += 1
            except:
                print(len(data))
                print(i)
                print(self.fieldsizes[i])

    def checksum(self, major, minor):
        return (0x07 + 0xD0 + major + minor + sum(self.blocks[major - 1][(minor-1) * 5:minor * 5])) & 0x00FF

    def byte(self, byte):
        if byte > sum(self.fieldsizes) or byte > (self.size() // 8) - 1:
            return None
        return bytes(self)[byte]

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
        return sum(self.fieldsizes[:block-1]) if len(self.blocks) >= block else -1

    def start_bit(self, block):
        return self.start_byte(block) * 8

    def block(self, block):
        return self.blocks[block]

    def mask_string(self, start, stop):
        i = 1
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
        for n in range((start // 40) * 40, stop, 40):
            string = string + " -" if cnt > 0 else string
            string = string + "7D0-%02X-%02X // 0x%-6s" % (i, l, "%02X" % (((2**(stop - start)) - 1) << (7-((stop-1) % 8)))) if cnt == 0 else string
            y = start % 40
            z = stop % 40
            if z > n and z < start % 40:
                z = 39
            if y > z:
                y = 0
            if cnt > 0:
                fin = z
            for x in range(0, y - (y % 4), 4):
                if x % 16 == 0:
                    string = string + " "
                string = string + "n"
            for x in range(y - (y % 4), (z + (4 - (z % 4))), 4):
                if x % 16 == 0:
                    string = string + " "
                if x == z and z != fin:
                    string = string + "n"
                    break
                if x != fin:
                    string = string + "X"
            for x in range(z + (4 - (z % 4)), fin, 4):
                if x % 16 == 0:
                    string = string + " "
                string = string + "n"
            l += 1
            cnt += 1


        return string



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


class HmiData(object):
    data = None
    items = []
    high_items = [] # block 7
    index_locations_high = [ # offset to DE04, includes DE05 and DE06 (7D0-05-07), format [byte start, byte end, bitvalue (first bit is 1)]
        [0, 2], [2, 2], [4, 2], [6, 1, 1], [6, 1, 2], [7, 1], [8, 1], [9, 1], [10, 1], [11, 1], [12, 2], [14, 2], [16, 2], [18, 1], [19, 1], [20, 1], [21, 2]
    ]

    items_unknown = [
        {     'name': 'Unknown item 133, has to be bigger than 5 items on list so 3 bits',
            'index': 133,
            'byte': 0,
            'bit': 0,
            'size': 7,
            'items': 0,
        },
    ]

    items_de07 = [ # indexes do not match a paticular order but instead a internal system, index change with changes in the settings so ... it's a guess but somewhat accurate as they stay in the same order
        {     'name': 'LANE_CHANGE_INDICATOR',
            'index': 169,
            'byte': 0,
            'bit': 6,
            'size': 1,
            'items': 0,
        },
        {     'name': 'VS_CAL_SVC_IF_MESSAGE_SET CAN Legacy/New status (might be incorrect bit/byte)',
            'index': 181,
            'byte': 0,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
        {     'name': 'CCS config',
            'index': 183,
            'byte': 2,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
        {     'name': 'VS_CAL_SVC_IF_B479_STRATEGY',
            'index': 184,
            'byte': 0,
            'bit': 3, # not sure!
            'size': 7,
            'items': 0,
        },
        {     'name': 'APACSI_SIGNAL_STRATEGY ',
            'index': 188,
            'byte': 7,
            'bit': 4, # not sure!
            'size': 3,
            'items': 0,
        },
        {     'name': 'VS_CAL_SVC_IF_ICONS',
            'index': 197,
            'byte': 3,
            'bit': 7,
            'size': 1,
            'items': 0,
        },
        {     'name': 'VS_CAL_SVC_IF_HAS_PARKING_HOTKEY',
            'index': 203,
            'byte': 6,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTO_HOLD',
            'index': 208,
            'byte': 4,
            'bit': 3,
            'size': 1,
            'items': 0,
        },
        {     'name': 'REVERSE_BRAKING_ASSIST',
            'index': 209,
            'byte': 2,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
    ]

    items_de08 = [
        {     'name': 'TIRE_PRESSURE_UNIT Support',
            'index': 217,
            'byte': 9,
            'bit': 2,
            'size': 1,
            'items': 0,
        },
        {     'name': 'TIRE_MOBILITY_KIT Support note, bit is possibly wrong could be 0, or 4',
            'index': 218,
            'byte': 9,
            'bit': 0, # ?
            'size': 1,
            'items': 0,
        },
        {     'name': 'TPMS_DISPLAY_UNIT',
            'index': 219,
            'byte': 9,
            'bit': 1,
            'size': 1,
            'items': 0,
        },
        {     'name': 'TRACTION_CONTROL',
            'index': 220,
            'byte': 7,
            'bit': 2,
            'size': 3,
            'items': 0,
        },
        {     'name': 'DO NOT DISTURB',
            'index': 221,
            'byte': 3,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'SEAT_ADJUSTMENT',
            'index': 222,
            'byte': 2,
            'bit': 7,
            'size': 1,
            'items': 0,
        },
        {     'name': 'SILENT_MODE',
            'index': 223,
            'byte': 5,
            'bit': 4,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AlarmSystem',
            'index': 224,
            'byte': 3,
            'bit': 2,
            'size': 1,
            'items': 0,
        },
        {     'name': 'Remote Start',
            'index': 225,
            'byte': 4,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUX_HEATER',
            'index': 226,
            'byte': 2,
            'bit': 4,
            'size': 1,
            'items': 0,
        },
        {     'name': 'Park Heater',
            'index': 227,
            'byte': 3,
            'bit': 4,
            'size': 1,
            'items': 0,
        },
        {     'name': 'GLOBAL_WINDOW_OPEN',
            'index': 228,
            'byte': 2,
            'bit': 3,
            'size': 1,
            'items': 0,
        },
        {     'name': 'GLOBAL_WINDOW_CLOSE',
            'index': 229,
            'byte': 2,
            'bit': 2,
            'size': 1,
            'items': 0,
        },
        {     'name': 'COURTESY_WIPER',
            'index': 230,
            'byte': 1,
            'bit': 1,
            'size': 1,
            'items': 0,
        },
        {     'name': 'REAR_REVERSE_GEAR_WIPE',
            'index': 231,
            'byte': 3,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
        {     'name': 'Power LiftGate',
            'index': 232,
            'byte': 3,
            'bit': 1,
            'size': 1,
            'items': 0,
        },
        {     'name': 'Auto High Beam',
            'index': 233,
            'byte': 0,
            'bit': 1,
            'size': 1,
            'items': 0,
        },
        {     'name': 'DAYTIME_RUNNING_LIGHTS',
            'index': 234,
            'byte': 2,
            'bit': 1,
            'size': 1,
            'items': 0,
        },
        {     'name': 'ADAPTIVE_HEADLAMPS_SUPPORT',
            'index': 235,
            'byte': 0,
            'bit': 4,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTOLAMP_DELAY',
            'index': 236,
            'byte': 0,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
        {     'name': 'WELCOME_LIGHTING_DETECT',
            'index': 237,
            'byte': 1,
            'bit': 2,
            'size': 1,
            'items': 0,
        },
        {     'name': 'REMOTE_UNLOCK',
            'index': 238,
            'byte': 3,
            'bit': 3,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTO_FOLD_MIRRORS',
            'index': 239,
            'byte': 3,
            'bit': 7,
            'size': 1,
            'items': 0,
        },
        {     'name': 'REVERSE_TILT_MIRRORS',
            'index': 240,
            'byte': 3,
            'bit': 6,
            'size': 1,
            'items': 0,
        },
        {     'name': 'POWER_RUNNING_BOARD',
            'index': 241,
            'byte': 8,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTO_ENGINE_OFF_WithOutOverRide',
            'index': 242,
            'byte': 0,
            'bit': 7,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTO_ENGINE_OFF_WithOverRide',
            'index': 243,
            'byte': 0,
            'bit': 6,
            'size': 1,
            'items': 0,
        },
        {     'name': 'PARK_LOCK_CONTROL',
            'index': 244,
            'byte': 9,
            'bit': 6,
            'size': 3,
            'items': 0,
        },
        {     'name': 'REMOTE_START_DriverSeat',
            'index': 245,
            'byte': 4,
            'bit': 6,
            'size': 1,
            'items': 0,
        },
        {     'name': 'REMOTE_START Steering Wheel',
            'index': 246,
            'byte': 4,
            'bit': 2,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTO_LOCK',
            'index': 247,
            'byte': 1,
            'bit': 7,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTO_UNLOCK',
            'index': 248,
            'byte': 1,
            'bit': 4,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTO_RELOCK',
            'index': 249,
            'byte': 1,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUDIBLE_LOCKING_FEEDBACK',
            'index': 250,
            'byte': 6,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'EXTERIOR_LIGHTS_FEEDBACK',
            'index': 251,
            'byte': 6,
            'bit': 4,
            'size': 1,
            'items': 0,
        },
        {     'name': 'ADAPTIVE_HEADLAMPS_SETUP_SUPPORT',
            'index': 252,
            'byte': 1,
            'bit': 6,
            'size': 1,
            'items': 0,
        },
        {     'name': 'ACC_MENU',
            'index': 253,
            'byte': 0,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'ADAPTIVE_CRUISE_CONTROL',
            'index': 254,
            'byte': 7,
            'bit': 1,
            'size': 1,
            'items': 0,
        },
        {     'name': 'ADJUSTABLE_SPEED_LIMITER',
            'index': 255,
            'byte': 0,
            'bit': 3,
            'size': 1,
            'items': 0,
        },
        {     'name': 'INTELLIGENT_SPEED_ASSISTANCE',
            'index': 256,
            'byte': 4,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
        {     'name': 'PRE_COLLISION_ASSIST',
            'index': 257,
            'byte': 5,
            'bit': 6,
            'size': 1,
            'items': 0,
        },
        {     'name': 'TOW_HAUL',
            'index': 258,
            'byte': 8,
            'bit': 6,
            'size': 1,
            'items': 0,
        },

        {     'name': 'BLINDSPOT_DETECTION',
            'index': 259,
            'byte': 4,
            'bit': 1,
            'size': 1,
            'items': 0,
        },
        {     'name': 'TRAILER_BLINDSPOT_DETECTION',
            'index': 260,
            'byte': 8,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'WRONG_WAY_ALERT',
            'index': 261,
            'byte': 8,
            'bit': 4,
            'size': 1,
            'items': 0,
        },
        {     'name': 'TRACTION_CONTROL',
            'index': 262,
            'byte': 0,
            'bit': 2,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTO_START_STOP',
            'index': 263,
            'byte': 9,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'HILL_DECENT_CONTROL',
            'index': 264,
            'byte': 8,
            'bit': 3,
            'size': 1,
            'items': 0,
        },
        {     'name': 'DRIVER_ALERT',
            'index': 265,
            'byte': 1,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
        {     'name': 'TRAILER_SWAY',
            'index': 266,
            'byte': 5,
            'bit': 7,
            'size': 1,
            'items': 0,
        },

        {     'name': 'DISTANCE_INDICATION',
            'index': 267,
            'byte': 2,
            'bit': 5,
            'size': 3,
            'items': 0,
        },
        {     'name': 'TRAFFIC_SIGN_RECOGNITION',
            'index': 268,
            'byte': 9,
            'bit': 3,
            'size': 1,
            'items': 0,
        },
        {     'name': 'LANE_KEEPING_SENSITIVITY',
            'index': 269,
            'byte': 7,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'LANE_ASSIST_HAPTIC_INTENSITY',
            'index': 270,
            'byte': 6,
            'bit': 2,
            'size': 1,
            'items': 0,
        },
        {     'name': 'LANE_CHANGE_ASSIST',
            'index': 271,
            'byte': 7,
            'bit': 6,
            'size': 3,
            'items': 0,
        },
        {     'name': 'INTELLIGENT_CRUISE_CONTROL',
            'index': 272,
            'byte': 6,
            'bit': 1,
            'size': 1,
            'items': 0,
        },
        {     'name': 'PRE_COLLISION_ASSIST_ACTIVE_BRAKING',
            'index': 273,
            'byte': 6,
            'bit': 6,
            'size': 1,
            'items': 0,
        },
        {     'name': 'PRE_COLLISION_ASSIST_EVASIVE_STEERING',
            'index': 274,
            'byte': 6,
            'bit': 3,
            'size': 1,
            'items': 0,
        },
        {     'name': 'TRAFFIC_SIGN_RECOGNITION_TOLERANCE',
            'index': 275,
            'byte': 7,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
        {     'name': 'TRAFFIC_SIGN_RECOGNITION_OVERSPEED_CHIME',
            'index': 276,
            'byte': 8,
            'bit': 7,
            'size': 1,
            'items': 0,
        },
        {     'name': 'LANE_KEEPING_AID',
            'index': 277,
            'byte': 10,
            'bit': 5,
            'size': 3,
            'items': 0,
        },
        {     'name': 'LANE_KEEPING_ALERT',
            'index': 278,
            'byte': 10,
            'bit': 3,
            'size': 3,
            'items': 0,
        },
        {     'name': 'BTT_LITE',
            'index': 279,
            'byte': 11,
            'bit': 3,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AIR_SUSPENSION',
            'index': 280,
            'byte': 11,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'Auto High Beam Menu',
            'index': 281,
            'byte': 11,
            'bit': 6,
            'size': 3,
            'items': 0,
        },
        {     'name': 'GRADE_ASSIST',
            'index': 283,
            'byte': 10,
            'bit': 1,
            'size': 1,
            'items': 0,
        },
        {     'name': 'ONE_TWO_STAGE_UNLOCK',
            'index': 284,
            'byte': 10,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTO_HEIGHT',
            'index': 285,
            'byte': 11,
            'bit': 4,
            'size': 1,
            'items': 0,
        },
        {     'name': 'CARGO_LOADING',
            'index': 286,
            'byte': 11,
            'bit': 0,
            'size': 1,
            'items': 0,
        },
        {     'name': 'PASSENGER_AIRBAG',
            'index': 287,
            'byte': 11,
            'bit': 2,
            'size': 1,
            'items': 0,
        },
        {     'name': 'KEY_FREE',
            'index': 288,
            'byte': 10,
            'bit': 2,
            'size': 1,
            'items': 0,
        },
        {     'name': 'INTELLIGENT_ACCESS',
            'index': 289,
            'byte': 5,
            'bit': 5,
            'size': 1,
            'items': 0,
        },
        {     'name': 'PREDICTIVE_LIGHTING_SUPPORT',
            'index': 290,
            'byte': 10,
            'bit': 7,
            'size': 1,
            'items': 0,
        },
        {     'name': 'AUTO_START_STOP_SPEED_THRESHOLD',
            'index': 291,
            'byte': 11,
            'bit': 1,
            'size': 1,
            'items': 0,
        },
        {     'name': 'VS_CAL_SVC_IF_SYNC_HELP',
            'index': 294,
            'byte': 19,
            'bit': 4,
            'size': 1,
            'items': 0,
        },
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

        string = ""

        for i in range(self.size()):
            string = string + "%-03s - %-02d - %-d  %-s %-s %-s // 0x%02X %s\n" % (
                self.index(i)+1,
                self.bits(i),
                self.bit(i),
                self.name(i),
                "." * (98 - len(self.name(i))),
                self.calc_field(ab1, i),
                ab1.byte(self.byte(i)),
                "" if ab2 is None else "0x%02X" % ab2.byte(self.byte(i))
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
        string = ""
        if ab1.start_byte(8) == -1 and ab2 is None or ab1.start_byte(8) == -1 and ab2.start_byte(8) == -1:
            return string
        for item in self.items_de07:
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
        string = ""
        if ab1.start_byte(9) == -1 and ab2 is None or ab1.start_byte(9) == -1 and ab2.start_byte(9) == -1:
            return string
        for item in self.items_de08:
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""These are the options from the options list in the HMI_AL code. Most of them I verified in code (e.g. by studieing the related log messages by decompiling the file). They match the inputs for de DE00-DE03 (7D0-01-xx to 7D0-03-xx).

Options are bit fields. So if the item as 4 options, the bitmask is 0x3, and 0x7 for 8. Most items are boolean (e.g. 0 disabled, 1 enabled)

Option 1-133 are bitfields
Option 134 and up (DE04-DE06, 7D0-05 to 7D0-07) are either lookup tables or offset/value calculation based on values in the calibration files"
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

    items = HmiData(args.hmifile)

    asbuilt1 = AsBuilt(abtfile[0]) if abtfile is not None else None
    asbuilt2 = AsBuilt(abtfile[1]) if len(abtfile) > 1 else None
    if asbuilt1 is not None and len(abtfile) > 0 and not debug:

        if not args.noprint:
            try:
                print(items.format(asbuilt1, asbuilt2))
            except Exception as e:
                print(asbuilt1.filename, asbuilt1.blocks)
                raise

    if debug:
        print_bits_known_de07_08()
        print(asbuilt1.filename, str(asbuilt1), sep="\n") if asbuilt1 is not None else ""
        print(asbuilt2.filename, str(asbuilt2), sep="\n") if asbuilt2 is not None else ""


    if args.export_hmidata:
        with open(args.export_hmidata, "wb") as f:
            f.write(items.data)

