#!/usr/bin/python

wrapFolder = "/home/ziji/build/modules/CPRplus"
k = bytearray('"The enemy of a good plan is the dream of a perfect plan" - Carl von Clausewitz')
header_len = 1 << 12


import os
import sys
import time


kN = len(k)


def is_binary(path):
    _, extension = os.path.splitext(i)
    return extension in ['.dds', '.tga', '.pda']


def encrypt(buf, length):
    for i in xrange(length):
        buf[i] ^= k[i % kN]


def encryptFile(path, header_only=False):
    tmpPath = path + '.tmp'
    with open(path, 'rb') as fsrc, open(tmpPath, 'wb') as fdst:
        length = os.path.getsize(path)
        buf = bytearray(length)
        fsrc.readinto(buf)
        if header_only:
            length = min(header_len, length)
        encrypt(buf, length)
        fdst.write(buf)
    os.unlink(path)
    os.rename(tmpPath, path)


if not os.path.exists(os.path.join(wrapFolder, 'no_shrinkwrap.txt')):
    sys.stderr.write('already shrinkwrapped: {}\n'.format(wrapFolder))
    sys.exit(2)

start = time.time()

for root, dirs, files in os.walk(wrapFolder):
    for i in files:
        path = os.path.join(root, i)
        encryptFile(path, header_only=is_binary(path))

end = time.time()

print("Elapsed: %0.1fsec" % (end - start))

sys.exit(0)
