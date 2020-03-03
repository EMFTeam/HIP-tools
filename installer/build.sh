#!/bin/bash

zipadd () {
	'/cygdrive/c/Program Files/7-Zip/7z' a -t7z -mx9 HIP.7z "$@"
}

set -e

#echo "$(date '+%F')" > ./modules/version.txt
rm -f HIP.7z
zipadd modules
zipadd HIP.exe
zipadd python27.dll
zipadd library.zip
zipadd HIP_ReadMe.txt
zipadd main.py
