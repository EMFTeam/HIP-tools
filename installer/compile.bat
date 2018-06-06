C:\prog\Python27\python.exe setup.py py2exe
move dist\main.exe "HIP.exe"
move dist\python27.dll ""
move dist\library.zip ""
RD /S /Q dist
RD /S /Q build
