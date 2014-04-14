
#ifndef _ZSV_SAVEGAME_H_
#define _ZSV_SAVEGAME_H_

#include <string>
using std::string;

class SaveGame {
    string filename;

public:
    SaveGame(const string& filename);
};

#endif

