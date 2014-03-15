// -*- c++ -*-

#ifndef _MDH_TOKEN_H_
#define _MDH_TOKEN_H_

typedef unsigned int uint;


struct token {
  uint  type;
  char* text;
  //  const char* filename;
  uint line;

  /* token type identifier constants, sequentially defined starting
     from 1 and ending with the FAIL token */
  static const uint INT     = 1;  // integer string sequence
  static const uint EQ      = 2;  // =
  static const uint OPEN    = 3;  // {
  static const uint CLOSE   = 4;  // }
  static const uint STR     = 5;  // "bareword" style string
  static const uint QSTR    = 6;  // quoted string
  static const uint DATE    = 7;  // date string of the form 867.1.1, loosely
  static const uint COMMENT = 8;  // hash-style comment (starts with '#')
  static const uint FLOAT   = 9;
  static const uint FAIL    = 10; // anything the ruleset couldn't match

  static const char* TYPE_MAP[];

  const char* type_name() const { return TYPE_MAP[type]; }
};


#endif
