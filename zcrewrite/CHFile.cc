
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <pcrecpp.h>
#include "CHFile.h"
#include "error.h"


CHFile::CHFile(const char* filename)
  : _p(0),
    _f(0),
    _n_line(0),
    _filename(filename) {

  if (( _f = fopen(filename, "rb") ) == NULL)
    throw error("Failed to open file: %s: %s", strerror(errno), filename);

  _p = &_cur_line[0]; // still working-out how to present partial line consumption  

  parse();
}

CHFile::~CHFile() {
  if (_f)
    fclose(_f);
}


void CHFile::parse() {
  
  char* line;

  while ( (line = read_line(false)) ) {
    /* read lines and do stuff with them until proper EOF */
  }
}



void CHFile::write_buf(const char* buf, uint_t len) {
  if ( fwrite(buf, 1, len, _f) < len )
    throw error("Write failed: %s: %s", strerror(errno), _filename.c_str());

  // NOTE: we don't currently advance line number on (re)writes
}


char* CHFile::read_line(bool eof_is_error = true) {

  if ( fgets(_p, BUF_SZ, _f) == NULL && feof(_f) == 0)
    throw error("Read failed: %s: %s: line %u", strerror(errno), _filename.c_str(), _n_line);

  /* find end of input, check that it wasn't early (right away), and
     trim any trailing CR-LF or lone LF, if present */

  char* p = _p;

  if (feof(_f)) {
    if (eof_is_error)
      throw error("File ended early: %s: line %u", _filename.c_str(), _n_line);
    else
      return 0;
  }

  // definitely did get data of some kind
  ++_n_line;

  while (*p) { ++p; }

  --p;

  if (*(p-1) == '\n')
    *(--p) = '\0';

  if (p > _p && *(p-1) == '\r')
    *(--p) = '\0';

  return _p;
}
