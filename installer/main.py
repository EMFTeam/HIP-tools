#!/usr/bin/python
# -*- coding: cp1252 -*-
# -*- python-indent-offset: 2 -*-


import os, shutil
import sys, traceback


def initLocalisation():
    global i18nDB
    i18nDB = {'INTRO':
                  {
                      'fr': "Cette version de Historical Immersion Project date du %s.\n"
                            "Taper 'o' ou 'oui' pour valider, ou laisser le champ vierge. Toute autre\n"
                            "reponse sera interpretee comme un non.\n",
                      'es': "Esta vercion de Historical Immersion Project fecha del %s.\n"
                            "Escribe 's' o 'si' para aceptar, o deja el campo en blanco. Cualquier otro\n"
                            "caso sera considerado un 'no'.\n",
                      'en': "This version of the Historical Immersion Project was released %s.\n"
                            "To confirm a prompt, respond with 'y' or 'yes' (sans quotes) or simply hit\n"
                            "ENTER. Besides a blank line, anything else will be interpreted as 'no.'\n",
                  },
              'ENABLE_MOD':
                  {
                      'fr': "Voulez-vous installer %s ? [oui]",
                      'es': "Deseas instalar %s? [si]",
                      'en': "Do you want to install %s? [yes]",
                  }
    }


def localise(key):
    return i18nDB[key][language]


class InstallerException(Exception): pass


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


class DebugTrace:
    def __init__(self, file, prefix='DBG: '):
        self.file = file
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
        if self.i <= 0: raise InstallerTraceNestingError()
        self.i -= 1
        if s: self.trace(s)


class VoidDebugTrace(DebugTrace):
    def __init__(self): pass

    def trace(self, s): pass

    def push(self, s): pass

    def pop(self, s=None): pass


def promptUser(prompt, lc=True):
    sys.stdout.write(prompt + ' ')
    sys.stdout.flush()
    response = sys.stdin.readline().strip()
    if lc:
        return response.lower()
    else:
        return response


def isYes(answer):
    if language == 'fr':
        return answer in ('', 'o', 'oui')
    elif language == 'es':
        return answer in ('', 's', 'si')
    else:
        return answer in ('', 'y', 'yes')


def enableMod(name):
    return isYes(promptUser(localise('ENABLE_MOD') % name))


def quoteIfWS(s):
    if ' ' in s: return "'{}'".format(s)
    return s


def src2Dst(src, dst):
    return '{} => {}'.format(quoteIfWS(src), quoteIfWS(dst))


def rmTree(directory, traceMsg=None):
    if traceMsg: dbg.trace(traceMsg)
    dbg.trace("RD: " + quoteIfWS(directory))
    if os.path.exists(directory):
        shutil.rmtree(directory)


def rmFile(f, traceMsg=None):
    if traceMsg: dbg.trace(traceMsg)
    dbg.trace("D: " + quoteIfWS(f))
    os.remove(f)


def mkTree(dir, traceMsg=None):
    if traceMsg: dbg.trace(traceMsg)
    dbg.trace("MD: " + quoteIfWS(dir))
    os.makedirs(dir)


def moveFolder(folder, prunePaths={}, ignoreFiles={}):
    if language == 'fr':
        print("Fusion repertoire " + quoteIfWS(folder))
    elif language == 'es':
        print("Carpeta de combinacion " + quoteIfWS(folder))
    else:
        print("Merging folder " + quoteIfWS(folder))

    srcFolder = os.path.join('modules', folder)
    dbg.push("merging folder " + src2Dst(srcFolder, targetFolder))

    for root, dirs, files in os.walk(srcFolder):
        newRoot = root.replace(srcFolder, targetFolder)
        dbg.push('merging dirpath ' + src2Dst(root, newRoot))

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
                if not os.path.exists(newDir):
                    mkTree(newDir)

        dirs[:] = prunedDirs  # Filter subdirectories into which we should recurse on next os.walk()

        for file in files:
            src = os.path.join(root, file)
            dst = os.path.join(newRoot, file)

            if os.path.exists(dst):
                clobberStr = '[!]'
            else:
                clobberStr = ''

            xferStr = "{}: {}: {}".format(clobberStr, quoteIfWS(file), src2Dst(src, dst))

            if src in ignoreFiles:  # Selective ignore filter for individual files
                dbg.trace('IGNORE' + xferStr)
                continue

            if move:
                dbg.trace('MV' + xferStr)
                shutil.move(src, dst)
            else:
                dbg.trace('CP' + xferStr)
                shutil.copy(src, dst)

        dbg.pop()
    dbg.pop()


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
        print('Clearing preexisting HIP gfx/map caches...')

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


def initVersionEnvInfo():
    global version
    version = {'major': 1, 'minor': 2, 'micro': 3, 'Release-Date': '2014-02-21 04:45:35 UTC',
               'Released-By': 'zijistark <zijistark@gmail.com>'}

    # Once I achieved successful, tested Mac support (and boy did it take a long
    # time to sort-out) post-overhaul, the version number was arbitrarily assigned
    # to 1.2.0. The micro version will increment with each public release in which
    # the installer's functionality is nontrivially patched. It should not be
    # incremented simply due to a HIP release; changes to the module package data
    # are independent of the installer's version. However, altered data
    # compilation logic (i.e., different compatch results) is relevant to the
    # installer version.

    # Extended elements

    # May or may not be present. Don't mess with the text replacement anchors
    # within the weird comment syntax, as the contents will be replaced by the
    # build script. Everything between the first comment line beginning with
    # "<*!EXTENDED_VERSION_INFO" and the closing comment line composed only of
    # "!*>" will be replaced or emptied at build time. Ergo, anything there
    # that's checked-into the repository is purely an example.

    # Anything could be inserted here by the build script or nothing at all
    # (special tags, commit author, git branch, checksum, information about the
    # building machine/toolkit, etc.). This is WIP.

    # <*!EXTENDED_VERSION_INFO
    ##    version['Commit-ID']        = '361fe74959ee65a5b6e7f9144097e1eb66fa33cd' # parent
    ##    version['Commit-Date']    = 'Tue Feb 18 16:56:33 2014 -0800'
    # !*>

    global versionStr
    versionStr = '{}.{}.{}'.format(version['major'], version['minor'], version['micro'])

    ##    if 'Commit-ID' in version:
    ##        versionStr += '.git~' + version['Commit-ID'][0:7]

    # Note that the above generates a version string that is lexicographically
    # ordered from semantic 'earlier' to 'later' in all cases, including variable
    # numbers of digits in any of the components.

    # Resolve the installer's own absolute path. Needs to be tested with a py2exe
    # rebuild, hence the exception-raising case below.

    # We have have a relative or absolute path in sys.argv[0] (in either case,
    # it may still be the right directory, but we'll have to find out)

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

    # Ideally, we will add another component to the HIP installer's build
    # automation that does a quick-n-easy parse of the output of `git rev-parse`
    # and then embeds the actual repository commit SHA (first 7 digits) and commit
    # time as well as the exact build time directly in this script. Thus, no
    # external dependencies will be needed to exactly identify the source revision
    # in question when a bug is reported. In the meantime, we do the uber-simple
    # thing instead.

    print('HIP Installer:')
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

    print('Installer Path: ')
    print(programPath + '\n')

    # Print the OS version/build info
    import platform as p

    print('OS / Platform:')
    print(sys.platform + ': ' + p.platform() + '\n')

    # Print our runtime interpreter's version/build info

    print("Python Runtime:")
    print(sys.version)
    return


def getPkgVersions(modDirs):
    global versions
    versions = {}
    dbg.push("reading package/module versions")
    for mod in modDirs.keys():
        f = os.path.join("modules/", modDirs[mod], "version.txt")
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
                          "Voulez-vous que les fichiers soient deplaces plutot que copies ? [oui]")
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
        if language == 'f':
            move = promptUser("Etes-vous s�r?\n"
                              "Voulez-vous supprimer le paquet apr�s l'installation? [oui]")
        elif language == 'e':
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

        global dbg
        if dbgMode:
            # the debug tracer's file object is unbuffered (always flushes all writes
            # to disk/pipe immediately), and it lives until the end of the program, so
            # we don't need to worry about closing it properly (e.g., upon an
            # exception), because it will be closed by the OS on program exit.
            dbg = DebugTrace(open('HIP_debug.log', 'w', 0))
        else:
            dbg = VoidDebugTrace()

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

        SWMH = enableMod("SWMH (%s)" % versions['SWMH'])
        if SWMH:
            if language == 'fr':
                SWMHnative = enableMod("SWMH avec les noms culturels locaux, plutot qu'en anglais ou francises")
            elif language == 'es':
                SWMHnative = enableMod("SWMH con localizacion nativa para culturas y titulos, en lugar de ingles")
            else:
                SWMHnative = enableMod("SWMH with native localisation for cultures and titles, rather than English")
        else:
            SWMHnative = True

        ARKOarmoiries = enableMod("ARKOpack Armoiries (coats of arms) (%s)" % versions['ARKO'])
        ARKOinterface = enableMod("ARKOpack Interface (%s)" % versions['ARKO'])
        NBRT = enableMod("NBRT+ (%s)" % versions['NBRT'])

        if PB:
            VIETtraits = False
        else:
            VIETtraits = enableMod("VIET traits (%s)" % versions['VIET'])

        VIETevents = enableMod("VIET events (%s)" % versions['VIET'])

        if SWMH:
            VIETimmersion = False
            if language == 'fr':
                print( "VIET immersion n'est pas compatible avec SWMH et ne peut donc pas etre actif en meme temps qu'SWMH.")
            elif language == 'es':
                print("VIET immersion no es todavia compatible con SWMH y no puede ser activado si has activado SWMH.")
            else:
                print("VIET immersion is not yet compatible with SWMH, thus cannot be enabled as you've enabled SWMH.")
        else:
            VIETimmersion = enableMod("VIET immersion (%s)" % versions['VIET'])

        VIET = (VIETtraits or VIETevents or VIETimmersion)

        # Prepare for installation
        if os.path.exists(targetFolder):
            rmTree(targetFolder, 'target folder preexists. removing...')

        mkTree(targetFolder)

        # Install...
        moduleOutput = ["Historical Immersion Project (%s)\nEnabled modules:\n" % versions['pkg']]
        dbg.push('merging source files into target folder...')

        moveFolder("Converter/Common")

        if ARKOarmoiries:
            dbg.push("merging ARKO CoA...")
            moduleOutput.append("ARKO Armoiries (%s)\n" % versions['ARKO'])
            moveFolder("ARKOpack_Armoiries")
            dbg.pop()

        if ARKOinterface:
            dbg.push("merging ARKO Interface...")
            moduleOutput.append("ARKO Interface (%s)\n" % versions['ARKO'])
            moveFolder("ARKOpack_Interface")
            if VIET:
                rmTree("%s/gfx/event_pictures" % targetFolder, 'removing ARKO event pictures')
            dbg.pop()

        if VIET:
            moveFolder("VIET_Assets")

        if PB:
            dbg.push("merging PB...")
            moduleOutput.append("Project Balance (%s)\n" % versions['PB'])
            moveFolder("ProjectBalance")
            moveFolder("Converter/PB")
            dbg.pop()

        if SWMH:
            dbg.push("merging SWMH...")
            moveFolder("SWMH")
            if SWMHnative:
                moduleOutput.append("SWMH - Native localisation (%s)\n" % versions['SWMH'])
            else:
                moduleOutput.append("SWMH - English localisation (%s)\n" % versions['SWMH'])
                moveFolder("English SWMH")
            if PB:
                moveFolder("PB + SWMH")
            dbg.pop()

        if NBRT:
            dbg.push("merging NBRT+...")
            moduleOutput.append("NBRT+ (%s)\n" % versions['NBRT'])
            moveFolder("NBRT+")
            if SWMH:
                moveFolder("NBRT+SWMH")
            if ARKOarmoiries:
                moveFolder("NBRT+ARKO")
            dbg.pop()

        if VIETtraits:
            dbg.push("merging VIET Traits...")
            moduleOutput.append("VIET Traits (%s)\n" % versions['VIET'])
            moveFolder("VIET_Traits")
            dbg.pop()

        if VIETevents:
            dbg.push("merging VIET Events...")
            moduleOutput.append("VIET Events (%s)\n" % versions['VIET'])
            moveFolder("VIET_Events")
            if PB:
                moveFolder("PB_VIET_Events")
            dbg.pop()

        if VIETimmersion:
            dbg.push("merging VIET Immersion...")
            moduleOutput.append("VIET Immersion (%s)\n" % versions['VIET'])
            if PB:  # This should be optimized in the future
                    # (Z: this entire process should be optimized to never copy/move a target file more than once)
                moveFolder("PB_VIET_Immersion")
            else:
                moveFolder("VIET_Immersion")
                moveFolder("Converter/VIET")

            if language == 'fr':
                answer = promptUser("VIET Immersion necessite tous les DLC de portraits. Les avez-vous tous ? [oui]")
            elif language == 'es':
                answer = promptUser("VIET inmersion depende de los retratos DLC. Tiene todos los retratos DLC? [si]")
            else:
                answer = promptUser(
                    "VIET Immersion depends on the portrait DLCs. Do you have all of the portrait DLCs? [yes]")

            if not isYes(answer):
                dbg.push("user chose VIET Immersion but does not have all portrait DLCs. applying fix...")
                rmTree("%s/common/cultures" % targetFolder, "removing merged cultures")
                dbg.push("removing portrait .gfx files...")
                rmFile("%s/interface/portrait_sprites_DLC.gfx" % targetFolder)
                rmFile("%s/interface/portraits_mediterranean.gfx" % targetFolder)
                rmFile("%s/interface/portraits_norse.gfx" % targetFolder)
                rmFile("%s/interface/portraits_persian.gfx" % targetFolder)
                rmFile("%s/interface/portraits_saxon.gfx" % targetFolder)
                rmFile("%s/interface/portraits_turkish.gfx" % targetFolder)
                rmFile("%s/interface/portraits_ugric.gfx" % targetFolder)
                rmFile("%s/interface/portraits_westernslavic.gfx" % targetFolder)
                dbg.pop()
                if not PB:
                    moveFolder("VIET_portrait_fix/VIET")
                else:
                    moveFolder("VIET_portrait_fix/PB")
                dbg.pop()
            dbg.pop()

        dbg.pop("merge complete")

        if move:
            rmTree("modules")  # Cleanup

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
                modFile.write('user_dir = "{}"    #For saves, gfx cache, etc.\n'.format(modFileBase))

        # Dump modules selected and their respective versions to <mod>/version.txt
        versionFilename = "%s/version.txt" % targetFolder
        dbg.trace("dumping compiled modpack version summary to " + quoteIfWS(versionFilename))
        print("Generating mod combination/versions summary: " + quoteIfWS(versionFilename))

        with open(versionFilename, "w") as output:
            output.write("".join(moduleOutput))

        # Reset all gfx/map/interface/logs cache for every instance of a preexisting
        # user_dir that includes HIP, platform-agnostic
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
        sys.stderr.write("\nUser interrupt: Exiting installer early...\n")
        sys.exit(2)

    except InstallerTraceNestingError as e:
        sys.stderr.write("\nFatal error: " + str(e))
        traceback.print_exc(file=sys.stderr)
        sys.stderr.write("Screenshot/copy this error and send it to the HIP team. Press ENTER to exit.")
        sys.exit(255)

    # Special handling for specific installer-understood error types (all derive from InstallerException)
    except InstallerException as e:
        sys.stderr.write("\nFatal error: " + str(e))
        sys.stderr.write("\nFor help, please provide this error message to the HIP team. Press ENTER to exit.")
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
