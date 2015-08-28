#!/usr/bin/python

__author__ = 'zijistark'
VERSION = '1.0'

import sys
import os
import traceback
import argparse
import re

DEFAULT_VANILLA_DIR = "/cygdrive/d/SteamLibrary/steamapps/common/Crusader Kings II/gfx/flags"
p_flag_file = re.compile(r'^(.*?)\.tga$')
p_title_all = re.compile(r'\W([cdek]_[\w_\-]+)')
p_title = re.compile(r'^[cdek]_[\w_\-]+')
p_txt_file = re.compile(r'^.*?\.txt$')

def get_args():
    parser = argparse.ArgumentParser(description="Ensure all CK2 landed_titles have a CoA.")
    parser.add_argument('--flags', '-f', default='./gfx/flags',
                        help='path to primary flag directory [default: %(default)s]')
    parser.add_argument('--flags-fallback', default=DEFAULT_VANILLA_DIR,
                        help='path to output file [default: %(default)s]')
    parser.add_argument('--titles', '-t', default='./common/landed_titles',
                        help='path to landed_titles directory [default: %(default)s]')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='show verbose information about what the script is doing;'
                             'repeat this option multiple times for more details')
    parser.add_argument('--version', '-V', action='version', version='%(prog)s '+VERSION,
                        help='show program version and quit')
    return parser.parse_args()


# noinspection PyBroadException


def main():

    args = get_args()

    try:
        if not os.path.isdir(args.flags):
            sys.stderr.write('Primary flag directory invalid: {}\n'.format(args.flags))
            return 1
        if not os.path.isdir(args.flags_fallback):
            sys.stderr.write('Vanilla (fallback) flag directory invalid: {}\n'.format(args.flags_fallback))
            return 1
        if not os.path.isdir(args.titles):
            sys.stderr.write('Landed titles directory invalid: {}\n'.format(args.titles))
            return 1

        flag_set = set()

        for f in os.listdir(args.flags_fallback) + os.listdir(args.flags):
            m = p_flag_file.match(f)
            if m is None:
                print("Filename does not match expected pattern (*.tga): {}".format(f))
            else:
                flag_set.add(m.group(1))

        print("Flag set: {}".format(flag_set))

        title_set = set()

        for f in os.listdir(args.titles):
            if p_txt_file.match(f):
                with open(os.path.join(args.titles, f)) as in_file:
                    data = in_file.read()
                    matches = []
                    m = p_title.match(data)
                    if m:
                        matches = [m.group(0)]
                    matches += p_title_all.findall(data)
                    print("Matches from {}:\n{}\n".format(f, matches))
                    for t in matches:
                        title_set.add(t)
        title_set -= flag_set

        for t in title_set:
            print(t)

        return 0

    except:
        sys.stderr.write("\nFATAL ERROR:\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(255)

if __name__ == "__main__":
    sys.exit(main())
