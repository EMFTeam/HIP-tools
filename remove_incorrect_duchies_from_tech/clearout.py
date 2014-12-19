import os

path = "D:\\GitHub\\SWMH\\SWMH\history\\technology\\"
filestopurge = os.listdir(path);
b = open("D:\\GitHub\\SWMH\\SWMH\\common\\landed_titles\\landed_titles.txt", "r")
btext = b.read()
b.close()

for i in filestopurge:
    a = open(path+i, "r")
    atext = a.read()
    alines = atext.split("\n")
    a.close()
    a = open(path+i, "w")
    for j in alines:
        if "d_" in j:
            c = j.strip()
            print c
            if c in btext:
                a.write(j + "\n");
        else:
            a.write(j + "\n");
    a.close()
