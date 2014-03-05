__author__ = 'zijistark'

import os
import codecs
import re

INDENT_UNIT = '\t'



p_opt_quoted = re.compile(r'^(?:"([^"]+)"|([^"\s]+))$')
p_char_end = re.compile(r'^[}]\s*$')

p_bare_comment_or_blank = re.compile(r'^(\s*#.*)|(\s*)$')
p_char_start = re.compile(r'^\s*(\d+)\s*=\s*[{]\s*(#.*)?$')
p_char_culture = re.compile(r'^\s*culture\s*=\s*(?:"([^"]+)"|([^"\s]+))\s*(#.*)?$')
p_char_dynasty = re.compile(r'^\s*dynasty\s*=\s*(?:"(\d+)"|(\d+))\s*(#.*)?$')
p_char_hist_entry_start = re.compile(r'^\s*(\d{1,4})\.(\d{1,2})\.(\d{1,2})\s*=\s*[{]$')
p_char_hist_entry_birth = re.compile(r'^\s*birth\s*=\s*(?:"(?:[^"]+)"|(?:[^"\s]+))')
p_open_brace = re.compile(r'^([^}]*)[{]')
p_close_brace = re.compile(r'^([^{]*)[}]')

class CHParseError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class CHFileLiteral:
    def __init__(self, literal):
        self.literal = literal


class DateVal:  # Assumes string values in constructor
    def __init__(self, y, m, d):
        self.y = int(y)
        self.m = int(m)
        self.d = int(d)
        self.c = '{}.{}.{}'.format(self.y, self.m, self.d)  # Lexicographic-comparable canonical date value

    def __str__(self):
        return self.c


class CommentableVal:
    def __init__(self, val, c=None):
        self.val = val
        self.cmt = c


def dequoteCommentableVal(m):
    return CommentableVal(m.group(2), m.group(3)) if m.group(2) is not None else CommentableVal(m.group(1), m.group(3))


class CHFileCharHistEntry:
    def __init__(self, date):
        self.date = date
        self.elems = []

    def parse(self, ch, chfc, f, n_line):
        buf = ''
        buf_idx = 0
        nest_level = 1
        birth = False
        while nest_level > 0:
            if len(buf) == buf_idx:
                buf = f.readline()
                if len(buf) == 0:  # EOF
                    raise CHParseError("Unexpected EOF while parsing character ID %d [%s: line %d]!" % (chfc.id,
                                                                                                        g_filename,
                                                                                                        n_line))
                n_line += 1
                buf_idx = 0  # Reset start pointer to beginning of new line
                buf = buf.rstrip()
                continue

            # buf is nonempty, buf[buf_idx:] is also nonempty, and we still having matching/consumption to do.

            # Look for a birth statement at nest_level == 1 in case this history entry includes/is a birth date
            if not birth and nest_level == 1:
                m = p_char_hist_entry_birth.match(buf[buf_idx:])
                if m:
                    birth = True
                    assert m.end() > 0
                    buf_idx += m.end()
                    continue

            # Look for a starting brace to increment the nest level, capture interim literal data
            m = p_open_brace.match(buf[buf_idx:])
            if m:
                self.elems.append(CHFileLiteral(m.group()))
                nest_level += 1
                assert m.end() > 0
                buf_idx += m.end()
                continue

            # Look for a closing brace to decrement the nest level, capture interim literal data
            m = p_close_brace.match(buf[buf_idx:])
            if m:
                self.elems.append(CHFileLiteral(m.group()))
                nest_level -= 1
                assert m.end() > 0
                buf_idx += m.end()
                continue

            # Else, it's just literal data/effects, so capture all the remainder
            self.elems.append(buf[buf_idx:])
            buf_idx = len(buf)  # One past end, fully consumed

        # nest_level == 0, return input file line number and whether we included a birth date/effect in this entry
        if buf_idx < len(buf):
            raise CHParseError("Out-of-place trailing characters after character history entry closing brace ["
                               "%s:L%d]!" % (g_filename, n_line))
        return (n_line, birth)


class CHFileChar:
    def __init__(self, id, comment=None):
        self.id = id
        self.comment = comment
        self.start_line = -1
        self.hist_entries = []
        self.elems = []


    def _finalize(self):
        self.dynasty = getattr(self, 'dynasty', CommentableVal(0))  # Default to lowborn dynasty = 0
        if not hasattr(self, 'culture'):
            raise CHParseError('Character ID %d [%s: line %d] has no culture defined!'
                               % (self.id, g_filename, self.start_line))
        if not hasattr(self, 'bdate'):
            raise CHParseError('Character ID %d [%s: line %d] has no birth date defined!'
                               % (self.id, g_filename, self.start_line))


    def parse(self, ch, f, n_line):
        self.start_line = n_line
        ch.log_dbg("Parsing character ID %d [%s:L%d] ..." % (self.id, g_filename, n_line))
        while True:
            line = f.readline()
            if len(line) == 0:  # EOF
                raise CHParseError("Unexpected EOF while parsing character ID %d [%s: line %d]!" % (self.id,
                                                                                                    g_filename,
                                                                                                    n_line))
            n_line += 1
            line = line.rstrip()

            m = p_char_dynasty.match(line)
            if m:
                self.dynasty = dequoteCommentableVal(m)
                continue

            m = p_char_culture.match(line)
            if m:
                self.culture = dequoteCommentableVal(m)
                continue

            m = p_char_hist_entry_start.match(line)
            if m:
                d = DateVal(m.group(1), m.group(2), m.group(3))
                h_ent = CHFileCharHistEntry(d)
                self.hist_entries.append(h_ent)
                (n_line, is_birth) = h_ent.parse(ch, self, f, n_line)
                if is_birth:
                    self.bdate = d
                continue

            m = p_char_end.match(line)
            if m:
                self._finalize()
                ch.log_dbg(str(self.id) + " {\n"
                           + ' dynasty  => ' + str(self.dynasty.val) + "\n"
                           + ' culture  => ' + self.culture.val + "\n"
                           + ' birthday => ' + str(self.bdate) + "\n"
                           + "}\n")
                return n_line

            # Upon no match, record the line as literal data (we don't support all possible character history
            # definition elements, esp. not Paradox scripting history effects, but we record them in-place so that we
            # can put it all back together neatly upon rewrite)
            self.elems.append(CHFileLiteral(line))


class CHFile:
    def __init__(self, ch, filename, path):
        assert os.path.isfile(path)
        self.ch = ch
        self.filename = filename
        self.path = path
        self.elems = []

    def parse(self):
        global g_filename
        g_filename = self.filename
        self.ch.log_info("Parsing file '%s' ..." % g_filename)
        n_line = 0
        with codecs.open(self.path, encoding='cp1252') as f:
            while True:
                line = f.readline()
                if len(line) == 0:  # EOF
                    break
                n_line += 1
                line = line.rstrip()

                m = p_char_start.match(line)
                if m:  # Matched the start of a character definition
                    if m.group(2):
                        comment = m.group(2)
                    else:
                        comment = None

                    id = int(m.group(1))
                    # TODO: check for duplicate ID
                    c = CHFileChar(id, comment)
                    n_line = c.parse(self.ch, f, n_line)
                    self.elems.append(c)
                    continue

                m = p_bare_comment_or_blank.match(line)
                if m:  # Literal data, should be kept in-place on rewrite if possible
                    self.elems.append(CHFileLiteral(m.group()))
                    continue

                raise CHParseError("Unexpected token at %s:%d!" % (self.filename, n_line))

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
        chf = CHFile(self, filename, path)
        chf.parse()

    def parse_dir(self, path):
        assert os.path.isdir(path)
        self.parse_file("test.txt", "./test.txt")
        return
        filenames = os.listdir(path)  # TODO: filter on .txt extension
        for filename in filenames:
            self.parse_file(filename, os.path.join(path, filename))


class Char:
    def __init__(self, id, name, traits, attrs, ):
        self.traits = {}

