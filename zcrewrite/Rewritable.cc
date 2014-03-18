
#include "Rewritable.h"
#include "CHFile.h"

void FileLiteral::rewrite(CHFile* p_dest) {
  p_dest->write_buf(_text.c_str(), _text.length());
}
