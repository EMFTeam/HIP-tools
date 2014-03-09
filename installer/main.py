#!/usr/bin/python
# -*- coding: cp1252 -*-
# -*- python-indent-offset: 4 -*-

import os
import sys
import shutil
import traceback
import time


version = {'major': 1, 'minor': 2, 'micro': 6,
           'Release-Date': '2014-03-07 18:01:33 UTC',
           'Released-By': 'Meneth <pb@meneth.com>'}


# noinspection PyPep8
def initLocalisation():
    global i18n
    i18n = {'INTRO':
                {
                    'fr': "Cette version de Historical Immersion Project date du %s.\n"
                          "Taper 'o' ou 'oui' pour valider, ou laisser le champ vierge. Toute autre\n"
                          "reponse sera interpretee comme un non.\n",
                    'es': "Esta vercion de Historical Immersion Project fecha del %s.\n"
                          "Escribe 's' o 'si' para aceptar, o deja el campo en blanco. Cualquier otro\n"
                          "caso sera considerado un 'no'.\n",
                    'en': "This version of the Historical Immersion Project was released %s.\n"
                          "To confirm a prompt, respond with 'y' or 'yes' (sans quotes) or simply hit\n"
                          "ENTER. Besides a blank line, anything else will be interpreted as 'no.'\n\n"
                          "If at any time you wish to abort the installation, press Ctrl+C.\n",
                },
            'ENABLE_MOD':
                {
                    'fr': "Voulez-vous installer %s ? [oui]",
                    'es': "Deseas instalar %s? [si]",
                    'en': "Do you want to install %s? [yes]",
                },
            'ENABLE_MOD_XOR':
                {
                    'fr': "Voulez-vous installer %s (%s) ? [oui]",
                    'es': "Deseas instalar %s (%s)? [si]",
                    'en': "Do you want to install %s (%s)? [yes]",
                },
            'ENABLE_MOD_XOR_WARN':
                {
                    'fr': "\n%s and %s are incompatible. You may only select one:",
                    'es': "\n%s and %s are incompatible. You may only select one:",
                    'en': "\n%s and %s are incompatible. You may only select one:",
                },
            'PUSH_FOLDER':
                {
                    'fr': 'Préparation %s',
                    'es': 'Preparación %s',
                    'en': 'Preparing %s',
                },
            'COMPILING':
                {
                    'fr': "Compilation '%s' ...",
                    'es': "Compilar '%s' ...",
                    'en': "Compiling '%s' ...",
                },
            }


def localise(key):
    return i18n[key][language]


class InstallerException(Exception):
    def __str__(self):
        return "Internal installer error"


class InstallerPathException(InstallerException):
    def __str__(self):
        return "Internal error: path separator expected in file path"


class InstallerPlatformError(InstallerException):
    def __str__(self):
        return "Platform '%s' is not supported for installation!" % sys.platform


class InstallerTraceNestingError(InstallerException):
    def __str__(self):
        return "Debugging trace nesting mismatch (more pops than pushes). Programmer error!"


class InstallerEmptyArgvError(InstallerException):
    def __str__(self):
        return "The runtime environment did not setup the program path."


class InstallerPackageNotFoundError(InstallerException):
    def __str__(self):
        return "The installer package files (modules/ folder) were not found!"


class NullDebugTrace:
    def __init__(self):
        pass

    def trace(self, msg):
        pass

    def push(self, s):
        pass

    def pop(self, s=None):
        pass


# noinspection PyMissingConstructor
class DebugTrace(NullDebugTrace):
    def __init__(self, f, prefix='DBG: '):
        self.file = f
        self.prefix = prefix
        self.i = 0
        self.indentStr = ' ' * 2

    def trace(self, msg):  # Trace msg to attached stream/file-like object with no output buffering
        self.file.write('{}{}{}\n'.format(self.indentStr * self.i, self.prefix, msg))
        self.file.flush()

    def push(self, s):  # Trace, then push indent stack
        self.trace(s)
        self.i += 1

    def pop(self, s=None):  # Pop indent stack
        if self.i <= 0:
            raise InstallerTraceNestingError()
        self.i -= 1
        if s:
            self.trace(s)


class TargetSource:
    def __init__(self, folder, srcPath, isDir=False):
        self.folder = folder
        self.srcPath = srcPath
        self.isDir = isDir


def promptUser(prompt, lc=True):
    sys.stdout.write(prompt + ' ')
    sys.stdout.flush()
    response = sys.stdin.readline().strip()
    return response.lower() if lc else response


def isYes(answer):
    yesSet = {'fr': ('', 'o', 'oui'),
              'es': ('', 's', 'si'),
              'en': ('', 'y', 'yes')}
    return answer in yesSet[language]


def enableMod(name):
    return isYes(promptUser(localise('ENABLE_MOD') % name))


def enableModXOR(nameA, versionA, nameB, versionB):
    print(localise('ENABLE_MOD_XOR_WARN') % (nameA, nameB))
    for n, v in [(nameA, versionA), (nameB, versionB)]:
        if isYes(promptUser(localise('ENABLE_MOD_XOR') % (n, v))):
            return n
    return None


def quoteIfWS(s):
    return "'{}'".format(s) if ' ' in s else s


def rmTree(directory, traceMsg=None):
    if traceMsg:
        dbg.trace(traceMsg)
    if os.path.exists(directory):
        dbg.trace("RD: " + quoteIfWS(directory))
        shutil.rmtree(directory)


def rmFile(f, traceMsg=None):
    if traceMsg:
        dbg.trace(traceMsg)
    dbg.trace("D: " + quoteIfWS(f))
    os.remove(f)


def mkTree(d, traceMsg=None):
    if traceMsg:
        dbg.trace(traceMsg)
    dbg.trace("MD: " + quoteIfWS(d))
    os.makedirs(d)


def pushFolder(folder, prunePaths=None, ignoreFiles=None):
    if not ignoreFiles:
        ignoreFiles = {}
    if not prunePaths:
        prunePaths = {}

    print(localise('PUSH_FOLDER') % quoteIfWS(folder))

    srcFolder = os.path.join('modules', folder)
    dbg.push("compile: pushing folder " + srcFolder)

    for root, dirs, files in os.walk(srcFolder):
        newRoot = root.replace(srcFolder, targetFolder)
        dbg.push('adding path ' + root)

        # Prune the source directory walk in-place according to prunePaths option,
        # and, of course, don't create pruned directories (none of the files in
        # them will be copied/moved)
        prunedDirs = []

        for directory in dirs:
            srcPath = os.path.join(root, directory)
            if srcPath in prunePaths:
                dbg.trace("PRUNE: " + srcPath)
            else:
                prunedDirs.append(directory)
                newDir = os.path.join(newRoot, directory)
                targetSrc[newDir] = TargetSource(folder, srcPath, isDir=True)

        dirs[:] = prunedDirs  # Filter subdirectories into which we should recurse on next os.walk()

        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(newRoot, f)

            if src in ignoreFiles:  # Selective ignore filter for individual files
                dbg.trace('IGNORE: ' + quoteIfWS(src))
                continue

            targetSrc[dst] = TargetSource(folder, src)
        dbg.pop()
    dbg.pop()


def popFile(f):
    p = os.path.join(targetFolder, f)
    if p in targetSrc:
        del targetSrc[p]


def popTree(d):
    t = os.path.join(targetFolder, d)
    for p in [p for p in targetSrc.keys() if p.startswith(t)]:
        del targetSrc[p]


def stripPathHead(path):
    i = path.find('/')
    if i == -1:
        i = path.find('\\')
    if i == -1:
        raise InstallerPathException()
    newStart = i + 1
    return path[newStart:]


def compileTarget():
    print(localise('COMPILING') % targetFolder)
    mapFilename = os.path.join(targetFolder, 'file2mod_map.txt')
    dbg.push("compiling target with file->mod mapping dumped to '%s'..." % mapFilename)
    x = len(targetSrc) // 20
    with open(mapFilename, "w") as mapFile:
        for n, dstPath in enumerate(sorted(targetSrc)):
            if n % x == 0:
                print("%s%%" % (n // x * 5))
            src = targetSrc[dstPath]
            mapFile.write('%s <= [%s]\n' % (stripPathHead(dstPath), src.folder))
            if src.isDir:
                mkTree(dstPath)
            elif move:
                shutil.move(src.srcPath, dstPath)
            else:
                shutil.copy(src.srcPath, dstPath)


def detectPlatform():
    p = sys.platform
    if p.startswith('darwin'):
        return 'mac'
    elif p.startswith('linux'):
        return 'lin'
    elif p.startswith('win') or p.startswith('cygwin'):  # Currently no need to differentiate win(32|64) and cygwin
        return 'win'
    raise InstallerPlatformError()


def cleanUserDir(userDir):
    if platform != 'mac':
        print('Clearing cache in ' + quoteIfWS(userDir))

    dbg.push('clearing cache in ' + quoteIfWS(userDir))
    for d in [os.path.join(userDir, e) for e in ['gfx', 'map', 'interface', 'logs']]:
        rmTree(d)
    dbg.pop()


def resetCaches():
    if platform == 'mac':
        print('Clearing preexisting gfx/map cache')
        cleanUserDir('..')
    elif platform == 'win':
        print('Clearing preexisting HIP gfx/map caches ...')

        # Match *all* userdirs in CKII user directory which include 'HIP' in their
        # directory name, as this also covers all cases with external mods used with
        # HIP, and then clear their caches. It works, because, without editing the
        # user_dir line in the .mod file, it is impossible to select a target folder
        # that won't result in a substring of 'HIP' somewhere in the combined
        # user_dir name.

        dirEntries = [os.path.join('..', e) for e in os.listdir('..')]
        for userDir in dirEntries:
            if os.path.isdir(userDir) and 'HIP' in userDir:
                cleanUserDir(userDir)
    else:
        pass  # TODO: linux user dirs are where?


# Changes the current working directory to the same as that of the
# fully-resolved path to this program. This is to enable the installer to be
# invoked from any directory, so long as it's been properly extracted to the
# right folder. While useful and the proper behavior in all cases where we
# depend upon data in the same directory (./modules/), the main use case is to
# enable GUI-based invocations of the installer on all platforms to always
# magically be in the right working directory before touching any files.
def normalizeCwd():
    # All but the final step was done in initVersionEnvInfo() already.
    d = os.path.dirname(programPath)
    if d != '':
        os.chdir(d)


# noinspection PyDictCreation
def initVersionEnvInfo():
    global versionStr
    versionStr = '{}.{}.{}'.format(version['major'], version['minor'], version['micro'])

    ##    if 'Commit-ID' in version:
    ##        versionStr += '.git~' + version['Commit-ID'][0:7]

    # Note that the above generates a version string that is lexicographically
    # ordered from semantic 'earlier' to 'later' in all cases, including variable
    # numbers of digits in any of the components.

    # Resolve the installer's own absolute path. Needs to be tested with a py2exe
    # rebuild, hence the exception-raising case below.

    # We have a relative or absolute path in sys.argv[0] (in either case, it may
    # still be the right directory, but we'll have to find out).

    if len(sys.argv) == 0 or sys.argv[0] == '':
        raise InstallerEmptyArgvError()

    global programPath

    # Resolve any symbolic links in path elements and canonicalize it
    programPath = os.path.realpath(sys.argv[0])

    # Make sure it's normalized and absolute with respect to platform conventions
    programPath = os.path.abspath(programPath)
    return


def printVersionEnvInfo():
    # Print the installer's version info (installer *script*, not module package)

    print('HIP Installer Version:')
    print(versionStr + '\n')

    # Fill this with any extended version info keys we want printed, if present.
    # This is the order in which they'll be displayed.
    extKeys = ['Commit-ID', 'Release-Date', 'Released-By']

    # Resolve optional keys to found keys
    extKeys = [k for k in extKeys if k in version]

    if extKeys:
        extVals = [version[k] for k in extKeys]
        extKeys = [k + ': ' for k in extKeys]
        maxKeyWidth = len(max(extKeys, key=len))
        for k, v in zip(extKeys, extVals):
            print('% -*s%s' % (maxKeyWidth, k, v))
        sys.stdout.write('\n')

    print('HIP Installer Path: ')
    print(programPath + '\n')

    # Print the OS version/build info
    import platform as p

    print('Operating System / Platform:')
    print(sys.platform + ': ' + p.platform() + '\n')

    # Print our runtime interpreter's version/build info

    print("Python Runtime Version:")
    print(sys.version)
    return


def getPkgVersions(modDirs):
    global versions
    versions = {}
    dbg.push("reading package/module versions")
    for mod in modDirs.keys():
        f = os.path.join("modules", modDirs[mod], "version.txt")
        dbg.trace("%s: reading %s" % (mod, f))
        versions[mod] = open(f).readline().strip()
        dbg.trace("%s: version: %s" % (mod, versions[mod]))
    dbg.pop()


def getInstallOptions():
    # Determine user language for installation
    global language
    language = promptUser("For English, hit ENTER. En francais, taper 'f'. Para espanol, presiona 'e'.")

    if language == 'f':
        language = 'fr'
    elif language == 'e':
        language = 'es'
    else:
        language = 'en'

    # Show HIP installer version & explain interactive prompting
    print(localise('INTRO') % versions['pkg'])

    global move

    if language == 'fr':
        move = promptUser("Deplacer les fichiers plutot que les copier est bien plus rapide, mais\n"
                          "rend l'installation de plusieurs copies du mod plus difficile.\n"
                          "Voulez-vous que les fichiers soient deplaces plutot que copies? [oui]")
    elif language == 'es':
        move = promptUser("Mover los archivos en lugar de copiarlos es mucho mas rapido, pero hace\n"
                          "que la instalacion de varias copias sea mas complicada.\n"
                          "Quieres que los archivos de los modulos se muevan en lugar de copiarse? [si]")
    else:
        move = promptUser("The installer can either directly MOVE the module package's data files\n"
                          "into your installation folder, deleting the package in the process, or\n"
                          "it can preserve the installation package by COPYING the files into the\n"
                          "installation folder. Moving is faster than copying, but copying allows\n"
                          "you to reinstall at will (e.g., with different module combinations).\n\n"
                          "Would you like to MOVE rather than COPY? [yes]")

    move = isYes(move)

    # Confirm. "User studies" now "prove" this default is questionable (i.e.,
    # copy not being default), but I think the move method should remain the
    # default if you hit ENTER to everything. Not because of speed. Not only are
    # all the package data files freshly primed in the OS filesystem cache due
    # to the installer archive extraction done previously, but the installer's
    # compilation logic will soon be overhauled for single-pass compilation,
    # thus dramatically reducing the number of file operations while merging to
    # the minimum possible required.

    # The reason MOVE ought to be default is simply that most users *should*
    # have their source package deleted after use (as they can simply unzip
    # again, worst-case). It avoids scenarios where users forget to delete a
    # preexisting modules/, unzip a new HIP release that deleted or renamed some
    # files into the mod folder, and then have multiple or old, extranneous
    # versions of files mixed into the new release.

    if move:
        if language == 'fr':
            move = promptUser("Etes-vous s�r?\n"
                              "Voulez-vous supprimer le paquet apr�s l'installation? [oui]")
        elif language == 'es':
            move = promptUser("�Est� seguro?\n"
                              "�Quieres eliminar el paquete despu�s de la instalaci�n? [si]")
        else:
            move = promptUser("Are you sure?\n"
                              "Do you want to delete the package after installation? [yes]")

    move = isYes(move)
    dbg.trace('user choice: move instead of copy: {}'.format(move))

    # Determine installation target folder...
    global defaultFolder
    defaultFolder = 'Historical Immersion Project'

    # Note that we use the case-preserving form of promptUser for the target folder (also determines name in launcher)

    global targetFolder

    if language == 'fr':
        targetFolder = promptUser("Installer le mod dans un repertoire existant supprimera ce repertoire.\n"
                                  "Dans quel repertoire souhaitez-vous proceder a l'installation ?\n"
                                  "Laissez le champ vierge pour '%s'." % defaultFolder, lc=False)
    elif language == 'es':
        targetFolder = promptUser("Instalar el mod en una carpeta existente eliminara dicha carpeta.\n"
                                  "En que carpeta deseas realizar la instalacion?\n"
                                  "Dejar en blanco para '%s'." % defaultFolder, lc=False)
    else:
        targetFolder = promptUser("Installing the mod into a folder that exists will first delete that folder.\n"
                                  "Into what folder would you like to install?\n"
                                  "Leave blank for '%s':" % defaultFolder, lc=False)

    if targetFolder == '':
        targetFolder = defaultFolder
    else:
        pass  # TODO: verify it contains no illegal characters
    dbg.trace('user choice: target folder: {}'.format(quoteIfWS(targetFolder)))


def main():
    # noinspection PyBroadException
    try:
        initLocalisation()
        initVersionEnvInfo()

        dbgMode = (len(sys.argv) > 1 and '-D' in sys.argv[1:])
        versionMode = (len(sys.argv) > 1 and '-V' in sys.argv[1:])
        timerMode = (len(sys.argv) > 1 and '-T' in sys.argv[1:])

        # The debug tracer's file object is unbuffered (always flushes all writes
        # to disk/pipe immediately), and it lives until the end of the program, so
        # we don't need to worry about closing it properly (e.g., upon an
        # exception), because it will be closed by the OS on program exit, and all
        # trace data will have already had its __write() syscalls queued to the OS.

        global dbg
        dbg = DebugTrace(open('HIP_debug.log', 'w', 0)) if dbgMode else NullDebugTrace()

        global platform
        platform = detectPlatform()
        dbg.trace('detected supported platform class: ' + platform)

        if versionMode:
            printVersionEnvInfo()
            return 0

        # Normal operation from here on...

        if platform == 'mac':
            print('WARNING: Mac OS X support is currently in beta.\n'
                  'While all mods and the installer should now work with OS X for all users, YMMV.\n'
                  'Please report any problems you encounter or any feedback that you\'d like to\n'
                  'share on the HIP forums or via an email to the owner of the OS X initiative:\n'
                  'zijistark <zijistark@gmail.com>\n')

        # Ensure the runtime's current working directory corresponds exactly to the
        # location of this module itself. In other words, allow it to be run from
        # anywhere on the system but still be able to assume the relative path to,
        # e.g., "modules/" is just that.
        normalizeCwd()

        if not os.path.isdir('modules'):
            raise InstallerPackageNotFoundError()

        # modDirs, the start of an attempt to centralize all references to
        # sub-module path info at the very least (better yet, paving the way toward
        # factoring the compatch logic out into a data file distributed with
        # modules/), is incomplete toward that end. Even currently, though, selected
        # module versioning output could be generated by a single zip-list
        # comprehension if a few corresponding changes were made to the
        # mod-selection code and the code which uses those vars.
        modDirs = {'pkg': '',
                   'VIET': 'VIET_Assets',
                   'PB': 'ProjectBalance',
                   'SWMH': 'SWMH',
                   'NBRT': 'NBRT+',
                   'ARKO': 'ARKOpack_Armoiries'}

        getPkgVersions(modDirs)

        # Prompt user for options related to this install
        getInstallOptions()

        # Determine module combination...
        PB = enableMod("Project Balance (%s)" % versions['PB'])
        ARKOarmoiries = enableMod("ARKOpack Armoiries (coats of arms) (%s)" % versions['ARKO'])
        ARKOinterface = enableMod("ARKOpack Interface (%s)" % versions['ARKO'])
        NBRT = enableMod("NBRT+ (%s)" % versions['NBRT'])

        if PB:
            VIETtraits = False
        else:
            VIETtraits = enableMod("VIET traits (%s)" % versions['VIET'])

        VIETevents = enableMod("VIET events (%s)" % versions['VIET'])

        SWMH = False
        VIETimmersion = False

        swmhVIET = enableModXOR('SWMH', versions['SWMH'], 'VIET Immersion', versions['VIET'])

        if swmhVIET == 'SWMH':
            SWMH = True
        elif swmhVIET == 'VIET Immersion':
            VIETimmersion = True

        VIET = (VIETtraits or VIETevents or VIETimmersion)

        if SWMH:
            if language == 'fr':
                SWMHnative = enableMod("SWMH avec les noms culturels locaux, plutot qu'en anglais ou francises")
            elif language == 'es':
                SWMHnative = enableMod("SWMH con localizacion nativa para culturas y titulos, en lugar de ingles")
            else:
                SWMHnative = enableMod("SWMH with native localisation for cultures and titles, rather than English")
        else:
            SWMHnative = True

        # Prepare for installation
        if os.path.exists(targetFolder):
            rmTree(targetFolder, 'target folder preexists. removing...')

        mkTree(targetFolder)

        # Install...
        global targetSrc
        targetSrc = {}
        
        moduleOutput = ["Historical Immersion Project (%s)\nEnabled modules:\n" % versions['pkg']]
        dbg.push('performing virtual filesystem merge...')

        pushFolder("Converter/Common")

        if ARKOarmoiries:
            dbg.push("merging ARKO CoA...")
            moduleOutput.append("ARKO Armoiries (%s)\n" % versions['ARKO'])
            pushFolder("ARKOpack_Armoiries")
            dbg.pop()

        if ARKOinterface:
            dbg.push("merging ARKO Interface...")
            moduleOutput.append("ARKO Interface (%s)\n" % versions['ARKO'])
            pushFolder("ARKOpack_Interface")
            if VIET:
                popTree("gfx/event_pictures")
            dbg.pop()

        if VIET:
            pushFolder("VIET_Assets")

        if PB:
            dbg.push("merging PB...")
            moduleOutput.append("Project Balance (%s)\n" % versions['PB'])
            pushFolder("ProjectBalance")
            pushFolder("Converter/PB")
            dbg.pop()

        if SWMH:
            dbg.push("merging SWMH...")
            pushFolder("SWMH")
            if SWMHnative:
                moduleOutput.append("SWMH - Native localisation (%s)\n" % versions['SWMH'])
            else:
                moduleOutput.append("SWMH - English localisation (%s)\n" % versions['SWMH'])
                pushFolder("English SWMH")
            if PB:
                pushFolder("PB + SWMH")
            dbg.pop()

        if NBRT:
            dbg.push("merging NBRT+...")
            moduleOutput.append("NBRT+ (%s)\n" % versions['NBRT'])
            pushFolder("NBRT+")
            if SWMH:
                pushFolder("NBRT+SWMH")
            if ARKOarmoiries:
                pushFolder("NBRT+ARKO")
            dbg.pop()

        if VIETtraits:
            dbg.push("merging VIET Traits...")
            moduleOutput.append("VIET Traits (%s)\n" % versions['VIET'])
            pushFolder("VIET_Traits")
            dbg.pop()

        if VIETevents:
            dbg.push("merging VIET Events...")
            moduleOutput.append("VIET Events (%s)\n" % versions['VIET'])
            pushFolder("VIET_Events")
            if PB:
                pushFolder("PB_VIET_Events")
            dbg.pop()

        if VIETimmersion:
            dbg.push("merging VIET Immersion...")
            moduleOutput.append("VIET Immersion (%s)\n" % versions['VIET'])
            if PB:
                pushFolder("PB_VIET_Immersion")
            else:
                pushFolder("VIET_Immersion")
                pushFolder("Converter/VIET")

            if language == 'fr':
                answer = promptUser("VIET Immersion necessite tous les DLC de portraits. Les avez-vous\n"
                                    "tous? [oui]")
            elif language == 'es':
                answer = promptUser("VIET inmersion depende de los retratos DLC. Tiene todos los retratos\n"
                                    "DLC? [si]")
            else:
                answer = promptUser("VIET Immersion depends on the portrait DLCs. Do you have all of the\n"
                                    "portrait DLCs? [yes]")

            if not isYes(answer):
                dbg.push("user chose VIET Immersion but does not have all portrait DLCs. applying fix...")
                popTree("common/cultures")
                dbg.push("removing portrait .gfx files...")
                popFile("interface/portrait_sprites_DLC.gfx")
                popFile("interface/portraits_mediterranean.gfx")
                popFile("interface/portraits_norse.gfx")
                popFile("interface/portraits_persian.gfx")
                popFile("interface/portraits_saxon.gfx")
                popFile("interface/portraits_turkish.gfx")
                popFile("interface/portraits_ugric.gfx")
                popFile("interface/portraits_westernslavic.gfx")
                dbg.pop()
                if not PB:
                    pushFolder("VIET_portrait_fix/VIET")
                else:
                    pushFolder("VIET_portrait_fix/PB")
                dbg.pop()
            dbg.pop()

        dbg.pop("virtual filesystem merge complete")

        startTime = time.clock()

        # do all the actual compilation (file I/O)
        compileTarget()

        if move:
            rmTree("modules")  # Cleanup
        if (platform == "mac" or platform == "lin") and SWMH and NBRT:
            os.remove("%s/gfx/FX/pdxmap.lua" % targetFolder)  # This file breaks the game on OS X/Linux

        endTime = time.clock()

        if timerMode:
            print('Compilation took %0.1f seconds' % (endTime - startTime))

        # Generate a new .mod file, regardless of whether it's default
        if targetFolder != defaultFolder:
            modFileBase = 'HIP_' + targetFolder
        else:
            modFileBase = 'HIP'

        modFilename = modFileBase + '.mod'
        dbg.trace("generating .mod file " + quoteIfWS(modFilename))
        print("Generating mod definition file: " + quoteIfWS(modFilename))

        with open(modFilename, "w") as modFile:
            modFile.write('name = "HIP - %s"    #Name that shows in launcher\n' % targetFolder)
            modFile.write('path = "mod/%s"\n' % targetFolder)
            if platform != 'mac':
                modFile.write('user_dir = "%s"    #For saves, gfx cache, etc.\n' % modFileBase)

        # Dump modules selected and their respective versions to <mod>/version.txt
        versionFilename = "%s/version.txt" % targetFolder
        dbg.trace("dumping compiled modpack version summary to " + quoteIfWS(versionFilename))
        print("Generating mod combination/versions summary: " + quoteIfWS(versionFilename))

        with open(versionFilename, "w") as output:
            output.write("".join(moduleOutput))

        # Reset all gfx/map/interface/logs cache for every instance of a preexisting
        # user_dir that includes HIP, platform-agnostic.
        resetCaches()

        # Installation complete
        dbg.trace("installation complete")

        if language == 'fr':
            promptUser("Installation terminee. Taper entree pour sortir.")
        elif language == 'es':
            promptUser("Instalacion terminada. Presiona Enter para salir.")
        else:
            promptUser("Installation done. Hit ENTER to exit.")

        return 0  # Return success code to OS

    except KeyboardInterrupt:
        # Ctrl-C just aborts (with a dedicated error code) rather than cause a
        # traceback. May want to catch it during filesystem modification stage
        sys.stderr.write("\nUser interrupt: Aborting installer early...\n")
        sys.exit(2)

    except InstallerTraceNestingError as e:
        sys.stderr.write("\nFatal error: " + str(e))
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write("Screenshot/copy this error and send it to the HIP team. Press ENTER to exit.")
        sys.exit(255)

    # Special handling for specific installer-understood error types (all derive from InstallerException)
    except InstallerException as e:
        sys.stderr.write("\nFatal error: " + str(e))
        sys.stderr.write("\nFor help, provide this error to the HIP team. Press ENTER to exit.")
        sys.stdin.readline()
        sys.exit(1)

    # And the unknowns...
    except:
        sys.stderr.write("\nUnexpected fatal error occurred:\n")
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write("Screenshot/copy this error and send it to the HIP team. Press ENTER to exit.")
        sys.stdin.readline()
        sys.exit(255)


if __name__ == "__main__":
    sys.exit(main())
