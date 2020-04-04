#!python2

from __future__ import print_function

import hashlib
import os
import sys
import shutil
import traceback
import time
import re

YES = 'yes'
NO = 'no'

g_version = {'major': 2, 'minor': 9, 'patch': 1,
             'Primary Developer': 'Matthew D. Hall <zijistark@gmail.com>',
             # 'Developer': 'Gabriel Rath', # perhaps?
             'Release Manager':   'Matthew D. Hall <zijistark@gmail.com>'}

g_text = {}

g_text['INTRO'] = '''\
+==============================================================================+
|{}|
+==============================================================================+

All prompts require a yes/no answer. The default answer for any particular
prompt is shown in brackets directly following it (e.g., "[yes]" or "[no]").
To answer yes, type "y" or "yes". To answer no, type "n" or "no". For the
default choice, simply hit the ENTER / RETURN key.

If at any time you wish to abort the installation, press Ctrl+C.
'''

g_text['ENABLE_MOD_NOT_DEFAULT_COMPAT'] = '''
NOTE: {} might be incompatible with your system.
Install {}? [no]'''

g_text['TARGET_FOLDER'] = '''
Installing the mod into a folder that exists will first delete that folder.
Into what folder would you like to install?

Leave blank for "{}":'''

g_text['INSTALL_DONE'] = 'Installation complete. Hit ENTER to exit.'
g_text['ENABLE_MOD'] = 'Install {}? [yes]'
g_text['ENABLE_MOD_NOT_DEFAULT'] = 'Install {}? [no]'
g_text['ENABLE_MOD_XOR'] = 'Install {} ({})? [yes]'
g_text['ENABLE_MOD_XOR_WARN'] = '\n{} and {} are incompatible. You may only select one:'
g_text['PUSH_FOLDER'] = 'Preparing {}'
g_text['COMPILING'] = '> Compiling ...'

def localise(key):
    return g_text[key]


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
        if s:
            self.trace(s)
        self.i -= 1
        self.trace('}')


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

def isYesDefaultNo(answer):
    return answer in ('y', 'yes', 'ye', 'es', 'ys', 'si', 's', 'ja', 'j', 'oui', 'd', 'da', 'tak')

def isYes(answer):
    return answer in ('', 'ok') or isYesDefaultNo(answer)


def promptUser(prompt, lc=True):
    sys.stdout.write(prompt + ' ')
    sys.stdout.flush()
    response = sys.stdin.readline().strip().strip("\"'").strip()
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


def rmFile(f, traceMsg=None):
    if traceMsg:
        g_dbg.trace(traceMsg)
    g_dbg.trace('rm("{}")'.format(f))
    os.remove(f)


def rmTree(f, traceMsg=None):
    if traceMsg:
        g_dbg.trace(traceMsg)
    if os.path.exists(f):
        if os.path.isdir(f):
            g_dbg.trace("rmTree('{}')".format(f))
            shutil.rmtree(f)
        else:
            rmFile(f)


def mkTree(d, traceMsg=None):
    if traceMsg:
        g_dbg.trace(traceMsg)
    g_dbg.trace("mkTree('{}')".format(d))
    os.makedirs(d)


def pushFolder(folder, targetFolder, ignoreFiles=None, prunePaths=None, wrapPaths=None):
    if ignoreFiles is None:
        ignoreFiles = set()
    if prunePaths is None:
        prunePaths = set()
    if wrapPaths is None:
        wrapPaths = set()
    # normalize paths in ignoreFiles and prunePaths
    folder = os.path.normpath(folder)
    srcFolder = os.path.join('modules', folder)
    if not os.path.exists(srcFolder):
        g_dbg.trace("MODULE_NOT_FOUND('{}')".format(folder))
        return
    g_dbg.push('pushModule("{}")'.format(srcFolder))
    ignoreFiles = {os.path.join(srcFolder, os.path.normpath(x)) for x in ignoreFiles}
    prunePaths = {os.path.join(srcFolder, os.path.normpath(x)) for x in prunePaths}
    wrapPaths = {os.path.join(srcFolder, os.path.normpath(x)) for x in wrapPaths}
    for x in ignoreFiles:
        g_dbg.trace('ignoredFile("{}")'.format(x))
    for x in prunePaths:
        g_dbg.trace('prunedPath("{}")'.format(x))
    for root, dirs, files in os.walk(srcFolder):
        newRoot = root.replace(srcFolder, targetFolder)
        g_dbg.push('pushDir("{}")'.format(root))
        # Prune the source directory walk in-place according to prunePaths
        # option, and, of course, don't create pruned directories (none of the
        # files in them will be copied/moved)
        prunedDirs = []
        for directory in dirs:
            srcPath = os.path.join(root, directory)
#           g_dbg.trace('dir({})'.format(quoteIfWS(srcPath)))
            if srcPath in prunePaths:
                g_dbg.trace('pruneDir("{}")'.format(srcPath))
            else:
                prunedDirs.append(directory)
                newDir = os.path.join(newRoot, directory)
                g_targetSrc[newDir] = TargetSource(folder, srcPath, isDir=True)
        dirs[:] = prunedDirs
        nPushed = 0
        wrapped = False
        for p in wrapPaths:
            if root.startswith(p):
                wrapped = True
        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(newRoot, f)
            if not isFileWanted(src):
                g_dbg.trace('unwantedFile("{}")'.format(src))
                continue
            if src in ignoreFiles:  # Selective ignore filter for individual files
                g_dbg.trace('filteredFile("{}")'.format(src))
                continue
            wrapType = WRAP_NONE
            if wrapped and not src.endswith('version.txt'):
                wrapType = WRAP_QUICK if isFileQuickUnwrapped(src) else WRAP_TOTAL
            g_targetSrc[dst] = TargetSource(folder, src, wrap=wrapType)
            nPushed += 1
        g_dbg.trace('numFilesPushed({})'.format(nPushed))
        g_dbg.pop()
    g_dbg.pop()


def popFile(f, targetFolder):
    f = os.path.normpath(f)
    p = os.path.join(targetFolder, f)
    if p in g_targetSrc:
        g_dbg.trace('popFile("{}")'.format(p))
        del g_targetSrc[p]


def popTree(d, targetFolder):
    d = os.path.normpath(d)
    t = os.path.join(targetFolder, d)
    g_dbg.push('popPathPrefix("{}")'.format(t))
    for p in [p for p in g_targetSrc.keys() if p.startswith(t)]:
        g_dbg.trace(p)
        del g_targetSrc[p]
    g_dbg.pop()


g_k  = bytearray(br'"The enemy of a good plan is the dream of a perfect plan" - Carl von Clausewitz')


def unwrapBuffer(buf, length):
    kN = len(g_k)
    try:
        for i in xrange(length):  # Py2
            buf[i] ^= g_k[i % kN]
    except NameError:
        for i in range(length):  # Py3
            buf[i] ^= g_k[i % kN]


def compileTargetFile(src, dst, wrap, manifest):
    global g_modified
    length = os.path.getsize(src)
    buf = bytearray(length)
    with open(src, 'rb') as fsrc:
        fsrc.readinto(buf)
    if manifest:
        hash_md5 = hashlib.md5()
        hash_md5.update(buf)
        cksum = hash_md5.hexdigest()
    if wrap != WRAP_NONE:
        if wrap == WRAP_QUICK:
            length = min(1 << 12, length)
        unwrapBuffer(buf, length)
    with open(dst, 'wb') as fdst:
        fdst.write(buf)
    if manifest and manifest.get(src, None) != cksum:
        g_dbg.trace("checksumMismatch('{}')".format(src))
        g_modified = True


# startFolder is the reference point for the relative paths in the map file
def compileTarget(mapFilename, startFolder, manifest):
    print(localise('COMPILING'))
    sys.stdout.flush()
    x = len(g_targetSrc) / 20.0
    with open(mapFilename, 'w') as mapFile:
        for n, dstPath in enumerate(sorted(g_targetSrc)):
            if n > 0 and x > 0 and (x < 1 or n % x < (n - 1) % x):
                print('{}%'.format(int(n / x) * 5))
                sys.stdout.flush()
            src = g_targetSrc[dstPath]
            mapFile.write('{} <= [{}]\n'.format(os.path.relpath(dstPath, startFolder), src.folder))
            if src.isDir:
                mkTree(dstPath)
            else:
                compileTargetFile(src.srcPath, dstPath, src.wrap, manifest)


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
    g_dbg.push('cleanUserDir("{}")'.format(userDir))
    for d in [os.path.join(userDir, e) for e in ['gfx', 'map']]:
        if os.path.isdir(d):
            rmTree(d)


def resetCaches():
    if g_platform in ('win', 'lin', 'cyg', 'mac'):
        print('Clearing preexisting HIP-related CKII gfx/map caches ...')
        dirEntries = ['..'] + [os.path.join('..', e) for e in os.listdir('..')]
        for userDir in dirEntries:
            if os.path.isdir(userDir) and 'HIP' in userDir:
                cleanUserDir(userDir)
    else:
        raise InstallerPlatformError()


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


def initVersionEnvInfo():
    global g_version
    g_version['Version'] = '{}.{}.{}'.format(g_version['major'], g_version['minor'], g_version['patch'])
    # We have a relative or absolute path in sys.argv[0] (in either case, it may
    # still be the right directory, but we'll have to find out).
    if len(sys.argv) == 0 or sys.argv[0] == '':
        raise InstallerEmptyArgvError()
    global g_programPath
    # Resolve any symbolic link in path elements and canonicalize it
    g_programPath = os.path.realpath(sys.argv[0])
    # Make sure it's normalized and absolute with respect to platform conventions
    g_programPath = os.path.abspath(g_programPath)



def printVersionEnvInfo():
    # Print the installer's version info (installer *script*, not module package)
    print('HIP Installer:')
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
            print('{:<{width}}{}'.format(k, v, width=maxKeyWidth))
        print()
    print('HIP Installer Path: ')
    print(g_programPath)
    print()
    # Print the OS version/build info
    import platform as p
    print('Operating System / Platform:')
    print(sys.platform + ': ' + p.platform())
    print()
    # Print our runtime interpreter's version/build info
    print('Python Runtime Version:')
    print(sys.version)
    return


def loadManifestFile(path):
    g_dbg.push('loadManifestFile"{}")'.format(path))
    manifest = {}
    t = None
    if not os.path.exists(path):
        g_dbg.pop('manifestPathNotFound("{}")'.format(path))
        return (None, t)
    try:
        with open(path) as f:
            timeline = f.readline().rstrip('\r\n')
            m = re.match(r'^time: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})$', timeline)
            if m:
                t = m.group(1)
            for line in f:
                relpath, cksum = line.split(' // ')
                path = os.path.join('modules', os.path.normpath(relpath))
                manifest[path] = cksum.strip()
    except IOError as e:
        g_dbg.pop('failureLoadingManifest("{}")'.format(e))
        return (None, t)
    g_dbg.pop('manifestSize({})'.format(len(manifest)))
    return (manifest, t)


def loadManifest():
    g_dbg.push('loadManifest')
    stdManifestPath = os.path.normpath('modules/release_manifest.txt')
    emfManifestPath = os.path.normpath('modules/emf_beta_manifest.txt')
    stdManifest, stdTime = loadManifestFile(stdManifestPath)
    emfManifest, emfTime = loadManifestFile(emfManifestPath)
    if emfTime and stdTime and emfTime > stdTime:
        # For every path (key) in stdManifest which is not in emfManifest and is under one of the EMF repository module
        # folders (i.e., EMF, EMF+MiniSWMH, EMF+SWMH, and EMF+Vanilla), delete the path from stdManifest.
        toDelete = []
        for s in stdManifest:
            if s not in emfManifest and s[:s.find('/')] in ('EMF', 'EMF+MiniSWMH', 'EMF+SWMH', 'EMF+Vanilla'):
                toDelete.append(s)
        for d in toDelete:
            del stdManifest[d]
        # Now, let entries that ARE in emfManifest override/add to stdManifest:
        for e in emfManifest:
            stdManifest[e] = emfManifest[e]
    return stdManifest
    g_dbg.pop('finalManifestSize({})'.format(len(stdManifest.keys())))


def getPkgVersions(modDirs):
    global g_versions
    g_versions = {}
    g_dbg.push('getPkgVersions')
    for mod in modDirs.keys():
        f = os.path.join('modules', modDirs[mod], 'version.txt')
        if os.path.exists(f):
            g_versions[mod] = open(f).readline().strip()
        else:
            g_versions[mod] = 'no version'
        g_dbg.trace('version("{}" => "{}")'.format(mod, g_versions[mod]))
    g_dbg.pop()


g_defaultFolder = 'Historical_Immersion_Project'
g_spacedDefaultFolder = g_defaultFolder.replace('_', ' ')


def getInstallOptions(batchMode=False):
    g_dbg.push('getInstallOptions')
    g_dbg.trace('batchMode({})'.format(batchMode))
    # Determine installation target folder...
    if batchMode:
        g_dbg.pop('targetFolderSelection("{}")'.format(g_defaultFolder))
        return g_defaultFolder
    # Show HIP installer version & explain interactive prompting
    print(localise('INTRO').format('HIP Release: {}'.format(g_versions['pkg']).center(80-2)))
    # Give the option to install to a custom folder & .mod file
    targetFolder = ''
    useCustomFolder = isYesDefaultNo(promptUser('Do you want to install to a custom folder / mod name? [{}]'.format(NO)))
    if useCustomFolder:
        # Note that we use the case-preserving form of promptUser (also determines name in launcher)
        targetFolder = promptUser(localise('TARGET_FOLDER').format(g_spacedDefaultFolder), lc=False)
    if targetFolder == '':
        targetFolder = g_defaultFolder
    g_dbg.pop('targetFolderSelection("{}")'.format(targetFolder))
    return targetFolder


# Find Steam master folder by checking the Windows Registry (32-bit mode and
# 64-bit mode are separate invocations)
def getSteamMasterFolderFromRegistry(x64Mode=True):
    g_dbg.push('getSteamMasterFolderFromRegistry(x64Mode={})'.format(x64Mode))
    pathVariant = '\\Wow6432Node' if x64Mode else ''
    keyPath = 'SOFTWARE{}\\Valve\\Steam'.format(pathVariant)
    # _winreg import will fail on Python 3 for Windows, because it's been
    # _standardized to winreg. For Python 2.7, we import _winreg instead.
    #
    # NOTE: cygwin Python lacks _winreg (as it should)
    if sys.version_info.major == 3:  # Using Python 3
        import winreg as wreg
    else:  # Presumably Py2.7, or else this script is now ancient and should be buried
        import _winreg as wreg
    try:
        hReg   = wreg.ConnectRegistry(None, wreg.HKEY_LOCAL_MACHINE)
        hKey   = wreg.OpenKey(hReg, keyPath)
        g_dbg.trace('queryRegistryKey("HKEY_LOCAL_MACHINE\\{}")'.format(keyPath))
        folder = wreg.QueryValueEx(hKey, 'InstallPath')
        if not folder:
            raise EnvironmentError()
        g_dbg.trace('registryInstallPathFound(InstallPath => "{}")'.format(folder[0]))
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
                  'Program Files/Steam',
                  'SteamLibrary',
                  'Steam',
                  'Games/Steam']
    g_dbg.push('getSteamMasterFolderFallbackCygwin')
    g_dbg.trace('assumingCygwinDriveRoot("{}")'.format(cygdrive))
    for d in os.listdir(cygdrive):
        g_dbg.trace('scanDrive("{}")'.format(d))
        for maybePath in maybePaths:
            masterFolder = os.path.join(cygdrive, d, maybePath, 'steamapps')
            g_dbg.trace('scan("{}")'.format(masterFolder))
            vdfPath = os.path.join(masterFolder, 'libraryfolders.vdf')
            if os.path.exists(vdfPath):
                g_dbg.pop('scanSuccess("{}")'.format(vdfPath))
                return masterFolder
    g_dbg.pop('scanFailed()')
    return None


def getSteamMasterFolder():
    g_dbg.push('getSteamMasterFolder')
    if g_platform == 'win':
        folder = getSteamMasterFolderFromRegistry()
        if folder is None:
            folder = getSteamMasterFolderFromRegistry(x64Mode=False)  # Try the 32-bit registry key
    elif g_platform == 'mac':
        folder = os.path.expanduser('~/Library/Application Support/Steam/SteamApps')
        if not os.path.exists(folder):
            folder = os.path.expanduser('~/Library/Application Support/Steam/steamapps')
    elif g_platform == 'lin':
        folder = os.path.expanduser('~/.steam/steam/steamapps')
        if not os.path.exists(folder):
            folder = os.path.expanduser('~/.steam/steam/SteamApps')
    elif g_platform == 'cyg':
        folder = getSteamMasterFolderFallbackCygwin()
    else:
        raise InstallerPlatformError()
    if folder and os.path.exists(folder):
        g_dbg.pop('steamMasterFolder("{}")'.format(folder))
        return folder
    else:
        g_dbg.pop('steamMasterFolder(NOT_FOUND)')
        return None


def readSteamLibraryFolders(dbPath):
    g_dbg.push('readSteamLibraryFolders("{}")'.format(dbPath))
    folders = []
    with open(dbPath, 'r') as f:
        while True:
            line = f.readline()
            if len(line) == 0:
                g_dbg.pop("numExternalLibrariesFound({})".format(len(folders)))
                return folders
            line = line.rstrip('\n')
            m = re.match(r'^\s*"\d+"\s+"([^"]+)"\s*$', line)
            if m:
                p = m.group(1).replace(r'\\', '/')
                if g_platform == 'cyg':
                    i = p.find(':/')
                    if i == 1:
                        drive = p[:1]
                        p = p.replace(p[:2], '/cygdrive/' + drive.lower(), 1)
                path = os.path.join(os.path.normpath(p), 'steamapps')
                g_dbg.trace('maybeExternalLibrary("{}")'.format(path))
                if os.path.exists(path):
                    g_dbg.trace('externalLibraryExists("{}")'.format(path))
                    folders.append(path)


def getSteamGameFolder(masterFolder, gameName, magicFile):
    g_dbg.push('getSteamGameFolder("{}", "{}", "{}")'.format(masterFolder, gameName, magicFile))
    libraryDBPath = os.path.join(masterFolder, 'libraryfolders.vdf')
    if not os.path.exists(libraryDBPath):
        g_dbg.trace('steamLibraryDBPath(NOT_FOUND, "{}")'.format(libraryDBPath))
    else:
        g_dbg.trace('steamLibraryDBPath(FOUND, "{}")'.format(libraryDBPath))
        for f in readSteamLibraryFolders(libraryDBPath):
            path = os.path.join(f, 'common', gameName)
            if os.path.exists(os.path.join(path, magicFile)):
                g_dbg.pop('steamLibraryFolder(GAME_FOUND, "{}")'.format(path))
                return path
            else:
                g_dbg.trace('steamLibraryFolder(GAME_NOT_FOUND, "{}")'.format(path))
        g_dbg.pop()
    g_dbg.push('searchForFallbackGameFolder')
    # Try an obvious path for a fallback game folder:
    fallbackPath = os.path.join(masterFolder, 'common', gameName)
    g_dbg.trace('potentialFallbackGameFolder("{}")'.format(fallbackPath))
    fallbackMagicPath = os.path.join(fallbackPath, magicFile)
    if os.path.exists(fallbackMagicPath):
        g_dbg.pop('fallbackGameFolderMagic(VALID)')
        return fallbackPath
    else:
        g_dbg.pop('fallbackGameFolderMagic(INVALID)')
    return None


cprReqDLCNames = {'dlc002.dlc': 'Mongol Face Pack',
                  'dlc013.dlc': 'African Portraits',
                  'dlc014.dlc': 'Mediterranean Portraits',
                  'dlc016.dlc': 'Russian Portraits',
                  'dlc020.dlc': 'Norse Portraits',
                  'dlc028.dlc': 'Celtic Portraits',
                  'dlc039.dlc': 'Rajas of India',
                  'dlc041.dlc': 'Turkish Portraits',
                  'dlc044.dlc': 'Persian Portraits',
                  'dlc046.dlc': 'Early Western Clothing Pack',
                  'dlc047.dlc': 'Early Eastern Clothing Pack',
                  'dlc052.dlc': 'Iberian Portraits',
                  'dlc057.dlc': 'Cuman Portraits',
                  'dlc063.dlc': 'Conclave Content Pack',
                  'dlc065.dlc': 'South Indian Portraits',
                  'dlc067.dlc': 'Reaper\'s Due Content Pack',
                  'dlc070.dlc': 'Monks and Mystics Content Pack',
                  'dlc072.dlc': 'South Indian Portraits',
                  'dlc073.dlc': 'Jade Dragon',
                  'dlc074.dlc': 'Holy Fury',
                  }


# Determine the DLCs installed in the active game folder. Returns None if DLC
# detection (game folder detection) fails, and otherwise the exact list of the
# DLCs' IDs (e.g. "dlc010.dlc").
def detectDLCs():
    g_dbg.push('detectDLCs')
    masterFolder = getSteamMasterFolder()
    if not masterFolder:
        g_dbg.pop('FAIL => steamMasterFolderNotFound')
        return None
    gameFolder = getSteamGameFolder(masterFolder, 'Crusader Kings II', 'dlc')
    if not gameFolder:
        g_dbg.pop('FAIL => steamGameFolderNotFound')
        return None
    g_dbg.trace('usingGameFolder("{}")'.format(gameFolder))
    dlcFolder = os.path.join(gameFolder, 'dlc')
    if not os.path.isdir(dlcFolder):
        g_dbg.pop('expectedDLCFolderIsNotADirectory("{}")'.format(dlcFolder))
        return None
    g_dbg.push('installedDLCs')
    dlcIDs = [f for f in os.listdir(dlcFolder) if f.endswith('.dlc')]
    for d in dlcIDs:
        g_dbg.trace(d)
    g_dbg.pop()
    return dlcIDs


# Determine whether the DLCs required for CPR are installed. Returns the exact
# list of the missing DLCs' names, or an empty list if there are none.
def detectCPRMissingDLCs(dlcIDs):
    reqDLCNames = cprReqDLCNames
    for f in dlcIDs:
        if f in reqDLCNames:
            del reqDLCNames[f]
    # hack alert for a hacky free dlc (south indian portraits has two versions, technically)
    ether = ['dlc065.dlc', 'dlc072.dlc']  # yep, ether
    if ether[0] in reqDLCNames and ether[1] in reqDLCNames:
        del reqDLCNames[ether[0]] # will fail still, but don't display duplicates
    elif ether[0] in reqDLCNames or ether[1] in reqDLCNames:
        for i in ether: # mm...
            reqDLCNames.pop(i, None) # will not fail, because at least one but not both could not be found
    return reqDLCNames.values()


def printCPRReqDLCNames():
    # Display names of required DLCs, sorted by latest release date
    for name in [cprReqDLCNames[f] for f in sorted(cprReqDLCNames.keys(), reverse=True)]:
        print('+ {}'.format(name))
    print()


def buildModFilename(baseFolder, modBasename):
    modFilename = modBasename + '.mod'
    # CKII command line argument parser can't handle dashes in .mod file names
    # (which are passed as arguments to CKII.exe by the launcher)
    modFilename = modFilename.replace('-', '__')
    modFilename = modFilename.replace(' ', '+')
    modFilename = os.path.join(baseFolder, modFilename)
    return modFilename


def removePreexistingMod(targetFolder, modFilename):
    # Remove preexisting target folder...
    if os.path.exists(targetFolder):
        if not g_steamMode:
            print()
        print("> Removing preexisting '%s' ..." % targetFolder)
        sys.stdout.flush()
        startTime = time.time()
        rmTree(targetFolder, 'rm_preexisting_mod("{}")'.format(targetFolder))
        endTime = time.time()
        print('> Removed (%0.1f sec).\n' % (endTime - startTime))
        sys.stdout.flush()
    # Remove preexisting .mod file...
    if os.path.exists(modFilename):
        rmFile(modFilename)


def scaffoldMod(modFilename, targetFolder, modBasename, modName, modPath, modUserDir=None, eu4Version=None, deps=None):
    mkTree(targetFolder)
    # Generate a new .mod file...
    g_dbg.trace('write_dot_mod("{}")'.format(modFilename))
    with open(modFilename, 'w') as modFile:
        modFile.write('# Name to use as a dependency if making a submod/compatch (see note at bottom about Steam Workshop):\nname = "{}"\n'.format(modName))
        modFile.write('path = "mod/{}"\n'.format(modPath))
        if deps is not None:
            modFile.write('dependencies = {\n')
            for dependencyName in deps:
                if ' ' in dependencyName:
                    dependencyName = r'\"{}\"'.format(dependencyName)
                modFile.write('"{}"\n'.format(dependencyName))
            modFile.write('}\n')
        if modUserDir is not None:
            modFile.write('user_dir = "%s"  '
                          '# Ensure we get our own versions of the gfx/map caches and savegames\n' %
                          modBasename)
        if eu4Version is not None:
            modFile.write('supported_version = {}\n'.format(eu4Version))
        modFile.write('''

# NOTE: If you are making a submod/compatch for HIP (or any mod with a name that has spaces in it) and you want to upload
# it to Steam Workshop, then not only must you use the 'dependencies' feature to specify that the submod/compatch needs to
# override HIP's files but also you must use Extra Special Redundant Double-Quoting so that Steam doesn't mangle things
# when users download your mod. In short, do this:
#
# dependencies = { "\\"HIP - Historical Immersion Project\\"" "\\"HIP (Steam Edition)\\"" }''')


def main():
    try:
        initVersionEnvInfo()
        global g_steamMode
        g_steamMode = '--steam' in sys.argv[1:]
        dbgMode = '-D' in sys.argv[1:] or '--debug' in sys.argv[1:]
        versionMode = '-V' in sys.argv[1:] or '--version' in sys.argv[1:]
        inplaceMode = '--in-place' in sys.argv[1:]
        swmhSelect = '--swmh' in sys.argv[1:]
        sedSelect = '--sed' in sys.argv[1:]
        emfSelect = '--emf' in sys.argv[1:]
        ltmSelect = '--ltm' in sys.argv[1:]
        arkocSelect = '--coa' in sys.argv[1:]
        arkoiSelect = '--interface' in sys.argv[1:]
        if '--arko' in sys.argv[1:]:
            arkocSelect = True
            arkoiSelect = True
        cprSelect = '--cpr' in sys.argv[1:]
        aksSelect = '--aks' in sys.argv[1:]
        uswmhSelect = '--mini' in sys.argv[1:]
        # Are we in a batch mode?
        batchMode = sedSelect or swmhSelect or emfSelect or ltmSelect or arkocSelect or \
                    arkoiSelect or cprSelect or aksSelect or uswmhSelect or g_steamMode
        global g_dbg
        g_dbg = DebugTrace(open('HIP_debug.log', 'w'), prefix='') if dbgMode else NullDebugTrace()
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
        if not inplaceMode:
            normalizeCwd()
        if not os.path.isdir('modules'):
            raise InstallerPackageNotFoundError()
        # Load release manifest:
        global g_modified
        g_modified = False
        manifest = loadManifest()
        # These are the modules/ directories from which to grab each mod's version.txt:
        modDirs = {'pkg': '',   # Installer package version
                   'SWMH':      'SWMH',
                   'CPR':       'CPRplus',
                   'EMF':       'EMF',
                   'SED':       'SED2',
                   'ARKOC':     'ARKOpack_Armoiries',
                   'ARKOI':     'ARKOpack_Interface',
                   'ArumbaKS':  'ArumbaKS',
                   'uSWMH':     'MiniSWMH',
                   'LTM':       'LTM+SWMH',
                   'Converter': 'Converter'
        }
        getPkgVersions(modDirs)
        # Prompt user for options related to this install (not re: module selections):
        targetFolder = getInstallOptions(batchMode)
        if not g_steamMode:
            print()
        # Determine module combination...
        EMF = False
        ARKOCoA = False
        ARKOInt = False
        ArumbaKS = False
        CPR = False
        SWMH = False
        uSWMH = False
        SED = False
        LTM = False
        Converter = False
        # What each selection implies:
        if sedSelect:
            SED = True
            SWMH = True
        if swmhSelect:
            SWMH = True
        if emfSelect:
            EMF = True
        if ltmSelect:
            LTM = True
        if arkocSelect:
            ARKOCoA = True
        if arkoiSelect:
            ARKOInt = True
        if cprSelect:
            CPR = True
        if aksSelect:
            ArumbaKS = True
        if uswmhSelect:
            uSWMH = True
            SWMH = True
        if g_steamMode:
            EMF = True
            ARKOCoA = True
            ArumbaKS = True
            SWMH = True
            LTM = True
        # K, let's get to prompting:
        cprMissingDLCNames = None
        dlcIDs = detectDLCs()
        if dlcIDs is not None:
            cprMissingDLCNames = detectCPRMissingDLCs(dlcIDs)
        if batchMode:
            CPR &= cprMissingDLCNames is not None and len(cprMissingDLCNames) == 0
        else:
            # EMF...
            EMF = enableMod('EMF ({})'.format(g_versions['EMF']))
            # ARKOpack...
            ARKOCoA = enableMod('ARKOpack Armoiries [CoA] ({})'.format(g_versions['ARKOC']))
            ARKOInt = enableMod('ARKOpack Interface ({})'.format(g_versions['ARKOI']))
            # Arumba's Keyboard Shortcuts...
            ArumbaKS = enableMod('Arumba and Internal Tab Shortcuts ({})'.format(g_versions['ArumbaKS']))
            # CPRplus...
            if cprMissingDLCNames is None:  # Failed to auto-detect game folder
                print('\nOOPS: The HIP installer could NOT successfully determine your active CKII\n'
                      'game folder! Thus, it cannot auto-detect whether you meet all the portrait DLC\n'
                      'prerequisites for CPRplus. But all other HIP modules CAN still be installed!\n')
                print()
            elif len(cprMissingDLCNames) > 0:  # DLC auto-detection succeeded, but there were missing DLCs.
                print('\n\nCPRplus (portrait upgrade module) requires portrait pack DLCs which you,\n'
                      'unfortunately, are lacking. If you want to use CPRplus, you\'ll need to install\n'
                      'the following DLCs first:\n')
                for name in sorted(cprMissingDLCNames):
                    print('+ {}'.format(name))
                print()
            else:  # DLC verification succeeded, and CPR is clear for take-off.
                CPR = enableMod('CPRplus ({})'.format(g_versions['CPR']))
            # SWMH...
            print('''
OPTION: MiniSWMH is an SWMH submod which significantly improves performance by
deactivating India and some parts of Africa on the map. If you'd like to try
MiniSWMH, you must select SWMH below in order to be prompted about it afterward.

If you want the vanilla map instead, simply type 'n' or 'no' for SWMH below:''')
            SWMH = enableMod('SWMH ({})'.format(g_versions['SWMH']))
            if SWMH:
                # MiniSWMH...
                uSWMH = enableModDefaultNo('MiniSWMH: Performance-Friendly SWMH ({})'.format(g_versions['uSWMH']), compat=True)
                # SED...
                SED = enableModDefaultNo('SED: English Localisation for SWMH ({})'.format(g_versions['SED']), compat=True)
                # Converter...
                if g_versions['Converter'] != 'no version':
                    # Don't prompt if Converter isn't present in this release package.
                    # Don't prompt if EU4 converter DLC is positively detected as missing.
                    if dlcIDs is None or 'dlc030.dlc' in dlcIDs:
                        print('\nNEW: HIP now supports the EU4 Converter even with SWMH enabled. This will\n'
                              'install a separate mod, which should be left disabled until you are ready to\n'
                              'convert a save.\n')
                        Converter = enableModDefaultNo('Converter: EU4 conversion support for SWMH ({})'.format(g_versions['Converter']), compat=True)
            # LTM...
            LTM = enableMod('Lindbrook\'s Texture Map ({})'.format(g_versions['LTM']))
        # Prepare for installation...
        if targetFolder != g_defaultFolder:
            modBasename = 'HIP_' + targetFolder
            converterName = 'HIP - ' + targetFolder + ' - Converter'
            modName = 'HIP - ' + targetFolder
        else:
            modBasename = 'HIP'
            converterName = 'HIP - Converter'
            modName = 'HIP - ' + targetFolder.replace('_', ' ')
        converterTargetFolder = modBasename + '_Converter'
        if EMF or ARKOCoA or ARKOInt or CPR or SWMH:
            modUserDir = modBasename
        else:
            modUserDir = None
        modFilename = buildModFilename('.', modBasename)
        euModFilename = buildModFilename('.', converterTargetFolder)
        removePreexistingMod(targetFolder, modFilename)
        # Also remove old space-separated default folder for giggles and to
        # avoid ambiguity, if it's there
        removePreexistingMod(g_spacedDefaultFolder, modFilename)
        removePreexistingMod(converterTargetFolder, euModFilename)
        scaffoldMod(modFilename,
                    targetFolder,
                    modBasename,
                    modName,
                    targetFolder,
                    modUserDir)
        if Converter:
            scaffoldMod(euModFilename,
                        converterTargetFolder,
                        converterTargetFolder,
                        converterName,
                        converterTargetFolder,
                        deps=[modName])
        # Prepare file mappings...
        global g_targetSrc
        g_targetSrc = {}
        moduleOutput = ['[ HIP Release: {} ]\n'.format(g_versions['pkg'])]
        globalFlags = []
        g_dbg.push('merge_all')
        if EMF:
            globalFlags.append('EMF_prestartup')
            moduleOutput.append('EMF: Extended Mechanics & Flavor (%s)\n' % g_versions['EMF'])
        if ArumbaKS:
            g_dbg.push('merge(ArumbaKS)')
            globalFlags.append('AKS')
            moduleOutput.append('Arumba and Internal Tab Shortcuts (%s)\n' % g_versions['ArumbaKS'])
            pushFolder('ArumbaKS', targetFolder)
            g_dbg.pop()
        if ARKOInt:
            g_dbg.push("merge('ARKO Interface')")
            globalFlags.append('ArkoUI')
            moduleOutput.append("ARKO Interface (%s)\n" % g_versions['ARKOI'])
            pushFolder('ARKOpack_Interface', targetFolder)
            if ArumbaKS:
                pushFolder('ArkoInterface+AKS', targetFolder)
            g_dbg.pop()
        if SWMH:
            g_dbg.push('merge(SWMH)')
            globalFlags.append('SWMH')
            moduleOutput.append('SWMH (%s)\n' % g_versions['SWMH'])
            pushFolder('SWMH', targetFolder)
            g_dbg.pop()
        if uSWMH:
            g_dbg.push('merge(uSWMH)')
            globalFlags.append('MiniSWMH')
            moduleOutput.append('MiniSWMH: Performance-Friendly SWMH (%s)\n' % g_versions['uSWMH'])
            pushFolder('MiniSWMH', targetFolder)
            g_dbg.pop()
        if SED:
            g_dbg.push('merge(SED)')
            globalFlags.append('SED')
            moduleOutput.append('SED: English Localisation for SWMH (%s)\n' % g_versions['SED'])
            pushFolder('SED2', targetFolder)
            if EMF:
                pushFolder('SED2+EMF', targetFolder)
            if uSWMH:
                pushFolder('SED2+MiniSWMH', targetFolder)
            g_dbg.pop()
        if ARKOCoA:
            g_dbg.push("merge('ARKO CoA')")
            globalFlags.append('ArkoCoA')
            moduleOutput.append('ARKO Armoiries (%s)\n' % g_versions['ARKOC'])
            pushFolder('ARKOpack_Armoiries', targetFolder)
            if SWMH:
            	pushFolder('SWMH/gfx/flags', os.path.join(targetFolder, 'gfx', 'flags'))
            g_dbg.pop()
        if LTM:
            g_dbg.push('merge(LTM)')
            globalFlags.append('LTM')
            moduleOutput.append('LTM (%s)\n' % g_versions['LTM'])
            if SWMH:
                pushFolder('LTM+SWMH', targetFolder)
            else:
                pushFolder('LTM+Vanilla', targetFolder)
            if ARKOCoA:
                pushFolder('ArkoCoA+LTM', targetFolder)
            g_dbg.pop()
        if EMF:
            g_dbg.push('merge(EMF)')
            pushFolder('EMF', targetFolder)
            if SWMH:
                pushFolder('EMF+SWMH', targetFolder)
                if uSWMH:
                    pushFolder('EMF+MiniSWMH', targetFolder)
            else:
                pushFolder('EMF+Vanilla', targetFolder)
            if ArumbaKS:
                pushFolder('EMF+AKS', targetFolder)
            if ARKOInt:
                pushFolder('EMF+ArkoInterface', targetFolder)
                if ArumbaKS:
                    pushFolder('EMF+ArkoInterface+AKS', targetFolder)
            g_dbg.pop()
        if CPR:
            g_dbg.push('merge(CPR)')
            globalFlags.append('CPR')
            moduleOutput.append('CPRplus (%s)\n' % g_versions['CPR'])
            wrappedPaths = set(['gfx'])
            pushFolder('CPRplus', targetFolder, wrapPaths=wrappedPaths)
            if SWMH:
                pushFolder('CPRplus-compatch/SWMH', targetFolder)
            elif EMF:
                pushFolder('CPRplus-compatch/EMF', targetFolder)
            g_dbg.pop()
        if Converter:
            g_dbg.push('merge(Converter)')
            moduleOutput.append('Converter (%s)\n' % g_versions['Converter'])
            pushFolder('Converter', converterTargetFolder)
            if uSWMH:
                pushFolder('Converter+Mini', converterTargetFolder)
            g_dbg.pop()
        g_dbg.pop('merge_done')
        # Where to dump a mapping of all the compiled files to their source modules (will include stuff from outside
        # targetFolder for now too if such stuff is pushed on to the virtual filesystem)
        mapFilename = os.path.join(targetFolder, "file2mod_map.txt")
        startTime = time.time()
        # Do all the actual compilation (file I/O)
        compileTarget(mapFilename, targetFolder, manifest)
        endTime = time.time()
        print('> Compiled (%0.1f sec).\n' % (endTime - startTime))
        # Report if the installed files didn't match release manifest checksum:
        if g_modified:
            msg = '''
ERROR: Some installed files do not match their released version. This means that
       your HIP installation will not be working as designed and is indeed
       corrupted. This issue is caused by either of the following:

A) Not deleting the previous HIP installation's "modules/" folder before
   extracting the new HIP release archive.
B) Modifying or adding new files inside the "modules/" folder directly when you
   should be using a personal submod to override/change HIP files. Note that
   installing an EMF Beta from the proper source cannot cause this issue.
'''
            moduleOutput.append(msg)
            print(msg)
            print()
        if not g_steamMode:
            print('Mapping of all compiled mod files to their HIP source modules:')
            print(mapFilename)
            print()
        # Dump modules selected and their respective g_versions to <mod>/version.txt
        versionFilename = os.path.join(targetFolder, 'version.txt')
        with open(versionFilename, 'w') as output:
            output.write(''.join(moduleOutput))
        print('Summary of mod combination & versions (INCLUDE THIS FILE IN BUG REPORTS):')
        print(versionFilename)
        print()
        # Add global flags for runtime module identification:
        flagDir = os.path.join(targetFolder, os.path.normpath('history/titles'))
        flagPath = os.path.join(flagDir, 'e_null.txt')
        if os.path.exists(flagDir):
            with open(flagPath, 'w') as of:
                of.write('# -*- ck2.history.titles -*-\n')
                of.write('476.1.1 = {\n')
                for flag in globalFlags:
                    of.write('\tset_global_flag = {}\n'.format(flag))
                of.write('}\n')
        # Reset all gfx/map/interface/logs cache for every instance of a preexisting
        # user_dir that includes HIP, platform-agnostic.
        resetCaches()
        g_dbg.trace('install_done')
        if batchMode:
            print('DONE!')
        else:
            promptUser(localise('INSTALL_DONE'))
        return 0  # Return success code to OS

    except KeyboardInterrupt:
        # Ctrl-C just aborts (with a dedicated error code) rather than cause a
        # traceback. May want to catch it during filesystem modification stage
        sys.stderr.write('\nUser interrupt: Aborting installer early...\n')
        sys.exit(2)
    except InstallerTraceNestingError as e:
        sys.stderr.write('\nFatal error: ' + str(e))
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write('Screenshot/copy this error and send it to the HIP team. Press ENTER to exit.')
        sys.stdin.readline()
        sys.exit(255)
    # Special handling for specific installer-understood error types (all derive from InstallerException)
    except InstallerException as e:
        sys.stderr.write('\nFatal error: ' + str(e))
        sys.stderr.write('\nFor help, provide this error to the HIP team. Press ENTER to exit.')
        sys.stdin.readline()
        sys.exit(1)
    # And the unknowns...
    except:
        sys.stderr.write('\nUnexpected fatal error occurred:\n')
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write('Screenshot/copy this error and send it to the HIP team. Press ENTER to exit.')
        sys.stdin.readline()
        sys.exit(255)


if __name__ == "__main__":
    sys.exit(main())
