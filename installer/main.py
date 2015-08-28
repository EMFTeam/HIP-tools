#!/usr/bin/python
# -*- coding: cp1252 -*-
# -*- python-indent-offset: 4 -*-

import os
import sys
import shutil
import traceback
import time
import re


g_version = {'major': 2, 'minor': 1, 'patch': 8,
             'Developer':       'zijistark <zijistark@gmail.com>',
             'Release Manager': 'zijistark <zijistark@gmail.com>'}


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
                    'en': u"\nHIP installer version: {}\n\n"
                          u"All prompts require a yes/no answer. The default answer for any particular\n"
                          u"prompt is shown in brackets directly following it (e.g, '[yes]' or '[no]').\n"
                          u"To answer yes, enter 'y' or 'yes'. To answer no, enter 'n' or 'no'. For the\n"
                          u"default, simply hit ENTER.\n\n"
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
                    'fr': u"> Compilation ...",
                    'es': u"> Compilar ...",
                    'en': u"> Compiling ...",
                },
            'SWMH_NATIVE':
                {
                    'fr': u"SWMH avec les noms culturels locaux, plutôt qu'en anglais ou francisés",
                    'es': u"SWMH con localizacion nativa para culturas y titulos, en lugar de ingles",
                    'en': u"SWMH with native localisation for cultures/titles, rather than English",
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
                    'en': u"\nAre you sure?\n"
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
    return i18n[key][g_language]


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
        self.trace('{} {{'.format(s))
        self.i += 1

    def pop(self, s=None):  # Pop indent stack
        if self.i <= 0:
            raise InstallerTraceNestingError()
        self.i -= 1
        self.trace('}')
        if s:
            self.trace(s)


WRAP_NONE  = 0
WRAP_QUICK = 1
WRAP_TOTAL = 2


class TargetSource:
    def __init__(self, folder, srcPath, isDir=False, wrap=WRAP_NONE):
        self.folder = folder
        self.srcPath = srcPath
        self.isDir = isDir
        self.wrap = wrap


g_bannedFileExt = ['.pdn', '.psd', '.xcf', '.bak', '.tmp', '.rar', '.zip', \
                   '.7z', '.gz', '.tgz', '.xz', '.bz2', '.tar', '.ignore', \
                   '.xls', '.xlsx', '.xlsm', '.db']


def isFileWanted(path):
    root, extension = os.path.splitext(path)
    return (extension.lower() not in g_bannedFileExt   and \
            not os.path.basename(root).startswith('.') and \
            not path.endswith('~'))


def isFileQuickUnwrapped(path):
    _, extension = os.path.splitext(path)
    return extension.lower() in ['.dds', '.tga']


def isYes(answer):
    yesSet = {'fr': ('', 'o', 'oui'),
              'es': ('', 's', 'si'),
              'en': ('', 'y', 'yes')}
    return answer in yesSet[g_language]


def isYesDefaultNo(answer):
    yesSet = {'fr': ('o', 'oui'),
              'es': ('s', 'si'),
              'en': ('y', 'yes')}
    return answer in yesSet[g_language]


def promptUser(prompt, lc=True):
    sys.stdout.write(prompt + u' ')
    sys.stdout.flush()
    response = sys.stdin.readline().strip()  # TODO: broken if diff locales use non-ASCII chars in response
    return response.lower() if lc else response


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
        g_dbg.trace(traceMsg)
    if os.path.exists(directory):
        g_dbg.trace("rmdir('{}')".format(directory))
        shutil.rmtree(directory)


def rmFile(f, traceMsg=None):
    if traceMsg:
        g_dbg.trace(traceMsg)
    g_dbg.trace('rm("{}")'.format(f))
    os.remove(f)


def mkTree(d, traceMsg=None):
    if traceMsg:
        g_dbg.trace(traceMsg)
    g_dbg.trace("mkdir('{}')".format(d))
    os.makedirs(d)


def pushFolder(folder, targetFolder, ignoreFiles=None, prunePaths=None, wrapPaths=None):
    if ignoreFiles is None:
        ignoreFiles = set()
    if prunePaths is None:
        prunePaths = set()
    if wrapPaths is None:
        wrapPaths = set()

    #print(localise('PUSH_FOLDER').format(unicode(quoteIfWS(folder))))

    # normalize paths in ignoreFiles and prunePaths

    folder = os.path.normpath(folder)
    srcFolder = os.path.join('modules', folder)

    if not os.path.exists(srcFolder):
        g_dbg.trace("MODULE_NOT_FOUND('{}')".format(folder))
        return

    g_dbg.push('push_module("{}")'.format(srcFolder))

    ignoreFiles = {os.path.join(srcFolder, os.path.normpath(x)) for x in ignoreFiles}
    prunePaths = {os.path.join(srcFolder, os.path.normpath(x)) for x in prunePaths}
    wrapPaths = {os.path.join(srcFolder, os.path.normpath(x)) for x in wrapPaths}

    for x in ignoreFiles:
        g_dbg.trace('file_filter("{}")'.format(x))

    for x in prunePaths:
        g_dbg.trace('path_filter("{}")'.format(x))

    for root, dirs, files in os.walk(srcFolder):
        newRoot = root.replace(srcFolder, targetFolder)
        g_dbg.push('push_dir("{}")'.format(root))

        # Prune the source directory walk in-place according to prunePaths option,
        # and, of course, don't create pruned directories (none of the files in
        # them will be copied/moved)
        prunedDirs = []

        for directory in dirs:
            srcPath = os.path.join(root, directory)
#           g_dbg.trace('dir({})'.format(quoteIfWS(srcPath)))
            if srcPath in prunePaths:
                g_dbg.trace('filtered_dir("{}")'.format(srcPath))
            else:
                prunedDirs.append(directory)
                newDir = os.path.join(newRoot, directory)
                g_targetSrc[newDir] = TargetSource(folder, srcPath, isDir=True)

        dirs[:] = prunedDirs  # Filter subdirectories into which we should recurse on next os.walk()
        nPushed = 0

        wrapped = False

        for p in wrapPaths:
            if root.startswith(p):
                wrapped = True

        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(newRoot, f)

            if not isFileWanted(src):
                g_dbg.trace('unwanted_file("{}")'.format(src))
                continue
            if src in ignoreFiles:  # Selective ignore filter for individual files
                g_dbg.trace('filtered_file("{}")'.format(src))
                continue

#           g_dbg.trace(quoteIfWS(dst) + ' <= ' + quoteIfWS(src))

            wrapType = WRAP_NONE

            if wrapped and not src.endswith('version.txt'):
                wrapType = WRAP_QUICK if isFileQuickUnwrapped(src) else WRAP_TOTAL

            g_targetSrc[dst] = TargetSource(folder, src, wrap=wrapType)
            nPushed += 1

        g_dbg.trace('num_files_pushed({})'.format(nPushed))
        g_dbg.pop()
    g_dbg.pop()


def popFile(f, targetFolder):
    f = os.path.normpath(f)
    p = os.path.join(targetFolder, f)
    if p in g_targetSrc:
        g_dbg.trace("pop_file('{}')".format(p))
        del g_targetSrc[p]


def popTree(d, targetFolder):
    d = os.path.normpath(d)
    t = os.path.join(targetFolder, d)
    g_dbg.push("pop_path_prefix('{}')".format(t))
    for p in [p for p in g_targetSrc.keys() if p.startswith(t)]:
        g_dbg.trace(p)
        del g_targetSrc[p]
    g_dbg.pop()


def stripPathHead(path):
    i = path.find('/')
    if i == -1:
        i = path.find(r'\\')
    if i == -1:
        i = path.find('\\')
    if i == -1:
        raise InstallerPathException()
    newStart = i + 1
    return path[newStart:]


g_k  = bytearray(br'"The enemy of a good plan is the dream of a perfect plan" - Carl von Clausewitz')


def unwrapBuffer(buf, length):
    kN = len(g_k)
    for i in xrange(length):
        buf[i] ^= g_k[i % kN]


def unwrapToFile(src, dst, quickMode=False):
    length = os.path.getsize(src)
    buf = bytearray(length)
    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
        fsrc.readinto(buf)
        if quickMode:
            length = min(1 << 12, length)
        unwrapBuffer(buf, length)
        fdst.write(buf)


def compileTarget(mapFilename):
    print(localise('COMPILING'))
    sys.stdout.flush()

    x = len(g_targetSrc) // 20

    with open(mapFilename, "w") as mapFile:
        for n, dstPath in enumerate(sorted(g_targetSrc)):

            if n and n % x == 0:
                print(u"{}%".format((n // x * 5)))
                sys.stdout.flush()

            src = g_targetSrc[dstPath]
            mapFile.write('%s <= [%s]\n' % (stripPathHead(dstPath), src.folder))

            if src.isDir:
                mkTree(dstPath)
            elif g_move and src.wrap == WRAP_NONE:
                shutil.move(src.srcPath, dstPath)
            elif src.wrap == WRAP_NONE:
                shutil.copy(src.srcPath, dstPath)
            elif src.wrap == WRAP_QUICK:
                unwrapToFile(src.srcPath, dstPath, quickMode=True)
            elif src.wrap == WRAP_TOTAL:
                unwrapToFile(src.srcPath, dstPath)


def detectPlatform():
    p = sys.platform
    if p.startswith('darwin'):
        return 'mac'
    elif p.startswith('linux'):
        return 'lin'
    elif p.startswith('win'):
        return 'win'
    elif p.startswith('cygwin'):
        return 'cyg'
    raise InstallerPlatformError()


def cleanUserDir(userDir):
    g_dbg.push('clean_userdir("{}")'.format(userDir))
    for d in [os.path.join(userDir, e) for e in ['gfx', 'map']]:
        rmTree(d)
    g_dbg.pop()


def resetCaches():
    if g_platform == 'mac':
        print(u'Clearing preexisting CKII gfx/map cache')
        cleanUserDir('..')  # TODO: Find out if the user_dir changes with the new 2.1.5 launcher
    elif g_platform == 'win' or g_platform == 'cyg':
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
    d = os.path.dirname(g_programPath)
    if d != '':
        os.chdir(d)


# noinspection PyDictCreation
def initVersionEnvInfo():
    global g_version
    g_version['Version'] = '{}.{}.{}'.format(g_version['major'], g_version['minor'], g_version['patch'])

    ## if 'Commit-ID' in version:
    ## versionStr += '.git~' + version['Commit-ID'][0:7]

    # Note that the above generates a version string that is lexicographically
    # ordered from semantic 'earlier' to 'later' in all cases, including variable
    # numbers of digits in any of the components.

    # We have a relative or absolute path in sys.argv[0] (in either case, it may
    # still be the right directory, but we'll have to find out).

    if len(sys.argv) == 0 or sys.argv[0] == '':
        raise InstallerEmptyArgvError()

    global g_programPath

    # Resolve any symbolic links in path elements and canonicalize it
    g_programPath = os.path.realpath(sys.argv[0])

    # Make sure it's normalized and absolute with respect to platform conventions
    g_programPath = os.path.abspath(g_programPath)


def printVersionEnvInfo():
    # Print the installer's version info (installer *script*, not module package)
    print(u'HIP Installer:')

    # Fill this with any extended version info keys we want printed, if present.
    # This is the order in which they'll be displayed.
    extKeys = ['Version', 'Commit ID', 'Primary Developer', 'Developer', 'Release Manager']

    # Resolve optional keys to found keys
    extKeys = [k for k in extKeys if k in g_version]

    if extKeys:
        extVals = [g_version[k] for k in extKeys]
        extKeys = [k + ': ' for k in extKeys]
        maxKeyWidth = len(max(extKeys, key=len))
        for k, v in zip(extKeys, extVals):
            print('% -*s%s' % (maxKeyWidth, k, v))  # TODO: needs to be upgraded to use format() and output UTF-8
        sys.stdout.write('\n')

    print(u'HIP Installer Path: ')
    print(unicode(g_programPath + '\n'))

    # Print the OS version/build info
    import platform as p

    print(u'Operating System / Platform:')
    print(unicode(sys.platform + ': ' + p.platform() + '\n'))

    # Print our runtime interpreter's version/build info

    print(u"Python Runtime Version:")
    print(unicode(sys.version))
    return


def getPkgVersions(modDirs):
    global g_versions
    g_versions = {}
    g_dbg.push("read_versions")
    for mod in modDirs.keys():
        f = os.path.join("modules", modDirs[mod], "version.txt")
        if os.path.exists(f):
            g_versions[mod] = unicode(open(f).readline().strip())
        else:
            g_versions[mod] = u'no version'
        g_dbg.trace("version('%s' => '%s')" % (mod, g_versions[mod]))
    g_dbg.pop()


def getInstallOptions():
    # Determine user g_language for installation
    global g_language
    global g_betaMode

    g_language = '' if (g_steamMode or g_zijiMode) else promptUser(u"For English, hit ENTER. En français, taper 'f'. "
                                                                   u"Para español, presiona 'e'.")

    if g_language.startswith('B') or g_language.startswith('b'):
        g_language = 'en'
        g_betaMode = True
    elif g_language == 'f':
        g_language = 'fr'
    elif g_language == 'e':
        g_language = 'es'
    else:
        g_language = 'en'

    # Show HIP installer version & explain interactive prompting
    if not (g_steamMode or g_zijiMode):
        print(localise('INTRO').format(g_versions['pkg']))

    global g_move
    #g_move = False if (g_steamMode or g_zijiMode) else isYes(promptUser(localise('MOVE_VS_COPY')))
    g_move = False

    if g_move:
        g_move = isYes(promptUser(localise('MOVE_CONFIRM')))
    g_dbg.trace('move_instead_of_copy({})'.format(g_move))

    # Determine installation target folder...
    global g_defaultFolder
    g_defaultFolder = 'Historical Immersion Project'
    targetFolder = ''

    useCustomFolder = False if (g_steamMode or g_zijiMode) else \
         isYesDefaultNo(promptUser(u'Do you want to install to a custom folder / mod name? [no]'))

    if useCustomFolder:
        # Note that we use the case-preserving form of promptUser (also determines name in launcher)
        targetFolder = '' if (g_steamMode or g_zijiMode) \
            else promptUser(localise('TARGET_FOLDER').format(unicode(g_defaultFolder)), lc=False)

    if targetFolder == '':
        targetFolder = g_defaultFolder

    g_dbg.trace('target_folder("{}")'.format(targetFolder))
    return targetFolder


# Find Steam master folder by checking the Windows Registry (32-bit mode and 64-bit mode are separate invocations)
def getSteamMasterFolderFromRegistry(x64Mode=True):
    pathVariant = r'\Wow6432Node' if x64Mode else ''
    keyPath = r'SOFTWARE{}\Valve\Steam'.format(pathVariant)

    g_dbg.push('search_winreg_key("{}")'.format(keyPath))

    # TODO:
    # _winreg import will fail on Python 3, so a check against the Python major version and subsequent conditional
    # import of 'winreg' instead of '_winreg' in that case *should* make this part of the script v2/v3-safe.

    # NOTE: cygwin Python lacks _winreg

    import _winreg
    from _winreg import HKEY_LOCAL_MACHINE

    try:
        hReg = _winreg.ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        hKey = _winreg.OpenKey(hReg, keyPath)

        folder = _winreg.QueryValueEx(hKey, 'InstallPath')

        if not folder:
            raise EnvironmentError()

        g_dbg.trace('winreg_key_found(InstallPath => "{}")'.format(folder[0]))

        hKey.Close()
        hReg.Close()

        return os.path.join(folder[0], 'steamapps')

    except EnvironmentError:
        return None

    finally:
        g_dbg.pop()


def getSteamMasterFolderFallbackCygwin():
    cygdrive = '/cygdrive'
    maybePaths = ['Program Files (x86)/Steam',
                  'Program Files/Steam'
                  'SteamLibrary',
                  'Steam',
                  'Games/Steam']

    g_dbg.push('find_steam_master_cygwin("{}")'.format(cygdrive))

    for d in os.listdir(cygdrive):
        for maybePath in maybePaths:
            masterFolder = os.path.join(cygdrive, d, maybePath, 'steamapps')
            g_dbg.trace('search("{}")'.format(masterFolder))
            if os.path.exists(os.path.join(masterFolder, 'libraryfolders.vdf')):
                g_dbg.pop()
                return masterFolder

    g_dbg.pop()
    return None


def getSteamMasterFolder():
    g_dbg.push('find_steam_master')
    folder = None
    if g_platform == 'mac':
        folder = os.path.expanduser('~/Library/Application Support/Steam/SteamApps')
        if not os.path.exists(folder):
            folder = os.path.expanduser('~/Library/Application Support/Steam/steamapps')
    elif g_platform == 'lin':
        folder = os.path.expanduser('~/.steam/steam/steamapps')
        if not os.path.exists(folder):
            folder = os.path.expanduser('~/.steam/steam/SteamApps')
    elif g_platform == 'cyg':
        folder = getSteamMasterFolderFallbackCygwin()
    elif g_platform == 'win':
        folder = getSteamMasterFolderFromRegistry()
        if folder is None:
            folder = getSteamMasterFolderFromRegistry(x64Mode=False)  # Try the 32-bit registry key

    if folder and os.path.exists(folder):
        g_dbg.pop('steam_master("{}")'.format(folder))
        return folder
    else:
        g_dbg.pop('steam_master(NOT_FOUND)')
        return None


def readSteamLibraryFolders(dbPath):
    g_dbg.push('read_steam_master_library_db("{}")'.format(dbPath))
    p_library = re.compile(r'^\s*"\d+"\s+"([^"]+)"\s*$')
    folders = []
    with open(dbPath, 'rb') as f:
        while True:
            line = f.readline()
            if len(line) == 0:
                g_dbg.pop("num_external_libraries_found({})".format(len(folders)))
                return folders
            line = line.rstrip('\r\n')
            m = p_library.match(line)
            if m:
                p = m.group(1).replace(r'\\', '/')
                if g_platform == 'cyg':
                    i = p.find(':/')
                    if i == 1:
                        drive = p[:1]
                        p = p.replace(p[:2], '/cygdrive/' + drive.lower(), 1)
                path = os.path.join(os.path.normpath(p), 'steamapps')
                g_dbg.trace('external_library("{}")'.format(path))
                if os.path.exists(path):
                    folders.append(path)


def getSteamGameFolder(masterFolder, gameName, magicFile):
    path = os.path.join(masterFolder, 'common', gameName)
    g_dbg.trace('potential_game_folder("{}")'.format(path))
    if os.path.exists(os.path.join(path, magicFile)):
        return path

    libraryDBPath = os.path.join(masterFolder, 'libraryfolders.vdf')
    if not os.path.exists(libraryDBPath):
        g_dbg.trace('steam_master_library_db(NOT_FOUND)')
        return None

    for f in readSteamLibraryFolders(libraryDBPath):
        path = os.path.join(f, 'common', gameName)
        g_dbg.trace('potential_game_folder("{}")'.format(path))
        if os.path.exists(os.path.join(path, magicFile)):
            return path

    return None


cprReqDLCNames = {'dlc/dlc013.dlc': 'African Portraits',
                  'dlc/dlc028.dlc': 'Celtic Portraits',
                  'dlc/dlc014.dlc': 'Mediterranean Portraits',
                  'dlc/dlc002.dlc': 'Mongol Face Pack',
                  'dlc/dlc020.dlc': 'Norse Portraits',
                  'dlc/dlc016.dlc': 'Russian Portraits',
                  'dlc/dlc039.dlc': 'Rajas of India',
                  'dlc/dlc041.dlc': 'Turkish Portraits',
                  'dlc/dlc044.dlc': 'Persian Portraits',
                  'dlc/dlc046.dlc': 'Early Western Clothing Pack',
                  'dlc/dlc047.dlc': 'Early Eastern Clothing Pack',
                  'dlc/dlc052.dlc': 'Iberian Portraits',
                  'dlc/dlc057.dlc': 'Cuman Portraits'}


# Determine whether the DLCs required for CPR are installed in the active game folder.
# Returns None if DLC detection (game folder detection) fails, an empty list if all
# requirements are met, and otherwise the exact list of the missing DLCs' names.
def detectCPRMissingDLCs():
    # Normalize path keys denormReqDLCNames, platform-specific (varies even between cygwin and win32)
    reqDLCNames = {os.path.normpath(f): cprReqDLCNames[f] for f in cprReqDLCNames.keys()}

    masterFolder = getSteamMasterFolder()
    if not masterFolder:
        return None

    gameFolder = getSteamGameFolder(masterFolder, 'Crusader Kings II', 'dlc')

    if not gameFolder:
        g_dbg.trace('game_folder(NOT_FOUND)')
        return None

    g_dbg.trace('game_folder("{}")'.format(gameFolder))

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


def scaffoldMod(baseFolder, targetFolder, modBasename, modName, modPath, modUserDir=None, eu4Version=None):
    # Remove preexisting target folder...
    if os.path.exists(targetFolder):

        if not g_steamMode:
            sys.stdout.write('\n')

        print(u"> Removing preexisting '%s' ..." % targetFolder)
        sys.stdout.flush()
        startTime = time.time()
        rmTree(targetFolder, 'rm_preexisting_mod("{}")'.format(targetFolder))
        endTime = time.time()
        print(u'> Removed (%0.1f sec).\n' % (endTime - startTime))
        sys.stdout.flush()

    mkTree(targetFolder)

    modFilename = modBasename + '.mod'

    # CKII command line argument parser can't handle dashes in .mod file names (which are passed as arguments to
    # CKII.exe by the launcher)
    if '-' in modFilename:
        modFilename = modFilename.replace('-', '__')
    if ' ' in modFilename:
        modFilename = modFilename.replace(' ', '+')

    modFilename = os.path.join(baseFolder, modFilename)

    # Generate a new .mod file...
    g_dbg.trace('write_dot_mod("{}")'.format(modFilename))

    with open(modFilename, "w") as modFile:
        modFile.write('name = "{}"  # Name to use as a dependency if making a sub-mod\n'.format(modName))
        modFile.write('path = "mod/{}"\n'.format(modPath))
        if modUserDir is not None:
            modFile.write('user_dir = "%s"  '
                          '# Ensure we get our own versions of the gfx/map caches and savegames\n' %
                          modBasename)
        if eu4Version is not None:
            modFile.write('supported_version = {}\n'.format(eu4Version))

    return modFilename


def main():
    # noinspection PyBroadException
    try:
        initLocalisation()
        initVersionEnvInfo()

        g_dbgMode = (len(sys.argv) > 1 and '-D' in sys.argv[1:])
        versionMode = (len(sys.argv) > 1 and '-V' in sys.argv[1:])

        global g_steamMode
        global g_zijiMode
        g_steamMode = (len(sys.argv) > 1 and '-S' in sys.argv[1:])
        g_zijiMode = (len(sys.argv) > 1 and '-Z' in sys.argv[1:])

        global g_betaMode
        g_betaMode = False

        global g_dbg
        g_dbg = DebugTrace(open('HIP_debug.log', 'w'), prefix='') if g_dbgMode else NullDebugTrace()

        global g_platform
        g_platform = detectPlatform()
        g_dbg.trace('platform({})'.format(g_platform))

        if versionMode:
            printVersionEnvInfo()
            return 0

        # Ensure the runtime's current working directory corresponds exactly to the
        # location of this module itself. In other words, allow it to be run from
        # anywhere on the system but still be able to assume the relative path to,
        # e.g., "modules/" is just that.
        normalizeCwd()

        if not os.path.isdir('modules'):
            raise InstallerPackageNotFoundError()

        # These are the modules/ directories from which to grab each mod's version.txt:
        modDirs = {'pkg': '',  # Installer package version
                   'VIET': 'VIET_Assets',
                   'SWMH': 'SWMH',
                   'NBRT': 'NBRT+',
                   'CPR': 'CPRplus',
                   'EMF': 'EMF',
                   'SED': 'SED2',
                   'ARKOC': 'ARKOpack_Armoiries',
                   'ARKOI': 'ARKOpack_Interface',
                   'ArumbaKS': 'ArumbaKS',
        }

        getPkgVersions(modDirs)

        # Prompt user for options related to this install
        targetFolder = getInstallOptions()

        if (not g_steamMode) and not g_zijiMode:
            sys.stdout.write('\n')

        # Determine module combination...

        # EMF...
        EMF = True if g_steamMode else enableMod(u"EMF ({})".format(g_versions['EMF']))

        # ARKOpack...
        ARKOCoA = True if g_steamMode \
            else enableMod(u"ARKOpack Armoiries [CoA] ({})".format(g_versions['ARKOC']))
        
        if (not g_steamMode) and not g_zijiMode:
            print(u"\nNOTE: Arumba's Keyboard Shortcuts and ARKOpack Interface are incompatible.\n"
                  u"      ARKOpack doesn't provide shortcuts. You may only select one of the two:\n")
        
        ARKOInt = False if (g_steamMode or g_zijiMode) \
            else enableMod(u"ARKOpack Interface ({})".format(g_versions['ARKOI']))

        # Arumba's Keyboard Shortcuts...
        ArumbaKS = False

        if not ARKOInt:
            ArumbaKS = True if (g_steamMode or g_zijiMode) \
                else enableMod(u"Arumba's Keyboard Shortcuts ({})".format(g_versions['ArumbaKS']))

        # CPRplus...
        CPR = False
        CPRfaces = False

        if not g_steamMode:
            cprMissingDLCNames = detectCPRMissingDLCs()

            if cprMissingDLCNames is None:  # Failed to auto-detect game folder
                if not g_zijiMode:
                    print(u"\nOOPS: The HIP installer could NOT successfully determine your active CKII\n"
                          u"game folder! Thus, it cannot auto-detect whether you meet all the portrait DLC\n"
                          u"prerequisites for CPRplus. All _other_ HIP modules can be installed, however.\n")

            elif len(cprMissingDLCNames) > 0:  # DLC auto-detection succeeded, but there were missing DLCs.
                if not g_zijiMode:
                    print(u"\n\nCPRplus (portrait upgrade mod) requires portrait pack DLCs which you,\n"
                          u"unforunately, are lacking. If you want to use CPRplus, you'll need to install\n"
                          u"the following DLCs first:\n")

                    for name in sorted(cprMissingDLCNames):
                        print(u"+ {}".format(name))

                    sys.stdout.write('\n')

            else:  # DLC verification succeeded, and CPR is clear for take-off.
                CPR = enableMod(u"CPRplus ({})".format(g_versions['CPR']))
                CPRfaces = False if not CPR else enableMod(u"CPRplus's custom western & muslim facial art")

        ## VIET ...
        VIETevents = False
        if g_steamMode:
            VIETevents = True
        elif not g_zijiMode:
            VIETevents = enableMod(u"VIET Events ({})".format(g_versions['VIET']))

        VIETtraits = False if EMF else enableMod(u"VIET Traits ({})".format(g_versions['VIET']))
        VIET = (VIETtraits or VIETevents)

        # SWMH...
        SWMH = False
        
        if (not g_steamMode) and not g_zijiMode:
            print(u"\nNOTE: The SWMH map will never include the 769 bookmark. However, SWMH does\n"
                  u"support all Charlemagne DLC mechanics in 867 and beyond. SWMH is also a very\n"
                  u"large map (35% more provinces than vanilla), and this can deter performance.\n"
                  u"If you want the vanilla map instead, simply type 'n' or 'no' for SWMH below:\n")

        SWMH = False if g_steamMode else enableMod(u'SWMH ({})'.format(g_versions['SWMH']))

        # SED...
        SED = SWMH and g_zijiMode
        if SWMH and not g_steamMode and not SED:
            SED = enableModDefaultNo(u'SED: English Localisation for SWMH ({})'.format(g_versions['SED']), compat=True)

        # NBRT+...
        if g_platform == 'win' or g_platform == 'cyg':
            NBRT = True if (g_steamMode or g_zijiMode) else enableMod(u"NBRT+ ({})".format(g_versions['NBRT']))
        else:
            NBRT = False if g_steamMode else enableModDefaultNo(u"NBRT+ ({})".format(g_versions['NBRT']))

        HIP = EMF or SWMH or VIETevents  # HIP_Common (Isis, e_hip, our event picture stash, etc.)
        # Converter = EMF and not SWMH  # Vanilla EUIV Converter

        euFolderBase = '../eu4_export/mod'
        euSubfolder = 'HIP_Converter'
        euFolder = euFolderBase + '/' + euSubfolder

        # Prepare for installation...

        if targetFolder != g_defaultFolder:
            modBasename = 'HIP_' + targetFolder
        else:
            modBasename = 'HIP'

        modFilename = scaffoldMod('.',
                                  targetFolder,
                                  modBasename,
                                  'HIP - ' + targetFolder,
                                  targetFolder,
                                  modBasename)

#        if Converter:
#            euModFilename = scaffoldMod(euFolderBase,
#                                        euFolder,
#                                        'HIP_Converter',
#                                        'HIP Converter Support',
#                                        euSubfolder,
#                                        eu4Version='1.10')

        # Prepare file mappings...
        global g_targetSrc
        g_targetSrc = {}

        moduleOutput = ["[HIP Release %s]\nEnabled HIP modules:\n" % g_versions['pkg']]
        g_dbg.push('merge_all')

        if EMF:
            moduleOutput.append("EMF: Extended Mechanics & Flavor (%s)\n" % g_versions['EMF'])
        
        if ARKOInt:
            g_dbg.push("merge('ARKO Interface')")
            moduleOutput.append("ARKO Interface (%s)\n" % g_versions['ARKOI'])
            pushFolder("ARKOpack_Interface", targetFolder)
            if HIP:
                popTree('gfx/event_pictures', targetFolder)
            g_dbg.pop()

        if ArumbaKS:
            g_dbg.push('merge(ArumbaKS)')
            moduleOutput.append("Arumba's Keyboard Shortcuts (%s)\n" % g_versions['ArumbaKS'])
            pushFolder('ArumbaKS', targetFolder)
            g_dbg.pop()

        if VIET:
            pushFolder("VIET_Assets", targetFolder)

        if HIP:
            pushFolder("HIP_Common", targetFolder)

        if SWMH:
            g_dbg.push("merge(SWMH)")
            moduleOutput.append("SWMH (%s)\n" % g_versions['SWMH'])
            pushFolder("SWMH", targetFolder)
            if ARKOInt:
                pushFolder("SWMH+ArkoInterface", targetFolder)
            elif ArumbaKS:
                pushFolder("SWMH+ArumbaKS", targetFolder)
            g_dbg.pop()

        if SED:
            g_dbg.push("merge(SED)")
            moduleOutput.append("SED: English Localisation for SWMH (%s)\n" % g_versions['SED'])
            pushFolder("SED2", targetFolder)
            g_dbg.pop()

        if ARKOCoA:
            g_dbg.push("merge('ARKO CoA')")
            moduleOutput.append("ARKO Armoiries (%s)\n" % g_versions['ARKOC'])
            pushFolder("ARKOpack_Armoiries", targetFolder)
            g_dbg.pop()

        if NBRT:
            g_dbg.push("merge(NBRT)")
            moduleOutput.append("NBRT+ (%s)\n" % g_versions['NBRT'])
            pushFolder("NBRT+", targetFolder)
            if SWMH and (g_platform == 'win' or g_platform == 'cyg') and False:  # Disabled for SWMH EE testing
                pushFolder("NBRT+SWMH", targetFolder)
            if ARKOCoA:
                pushFolder("NBRT+ARKO", targetFolder)
            if not SWMH or True:  # Enabled for SWMH EE testing
                popFile('gfx/FX/pdxmap.fxh', targetFolder)  # Z: 2.2 compatch for NBRT+ Light (and Mac/Linux compatch)
            g_dbg.pop()

        if VIETtraits:
            g_dbg.push("merge('VIET Traits')")
            moduleOutput.append("VIET Traits (%s)\n" % g_versions['VIET'])
            pushFolder("VIET_Traits", targetFolder)
            g_dbg.pop()

        if VIETevents:
            g_dbg.push("merge('VIET Events')")
            moduleOutput.append("VIET Events (%s)\n" % g_versions['VIET'])
            pushFolder("VIET_Events", targetFolder)
            g_dbg.pop()

        if EMF:
            g_dbg.push('merge(EMF)')
            pushFolder('EMF', targetFolder)

            if SWMH:
                pushFolder('EMF+SWMH', targetFolder)
            else:
                pushFolder('EMF+Vanilla', targetFolder)

            if ARKOInt:
                pushFolder("EMF+ArkoInterface", targetFolder)

            g_dbg.pop()

        if CPR:
            g_dbg.push('merge(CPR)')
            moduleOutput.append("CPRplus (%s)\n" % g_versions['CPR'])

            wrappedPaths = set(['gfx'])
            pushFolder('CPRplus', targetFolder, wrapPaths=wrappedPaths)

            if CPRfaces:
                pushFolder('CPRplus-compatch/CustomFaces', targetFolder)

            if SWMH:
                pushFolder('CPRplus-compatch/SWMH', targetFolder)
            elif EMF:
                pushFolder('CPRplus-compatch/EMF', targetFolder)

            g_dbg.pop()

#        if Converter:
#            pushFolder("Converter/Vanilla", targetFolder)
#            pushFolder("Converter/Extra", euFolder)

        g_dbg.pop("merge_done")

        # Where to dump a mapping of all the compiled files to their source modules (will include stuff from outside
        # targetFolder for now too if such stuff is pushed on to the virtual filesystem)
        mapFilename = os.path.join(targetFolder, "file2mod_map.txt")

        startTime = time.time()

        # do all the actual compilation (file I/O)
        compileTarget(mapFilename)

        if g_move:
            rmTree("modules")  # Cleanup

        endTime = time.time()
        print(u'> Compiled (%0.1f sec).\n' % (endTime - startTime))

        if not g_steamMode:
            print(u"Mapping of all compiled mod files to their HIP source modules:")
            print(unicode(mapFilename + '\n'))

        # Dump modules selected and their respective g_versions to <mod>/version.txt
        versionFilename = os.path.join(targetFolder, "version.txt")

        with open(versionFilename, "w") as output:
            output.write("".join(moduleOutput))

        print(u"Summary of mod combination & versions (INCLUDE THIS FILE IN BUG REPORTS):")
        print(unicode(versionFilename + "\n"))

        # Reset all gfx/map/interface/logs cache for every instance of a preexisting
        # user_dir that includes HIP, platform-agnostic.
        resetCaches()

        # Installation complete
        g_dbg.trace("install_done")
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
