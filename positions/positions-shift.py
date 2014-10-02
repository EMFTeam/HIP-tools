#!/usr/bin/python
# -*- coding: cp1252 -*-
# -*- python-indent-offset: 4 -*-

VERSION = '1.0'

import sys
import traceback
import argparse
import os
import re


p_position = re.compile(r'^(\-?\d+\.\d{3}) (\-?\d+\.\d{3}) (\-?\d+\.\d{3}) (\-?\d+\.\d{3}) (\-?\d+\.\d{3}) '
                        r'(\-?\d+\.\d{3}) (\-?\d+\.\d{3}) (\-?\d+\.\d{3}) (\-?\d+\.\d{3}) (\-?\d+\.\d{3}) \t\t\}$')

p_rotation = re.compile(r'^(\-?\d+\.\d{3}) (\-?\d+\.\d{3}) (\-?\d+\.\d{3}) (\-?\d+\.\d{3}) (\-?\d+\.\d{3}) \t\t\}$')


class Point:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def translate_west(self, delta):
        self.x -= delta
        if self.x < 0:
            self.x = 0


class ProvincePositions:
    def __init__(self, name, prov_id, position, rotation, height):
        self.skip = False
        self.name = name
        self.id = prov_id
        self.position = position
        self.rotation = rotation
        self.height = height

    def preserve(self):
        self.skip = True

    def translate_west(self, delta):
        if not self.skip:
            for p in self.position:
                p.translate_west(delta)

    def serialize(self, f):
        f.write('#{0.name}\n\t{0.id}=\n\t{{\n\t\tposition=\n\t\t{{\n'.format(self))
        for p in self.position:
            f.write('{0.x:0.3f} {0.y:0.3f} '.format(p))
        f.write('\t\t}\n\t\trotation=\n\t\t{\n')
        for theta in self.rotation:
            f.write('{0:0.3f} '.format(theta))
        f.write('\t\t}\n\t\theight=\n\t\t{\n')
        for h in self.height:
            f.write('{0:0.3f} '.format(h))
        f.write('\t\t}\n\t}\n')


def get_args():
    parser = argparse.ArgumentParser(description="Translate CK2-style map/positions.txt on the X-axis.")
    parser.add_argument('input_file', metavar='FILENAME',
                        help='path to input positions.txt file')
    parser.add_argument('--pixels-west', '-p', required=True,
                        help='how many pixels to translate positions westward (negative for eastward)')
    parser.add_argument('--output-file', '-o', default='./positions.txt',
                        help='path to output file [default: %(default)s]')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='show verbose information about what the script is doing;'
                             'repeat this option multiple times for more details')
    parser.add_argument('--version', '-V', action='version', version='%(prog)s '+VERSION,
                        help='show program version and quit')
    return parser.parse_args()


def main():
    # noinspection PyBroadException
    args = get_args()

    try:
        if not os.path.isfile(args.input_file):
            sys.stderr.write('Not an input file: {}\n'.format(args.input_file))
            return 1

        if os.path.realpath(args.input_file) is os.path.realpath(args.output_file):
            sys.stderr.write('Fatal: Input and output are the same file!\n')
            return 1

        n_line = 0

        with open(args.input_file, mode='rb') as f:
            with open(args.output_file, mode='wb') as of:
                while True:
                    l = f.readline()
                    if len(l) == 0:
                        break
                    n_line += 1
                    name = (l.rstrip('\r\n'))[1:]

                    l = f.readline()
                    if len(l) == 0:
                        sys.stderr.write('Fatal: Unexpected EOF!\n')
                        return 1
                    n_line += 1
                    prov_id = int(l.rstrip('=\r\n').lstrip('\t'))

                    for i in range(4):
                        l = f.readline()
                        if len(l) == 0:
                            sys.stderr.write('Fatal: Unexpected EOF!\n')
                            return 1
                        n_line += 1
                    m = p_position.match(l)
                    if not m:
                        sys.stderr.write('Fatal: Failed to match position values: line {}\n'.format(n_line))
                        return 1
                    position = [Point(m.group(1), m.group(2)), Point(m.group(3), m.group(4)),
                                Point(m.group(5), m.group(6)), Point(m.group(7), m.group(8)),
                                Point(m.group(9), m.group(10))]

                    for i in range(3):
                        l = f.readline()
                        if len(l) == 0:
                            sys.stderr.write('Fatal: Unexpected EOF!\n')
                            return 1
                        n_line += 1
                    m = p_rotation.match(l)
                    if not m:
                        sys.stderr.write('Fatal: Failed to match rotation values: line {}\n'.format(n_line))
                        return 1
                    rotation = [float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)),
                                float(m.group(5))]

                    for i in range(3):
                        l = f.readline()
                        if len(l) == 0:
                            sys.stderr.write('Fatal: Unexpected EOF!\n')
                            return 1
                        n_line += 1
                    m = p_rotation.match(l)  # Rotation and height value list are same pattern
                    if not m:
                        sys.stderr.write('Fatal: Failed to match rotation values: line {}\n'.format(n_line))
                        return 1
                    height = [float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)),
                              float(m.group(5))]

                    l = f.readline()
                    if len(l) == 0:
                        sys.stderr.write('Fatal: Unexpected EOF!\n')
                        return 1
                    n_line += 1

                    prov_entry = ProvincePositions(name, prov_id, position, rotation, height)
                    prov_entry.translate_west(float(args.pixels_west))
                    prov_entry.serialize(of)

                    if args.verbose:
                        sys.stderr.write('#{} ({})\n'.format(prov_id, name))
                        sys.stderr.flush()

        return 0

    except:
        sys.stderr.write("\nFATAL ERROR:\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(255)

if __name__ == "__main__":
    sys.exit(main())
