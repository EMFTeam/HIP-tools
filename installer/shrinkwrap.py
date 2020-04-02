#!/usr/bin/python2

import os
import sys
import time
import datetime
import argparse
import hashlib

default_module_folder = '/cygdrive/c/Users/{}/Documents/Paradox Interactive/Crusader Kings II/mod/modules'.format(os.environ.get('USER', 'ziji'))
shrinkwrap_sentinel_file = 'no_shrinkwrap.txt'
k = bytearray(br'"The enemy of a good plan is the dream of a perfect plan" - Carl von Clausewitz')
header_len = 1 << 12
banned_file_ext = ['.pdn', '.psd', '.xcf', '.bak', '.tmp', '.rar', '.zip', \
                  '.7z', '.gz', '.tgz', '.xz', '.bz2', '.tar', '.ignore', \
                  '.xls', '.xlsx', '.xlsm', '.db']


def is_wanted(path):
    root, extension = os.path.splitext(path)
    return (extension.lower() not in banned_file_ext   and \
            not os.path.basename(root).startswith('.') and \
            not path.endswith('~'))


def is_binary(path):
    _, extension = os.path.splitext(path)
    return extension.lower() in ['.dds', '.tga']

def encrypt(buf, length):
    kN = len(k)
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


def cksum_file(fname):
    cksum = hashlib.md5()
    with open(fname, "rb") as f:
        cksum.update(f.read())
    return cksum.hexdigest()


def get_args():
    parser = argparse.ArgumentParser(
        description="Prepare a HIP modules/ folder for build (remove unwanted files & shrinkwrap).")
    parser.add_argument('--modules-dir', default=default_module_folder,
                        help='path to modules/ folder for build')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help="show verbose information about what I'm doing")
    return parser.parse_args()


args = get_args()
module_folder = os.path.abspath(args.modules_dir)
shrinkwrap_folder = os.path.join(module_folder, "CPRplus")

# CPRplus only wants its gfx/ sub-folder encrypted so that power users can play with the portrait definitions
real_shrinkwrap_folder = os.path.join(shrinkwrap_folder, 'gfx')

if not os.path.exists(module_folder):
    sys.stderr.write('invalid modules folder: {}\n'.format(module_folder))
    sys.exit(1)

if not os.path.exists(shrinkwrap_folder):
    sys.stderr.write('invalid shrinkwrap folder: {}\n'.format(shrinkwrap_folder))
    sys.exit(2)

if not os.path.exists(real_shrinkwrap_folder):
    sys.stderr.write('invalid "real" shrinkwrap folder: {}\n'.format(real_shrinkwrap_folder))
    sys.exit(3)

n_removed_files = 0
n_removed_bytes = 0
n_files = 0
n_bytes = 0

version_path = os.path.join(module_folder, 'version.txt')
manifest_path = os.path.join(module_folder, 'release_manifest.txt')
sentinel_path = os.path.join(shrinkwrap_folder, shrinkwrap_sentinel_file)

# Clear unwanted files from full distribution

if os.path.exists(manifest_path):
    os.unlink(manifest_path)

for root, dirs, files in os.walk(module_folder):
    for i in files:
        path = os.path.join(root, i)
        if path.endswith(shrinkwrap_sentinel_file):
            continue  # will get removed at end
        elif is_wanted(path):
            n_files += 1
            n_bytes += os.path.getsize(path)
        else:
            size = os.path.getsize(path)
            n_removed_files += 1
            n_removed_bytes += size
            os.unlink(path)
            if args.verbose > 0:
                head, f = os.path.split(path)
                d = head.replace(module_folder, '', 1)
                if d == '':
                    d = '/'
                print("removed file: '{}' ({}KB) in '{}'".format(f, size // 1000, d))

removed_MB = n_removed_bytes / 1000 / 1000
final_MB = n_bytes / 1000 / 1000

# Now, onward to encryption of real_shrinkwrap_folder...

# We will check for the encryption sentinel first

if not os.path.exists(sentinel_path):
    sys.stderr.write('already shrinkwrapped: {}\n'.format(shrinkwrap_folder))
else:
    start_wrap_time = time.time()
    for root, dirs, files in os.walk(real_shrinkwrap_folder):
        for i in files:
            path = os.path.join(root, i)
            encrypt_file(path, header_only=is_binary(path))
    end_wrap_time = time.time()
    os.unlink(sentinel_path)
    print("shrinkwrap time: %0.2fsec" % (end_wrap_time - start_wrap_time))

# Now that we've shrinkwrapped, build a checksum manifest file
start_cksum_time = time.time()
path_cksum_map = {}

for root, dirs, files in os.walk(module_folder):
    for i in files:
        real_path = os.path.join(root, i)
        if real_path == version_path:  # Don't checksum the module pack version.txt
            continue
        virt_path = os.path.relpath(real_path, module_folder)
        path_cksum_map[virt_path] = cksum_file(real_path)

with open(manifest_path, 'wb') as f:
    f.write('time: {}\n'.format(datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))
    for p in sorted(path_cksum_map):
        f.write('{} // {}\n'.format(p, path_cksum_map[p]))

end_cksum_time = time.time()
print("checksum time:   %0.2fsec" % (end_cksum_time - start_cksum_time))

print('final package:   %d files (%dMB)' % (n_files, final_MB))

if n_removed_files > 0:
    print('\n> removed %d unwanted files (%0.2fMB)' % (n_removed_files, removed_MB))

sys.exit(0)
