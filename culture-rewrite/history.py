__author__ = 'zijistark'

import os
import codecs
import re

INDENT_UNIT = '\t'


class Element:
    def __init__(self, comment=None):
        self.comment = comment

    def __str__(self):
        return ' ' + self.comment

    def serialize(self, f, indent=0):
        if indent > 0:
            f.write(INDENT_UNIT * indent)
        s = str(self)
        if s != '':
            f.write(s + '\n')


class CharHistory:
    def __init__(self, log_file=None, log_verbosity=0):
        assert(log_verbosity == 0 or log_file is not None)
        self.log_file = log_file
        self.log_verbosity = log_verbosity
        self.files = {}

    def log_print(self, msg, level):
        if self.log_verbosity >= level:
            self.log_file.write(msg + '\n')
            self.log_file.flush()

    def log_dbg(self, msg):
        self.log_print(msg, 3)

    def log_notice(self, msg):
        self.log_print(msg, 2)

    def log_info(self, msg):
        self.log_print(msg, 1)

    def parse_file(self, filename, path):
        assert os.path.isfile(path)
        with codecs.open(path, encoding='cp1252') as f:
            file_elems = self.files[filename] = []
            p_comment = re.compile(r'^\s*#.*$')
            p_char_start = re.compile(r'^\s*(\d+)\s*=\s*\{\s*$')
            for ln in f:
                ln = ln.strip()
                m = p_comment.match(ln)
                if m:
                    file_elems.append(m.group())  # Only a comment on this line
                    continue
                m = p_char_start.match(ln)
                if m:
                    file_elems.append(int(m.group(1)))
                    continue

    def parse_dir(self, path):
        assert os.path.isdir(path)
        filenames = os.listdir(path)
        for filename in filenames:
            self.parse_file(filename, os.path.join(path, filename))


class Char:
    def __init__(self, id, name, traits, attrs, ):
        self.traits = {}

