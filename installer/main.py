def enableMod(name):
    if language == "f":
        answer = raw_input("Voulez-vous installer %s ? [oui]" % name).lower()
    elif language == "e":
        answer = raw_input("Deseas instalar %s? [si]" % name).lower()
    else:
        answer = raw_input("Do you want to install %s? [yes]" % name).lower()
    if answer == "" or answer == "y" or answer == "yes" or answer == "oui" or answer == "o" or answer == "s" or answer == "si":
        return True
    return False

def moveFolder(folder):
    if language == "f":
        print("Fusion repertoire " + folder)
    elif language == "e":
        print("Carpeta de combinacion " + folder)
    else:
        print("Merging folder " + folder)
    for root, dirs, files in os.walk("modules/"+folder):
        for dir in dirs:
            if not os.path.exists("%s/%s" % (root.replace("modules/"+folder, targetFolder),dir)):
                os.makedirs(root.replace("modules/"+folder, targetFolder)+"/"+dir)
        for file in files:
            if move:
                shutil.move("%s/%s" % (root, file), "%s/%s" % (root.replace("modules/"+folder, targetFolder), file))
            else:
                shutil.copy("%s/%s" % (root, file), "%s/%s" % (root.replace("modules/"+folder, targetFolder), file))

try:
    import os
    import shutil
    import sys, traceback

    version = open("modules/version.txt").readline().strip()
    VIETversion = open("modules/VIET_Assets/version.txt").readline().strip()
    PBversion = open("modules/ProjectBalance/version.txt").readline().strip()
    SWMHversion = open("modules/SWMH/version.txt").readline().strip()
    NBRTversion = open("modules/NBRT+/version.txt").readline().strip()
    ARKOversion = open("modules/ARKOpack_Armoiries/version.txt").readline()
    language = raw_input("For English, press enter. En francais, taper 'f'. Para espanol, presiona 'e'.").lower()
    if language == "f":
        print("Cette version de Historical Immersion Project date du %s" % version)
        print("Taper 'y' ou 'oui' pour valider, ou laisser le champ vierge. Toute autre reponse sera interpretee comme un non.")
    elif language == "e":
        print("Esta vercion de Historical Immersion Project fecha del %s" % version)
        print("Escribe 'y' o 'si' para aceptar, o deja el campo en blanco. Cualquier otro caso sera considerado un 'no'.")
    else:
        print("This version of the Historical Immersion Project was released %s" % version)
        print("Type 'y' or 'yes' for yes, or leave the field blank. Anything else will be interpreted as 'no'.")
    if language == "f":
        move = raw_input("Deplacer les fichiers plutot que les copier est bien plus rapide, mais rend l'installation de plusieurs copies du mod plus difficile. \n"
                         "Voulez-vous que les fichiers soient deplaces plutot que copies ? [oui]").lower()
    elif language == "e":
        move = raw_input("Mover los archivos en lugar de copiarlos es mucho mas rapido, pero hace que la instalacion de varias copias sea mas complicada.\n"
                         "Quieres que los archivos de los modulos se muevan en lugar de copiarse? [si]").lower()
    else:
        move = raw_input("Moving the files instead of copying them is much quicker, but makes installing several copies more difficult.\n"
                         "Do you want to have the module files moved rather than copied? [yes]").lower()
    if move == "" or move == "y" or move == "yes" or move == "oui" or move == "o":
        move = True
    else:
        move = False
    if language == "f":
        targetFolder = raw_input("Installer le mod dans un repertoire existant supprimera ce repertoire. Dans quel repertoire souhaitez-vous proceder a l'installation ?\n"
                                 "Laissez le champ vierge pour 'Historical Immersion Project'. ")
    elif language == "e":
        targetFolder = raw_input("Instalar el mod en una carpeta existente eliminara dicha carpeta. En que carpeta deseas realizar la instalacion?\n"
                                 "Dejar en blanco para 'Historical Immersion Project'. ")
    else:
        targetFolder = raw_input("Installing the mod to a folder that exists will delete that folder. What folder would you like to install to?\n"
                                 "Leave blank for 'Historical Immersion Project'. ")
    if targetFolder == "":
        targetFolder = "Historical Immersion Project"
    moduleOutput = []
    moduleOutput.append("Historical Immersion Project (%s)\nEnabled modules:\n" % version)
    PB = enableMod("Project Balance (%s)" % PBversion)
    SWMH = enableMod("SWMH (%s)" % SWMHversion)
    if SWMH:
        if language == "f":
            SWMHnative = enableMod("SWMH avec les noms culturels locaux, plutot qu'en anglais ou francises")
        elif language == "e":
            SWMHnative = enableMod("SWMH con localizacion nativa para culturas y titulos, en lugar de ingles")
        else:
            SWMHnative = enableMod("SWMH with native localisation for cultures and titles, rather than English")
    else:
        SWMHnative = True
    ARKOarmoiries = enableMod("ARKOpack Armoiries (coats of arms) (%s)" % ARKOversion)
    ARKOinterface = enableMod("ARKOpack Interface (%s)" % ARKOversion)
    NBRT = enableMod("NBRT+ (%s)" % NBRTversion)
    VIET = False
    if PB:
        VIETtraits = False
    else:
        VIETtraits = enableMod("VIET traits (%s)" % VIETversion)
    VIETevents = enableMod("VIET events (%s)" % VIETversion)
    if SWMH:
        if language == "f":
            print("VIET immersion n'est pas compatible avec SWMH et ne peut donc pas etre actif en meme temps qu'SWMH.")
        elif language == "e":
            print("VIET immersion no es todavia compatible con SWMH y no puede ser activado si has activado SWMH.")
        else:
            print("VIET immersion is not yet compatible with SWMH, thus cannot be enabled as you've enabled SWMH.")
        VIETimmersion = False
    else:
        VIETimmersion = enableMod("VIET immersion (%s)" % VIETversion)
        #VIETmusic = enableMod("VIET music")
    if VIETtraits or VIETevents or VIETimmersion:
        VIET = True

    if os.path.exists(targetFolder):
        shutil.rmtree(targetFolder)
    os.makedirs(targetFolder)

    moveFolder("Converter/Common")
    if ARKOarmoiries:
        moduleOutput.append("ARKO Armoiries (%s)\n" %ARKOversion)
        moveFolder("ARKOpack_Armoiries")
    if ARKOinterface:
        moduleOutput.append("ARKO Interface (%s)\n" %ARKOversion)
        moveFolder("ARKOpack_Interface")
        if VIET:
            shutil.rmtree("%s/gfx/event_pictures" % targetFolder)
    if VIET:
        moveFolder("VIET_Assets")
    if PB:
        moduleOutput.append("Project Balance (%s)\n" % PBversion)
        moveFolder("ProjectBalance")
        moveFolder("Converter/PB")
    if SWMH:
        if SWMHnative:
            moduleOutput.append("SWMH - Native localisation (%s)\n" % SWMHversion)
            moveFolder("SWMH")
        if not SWMHnative:
            moduleOutput.append("SWMH - English localisation(%s)\n" % SWMHversion)
            moveFolder("SWMH")
            moveFolder("English SWMH")
        if PB:
            moveFolder("PB + SWMH")
    if NBRT:
        moduleOutput.append("NBRT+ (%s)\n" % NBRTversion)
        if not SWMH:
            os.remove("modules/NBRT+/map/terrain.bmp")
            os.remove("modules/NBRT+/map/trees.bmp")
            os.remove("modules/NBRT+/map/terrain/colormap.dds")
            os.remove("modules/NBRT+/map/terrain/colormap_water.dds")
        moveFolder("NBRT+")
        if ARKOarmoiries:
            moveFolder("NBRT+ARKO")
    if VIETtraits:
        moduleOutput.append("VIET Traits (%s)\n" % VIETversion)
        moveFolder("VIET_Traits")
    if VIETevents:
        moduleOutput.append("VIET Events(%s)\n" % VIETversion)
        moveFolder("VIET_Events")
        if PB:
            moveFolder("PB_VIET_Events")
    if VIETimmersion:
        moduleOutput.append("VIET Immersion(%s)\n" % VIETversion)
        if PB: #This should be optimized in the future
            moveFolder("PB_VIET_Immersion")
        if not PB:
            moveFolder("VIET_Immersion")
            moveFolder("Converter/VIET")
        if language == "f":
            answer = raw_input("VIET Immersion necessite tous les DLC de portraits. Les avez-vous tous ? [oui]")
        if language == "e":
            answer = raw_input("VIET inmersion depende de los retratos DLC. Tiene todos los retratos DLC? [si]")
        else:
            answer = raw_input("VIET Immersion depends on the portrait DLC. Do you have all portrait DLC? [yes]")
        if not (answer == "" or answer == "y" or answer == "yes" or answer == "oui" or answer == "o" or answer == "s" or answer == "si"):
            shutil.rmtree("%s/common/cultures" % targetFolder)
            os.remove("%s/interface/portrait_sprites_DLC.gfx" % targetFolder)
            os.remove("%s/interface/portraits_mediterranean.gfx" % targetFolder)
            os.remove("%s/interface/portraits_norse.gfx" % targetFolder)
            os.remove("%s/interface/portraits_persian.gfx" % targetFolder)
            os.remove("%s/interface/portraits_saxon.gfx" % targetFolder)
            os.remove("%s/interface/portraits_turkish.gfx" % targetFolder)
            os.remove("%s/interface/portraits_ugric.gfx" % targetFolder)
            os.remove("%s/interface/portraits_westernslavic.gfx" % targetFolder)
            if not PB:
                moveFolder("VIET_portrait_fix/VIET")
            else:
                moveFolder("VIET_portrait_fix/PB")
    if move:
        shutil.rmtree("modules") #Cleanup
    if targetFolder != "Historical Immersion Project":
        with open("HIP_%s.mod" % targetFolder, "w") as modFile:
            modFile.write('name = "HIP - %s"\n' % targetFolder)
            modFile.write('path = "mod/%s"\n' % targetFolder)
            modFile.write('user_dir = "HIP - %s"\n' % targetFolder)
    with open("%s/version.txt" % targetFolder, "w") as output:
        output.write("".join(moduleOutput))
    if language == "f":
        raw_input("Installation terminee. Taper entree pour sortir.")
    elif language == "e":
        raw_input("Instalacion terminada. Presiona Enter para salir.")
    else:
        raw_input("Installation done. Hit enter to exit.")
except:
    print("Error:")
    traceback.print_exc(file=sys.stdout)
    input("An error has occurred. Please screenshot/copy this error and send it to the HIP team. Press enter to exit this command line.")