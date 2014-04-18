
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
    
    static constexpr int32_t MONTH_DAY[12] = {
        31,
        28,
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    };
    
    static constexpr int32_t MONTH_DOY[12] = {
        0,
        31,
        59,
        90,
        120,
        151,
        181,
        212,
        243,
        273,
        304,
        334,
    };

    static constexpr int32_t calc_epoch_days(uint16_t y, uint8_t m, uint8_t d, int factor) {
        return factor * ( 365*y + MONTH_DOY[m] + d );
    }
    
public:
    
    //Date(char* s); // parse date from a mutable NULL-terminated string

    constexpr Date(uint16_t _y, uint8_t _m, uint8_t _d, int factor)
        : epoch_d( calc_epoch_days(_y-1, _m-1, _d-1, factor) ), y(_y), m(_m), d(_d) { }
    
    constexpr Date(int32_t e) : epoch_d(e), y( (e < 0) ? -1*e/365 : e/365 ), m(0), d(0) { }  // FIXME
    
    constexpr uint16_t year()       { return y; }
    constexpr uint8_t  month()      { return m; }
    constexpr uint8_t  day()        { return d; }
    constexpr int32_t  epoch_days() { return epoch_d; }
    
    constexpr bool operator<(const Date& rhs) { return epoch_d < rhs.epoch_d; }
    constexpr bool operator==(const Date& rhs) { return epoch_d == rhs.epoch_d; }
    constexpr Date operator-(const Date& rhs) { return Date(epoch_d - rhs.epoch_d); }
};


#endif

