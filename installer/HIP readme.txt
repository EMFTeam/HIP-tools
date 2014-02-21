====================
Windows Installation

1. Unzip *everything* inside the downloaded .7z archive (normally
   "HIP - <RELEASE DATE>.7z") directly into your mod folder.
2. If on Mac OS X, proceed to the Mac OS X Installation below. If on
   Windows, continue.
3. Run HIP.exe, which was unzipped into your mod folder.
4. Answer the questions the command line asks. Default is "yes" for
   every question.
5. Enable HIP through the launcher and start the game.
6. *Optionally* delete python27.dll, library.zip, HIP.exe, main.py,
   the original .7z archive, and even this file. You will probably
   want to keep at least the original .7z archive, though.

=====================
Mac OS X Installation

1. Unzip *everything* inside the downloaded .7z archive (normally
   "HIP - <RELEASE DATE>.7z") directly into your mod folder.

2. Find the application Terminal that comes with your Mac. It is
   impossible to uninstall and bundled with every Mac. If it's not on
   your Launcher already, then search Finder under Applications for
   Terminal. It should be in a subfolder in Applications with other
   system utilities. Run Terminal.

3. Copy and then paste the following line of text, precisely, into the
   Terminal window:

python "Documents/Paradox Interactive/Crusader Kings II/mod/main.py"

4. If you didn't paste the line-ending as well and the text is just
   sitting there, it's waiting for you to press ENTER. Hit ENTER.
   
5. You should now be running the automatic installer, and your
   experience should be identical to that of Windows, except Terminal
   is a lot more user-friendly than the Windows console.

6. Answer the questions prompted on the command line. Default is "yes"
   for every question.

7. Run CKII. Enable HIP through the launcher, make sure any
   incompatible mods (such as old versions of HIP mods) are
   deselected, and enjoy the game!

Troubleshooting:

If you experience any problems running the installer through Terminal,
execute the following commands on the command prompt, and then
copy/paste their output into your bug report / question on the forums:

First, from a freshly-started Terminal, try running (copy/paste to
make sure you don't make any syntax mistakes):

python "Documents/Paradox Interactive/Crusader Kings II/mod/main.py" -V

If that works, copy all the output from that command (scroll up if you
have to do so) into your forum post.  That tells us everything we need
to know about your system, python version, HIP installer version, etc.

If that doesn't work, the file "main.py" that you were supposed to
extract into your mod folder probably isn't where we expect it to be
for some reason.  Indicate in your post if you have a non-standard
mod folder location, as that would break these instructions. Check for
a "main.py" wherever you DID extract the 7zip archive. Was that in the
right place?  Finally, what output *does* Terminal give you instead of
running the installer?

If the installer ran but could not complete or did something obviously
broken mid-way through, try running it this way and repeating the steps
that made it crash/error:

python "Documents/Paradox Interactive/Crusader Kings II/mod/main.py" -D

This should generate a file called HIP_debug.log in your mod folder which
you can attach on the forums or send in an email to me at:

zijistark@gmail.com

=====================
NOTE:
The following manual instructions are out of date!  Even if you're
using Linux, simply adapt the Mac OS X instructions. You know how to
open a terminal. The rest is the same, except for the location of
your mod folder.

DEPRECATED:

Manual installation for those who cannot run .exe files:
0. Ignore the install instructions above
1. Unzip the modules folder and HIP.mod into your mod folder
2. If on OS X edit HIP.mod and remove the "user_dir" line
3. Create a folder named "Historical Immersion Project"
4. Follow the following order for mod installation. "Copy" means copy/move the *contents* of the folder into the HIP folder, overwriting any conflicts:
	0. If you want to convert to EU4 later, copy the "Converter/Common" folder. Note that conversion of SWMH does not work
	1. If using ARKO armoiries, copy the "ARKOpack_Armoiries" folder
	2. If using ARKO interface, copy the "ARKOpack_Interface folder". If using VIET, delete the gfx/event_pictures folder
	3. If using *any* VIET module, copy the "VIET_Assets" folder
	4. If using Project Balance, copy the "ProjectBalance" folder and the "Converter/PB" folder
	5. If using SWMH, copy the "SWMH" folder
		* If using English title names instead of native, copy the "English SWMH" folder
		* If using Project Balance, copy the "PB + SWMH" folder
	6. If using NBRT+ interface, copy the "NBRT+" folder
		* If not using SWMH, delete Historical Immersion Project\map\terrain.bmp and trees.bmp
		* If not using SWMH, delete Historical Immersion Project\map\terrain\colormap.dds and colormap_water.dds
		* If using ARKO armoiries, also copy the "NBRT+ARKO" folder
	7. If using VIET Traits, copy the "VIET_Traits" folder. Note that this cannot be done together with PB as it is included in PB
	8. If using VIET Events, copy the "VIET_Events" folder
		* If using Project Balance, copy the "PB_VIET_Events" folder
	9. If using VIET Immersion:
		* If you lack any of the portrait DLC, follow the instructions in the VIET_portrait_fix folder
		* If NOT using Project Balance, copy the "VIET_Immersion" folder and the "Converter/VIET" folder. Note that Immersion does not work with SWMH
		* If using Project Balance, copy the "PB_VIET_Immersion" folder. Note that Immersion does not work with SWMH
5. (Optional) Delete the modules folder
6. Enable HIP through the launcher and start the game
