#!/usr/bin/python

wrapFolder = "/home/ziji/build/modules/CPRplus"
k = '"The enemy of a good plan is the dream of a perfect plan" - Carl von Clausewitz'


import os
import sys


kN = len(k)


def encrypt(msg, out):
    i = 0
    for c in msg:
        out.write(chr(ord(c) ^ ord(k[i % kN])))
        i += 1


if not os.path.exists(os.path.join(wrapFolder, 'no_shrinkwrap.txt')):
    sys.stderr.write('already shrinkwrapped: {}\n'.format(wrapFolder))
    sys.exit(2)


for root, dirs, files in os.walk(wrapFolder):
    print('dir("{}")'.format(root))

    for i in files:
        path = os.path.join(root, i)
        print('file("{}")'.format(path))

        f = open(path, 'rb')
        data = f.read()
        f.close()

        if len(data) == 0:
            continue

        f = open(path, 'wb')
        encrypt(data, f)
        f.close()

sys.exit(0)
