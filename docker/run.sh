#!/bin/bash
cd /src/
pyinstaller --onefile --distpath /dist/ --workpath /build/ apim.py
