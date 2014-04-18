
#include "FileScanner.h"


/* read a line, chomp off any end-of-line characters, and return it */
char* FileScanner::readline_chomp() {
    char* p = readline();
    if (!p)
        return p;

    char* q = p;
    while (*q) ++q; // to the end (the NULL terminator)
    --q;

    /* precede to chomp off a trailing LF, CRLF, or CR (all possible variants) */

    if (q >= p && *q == '\n') {
        *q = '\0';
        --q;
    }
    
    if (q >= p && *q == '\r')
        *q = '\0';

    return p;
}


/* skip lines of input until line exactly matches given string */
char* FileScanner::skip_until_line(const char* stop) {

    while (readline()) {
        char* s1 = &buf[0];
        const char* s2 = stop;
        
        /* compare the strings, stopping either at their end or a diff */
        while(*s1 && (*s1 == *s2)) s1++, s2++;
        
        if (*s1 == *s2) // strings matched exactly
            return &buf[0];
    }

    return 0;
}

