# Ford APIM AsBuilt decoder tool
## Intro
This repository is meant for users who want to edit their values of the AsBuilt data of the Ford Sync 3 APIM.

There are several options to get the information in this repository though the following give problems:

- The debug menu on the APIM module: Offsets the data incorrectly somewhere after option 30 (verified in program code) this is the cause of some confusion in some sheets containing the decoded data already on the internet
- Trail and error (used to verify the data)
- The source, e.g. the binary data of the files present in the updates packages

Fortunately Ford included a lot of debugging strings in their code! This allowed me to debug all the data for my device and some other options for the My19 and My20 devices. There are however no lookup tables for those options and not all are debugged in the code so not everything is included.

There are in total 134 "standard" options in 7D0-01 to 7D0-04. There are more options in 7D0-05 to 07 which are mostly offset/multiplier values. All are included in this thing.

Please note that some settings change quite a lot. Most radio and CGEA/C1MCA settings change quite a lot internally. There are at least 177 calibration options in the 3.0 release of Sync 3 and 295 in Sync 3.4 and this build does only includes 151.

## Inconsistencies and known issues
The following is incorrect or missing in the decode program:
- The splash screen option (option 70) is missing data. This has to be added manually.
- Vehicle styles might be incomplete (there are indications of additional types but none are present in the binaries)
- I have no clue wat some "strategies" are but they seem to change some other settings
- The bluetooth pairing timeout field (119) is too big as there are options in it which are not in code. They are options for sync 3.2 and up which are not in the 3.0 code. You should find out those from other sources.
- The bluetooth audio profile does simething but I haven't figured out what yet. It looks like a lookup table change but I'm not sure.
- For sync 3.2 and up there are more options for the climate option (130) which are not know to me
- Options 127, 128 and 129 seem to be in a different place but I do not know where.
- Field 131 has all the values but they are in the wrong order. There is some translation going on from calibration data to the internal data which I have not figured out yet. It is a simple lookup table in code so I assumed it was 1:1 but it isn't.

## Features
- Dumps your abt binary data into something somewhat readable
- Lets you compare files to figure out you prefered configuration

## Todo
- Add save option to fix the checksums
- Add 7D0-08 (My19) and 7D0-09 (My20) decoding formats

## Usage
Requires the following:
- Python 3.5 and up (3.3 and up might work)
- As built file in either Ford XML format (.ab) or ForScan dump format (.abt) in new or old style.
- A blob with all the data (one included for your conveniance)

Example with two files:
```
> python3 src/decode.py filename.abt YOURVINHERE.ab

Loading filename.abt
Forscan ABT format
Loaded 7 blocks, 57 bytes
Loading YOURVINHERE.ab
Loading Ford XML file
Loaded 9 blocks, 86 bytes
0   - 1  - 0  Smart DSP:  ....................................................................................... 7D0-01-01 // 0x80     Xnnn nnnn nn // 0x09 0xAA
                     1>    0:   Do not log missing DSP Messages
                        2> 1:   Log missing DSP Messages (When configured for Smart DSP and Lincoln then enable THX Deep Note)
1   - 1  - 1  AAM:  ............................................................................................. 7D0-01-01 // 0x40     Xnnn nnnn nn // 0x09 0xAA
                     1> 2> 0:   Do not log missing AAM messages
                           1:   Log Missing AAM messages (Send speaker walkaround request to ACM)
2   - 1  - 2  SDARS:  ........................................................................................... 7D0-01-01 // 0x20     Xnnn nnnn nn // 0x09 0xAA
                     1>    0:   Do not log missing SDARS (ACM) message
                        2> 1:   Log Missing SDARS (ACM) message
3   - 1  - 3  RSEM:  ............................................................................................ 7D0-01-01 // 0x10     Xnnn nnnn nn // 0x09 0xAA
                     1> 2> 0:   Do not log missing RSEM messages
                           1:   Log Missing RSEM messages
4   - 1  - 4  PDC HMI:  ......................................................................................... 7D0-01-01 // 0x08     nXnn nnnn nn // 0x09 0xAA
                           0:   Off
                     1> 2> 1:   On
5   - 2  - 5  Rear Camera:  ..................................................................................... 7D0-01-01 // 0x06     nXnn nnnn nn // 0x09 0xAA
                     1>    0:   RVC Not Present
                        2> 1:   RVC Present
                           2:   Reserved
                           3:   Reserved
6   - 1  - 7  Illumination:  .................................................................................... 7D0-01-01 // 0x01     nXnn nnnn nn // 0x09 0xAA
                        2> 0:   FNA Strategy
                     1>    1:   FoE Strategy
7   - 1  - 8  Extended Play:  ................................................................................... 7D0-01-01 // 0x80     nnXn nnnn nn // 0x68 0x0A
                     1> 2> 0:   On
                           1:   Off
8   - 2  - 9  Extended Play Time:  .............................................................................. 7D0-01-01 // 0x60     nnXn nnnn nn // 0x68 0x0A
                        2> 0:   20 minutes
                           1:   30 minutes (FNA)
                           2:   40 minutes
                     1>    3:   60 minutes (FoE)

...
```


