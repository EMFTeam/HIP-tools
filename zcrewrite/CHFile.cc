
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <pcrecpp.h>
#include "CHFile.h"
#include "error.h"


regex_t CHFile::pat_literal( R"(^(\s*#.*)|(\s*)$)" );
regex_t CHFile::pat_char_start( R"(^\s*(\d+)\s*=\s*[{]\s*(#.*)?$)" );


CHFile::CHFile(const char* filename)
  : p(0),
    f(0),
    n_line(0),
    fname(filename) {

  /* before doing anything, check that our statically-initialized
     patterns didn't fail to compile. Google's C++ interface to
     libpcre (pcrecpp) is a little weird in this respect (and others,
     frankly-- makes me wonder if I wouldn't just find direct usage of
     the C interface easier). */

  if (pat_literal.error().length())
    throw error("Internal error: could not compile RE 'literal': %s: %s",
		pat_literal.error().c_str(),
		pat_literal.pattern().c_str());

  if (pat_char_start.error().length())
    throw error("Internal error: could not compile RE 'char_start': %s: %s",
		pat_char_start.error().c_str(),
		pat_char_start.pattern().c_str());

  if (( f = fopen(filename, "rb") ) == NULL)
    throw error("Failed to open file: %s: %s", strerror(errno), filename);

  p = &in_buf[0]; // still working-out how to present partial line consumption  

  parse();
}

CHFile::~CHFile() {
  if (f)
    fclose(f);
}


void CHFile::parse() {
  
  char* line;

  while ( (line = read_line(false)) ) {
    /* read lines and do stuff with them until proper EOF */

    
  }
}



void CHFile::write_buf(const char* buf, uint_t len) {
  if ( fwrite(buf, 1, len, f) < len )
    throw error("Write failed: %s: %s", strerror(errno), fname.c_str());

  // NOTE: we don't currently advance line number on (re)writes
}


char* CHFile::read_line(bool eof_is_error = true) {

  if ( fgets(p, BUF_SZ, f) == NULL && feof(f) == 0)
    throw error("Read failed: %s: %s: line %u", strerror(errno), fname.c_str(), n_line);

  /* find end of input, check that it wasn't early (right away), and
     trim any trailing CR-LF or lone LF, if present */

  if (feof(f)) {
    if (eof_is_error)
      throw error("File ended early: %s: line %u", fname.c_str(), n_line);
    else
      return 0;
  }

  // definitely did get data of some kind
  ++n_line;

  char* q = p;

  while (*q) { ++q; } // advance to end

  if (*(q-1) == '\n')
    *(--q) = '\0';

  if (q > p && *(q-1) == '\r')
    *(--q) = '\0';

  return p;
}
