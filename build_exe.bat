@echo off
rem ============================================================================
rem  P3D PDF Reader - EINE einzelne EXE bauen (PyInstaller, onefile)
rem
rem  Ergebnis:  build_exe\dist\P3D_PDF_Reader.exe   (Ordner per BUILD_OUT ueberschreibbar)
rem
rem  Fuer die IT:
rem   - keine Installation, keine Administratorrechte: die EXE laeuft aus jedem Ordner
rem   - Daten, Einstellungen, Sicherungen, Logs: %LOCALAPPDATA%\P3D_PDFREADER
rem     (oder Ordner aus der Umgebungsvariable P3D_PDFREADER_HOME)
rem   - die EXE entpackt sich beim Start nach %TEMP% (benutzerschreibbar)
rem   - kein UPX (Packer loesen oft Virenwarnungen aus), kein Registry-Eintrag, kein Dienst
rem   - nicht signiert: bei Bedarf SHA256 (unten ausgegeben) in der Allow-List hinterlegen
rem
rem  Aufruf:  build_exe.bat            (Standard: onefile, eine EXE)
rem           build_exe.bat onedir     (Ordner build_exe\dist\P3D_PDF_Reader\ - ganzen Ordner kopieren; schneller Start,
rem                                     weniger Virenscanner-/AppLocker-Probleme, empfohlen fuer Firmenrechner)
rem           build_exe.bat noversion  (ohne Versionsinfo in der EXE - nur zur Fehlersuche bei Richtlinien-Sperren)
rem           build_exe.bat console   (mit Konsolenfenster fuer die Fehlersuche; kombinierbar: onedir console)
rem ============================================================================
setlocal EnableExtensions
set "TOOL=%~dp0"
if "%TOOL:~-1%"=="\" set "TOOL=%TOOL:~0,-1%"
if not defined BUILD_OUT set "BUILD_OUT=%TOOL%\build_exe"
rem Das zentrale Python enthaelt fremde Qt-Bindungen (PyQt5 ...): PyInstaller bricht bei mehreren Qt-Bindungen ab.
rem Deshalb wird in einer eigenen, sauberen Umgebung gebaut (.venv_build, nur PySide6 + requirements.txt + PyInstaller).
rem Mit "set BUILD_PY=Pfad\zu\python.exe" laesst sich ein anderer Interpreter erzwingen (dann keine venv).
rem Ein geerbtes PY (z.B. aus START_LAUNCHER.bat) wird bewusst ignoriert - sonst wuerde das zentrale Python
rem mit PyQt5 benutzt und PyInstaller bricht ab.
set "PY="
if defined BUILD_PY set "PY=%BUILD_PY%"
set "BASEPY=%TOOL%\..\..\Tools_Central\Python\python\python.exe"
set "VENV=%TOOL%\.venv_build"
set "EXCL=--exclude-module tkinter --exclude-module PyQt5 --exclude-module PyQt6 --exclude-module PySide2"
set "MODE=--windowed"
set "PACK=--onefile"
for %%A in (%*) do (
  if /i "%%~A"=="console" set "MODE=--console"
  if /i "%%~A"=="onedir" set "PACK=--onedir"
  if /i "%%~A"=="noversion" set "NOVER=1"
)

if not defined PY (
  set "PY=%VENV%\Scripts\python.exe"
  if not exist "%VENV%\Scripts\python.exe" (
    if not exist "%BASEPY%" (
      echo Basis-Python nicht gefunden: %BASEPY%
      exit /b 1
    )
    echo Build-Umgebung anlegen: %VENV%
    "%BASEPY%" -m venv "%VENV%" || exit /b 1
  )
  "%VENV%\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r "%TOOL%\requirements-build.txt"
  if errorlevel 1 (
    echo *** Installation der Build-Abhaengigkeiten fehlgeschlagen
    exit /b 1
  )
)
if not exist "%PY%" (
  echo Python nicht gefunden: %PY%
  exit /b 1
)
"%PY%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo PyInstaller fehlt. Einmalig installieren:  "%PY%" -m pip install pyinstaller
  exit /b 1
)
"%PY%" -c "import PySide6" >nul 2>&1
if errorlevel 1 (
  echo PySide6 fehlt im Build-Python: %PY%
  exit /b 1
)

set /p VER=<"%TOOL%\VERSION"
echo.
echo === P3D PDF Reader %VER% - EXE bauen ===
echo Python : %PY%
echo Ausgabe: %BUILD_OUT%
echo.

if exist "%BUILD_OUT%" rmdir /s /q "%BUILD_OUT%"
mkdir "%BUILD_OUT%" || exit /b 1

rem --- Versionsinformationen der EXE (Eigenschaften > Details) ---
"%PY%" "%TOOL%\tools\make_version_info.py" "%VER%" "%BUILD_OUT%\version_info.txt"
if errorlevel 1 exit /b 1
set "VERARG=--version-file"
set "VERVAL=%BUILD_OUT%\version_info.txt"
rem noversion: ohne Versionsinfo (Platzhalter-Option, damit die Zeile unten gueltig bleibt)
if defined NOVER (
  set "VERARG=--log-level"
  set "VERVAL=INFO"
)

"%PY%" -m PyInstaller --noconfirm --clean --noupx %PACK% %MODE% ^
  --name P3D_PDF_Reader ^
  --distpath "%BUILD_OUT%\dist" --workpath "%BUILD_OUT%\work" --specpath "%BUILD_OUT%" ^
  --paths "%TOOL%\src" --paths "%TOOL%" ^
  --add-data "%TOOL%\src\p3d_pdfreader\assets;p3d_pdfreader\assets" ^
  %VERARG% "%VERVAL%" ^
  %EXCL% ^
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.Qt3DCore --exclude-module PySide6.QtQuick --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtMultimedia --exclude-module PySide6.QtCharts --exclude-module PySide6.QtDataVisualization ^
  "%TOOL%\run_p3d_pdfreader.py"
if errorlevel 1 (
  echo.
  echo *** Build fehlgeschlagen ***
  exit /b 1
)

set "EXE=%BUILD_OUT%\dist\P3D_PDF_Reader.exe"
if "%PACK%"=="--onedir" set "EXE=%BUILD_OUT%\dist\P3D_PDF_Reader\P3D_PDF_Reader.exe"
if not exist "%EXE%" (
  echo *** EXE nicht gefunden: %EXE%
  exit /b 1
)
rem --- Rauchtest: die EXE muss starten und mit Code 0 enden (windowed: start /wait liefert den Exitcode) ---
start "" /wait "%EXE%" --version
if errorlevel 1 (
  echo *** Rauchtest fehlgeschlagen: die EXE startet nicht ^(--version^)
  exit /b 1
)
echo Rauchtest: OK
echo.
echo === Fertig ===
echo %EXE%
for %%F in ("%EXE%") do echo Groesse: %%~zF Bytes
echo SHA256 :
certutil -hashfile "%EXE%" SHA256 | findstr /v /c:"hash" /c:"CertUtil"
echo.
echo Hinweis: Beim ersten Start legt die EXE %%LOCALAPPDATA%%\P3D_PDF_Reader an. Pruefung: Menueband - Systempruefung.
endlocal
