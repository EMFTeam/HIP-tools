#!/usr/bin/python
# -*- coding: cp1252 -*-
# -*- python-indent-offset: 4 -*-

import sys
import traceback


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def translate_west(self, delta):
        self.x -= delta


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
        f.write('#{0.name}\n\t{0.id}=\n\t{{\t\tposition=\n\t\t{{\n'.format(self))
        for p in self.position:
            f.write('{0.x:0.3f} {0.y:0.3f} '.format(p))
        f.write('\t\t}\n\t\trotation=\n\t\t{\n')
        for theta in self.rotation:
            f.write('{0:0.3f} '.format(theta))
        f.write('\t\t}\n\t\theight=\n\t\t{\n')
        for h in self.height:
            f.write('{0:0.3f} '.format(h))
        f.write('\t\t}\n\t}\n')


def main():
    # noinspection PyBroadException
    try:
        return 0

    except:
        sys.stderr.write("\nFATAL ERROR:\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(255)

if __name__ == "__main__":
    sys.exit(main())
