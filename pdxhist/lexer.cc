
#include <stdio.h>
#include <assert.h>
#include "lexer.h"
#include "scanner.h"
#include "token.h"

bool lexer::next(token* p_tok) {

  uint type;

  if (( type = yylex() ) == 0) {
    /* EOF, so close our filehandle, and signal EOF */
    fclose(_f);
    _f = 0;
    p_tok->line = yylineno;
    return false;
  }

  /* yytext contains token,
     yyleng contains token length,
     yylineno contains line number,
     type contains token ID */

  p_tok->type = type;
  p_tok->line = yylineno;

  if (type == token::QSTR) {
    assert( yyleng > 2 );

    /* trim quote characters from actual string */
    yytext[ yyleng-1 ] = '\0';
    p_tok->text = yytext + 1;
  }
  else {
    p_tok->text = yytext;
  }

  if (type == token::COMMENT) {
    /* if found, strip any trailing '\r' */

    char* last = &yytext[ yyleng-1 ];

    if (*last == '\r')
      *last = '\0';
  }

  return true;
}
