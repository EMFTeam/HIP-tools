// -*- c++ -*-

#ifndef _MDH_REWRITABLE_H_
#define _MDH_REWRITABLE_H_

#include <string>

class CHFile;

class Rewritable {
public:
  virtual void rewrite(CHFile* p_dest) = 0;
  virtual ~Rewritable() { }
};


class FileLiteral : public Rewritable {
  std::string _text;
  
public:
  FileLiteral(const char* text) : _text(text) { }
  void rewrite(CHFile* p_dest);
};


#endif
