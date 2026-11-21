# Changelog

## 1.0.8 – 2026-11-21
- **Monochrom-Ansicht im PDF-Viewer:** Button „Monochrom“ in der Viewer-Leiste (Desktop und Web). Die Seite wird wie ein Schwarz-Weiß-Plot gezeigt: Weiß bleibt weiß, jede kräftige Farbe (auch Gelb, Cyan) wird schwarz, Pastelltöne grau, Kantenglättung bleibt. Zoom, Drehung und Markierungen bleiben beim Umschalten erhalten; die Wahl wird gemerkt (Desktop `config\state.json`, Web im Browser). Nur Ansicht – die PDF wird nicht verändert.
- Neues Kernmodul `coreender.py` (ohne Qt, ohne numpy), genutzt von Desktop-Vorschau und Web-Server (`/render?...&mono=1`). Monochrom kostet beim Grundbild ca. 0,7 s zusätzlich je Seite.
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
