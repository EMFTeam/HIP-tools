import os
import re

path = "D:\\GitHub\\SWMH\\SWMH\\history\\provinces\\"
filestoripnamesfrom = os.listdir(path);
mappath = "D:\\GitHub\\SWMH\\SWMH\\map\\definition.csv"
path2 = "D:\\SteamLibrary\\SteamApps\\common\\Crusader Kings II\\history\\provinces\\"
landedpath = "D:\\GitHub\\SWMH\\SWMH\\common\\landed_titles\\landed_titles.txt"

a = open(mappath, "r")
maplines = a.readlines()
a.close()
n = open(landedpath, "r")
o = n.read()
n.close()
a = open(mappath, "w")
for j in filestoripnamesfrom:
    delete = True
    f = open(path+j,'r')
    g = f.readlines()
    f.close()
    for k in g:
        if k[0] != '#':
            delete = False
    if delete == True:
        print j
        os.remove(path+j)
filestoripnamesfrom = os.listdir(path);
filestoripnamesfrom2 = os.listdir(path2);
for i in maplines:
    b = i[0:i.index(';')]
    ba = b+" -"
    c = [x for x in filestoripnamesfrom if (b + " -") == x[:len(ba)]]
    if len(c) == 0:
        c = [x for x in filestoripnamesfrom2 if (b + " -") == x[:len(ba)]]
        if len(c) != 0:
            d = i.split(';')
            c = c[0]
            l = open(path2+c, 'r')
            m = l.read()
            l.close()
            m = m[m.index('title'):]
            m = m[m.index('= ')+2:]
            m = m[:m.index('\n')]
            if m in o:
                d[4] = c[c.index('-')+2:c.index('.')]
            else:
                d[4] = ''
            e = ';'.join(d)
            a.write(e)
        else:
            a.write(i)
    else:
        print b, c
        d = i.split(';')
        c = c[0]
        d[4] = c[c.index('-')+2:c.index('.')]
        e = ';'.join(d)
        a.write(e)
a.close()
    
