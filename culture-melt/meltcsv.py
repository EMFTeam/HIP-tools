__author__ = 'zijistark'

# A super-simple CSV parser for a rather specific dialect of CSV, with no [needed] support for proper quote escaping
# and other such usual CSV problems. This module was slapped together in response to Python's builtin module csv
# proving unreliable to my ends.
#
# Hand it a freshly-opened CSV file, it will do a quick format sanity check on construction, and then just iterate
# over its row objects. Only those rows that are valid for culture-melt are returned. The constructor also takes an
# optional file object for where it should direct non-critical errors and warnings about the row's raw data (using
# sys.stdout by default). Actual CSV format errors raise a generic MeltCSVError which does at least give a  line
# number for manual inspection of the CSV vs. MeltCSV's fairly  braindead-simple CSV dialect support).

import re
import sys

p_dyn_col_comment = re.compile(r'^#.*$')
p_dyn_col_real = re.compile(r'^\d+$')
p_col_placeholder = re.compile(r'^.*\?+.*$')


class MeltCSVError(Exception):
    def __init__(self, n_line):
        self.msg = "CSV file format input error on line " + str(n_line)

    def __str__(self):
        return self.msg


class MeltCSVRule:
    def __init__(self, dyn_id, cul_early, cul_later):
        self.dyn_id = dyn_id
        self.cul_early = cul_early
        self.cul_later = cul_later

    def __str__(self):
        return '{}: {} ==> {}'.format(self.dyn_id, self.cul_early, self.cul_later)


def row_warn(f, n_row, msg, error=False):
    msg_type = "ERROR" if error else "WARN"
    f.write("{}: ROW {}: {}\n".format(msg_type, n_row, msg))


def parse_melt_rules(f, fwarn=sys.stdout):
    # Spreadsheet field indices of interest
    DYN = 0
    CUL_EARLY = 3
    CUL_LATER = 4

    rules = []
    n_row = 1

    # Advance past the header row
    f.readline()

    for line in f:
        n_row += 1
        row = line.split(';')
        row = row[:5]

        if len(row) != 5:
            raise MeltCSVError(n_row)

        row[DYN].strip()
        row[CUL_EARLY].strip()
        row[CUL_LATER].strip()

        if len(row[DYN]) == 0 and len(row[CUL_EARLY]) == 0 and len(row[CUL_LATER]) == 0:
            continue  # Blank row

        if len(row[DYN]) == 0 and (len(row[CUL_EARLY]) > 0 or len(row[CUL_LATER]) > 0):
            row_warn(fwarn, n_row, "Dynasty column blank while culture(s) aren't", error=True)
            continue

        if p_dyn_col_comment.match(row[DYN]):
            continue  # Commented-out row

        if not p_dyn_col_real.match(row[DYN]):
            row_warn(fwarn, n_row, 'Malformatted dynasty ID (typo? forget to insert a comment character?)', error=True)
            continue

        # We do know we have a valid dynasty ID field now, at least.

        if len(row[CUL_EARLY]) == 0 or len(row[CUL_LATER]) == 0:
            row_warn(fwarn, n_row, 'Dynasty ID defined but one or more of the culture columns is blank', error=True)
            continue

        if p_col_placeholder.match(row[CUL_EARLY]) or p_col_placeholder.match(row[CUL_EARLY]):
            row_warn(fwarn, n_row, 'Placeholder / Marked TODO')
            continue

        # K, fine. It's really a rule.
        rules.append(MeltCSVRule(int(row[DYN]), row[CUL_EARLY], row[CUL_LATER]))

    return rules
