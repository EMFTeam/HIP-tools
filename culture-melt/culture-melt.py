#!/usr/bin/python
__author__ = 'zijistark'
VERSION = '1.0.1'


import os
import sys
import shutil
import re
import codecs
import traceback
import argparse
import meltcsv
import history
import pprint


p_date = re.compile(r'^(\d{1,4})\.(\d{1,2})\.(\d{1,2})$')


def get_args():
    parser = argparse.ArgumentParser(
        description="Split, merge, & melt cultures in a CKII character history database [SWMH German target].",
    )
    parser.add_argument('rule_file', metavar='FILENAME',
                        help='name of CSV file containing dynasty and early -> later culture melt rules')
    parser.add_argument('--date', required=True,
                        help='date at which the early -> later cultural transition occurs for characters, '
                             'based upon their birth date (e.g., 1120.1.1)')
    parser.add_argument('--history-dir', required=True,
                        help='path to directory from which to load preexisting character history')
    parser.add_argument('--output-history-dir', default='./characters',
                        help='path at which the new character history directory should be created [default: '
                             '%(default)s]')
    parser.add_argument('--force', '-f', action='store_true',
                        help='if the given new character history directory already exists, '
                             'delete it, and recreate it with the new character history')
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='show verbose information about what the script is doing;'
                             'repeat this option multiple times for more details')
    parser.add_argument('--version', '-V', action='version', version='%(prog)s '+VERSION,
                        help='show program version and quit')
    return parser.parse_args()


def transform(rules, ch, melt_date):
    cultures_melted = {}

    cbd = ch.chars_by_dynasty

    for r in rules:
        if r.dyn_id not in cbd:  # Unused dynasty (dynasty exists, but no characters use it)
            continue

        # Track actual cultures melted in practice (and how many rules had an effect upon each, while at it)

        if r.cul_early in cultures_melted:
            cultures_melted[r.cul_early] += 1
        else:
            cultures_melted[r.cul_early] = 1

        if r.cul_later in cultures_melted:
            cultures_melted[r.cul_later] += 1
        else:
            cultures_melted[r.cul_later] = 1

        global stats_n_chars_melted

        #print('\nDynasty: ' + str(r.dyn_id))

        # Actual transform rule implied by original spreadsheet row finally gets executed...
        for c in ch.chars_by_dynasty[r.dyn_id]:
            new_cul = r.cul_early if c.bdate < melt_date else r.cul_later
            if new_cul != c.culture.val:
                #print('  Character{{ Name: "{}" / ID: {} }}'.format(c.name.val, c.id))
                c.dirty = True
                stats_n_chars_melted += 1
                c.culture = history.CommentableVal(new_cul, '# was ' + c.culture.val)

    return cultures_melted


def main():
    args = get_args()
    try:
        # Validate the split date
        m = p_date.match(args.date)
        if not m:
            sys.stderr.write("The given cultural split date '%s' is not a valid CKII-format date (or pseudo-date).\n"
                             % args.date)
            return 1

        # Canonicalize date for later lexicographic comparisons in rules
        args.date = history.DateVal(m.group(1), m.group(2), m.group(3))

        # Ensure that we can open the input spreadsheet and parse its rules sufficiently
        if not os.path.isfile(args.rule_file):
            sys.stderr.write("The given culture melt input spreadsheet '%s' is not a valid file.\n" % args.rule_file)
            return 1

        global stats_n_chars_melted
        stats_n_chars_melted = 0

        with codecs.open(args.rule_file, mode='rb', encoding='cp1252') as f:
            melt_rules = meltcsv.parse_melt_rules(f)

        #for r in melt_rules:
        #    print(str(r))

        # Handle output directory preexistence
        if os.path.exists(args.output_history_dir):
            if args.force:
                if os.path.isdir(args.output_history_dir):
                    shutil.rmtree(args.output_history_dir)
                else:
                    os.remove(args.output_history_dir)
            else:
                sys.stderr.write("The output directory already exists (use -f / --force to overwrite by default): " +
                                 args.output_history_dir + "\n")
                return 1

        # Create a new output directory
        os.makedirs(args.output_history_dir)

        char_hist = history.CharHistory(sys.stdout, args.verbose)
        char_hist.parse_dir(args.history_dir)  # Parse entire character history folder

        # with open('1170_vanilla_survey.csv', 'wb') as o:
        #     o.write('DYNASTY;ID;DEMESNE;COMMENT;CHARACTER ID\r\n')
        #     with open('raw_1170_survey.txt', 'r') as i:
        #         for line in i:
        #             line.rstrip('\r\n')
        #             s = line.split(' ', 1)
        #
        #             m = re.match(r'^([^\|]+)\|([^\|]+)\|\s*(\[[^\]]+\])?\s*$', s[1])
        #             if not m:
        #                 print('failed match: ' + line)
        #                 continue
        #             s = {'dynID': int(char_hist.chars[int(s[0])].dynasty.val),
        #                  'dynasty': m.group(1),
        #                  'charID': s[0],
        #                  'comment': m.group(3),
        #                  'demesne': m.group(2)}
        #             o.write('{dynasty};{dynID};{demesne};{comment};{charID}\r\n'.format(**s))



        cul_melted = transform(melt_rules, char_hist, args.date)

        char_hist.rewrite(args.output_history_dir)  # Fully rewrite the history folder from parse trace in RAM

        if len(cul_melted) > 0:
            print('Cultures melted:')

            for cul in sorted(cul_melted):
                print('  {} [{} dynasty rules effectively contributed to melt]'.format(cul, cul_melted[cul]))
        else:
            print('No cultures were melted.')

        print('Characters actually melted: {}'.format(stats_n_chars_melted))

        return 0

    except history.CHParseError as e:
        sys.stderr.write('\nFatal character history parse error:\n' + str(e))
        return 2

    except meltcsv.MeltCSVError as e:
        sys.stderr.write('\n' + str(e) + '\n')
        return 3

    except:
        sys.stderr.write('\nUnexpected fatal error occurred! Stack trace:\n\n')
        traceback.print_exc(file=sys.stderr)
        return 255



if __name__ == '__main__':
    sys.exit(main())
