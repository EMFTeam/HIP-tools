
#ifndef _ZSV_FILESCANNER_H_
#define _ZSV_FILESCANNER_H_

#include <stdio.h>
#include <string.h>


class FileScanner {
    FILE* f;
    unsigned int n_line;
    char buf[512-sizeof(n_line)-sizeof(f)];
    
public:
    
    FileScanner(FILE* _f) : f(_f), n_line(0) {
        buf[0] = '\0';
    }
    
    ~FileScanner() {
        if (f)
           fclose(f);

        f = 0;
    }
    
    FILE* handle() const { return f; }
    unsigned int line() const { return n_line; }

    /* raw line input */
    char* readline() {
        if (!fgets(&buf[0], sizeof(buf), f))
            return 0;

        ++n_line;
        return &buf[0];
    }

    /* EOL characters stripped from next line (Windows CRLF assumed) */
    char* next() {
        if (!readline())
            return 0;

        char* eol = strrchr(&buf[0], '\r');

        if (eol)
            *eol = '\0';
        
        return &buf[0];
    }
    
    /* consume n lines blindly */
    bool eat() {
        return readline();
    }
    
    bool eat(unsigned int n) {
        for (unsigned int i = n; i > 0; --i)
            if (!eat()) return false;
    }
    
    /* skip lines until see literal string stop */
    char* skip_until(const char* stop) {
        while (readline()) {
            if (strcmp(&buf[0], stop) == 0)
                return &buf[0];
        }
        
        return 0;
    }
};


#endif

