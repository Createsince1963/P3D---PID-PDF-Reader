# Changelog

## 1.0.33 – 2026-11-22
- **Kachel-Editor komplett deutsch:** Kacheln, Bereichs-Überschriften, Kachelmenü, Seitenleiste (Aktive Kachel, Schritte), alle Dialoge (Teilen, Ersetzen, Typ ändern, Wenn-dann, Liste prüfen, Aus Liste, Gruppieren, Index-, Ja/Nein-Spalte, Leere füllen, Spalten hinzufügen), Typnamen (Ganzzahl, Dezimalzahl, Datum …), Meldungen und Verlaufstexte.
- Neu: `tools	ranslate_column_editor.py` – übersetzt die Kopie `column_editor` per Wörterbuch (nur Anzeigetexte; interne Schlüssel bleiben) und baut `qml_resources.py` neu. Wiederholbar; nach einer neuen Kopie aus Tag Compliance erneut ausführen, das Werkzeug meldet nicht mehr gefundene Texte. `QUELLE.md` beschreibt den Ablauf.
- Neue Prüfspalten schreiben „NICHT IN LISTE“ (bisher „NOT IN LIST“); gespeicherte Anpassungen behalten ihren Text.
- Handbuch-Hinweis auf englische Texte entfernt; Hilfebilder neu erzeugt.

## 1.0.32 – 2026-11-22
- **Kachel-Editor aus P3D Tag Compliance übernommen – als Vollfenster** (Datenlink › Excel-Liste importieren / Importtabelle bearbeiten). Die importierte Excel-Liste wird hier zu einer für den P3D PDF Reader kompatiblen Importliste angepasst. Die drei Bereiche wie in Tag Compliance:
  1. **Kachel-Editor** mit Menüband Start / Umwandeln / Spalte hinzufügen (Rückgängig, Export ja/nein, Gruppen, Ersetzen, Teilen, Extrahieren, Füllen, Wenn-dann-, Ja/Nein-, Index-Spalte, Spalten aus einer anderen Liste …) und den Kachel-Bereichen „Nicht exportiert“, „Ausgeblendet“, „Umbenannt“.
  2. **Seitenleiste** rechts als Dock über die volle Höhe: aktive Kachel, Gruppe, Verlauf; einklappbar, lösbar (Zustand in `config\state.json`, `tile_deck`).
  3. **Datentabelle** unten in Kachel-Reihenfolge; Rechtsklick auf den Kopf = Datenlink 1/2 (dunkelgrün), Klick wählt die Kachel, Zellen der Originalspalten bearbeitbar.
- **Ladebildschirm** wie in Tag Compliance („Kachel-Editor wird geladen …“, Zahnrad, Schritt, Prozent) beim Öffnen und bei „Andere Excel-Liste …“; Farben aus `design`/`appearance`.
- **Anpassung bleibt erhalten:** `config\data_link.json` speichert jetzt Originalliste (`raw_headers`/`raw_rows`), Anpassung (`tile_config`) und Ergebnis; beim erneuten Öffnen werden alle Schritte wieder angewendet. Ältere Dateien werden weiter gelesen (ausgeblendete Spalten = „Nicht exportiert“).
- Neu: **Anpassung speichern / laden …** (JSON, für die nächste Version der Liste), **Als Excel speichern …** (angepasste Liste, nur exportierte Spalten – wieder mit „Liste importieren“ lesbar; `core.data_link.write_excel`).
- Eigenständiges Modul: `src\p3d_pdfreader\column_editor\` = unveränderte Kopie aus Tag Compliance 0.9.416 (Modul 0.1.0, siehe `QUELLE.md`, nicht ändern); PDF-Reader-Teil in `gui	ile_editor\` (Fenster, Ladebildschirm, Seitenleiste, Datenquelle, deutsches Menüband). Der bisherige Import-Dialog entfällt.
- Bekannt: Texte in den QML-Kacheln und der Seitenleiste sind englisch (Kopie unverändert); das Menüband ist deutsch.
- EXE-Build: QtQuick/QtQml werden nicht mehr ausgeschlossen (für den Kachel-Editor nötig), QtQuickWidgets/QtQuickControls2 und die QML-Ressourcen als Hidden Imports.
- Handbuch (Kapitel Datenlink), Hilfebild-Werkzeug `tools\make_help_workflow.py` (Schritt 3 zeigt das Vollfenster; wegen der QML-Schrift mit `QT_QPA_PLATFORM=windows` ausführen) und Tests angepasst; Hilfebilder neu erzeugt.

## 1.0.31 – 2026-11-22
- **Handbuch: neues Kapitel „Workflow Schritt für Schritt“** – der ganze Ablauf mit echten Bildern der Oberfläche: Überblick, 1 Projekt einrichten, 2 PDFs einlesen, 3 Excel-Liste importieren (Datenlink), 4 Datenlink-Feld setzen, 5 Ansehen und prüfen, 6 Review/Redline, 7 Exportieren. Jedes Bedienelement trägt im Bild eine Nummer (1, 2, 3 …) mit Erklärung darunter; Klick auf Nummer oder Erklärung rahmt das Element ein, Klick ins Bild vergrößert. 12 Bilder, 78 Markierungen.
  - Erzeugt von `tools\make_help_workflow.py` aus der laufenden App mit Beispiel-PDFs (Lage der Nummern aus den Widgets berechnet; nach GUI-Änderungen neu ausführen). Ausgabe: `assets\help\img\wf_*.png` und `assets\help\workflow.js`.
  - Schnellstart verweist auf das neue Kapitel; Farben nur aus den vorhandenen Handbuch-Variablen.
- **Fehler behoben:** Bei einigen Knöpfen stand der Erklärungstext auf dem Knopf statt im Tooltip – `action_button` des Kits nimmt als dritten Parameter ein Symbol. Betroffen: Kachel-Editor (Projektdefinitionen und Datenlink: „+ Spalte“, „Alle einblenden“, „Kachel-Editor“), Datenlink-Dialog („Andere Excel-Liste …“, „Übernehmen und verlinken“). Neu: `controls.tip_button`.
- Datenlink-Kennzeichnung „» Datenlink 1/2“ statt eines Zeichens, das in der Standardschrift fehlte.
- `.claude\launch.json`: Vorschau „help-static“ (Handbuch über http://localhost:8791).

## 1.0.30 – 2026-11-22
- **Neu: Datenlink – Excel-Liste importieren** (Menüband „1 Einlesen“ › **Liste importieren**): z. B. die Instrumenten-Gesamtliste aus P3D InstrumentationList (Blatt „Gesamtliste“ wird vorgeschlagen). Die Excel-Datei wird nur gelesen.
  - **Vorschau mit Kachel-Editor** (`gui\data_link_ui.py`, nutzt `ColumnTiles`): Spalten verschieben, ein-/ausblenden (= übergeben oder nicht), umbenennen, einfügen, löschen, sortieren; Zellen bearbeiten. Schnelles Tabellenmodell – auch die Gesamtliste mit ~1450 Zeilen × 346 Spalten öffnet in unter einer Sekunde.
  - **Datenlink 1** (zu Tabelle 1 – Dateien) und **Datenlink 2** (zu Tabelle 2 – Tags) per Rechtsklick auf Spaltenkopf/Kachel oder Auswahlfeld; Vorschlag „P&ID No.“/„DWG Number“ und „Tag“. „Übernehmen und verlinken“ speichert nach `config\data_link.json`.
  - **Datenlink-Feld je Tool-Tabelle** per Rechtsklick auf den Spaltenkopf („… als Datenlink-Feld setzen“ / „entfernen“); der Kopf wird **dunkelgrün** (`appearance.ACCENT_CHOICES[1]`, passend zum dunkelblauen Kopf). Gemerkt in `config\state.json` (`data_link_fields`).
  - Sobald beide Seiten gesetzt sind: Dateien bekommt „Datenlink-Treffer“, die Tag-Tabelle „Datenlink-Treffer“ plus alle übergebenen Listenspalten (auch im Tabellen-Excel).
  - Abgleich (`core\data_link.py`, ohne Qt): ohne Groß-/Kleinschreibung; ohne exakten Treffer zählt die Endung ab einem Bindestrich („301-30-149-TI-300“ ↔ „TI-300“); mit beiden Datenlinks nur Listenzeilen derselben Zeichnung.
- Handbuch: neues Kapitel „Datenlink (Excel-Liste)“, Menüband-Eintrag und Rechtsklick-Übersicht ergänzt; Hilfebilder neu erzeugt.
- Tests: `tests\test_data_link.py` (Einlesen, Abgleich, Speichern, Import-Dialog, Datenlink-Felder im Hauptfenster).

## 1.0.29 – 2026-11-22
- **Menüband, Standardansicht:** ohne gemerkten Zustand ist nur die Gruppe **Projekt** aufgeklappt, alle anderen sind eingeklappt.
- **Beim Start** stehen die eingeklappten Überschriften **in einer Reihe** nebeneinander; nach dem ersten Ein- oder Aufklappen wird wieder gestapelt (4 je Spalte).

## 1.0.28 – 2026-11-22
- **Menüband-Stapel:** jetzt **4** eingeklappte Gruppen-Überschriften je Spalte (vorher 3), danach neue Spalte. Text der gestapelten Überschriften **linksbündig**; Höhe so bemessen, dass das Menüband nicht höher wird.

## 1.0.27 – 2026-11-22
- **Menüband-Gruppen einklappbar:** Klick auf die dunkelblaue Überschrift einer Gruppe klappt sie ein. Ihre Überschrift steht dann rechts hinter den sichtbaren Gruppen im Stapel – 3 untereinander, danach beginnt eine neue Spalte. Klick auf die gestapelte Überschrift klappt die Gruppe an ihrer ursprünglichen Stelle wieder auf (neu: `gui\ribbon_fold.py`, `ribbon.py` unverändert).
- Der Zustand wird in `config\state.json` (`ribbon_collapsed`) gemerkt und beim nächsten Start wiederhergestellt.
- Handbuch (Kapitel Menüband) ergänzt; Tests für Stapel, Aufklappen und Wiederherstellen.

## 1.0.26 – 2026-11-22
- **Viewer auf dem 2. Monitor:** die Tag-Tabelle nutzt jetzt die ganze Breite (kein leerer Platzhalter mehr rechts). Hinweis und Knopf **„Viewer zurückholen“** stehen oberhalb der Tag-Tabelle rechts in der Kopfzeile.
- **Viewer zurückholen** teilt den Bereich wieder im Standardverhältnis (Tag-Tabelle : Viewer = 5 : 8).
- Test: Zwei-Monitor-Umschalter und neue Knöpfe der Tag-Leiste.

## 1.0.25 – 2026-11-22
- **Fortschrittsfenster beim Laden** (Fenster wie in P3D XCHANGE, `gui\progress.py`): nach dem Scan „Tabellen werden geladen“ (Dateiliste/Alle Tags, Tag-Tabelle, PDF in drei Schritten); bei Wahl einer anderen PDF „PDF wird geladen“ (Tag-Tabelle lesen, PDF öffnen und anzeigen).
- **Tabellenanpassungen werden als Standard gemerkt:** neben Breite, Reihenfolge, Sortierung, Filter und Zoom jetzt auch Ein-/Ausblenden über den Spalten-Dialog (Rechtsklick › Spalten …) – gespeichert in `config\table_views.json` und beim nächsten Start bzw. jeder neuen PDF wieder angewendet.

## 1.0.24 – 2026-11-22
- **Tag-Tabelle, neue Knöpfe vor „Bearbeiten“:**
  - **Aus PDF-Scan übernehmen** (Umschalter, gemerkt in `config\state.json`): Ersteller, Checked, Rev, Rev-Datum und Rev-Text aus dem Schriftfeld der PDF als Spalten hinten an die Tag-Tabelle (auch im Tabellen-Excel).
  - **Autofill OK:** bei allen Tags mit Review „OK“ oder leerem Review und Projekt-Prüfung „OK“: Review = OK, User und Datum (heute, ohne Uhrzeit); leeres WPO bekommt den Checked-Wert aus dem Schriftfeld. Danach Speichern (`ReviewStore.autofill_ok`, ohne Qt).
- **Review-Excel:** Spalten X und Y entfernt; Spaltenbreite (autofit) rechnet fetten Kopf und Filterknopf mit ein, damit Überschriften nicht abgeschnitten werden.
- Tag-Tabelle: Änderungen nach „Nur doppelte“/Filterwechsel aktivieren „Speichern“ wieder zuverlässig.

## 1.0.23 – 2026-11-22
- **EXE-Build repariert:** `build_exe.bat` übernahm die Variable `PY` aus `START_LAUNCHER.bat` und baute deshalb mit dem zentralen Python statt in `.venv_build`; PyInstaller brach wegen PyQt5 neben PySide6 ab. Ein anderes Build-Python wird jetzt nur noch über `BUILD_PY` erzwungen.
- Zusätzlich werden PyQt5, PyQt6 und PySide2 beim Build immer ausgeschlossen.

## 1.0.22 – 2026-11-22
- **Menüband, Gruppe Projekt:** „Projektmodus“ und „Rohrleitungen“ stehen jetzt direkt hinter „Projekt wählen“ (1. Projektmodus, 2. Rohrleitungen). „Rohrleitungen“ ist ein Umschalter wie der Projektmodus: „Rohrleitungen: an/aus“, Symbol grün solange an; das Untermenü „Rohrleitungsnummern mit einlesen“ entfällt. Gemerkt wie bisher, Umschalten liest geladene PDFs neu ein.
- Handbuch, README und Übersetzungen angepasst; Test auf den Umschalter umgestellt.

## 1.0.21 – 2026-11-22
- **Handbuch: neues Kapitel „Ablauf & Bausteine“** mit einem klickbaren Ablaufdiagramm (Eingaben → Kern mit den Schritten 1–5 und Review-Speicher → Oberflächen Desktop-App, Web-Server, Offline-Bericht → Ergebnisse). Klick auf einen Baustein erklärt ihn; die Handbuchsuche findet auch die Erklärungen. Farben nur aus den vorhandenen Handbuch-Variablen.

## 1.0.20 – 2026-11-22
- **Review-Layer im Redline-PDF:** Rahmen, Pos.-Nr. und Kommentare liegen auf einer eigenen PDF-Ebene `Review_TT.MM.JJJJ` (Erstellungsdatum), in Acrobat, PDF-XChange und Bluebeam unter „Ebenen“ ein- und ausblendbar. Die Ebenen des Plots bleiben erhalten.
  - Neu im Menüband, Gruppe Projekt: **Einstellungen › Layer für Review im PDF** (Häkchen, Standard an, gemerkt in `config\state.json`).
  - Gilt für Redline der gewählten PDF, Review Auswahl/Bulk, Web-Server und Offline-Bericht (`redline.review_layer_enabled()`, ohne Qt).
  - Übersichtskommentar nennt die Ebene.
- Tests: Review-Layer an/aus, Menüpunkt im Menüband.

## 1.0.19 – 2026-11-22
- **Redline-PDF mit den Farben und Rahmen des Viewers:** korrekte Tags grün, fehlerhafte rot (Review „Korrektur erforderlich“, im Projektmodus Abweichung ohne angenommenen Review), doppelte Tags zusätzlich gelb hinterlegt (Multiplizieren, Plotlinien bleiben sichtbar). Rahmenabstand 3 pt, Linienbreite 1,5 wie im Viewer; Pos.-Nr. in Rahmenfarbe.
  - Farben aus `main_gui_kit.theme` (ok/err) und `DEFAULT_DIRTY`; Regel „fehlerhaft“ zentral in `review_store.is_faulty` (Viewer und Redline gleich).
  - Desktop: Redline der gewählten PDF nutzt auch noch nicht gespeicherte Review-Einträge; Bulk und Web nutzen den gespeicherten Stand.
  - Kommentar zeigt „Status: fehlerhaft“, Übersichtskommentar zählt fehlerhafte Tags. Bisher: rot/orange.
- Test: Redline-Farben wie im Viewer.

## 1.0.18 – 2026-11-21
- Neu: `HANDOFF.md` als Einstieg für neue Entwickler (Struktur, Start, Tests, Regeln, offene Punkte).

## 1.0.17 – 2026-11-21
- Launcher: Karten „Build“ und „Folders“ sind wie „Quality gate“ einklappbar und starten eingeklappt.

## 1.0.16 – 2026-11-21
- **Variante 1 „nur HTML“ als Offline-HTML-Bericht** (`web\report.py`): eine einzelne HTML-Datei ohne Server und ohne Internet.
  - Inhalt: Oberfläche der Web-Version, Scan-Daten und ein JPEG je Seite (3000 px). Tabellen, Filter, Fundstellen-Navigation und Viewer funktionieren darin.
  - Eingebettet zum Herunterladen: **Redline-PDF und Review-Excel je PDF**, Export Excel, Review-Excel gesamt. Alle werden mit `core` erzeugt und enthalten alle Tags.
  - Erstellen: App (Gruppe „Web“ › Offline-Bericht …), Web-Version (Gruppe „4 Export“), Launcher (Karte „Variant 1 · Offline HTML report“, ganzer Ordner) oder `python -m p3d_pdfreader --report --source <Ordner>`.
- **Audit-Spalten in Web-Version und Bericht:** Review, Änderung, Neuer Wert, Bemerkung, WPO sowie automatisch Datum und User.
  - Bearbeiten per Doppelklick, Auswahllisten aus `review_store`, Speichern mit „Review speichern“ oder Strg+S. „Korrektur erforderlich“ erscheint rot in Tabelle und Viewer.
  - Web: Gespeichert wird auf dem Server im selben Format wie die Desktop-App (neuer Stand in `data\reviews`, nur geänderte Felder, Einträge anderer Nutzer bleiben). Als User gilt der im Browser angegebene Name. Beim Wechsel der PDF wird automatisch gespeichert.
  - Bericht: Die Einträge bleiben im Browser. „Review speichern“ lädt eine CSV mit allen Tags herunter. Schon gespeicherte Reviews stehen beim Erstellen im Bericht.
- Tests: Audit speichern (Feldprüfung, unbekannte Tags, User, Review-Excel), Bericht vollständig inline, Kommandozeile. Der Web-Test-Server nutzt einen eigenen Datenordner.
- Hinweis SharePoint: HTML-Dateien öffnet SharePoint Online nicht als Webseite. Den Bericht herunterladen oder synchronisieren und lokal öffnen.

## 1.0.15 – 2026-11-21
- **Web-Version in der App:** neue Menüband-Gruppe **„Web“** (vor „Hilfe“) mit den Knöpfen „Web-Server“ (an/aus; an = grünes Symbol, Meldung mit den Adressen für die Kollegen) und „Im Browser öffnen“. Der Server läuft als eigener Prozess (`python -m p3d_pdfreader --web`, aus der EXE `<EXE> --web`), weil PyMuPDF nicht threadsicher ist. Ein schon laufender Server auf Port 8765 (Launcher, `start_web_server.bat`) wird genutzt statt ein zweiter gestartet. Beim Schließen der App wird nur ein selbst gestarteter Server beendet. Neues Modul `gui\web_control.py`.
- **Launcher:**
  - **Quality gate** einklappbar, beim Start eingeklappt (Pfeil im Kartentitel).
  - Neue Karte **„Variant 3 · Remote GUI“** (eingeklappt): Server-PC eintragen, Remotedesktop verbinden (`mstsc /v:`) oder `.rdp`-Datei für Kollegen speichern. Der Server-PC wird gemerkt.
  - Die Web-Karte heißt jetzt „Variant 2 · Web server“.
- Tests: Start/Stopp des Web-Servers über die App (`test_web.py`), Gruppenreihenfolge mit „Web“ (`test_ribbon_menus.py`).
- Variante 1 („nur HTML“, ohne Server) ist nicht umgesetzt.

## 1.0.14 – 2026-11-21
- **Menüband neu geordnet:** Projekt (jetzt mit den Einstellungen Pfade und Tag-Muster) → 1 Einlesen → **2 Ansicht** → 3 Prüfen → 4 Review / Redline → 5 Export → Hilfe. Die eigene Gruppe „Einstellungen“ entfällt; „Ansicht“ steht vor „Prüfen“, die Gruppen sind neu nummeriert (Übersetzungen EN/FR ergänzt).
- **Projektmodus an = grünes Symbol** (Kit-Farbe `ok`); aus = Standardsymbol.
- Handbuch (Menüband-Nachbau, Schnellstart, Hilfebilder neu erzeugt) und README angepasst.
- Tests: Gruppenreihenfolge, Knöpfe der Gruppe Projekt, Symbolfarbe beim Umschalten.

## 1.0.13 – 2026-11-21
- **Projektdefinitionen wie in P3D Tag Compliance** (Vorlage: Fenster „Project definitions“, `pidtag_gui.py` + `linetag_defs_tiles.py`; neues Modul `gui\project_tiles.py`):
  - **Rechtsklick in eine Zelle:** Zeile hinzufügen, Zeile(n) duplizieren/löschen, Nach Code A–Z sortieren, Kopieren, Einfügen, Inhalt löschen, Nur Zeilen mit „Wert“ zeigen, Filter zurücksetzen, Kachel-Editor ein/aus, Ansicht nach Excel …, Rückgängig/Wiederholen.
  - **Rechtsklick auf Zeilennummern (wie Excel):** Zeile(n) oberhalb/unterhalb einfügen, duplizieren, kopieren, ausschneiden, aus der Zwischenablage oberhalb/unterhalb einfügen, löschen, Inhalt löschen.
  - **Rechtsklick auf Spaltenkopf:** umbenennen, links/rechts einfügen, duplizieren, kopieren, ausschneiden, einfügen, löschen, Inhalt löschen, Zeilen auf-/absteigend sortieren, ausblenden, alle einblenden. Spaltenänderungen nur bei Listen; feste Tabellen behalten ihre Spalten.
  - **Kachel-Editor** (Knopf über der Tabelle, Zustand gemerkt): Spalten als Kacheln – ziehen = verschieben, Haken = sichtbar, Doppelklick = umbenennen, Rechtsklick = Spaltenmenü, „+ Spalte“, „Alle einblenden“. Bei Listen schreibt „Speichern“ neue Spaltenfolge und -namen zusammen mit den Zeilen (eine Transaktion, `ProjectDB.save(..., columns=)`).
  - **Kacheln links** per Drag & Drop umsortieren und umbenennen (Doppelklick, F2, Rechtsklick); Reihenfolge und Namen liegen in der Projekt-Datenbank.
  - **Ansicht nach Excel …**: sichtbare Spalten in angezeigter Reihenfolge, nur gefilterte Zeilen (gilt jetzt allgemein für `visible_table`).
  - Tastatur: Strg+Z/Strg+Y, Strg+C/Strg+V (tabulatorgetrennt wie Excel), Entf leert die markierten Zellen. Spaltenköpfe lassen sich ziehen.
  - Nicht übernommen: der QML-Kachel-Editor von Tag Compliance mit berechneten Spalten und Profilen.
- Tests: Speichern mit neuen Listenspalten, Menüs, Undo/Redo, Kachel-Editor, Kachelreihenfolge, Ansicht-Export.

## 1.0.12 – 2026-11-21
- **Tests:** pytest legt seine Temp-Dateien jetzt im Projektordner `.pytest_tmp\` an (`pytest.ini`, `--basetemp`; in `.gitignore`). Vorher brachen alle Tests mit `tmp_path` mit „Zugriff verweigert“ ab, wenn der Standardordner `%TEMP%\pytest-of-<Benutzer>` gesperrt war.

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
