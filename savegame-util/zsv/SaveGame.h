
#ifndef _ZSV_SAVEGAME_H_
#define _ZSV_SAVEGAME_H_

#include <string>
using std::string;

#include "Error.h"

class SaveGame {
    string filename;

public:
    struct OpenError : public std::runtime_error {
        OpenError() : std::runtime_error("Failed to open savegame file: " + string(strerror(errno))) { }
    };


    SaveGame(const string& filename);
};

#endif

