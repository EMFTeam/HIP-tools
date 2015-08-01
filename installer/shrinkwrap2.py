#!/usr/bin/python

wrapFolder = "/home/ziji/build/modules/CPRplus"
k = bytearray('"The enemy of a good plan is the dream of a perfect plan" - Carl von Clausewitz')


import os
import sys
import time


kN = len(k)


def encrypt(buf, length):
    for i in xrange(length):
        buf[i] ^= k[i % kN]


buf = bytearray(1 << 15)
mv_buf = memoryview(buf)


def encryptFile(path):
    tmpPath = path + '.tmp'
    with open(path, 'rb') as fsrc:
        with open(tmpPath, 'wb') as fdst:
            while 1:
                len = fsrc.readinto(buf)
                if len == 0:
                    break
                encrypt(buf, len)
                fdst.write(mv_buf[:len])
    os.unlink(path)
    os.rename(tmpPath, path)


if not os.path.exists(os.path.join(wrapFolder, 'no_shrinkwrap.txt')):
    sys.stderr.write('already shrinkwrapped: {}\n'.format(wrapFolder))
    sys.exit(2)

start = time.time()

for root, dirs, files in os.walk(wrapFolder):

    for i in files:
        path = os.path.join(root, i)
        encryptFile(path)

end = time.time()

print("Elapsed: %0.1fsec" % (end - start))

sys.exit(0)
