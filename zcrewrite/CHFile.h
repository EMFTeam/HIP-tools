// -*- c++ -*-

#ifndef _MDH_CHFILE_H_
#define _MDH_CHFILE_H_

#include <stdio.h>
#include <string>


typedef unsigned int uint_t;

class CHFile {

  char* _p; // pointer to next character in _cur_line[]
  FILE* _f; // stdio filehandle
  uint_t _n_line; // current line number
  std::string _filename; // copy associated filename

  static const size_t BUF_SZ = 4096;
  char _cur_line[BUF_SZ];

  void parse();

protected:

  void write_buf(const char* buf, uint_t len);
  char* read_line(bool eof_is_error);

  friend class FileLiteral;
  friend class Char;

public:

  CHFile(const char* filename);
  ~CHFile();
};



#endif
