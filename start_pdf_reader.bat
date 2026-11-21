@echo off
rem P3D PDF Reader starten (%~dp0 = Ordner dieser Datei)
rem Reihenfolge: P3D_PDFREADER_PYTHON > zentrales Python aus Tools_Central (Entwicklungs-PC)
rem             > Firmen-PC-Python aus Launcher\python_company.txt (im Launcher eingestellt, wird bei "Copy" mitkopiert)
rem             > installiertes Python 3.14
setlocal
set "TOOL=%~dp0"
set "PY=%TOOL%..\..\Tools_Central\Python\python\python.exe"
if not exist "%PY%" (
  set "PY=C:\Program Files\Python314\python.exe"
  if exist "%TOOL%Launcher\python_company.txt" for /f "usebackq delims=" %%P in ("%TOOL%Launcher\python_company.txt") do set "PY=%%~P"
)
if defined P3D_PDFREADER_PYTHON set "PY=%P3D_PDFREADER_PYTHON%"
if not exist "%PY%" (
  echo Python nicht gefunden: %PY%
  echo Im Launcher unter "Company PC" den python.exe-Pfad eintragen oder P3D_PDFREADER_PYTHON setzen.
  pause
  exit /b 1
)
set "PYTHONPATH=%TOOL%src;%TOOL%"
"%PY%" -m p3d_pdfreader %*
endlocal
