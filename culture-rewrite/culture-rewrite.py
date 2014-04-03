#!/usr/bin/python
__author__ = 'zijistark'
VERSION = '0.9.0~alpha1'


import os
import sys
import shutil
import re
import traceback
import argparse
import csv
import history


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


def main():
    args = get_args()
    try:
        # Validate the split date
        m = p_date.match(args.date)
        if not m:
            sys.stderr.write("The given cultural split date '%s' is not a valid CKII-format date (or pseudo-date).\n"
                             % args.date)
            return 1

        # Ensure that we can open the input spreadsheet and auto-recognize its CSV dialect
        if not os.path.isfile(args.rule_file):
            sys.stderr.write("The given culture melt input spreadsheet '%s' is not a valid file.\n" % args.rule_file)
            return 1

        with open(args.rule_file, 'rb') as f:
            # Sample file data, auto-detect CSV dialect, reset file pointer to beginning
            csv_dialect = csv.Sniffer().sniff(f.read(2048), ';,')
            f.seek(0)

            # Wrap a CSV reader for the detected dialect around the input file
            csv_reader = csv.reader(f, dialect=csv_dialect)

            csv_header = csv_reader.next()  # Advance past header row

            if csv_header is None:
                sys.stderr.write("Failed to read CSV spreadsheet header row (corrupt/invalid file?)\n")
                return 3

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

            # Spreadsheet field indices of interest
            DYN = 0
            CUL_EARLY = 3
            CUL_LATER = 4

            for row in csv_reader:
                print('for dynasty {}, {} => {}'.format(row[DYN], row[CUL_EARLY], row[CUL_LATER]))

        char_hist.rewrite(args.output_history_dir)  # Fully rewrite the history folder from parse trace in RAM

        return 0

    except history.CHParseError as e:
        sys.stderr.write('\nFatal character history parse error:\n' + str(e))
        return 2

    except csv.Error:
        sys.stderr.write('\nFatal error while reading input CSV spreadsheet\n')
        return 3

    except:
        sys.stderr.write('\nUnexpected fatal error occurred! Stack trace:\n\n')
        traceback.print_exc(file=sys.stderr)
        return 255



if __name__ == '__main__':
    sys.exit(main())
