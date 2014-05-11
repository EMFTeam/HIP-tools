// -*- c++ -*-

#ifndef _MDH_LEXER_H_
#define _MDH_LEXER_H_

#include <stdio.h>
#include "scanner.h"

/* simple API/namespace around the flex-generated C-style global
   scanner symbols (lexer is not presently implemented for
   reentrant-safety, but this API wraps that) as well as safely
   closing the wrapped stdio file for which it assumes ownership upon
   construction.

   for convenience, a filename can be associated with the lexer object
   to allow passing a reference to the lexer around on the stack and
   always having the filename associated with the current line number.
   note that line numbering is relative to the state of the stream at
   the time at which it was transferred to the lexer (it could be
   nothing else without forcing only pure filesystem objects rather
   than streams like stdin or pipes to be used). also for convenience,
   lexer can be constructed only with a filename, and it will open the
   file and setup the file stream for the scanner.

   naturally, this is also the namespace for the token type IDs that
   the scanner returns whenever it successfully matches a pattern. a
   symbolic TK_EOF represents the end-of-file "token."

   TODO: lexical errors are handled where and how?
*/

class token;

class lexer {

  FILE* _f;

public:

  lexer(FILE* f) : _f(f) {
    yyin = f;
  }

  ~lexer() {
    if (_f)
      fclose(_f);
  }

  bool next(token* p_tok);
};


#endif
