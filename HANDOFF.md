# HANDOFF – P3D PDF Reader (Stand 1.0.45, 2026-11-24)

Einstieg für neue Entwickler. Funktionen aus Nutzersicht: `README.md`. Historie mit Begründungen: `CHANGELOG.md`
(oben = neu). Projektregeln: `CLAUDE.md` (liegt nur lokal, steht in `.gitignore`; die Regeln sind unten zusammengefasst).

## Was das Tool macht
Liest PDF-Plots von P&IDs (AutoCAD Plant 3D), listet die PID-Tags je PDF, erkennt Doppelte, liest Schriftfeld und
Metadaten, prüft Tags optional gegen Projektdefinitionen (wie P3D Tag Compliance), gleicht sie mit einer importierten
Excel-Liste ab (Datenlink) und erzeugt Redline-PDFs und Review-Excel. Ein Kern, drei Oberflächen:
- **Desktop-App** (PySide6, Aufbau wie P3D XCHANGE) – Hauptprodukt, hier passiert die meiste Entwicklung
- **Web-Version** (`web\server.py`, nur Standardbibliothek) für Kollegen im Firmennetz
- **Offline-HTML-Bericht** (`web\report.py`), eine Datei ohne Server

## Verzeichnisse
| Pfad | Inhalt |
|---|---|
| `src\p3d_pdfreader\core\` | Fachlogik **ohne Qt** (Architekturtest prüft das): `extract` (PDF → Metadaten, Schriftfeld, Tags), `patterns`, `render`, `redline`, `review`, `review_store` (Review-Einträge je PDF), `export`, `xlsx`, `project_defs` (Projektprüfung), `project_settings` (Tool-Einstellungen in der Projekt-DB), `data_link` (Importliste, Abgleich) |
| `src\p3d_pdfreader\gui\` | Qt-Oberfläche. Kern: `main_window.py` (Hauptfenster, Blätter, Menüband, `DataTable`). Dazu `data_link_ui` (Datenlink im Hauptfenster), `tile_editor\` (Vollfenster Kachel-Editor), `project_dialog`/`project_tiles` (Projektdefinitionen), `table_views`/`table_profiles`/`table_menu`/`table_export` (Tabellenstandard), `msgbox` (Auswertung von Dialog-Buttons), `viewer_panel`/`preview` (PDF-Viewer), `web_control` |
| `src\p3d_pdfreader\web\` | HTTP-Server und Offline-Bericht, nutzen `core` unverändert |
| `src\p3d_pdfreader\assets\` | `web\` (HTML/JS/CSS), `help\` (Handbuch + Bilder), `i18n\` (`catalog*.json`, alle Dateien werden geladen), `icons\` |
| `main_gui_kit\`, `gui\design.py`, `gui\appearance.py` | **Kopien aus XCHANGE 0.5.0 – nicht ändern** (Regel aus CLAUDE.md) |
| `gui\ribbon.py`, `sheet.py`, `progress.py`, `icons.py` | ebenfalls unverändert aus XCHANGE 0.5.0 übernommen (Kopfkommentar „Quelle“) – Erweiterungen daneben (`ribbon_fold.py`, `toolstrip.py`, `ribbon_heads.py`) |
| `src\p3d_pdfreader\column_editor\` | **Kopie des Kachel-Editors aus Tag Compliance – nicht von Hand ändern** (`QUELLE.md`); Einbindung in `gui\tile_editor\` |
| `Launcher\` | `START_LAUNCHER.bat`, `launcher_gui.py` (Start, Quality gate, EXE, portable Kopie, Hotspot, Web-Server) |
| `data\` (in `.gitignore`) | Datenordner im Entwicklungsbetrieb: `config\` (Einstellungen, Importliste), `reviews\`, `projects\`, `exports\`, `logs\` |
| `config\` (Wurzel, **nicht in Git**) | Alte Projektdefinitionen/Listen (Okt. 2026). Weder App noch Launcher nutzen sie (beide: `data\`); Nutzerdaten, nicht löschen, mit dem Nutzer klären |
| `tools\` | Generatoren: Handbuch-Bilder (`make_help_images`, `make_help_workflow`), i18n-Katalog, Versionsinfo für EXE, `translate_column_editor` |
| `tests\` | pytest, siehe unten |

## Starten / Testen
- Python: `C:\Users\mail\AI_Coworker_Claude\Tools_Central\Python\python\python.exe` (überschreibbar per `P3D_PDFREADER_PYTHON`)
- App: `start_pdf_reader.bat` oder Launcher; Web: `start_web_server.bat` oder Launcher-Karte „Web server“
- Tests (PowerShell, ganze Suite ca. 8 Minuten, 75 Tests):
  ```powershell
  $env:QT_QPA_PLATFORM='offscreen'; $env:PYTHONPATH='src;.;tests'; & 'C:\Users\mail\AI_Coworker_Claude\Tools_Central\Python\python\python.exe' -m pytest -q -W ignore tests
  ```
- Viele Tests brauchen echte Plots in `%USERPROFILE%\Downloads\PID Plots` (anderer Ordner: `P3D_PDFREADER_SAMPLES`), sonst werden sie übersprungen.
- Der Kachel-Editor (QML) braucht im Test `QT_QUICK_BACKEND=software` (setzt der Test selbst).
- EXE: `build_exe.bat` (onefile) bzw. `build_exe.bat onedir` → `build_exe\dist\` (Ordner nicht in Git).

## Verbindliche Regeln (Kurzfassung von CLAUDE.md)
1. Nach **jeder** Anpassung die dritte Stelle der Version erhöhen: `VERSION` + neuer Abschnitt `## 1.0.x – Datum` oben in `CHANGELOG.md` (auch in `CLAUDE.md` „Aktuell 1.0.x“ nachziehen).
2. GUI-Texte auf Deutsch; Übersetzungen (en/fr) in `assets\i18n\catalog*.json`. Keine eigenen Farben/Hex-Werte – nur aus design/appearance/Kit-Theme (gilt auch für `assets\web`).
3. PDFs nur lesen. Keine festen `A:`-Pfade (A: ist Subst auf `C:\Users\mail\AI_Coworker_Claude`), Pfade nur nach `resolve()` vergleichen.
4. P3D XCHANGE ist nur Vorlage – dort nichts ändern. GUI-Vorgaben: `...\P3D_XCHANGE Modul\docs\GUI_DESIGN.md`.
5. Neue Fachlogik in `core` (ohne Qt, mit Test), Desktop und Web nur als dünne Oberflächen.
6. Kopierte Module (`main_gui_kit`, `design`, `appearance`, `column_editor`) nicht ändern – Verhalten im Tool-Code anpassen (Beispiele: `gui\table_views.py`, `gui\tile_editor\`).

## Wichtige Abläufe im Code
- **Scan:** `MainWindow.scan` → `worker.ScanWorker` (Thread) → `core.extract.read_pdf` je PDF → `_refresh` füllt Dateiliste/Alle Tags.
- **PDF-Wechsel:** `TagsSheet._file_changed` → ungespeicherte Review-Einträge abfragen (`confirm_unsaved`) → Filter der Tag-Tabelle auf Standard (`_default_tag_filters`) → `_load_with_progress` (ReviewStore laden, Tag-Tabelle, Viewer).
- **Tag-Tabelle:** `TagsSheet.tag_rows_for(result, store)` baut die Zeilen (Spalten `TAG_COLS` + Datenlink-Spalten); `_only_duplicates` füllt die Tabelle neu (Filter „Nur doppelte“/„Nur Abweichungen“). Dieselben Zeilen nutzt die Tabellen-Vorschau (`MainWindow.preview_table`).
- **Review-Einträge:** `core.review_store.ReviewStore` je PDF, jede Speicherung ist ein neuer Stand: mit Projekt in dessen Datenbank (`core.project_store`, Tabelle `review_versions`; JSON-Altstände werden beim ersten Laden übernommen), sonst mit Zeitstempel in `data\reviews\<PDF>_<hash>\`. `project_store.activate` setzt die Oberfläche; ohne Aufruf (Web-Server) gilt `project_db` aus `state.json`. Gelesene PDF-Daten: `project_store.ScanCache` (gültig bei gleicher Dateigröße, Änderungszeit, Tool-Version, Tag-Mustern). Einstellungen: `MainWindow.autosave_project` → `project_settings.autosave`. Bearbeitet in `ReviewModel` (Bearbeiten-Modus, oder per Rechtsklick über `ReviewModel.set_cell`). **Aus dem Review genommene Tags** stehen in `ReviewStore.removed`; jede Ausgabe holt die Tags über `store.visible(...)` bzw. `review_store.visible_tags(result)` – wer eine neue Ausgabe baut, muss das ebenfalls tun.
- **Tag-Tabelle, Layouts:** `TagsSheet._bind_tag_layout` hängt die gemerkte Ansicht je nach Importspalten an `auto|tags` oder `auto|tags_link` (Kit-Funktion `bind_layout_persistence`).
- **Datenlink:** `core.data_link.ImportTable` (gespeichert in `data\config\data_link.json`) + `DataLink` (Index, Abgleich). Datenlink 1 = Zeichnung (Dateiliste ↔ z. B. „P&ID No.“), Datenlink 2 = Tag (Tag-Tabelle ↔ z. B. „Tag -PID“). Mit beiden zählen nur Importzeilen derselben Zeichnung. Abgleich: exakt, sonst Endung ab Bindestrich; Zeichnung zusätzlich ohne „.pdf“ und „ (2)“ (`file_variants`). Richtung der Tag-Tabelle: `DataLink.tag_join` (PDF → Liste / Liste → PDF / beide), fehlend = „n.a.“. Im Hauptfenster: `gui\data_link_ui.LinkController`.
- **Review Importliste:** `core.data_link.review_rows` (Prüfergebnis je Zeile) → Blatt `LinkReviewSheet`.
- **Projektmodus:** `core.project_defs.Checker`; Projekt-DB speichert auch alle Tool-Einstellungen (`core.project_settings`).
- **Tabellenstandard:** `DataTable` in `main_window.py` (Kit-Tabelle + Blattfilter, Excel-Ecke, Rechtsklick-Menüs, Layout-Leiste). Gemerkte Ansichten über `gui\table_views.py` (`data\config\table_views.json`).

## Stolperfallen (aus der Praxis)
- **Dialog-Buttons nie mit `box.clickedButton() is button` auswerten.** Der i18n-Filter übersetzt Dialoge beim Anzeigen; danach ist der Python-Wrapper des gemerkten Buttons ungültig und der Vergleich schlägt fehl (so ließ sich das Fenster mit ungespeicherten Reviews nicht schließen). Immer `gui\msgbox.clicked(box, *buttons)` verwenden.
- **Das Kit wendet die gemerkte Tabellenansicht bei jedem neuen Modell erneut an** (Scan, PDF-Wechsel) – inklusive Filtern. Für Dateiliste und Tag-Tabelle werden Filter deshalb nicht gespeichert (`table_views.LayoutStore`, `NO_FILTER_TABLES`). Wer Filter für weitere Tabellen abschalten will: dort eintragen.
- **Modale Dialoge blockieren Tests.** `MainWindow.close()` fragt bei ungespeicherten Review-Einträgen nach – im Test vorher `page.save_review()` aufrufen oder die Frage per `monkeypatch` beantworten.
- **Parallele pytest-Läufe** teilen sich `.pytest_tmp` und brechen mit `PermissionError` ab – nur einen Lauf gleichzeitig.
- **Zeichnungsnummer im Schriftfeld:** größte Schrift mit „-PID-“ im unteren Zehntel; Schriftgröße = kürzere Seite des Wortrahmens (sonst gewinnen senkrechte Verweise). Ausweichsuche ab 60 % Breite nur bei deutlich größerer Schrift. Bei Änderungen an `extract.py` den Lauf über alle Test-PDFs wiederholen (Stand: 647 von 663 richtig, 0 falsch; 16 ohne lesbaren Text im Schriftfeld).
- **PowerShell 5.1 und mehrzeilige Git-Commit-Texte:** Here-Strings werden an `git` falsch übergeben; Nachricht in eine Datei schreiben und `git commit -F <Datei>` nutzen.
- Nach GUI-Änderungen: Handbuch-Bilder mit `tools\make_help_images.py` bzw. `tools\make_help_workflow.py` neu erzeugen (Workflow-Bilder mit `QT_QPA_PLATFORM=windows`, sonst fehlt die QML-Schrift).

## Aktueller Stand / offene Punkte
- Stand **1.0.43**, committet, Tests 79/79 grün (ganze Suite ca. 8 Minuten). Ungetrackt und bewusst nicht committet: `Anpassung_Importliste_*.json`, `Tabellenprofil_*.json` (vom Nutzer gespeicherte Dateien), `build_exe\`, `config\`.
- Erledigt in 1.0.42: Handbuch auf Stand 1.0.42, Launcher „Open data/logs“ zeigt auf den Datenordner der App, Export Excel/CSV ohne X/Y.
- 1.0.43: Importspalten ein/aus mit getrennten Layouts, Menü Importliste, Dateiliste einklappbar, Rechtsklick der Review-Tabelle (Einfügen, Wert übernehmen, leeren, Zeilen aus Review nehmen), Autofill-Knopf blau. Beim ersten Einblenden der Importspalten ist deren Layout leer (früher lag es unter `auto|tags`).
- **Web-Version:** zeigt aus dem Review genommene Tags in der Tag-Liste noch an (Redline/Review-Excel/CSV lassen sie weg).
- **Handbuch-Workflow-Bilder** (`tools\make_help_workflow.py`, `img\wf_*.png`) zeigen noch den Stand vor 1.0.38 (z. B. ohne Knopf „Abgleich“). Neu erzeugen, wenn die Oberfläche fertig abgenommen ist (mit `QT_QPA_PLATFORM=windows`).
- **i18n:** Texte der neuen Tabellen-Vorschau und des Kachel-Editor-Zeilenzählers sind nur deutsch; `i18n.untranslated()` listet fehlende Texte zur Laufzeit.
- **Web-Version** kennt Datenlink, Abgleich, Tabellen-Vorschau und Projektmodus nicht (siehe README, „Noch nicht in der Web-Version“).
- **Datenlink-Feld „PDF“:** funktioniert seit 1.0.40. Empfehlung an Nutzer bleibt „Zeichnungsnr.“, weil sie unabhängig vom Dateinamen ist.
- Alles aus 1.0.38–1.0.42 ist mit Tests und Skripten auf den echten Testdaten geprüft, aber noch nicht vom Nutzer in der laufenden App abgenommen.

## Typischer Arbeitsablauf
1. `CHANGELOG.md` oben und diese Datei lesen, `git status` prüfen.
2. Änderung in `core` mit Test, dann GUI/Web anbinden.
3. Tests offscreen ausführen; ggf. Handbuch, Hilfebilder und i18n (`catalog*.json`) aktualisieren.
4. Version + CHANGELOG (+ `CLAUDE.md` „Aktuell“), dann committen.
