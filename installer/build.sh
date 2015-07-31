#!/bin/bash

zipadd () {
	'/cygdrive/c/Program Files/7-Zip/7z' a -t7z -mx9 HIP.7z "$@"
}

set -e

rm -f HIP.7z
zipadd modules
zipadd HIP.exe
zipadd python27.dll
zipadd library.zip
zipadd "HIP readme.txt"
zipadd main.py
