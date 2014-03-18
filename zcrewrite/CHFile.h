// -*- c++ -*-

#ifndef _MDH_CHFILE_H_
#define _MDH_CHFILE_H_

#include <stdio.h>
#include <string>
#include <pcrecpp.h>

typedef unsigned int uint_t;
typedef pcrecpp::RE regex_t;

/* currently, a CHFile can be used for both input and output,
   reversing the read-write mode of its underlying FILE object when
   rewriting. the interface support for this exists only insofar as
   Rewritable implementations at the moment.
*/
class CHFile {

  char* p; // pointer to next character in _cur_line[] (unused)
  FILE* f; // stdio filehandle
  uint_t n_line; // current line number
  std::string fname; // copy associated filename

  static const size_t BUF_SZ = 4096;
  char in_buf[BUF_SZ];

  static regex_t pat_literal;
  static regex_t pat_char_start;

  void parse();

protected:

  void write_buf(const char* buf, uint_t len);
  char* read_line(bool eof_is_error);

  /* these classes can twiddle w/ CHFile state by directly
     read/writing from it. this list should include any Rewritable. */
  friend class FileLiteral;
  friend class Char;

public:

  CHFile(const char* filename);
  ~CHFile();
};



#endif
