#!/usr/bin/python
# -*- coding: cp1252 -*-
# -*- python-indent-offset: 4 -*-

import os
import sys
import shutil
import traceback
import time


version = {'major': 1, 'minor': 5, 'patch': 6,
           'Developer':       'zijistark <zijistark@gmail.com>',
           'Release Manager': 'Meneth    <hip@meneth.com>'}


# noinspection PyPep8
def initLocalisation():
    global i18n
    i18n = {'INTRO':
            {
                'fr': u"Cette version de Historical Immersion Project date du {}.\n"
                      u"Taper 'o' ou 'oui' pour valider, ou laisser le champ vierge. Toute autre\n"
                      u"réponse sera interpretée comme négative.\n"
                      u"Pour abandonner à tout moment l'installation, appuyer sur Ctrl+C.\n",
                'es': u"Esta vercion de Historical Immersion Project fecha del {}.\n"
                      u"Escribe 's' o 'si' para aceptar, o deja el campo en blanco. Cualquier otro\n"
                      u"caso sera considerado un 'no'.\n",
                'en': u"This version of the Historical Immersion Project was released {}.\n"
                      u"To confirm a prompt, respond with 'y' or 'yes' (sans quotes) or simply hit\n"
                      u"ENTER. Besides a blank line, anything else will be interpreted as 'no.'\n\n"
                      u"If at any time you wish to abort the installation, press Ctrl+C.\n",
            },
            'ENABLE_MOD':
            {
                'fr': u"Voulez-vous installer {} ? [oui]",
                'es': u"Instalar {}? [si]",
                'en': u"Install {}? [yes]",
            },
            'ENABLE_MOD_NOT_DEFAULT':
            {
                'fr': u"Voulez-vous installer {} ? [non]",
                'es': u"Instalar {}? [no]",
                'en': u"Install {}? [no]",
            },
            'ENABLE_MOD_XOR':
            {
                'fr': u"Voulez-vous installer {} ({}) ? [oui]",
                'es': u"Instalar {} ({})? [si]",
                'en': u"Install {} ({})? [yes]",
            },
            'ENABLE_MOD_NOT_DEFAULT_COMPAT':
            {
                'fr': u"\nNOTE: {} might be incompatible with your system.\nVoulez-vous installer {} ? [non]",
                'es': u"\nNOTE: {} might be incompatible with your system.\nInstalar {}? [no]",
                'en': u"\nNOTE: {} might be incompatible with your system.\nInstall {}? [no]",
            },
            'ENABLE_MOD_XOR_WARN':
            {
                'fr': u"\n{} et {} sont incompatibles. Vous devez n'en choisir qu'un : ",
                'es': u"\n{} and {} are incompatible. You may only select one:",
                'en': u"\n{} and {} are incompatible. You may only select one:",
            },
            'PUSH_FOLDER':
            {
                'fr': u'Préparation {}',
                'es': u'Preparaciòn {}',
                'en': u'Preparing {}',
            },
            'COMPILING':
            {
                'fr': u"Compilation '{}' ...",
                'es': u"Compilar '{}' ...",
                'en': u"Compiling '{}' ...",
            },
            'SWMH_NATIVE':
            {
                'fr': u"SWMH avec les noms culturels locaux, plutôt qu'en anglais ou francisés",
                'es': u"SWMH con localizacion nativa para culturas y titulos, en lugar de ingles",
                'en': u"SWMH with native localisation for cultures and titles, rather than English",
            },
            'MOVE_VS_COPY':
            {
                'fr': u"L'installeur DEPLACE ou COPIE les fichiers d'installation. La\n"
                      u"COPIE permet l'installation ultérieure de differents combos de\n"
                      u"mods à partir de l'installeur de base. Notez que DEPLACER est\n"
                      u"plus rapide que COPIER.\n\n"
                      u"Voulez-vous donc que les fichiers soient DEPLACES plutôt que\n"
                      u"COPIES ? [oui]",
                'es': u"Mover los archivos en lugar de copiarlos es mucho mas rapido, pero hace\n"
                      u"que la instalacion de varias copias sea mas complicada.\n\n"
                      u"Quieres que los archivos de los modulos se muevan en lugar de copiarse? [si]",
                'en': u"The installer can either directly MOVE the module package's data files\n"
                      u"into your installation folder, deleting the package in the process, or\n"
                      u"it can preserve the installation package by COPYING the files into the\n"
                      u"installation folder. Moving is faster than copying, but copying allows\n"
                      u"you to reinstall at will (e.g., with different module combinations).\n\n"
                      u"Would you like to MOVE rather than COPY? [yes]",
            },
            'MOVE_CONFIRM':
            {
                'fr': u"Etes-vous sûr ?\n"
                      u"Voulez-vous supprimer les fichiers d'installation une fois l'opération terminée ? "
                      u"[oui]",
                'es': u"?Esta seguro?\n"
                      u"?Quieres eliminar el paquete despuès de la instalaciòn? [si]",
                'en': u"Are you sure?\n"
                      u"Do you want to delete the package after installation? [yes]",
            },
            'TARGET_FOLDER':
            {
                'fr': u"Installer le mod dans un répertoire existant supprimera ce répertoire.\n"
                      u"Dans quel répertoire souhaites-tu procéder à l'installation ?\n"
                      u"Laisser le champ vierge pour '{}'.",
                'es': u"Instalar el mod en una carpeta existente eliminara dicha carpeta.\n"
                      u"En que carpeta deseas realizar la instalacion?\n"
                      u"Dejar en blanco para '{}'.",
                'en': u"Installing the mod into a folder that exists will first delete that folder.\n"
                      u"Into what folder would you like to install?\n"
                      u"Leave blank for '{}':",
            },
            'INSTALL_DONE':
            {
                'fr': u"Installation terminée. Taper ENTREE pour quitter.",
                'es': u"Instalacion terminada. Presiona ENTER para salir.",
                'en': u"Installation done. Hit ENTER to exit.",
            }
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
    sys.stdout.write(prompt + u' ')
    sys.stdout.flush()
    response = sys.stdin.readline().strip()  # TODO: broken if diff locales use non-ASCII chars in response
    return response.lower() if lc else response


def isYes(answer):
    yesSet = {'fr': ('', 'o', 'oui'),
              'es': ('', 's', 'si'),
              'en': ('', 'y', 'yes')}
    return answer in yesSet[language]


def isYesDefaultNo(answer):
    yesSet = {'fr': ('o', 'oui'),
              'es': ('s', 'si'),
              'en': ('y', 'yes')}
    return answer in yesSet[language]


def enableMod(name):
    return isYes(promptUser(localise('ENABLE_MOD').format(name)))


def enableModDefaultNo(name, compat=False):
    if compat:
        return isYesDefaultNo(promptUser(localise('ENABLE_MOD_NOT_DEFAULT').format(name)))
    else:
        return isYesDefaultNo(promptUser(localise('ENABLE_MOD_NOT_DEFAULT_COMPAT').format(name, name)))


def enableModXOR(nameA, versionA, nameB, versionB):
    print(localise('ENABLE_MOD_XOR_WARN').format(nameA, nameB))
    for n, v in [(nameA, versionA), (nameB, versionB)]:
        if isYes(promptUser(localise('ENABLE_MOD_XOR').format(n, v))):
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

    #print(localise('PUSH_FOLDER').format(unicode(quoteIfWS(folder))))

    folder = os.path.normpath(folder)
    srcFolder = os.path.join('modules', folder)

    if not os.path.exists(srcFolder):
        dbg.trace("WARNING! MODULE NOT FOUND: {}".format(quoteIfWS(folder)))
        return

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

            dbg.trace(quoteIfWS(dst) + ' <= ' + quoteIfWS(src))

            targetSrc[dst] = TargetSource(folder, src)
        dbg.pop()
    dbg.pop()


def popFile(f):
    f = os.path.normpath(f)
    p = os.path.join(targetFolder, f)
    if p in targetSrc:
        dbg.trace("popFile: {}".format(quoteIfWS(p)))
        del targetSrc[p]


def popTree(d):
    d = os.path.normpath(d)
    t = os.path.join(targetFolder, d)
    dbg.push("popTree: {}".format(quoteIfWS(t)))
    for p in [p for p in targetSrc.keys() if p.startswith(t)]:
        dbg.trace(p)
        del targetSrc[p]
    dbg.pop()


def stripPathHead(path):
    i = path.find('/')
    if i == -1:
        i = path.find('\\')
    if i == -1:
        raise InstallerPathException()
    newStart = i + 1
    return path[newStart:]


def compileTarget():
    print(localise('COMPILING').format(targetFolder))
    sys.stdout.flush()
    mapFilename = os.path.join(targetFolder, 'file2mod_map.txt')
    dbg.push("compiling target with file->mod mapping dumped to '{}'...".format(mapFilename))
    x = len(targetSrc) // 10
    with open(mapFilename, "w") as mapFile:
        for n, dstPath in enumerate(sorted(targetSrc)):
            if n % x == 0:
                print(u"{}%".format((n // x * 10)))
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
    #if platform != 'mac':
    #    print('Clearing cache in ' + quoteIfWS(userDir))

    dbg.push('clearing cache in ' + quoteIfWS(userDir))
    for d in [os.path.join(userDir, e) for e in ['gfx', 'map', 'interface', 'logs']]:
        rmTree(d)
    dbg.pop()


def resetCaches():
    if platform == 'mac':
        print(u'Clearing preexisting CKII gfx/map cache')
        cleanUserDir('..')  # TODO: Find out if the user_dir changes with the new 2.1.5 launcher
    elif platform == 'win':
        print(u'Clearing preexisting HIP-related CKII gfx/map caches ...')

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
        pass  # TODO: Find out if the user_dir changes with the new 2.1.5 launcher


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
    global version
    version['Version'] = '{}.{}.{}'.format(version['major'], version['minor'], version['patch'])

    ## if 'Commit-ID' in version:
    ## versionStr += '.git~' + version['Commit-ID'][0:7]

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
    print(u'HIP Installer:')

    # Fill this with any extended version info keys we want printed, if present.
    # This is the order in which they'll be displayed.
    extKeys = ['Version', 'Commit ID', 'Primary Developer', 'Developer', 'Release Manager']

    # Resolve optional keys to found keys
    extKeys = [k for k in extKeys if k in version]

    if extKeys:
        extVals = [version[k] for k in extKeys]
        extKeys = [k + ': ' for k in extKeys]
        maxKeyWidth = len(max(extKeys, key=len))
        for k, v in zip(extKeys, extVals):
            print('% -*s%s' % (maxKeyWidth, k, v))  # TODO: needs to be upgraded to use format() and output UTF-8
        sys.stdout.write('\n')

    print(u'HIP Installer Path: ')
    print(unicode(programPath + '\n'))

    # Print the OS version/build info
    import platform as p

    print(u'Operating System / Platform:')
    print(unicode(sys.platform + ': ' + p.platform() + '\n'))

    # Print our runtime interpreter's version/build info

    print(u"Python Runtime Version:")
    print(unicode(sys.version))
    return


def getPkgVersions(modDirs):
    global versions
    versions = {}
    dbg.push("reading package/module versions")
    for mod in modDirs.keys():
        f = os.path.join("modules", modDirs[mod], "version.txt")
        dbg.trace("%s: reading %s" % (mod, f))
        if os.path.exists(f):
            versions[mod] = unicode(open(f).readline().strip())
        else:
            versions[mod] = u'no version'
        dbg.trace("%s: version: %s" % (mod, versions[mod]))
    dbg.pop()


def getInstallOptions():
    # Determine user language for installation
    global language
    global betaMode
    language = promptUser(u"For English, hit ENTER. En français, taper 'f'. Para español, presiona 'e'.")

    if language.startswith('B') or language.startswith('b'):
        language = 'en'
        betaMode = True
    elif language == 'f':
        language = 'fr'
    elif language == 'e':
        language = 'es'
    else:
        language = 'en'

    # Show HIP installer version & explain interactive prompting
    print(localise('INTRO').format(versions['pkg']))

    global move
    move = isYes(promptUser(localise('MOVE_VS_COPY')))

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
        move = isYes(promptUser(localise('MOVE_CONFIRM')))
    dbg.trace('user choice: move instead of copy: {}'.format(move))

    # Determine installation target folder...
    global defaultFolder
    defaultFolder = 'Historical Immersion Project'

    # Note that we use the case-preserving form of promptUser for the target folder (also determines name in launcher)

    global targetFolder
    targetFolder = promptUser(localise('TARGET_FOLDER').format(unicode(defaultFolder)), lc=False)
    if targetFolder == '':
        targetFolder = defaultFolder
    else:
        pass  # TODO: verify it contains no illegal characters
    dbg.trace('user choice: target folder: {}'.format(quoteIfWS(targetFolder)))


# Find installation location for a Steam game with the given Steam AppID with the methodology variant denoted
# by variantID, where variantID is currently either 0 or 1.
def getSteamGameFolder(appID, variantID):

    pathVariant = [r'\Wow6432Node', '']
    keyPath = r'SOFTWARE{}\Microsoft\Windows\CurrentVersion\Uninstall\Steam App {}'.format(pathVariant[variantID],
                                                                                           appID)

    dbg.push('looking for steam game folder in registry key ' + keyPath)

    # TODO!!
    # _winreg import will fail on Python 3, so a check against the Python major version and subsequent conditional
    # import of 'winreg' instead of '_winreg' in that case *should* make this part of the script v2/v3-safe.

    # NOTE: Also need to either check for cygwin and remind the user that they need to invoke the standard python (via
    # cygwin still) to be able to support auto-detection since the cygwin platform python distribution doesn't include
    # any Windows registry libraries at all. At the moment it just crashes as a reminder to me to properly handle this,
    # since I think it'd be in the best interests of all if all installed and used cygwin as the standard platform
    # for HIP tools of all kinds. [Indeed almost all those that exist have it as a pre-req, though usually only due to
    # default config values.]

    import _winreg
    from _winreg import HKEY_LOCAL_MACHINE

    try:
        hReg = _winreg.ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        hKey = _winreg.OpenKey(hReg, keyPath)

        folder = _winreg.QueryValueEx(hKey, 'InstallLocation')

        if not folder:
            raise EnvironmentError()

        dbg.trace('InstallLocation = {}'.format(folder[0]))

        hKey.Close()
        hReg.Close()

        return folder[0]

    except EnvironmentError:
        return None

    finally:
        dbg.pop()


cprReqDLCNames = {'dlc/dlc013.dlc': 'African Portraits',
                  'dlc/dlc028.dlc': 'Celtic Portraits',
                  'dlc/dlc014.dlc': 'Mediterranean Portraits',
                  'dlc/dlc002.dlc': 'Mongol Face Pack',
                  'dlc/dlc020.dlc': 'Norse Portraits',
                  'dlc/dlc016.dlc': 'Russian Portraits',
                  'dlc/dlc041.dlc': 'Turkish Portraits',
                  'dlc/dlc044.dlc': 'Persian Portraits'}


# Determine whether the DLCs required for CPR are installed in the active game folder.
# Returns None if DLC detection (game folder detection) fails, an empty list if all
# requirements are met, and otherwise the exact list of the missing DLCs' names.
def detectCPRMissingDLCs():

    # Normalize path keys denormReqDLCNames, platform-specific (varies even between cygwin and win32)
    reqDLCNames = {os.path.normpath(f): cprReqDLCNames[f] for f in cprReqDLCNames.keys()}

    # Method currently only works on Windows (and probably only Win7 and Win8), so quit
    # now if we're not at least running a Windows platform (win32, win64, or cygwin).
    if platform != 'win' or sys.platform.startswith('cyg'):
        return None

    gameFolder = None

    # Try up to every method known to acquire the game install location
    for methodID in range(2):
        gameFolder = getSteamGameFolder(203770, methodID)  # Crusader Kings II is 203770
        if gameFolder:
            break

    if not gameFolder:
        # Get really desperate now and just try to see if the default game folder is a valid one.
        gameFolder = os.path.normpath("C:/Program Files (x86)/Steam/SteamApps/common/Crusader Kings II")

    dlcFolder = os.path.join(gameFolder, 'dlc')
    if not os.path.isdir(dlcFolder):
        return None

    for f in [os.path.join('dlc', e) for e in os.listdir(dlcFolder)]:
        if f in reqDLCNames:
            del reqDLCNames[f]

    return reqDLCNames.values()


def printCPRReqDLCNames():
    # Display names of required DLCs, sorted by latest release date
    for name in [cprReqDLCNames[f] for f in sorted(cprReqDLCNames.keys(), reverse=True)]:
        print(u"+ {}".format(name))

    sys.stdout.write('\n')


def main():
    # noinspection PyBroadException
    try:
        initLocalisation()
        initVersionEnvInfo()

        dbgMode = (len(sys.argv) > 1 and '-D' in sys.argv[1:])
        versionMode = (len(sys.argv) > 1 and '-V' in sys.argv[1:])
        global betaMode
        betaMode = False

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
                   'ARKO': 'ARKOpack_Armoiries',
                   'CPR': 'Cultures and Portraits Revamp',
                   'EMF': 'EMF',
                   }

        getPkgVersions(modDirs)

        # Prompt user for options related to this install
        getInstallOptions()

        # Determine module combination...

        EMF = enableMod(u"EMF: Extended Mechanics & Flavor ({})".format(versions['EMF']))
        PB = True

        if EMF:
            print(u"[ Automatically including some of Project Balance ... ]")
        else:
            PB = enableMod(u"Project Balance ({})".format(versions['PB']))

        ARKOarmoiries = enableMod(u"ARKOpack Armoiries (coats of arms) ({})".format(versions['ARKO']))
        ARKOinterface = enableMod(u"ARKOpack Interface ({})".format(versions['ARKO']))

        if platform == 'win':
            NBRT = enableMod(u"NBRT+ ({})".format(versions['NBRT']))
        else:
            NBRT = enableModDefaultNo(u"NBRT+ ({})".format(versions['NBRT']))

        CPR = False
        cprMissingDLCNames = detectCPRMissingDLCs()

        if cprMissingDLCNames is None:  # DLC auto-detection failed
            if platform == 'win':  # While unlikely, this happens with the current auto-detection code.
                                   # It is treated as a special case to still draw some visibility to
                                   # the problem.
                print(u"\n\nNOTE: The HIP installer could not successfully determine your active CKII\n"
                      u"game folder. Thus, it cannot auto-detect whether you meet all the portrait DLC\n"
                      u"prerequisites of CPR. You may still install CPR, but expect the game to crash\n"
                      u"with reckless abandon if you don't have all of the following DLCs enabled:\n")

                printCPRReqDLCNames()

                CPR = enableModDefaultNo(u"CPR ({})".format(versions['CPR']), compat=True)

            else:  # No auto-detection supported on mac/lin, so allow the user to choose CPR w/ zero fuss.
                print(u"\n\nNOTE: Cultures and Portraits Revamp (CPR) requires ALL of the\n"
                      u"portrait packs to run without crashing. Portrait DLCs required for CPR:\n")

                printCPRReqDLCNames()

                CPR = enableModDefaultNo(u"CPR ({})".format(versions['CPR']), compat=True)

        elif len(cprMissingDLCNames) > 0:  # DLC auto-detection succeeded, but there were missing DLCs.
            print(u"\n\nCultures and Portraits Revamp (CPR) requires portrait pack DLCs which you,\n"
                  u"unforunately, are lacking. If you want to use CPR, you'll need to install the\n"
                  u"following DLCs first:\n")

            for name in sorted(cprMissingDLCNames):
                print(u"+ {}".format(name))

            sys.stdout.write('\n')

        else:  # DLC auto-detection succeeded, and CPR is clear for take-off. However, we still default to No.
            print(u"[ Required portrait DLCs for CPR auto-detected OK... ]")
            CPR = enableModDefaultNo(u"CPR ({})".format(versions['CPR']), compat=True)

        VIETimmersion = False

        if betaMode:
            VIETimmersion = enableMod(u"VIET Immersion ({})".format(versions['VIET']))

        VIETevents = True if VIETimmersion else enableMod(u"VIET Events ({})".format(versions['VIET']))
        VIETtraits = False if (PB or EMF) else enableMod(u"VIET Traits ({})".format(versions['VIET']))
        VIET = (VIETtraits or VIETevents or VIETimmersion)

        SWMH = enableMod(u'SWMH ({})'.format(versions['SWMH']))
        SWMHnative = True

        if SWMH:
            SWMHnative = enableMod(localise('SWMH_NATIVE'))

		HIP = EMF or PB or VIETimmersion or VIETevents
			
        # Prepare for installation
        if os.path.exists(targetFolder):
            print(u"\nRemoving preexisting '%s' ..." % targetFolder)
            sys.stdout.flush()
            startTime = time.time()
            rmTree(targetFolder, 'target folder preexists. removing...')
            endTime = time.time()
            print(u'Removed (%0.1f sec).\n' % (endTime - startTime))

        mkTree(targetFolder)

        # Install...
        global targetSrc
        targetSrc = {}

        moduleOutput = ["Historical Immersion Project (%s)\nEnabled modules:\n" % versions['pkg']]
        dbg.push('performing virtual filesystem merge...')

        if EMF or PB or VIETimmersion:
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
            if HIP:
                popTree("gfx/event_pictures")
            dbg.pop()

        if HIP:
            pushFolder("HIP_Common")
			
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
            pushFolder("SWMH_Logic")
            dbg.pop()

        if NBRT:
            dbg.push("merging NBRT+...")
            moduleOutput.append("NBRT+ (%s)\n" % versions['NBRT'])
            pushFolder("NBRT+")
            if SWMH and platform == "win":
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
            pushFolder("VIET_Immersion/common")
            if PB:
                pushFolder("VIET_Immersion/PB")
                if EMF:
                    pushFolder("VIET_Immersion/EMF")
            else:
                pushFolder("VIET_Immersion/vanilla")
                pushFolder("Converter/VIET")
            dbg.pop()

        if EMF:
            dbg.push('merging EMF...')
            moduleOutput.append("Extended Mechanics & Flavor [EMF] (%s)\n" % versions['EMF'])
            pushFolder('EMF')
            if SWMH:
                pushFolder('EMF+SWMH')
            if VIETevents:
                pushFolder('EMF+VEvents')
            dbg.pop()

        if CPR:
            dbg.push('merging CPR...')
            moduleOutput.append("Cultures and Portaits Revamp (%s)\n" % versions['CPR'])
            pushFolder('Cultures and Portraits Revamp/common')
            if SWMH:
                pushFolder('Cultures and Portraits Revamp/SWMH')
            elif VIETimmersion:
                pushFolder('Cultures and Portraits Revamp/VIET')
            elif PB:
                pushFolder('Cultures and Portraits Revamp/PB')
            else:
                pushFolder('Cultures and Portraits Revamp/Vanilla')
            dbg.pop()

        dbg.pop("virtual filesystem merge complete")

        startTime = time.time()

        # do all the actual compilation (file I/O)
        compileTarget()

        if move:
            rmTree("modules")  # Cleanup

        endTime = time.time()
        print(u'Installed (%0.1f sec).\n' % (endTime - startTime))

        mapFilename = os.path.join(targetFolder, "file2mod_map.txt")
        print(u"Mapped listing of all compiled files to their source modules:")
        print(unicode(mapFilename + '\n'))

        # Generate a new .mod file, regardless of whether it's default
        if targetFolder != defaultFolder:
            modFileBase = 'HIP_' + targetFolder
        else:
            modFileBase = 'HIP'

        modFilename = modFileBase + '.mod'

        # CKII command line argument parser can't handle dashes in .mod file names (which are passed as arguments to
        # CKII.exe by the launcher)
        if '-' in modFilename:
            modFilename = modFilename.replace('-', '__')

        dbg.trace("generating .mod file " + quoteIfWS(modFilename))

        with open(modFilename, "w") as modFile:
            modFile.write('name = "HIP - %s"  # Name to use as a dependency if making a sub-mod\n' % targetFolder)
            modFile.write('path = "mod/%s"\n' % targetFolder)
            if platform != 'mac':
                modFile.write('user_dir = "%s"  '
                              '# Ensure we get our own versions of the gfx/map caches and log folders\n' %
                              modFileBase)

        print(u"Generated new mod definition file:")
        print(unicode(modFilename + '\n'))

        # Dump modules selected and their respective versions to <mod>/version.txt
        versionFilename = os.path.join(targetFolder, "version.txt")

        with open(versionFilename, "w") as output:
            output.write("".join(moduleOutput))

        dbg.trace("dumping compiled modpack version summary to " + quoteIfWS(versionFilename))
        print(u"Summarized mod combination/versions (INCLUDE FILE CONTENTS IN BUG REPORTS):")
        print(unicode(versionFilename + "\n"))

        # Reset all gfx/map/interface/logs cache for every instance of a preexisting
        # user_dir that includes HIP, platform-agnostic.
        resetCaches()

        # Installation complete
        dbg.trace("installation complete")
        promptUser(localise('INSTALL_DONE'))

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
    import codecs
    import locale

    encoding = locale.getpreferredencoding()
    writer = codecs.getwriter(encoding)
    sys.stdout = writer(sys.stdout, errors='ignore')

    sys.exit(main())
