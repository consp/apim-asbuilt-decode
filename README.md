# Ford APIM AsBuilt decoder tool
## Intro
This repository is meant for users who want to edit their values of the AsBuilt data of the Ford Sync 3 APIM.

There are several options to get the information in this repository though the following give problems:

- The debug menu on the APIM module: Offsets the data incorrectly somewhere after option 30 (verified in program code) this is the cause of some confusion in some sheets containing the decoded data already on the internet
- Trail and error (used to verify the data)
- The source, e.g. the binary data of the files present in the updates packages

Fortunately Ford included a lot of debugging strings in their code! This allowed me to debug all the data for my device and some other options for the My19 and My20 devices. There are however no lookup tables for those options and not all are debugged in the code so not everything is included.

There are in total 134 "standard" options in 7D0-01 to 7D0-04 (DE00-03). There are more options in 7D0-05 to 07 (DE04-06) which are mostly offset/multiplier values.

Please note that some settings change quite a lot. Most radio and CGEA/C1MCA settings change quite a lot internally. There are at least 177 calibration options in the 3.0 release of Sync 3 and 295 in Sync 3.4. 

## Acknowledgements

~~Since I do not own a gen 4 module (Sync 3.3 and up) it is imposible to test things for me.~~ Not all Gen4 stuff works on my module as the car it is in does not support it. I got most of the info from DE07/08 (7D0-08/09) from code but information was missing, like detailed names and some exact bit locations especially for 7D0-08. The data was corrected by the F150 ASBuilt sheet from the F150Forums which confirmed the data present in code. I'm not completely sure who is/are the author(s), leave a pull request if you want to add you name here. The code from the 3.4 update floating around on the intenet contains a lot of the 08/09 block options and I used those to verify most options.


## Inconsistencies and known issues
The following is incorrect or missing in the decode program:
- The bluetooth audio profile does something but I haven't figured out what yet. It looks like a lookup table change but I'm not sure.

## Features
- Dumps your abt binary data into something 'somewhat' readable
- Lets you compare files to figure out you prefered configuration
- Uses GUI to change options more easy and lets you see the results in the files if you change them.

## Todo
- ~~Add save option to fix the checksums~~ See GUI and ```--save``` option
- ~~Add 7D0-08 (My19) and 7D0-09 (My20) decoding formats~~ Most has been confirmed by other people figuring things out on their own and from the 3.4 update.

## Usage and requirements
Requires the following:
- Python 3.5 and up
- Qt5 libraries and PyQt5. x64 windows executables have everything built in, 32bit require meddeling with pyqt5.
- As built file(s) in either Ford XML format (.ab) or ForScan dump format (.abt) in new or old style or a UCDS xml file.

GUI: python3 src/apim.py or run the excutable. You can open a file, change stuff and save it

Command line options: Either one or two files need to be present
```
> python3 src/apim.py YOURVINHERE.ab filename.abt 
Loading ../YOURVINHERE.ab
Loading Ford XML file
Loaded 9 blocks, 87 bytes
Loading ../filename.abt
Forscan ABT format
New forscan format
Loaded 7 blocks, 57 bytes
Block 1 (7D0-01 or DE00)
#Name                                                                                              - Field      Location     Val&Msk  = Res
Smart DSP: ......................................................................................... 7D0-01-01 Xnnn nnnn nn AA & 80 = 80 vs 00 & 80 = 00
        2> 00:	Do not log missing DSP Messages
     1>    01:	Log missing DSP Messages (When configured for Smart DSP and Lincoln then enable THX Deep Note)
AAM: ............................................................................................... 7D0-01-01 Xnnn nnnn nn AA & 40 = 00 vs 00 & 40 = 00
     1> 2> 00:	Do not log missing AAM messages
           01:	Log Missing AAM messages (Send speaker walkaround request to ACM)
SDARS: ............................................................................................. 7D0-01-01 Xnnn nnnn nn AA & 20 = 20 vs 00 & 20 = 00
        2> 00:	Do not log missing SDARS (ACM) message
     1>    01:	Log Missing SDARS (ACM) message
RSEM: .............................................................................................. 7D0-01-01 Xnnn nnnn nn AA & 10 = 00 vs 00 & 10 = 00
     1> 2> 00:	Do not log missing RSEM messages
           01:	Log Missing RSEM messages
PDC HMI: ........................................................................................... 7D0-01-01 nXnn nnnn nn AA & 08 = 08 vs 01 & 08 = 00
           00:	Off
     1> 2> 01:	On
Rear Camera: ....................................................................................... 7D0-01-01 nXnn nnnn nn AA & 06 = 02 vs 00 & 06 = 00
        2> 00:	RVC Not Present
     1>    01:	RVC Present
           02:	Reserved
           03:	Reserved
Illumination: ...................................................................................... 7D0-01-01 nXnn nnnn nn AA & 01 = 00 vs 01 & 01 = 01
     1>    00:	FNA Strategy
        2> 01:	FoE Strategy
Extended Play: ..................................................................................... 7D0-01-01 nnXn nnnn nn 0A & 80 = 00 vs 00 & 80 = 00
     1> 2> 00:	On
           01:	Off
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


