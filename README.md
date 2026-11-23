# P3D PDF Reader

Liest PDF-Plots von P&IDs aus AutoCAD Plant 3D und listet alle PID-Tags je PDF. Zu jeder PDF zeigt das Tool Erstellungsdatum, Ersteller und Schriftfeld. Doppelte Tags werden erkannt, und man kann sie in der PDF-Vorschau einzeln anspringen. Review-Einträge (OK, Korrektur erforderlich …) trägt man direkt in der Tag-Tabelle ein. Für den Review erzeugt das Tool Redline-PDFs mit Kommentaren und Review-Excel-Tabellen mit Positionsnummern, für eine einzelne PDF oder im Bulk.

Zusätzlich prüft das Tool Tags gegen Projektdefinitionen (Projektmodus, wie P3D Tag Compliance) und gleicht sie mit einer importierten Excel-Liste ab, z. B. der Instrumenten-Gesamtliste (Datenlink).

Der Aufbau (Menüband, Blätter, Tabellen, Launcher) entspricht P3D XCHANGE. Aktuelle Version: siehe `VERSION`, Änderungen: `CHANGELOG.md`, Einstieg für Entwickler: `HANDOFF.md`.

## Start
- **Launcher:** `Launcher\START_LAUNCHER.bat`, wie bei P3D InstrumentationList. Python für den Entwicklungs-PC (Tools_Central) und den Firmen-PC. Der Firmen-PC-Pfad wird in `Launcher\python_company.txt` gespeichert und bei der portablen Kopie mitgenommen. Funktionen:
  - App oder EXE starten
  - Quality gate: Umgebung prüfen, `--version`, Architekturtest, Tests
  - EXE bauen
  - Ordner öffnen
  - Portable Kopie (USB, Firmen-Laptop)
  - Hotspot
  - **Web-Server** (Browser-Zugriff im Firmennetz, siehe unten)
- **Direkt:** `start_pdf_reader.bat` startet die App mit dem zentralen Python `Tools_Central\Python\python\python.exe`. Ein anderes Python lässt sich über die Umgebungsvariable `P3D_PDFREADER_PYTHON` setzen.
- **EXE:** `build_exe.bat` baut eine einzelne EXE, `build_exe.bat onedir` einen Ordner. Ergebnis in `build_exe\dist\`.

## Offline-HTML-Bericht (Variante 1, ohne Server)
Eine einzelne HTML-Datei zum Weitergeben per Mail, Freigabe oder SharePoint. Sie läuft im Browser (Edge, Chrome) ohne Server, ohne Internet und ohne Python. Die PDFs braucht sie nicht, die Datei kann also in **jedem** Ordner liegen.
- **Erstellen:**
  - App, Gruppe „Web“ › **Offline-Bericht …**: markierte PDFs, sonst alle
  - Web-Version, Gruppe „4 Export“ › **Offline-Bericht**
  - Launcher, Karte „Variant 1 · Offline HTML report“: ganzer Ordner, Ergebnis in `data\exports`
  - Kommandozeile: `python -m p3d_pdfreader --report --source <Ordner> [--out Datei.html] [--no-redline] [--max-px 3000]`
- **Inhalt:** Tabellen, Filter, Nur doppelte, Fundstellen-Navigation, Viewer mit Zoom bis zur Bildauflösung (3000 px), Drehen, Seiten und Schwarz-Weiß.
- **Eingebettete Dateien (Download per Klick):**
  - **Redline-PDF** und **Review-Excel** je PDF
  - **Export Excel** und **Review-Excel gesamt**
  - Sie werden beim Erstellen erzeugt und enthalten alle Tags. Ein Filter im Bericht wirkt auf sie nicht.
- **Audit im Bericht:** Die Audit-Spalten lassen sich wie in der Web-Version ausfüllen. Die Einträge bleiben im Browser des Nutzers. „Review speichern“ speichert sie als **CSV** (öffnet in Excel) mit allen Tags aller PDFs.
- **Größe:** ca. 0,7 MB je Seite, mit Redline zusätzlich etwa die Größe der PDFs. Bei vielen PDFs besser nur die benötigten markieren.
- **SharePoint:** SharePoint Online zeigt HTML-Dateien aus Sicherheitsgründen nicht als Webseite an, sondern lädt sie herunter oder zeigt den Quelltext. Den Bericht deshalb herunterladen bzw. über OneDrive synchronisieren und lokal im Browser öffnen, dann funktioniert alles.

## Fernzugriff auf die Desktop-App (Variante 3, Remotedesktop)
Launcher, Karte „Variant 3 · Remote GUI“ (eingeklappt): Server-PC eintragen, dann „Connect (Remote Desktop)“ (`mstsc /v:<PC>`) oder „Save .rdp file …“ für Kollegen. Auf dem Server-PC muss Remotedesktop eingeschaltet sein. Windows Pro erlaubt nur einen Benutzer gleichzeitig; für mehrere gleichzeitig braucht es einen Windows-Server mit Remotedesktopdiensten (IT).

## Web-Version (Browser, Firmennetz)
Ein PC oder Server startet den Web-Server, Kollegen öffnen die Adresse im Browser (Edge, Chrome). Sie brauchen weder Python noch die EXE. Erkennung, Redline, Review-Excel und Export laufen auf dem Server über denselben `core\` wie die Desktop-App. Die Ergebnisse sind deshalb identisch.
- **Start:**
  - **In der App:** Menüband-Gruppe „Web“, Knopf „Web-Server“ (an = grünes Symbol, zeigt die Adressen für die Kollegen) und „Im Browser öffnen“. Der Server läuft als eigener Prozess, bis er ausgeschaltet oder die App geschlossen wird. Läuft schon ein Server auf Port 8765 (z. B. aus dem Launcher), nutzt die App diesen.
  - Launcher, Karte „Variant 2 · Web server“: Port (Standard 8765), „Reachable in the network“, Start / Stop / Open in browser. Die Adressen für die Kollegen stehen im Log, z. B. `http://<Rechnername>:8765/`.
  - Alternativ `start_web_server.bat` (ohne Argumente im Netzwerk erreichbar, Port 8765) oder `python -m p3d_pdfreader.web --host 0.0.0.0 --port 8765 [--source "\\server\freigabe\PID Plots"]`.
  - Beim ersten Start fragt Windows eventuell nach einer Firewall-Freigabe für Python.
- **PDFs einlesen:**
  - „Quellordner scannen“ (F5) liest die Quellordner des **Server-PCs**: `config\paths.json`, im Desktop-Tool unter Projekt › Pfade, plus `--source`. UNC-Freigaben sind möglich.
  - „PDFs hochladen“ oder PDFs ins Browserfenster ziehen liest Dateien vom PC des Kollegen.
  - „Rohrleitungen“ schaltet das Einlesen der Rohrleitungsnummern ein.
- **Funktionen wie in der Desktop-App:**
  - Blätter „PID-Tags“ und „Alle Tags“, Spaltenfilter, Filter über das ganze Blatt, Sortierung, Mehrfachauswahl, Nur doppelte
  - Fundstellen-Navigation: Klick, F3 / Umschalt+F3, nummerierte Rahmen
  - Viewer: Mausrad, Ziehen, Doppelklick, Drehen, Seiten. Der Ausschnitt wird bei jedem Zoom scharf vom Server gerendert.
  - Redline-PDF und Review-Excel der gewählten PDF (es gilt der Tabellenfilter), Review Auswahl/Bulk als ZIP, Export Excel und CSV
- **Ausgaben** kommen als Download in den Browser. Auf dem Server wird nichts gespeichert, die Original-PDFs werden nur gelesen.
- **Sitzungen:** Jeder Browser hat seine eigene Liste. Hochgeladene PDFs liegen in einem Temp-Ordner und werden nach 12 Stunden ohne Zugriff gelöscht.
- **Sicherheit:** Der Browser kann keine Pfade angeben. Gelesen wird nur, was in einem Quellordner liegt oder hochgeladen wurde. Es gibt keine Anmeldung: Wer die Adresse im Netz erreicht, kann das Tool nutzen. Den Server deshalb nur im Firmennetz betreiben.
- **Audit-Spalten** in der Tag-Tabelle: Review und Änderung als Auswahlliste, dazu Neuer Wert, Bemerkung und WPO. Datum und User werden automatisch gesetzt.
  - Bearbeiten per Doppelklick in die Zelle, speichern mit „Review speichern“ oder Strg+S. Beim Wechsel der PDF wird automatisch gespeichert.
  - Gespeichert wird auf dem Server wie „Review speichern“ der Desktop-App (`data\reviews`, jeder Stand eine neue Datei). Redline, Review-Excel und Desktop-App sehen die Einträge.
  - „Korrektur erforderlich“ erscheint rot in der Tabelle und im Viewer.
  - Als User steht der Name, den jeder Browser beim ersten Eintrag einmal abfragt.
- **Noch nicht in der Web-Version:** Tabellenansichten speichern, Viewer auf 2. Monitor, Einstellungen (Pfade, Tag-Muster) im Browser, Sprachwahl, Projektmodus, Datenlink (Importliste, Abgleich, Review Importliste) und Tabellen-Vorschau. Diese Funktionen gibt es nur im Desktop-Tool.

## Projektmodus (Projektdefinitionen wie P3D Tag Compliance)
- **Aus (Standard):** das Tool arbeitet wie bisher mit den Tag-Mustern, ohne Projektregeln.
- **An:** Jeder Tag wird gegen die Projektdefinitionen geprüft. Neue Spalten „Projekt-Prüfung“ (OK / Fehler) und „Projekt-Hinweis“, Filter „Nur Abweichungen“, Abweichungen im Viewer rot (außer Review „OK“ / „Nicht relevant“), Prüfspalten auch in Export und Review-Excel.
- **Projekt wählen:** „Aus Tag Compliance übernehmen …“ liest die `pidtag_project.db` von P3D Tag Compliance (nur lesend) und legt ein Projekt in `<Datenordner>\projects` an. Alternativ Projekt öffnen oder neu anlegen.
- **Projekt mit allen Einstellungen:** Die Projekt-Datenbank speichert auch die Einstellungen des Tools: Quell-/Exportordner, Tag-Muster, Importliste samt Kachel-Editor-Anpassung, Datenlink-Felder, Tabellenansichten, Umschalter und Review-Optionen. Menü „Projekt wählen“: Projekt speichern, Projekt speichern unter …, Einstellungen des Projekts laden. Beim Öffnen fragt das Tool, ob gespeicherte Einstellungen geladen werden; beim Programmstart öffnet es das zuletzt gewählte Projekt ohne Rückfrage.
- **Projektdefinitionen …:** Codelisten, Listen, Tag-Strukturen und -Segmente, Notizen, Trennzeichen-Regel und die **PDF-Prüfregeln** (PDF-Tag-Typ → Tag-Struktur) bearbeiten; Listen anlegen, Spalten, Liste aus Excel; Excel-Export/-Import im Blattformat von Tag Compliance; „Tag testen“.
- **Segment-Quellen:** Tabelle (`def_function_codes`), Liste mit Spalte (`list:media|Medium Code (Fluid)`), `const:TEXT`, `seq:3` (laufende Nummer), `free`. Ein Tag ist OK, wenn er zu einer Struktur seines Typs passt; sonst nennt der Hinweis das erste nicht passende Segment oder die Trennzeichen-Regel.
- **Befunde (Spalte „Projekt-Prüfung“, kombinierbar mit „ + “):** „Regelfehler Projektdefinition“ (Trennzeichen oder Aufbau), „Code fehlt in Projektdefinition“ (Code nicht in der Liste), „Code unvollständig“ (Platzhalter `?`, X statt Ziffern wie `XXX`, `SSXX`, `ST1X`), dazu „mehrfach vorhanden“, wenn der Tag auf einer Seite mehrfach steht. Platzhalter-Tags werden nur im Projektmodus eingelesen.
- Noch nicht in der Web-Version.

## Arbeitsablauf (Menüband)
| Gruppe | Funktionen |
|---|---|
| **Projekt** | Projekt wählen (aus Tag Compliance übernehmen, öffnen, neu, speichern), Projektmodus an/aus und Rohrleitungen an/aus (an = Symbol grün), Projektdefinitionen …, Pfade, Tag-Muster, Einstellungen › Layer für Review im PDF |
| **1 Einlesen** | Quellordner scannen (F5), Ordner öffnen, Dateien öffnen, **Liste importieren** (Datenlink: Excel-Liste importieren, Importtabelle bearbeiten, Review-Tabelle, Datenlinks anzeigen, Importtabelle entfernen) |
| **2 Ansicht** | Blätter „PID-Tags“ und „Alle Tags“, Viewer auf 2. Monitor, Tabellen-Vorschau, Tabellenprofil (Ansicht aller Tabellen speichern/laden) |
| **3 Prüfen** | Fundstelle zurück / weiter (Umschalt+F3 / F3), Nur doppelte Tags, Nur Projektabweichungen, Review Importliste, Filter zurücksetzen, Tabelle bearbeiten, Review speichern |
| **4 Review / Redline** | Review Auswahl/Bulk, Redline-PDF der gewählten PDF, Review-Excel der gewählten PDF |
| **5 Export** | Export Excel, Export CSV, Exportordner öffnen |
| **Hilfe** | Handbuch (interaktive HTML-Datei `assets\help\handbuch.html`), Info, **Sprache** (Deutsch / English / Français, wirkt sofort, wird gemerkt) |

Jede Gruppe hat oben eine dunkelblaue Überschrift; ein Klick darauf klappt die Gruppe ein (Zustand wird gemerkt). Die direkten Funktionen sitzen zusätzlich als Tab-Buttons in Leisten über den Bereichen:
- **Dateien:** Alle markieren, Review markierte …, Excel
- **Tags:** Aus PDF-Scan übernehmen, Autofill OK, Bearbeiten, Speichern, Nur doppelte, Nur Abweichungen, Filter zurücksetzen, Abgleich (mit der Importliste), ◀ ▶ Fundstelle, Excel, Redline
- **PDF-Viewer:** Einpassen, Zoom ±, Drehen, ◀ ▶ Fundstelle, Redline, Öffnen (im Standardprogramm), 2. Monitor

## Blatt „PID-Tags“
1. **Dateien:** eine Zeile je PDF.
   - Spalten: PDF, Zeichnungsnr., Erstellt (PDF), Ersteller, Checked, Rev, Rev-Datum, Rev-Text, Plot-Benutzer, Anzahl Tags, Fehler; mit Datenlink 1 dazu „Datenlink-Treffer“ und die Spalten der Importliste.
   - Mehrere PDFs markierst du mit Strg- oder Umschalt-Klick, etwa für den Review.
2. **Tags der gewählten PDF:** Typ, Tag, Anzahl, Seiten, im Projektmodus Projekt-Prüfung und Projekt-Hinweis, die Review-Spalten (Review, Änderung, Neuer Wert, Bemerkung, WPO, Datum, User), mit „Aus PDF-Scan übernehmen“ die Schriftfeld-Werte und mit Datenlink 2 die Spalten der Importliste. Zeilen mit Anzahl > 1 (doppelte Tags) sind **gelb** hinterlegt.
   - **Beim Wechsel der PDF** fragt das Tool nach ungespeicherten Review-Einträgen (Speichern / Verwerfen / Abbrechen) und setzt die Filter der Tag-Tabelle auf Standard zurück.
3. **PDF-Viewer:** Die Fundstellen doppelter Tags sind gelb hinterlegt.
   - **Tag mit einer Fundstelle:** Ein Klick oder die Pfeiltasten markieren den Tag und zoomen darauf.
   - **Tag mit mehreren Fundstellen:**
     - Der erste Klick zeigt die ganze Seite, alle Fundstellen sind umrahmt und nummeriert.
     - Jeder weitere Klick auf denselben Tag (oder F3) springt zur nächsten Fundstelle. Nach der letzten kommt wieder die Übersicht.
     - Oben links steht z. B. „151ISO01: Fundstelle 2 / 6“.
   - **Bedienung:** Mausrad zoomt, Ziehen verschiebt, Doppelklick zeigt die ganze Seite. Der sichtbare Ausschnitt wird bei jedem Zoom scharf neu aus der PDF gezeichnet.
   - **Drehen:** Plots mit Seitendrehung (/Rotate) erscheinen automatisch richtig herum. Mit „Drehen“ lässt sich die Ansicht zusätzlich in 90°-Schritten drehen.
   - **2. Monitor:** zeigt den Viewer in einem eigenen Fenster auf dem anderen Bildschirm. Die Wahl wird gemerkt. Schließen oder „Viewer zurückholen“ setzt ihn wieder ins Hauptfenster.

Das Blatt „Alle Tags“ zeigt die Tags aller eingelesenen PDFs in einer Tabelle.

## Review-Einträge in der Tag-Tabelle
- **Bearbeiten** (Umschalter): Review und Änderung als Auswahlliste, Neuer Wert, Bemerkung und WPO frei. Doppelklick oder Tippen in die Zelle; Datum und User setzt das Tool automatisch.
- **Autofill OK:** bei allen Tags mit Review „OK“ (oder leerem Review und Projekt-Prüfung „OK“) Review = OK, Datum und User setzen; leeres WPO bekommt den Checked-Wert aus dem Schriftfeld.
- **Speichern** (Strg+S): jeder Stand wird als neue Datei mit Zeitstempel in `<Datenordner>\reviews` gespeichert. Die PDF selbst wird nie verändert.
- „Korrektur erforderlich“ erscheint rot in der Tabelle, im Viewer und im Redline-PDF.

## Datenlink: Excel-Liste importieren und abgleichen
Verknüpft eine Excel-Liste (z. B. die Instrumenten-Gesamtliste aus P3D InstrumentationList) mit den Tabellen des Tools. Die Excel-Datei wird nur gelesen.
1. **Liste importieren** (Menüband „1 Einlesen“): Excel-Datei und Blatt wählen. Es öffnet sich der **Kachel-Editor** als Vollfenster:
   - oben die Kacheln mit Menüband Start / Umwandeln / Spalte hinzufügen (Spalten verschieben, umbenennen, nicht exportieren, gruppieren, teilen, ersetzen, Wenn-dann-, Ja/Nein-, Index-Spalten, Spalten aus einer anderen Liste …; alles rückgängig zu machen),
   - rechts die Seitenleiste (aktive Kachel, Gruppe, Verlauf),
   - unten die Datentabelle mit den Standard-Tabellenfunktionen (Filterfeld je Spalte, Wertauswahl per Doppelklick, Rechtsklick-Menü, Excel-Symbol, Zoom).
   - **Datenlink 1** (Zeichnung, z. B. „P&ID No.“) und **Datenlink 2** (Tag, z. B. „Tag -PID“) per Auswahlfeld oder Rechtsklick auf den Spaltenkopf.
   - Anpassung speichern / laden (für die nächste Version der Liste), Als Excel speichern, „Übernehmen und verlinken“.
2. **Datenlink-Feld im Tool setzen:** Rechtsklick auf den Spaltenkopf der Dateiliste (z. B. „Zeichnungsnr.“ oder „PDF“) bzw. der Tag-Tabelle (z. B. „Tag“) › „… als Datenlink-Feld setzen“. Der Kopf wird dunkelgrün, die Spalten aus der Importliste bekommen einen hellgrünen Kopf mit „Import“.
3. **Abgleich:** ohne Groß-/Kleinschreibung; ohne exakten Treffer zählt die Endung ab einem Bindestrich („301-30-149-TI-300“ ↔ „TI-300“). Beim Zeichnungsabgleich zählen „.pdf“ und ein Kopie-Zusatz wie „ (2)“ nicht. Mit beiden Datenlinks zählen nur Zeilen der Importliste **derselben Zeichnung**. Haben die Tabellen keinen einzigen gemeinsamen Wert, meldet das Tool das mit Beispielwerten.
4. **Abgleich-Richtung** (Leiste der Tag-Tabelle › Abgleich, wird gemerkt):
   - **PDF-Tags → Importliste** (Standard): alle Tags der PDF mit den passenden Listenwerten,
   - **Importliste → PDF-Tags:** alle Zeilen der Liste zu dieser Zeichnung, getroffene mit ihrem PDF-Tag,
   - **Tags beider Listen:** alles zusammen.
   Fehlende Werte stehen als **„n.a.“** da. Zeilen ohne PDF-Tag lassen sich nicht bearbeiten.
5. **Review Importliste** (Menüband „3 Prüfen“): eigenes Blatt mit einem Prüfergebnis je Zeile über alle PDFs: **OK**, **Nicht in Liste** (Tag im PDF, nicht in der Liste), **Fehlt im PDF** (Zeile der Liste zu einer gescannten Zeichnung), **Zeichnung nicht gescannt**. Rechts die exportierten Spalten der Importliste, Excel über das Symbol in der Tabellenecke.

Die Importliste liegt in `<Datenordner>\config\data_link.json` (Originalliste, Anpassung und Ergebnis), die Datenlink-Felder in `config\state.json`.

## Tabellen-Vorschau
Menüband „2 Ansicht“ › Tabellen-Vorschau öffnet ein eigenes Blatt mit den Tags **aller** PDFs. Vorne PDF und Zeichnungsnr., danach die Spalten der Tag-Tabelle in der Reihenfolge und Sichtbarkeit, die du dort eingestellt hast (Review-, Projekt-, Scan- und Datenlink-Spalten, Abgleich wie gewählt), ohne X/Y. Ungespeicherte Review-Einträge der gewählten PDF sind enthalten. Excel über das Symbol in der Tabellenecke.

## Tabellen
Alle Tabellen folgen dem Standard aus `main_gui_kit`:
- Filter je Spalte (Doppelklick öffnet die Wertauswahl) und Filter über das ganze Blatt
- Sortierung, Spalten verschieben oder ausblenden, Zoom
- dunkelblauer Tabellenkopf

Die Ansicht jeder Tabelle (Spaltenreihenfolge, Breiten, Ausblenden, Sortierung, Zoom) wird automatisch gemerkt. **Ausnahme Filter:** Dateiliste und Tag-Tabelle starten immer ohne Filter, Filter werden dort nicht gemerkt. Benannte Ansichten verwaltest du über *Save / Load / Reset Layout*, die Ansicht aller Tabellen auf einmal über **Tabellenprofil** (Menüband „2 Ansicht“). Das **Excel-Symbol** oben links in der Tabelle sichert die sichtbare Ansicht als Excel oder CSV. Der Dateiname ist vorbelegt mit PDF- oder Tabellenname und Zeitstempel, z. B. `SGOPS-…-EQPM-001_Tags_2026-11-20_14-29.xlsx`.

**Rechtsklick (wie P3D XCHANGE):**
- **Zelle:** Kopieren, Zeile kopieren (mit/ohne Überschriften), nur diesen Wert zeigen, Filter der Spalte / alle Filter zurücksetzen, Spalten …, Nach Excel …
- **Excel-Symbol:** Dialog „Spalten …“ (verschieben, ein-/ausblenden, Standard)
- **Spaltenkopf:** ausblenden, verschieben, Ausrichtung, Ansicht zurücksetzen, Teilreiter

## Review / Redline
- **Redline-PDF:** eine Kopie der PDF, das Original bleibt unverändert.
  - An jeder Fundstelle stehen ein Rahmen und die **Pos.-Nr.** Farben wie im Viewer: grün = korrekt, rot = fehlerhaft (Review „Korrektur erforderlich“, im Projektmodus Abweichung), doppelte Tags gelb hinterlegt.
  - Mit **Einstellungen › Layer für Review im PDF** (Standard an) liegen alle Review-Kommentare auf der PDF-Ebene `Review_TT.MM.JJJJ` und lassen sich im PDF-Programm unter „Ebenen“ ein- und ausblenden.
  - Jede Fundstelle trägt einen PDF-Kommentar mit Pos., Typ, Tag und „Fundstelle n / m“. Er erscheint in Acrobat, Bluebeam oder PDF-XChange in der Kommentarliste.
  - Oben links steht ein Übersichtskommentar.
  - Es gilt der Tabellenfilter: Mit „Nur doppelte“ entsteht ein Redline nur mit den doppelten Tags.
- **Review-Excel:** Blatt „Review“ mit einer Zeile je Fundstelle.
  - Spalten: **Pos.-Nr.** (dieselbe wie im Redline, im Bulk `<PDF-Nr>.<Pos>`), PDF, Zeichnungsnr., Rev, Typ, Tag, Seite, Fundstelle, Anzahl auf Seite, Doppelt, im Projektmodus Projekt-Prüfung und Projekt-Hinweis, **Review-Kommentar**, dann die Review-Spalten der Tag-Tabelle: **Review** und **Änderung** (Auswahllisten), Neuer Wert, Bemerkung, WPO, Datum, User. Keine X/Y-Koordinaten (seit 1.0.24).
  - Doppelte Tags sind gelb hinterlegt, sie bekommen den Status „Offen“.
  - Dazu kommen die Blätter „Dateien“ und „Info“.
- **Review Auswahl/Bulk:**
  - Auswahl: markierte oder alle eingelesenen PDFs.
  - Ausgaben zum Ankreuzen: Redline-PDF je PDF, Review-Excel je PDF, Review-Excel gesamt.
  - Zielordner wählbar, optional mit Unterordner `Review_<Zeitstempel>`. Die Auswahl wird gemerkt.

## Export
- **Export Excel:** Blätter „Dateien“ und „Tags“ über alle PDFs (Tags mit Seiten, X/Y der ersten Fundstelle, gespeicherten Review-Spalten und im Projektmodus den Prüfspalten).
- **Export CSV:** Tags plus `_Dateien.csv`, getrennt mit `;`, UTF-8 mit BOM.
- Für eine Tabelle genau so, wie sie im Tool eingestellt ist: Tabellen-Vorschau bzw. das Excel-Symbol der jeweiligen Tabelle.

## Erkennung
| Feld | Quelle |
|---|---|
| Erstellt | PDF-Metadaten `creationDate` (Plotzeitpunkt) |
| Ersteller | Schriftfeld `DRAWN:` → Kürzel der letzten Revisionszeile → PDF-Author → Plot-Benutzer |
| Checked, Designed, Datum, Rev | Schriftfeld (rechts unten) und letzte Revisionszeile. Steht neben dem Label („CHECKED:“) nichts, gilt der Text direkt darunter in derselben Spalte (Name in der zweiten Zeile) |
| Zeichnungsnr. | größte Schrift mit „-PID-“ im unteren Zehntel des Schriftfelds; liegt sie weiter links (Schriftfeld mit Kunden- und Exyte-Nummer), Ausweichsuche ab 60 % der Breite nur in deutlich größerer Schrift. Senkrecht geschriebene Verweise zählen nicht. Die Nummer wird aus der Tag-Liste entfernt |
| Plot-Benutzer | Plotpfad am Blattrand `C:\Users\<name>\…` |
| Instrument | Kürzel in der Blase plus Nummer darunter, über die Lage zusammengesetzt (`TIT-130`) |
| Equipment / Armatur / Volltag / Zeichnungsverweis | Regex (`111PMP01`, `VH340`, `203-17-111-TZIT-011`, `…-PID-…`) |
| Rohrleitung (optional: Menüband › Projekt › Rohrleitungen) | Regex `pipe_line` (`TFHR_SS01_001_1"`, `PFC_ST10_015_1/2"`), waagerecht und senkrecht; getrennte Teile (`… 1/2"`, `_205_1`) werden zusammengesetzt |
| Gedrehte Plots | Wortpositionen werden in die sichtbare Lage umgerechnet (/Rotate 90/180/270) |

Die Muster stehen in `data\config\tag_patterns.json` und werden beim ersten Start angelegt. Unter **Projekt › Tag-Muster** lassen sich Regex und Ausschlussliste für Kürzel anpassen, z. B. `MIN`, `HALF`, `SHORT`.

Hinweis: Equipment steht oft zusätzlich in der Equipment-Tabelle am Blattfuß. Es erscheint dann als doppelter Tag, was gewollt sein kann.

## Pfade
- **Datenordner:** `%P3D_PDFREADER_HOME%`, sonst `<Tool>\data`, als EXE `%LOCALAPPDATA%\P3D_PDFREADER`.
  - `config\paths.json`: Quellordner, Exportordner
  - `config\state.json`: zuletzt verwendete Ordner, Review-Optionen, Viewer auf 2. Monitor, Sprache, Umschalter, eingeklappte Menüband-Gruppen, Datenlink-Felder (`data_link_fields`), Abgleich-Richtung (`data_link_join`)
  - `config\table_views.json`: gemerkte Tabellenansichten
  - `config\tag_patterns.json`
  - `config\data_link.json`: Importliste mit Kachel-Editor-Anpassung
  - `reviews\`: Review-Einträge je PDF (jeder Stand eine Datei)
  - `projects\`: Projekt-Datenbanken
  - `logs\`, `exports\`
- **Pfade-Dialog** (**Projekt › Pfade**): Quellordner hinzufügen oder entfernen (✓/✗ = vorhanden), Exportordner wählen, Speicherorte öffnen.
- Pfade werden über `resolve()` normalisiert, das Subst-Laufwerk A: wird dabei zu C:. Es gibt keine festen Laufwerksbuchstaben.

## Aufbau
```
src\p3d_pdfreader\
  core\      extract (PDF → Metadaten, Schriftfeld, Tags), patterns, export, review (Pos.-Nr., Review-Excel),
             redline (Redline-PDF), review_store (Review-Einträge), project_defs + project_settings (Projektmodus),
             data_link (Importliste, Abgleich, Review Importliste) – ohne Qt
  gui\       main_window (Menüband, Blätter, Tabellen), viewer_panel + preview (PDF-Viewer), toolstrip (Tab-Buttons),
             data_link_ui (Datenlink im Hauptfenster), tile_editor\ (Kachel-Editor-Fenster), project_dialog + project_tiles,
             review_dialog, paths_dialog, worker (Scan im Hintergrund), table_views, table_profiles, table_menu,
             table_export, msgbox, ribbon_fold, web_control, last_paths
             übernommen aus P3D XCHANGE 0.5.0 (nicht ändern): design, appearance, ribbon, sheet, progress, icons
  column_editor\  Kachel-Editor aus P3D Tag Compliance (nicht von Hand ändern, siehe QUELLE.md)
  web\       server (Web-Server, nur Standardbibliothek; nutzt core), report (Offline-Bericht) – Oberfläche in assets\web
  paths.py   Pfadverwaltung
main_gui_kit\  aus P3D XCHANGE (nicht ändern)
Launcher\      Launcher (aus P3D XCHANGE, nur Namen/Pfade angepasst)
tools\         Hilfebilder, i18n-Katalog, Versionsinfo, Übersetzung des Kachel-Editors
tests\         test_architecture, test_extract, test_gui, test_data_link, test_project_defs, test_ribbon_menus,
               test_viewer_display, test_web
```
Eigene Icons: PNG-Dateien in `src\p3d_pdfreader\assets\icons\<schlüssel>.png` haben Vorrang vor den gezeichneten Platzhaltern, z. B. `excel.png` oder `redline.png`.

## Tests
PowerShell (ganze Suite ca. 8 Minuten):
```powershell
$env:QT_QPA_PLATFORM='offscreen'; $env:PYTHONPATH='src;.;tests'; & 'C:\Users\mail\AI_Coworker_Claude\Tools_Central\Python\python\python.exe' -m pytest -q -W ignore tests
```
Beispiel-PDFs: `%USERPROFILE%\Downloads\PID Plots`. Ein anderer Ordner lässt sich über `P3D_PDFREADER_SAMPLES` setzen. Die Tests prüfen unter anderem einen gedrehten Plot (EQPM-012), Schriftfeld und Zeichnungsnummer, Redline-Kommentare, die Navigation durch die Fundstellen, den Review-Lauf, Datenlink und Abgleich, den Kachel-Editor und die Tabellen-Vorschau. Nur einen Testlauf gleichzeitig starten (gemeinsamer Ordner `.pytest_tmp`).
