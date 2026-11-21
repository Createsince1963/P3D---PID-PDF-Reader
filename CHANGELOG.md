# Changelog

## 1.0.11 – 2026-11-21
- **Menüband:** Jede Gruppe hat oben eine **dunkelblaue Überschrift** (Farbe des Tabellenkopfs, folgt der Akzentfarbe). `ribbon.py` (Kopie aus XCHANGE) bleibt unverändert; neues Modul `gui\ribbon_heads.py`.
- **Gruppe „Einstellungen“** (Pfade, Tag-Muster) steht jetzt direkt nach „1 Einlesen“, vor „2 Prüfen“.
- **Rechtsklick in Tabellen wie P3D XCHANGE** (`gui\table_menu.py`), in allen Tabellen (Dateien, Tags, Alle Tags):
  - **Zelle:** Kopieren (markierte Zellen, Tabulator-getrennt), Zeile kopieren, Zeile mit Überschriften kopieren, Nur „Wert“ in „Spalte“ zeigen, Filter der Spalte zurücksetzen, Alle Filter zurücksetzen, Spalten …, Nach Excel ….
  - **Excel-Symbol (Tabellenecke), Rechtsklick:** Dialog **„Spalten …“** wie XCHANGE (Nach oben/unten, Anzeigen Ja/Nein, „Standard“ = wie eingelesen).
  - Spaltenkopf-Menü (Kit) unverändert.
- **Handbuch als interaktive HTML-Datei** (`assets\help\handbuch.html`, öffnet über Hilfe › Handbuch im Browser): klickbarer Nachbau des Menübands mit den App-Symbolen und Erklärung je Knopf, Schnellstart, Rechtsklick-Demo, Suche mit Hervorhebung, Inhaltsverzeichnis. Die Symbole erzeugt `tools\make_help_images.py` direkt aus der App (neue PNG-Symbole in `assets\icons` kommen beim erneuten Ausführen automatisch mit). Ohne HTML-Datei öffnet weiterhin die README.
- Übersetzungen EN/FR für die neuen Menütexte (`tools\make_i18n_catalog.py`, Katalog neu erzeugt).
- Tests: `test_ribbon_menus.py` (Gruppenköpfe oben, Reihenfolge, Zellenmenü, Wertfilter, Spalten-Dialog).

## 1.0.10 – 2026-11-21
- **Projekt-Prüfung mit benannten Befunden** (Spalte „Projekt-Prüfung“; mehrere Befunde werden mit „ + “ verbunden, es wird immer alles gegengeprüft):
  - **Regelfehler Projektdefinition:** Trennzeichen-Regel verletzt (z. B. alle Volltags `203-17-111-TZIT-011`: „-“ statt „_“) oder Aufbau passt nicht zur Tag-Struktur.
  - **Code fehlt in Projektdefinition:** Code nicht in der Liste, z. B. `…LTCHW_CS01…` (Fluid code fehlt in der Media list), `151HPP01` (Function code HPP).
  - **Code unvollständig:** Platzhalter statt Code. Zählt bei: `?` irgendwo, `X` an Stelle von Ziffern (`AV_TL02_XXX_2"`, `VHXXX`), Code nur aus X oder mit `XX` (`SSXX`), einzelnes X für eine Ziffer eines bekannten Codes (`ST1X` → ST10). Ein X in einem Buchstaben-Code (HEX, XV, CHX) zählt nicht, ein solcher unbekannter Code „fehlt“.
  - **mehrfach vorhanden:** kommt zu jedem Befund dazu, wenn der Tag auf einer Seite mehrfach steht, z. B. „Code unvollständig + mehrfach vorhanden“.
  - Je Tag höchstens ein unbekannter Code (Platzhalter an allen Stellen), sonst gilt er als Regelfehler. Verhindert irreführende Hinweise, z. B. bei `203_17_152_PFC_…` (überzähliges „_“).
- **Platzhalter-Tags werden im Projektmodus mit eingelesen** (X/? statt Ziffern, für alle Tag-Typen und Rohrleitungen). Beim Ein- und Ausschalten des Projektmodus werden geladene PDFs neu eingelesen. Im Standardmodus bleibt alles wie bisher.
- „Nur Abweichungen“, rote Rahmen im Viewer, Kopfband und Exporte erfassen jeden Befund. Review-Excel, Blatt Info: „Projekt-Befunde (Fundstellen)“.
- Beispielordner (25 PDFs, SGOPS): 23 zusätzliche Platzhalter-Tags. Alle drei Befundarten kommen vor, teils kombiniert, z. B. `LTCWR_ST04_XXX_1"`: Fluid code fehlt + Line number Platzhalter).
- Tests: `test_project_defs.py` um Befund-Kombinationen und das Einlesen von Platzhaltern erweitert (jetzt 10 Tests).

## 1.0.9 – 2026-11-21
- **Projektmodus mit Projektdefinitionen (Modul aus P3D Tag Compliance):** neue Menüband-Gruppe „Projekt“ (vorne). „Projektmodus: an/aus“ schaltet das Modul ein und aus; **aus = Standardmodus wie bisher** (keine Prüfspalten, keine Projektregeln). Modus und Projekt werden gemerkt (`config\state.json`).
- **Projekt wählen:** aus Tag Compliance übernehmen (`pidtag_project.db` wählen, wird nur gelesen), Projekt öffnen, neues Projekt; Liste der Projekte in `<Datenordner>\projects\*.db`.
- **Projekt-Datenbank im Schema von Tag Compliance:** alle Definitionstabellen (General/Building/System/Fitting/Function/Pipeclass codes, Nummernkreise, Tag structures, Tag segments, Notes, Quelle), alle Listen (z. B. Media list, Pipeclass Project) und die Trennzeichen-Regel (`-` → `_`). Lizenz-, DCF- und Projektdatei-Tabellen werden nicht übernommen. Erneute Übernahme ersetzt die Definitionen; eigene Prüfregeln und PDF-Strukturen bleiben.
- **Verwaltungsdialog „Projektdefinitionen …“** (Aufbau wie in Tag Compliance): Tabellen/Listen mit Zeilenzahl, bearbeitbares Raster mit Filter, + Zeile / Zeile löschen / Speichern / Verwerfen (Rückfrage bei ungespeicherten Änderungen), Neue Liste, Liste aus Excel, Spalten, Liste löschen, Excel-Export/-Import (Blattnamen wie Tag Compliance), Übernahme aus Tag Compliance (optional vorher Excel-Sicherung), Projektname, Standard-Prüfregeln, „Tag testen“.
- **Prüfregeln** (Tabelle „PDF-Prüfregeln“): PDF-Tag-Typ → Tag-Struktur(en) aus Segmenten (Segment-Quellen wie im Segment Tag Designer: Codeliste, Liste|Spalte, const:, seq:n, free). Mitgeliefert: PDF_EQUIPMENT (Unit + Function code + Nr.), PDF_VALVE (Fitting type + Nr.), PDF_PIPE_LINE und PDF_HOSE, PDF_FULL_TAG (Building_System_Unit_Tag), PDF_INSTRUMENT. Zeichnungsverweise werden nicht geprüft.
- **Im Projektmodus:** Spalten „Projekt-Prüfung“ (OK/Fehler) und „Projekt-Hinweis“ (passende Struktur bzw. erstes nicht passendes Segment oder Trennzeichen-Regel) in „Tags der gewählten PDF“ und „Alle Tags“; Filter „Nur Abweichungen“ (Leiste und Menüband); Viewer: Abweichungen rot umrandet, außer der Review ist „OK“ oder „Nicht relevant“; Kopfband mit Projekt und Anzahl Abweichungen; Export Excel/CSV und Review-Excel mit den Prüfspalten (Info-Blatt mit Projekt und Abweichungen).
- Beispielordner (25 PDFs, SGOPS-Definitionen): u. a. alle Volltags `203-17-…` → Trennzeichen „-“ statt „_“, `151HPP01`/`215CHX01` → Function code nicht in der Liste, `…LTCHW_CS01…` → Fluid code nicht in der Media list.
- Neu: `core\project_defs.py` (ohne Qt), `gui\project_dialog.py`; Spalten der Tag-Tabelle: Prüfspalten nach „Seiten“. Web-Version unverändert (noch ohne Projektmodus).
- Tests: `tests\test_project_defs.py` (8 Tests: Anlage, Übernahme nur lesend, Prüfung und Hinweise, Tabellen/Listen, erneute Übernahme, Excel, Viewer-Status, GUI-Umschaltung mit Dialog); `test_gui.py` an die neuen Spaltenpositionen angepasst.

## 1.0.8 – 2026-11-21
- **Monochrom-Ansicht im PDF-Viewer:** Button „Monochrom“ in der Viewer-Leiste (Desktop und Web). Die Seite wird wie ein Schwarz-Weiß-Plot gezeigt: Weiß bleibt weiß, jede kräftige Farbe (auch Gelb, Cyan) wird schwarz, Pastelltöne grau, Kantenglättung bleibt. Zoom, Drehung und Markierungen bleiben beim Umschalten erhalten; die Wahl wird gemerkt (Desktop `config\state.json`, Web im Browser). Nur Ansicht – die PDF wird nicht verändert.
- Neues Kernmodul `core
ender.py` (ohne Qt, ohne numpy), genutzt von Desktop-Vorschau und Web-Server (`/render?...&mono=1`). Monochrom kostet beim Grundbild ca. 0,7 s zusätzlich je Seite.
- **Alle gefundenen Tags im Viewer umrandet:** grün = korrekt, rot = fehlerhaft (Review „Korrektur erforderlich“). Tags ohne Review oder mit anderem Review-Wert sind grün. Die Farben ändern sich sofort beim Bearbeiten der Review-Spalte. Farben aus dem Kit-Theme (`LIGHT.ok` / `LIGHT.err`). Doppelte Tags bleiben zusätzlich gelb hinterlegt, die Auswahl-Markierung liegt darüber.
- Web: alle gefundenen Tags grün umrandet (Review-Status gibt es im Web noch nicht, daher dort kein Rot).
- Tests: `tests	est_viewer_display.py` (Monochrom-Bild, Statuszuordnung, Viewer-Umschaltung und Rahmenfarben).

## 1.0.7 – 2026-11-20
- **Web-Version (Prototyp) für Browser-Zugriff im Firmennetz:** `python -m p3d_pdfreader.web` startet einen Web-Server, der nur die Python-Standardbibliothek braucht. Die Kollegen öffnen `http://<PC>:8765/` im Browser. Erkennung, Redline, Review-Excel und Export kommen unverändert aus `core\`. Die Ergebnisse sind identisch mit der Desktop-App: Für EQPM-001 werden Tags, Anzahl, Schriftfeld und Revision per Test verglichen.
- Oberfläche im Aufbau der Desktop-App: Menüband, Blätter „PID-Tags“ und „Alle Tags“, Tabellen mit Spaltenfiltern, Sortierung und Mehrfachauswahl. Die Farben stammen nur aus `design.py`, `appearance.py` und dem Kit-Theme.
- PDF-Viewer im Browser: Seite und scharfer Zoom-Ausschnitt werden auf dem Server gerendert (PyMuPDF), eine Internetverbindung oder CDN ist nicht nötig. Fundstellen-Navigation (Klick, F3 / Umschalt+F3), nummerierte Rahmen, doppelte Tags gelb, Drehen, Seitenwechsel, gedrehte Plots.
- Einlesen aus den Quellordnern des Server-PCs (`config\paths.json`, `--source`, auch UNC) oder per Upload/Drag & Drop. Die Rohrleitungsnummern lassen sich zuschalten.
- Redline-PDF und Review-Excel der gewählten PDF (es gilt der Tabellenfilter), Review Auswahl/Bulk als ZIP, Export Excel/CSV. Alles kommt als Download, die Original-PDFs werden nur gelesen.
- Jeder Browser hat eine eigene Sitzung. Der Browser kann keine Serverpfade angeben. PyMuPDF-Zugriffe sind serialisiert.
- **Launcher:** neue Karte „Web server“ (Port, im Netzwerk erreichbar, Start / Stop / Open in browser, Adressen im Log). Neue Datei `start_web_server.bat`; sie wird bei der portablen Kopie mitgenommen.
- Tests: `tests\test_web.py` mit 7 Tests: API, Sitzungstrennung, Pfadschutz, Upload-Prüfung, gedrehter Plot, Downloads, Abgleich mit `read_pdf`.
- Noch nicht im Web: Review-Spalten bearbeiten, gespeicherte Tabellenansichten, 2. Monitor, Einstellungen und Sprachwahl im Browser.

## 1.0.6 – 2026-11-20
- **Rohrleitungsnummern optional in der Tag-Liste:** Menüband „1 Einlesen“ → „Rohrleitungen“ → „Rohrleitungsnummern mit einlesen“. Die Wahl wird je Benutzer gemerkt (`config\state.json`); beim Umschalten werden die geladenen PDFs neu eingelesen. Standard: aus.
- Neuer Typ **„Rohrleitung“**, z. B. `TFHR_SS01_001_1"`, `PFC_ST10_015_1/2"`, `203_17_112PFC_ST10_013_1"`, `151_HOS_206_1"`. Erkannt werden **waagerechte und senkrechte** Beschriftungen (auch in gedrehten Plots). Zerfällt ein Label in mehrere Wörter, wird es wieder zusammengesetzt: `TFHR_SS01_004_1` + `1/2"` → `TFHR_SS01_004_1 1/2"`, `201_07_092PS_ST03` + `_205_1` → `201_07_092PS_ST03_205_1`.
- Platzhalter ohne Nummer (`AV_TL02_XXX_2"`) werden nicht übernommen. Muster `pipe_line` in `tag_patterns.json` anpassbar.
- Rohrleitungen laufen wie alle Tags durch Tabelle, Filter, Fundstellen-Navigation, Redline, Review-Excel und Export. Eine Leitung, die auf einer Seite mehrfach beschriftet ist, zählt wie bisher als doppelt (gelb).
- Beispielordner (201 PDFs): 5740 Rohrleitungs-Einträge, EQPM-001: 81.

## 1.0.5 – 2026-11-20
- **Sprachen Deutsch / English / Français:** Globus-Button „Sprache“ im Menüband (Gruppe Hilfe) mit Auswahlmenü. Der Wechsel wirkt sofort auf alle offenen Fenster: Menüband, Leisten, Tabellenköpfe, Filter-Tooltips, Zähler, Blattkopf, Seitenanzeige und Dialoge. Die Wahl wird je Benutzer gemerkt (`config\state.json`).
- Übersetzungsmodul aus P3D XCHANGE 0.5.0 übernommen (`i18n.py`, unverändert). Katalog `src\p3d_pdfreader\assets\i18n\catalog.json` mit 160 Einträgen, erzeugt mit `tools\make_i18n_catalog.py`; fehlende Texte bleiben deutsch.
- Nicht übersetzt: Tabellendaten (z. B. Typ „Armatur“, Review-Auswahlwerte), Meldungsfenster mit wechselndem Inhalt, Hinweis-Text in der PDF-Vorschau sowie die englischen Texte des GUI-Kits (Save/Load/Reset Layout).

## 1.0.4 – 2026-11-20
- **Launcher wie P3D InstrumentationList** (nur Namen und Pfade angepasst): zwei Python-Zeilen, **Development** (Tools_Central) und **Company PC** (Standard `C:\Program Files\Python314\python.exe`). Der Firmen-PC-Pfad wird in `Launcher\python_company.txt` gespeichert. Ist das Entwicklungs-Python auf dem PC nicht vorhanden, nehmen Launcher und Jobs den Firmen-PC-Pfad.
- **Portable Kopie („Copy project here …“)** schreibt den eingetragenen Firmen-PC-Pfad immer nach `Launcher\python_company.txt` im Ziel. Mitkopiert werden nur Programmdateien (src, main_gui_kit, Launcher, start_pdf_reader.bat, requirements.txt, README.md, VERSION) und INSTALL.txt; Daten, Reviews und Tests nicht.
- **`start_pdf_reader.bat` und `Launcher\START_LAUNCHER.bat`:** Reihenfolge `P3D_PDFREADER_PYTHON` → Tools_Central → `python_company.txt` → Python 3.14. Damit startet die Kopie auf dem Firmen-PC ohne Anpassung.
- Umgebungsprüfung im Launcher prüft jetzt auch PyMuPDF.

## 1.0.3 – 2026-11-20
- **Original-PDFs schreibgeschützt:** Das Tool liest PDFs nur. Eingelesene PDFs sind als Ausgabeziel gesperrt; der Speicherdialog weist das mit einer Meldung ab.
- **Ausgaben immer mit Zeitstempel** (Redline-PDF, Excel, CSV, Tabellen-Export, Review-Excel): Fehlt der Zeitstempel im gewählten Namen, wird er ergänzt. Vorhandene Dateien werden nie überschrieben (dann Zähler `_2`, `_3`). Zeitstempel jetzt sekundengenau (`JJJJ-MM-TT_hh-mm-ss`).
- **Review speichern legt jedes Mal einen neuen Stand an:** `data\reviews\<PDF>_<Hash>\<PDF>_Review_<Zeitstempel>.json`. Der Verlauf bleibt erhalten, geladen wird der neueste Stand. Ältere Einzeldateien werden weiter gelesen.
- Rückfrage bei ungespeicherten Review-Einträgen auf Deutsch (Speichern / Verwerfen / Abbrechen), mit dem Hinweis, dass die PDF nicht verändert wird. Qt-Standarddialoge (Ja/Nein, Dateidialog) jetzt auf Deutsch.

## 1.0.2 – 2026-11-20
- **Fehler behoben, mehrseitige PDFs:** Die Anzahl wurde über alle Seiten summiert. 28 der 201 Plots haben mehrere Seiten, oft dieselbe Zeichnung noch einmal mit Markup-Kommentaren (z. B. EQPM-003). Deshalb galten fast alle Tags als doppelt (EQPM-003: 162 von 171). Jetzt wird je Seite gezählt: Doppelt ist ein Tag nur, wenn er auf **einer** Seite mehrfach steht (EQPM-003: 18, z. B. Equipment, das zusätzlich in der Equipment-Tabelle am Blattfuß steht).
- Deckungsgleicher Text (im Plot doppelt übereinander gezeichnet) zählt nur einmal.
- Neue Spalte **Seiten** in der Tag-Tabelle und im Export, z. B. „1, 2 (2×)“.
- **PDF-Viewer mit Seitenumschaltung** (◀ Seite n / m ▶). Die Fundstellen-Navigation (Klick, F3) springt über alle Seiten, der Hinweis nennt die Seite. Gelbe Markierung je Seite.
- **Redline** kommentiert Fundstellen auf allen Seiten. **Review-Excel** mit Spalten „Seite“ und „Anzahl auf Seite“.
- **Absturz behoben** beim Einschalten von „Bearbeiten“ (Modell-Signal an den Filter, trat sporadisch auf).

## 1.0.1 – 2026-11-20
- Hauptfenster im Aufbau von P3D XCHANGE: Kopfband, Menüband (ribbon), Blätter als Reiter, Blattkopf mit Band, dunkelblauer Tabellenkopf, Fortschrittsdialog mit Abbrechen. ribbon, sheet, progress und icons sind aus XCHANGE 0.5.0 übernommen.
- Vorschau: Der sichtbare Ausschnitt wird bei jedem Zoom scharf aus dem Vektor-PDF neu gerendert. Ein gewählter Tag (Klick oder Pfeiltasten) wird automatisch markiert und gezoomt.
- Doppelte Tags (Anzahl > 1): Die Tabellenzeile ist gelb hinterlegt, in der PDF sind alle Fundstellen gelb hinterlegt.
- Export-Symbol in der Tabellenecke ist jetzt das Excel-Symbol. Der Dateiname wird vorbelegt mit PDF-Name bzw. Tabellenname plus Zeitstempel.
- **Gedrehte Plots (/Rotate 270, 29 von 201 Beispielen):** Wortpositionen werden in die sichtbare Lage umgerechnet. Damit passen Blasen-Paarung, Schriftfeld, Markierungen und Redline. Vorher fehlten dort zum Teil Schriftfeld und Instrumente.
- **Mehrfach-Tags:** Die erste Auswahl zeigt die ganze Seite mit nummerierten Fundstellen. Jeder weitere Klick auf denselben Tag (oder F3, Umschalt+F3) springt zur nächsten bzw. vorherigen, danach kommt wieder die Übersicht. Oben in der Vorschau steht ein Hinweis „Fundstelle n / m“.
- **Redline-PDF:** Kopie der PDF mit Kommentaren. Jede Fundstelle hat einen Rahmen mit Pos.-Nr. (rot, doppelte Tags orange), dazu ein Übersichtskommentar. Der Tabellenfilter gilt.
- **Review-Excel:** eine Zeile je Fundstelle mit Pos.-Nr. (wie im Redline), Review-Kommentar, Prüfstatus (Auswahlliste), Bemerkung, Geprüft von/am. Doppelte Tags sind gelb.
- **Review / Audit einzeln oder im Bulk:** markierte oder alle PDFs; Redline je PDF, Review-Excel je PDF und gesamt in einen Unterordner „Review_<Zeitstempel>“.
- **Menüband nach Arbeitsschritten** (1 Einlesen, 2 Prüfen, 3 Review/Redline, 4 Export, Ansicht, Einstellungen, Hilfe), jede Funktion mit Icon. Über Dateien, Tags und PDF-Viewer gibt es Leisten mit Tab-Buttons für die direkten Funktionen.
- **PDF-Viewer:** wahlweise in eigenem Fenster auf dem 2. Monitor (wird gemerkt), Ansicht drehen, Zoom-Buttons, „Öffnen“ im Standardprogramm.
- **Bearbeiten-Modus der Tag-Tabelle:** Spalten Review (Auswahlliste), Änderung (Auswahlliste, frei ergänzbar), Neuer Wert, Bemerkung, WPO. Bei jeder Änderung werden **Datum** und **User** automatisch in die letzten zwei Spalten eingetragen. Speichern je PDF (Strg+S) nach `data\reviews\`; beim PDF-Wechsel, neuen Scan oder Schließen wird bei offenen Änderungen nachgefragt.
- **Excel-Ausgaben als Excel-Datentabelle** (Formatvorlage, Filterknöpfe, gebänderte Zeilen) mit automatischer Spaltenbreite: Tabellen-Export, Export Excel und Review-Excel. Review-Excel und Export enthalten die gespeicherten Review-Spalten.
- **Redline / Review-Excel bei aktivem Tabellenfilter:** Das Tool fragt nach, ob nur die gefilterten oder alle Tags ausgegeben werden sollen (Standard: alle). Bisher wurde stillschweigend nur der Filter verwendet, z. B. „Nur doppelte“, und einfache Tags fehlten im Redline. Die Review-Excel speichert offene Review-Einträge vorher.
- **Subtabs:** Rechtsklick auf die Subtab-Leiste → „Subtabs aus (zurück zur Gesamttabelle)“.
- **Senkrechte Tags** (z. B. VH203, SGL010) werden erkannt und im Redline richtig umrahmt (Test ergänzt).
- **Instrumente:** Kürzel brauchen mindestens 2 Buchstaben. Das entfernt 21 Fehlgriffe aus Revisionsdreiecken und Stutzen (z. B. „B-011“). Ein alter Standardwert in `tag_patterns.json` wird automatisch ersetzt, eigene Ausschlüsse ergänzen die Standardliste.
- Launcher 1:1 aus XCHANGE übernommen (Start, Prüfen, Build, Ordner, Portable-Kopie, Hotspot), dazu build_exe.bat, run_p3d_pdfreader.py, `--version` und test_architecture.

## 0.1.0 – 2026-11-20
- Erste Fassung: Scan von Plant-3D-PDF-Plots (PyMuPDF). Erkennt Instrumente, Equipment, Armaturen, Volltags und Zeichnungsverweise.
- Schriftfeld: Drawn, Checked, Datum, Zeichnungsnr. und letzte Revision, dazu der Plot-Benutzer.
- GUI (PySide6, main_gui_kit): Dateien, Tags je PDF, alle Tags, Seitenvorschau mit Markierung der Fundstelle, Tabellen-Vorschau.
- Tabellen: Filter, Sortierung, Zoom, gemerkte und benannte Ansichten, Export-Symbol in der Tabellenecke.
- Pfadverwaltung (Quellordner, Exportordner, Speicherorte) und Launcher.
- Export als Excel (Blätter Dateien und Tags) und CSV.
