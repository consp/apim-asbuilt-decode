# Ford APIM Sync 3/4 AsBuilt decoder tool
## Current state
Latest "Stable" release version: [1.3](https://github.com/consp/apim-asbuilt-decode/releases)
## Intro
This repository is meant for users who want to edit their values of the AsBuilt data of the Ford Sync 3 APIM and do not have a tool which has all information built in. The data has been collected from code (extracting debug information from the QNX applications) and other peoples findings on fora.

Please note that some settings change quite a lot. Most radio and CGEA/C1MCA settings change quite a lot internally.

As with all DIY tools: YMMV and you do everything at your own risk. Changing stuff might brick your APIM, you have been warned!

## Acknowledgements
- F150Forum's Livinitup and F150chief for the Sync 3 ASBuild sheet and information about Sync 3.x which was not present in the source code (or at least not obvious).
- F150Forum's Livinitup for the Sync 4 config sheet


## Inconsistencies and known issues
- After opening some files or misformed file the application might crash, this has been mostly mitigated

## Features
- Dumps your abt binary data into something 'somewhat' readable
- Lets you compare files to figure out you prefered configuration
- Uses GUI to change options more easy and lets you see the results in the files if you change them.
- Being an offline tool so you can use it while doing stuff in your garage.

## Todo
- Finish Sync 4 support by adding 7D0-08/09/10

## Usage and requirements
Requires the following:
- Python 3.5 and up
- Qt5 libraries and PyQt5.
- Or: download the x64 windows executables which have everything built in, 32bit require meddeling with pyqt5 if you are unlucky.
- As built file(s) in either Ford XML format (.ab) or ForScan dump format (.abt) in new or old style or a UCDS xml file.

GUI: ```python3 src/apim.py``` or run the excutable. You can open a file, change stuff and save it
![open image](/img/open.png?raw=true)
![main menu](/img/main.png?raw=true)

Command line options: Either one or two files need to be present
```
> python3 src/apim.py YOURVINHERE.ab forscanfile.abt
Loading YOURVINHERE.ab
Loading Ford XML file
Loaded 7 blocks, 57 bytes
Loading forscanfile.abt
Forscan ABT format
New forscan format
Loaded 8 blocks, 67 bytes
Block 1 (7D0-01 or DE00)
#Name                                                                          - Field     Loc Byte     Loc bit  Val1 Val2
Smart DSP: ..................................................................... 7D0-01-01 Xnnn nnnn nn 1.......  88   08
        2> 00:  Do not log missing DSP Messages
     1>    80:  Enable, Log missing DSP Messages (When configured for Smart DSP and Lincoln then enable THX Deep Note)
AAM (Module is related to Smart DSP): .......................................... 7D0-01-01 Xnnn nnnn nn .0......  88   08
     1> 2> 00:  Do not log missing AAM messages
           40:  Enable, Log Missing AAM messages (Send speaker walkaround request to ACM)
SDARS: ......................................................................... 7D0-01-01 Xnnn nnnn nn ..0.....  88   08
     1> 2> 00:  Do not log missing SDARS (ACM) message
           20:  Enable, Log Missing SDARS (ACM) message
RSEM: .......................................................................... 7D0-01-01 Xnnn nnnn nn ...0....  88   08
     1> 2> 00:  Do not log missing RSEM messages
           10:  Enable, Log Missing RSEM messages
PDC HMI: ....................................................................... 7D0-01-01 nXnn nnnn nn ....1...  88   08
           00:  Off
     1> 2> 08:  On
Rear Camera: ................................................................... 7D0-01-01 nXnn nnnn nn .....00.  88   08
     1> 2> 00:  RVC Not Present
           02:  RVC Present
           04:  Reserved
           06:  Reserved
Illumination: .................................................................. 7D0-01-01 nXnn nnnn nn .......0  88   08
     1> 2> 00:  FNA Strategy
           01:  FoE Strategy
Extended Play: ................................................................. 7D0-01-01 nnXn nnnn nn 0.......  6A   68
     1> 2> 00:  On
           80:  Off 
...
```

Command line options:
```
usage: apim.py [-h] [--debug] [--noprint] [--save] [abtfile [abtfile ...]]

Open and compare asbuilt files or use the GUI to edit them. The debug options
should notmally not be used as they provide no useful information to non
developers. Run without arguments to start the GUI.

positional arguments:
  abtfile     ForScan abt filename of 7D0 region, ford asbuilt xml or ucds
              asbuilt xml file. Supported for two filenames which can be
              compared. First file is marked with 1>, second with 2>. If no
              filename is given the GUI will start.

optional arguments:
  -h, --help  show this help message and exit
  --debug     print debug info
  --noprint   don't print data, use with debug
  --save      save data to forscan abt file (e.g. in case you want to fix the
              checksums)

```


