
#include <stdio.h>
#include "CHFile.h"

int main(int argc, char** argv) {

  if (argc != 2) {
    fprintf(stderr, "supply a single character history file, yo!\n");
    return -1;
  }

  try {
    CHFile cf(argv[1]);

  }
  catch (std::exception& e) {
    fprintf(stderr, "Fatal: %s\n", e.what());
    return 1;
  }

  return 0;
}
