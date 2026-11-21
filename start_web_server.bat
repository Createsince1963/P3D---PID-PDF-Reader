@echo off
rem P3D PDF Reader als Web-Server starten (%~dp0 = Ordner dieser Datei). Kollegen oeffnen http://<dieser PC>:8765/
rem Python wie start_pdf_reader.bat: P3D_PDFREADER_PYTHON > Tools_Central > Launcher\python_company.txt > Python 3.14
rem Ohne Argumente: im Netzwerk erreichbar (--host 0.0.0.0 --port 8765). Eigene Argumente ersetzen die Vorgabe,
rem z. B. start_web_server.bat --host 127.0.0.1 --port 9000 --source "\\server\freigabe\PID Plots"
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
set "PYTHONUTF8=1"
if "%~1"=="" (
  "%PY%" -m p3d_pdfreader.web --host 0.0.0.0 --port 8765
) else (
  "%PY%" -m p3d_pdfreader.web %*
)
endlocal
