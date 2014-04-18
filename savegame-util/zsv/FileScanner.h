
#ifndef _ZSV_FILESCANNER_H_
#define _ZSV_FILESCANNER_H_

#include <stdio.h>
#include <string.h>


class FileScanner {
    FILE* f;
    unsigned int n_line;
    char buf[512-sizeof(n_line)-sizeof(f)];
    
public:
    
    FileScanner(FILE* _f) : f(_f), n_line(0) { *buf = '\0'; }
    
    FILE* handle() const { return f; }
    unsigned int line() const { return n_line; }

    /* raw line input */
    char* readline() {
        if (!fgets(&buf[0], sizeof(buf), f))
            return 0;

        ++n_line;
        return &buf[0];
    }

    /* line input w/ EOL character(s) stripped (supports all EOL variants) */
    char* readline_chomp();
    
    /* consume n lines blindly */
    bool skip_line() { return readline(); }
    
    bool skip_lines(unsigned int n) {
        for (unsigned int i = n; i > 0; --i) if (!skip_line()) return false;
    }
    
    /* skip lines until see literal string stop */
    char* skip_until_line(const char* stop);
};


#endif

