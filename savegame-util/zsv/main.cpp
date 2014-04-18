
#include "SaveGame.h"
#include <stdio.h>

int main(int argc, char** argv) {

    if (argc < 2) {
        fprintf(stderr, "Specify a save file, yo!\n");
        return -1;
    }
    
    try {
        SaveGame sg( argv[1] );
    }
    catch (std::exception& e) {
        fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }
    
    return 0;
}

