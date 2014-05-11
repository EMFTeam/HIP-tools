
#include "lexer.h"
#include "token.h"

#include <stdio.h>
#include <exception>

int main(int argc, char** argv) {
  try {
    lexer lex(stdin);
    token tok;

    while (lex.next(&tok)) {
      printf("L%d:%s:%s\n", tok.line, tok.type_name(), tok.text);

      if (tok.type == token::FAIL)
	break;
    }

  }
  catch (std::exception& e) {
    fprintf(stderr, "fatal: %s\n", e.what());
  }

  return 0;
}
