
#ifndef _ZSV_DATE_H_
#define _ZSV_DATE_H_

#include <inttypes.h>

class Date {
    /* can represent negative dates; y/m/d are intepreted negative if epoch_d < 0
       however, this is a bit awkward to query if you're working with the literal
       year, month, or day accessors, as you need to need then also check is_negative().
       luckily, we basically are never interested in y/m/d until we _might_ output them
       as a string. all date comparisons, sorts, indexing, offsets, etc. work with
       the number of days since the epoch, 1.1.1, and they'll also work seamlessly
       with pre-epoch date values. */
       
    int32_t epoch_d; // days since 1.1.1, without consideration of leap years.
    
    /* these values start at 1. the value 0 would technically be an invalid date. */
    uint16_t y;
    uint8_t  m;
    uint8_t  d;
    
public:
    
    Date(char* s); // parse date from a mutable NULL-terminated string
    
    uint16_t year()       const { return y; }
    uint8_t  month()      const { return m; }
    uint8_t  day()        const { return d; }
    int32_t  epoch_days() const { return epoch_d; }
};


#endif

