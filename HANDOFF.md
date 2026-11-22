# HANDOFF – P3D PDF Reader (Stand 1.0.20, 2026-11-22)

Einstieg für neue Entwickler. Details zu Funktionen: `README.md`, Historie: `CHANGELOG.md`, Regeln: `CLAUDE.md`.

## Was das Tool macht
Liest PDF-Plots von P&IDs (AutoCAD Plant 3D), listet PID-Tags je PDF, erkennt Doppelte, zeigt Schriftfeld/Metadaten,
erzeugt Redline-PDFs und Review-Excel. Zwei Oberflächen auf demselben Kern:
- **Desktop-App** (PySide/Qt, Aufbau wie P3D XCHANGE)
- **Web-Version** (`web\server.py`, nur Standardbibliothek) plus **Offline-HTML-Bericht** (`web\report.py`)

## Verzeichnisse
| Pfad | Inhalt |
|---|---|
| `src\p3d_pdfreader\core\` | Fachlogik **ohne Qt**: extract, patterns, render, redline, review, review_store, export, xlsx, project_defs |
| `src\p3d_pdfreader\gui\` | Qt-Oberfläche (main_window, ribbon, sheet, viewer_panel, Dialoge, web_control) |
| `src\p3d_pdfreader\web\` | HTTP-Server und Offline-Bericht, nutzt `core` unverändert |
| `src\p3d_pdfreader\assets\` | web (HTML/JS/CSS), help (Handbuch + Bilder), i18n-Katalog, Icons |
| `main_gui_kit\`, `gui\design.py`, `gui\appearance.py` | **Kopien aus XCHANGE 0.5.0 – nicht ändern** |
| `Launcher\` | `START_LAUNCHER.bat`, `launcher_gui.py` (Start, Quality gate, EXE, portable Kopie, Hotspot, Web-Server) |
| `config\` | Projektdefinitionen, Listen, Profile (Laufzeitdaten) |
| `data\exports\` | Export-Ziel (Berichte) |
| `tools\` | Generatoren: Handbuch-Bilder, i18n-Katalog, Versionsinfo für EXE |
| `tests\` | pytest; `test_architecture.py` prüft u. a. „core ohne Qt“ |

## Starten / Testen
- Python: `C:\Users\mail\AI_Coworker_Claude\Tools_Central\Python\python\python.exe` (überschreibbar per `P3D_PDFREADER_PYTHON`)
- App: `start_pdf_reader.bat` oder Launcher
- Web: `start_web_server.bat` oder Launcher-Karte „Web server“; Dev-Konfiguration in `.claude\launch.json` (Port 8766)
- Tests (PowerShell):
  ```powershell
  $env:QT_QPA_PLATFORM='offscreen'; $env:PYTHONPATH='src;.;tests'; & 'C:\Users\mail\AI_Coworker_Claude\Tools_Central\Python\python\python.exe' -m pytest
  ```
- EXE: `build_exe.bat` (onefile) bzw. `build_exe.bat onedir` → `build_exe\dist\`

## Verbindliche Regeln (Kurzfassung von CLAUDE.md)
1. Nach **jeder** Anpassung Version an dritter Stelle erhöhen: `VERSION` + neuer Abschnitt `## 1.0.x – Datum` in `CHANGELOG.md`.
2. GUI-Texte auf Deutsch; keine eigenen Farben/Hex-Werte – nur aus design/appearance/Kit-Theme (gilt auch für `assets\web`).
3. PDFs nur lesen. Keine festen `A:`-Pfade (A: ist Subst auf `C:\Users\mail\AI_Coworker_Claude`), Pfade nur nach `resolve()` vergleichen.
4. P3D XCHANGE (`...\P3D_XCHANGE Modul`) ist nur Vorlage – dort nichts ändern. GUI-Vorgaben: dessen `docs\GUI_DESIGN.md`.
5. Neue Funktionen in `core` implementieren, Desktop und Web nur als dünne Oberflächen.

## Aktueller Stand / offene Punkte
- Letzter Commit: 1.0.14. Die Versionen **1.0.15–1.0.17 sind nicht committet** (u. a. Web-Steuerung in der App
  `gui\web_control.py`, Offline-Bericht `web\report.py`, Launcher-Web-Karte, Ordner `config\`). Erster Schritt:
  Diff prüfen, Tests laufen lassen, committen.
- `config\` enthält Laufzeitdaten (u. a. `pidtag_project.db`, Excel) – vor dem Commit klären, was ins Repo gehört
  und was in `.gitignore`.
- Was in den letzten Versionen geändert wurde und noch offen ist, steht oben im `CHANGELOG.md`.

## Typischer Arbeitsablauf
1. `CHANGELOG.md` oben lesen, `git status` prüfen.
2. Änderung in `core` (mit Test), dann GUI/Web anbinden.
3. Tests offscreen ausführen, ggf. Handbuch (`assets\help\handbuch.html`, Bilder via `tools\make_help_images.py`) und i18n (`tools\make_i18n_catalog.py`) aktualisieren.
4. Version + CHANGELOG, dann committen.
