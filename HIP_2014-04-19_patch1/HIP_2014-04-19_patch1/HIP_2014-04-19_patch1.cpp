// HIP_2014-04-19_patch1.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"


const char* files[] = {
	"./VIET_Immersion/common/history/provinces/883 - Gondar.txt",
	"./VIET_Immersion/vanilla/history/titles/d_east_african_pagan_reformed.txt",
	"./VIET_Events/common/event_modifiers/VIET_culture_mechanic_modifiers.txt",
	"./VIET_Events/common/event_modifiers/VIET_event_modifiers.txt",
	"./VIET_portrait_fix/VIET/common/cultures/00_cultures.txt", // removing whole dir
	"./VIET_portrait_fix/VIET/common/cultures/altaic.txt",
	"./VIET_portrait_fix/VIET/common/cultures/andamanese.txt",
	"./VIET_portrait_fix/VIET/common/cultures/arabic.txt",
	"./VIET_portrait_fix/VIET/common/cultures/baltic.txt",
	"./VIET_portrait_fix/VIET/common/cultures/byzantine.txt",
	"./VIET_portrait_fix/VIET/common/cultures/celtic.txt",
	"./VIET_portrait_fix/VIET/common/cultures/central_african.txt",
	"./VIET_portrait_fix/VIET/common/cultures/central_germanic.txt",
	"./VIET_portrait_fix/VIET/common/cultures/dravidian_group.txt",
	"./VIET_portrait_fix/VIET/common/cultures/east_african.txt",
	"./VIET_portrait_fix/VIET/common/cultures/east_asian.txt",
	"./VIET_portrait_fix/VIET/common/cultures/east_slavic.txt",
	"./VIET_portrait_fix/VIET/common/cultures/finno_ugric.txt",
	"./VIET_portrait_fix/VIET/common/cultures/gallic.txt",
	"./VIET_portrait_fix/VIET/common/cultures/himalayan.txt",
	"./VIET_portrait_fix/VIET/common/cultures/iberian.txt",
	"./VIET_portrait_fix/VIET/common/cultures/indian.txt",
	"./VIET_portrait_fix/VIET/common/cultures/indo_aryan.txt",
	"./VIET_portrait_fix/VIET/common/cultures/iranian.txt",
	"./VIET_portrait_fix/VIET/common/cultures/israelite.txt",
	"./VIET_portrait_fix/VIET/common/cultures/latin.txt",
	"./VIET_portrait_fix/VIET/common/cultures/magyar.txt",
	"./VIET_portrait_fix/VIET/common/cultures/mesoamerican.txt",
	"./VIET_portrait_fix/VIET/common/cultures/north_african.txt",
	"./VIET_portrait_fix/VIET/common/cultures/north_germanic.txt",
	"./VIET_portrait_fix/VIET/common/cultures/papuan.txt",
	"./VIET_portrait_fix/VIET/common/cultures/south_slavic.txt",
	"./VIET_portrait_fix/VIET/common/cultures/southeast_asian.txt",
	"./VIET_portrait_fix/VIET/common/cultures/taiwanese.txt",
	"./VIET_portrait_fix/VIET/common/cultures/west_african.txt",
	"./VIET_portrait_fix/VIET/common/cultures/west_germanic.txt",
	"./VIET_portrait_fix/VIET/common/cultures/west_slavic.txt",
	"./VIET_Immersion/common/common/cultures/altaic.txt",
	"./VIET_Immersion/common/common/cultures/andamanese.txt",
	"./VIET_Immersion/common/common/cultures/arabic.txt",
	"./VIET_Immersion/common/common/cultures/baltic.txt",
	"./VIET_Immersion/common/common/cultures/byzantine.txt",
	"./VIET_Immersion/common/common/cultures/celtic.txt",
	"./VIET_Immersion/common/common/cultures/central_african.txt",
	"./VIET_Immersion/common/common/cultures/central_germanic.txt",
	"./VIET_Immersion/common/common/cultures/dravidian_group.txt",
	"./VIET_Immersion/common/common/cultures/east_african.txt",
	"./VIET_Immersion/common/common/cultures/east_asian.txt",
	"./VIET_Immersion/common/common/cultures/east_slavic.txt",
	"./VIET_Immersion/common/common/cultures/finno_ugric.txt",
	"./VIET_Immersion/common/common/cultures/gallic.txt",
	"./VIET_Immersion/common/common/cultures/himalayan.txt",
	"./VIET_Immersion/common/common/cultures/iberian.txt",
	"./VIET_Immersion/common/common/cultures/indo_aryan.txt",
	"./VIET_Immersion/common/common/cultures/iranian.txt",
	"./VIET_Immersion/common/common/cultures/israelite.txt",
	"./VIET_Immersion/common/common/cultures/latin.txt",
	"./VIET_Immersion/common/common/cultures/magyar.txt",
	"./VIET_Immersion/common/common/cultures/mesoamerican.txt",
	"./VIET_Immersion/common/common/cultures/north_african.txt",
	"./VIET_Immersion/common/common/cultures/north_germanic.txt",
	"./VIET_Immersion/common/common/cultures/papuan.txt",
	"./VIET_Immersion/common/common/cultures/south_slavic.txt",
	"./VIET_Immersion/common/common/cultures/southeast_asian.txt",
	"./VIET_Immersion/common/common/cultures/taiwanese.txt",
	"./VIET_Immersion/common/common/cultures/west_african.txt",
	"./VIET_Immersion/common/common/cultures/west_germanic.txt",
	"./VIET_Immersion/common/common/cultures/west_slavic.txt",
	"./VIET_portrait_fix/PB/common/cultures/altaic.txt",
	"./VIET_portrait_fix/PB/common/cultures/andamanese.txt",
	"./VIET_portrait_fix/PB/common/cultures/arabic.txt",
	"./VIET_portrait_fix/PB/common/cultures/baltic.txt",
	"./VIET_portrait_fix/PB/common/cultures/byzantine.txt",
	"./VIET_portrait_fix/PB/common/cultures/celtic.txt",
	"./VIET_portrait_fix/PB/common/cultures/central_african.txt",
	"./VIET_portrait_fix/PB/common/cultures/central_germanic.txt",
	"./VIET_portrait_fix/PB/common/cultures/dravidian_group.txt",
	"./VIET_portrait_fix/PB/common/cultures/east_african.txt",
	"./VIET_portrait_fix/PB/common/cultures/east_asian.txt",
	"./VIET_portrait_fix/PB/common/cultures/east_slavic.txt",
	"./VIET_portrait_fix/PB/common/cultures/finno_ugric.txt",
	"./VIET_portrait_fix/PB/common/cultures/gallic.txt",
	"./VIET_portrait_fix/PB/common/cultures/himalayan.txt",
	"./VIET_portrait_fix/PB/common/cultures/iberian.txt",
	"./VIET_portrait_fix/PB/common/cultures/indian.txt",
	"./VIET_portrait_fix/PB/common/cultures/indo_aryan.txt",
	"./VIET_portrait_fix/PB/common/cultures/iranian.txt",
	"./VIET_portrait_fix/PB/common/cultures/israelite.txt",
	"./VIET_portrait_fix/PB/common/cultures/latin.txt",
	"./VIET_portrait_fix/PB/common/cultures/magyar.txt",
	"./VIET_portrait_fix/PB/common/cultures/mesoamerican.txt",
	"./VIET_portrait_fix/PB/common/cultures/north_african.txt",
	"./VIET_portrait_fix/PB/common/cultures/north_germanic.txt",
	"./VIET_portrait_fix/PB/common/cultures/papuan.txt",
	"./VIET_portrait_fix/PB/common/cultures/PB_cultures.txt",
	"./VIET_portrait_fix/PB/common/cultures/south_slavic.txt",
	"./VIET_portrait_fix/PB/common/cultures/southeast_asian.txt",
	"./VIET_portrait_fix/PB/common/cultures/taiwanese.txt",
	"./VIET_portrait_fix/PB/common/cultures/west_african.txt",
	"./VIET_portrait_fix/PB/common/cultures/west_germanic.txt",
	"./VIET_portrait_fix/PB/common/cultures/west_slavic.txt",
};

const char* dirs[] = {
	"VIET_portrait_fix/VIET/common/cultures",
	"VIET_portrait_fix/VIET/common",
	"VIET_portrait_fix/VIET",
	"VIET_Events/common/event_modifiers",
};


int main(int argc, const char** argv)
{
	
	if (_chdir("modules") != 0) {
		fprintf(stderr, "could not switch to modules/ folder: %s\n", strerror(errno));
		return 1;
	}

	// remove files
	for (unsigned int i = 0; i < sizeof(files)/sizeof(*files); ++i) {
		const char* filename = files[i];
		if (_unlink(filename) != 0 && errno != ENOENT) {
			fprintf(stderr, "could not delete file: %s: %s\n", strerror(errno), filename);
			return 1;
		}
	}

	// remove dirs
	for (unsigned int i = 0; i < sizeof(dirs)/sizeof(*dirs); ++i) {
		const char* filename = dirs[i];
		if (_rmdir(filename) != 0 && errno != ENOENT) {
			fprintf(stderr, "could not delete folder: %s: %s\n", strerror(errno), filename);
			return 1;
		}
	}

	// rename VIET_portrait_fix/vanilla -> VIET_portrait_fix/VIET (latter now deleted)

	if (_chdir("VIET_portrait_fix") != 0) {
		fprintf(stderr, "could not switch to modules/VIET_portrait_fix/ folder: %s\n", strerror(errno));
		return 1;
	}

	if (rename("vanilla", "VIET") != 0 && errno == EINVAL) {
		fprintf(stderr, "in folder modules/VIET_portrait_fix/: could not rename vanilla/ folder to VIET/ folder: %s\n", strerror(errno));
		return 1;
	}

	printf("VIET patch for the HIP 2014-04-19 official release applied successfully.\n");
	printf("[Re]install any VIET-related mod combinations via the standard installer.\n\n");
	printf("Press any key to exit.\n");
	fflush(stdout);

	_getch();

	return 0;
}

