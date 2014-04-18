
#include "SaveGame.h"
#include "FileScanner.h"
#include "Error.h"


SaveGame::SaveGame(const string& _filename) : filename(_filename) {

    FILE* fh = fopen(filename.c_str(), "rb");
    
    if (!fh)
        throw OpenError();
    
    FileScanner f(fh);

}
