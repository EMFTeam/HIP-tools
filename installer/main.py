#!/usr/bin/python
# -*- python-indent-offset: 2 -*-

import os, shutil
import sys, traceback

class InstallerException(Exception): pass
class InstallerPlatformError(InstallerException):
  def __str__(self):
    return "Platform '%s' is not supported for installation!" % sys.platform
class InstallerTraceNestingError(InstallerException):
  def __str__(self):
    return "Debugging trace nesting mismatch (more pops than pushes). Programmer error!"

class DebugTrace:
  def __init__(self, file, prefix='DBG: '):
    self.file = file
    self.prefix = prefix
    self.i = 0
    self.indentStr = ' ' * 2
  def trace(self, msg): #Trace msg to attached stream/file-like object with no output buffering
    self.file.write('{}{}{}\n'.format(self.indentStr * self.i, self.prefix, msg))
    self.file.flush()
  def push(self, s): #Trace, then push indent stack
    self.trace(s)
    self.i += 1
  def pop(self, s=None): #Pop indent stack
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
  if language == 'f':
    return answer in ('','o','oui')
  elif language == 'e':
    return answer in ('','s','si')
  else:
    return answer in ('','y','yes')

def enableMod(name):
  if language == "f":
    answer = promptUser("Voulez-vous installer %s ? [oui]" % name)
  elif language == "e":
    answer = promptUser("Deseas instalar %s? [si]" % name)
  else:
    answer = promptUser("Do you want to install %s? [yes]" % name)
  return isYes(answer)

def quoteIfWS(s):
  if ' ' in s: return "'{}'".format(s)
  return s

def src2Dst(src, dst):
  return '{} => {}'.format(quoteIfWS(src), quoteIfWS(dst))

def rmTree(dir, traceMsg=None):
  if traceMsg: dbg.trace(traceMsg)
  dbg.trace("RD: " + quoteIfWS(dir));
  shutil.rmtree(dir);

def rmFile(f, traceMsg=None):
  if traceMsg: dbg.trace(traceMsg)
  dbg.trace("D: " + quoteIfWS(f));
  os.remove(f);

def mkTree(dir, traceMsg=None):
  if traceMsg: dbg.trace(traceMsg)
  dbg.trace("MD: " + quoteIfWS(dir));
  os.makedirs(dir);

def moveFolder(folder, prunePaths={}, ignoreFiles={}):
  if language == "f":
    print("Fusion repertoire " + folder)
  elif language == "e":
    print("Carpeta de combinacion " + folder)
  else:
    print("Merging folder " + folder)

  srcFolder = os.path.join('modules', folder)
  dbg.push("merging root folder " + src2Dst(srcFolder, targetFolder))

  for root, dirs, files in os.walk(srcFolder):
    newRoot = root.replace(srcFolder, targetFolder)
    dbg.push('merging dirpath ' + src2Dst(root, newRoot))

    # Prune the source directory walk in-place according to prunePaths option,
    # and, of course, don't create pruned directories (none of the files in
    # them will be copied/moved)
    prunedDirs = []

    for dir in dirs:
      srcPath = os.path.join(root, dir)
      if srcPath in prunePaths:
        dbg.trace("PRUNE: " + srcPath)
      else:
        prunedDirs.append(dir)
        newDir = os.path.join(newRoot, dir)
        if not os.path.exists(newDir):
          mkTree(newDir)

    dirs[:] = prunedDirs #Filter subdirectories into which we should recurse on next os.walk()

    for file in files:
      src = os.path.join(root, file)
      dst = os.path.join(newRoot, file)

      if os.path.exists(dst):
        clobberStr = '[!]'
      else:
        clobberStr = ''

      xferStr = "{}: {}: {}".format(clobberStr, quoteIfWS(file), src2Dst(src, dst))

      if src in ignoreFiles: #Selective ignore filter for individual files
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
  elif p.startswith('win') or p.startswith('cygwin'): #Currently no need to differentiate win(32|64) and cygwin
    return 'win'
  raise InstallerPlatformError()


# If necessary, changes the current working directory to that of the resolved
# location of this script itself. This is to enable the installer to be invoked
# from any directory, so long as it's been properly extracted to the CKII mod
# folder. In general, that is useful, but it also ensures that GUI-based
# invocation of the installer will always still result in the correct working
# directory.
def normalizeCwd():  
  pass

def initVersionInfo():
  global version
  version = {}
  version['major'] = 1
  version['minor'] = 1
  version['micro'] = 0

  # extended elements
  version['SHA'] = 'cd67d5bc01edf9787f03add81573beb5d0ca4f33'
  version['commitDate'] = 'Mon Feb 17 21:17:42 2014 -0800'
  version['buildDate'] = '2014-02-18 07:17:47 +0100'

  global versionStr
  versionStr = '{}.{}.{}'.format( version['major'], version['minor'], version['micro'] )

  if 'SHA' in version:
    versionStr += '-git~' + version['SHA'][0:10]


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
  
  if 'commitDate' in version:
    print('[commit] ' + version['commitDate'])
  if 'buildDate' in version:
    print('[build]  ' + version['buildDate'])

  sys.stdout.write('\n')
  
  # Print the OS version/build info
  import platform as p

  print('OS / Platform:')
  print(sys.platform + ': ' + p.platform() + '\n')

  # Print our runtime interpreter's version/build info

  print("Python Runtime:")
  print(sys.version)

  return 0


def main():
  initVersionInfo()
  
  try:
    dbgMode = (len(sys.argv) > 1 and '-D' in sys.argv[1:])
    versionMode = (len(sys.argv) > 1 and '-V' in sys.argv[1:])
        
    global dbg
    if dbgMode:
      dbg = DebugTrace(file=sys.stderr)
    else:
      dbg = VoidDebugTrace()

    global platform
    platform = detectPlatform()
    dbg.trace('detected supported platform class: ' + platform)

    if versionMode:
      return printVersionEnvInfo()

    if (platform == 'mac'):
      print('WARNING: Mac OS X support is currently experimental!\n'
            'Please help us make it work reliably for you by detailing any problems you '
            'may encounter in a direct email to zijistark@gmail.com.\n')

    # modDirs dynamic folders and straightforward keys are obviously
    # incomplete toward their end, which is encoding almost all of the logic
    # for them in a few tables and making as much of the rest as is reasonable
    # pure code. This would lend itself well to a straight rule-based
    # compilation system.  Even currently, selected module versioning output
    # could be generated by a single zip-list comprehension if a few changes
    # were made to the mod-selection code and the code which uses those vars.

    modDirs = {'VIET':'VIET_Assets',
               'PB':'ProjectBalance',
               'SWMH':'SWMH',
               'NBRT':'NBRT+',
               'ARKO':'ARKOpack_Armoiries'}

    versions = {}

    dbg.push("reading package/module versions")

    dbg.trace("pkg: reading modules/version.txt")
    versions['pkg'] = open("modules/version.txt").readline().strip()
    dbg.trace("pkg: version: %s" % versions['pkg'])

    for mod in modDirs.keys():
      f = "modules/"+modDirs[mod]+"/version.txt"
      dbg.trace("%s: reading %s" % (mod, f))
      versions[mod] = open(f).readline().strip()
      dbg.trace("%s: version: %s" % (mod, versions[mod]))

    dbg.pop()

    # Determine user language for installation
    global language
    language = promptUser("For English, press ENTER. En francais, taper 'f'. Para espanol, presiona 'e'.")

    # Show HIP installer version & explain interactive prompting
    if language == "f":
      print("\nCette version de Historical Immersion Project date du %s.\n" % versions['pkg'])
      print("Taper 'o' ou 'oui' pour valider, ou laisser le champ vierge. Toute autre reponse sera interpretee comme un non.\n")
    elif language == "e":
      print("\nEsta vercion de Historical Immersion Project fecha del %s.\n" % versions['pkg'])
      print("Escribe 's' o 'si' para aceptar, o deja el campo en blanco. Cualquier otro caso sera considerado un 'no'.\n")
    else:
      print("\nThis version of the Historical Immersion Project was released %s.\n" % versions['pkg'])
      print("To answer yes to a prompt, respond with 'y' or 'yes' (sans quotes) or simply hit ENTER. Besides a blank line, anything else will be interpreted as 'no'.\n")

    # Are we moving the module content for speed or copying it to preserve the source?
    global move

    if language == "f":
      move = promptUser("Deplacer les fichiers plutot que les copier est bien plus rapide, mais rend l'installation de plusieurs copies du mod plus difficile.\n"
                        "Voulez-vous que les fichiers soient deplaces plutot que copies ? [oui]")
    elif language == "e":
      move = promptUser("Mover los archivos en lugar de copiarlos es mucho mas rapido, pero hace que la instalacion de varias copias sea mas complicada.\n"
                        "Quieres que los archivos de los modulos se muevan en lugar de copiarse? [si]")
    else:
      move = promptUser("Moving the files instead of copying them is much quicker. "
                        "Unfortunately, it makes installing and managing multiple versions (e.g., different mod combinations) or reinstalling difficult, "
                        "because moving effectively destroys the installer's source files rather than keeping them intact.\n\n"
                        "Do you want to have the module files moved rather than copied anyway? [yes]")

    move = isYes(move)
    dbg.trace('user choice: move instead of copy: {}'.format(move))

    # Determine installation target folder...
    defaultFolder = 'Historical Immersion Project'

    # Note that we use the case-preserving form of promptUser for the target folder (also determines name in launcher)

    global targetFolder

    if language == "f":
      targetFolder = promptUser("Installer le mod dans un repertoire existant supprimera ce repertoire. Dans quel repertoire souhaitez-vous proceder a l'installation ?\n"
                                "Laissez le champ vierge pour '%s'." % defaultFolder, lc=False)
    elif language == "e":
      targetFolder = promptUser("Instalar el mod en una carpeta existente eliminara dicha carpeta. En que carpeta deseas realizar la instalacion?\n"
                                "Dejar en blanco para '%s'." % defaultFolder, lc=False)
    else:
      targetFolder = promptUser("Installing the mod to a folder that exists will delete that folder. What folder would you like to install to?\n"
                                "Leave blank for '%s'." % defaultFolder, lc=False)

    if targetFolder == '':
      targetFolder = defaultFolder
    else: pass #TODO: verify it contains no illegal characters

    dbg.trace('user choice: target folder: {}'.format(quoteIfWS(targetFolder)))

    # Determine module combination...
    moduleOutput = []
    moduleOutput.append("Historical Immersion Project (%s)\nEnabled modules:\n" % versions['pkg'])

    PB = enableMod("Project Balance (%s)" % versions['PB'])

    SWMH = enableMod("SWMH (%s)" % versions['SWMH'])
    if SWMH:
      if language == "f":
        SWMHnative = enableMod("SWMH avec les noms culturels locaux, plutot qu'en anglais ou francises")
      elif language == "e":
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
      VIETimmersion = false
      if language == "f":
        print("VIET immersion n'est pas compatible avec SWMH et ne peut donc pas etre actif en meme temps qu'SWMH.")
      elif language == "e":
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
      ignoreF = {}
      if not SWMH:
        ignoreF = {"modules/NBRT+/map/terrain.bmp":1,
                   "modules/NBRT+/map/trees.bmp":1,
                   "modules/NBRT+/map/terrain/colormap.dds":1,
                   "modules/NBRT+/map/terrain/colormap_water.dds":1}
        moveFolder("NBRT+", ignoreFiles=ignoreF)
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
      if PB: #This should be optimized in the future (Z: this entire process should be optimized to never copy/move a target file more than once)
        moveFolder("PB_VIET_Immersion")
      else:
        moveFolder("VIET_Immersion")
        moveFolder("Converter/VIET")

      if language == "f":
        answer = promptUser("VIET Immersion necessite tous les DLC de portraits. Les avez-vous tous ? [oui]")
      if language == "e":
        answer = promptUser("VIET inmersion depende de los retratos DLC. Tiene todos los retratos DLC? [si]")
      else:
        answer = promptUser("VIET Immersion depends on the portrait DLCs. Do you have all of the portrait DLCs? [yes]")

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
      rmTree("modules") #Cleanup

    # Generate a new .mod file, regardless of whether it's default
    if targetFolder != defaultFolder:
      modFileBase = 'HIP_'+targetFolder
    else:
      modFileBase = 'HIP'

    modFilename = modFileBase + '.mod'
    dbg.trace("generating .mod file " + quoteIfWS(modFilename))

    with open(modFilename, "w") as modFile:
      modFile.write('name = "HIP - %s"  #Name that shows in launcher\n' % targetFolder)
      modFile.write('path = "mod/%s"\n' % targetFolder)
      if platform != 'mac':
        modFile.write('user_dir = "{}"  #For saves, gfx cache, etc.\n'.format(modFileBase))

    # Dump modules selected and their respective versions to <mod>/version.txt
    versionFilename = "%s/version.txt" % targetFolder
    dbg.trace("dumping compiled modpack version summary to " + quoteIfWS(versionFilename))

    with open(versionFilename, "w") as output:
      output.write("".join(moduleOutput))

    # Installation complete
    dbg.trace("installation complete")

    if language == "f":
      promptUser("Installation terminee. Taper entree pour sortir.")
    elif language == "e":
      promptUser("Instalacion terminada. Presiona Enter para salir.")
    else:
      promptUser("Installation done. Hit ENTER to exit.")

    return 0 # Return success code to OS

  except KeyboardInterrupt:
    # Ctrl-C just aborts (with a dedicated error code) rather than cause a
    # traceback. May want to catch it during filesystem modification stage
    sys.stderr.write("\nUser interrupt: terminating early...\n")
    sys.exit(2)

  except InstallerTraceNestingError as e:
    sys.stderr.write("\nFatal error: " + str(e));
    traceback.print_exc(file=sys.stderr)
    sys.stderr.write("Screenshot/copy this error and send it to the HIP team. Press ENTER to exit.")
    sys.exit(255)

  # Special handling for specific installer-understood error types (all derive from InstallerException)
  except InstallerException as e:
    sys.stderr.write("\nFatal error: " + str(e));
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
    sys.exit( main() )
