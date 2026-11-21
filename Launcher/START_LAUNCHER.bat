@echo off
rem Startet den Launcher von P3D PDF Reader mit dem zentralen Python aus Tools_Central (%~dp0 = Ordner dieser Datei).
rem Anderes Python:  set P3D_PDFREADER_PYTHON=C:\Pfad\zu\python.exe
setlocal EnableExtensions
title P3D PDF Reader - Launcher
set "HERE=%~dp0"
set "PY=%HERE%..\..\..\Tools_Central\Python\python\python.exe"
rem Firmen-PC / USB-Kopie: kein Tools_Central - dann das Python aus python_company.txt (im Launcher eingestellt),
rem sonst das installierte Python 3.14
if not exist "%PY%" (
  set "PY=C:\Program Files\Python314\python.exe"
  if exist "%HERE%python_company.txt" for /f "usebackq delims=" %%P in ("%HERE%python_company.txt") do set "PY=%%~P"
)
if defined P3D_PDFREADER_PYTHON set "PY=%P3D_PDFREADER_PYTHON%"
if not exist "%PY%" goto :nopython
if not exist "%HERE%launcher_gui.py" goto :nolauncher
set "PYTHONUTF8=1"
"%PY%" "%HERE%launcher_gui.py"
exit /b %errorlevel%

:nopython
echo [FEHLER] Python nicht gefunden: %PY%
echo          P3D_PDFREADER_PYTHON auf ein python.exe mit PySide6 setzen.
pause
exit /b 1

:nolauncher
echo [FEHLER] launcher_gui.py liegt nicht neben dieser Datei: %HERE%
pause
exit /b 1
