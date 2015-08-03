import os
import re

characteridregex = re.compile('^([0-9]+) ?=', re.MULTILINE)
path = "D:\\g\\SWMH-BETA\\SWMH\\history\\characters\\"
filestoaddto = os.listdir(path);
vanillapath = "D:\\SteamLibrary\\SteamApps\\common\\Crusader Kings II\\history\\characters\\"
filestostealfrom = os.listdir(vanillapath);

allswmhchars=""
for i in filestoaddto:
    b = open(path+i, "r")
    btext = b.read()
    b.close()
    allswmhchars += btext
    print "73931" in btext, i
for i in filestostealfrom:
    debug = False
    exactMatch = True
    characterstoadd=""
    a = open(vanillapath+i, "r")
    atext = a.read()
    a.close()
    iterator = characteridregex.finditer(atext)
    for match in iterator:
        index = match.end()
        index = atext.find('{', index) + 1
        counter = 1
        while counter != 0:
            if atext[index] == '{':
                counter += 1
            elif atext[index] == '}':
                counter -= 1
            index += 1
        characterid = match.group(1)
        character = atext[match.start():index]
        if characterid not in allswmhchars:
            characterstoadd += character + '\n'
        if characterid in allswmhchars:
            exactMatch = False
    if debug:
        print i
        print characterstoadd
    if exactMatch:
        print i
        print "Keeping vanilla file"
    if not exactMatch:
        c = open(path+i, "a")
        c.write(characterstoadd)
        c.close()
