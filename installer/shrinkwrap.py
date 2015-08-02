#!/usr/bin/python

folder = "/home/ziji/build/modules/CPRplus"
k = bytearray(br'"The enemy of a good plan is the dream of a perfect plan" - Carl von Clausewitz')
header_len = 1 << 12


import os
import sys
import time


def is_binary(path):
    _, extension = os.path.splitext(path)
    return extension.lower() in ['.dds', '.tga', '.pdn', '.psd', '.xcf']


kN = len(k)


def encrypt(buf, length):
    for i in xrange(length):
        buf[i] ^= k[i % kN]


def encrypt_file(path, header_only=False):
    tmp_path = path + '.tmp'
    with open(path, 'rb') as fsrc, open(tmp_path, 'wb') as fdst:
        length = os.path.getsize(path)
        buf = bytearray(length)
        fsrc.readinto(buf)
        if header_only:
            length = min(header_len, length)
        encrypt(buf, length)
        fdst.write(buf)
    os.unlink(path)
    os.rename(tmp_path, path)

if not os.path.exists(folder):
    sys.stderr.write('invalid shrinkwrap folder: {}\n'.format(folder))
    sys.exit(1)

# Check for the encryption sentinel first
sentinel_path = os.path.join(folder, 'no_shrinkwrap.txt')

if not os.path.exists(sentinel_path):
    sys.stderr.write('already shrinkwrapped: {}\n'.format(folder))
    sys.exit(0)

start_time = time.time()

for root, dirs, files in os.walk(folder):
    for i in files:
        path = os.path.join(root, i)
        encrypt_file(path, header_only=is_binary(path))

end_time = time.time()

# Remove encryption sentinel
os.unlink(sentinel_path)

sys.stderr.write("shrinkwrapped: %0.1fs\n" % (end_time - start_time))
sys.exit(0)
