__author__ = 'zijistark'

import os
import codecs
import re

INDENT_UNIT = '\t'

p_date = re.compile(r'^(\d{1,4})\.(\d{1,2})\.(\d{1,2})$')
p_txt_file = re.compile(r'^.*?\.txt$')
p_opt_quoted = re.compile(r'^(?:"([^"]+)"|([^"\s]+))$')
p_bare_comment_or_blank = re.compile(r'^(\s*#.*)|(\s*)$')
p_char_start = re.compile(r'^\s*(\d+)\s*=\s*\{\s*(#.*)?$')
p_char_end = re.compile(r'^\}\s*$')
p_char_culture = re.compile(r'^\s*culture\s*=\s*(?:"([^"]+)"|([^"\s]+))\s*(#.*)?$')
p_char_name = re.compile(r'^\s*name\s*=\s*(?:"([^"]+)"|([^"\s]+))\s*(#.*)?$')
p_char_dynasty = re.compile(r'^\s*dynasty\s*=\s*(?:"(\d+)"|(\d+))\s*(#.*)?$')
p_char_hist_entry_start = re.compile(r'^\s*(\d{1,4})\.(\d{1,2})\.(\d{1,2})\s*=\s*\{')  # NOTE: Captures no comment
p_char_hist_entry_birth = re.compile(r'^\s*birth\s*=\s*(?:"(?:[^"]+)"|(?:[^"\s]+))')  # NOTE: Captures no comment
p_open_brace = re.compile(r'^([^}]*)\{')
p_close_brace = re.compile(r'^([^{]*)\}')
p_single_line_one_block = re.compile(r'.*\{.*\}')  # Used to detect an unsupported parse case for top-level char blocks

class CHParseError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class CHFileLiteral:
    def __init__(self, literal):
        self.literal = literal

    def rewrite(self, f):
        f.write(self.literal)
        f.write('\n')


class CHFileLiteralPart:  # Identical but without an implied EOL
    def __init__(self, literal):
        self.literal = literal

    def rewrite(self, f):
        f.write(self.literal)


class DateVal:  # Assumes string values in constructor
    def __init__(self, y, m, d):
        self.y = int(y)
        self.m = int(m)
        self.d = int(d)
        self.c = '{}.{}.{}'.format(self.y, self.m, self.d)  # Lexicographic-comparable canonical date value

    def __str__(self):  # sorted(dates) should work as well as <, >, etc.
        return self.c


class CommentableVal:
    def __init__(self, val, c=None):
        self.val = val
        self.cmt = c


def dequoteCommentableVal(m):
    return CommentableVal(m.group(2), m.group(3)) if m.group(2) is not None else CommentableVal(m.group(1), m.group(3))


# TODO: Ought be commentable (the start line; the contents are already comment-preserved, of course)
class CHFileCharHistEntry:
    def __init__(self, date):
        self.date = date
        self.elems = []

    def rewrite(self, f):
        f.write('\t%s = {\n' % str(self.date))
        for e in self.elems:
            e.rewrite(f)

    def parse(self, ch, chfc, f, n_line):
        buf = ''
        buf_idx = 0  # Index into buf for current parsing position
        nest_level = 1  # Already started the history entry, so we're already nested by 1 level
        birth = False  # Have we seen a birth history effect in this entry?

        while nest_level > 0:
            if len(buf) == buf_idx:  # Parsing has reached the end of our useful buffered input
                buf = f.readline()
                if len(buf) == 0:  # EOF
                    raise CHParseError("Unexpected EOF while parsing character ID %d [%s: line %d]!" % (chfc.id,
                                                                                                        g_filename,
                                                                                                        n_line))
                n_line += 1
                buf_idx = 0  # Reset index to beginning of new line
                buf = buf.rstrip()

                chfc.literal_elems.append(CHFileLiteral(buf))  # Make a literal copy for our dirty-marking mechanism

                continue  # Hopefully that gave us something with which to work, try again.

            # buf is nonempty, buf[buf_idx:] is also nonempty, so we still having matching/consumption to do.

            # Look for a birth statement at nest_level == 1 in case this history entry includes/is a birth date
            if nest_level == 1:
                m = p_char_hist_entry_birth.match(buf[buf_idx:])
                if m:
                    if birth:
                        raise CHParseError("Multiple birth-date history effects for character ID %d [%s: line %d]!"
                                           % (chfc.id, g_filename, n_line))  #Could still be multiple from diff entries.
                    birth = True
                    buf_idx += m.end()
                    self.elems.append(CHFileLiteral('\t\tbirth=yes'))
                    continue

            # Look for a starting brace to increment the nest level, capture interim literal data
            m = p_open_brace.match(buf[buf_idx:])
            if m:
                nest_level += 1
                buf_idx += m.end()
                if buf_idx < len(buf):  # Oh, but there's MORE!
                    self.elems.append(CHFileLiteralPart(m.group()))
                else:
                    self.elems.append(CHFileLiteral(m.group()))
                continue

            # Look for a closing brace to decrement the nest level, capture interim literal data
            m = p_close_brace.match(buf[buf_idx:])
            if m:
                nest_level -= 1
                buf_idx += m.end()
                if buf_idx < len(buf):  # Oh, but there's YET MORE!
                    self.elems.append(CHFileLiteralPart(m.group()))
                else:
                    self.elems.append(CHFileLiteral(m.group()))
                continue

            # Else, it's just literal data/effects, so capture all the remainder (no change in brace nesting)
            self.elems.append(CHFileLiteral(buf[buf_idx:]))
            buf_idx = len(buf)  # One past end, fully consumed

#        if buf_idx < len(buf):
#            raise CHParseError("Out-of-place trailing characters after character history entry closing brace ["
#                               "%s:L%d]!" % (g_filename, n_line))

        # nest_level == 0, return input file line number and whether we included a birth date/effect in this entry
        return (n_line, birth)


class CHFileChar:
    def __init__(self, id, comment=None):
        self.id = id
        self.comment = comment
        self.start_line = -1
        self.hist_entries = []
        self.elems = []
        self.literal_elems = []  # Original string rep. of each line of the character, used for output when !self.dirty
        self.dirty = False  # Has the object been modified by a transform rule? Used to minimize text diff on rewrite.


    def _finalize(self):
        self.dynasty = getattr(self, 'dynasty', CommentableVal(u'0'))  # Default to lowborn dynasty = 0
        if not hasattr(self, 'culture'):
            raise CHParseError('Character ID %d [%s: line %d] has no culture defined!'
                               % (self.id, g_filename, self.start_line))
        if not hasattr(self, 'name'):
            raise CHParseError('Character ID %d [%s: line %d] has no given name defined!'
                               % (self.id, g_filename, self.start_line))
        if not hasattr(self, 'bdate'):
            raise CHParseError('Character ID %d [%s: line %d] has no birth date defined!'
                               % (self.id, g_filename, self.start_line))


    def rewrite(self, f):  # Must be called post object-finalization (which happens immediately after successful parse)

        if self.comment is None:
            f.write('%d = {\n' % self.id)
        else:
            f.write('%d = {  %s\n' % (self.id, self.comment))

        if self.dirty:

            if self.name.cmt is None:
                f.write('\tname="{}"\n'.format(self.name.val))
            else:
                f.write('\tname="{}"  {}\n'.format(self.name.val, self.name.cmt))

            if self.dynasty.val != u'0':  # Don't print explicit dynasty info for lowborns
                if self.dynasty.cmt is None:
                    f.write('\tdynasty={}\n'.format(self.dynasty.val))
                else:
                    f.write('\tdynasty={}  {}\n'.format(self.dynasty.val, self.dynasty.cmt))

            if self.culture.cmt is None:
                f.write('\tculture="{}"\n'.format(self.culture.val))
            else:
                f.write('\tculture="{}"  {}\n'.format(self.culture.val, self.culture.cmt))

            for e in self.elems:
                e.rewrite(f)

            for h in self.hist_entries:
                h.rewrite(f)

            f.write('}\n')

        else:
            # Straight-up copy of the character definition block, only possible difference being CRLF->LF conversion
            # and [currently-- I might disable it] stripping of any unnecessary trailing whitespace on lines.
            for e in self.literal_elems:
                e.rewrite(f)


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

            # Always make an exact copy of the original line (minus the whitespace/EOL normalization above) of the
            # line in the likely case that we never modify this character object and thus can trivially do its rewrite
            # with a zero text diff.
            self.literal_elems.append(CHFileLiteral(line))

            m = p_char_dynasty.match(line)
            if m:
                self.dynasty = dequoteCommentableVal(m)
                continue

            m = p_char_culture.match(line)
            if m:
                self.culture = dequoteCommentableVal(m)
                continue

            m = p_char_name.match(line)
            if m:
                self.name = dequoteCommentableVal(m)
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

                # Index
                ch.chars[self.id] = self

                if self.dynasty.val in ch.chars_by_dynasty:
                    ch.chars_by_dynasty[self.dynasty.val].append(self)
                else:
                    ch.chars_by_dynasty[self.dynasty.val] = [ self ]

                ch.log_dbg(str(self.id) + " {\n"
                           + ' dynasty  => ' + str(self.dynasty.val) + "\n"
                           + ' culture  => ' + str(self.culture.val) + "\n"
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

    def rewrite(self, basedir):
        path = os.path.join(basedir, self.filename)
        with codecs.open(path, mode='w', encoding='cp1252') as f:
            for e in self.elems:
                e.rewrite(f)

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

                    if id in self.ch.chars:
                        raise CHParseError("Duplicate character ID found at %s: line %d!" % (g_filename, n_line))

                    c = CHFileChar(id, comment)
                    n_line = c.parse(self.ch, f, n_line)
                    self.elems.append(c)
                    continue

                m = p_bare_comment_or_blank.match(line)
                if m:  # Literal data, should be kept in-place on rewrite if possible
                    self.elems.append(CHFileLiteral(m.group()))
                    continue

                # Or else...
                raise CHParseError("Unexpected token at %s: line %d!" % (g_filename, n_line))


class CharHistory:
    def __init__(self, log_file=None, log_verbosity=0):
        assert(log_verbosity == 0 or log_file is not None)
        self.log_file = log_file
        self.log_verbosity = log_verbosity
        self.files = {}  # Parsed character history files, indexed by base filename
        self.chars = {}  # Objects indexed by ID
        self.chars_by_dynasty = {}  # Object list indexed by dynasty ID

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
        if filename in self.files:
            raise CHParseError("Conflicting filenames '%s' added to single character history database" % filename)
        chf = CHFile(self, filename, path)
        chf.parse()
        self.files[filename] = chf

    def parse_dir(self, path):
        assert os.path.isdir(path)
        filenames = os.listdir(path)
        for filename in filenames:
            m = p_txt_file.match(filename)
            if m:
                self.parse_file(filename, os.path.join(path, filename))
            else:
                self.log_notice("Skipping possible history file '%s' due to lack of a '.txt' extension" % filename)


