__author__ = 'zijistark'
VERSION = '1.0'

import sys
import os
import traceback
import argparse
import re

DEFAULT_VANILLA_DIR = "/cygdrive/d/SteamLibrary/steamapps/common/Crusader Kings II/common/landed_titles"
DEFAULT_VANILLA_HISTORY_DIR = "/cygdrive/d/SteamLibrary/steamapps/common/Crusader Kings II/history/titles"
p_title_all = re.compile(r'\W([cdek]_[\w_\-]+)')
p_title = re.compile(r'^[cdek]_[\w_\-]+')
p_txt_file = re.compile(r'^(.+?)\.txt$')

def get_args():
    parser = argparse.ArgumentParser(description="Show titles that are defined in vanilla but not a mod.")
    parser.add_argument('--base-history', default=DEFAULT_VANILLA_HISTORY_DIR,
                        help='path to base history/titles directory [default: %(default)s]')
    parser.add_argument('--base-titles', default=DEFAULT_VANILLA_DIR,
                        help='path to base landed_titles directory [default: %(default)s]')
    parser.add_argument('--titles', '-t', default='./common/landed_titles',
                        help='path to mod landed_titles directory [default: %(default)s]')
    parser.add_argument('--history', '-o', default='./history/titles',
                        help='path to output mod history/titles directory [default: %(default)s]')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='show verbose information about what the script is doing;'
                             'repeat this option multiple times for more details')
    parser.add_argument('--version', '-V', action='version', version='%(prog)s '+VERSION,
                        help='show program version and quit')
    return parser.parse_args()


# noinspection PyBroadException


def getTitleSet(titles_dir):
    title_set = set()
    for f in os.listdir(titles_dir):
        if p_txt_file.match(f):
            with open(os.path.join(titles_dir, f)) as in_file:
                data = in_file.read()
                matches = []
                m = p_title.match(data)
                if m:
                    matches = [m.group(0)]
                matches += p_title_all.findall(data)
                for t in matches:
                    title_set.add(t)
    return title_set


def main():

    args = get_args()

    try:
        if not os.path.isdir(args.base_history):
            sys.stderr.write('Base title history directory invalid: {}\n'.format(args.base_history))
            return 1
        if not os.path.isdir(args.history):
            sys.stderr.write('Output title history directory invalid: {}\n'.format(args.history))
            return 1
        if not os.path.isdir(args.base_titles):
            sys.stderr.write('Base landed_titles directory invalid: {}\n'.format(args.flags))
            return 1
        if not os.path.isdir(args.titles):
            sys.stderr.write('Landed titles directory invalid: {}\n'.format(args.titles))
            return 1

        history_set = set()

        for f in os.listdir(args.base_history):
            m = p_txt_file.match(f)
            if m is None:
                print("Filename does not match expected pattern (*.txt): {}".format(f))
            else:
                history_set.add(m.group(1))

        base_title_set = getTitleSet(args.base_titles)
        mod_title_set = getTitleSet(args.titles)

        base_title_set -= mod_title_set

        for t in sorted(base_title_set):
            print(t)

        # for t in history_set:
        #     if t in base_title_set:
        #         f = t + '.txt'
        #         f = os.path.join(args.history, f)
        #         if os.path.exists(f):
        #             print("WARN: Title '{}' has no definition in mod but a modded history file".format(t))
        #         else:
        #             of = open(f, 'w')
        #             of.write("#BLOCKED: vanilla history file for vanilla title without SWMH definition\n")
        #             of.close()

        return 0

    except:
        sys.stderr.write("\nFATAL ERROR:\n")
        traceback.print_exc(file=sys.stderr)
        sys.exit(255)

if __name__ == "__main__":
    sys.exit(main())
