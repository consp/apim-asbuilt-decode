import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")
if sys.version_info[1] < 4:
    raise Exception("Must be using Python 3.4 or up")

# Specific imports
from binascii import unhexlify, hexlify

# local imports
from asbuilt import AsBuilt
from encoder import HmiData, print_bits_known_de07_08, ItemEncoder
from statics import JumpTables, Fields
# global imports
import argparse

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

    asbuilt1 = AsBuilt(abtfile[0]) if abtfile is not None else None
    asbuilt2 = AsBuilt(abtfile[1]) if len(abtfile) > 1 else None
    if asbuilt1 is not None and len(abtfile) > 0 and not debug:

        if not args.noprint:
            try:
                print(ItemEncoder().format_all(asbuilt1, asbuilt2))
            except Exception as e:
                print(asbuilt1.filename, asbuilt1.blocks)
                raise

    if debug:
        print_bits_known_de07_08()
        print(asbuilt1.filename, str(asbuilt1), sep="\n") if asbuilt1 is not None else ""
        print(asbuilt2.filename, str(asbuilt2), sep="\n") if asbuilt2 is not None else ""

