/* Erzeugt von tools/make_help_workflow.py - nicht von Hand bearbeiten. */
const WF = [
 {
  "id": "overview",
  "title": "Überblick – das Hauptfenster",
  "intro": "So ist das Fenster aufgebaut. Die Gruppen im Menüband entsprechen den Arbeitsschritten; ein Klick auf die dunkelblaue Gruppenüberschrift klappt eine Gruppe ein oder aus.",
  "figs": [
   {
    "img": "img/wf_overview.png",
    "w": 2843,
    "h": 1060,
    "caption": "Hauptfenster mit Beispiel-PDFs",
    "marks": [
     {
      "rect": [
       0.28,
       6.7,
       21.03,
       1.79
      ],
      "pin": [
       0.28,
       6.7
      ],
      "title": "Menüband: Projekt",
      "text": "Projekt wählen, Projektmodus, Rohrleitungen, Projektdefinitionen, Pfade, Einstellungen."
     },
     {
      "rect": [
       21.63,
       6.7,
       10.94,
       1.79
      ],
      "pin": [
       21.63,
       6.7
      ],
      "title": "Menüband: 1 Einlesen",
      "text": "PDFs einlesen und Excel-Liste für den Datenlink importieren."
     },
     {
      "rect": [
       32.89,
       6.7,
       10.59,
       1.79
      ],
      "pin": [
       32.89,
       6.7
      ],
      "title": "Menüband: 2 Ansicht",
      "text": "Blätter wechseln, Viewer auf den 2. Monitor, Tabellen-Vorschau."
     },
     {
      "rect": [
       43.79,
       6.7,
       21.07,
       1.79
      ],
      "pin": [
       43.79,
       6.7
      ],
      "title": "Menüband: 3 Prüfen",
      "text": "Fundstellen, Filter, Tabelle bearbeiten, Review speichern."
     },
     {
      "rect": [
       65.18,
       6.7,
       10.45,
       1.79
      ],
      "pin": [
       65.18,
       6.7
      ],
      "title": "Menüband: 4 Review / Redline",
      "text": "Redline-PDF und Review-Excel erzeugen."
     },
     {
      "rect": [
       75.94,
       6.7,
       6.89,
       1.79
      ],
      "pin": [
       75.94,
       6.7
      ],
      "title": "Menüband: 5 Export",
      "text": "Alle Dateien und Tags als Excel oder CSV."
     },
     {
      "rect": [
       83.15,
       6.7,
       8.44,
       1.79
      ],
      "pin": [
       83.15,
       6.7
      ],
      "title": "Menüband: Web",
      "text": "Web-Server für Kollegen, Offline-Bericht."
     },
     {
      "rect": [
       91.91,
       6.7,
       7.35,
       1.79
      ],
      "pin": [
       91.91,
       6.7
      ],
      "title": "Menüband: Hilfe",
      "text": "Dieses Handbuch, Info und Sprache."
     },
     {
      "rect": [
       0.04,
       23.49,
       99.93,
       2.64
      ],
      "pin": [
       0.04,
       23.49
      ],
      "title": "Kopfband",
      "text": "Projekt, Quelle, Anzahl PDFs, Tags, Fehler und (Projektmodus) Abweichungen."
     },
     {
      "rect": [
       0.39,
       27.17,
       99.23,
       30.0
      ],
      "pin": [
       2.93,
       27.17
      ],
      "title": "Tabelle 1 – Dateien",
      "text": "Eine Zeile je PDF mit Schriftfeld-Werten. Auswahl einer Zeile lädt Tags und PDF."
     },
     {
      "rect": [
       0.39,
       57.64,
       60.64,
       39.81
      ],
      "pin": [
       0.39,
       57.64
      ],
      "title": "Tabelle 2 – Tags der gewählten PDF",
      "text": "Alle Tags mit Anzahl, Seiten, Review-Spalten und – mit Datenlink – Spalten aus der Excel-Liste."
     },
     {
      "rect": [
       61.2,
       57.64,
       38.41,
       39.81
      ],
      "pin": [
       61.2,
       57.64
      ],
      "title": "PDF-Viewer",
      "text": "Seite mit farbigen Rahmen an den Fundstellen; Klick auf einen Tag zoomt hin."
     }
    ]
   }
  ]
 },
 {
  "id": "project",
  "title": "Projekt einrichten",
  "intro": "Einmal je Projekt: Projekt wählen und bei Bedarf den Projektmodus einschalten. Ohne Projekt arbeitet das Tool im Standardmodus mit den Tag-Mustern.",
  "figs": [
   {
    "img": "img/wf_project.png",
    "w": 616,
    "h": 104,
    "caption": "Menüband, Gruppe „Projekt“",
    "marks": [
     {
      "rect": [
       1.62,
       26.92,
       10.36,
       65.38
      ],
      "pin": [
       1.62,
       26.92
      ],
      "title": "Projekt wählen",
      "text": "Projekt anlegen, öffnen oder aus P3D Tag Compliance übernehmen (pidtag_project.db wird nur gelesen)."
     },
     {
      "rect": [
       12.3,
       26.92,
       18.61,
       65.38
      ],
      "pin": [
       12.3,
       26.92
      ],
      "title": "Projektmodus an/aus",
      "text": "Prüft jeden Tag gegen die Projektdefinitionen. An = Symbol grün; Spalten „Projekt-Prüfung“ und „Projekt-Hinweis“ erscheinen."
     },
     {
      "rect": [
       31.23,
       26.92,
       18.93,
       65.38
      ],
      "pin": [
       31.23,
       26.92
      ],
      "title": "Rohrleitungen an/aus",
      "text": "Rohrleitungsnummern mit in die Tag-Liste übernehmen; Umschalten liest die PDFs neu ein."
     },
     {
      "rect": [
       50.49,
       26.92,
       15.86,
       65.38
      ],
      "pin": [
       50.49,
       26.92
      ],
      "title": "Projektdefinitionen …",
      "text": "Codelisten, Listen, Tag-Strukturen und Prüfregeln im Kachel-Editor bearbeiten; Excel-Export/-Import."
     },
     {
      "rect": [
       66.67,
       26.92,
       10.36,
       65.38
      ],
      "pin": [
       66.67,
       26.92
      ],
      "title": "Pfade",
      "text": "Quellordner (für „Quellordner scannen“) und Exportordner festlegen."
     },
     {
      "rect": [
       77.35,
       26.92,
       10.36,
       65.38
      ],
      "pin": [
       77.35,
       26.92
      ],
      "title": "Tag-Muster",
      "text": "tag_patterns.json öffnen: Erkennungsmuster je Tag-Typ."
     },
     {
      "rect": [
       88.03,
       26.92,
       10.36,
       65.38
      ],
      "pin": [
       88.03,
       26.92
      ],
      "title": "Einstellungen",
      "text": "Layer für Review im PDF (Redline-Kommentare auf eigener PDF-Ebene)."
     }
    ]
   }
  ]
 },
 {
  "id": "read",
  "title": "PDFs einlesen",
  "intro": "PDF-Plots einlesen. Danach steht je PDF eine Zeile in Tabelle 1; die erste PDF wird gewählt und angezeigt.",
  "figs": [
   {
    "img": "img/wf_read.png",
    "w": 331,
    "h": 104,
    "caption": "Menüband, Gruppe „1 Einlesen“",
    "marks": [
     {
      "rect": [
       3.02,
       26.92,
       25.68,
       65.38
      ],
      "pin": [
       3.02,
       26.92
      ],
      "title": "Quellordner scannen",
      "text": "Alle PDFs der Quellordner (aus „Pfade“) samt Unterordnern einlesen. Taste F5. Ein Fortschrittsfenster zeigt den Stand."
     },
     {
      "rect": [
       29.31,
       26.92,
       20.54,
       65.38
      ],
      "pin": [
       29.31,
       26.92
      ],
      "title": "Ordner öffnen …",
      "text": "Einen beliebigen Ordner mit PDF-Plots einlesen."
     },
     {
      "rect": [
       50.45,
       26.92,
       20.54,
       65.38
      ],
      "pin": [
       50.45,
       26.92
      ],
      "title": "Dateien öffnen …",
      "text": "Einzelne PDF-Dateien wählen."
     },
     {
      "rect": [
       71.6,
       26.92,
       25.38,
       65.38
      ],
      "pin": [
       71.6,
       26.92
      ],
      "title": "Liste importieren",
      "text": "Excel-Liste für den Datenlink importieren – siehe Schritt 3."
     }
    ]
   },
   {
    "img": "img/wf_files.png",
    "w": 2829,
    "h": 326,
    "caption": "Tabelle 1 – Dateien nach dem Einlesen",
    "marks": [
     {
      "rect": [
       1.66,
       1.23,
       96.29,
       8.28
      ],
      "pin": [
       1.66,
       1.23
      ],
      "title": "Blattfilter",
      "text": "Sucht in allen Spalten der Tabelle."
     },
     {
      "rect": [
       2.26,
       11.96,
       4.14,
       7.67
      ],
      "pin": [
       4.81,
       11.96
      ],
      "title": "Alle markieren",
      "text": "Alle PDFs markieren, z. B. für den Review."
     },
     {
      "rect": [
       6.54,
       11.96,
       4.98,
       7.67
      ],
      "pin": [
       9.08,
       11.96
      ],
      "title": "Review markierte …",
      "text": "Redline und Review-Excel für die markierten PDFs (Schritt 6)."
     },
     {
      "rect": [
       1.2,
       22.7,
       98.59,
       23.01
      ],
      "pin": [
       13.93,
       22.7
      ],
      "title": "Spaltenkopf mit Filterzeile",
      "text": "Klick sortiert, Feld darunter filtert, Doppelklick im Feld wählt Werte. Rechtsklick: Spaltenmenü."
     },
     {
      "rect": [
       1.2,
       45.71,
       98.59,
       21.78
      ],
      "pin": [
       1.2,
       45.71
      ],
      "title": "PDF wählen",
      "text": "Zeile anklicken: Tag-Tabelle und Viewer zeigen diese PDF. Mehrere mit Strg- oder Umschalt-Klick markieren."
     },
     {
      "rect": [
       0.14,
       90.8,
       92.86,
       7.98
      ],
      "pin": [
       0.14,
       90.8
      ],
      "title": "Tabellenansicht",
      "text": "Ansicht speichern, laden, zurücksetzen; der Regler daneben zoomt."
     }
    ]
   }
  ]
 },
 {
  "id": "import",
  "title": "Excel-Liste importieren (Datenlink)",
  "intro": "Optional: eine Excel-Liste – z. B. die Instrumenten-Gesamtliste – einlesen und im Kachel-Editor (Vollfenster) zu einer passenden Importliste anpassen; dann die beiden Schlüsselspalten festlegen.",
  "figs": [
   {
    "img": "img/wf_import.png",
    "w": 1720,
    "h": 900,
    "caption": "Liste importieren › Excel-Liste importieren … – Kachel-Editor im Vollfenster (Beispielliste)",
    "marks": [
     {
      "rect": [
       10.76,
       0.67,
       28.2,
       2.89
      ],
      "pin": [
       10.76,
       0.67
      ],
      "title": "Quelle",
      "text": "Gewählte Excel-Datei und Blatt (Blatt „Gesamtliste“ wird vorgeschlagen)."
     },
     {
      "rect": [
       39.19,
       0.67,
       7.21,
       2.89
      ],
      "pin": [
       39.19,
       0.67
      ],
      "title": "Andere Excel-Liste …",
      "text": "Andere Datei oder anderes Blatt einlesen; die Anpassung und die Datenlinks werden darauf angewendet."
     },
     {
      "rect": [
       53.78,
       0.67,
       8.08,
       2.89
      ],
      "pin": [
       53.78,
       0.67
      ],
      "title": "Anpassung speichern / laden",
      "text": "Alle Schritte als Datei sichern und auf die nächste Version der Liste anwenden."
     },
     {
      "rect": [
       62.09,
       0.67,
       7.38,
       2.89
      ],
      "pin": [
       62.09,
       0.67
      ],
      "title": "Als Excel speichern …",
      "text": "Die angepasste Liste als kompatible Excel-Datei speichern."
     },
     {
      "rect": [
       10.06,
       4.0,
       15.12,
       3.0
      ],
      "pin": [
       15.15,
       4.0
      ],
      "title": "Datenlink 1 → Tabelle 1 (Dateien)",
      "text": "Spalte der Liste mit der Zeichnungsnummer, z. B. „P&ID No.“."
     },
     {
      "rect": [
       35.17,
       4.0,
       15.12,
       3.0
      ],
      "pin": [
       35.17,
       4.0
      ],
      "title": "Datenlink 2 → Tabelle 2 (Tags)",
      "text": "Spalte der Liste mit dem Tag, z. B. „Tag“."
     },
     {
      "rect": [
       0.47,
       7.67,
       84.59,
       10.44
      ],
      "pin": [
       0.47,
       7.67
      ],
      "title": "Bereich 1: Menüband des Kachel-Editors",
      "text": "Start / Umwandeln / Spalte hinzufügen: rückgängig, ausblenden, Export ja/nein, gruppieren, teilen, ersetzen, Wenn-dann …"
     },
     {
      "rect": [
       0.47,
       18.11,
       84.59,
       27.33
      ],
      "pin": [
       0.47,
       18.11
      ],
      "title": "Kacheln = Spalten",
      "text": "Ziehen = verschieben, Doppelklick = umbenennen, Kachel in „Nicht exportiert“ = wird nicht übergeben."
     },
     {
      "rect": [
       85.76,
       0.0,
       14.24,
       97.78
      ],
      "pin": [
       85.76,
       0.0
      ],
      "title": "Bereich 2: Seitenleiste",
      "text": "Aktive Kachel, Gruppe und Verlauf aller Schritte (einklappbar, als Fenster lösbar)."
     },
     {
      "rect": [
       2.15,
       49.67,
       16.92,
       3.67
      ],
      "pin": [
       2.15,
       49.67
      ],
      "title": "Bereich 3: Datentabelle",
      "text": "Die Liste, wie sie übergeben wird. Rechtsklick auf einen Spaltenkopf: „Als Datenlink 1/2 setzen“ – gesetzte Spalten werden dunkelgrün."
     },
     {
      "rect": [
       75.99,
       0.67,
       9.07,
       2.89
      ],
      "pin": [
       75.99,
       0.67
      ],
      "title": "Übernehmen und verlinken",
      "text": "Speichert Liste und Anpassung und übergibt sie an das Tool."
     }
    ]
   }
  ]
 },
 {
  "id": "link",
  "title": "Datenlink-Feld in den Tabellen setzen",
  "intro": "Je Tabelle ein Feld festlegen, das zur Liste passt. Sobald Datenlink und Feld gesetzt sind, erscheinen die Listenspalten. Abgleich ohne Groß-/Kleinschreibung; ohne exakten Treffer zählt die Endung ab einem Bindestrich („203-17-TI-300“ ↔ „TI-300“).",
  "figs": [
   {
    "img": "img/wf_link_fields.png",
    "w": 2829,
    "h": 555,
    "caption": "Datenlink-Felder gesetzt: Köpfe dunkelgrün, Listenspalten angefügt",
    "marks": [
     {
      "rect": [
       4.03,
       13.33,
       4.45,
       13.51
      ],
      "pin": [
       4.03,
       13.33
      ],
      "title": "Datenlink-Feld Tabelle 1",
      "text": "Rechtsklick auf „Zeichnungsnr.“ › „als Datenlink-Feld setzen“ – der Kopf wird dunkelgrün."
     },
     {
      "rect": [
       69.67,
       13.33,
       30.12,
       13.51
      ],
      "pin": [
       69.67,
       13.33
      ],
      "title": "Datenlink-Treffer (Dateien)",
      "text": "Anzahl der Listenzeilen zu dieser Zeichnung."
     },
     {
      "rect": [
       5.2,
       71.53,
       6.72,
       13.51
      ],
      "pin": [
       5.2,
       71.53
      ],
      "title": "Datenlink-Feld Tabelle 2",
      "text": "Rechtsklick auf „Tag“ › „als Datenlink-Feld setzen“."
     },
     {
      "rect": [
       17.82,
       71.53,
       29.02,
       13.51
      ],
      "pin": [
       17.82,
       71.53
      ],
      "title": "Spalten aus der Liste",
      "text": "„Datenlink-Treffer“ (0 = Tag fehlt in der Liste) und alle übergebenen Spalten der Liste; gleichnamige mit „ (Liste)“. Spalten bei Bedarf über Rechtsklick › Spalten … nach vorne holen."
     }
    ]
   },
   {
    "img": "img/wf_link_menu.png",
    "w": 237,
    "h": 101,
    "caption": "Rechtsklick auf einen Spaltenkopf (Ausschnitt mit den Datenlink-Einträgen)",
    "marks": [
     {
      "rect": [
       1.27,
       2.97,
       97.05,
       22.77
      ],
      "pin": [
       1.27,
       2.97
      ],
      "title": "Datenlink-Feld entfernen",
      "text": "Erscheint auf dem gesetzten Feld."
     },
     {
      "rect": [
       1.27,
       51.49,
       97.05,
       22.77
      ],
      "pin": [
       1.27,
       51.49
      ],
      "title": "Als Datenlink-Feld setzen",
      "text": "Auf einer anderen Grundspalte: macht sie zum Datenlink-Feld."
     },
     {
      "rect": [
       1.27,
       25.74,
       97.05,
       22.77
      ],
      "pin": [
       13.08,
       25.74
      ],
      "title": "Datenlink: Importtabelle …",
      "text": "Öffnet die Importtabelle im Kachel-Editor."
     }
    ]
   }
  ]
 },
 {
  "id": "check",
  "title": "Ansehen und prüfen",
  "intro": "PDF in Tabelle 1 wählen, Tags durchgehen, Fundstellen im Viewer prüfen und den Review eintragen.",
  "figs": [
   {
    "img": "img/wf_check_ribbon.png",
    "w": 929,
    "h": 104,
    "caption": "Menüband, Gruppen „2 Ansicht“ und „3 Prüfen“",
    "marks": [
     {
      "rect": [
       8.61,
       26.92,
       7.32,
       65.38
      ],
      "pin": [
       8.61,
       26.92
      ],
      "title": "Alle Tags",
      "text": "Blatt mit den Tags aller PDFs."
     },
     {
      "rect": [
       16.15,
       26.92,
       8.29,
       65.38
      ],
      "pin": [
       16.15,
       26.92
      ],
      "title": "Viewer 2. Monitor",
      "text": "PDF-Viewer in eigenem Fenster."
     },
     {
      "rect": [
       42.84,
       26.92,
       8.18,
       65.38
      ],
      "pin": [
       42.84,
       26.92
      ],
      "title": "Fundstelle weiter",
      "text": "Nächste Fundstelle des gewählten Tags (F3, zurück: Umschalt+F3)."
     },
     {
      "rect": [
       51.24,
       26.92,
       10.01,
       65.38
      ],
      "pin": [
       51.24,
       26.92
      ],
      "title": "Nur doppelte Tags",
      "text": "Nur mehrfach vorkommende Tags (gelb)."
     },
     {
      "rect": [
       61.46,
       26.92,
       10.66,
       65.38
      ],
      "pin": [
       61.46,
       26.92
      ],
      "title": "Nur Projektabweichungen",
      "text": "Nur Tags mit Befund (Projektmodus)."
     },
     {
      "rect": [
       82.35,
       26.92,
       8.5,
       65.38
      ],
      "pin": [
       82.35,
       26.92
      ],
      "title": "Tabelle bearbeiten",
      "text": "Review-Spalten freischalten."
     },
     {
      "rect": [
       91.07,
       26.92,
       7.86,
       65.38
      ],
      "pin": [
       91.07,
       26.92
      ],
      "title": "Review speichern",
      "text": "Review-Einträge sichern (Strg+S)."
     }
    ]
   },
   {
    "img": "img/wf_check.png",
    "w": 2829,
    "h": 430,
    "caption": "Tag-Tabelle mit Leiste und PDF-Viewer",
    "marks": [
     {
      "rect": [
       1.7,
       9.07,
       6.36,
       5.81
      ],
      "pin": [
       1.7,
       9.07
      ],
      "title": "Aus PDF-Scan übernehmen",
      "text": "Ersteller, Checked, Rev … aus dem Schriftfeld als Spalten anfügen."
     },
     {
      "rect": [
       8.2,
       9.07,
       3.53,
       5.81
      ],
      "pin": [
       8.2,
       9.07
      ],
      "title": "Autofill OK",
      "text": "Alle OK-Tags: Review = OK, User, Datum; leeres WPO = Checked."
     },
     {
      "rect": [
       11.88,
       9.07,
       3.5,
       5.81
      ],
      "pin": [
       11.88,
       9.07
      ],
      "title": "Bearbeiten",
      "text": "Review, Änderung, Neuer Wert, Bemerkung, WPO eintragen (Datum/User automatisch)."
     },
     {
      "rect": [
       15.52,
       9.07,
       3.36,
       5.81
      ],
      "pin": [
       15.52,
       9.07
      ],
      "title": "Speichern",
      "text": "Review-Einträge dieser PDF speichern."
     },
     {
      "rect": [
       19.26,
       9.07,
       3.96,
       5.81
      ],
      "pin": [
       19.26,
       9.07
      ],
      "title": "Nur doppelte",
      "text": "Nur Tags, die mehrfach in der PDF stehen."
     },
     {
      "rect": [
       28.49,
       9.07,
       4.84,
       5.81
      ],
      "pin": [
       28.49,
       9.07
      ],
      "title": "Filter zurücksetzen",
      "text": "Alle Filter der Tag-Tabelle aufheben."
     },
     {
      "rect": [
       35.17,
       9.07,
       3.43,
       5.81
      ],
      "pin": [
       35.17,
       9.07
      ],
      "title": "Fundstelle",
      "text": "Zur nächsten Fundstelle springen (◀ zurück)."
     },
     {
      "rect": [
       38.99,
       9.07,
       2.55,
       5.81
      ],
      "pin": [
       38.99,
       9.07
      ],
      "title": "Excel",
      "text": "Tag-Tabelle als Excel sichern (mit Listenspalten)."
     },
     {
      "rect": [
       1.38,
       34.65,
       59.21,
       16.51
      ],
      "pin": [
       1.38,
       34.65
      ],
      "title": "Tag anklicken",
      "text": "Markiert den Tag im Viewer und zoomt hin; gelbe Zeilen = doppelte Tags."
     },
     {
      "rect": [
       61.26,
       0.93,
       38.6,
       7.67
      ],
      "pin": [
       61.26,
       0.93
      ],
      "title": "Viewer-Leiste",
      "text": "Einpassen, Zoom, Drehen, Monochrom, Seiten, Fundstellen, Redline, PDF öffnen, 2. Monitor."
     },
     {
      "rect": [
       61.26,
       9.53,
       38.6,
       89.53
      ],
      "pin": [
       63.8,
       9.53
      ],
      "title": "PDF-Ansicht",
      "text": "Rahmen grün = korrekt, rot = fehlerhaft, gelb = doppelt. Mausrad zoomt, Doppelklick passt ein."
     }
    ]
   }
  ]
 },
 {
  "id": "review",
  "title": "Review und Redline erzeugen",
  "intro": "Ergebnisse als Redline-PDF und Review-Excel ausgeben – für die gewählte PDF oder viele PDFs auf einmal.",
  "figs": [
   {
    "img": "img/wf_review_ribbon.png",
    "w": 317,
    "h": 104,
    "caption": "Menüband, Gruppe „4 Review / Redline“",
    "marks": [
     {
      "rect": [
       3.15,
       26.92,
       33.12,
       65.38
      ],
      "pin": [
       3.15,
       26.92
      ],
      "title": "Review Auswahl/Bulk …",
      "text": "Redline und Review-Excel für markierte oder alle PDFs."
     },
     {
      "rect": [
       36.91,
       26.92,
       29.65,
       65.38
      ],
      "pin": [
       36.91,
       26.92
      ],
      "title": "Redline-PDF gewählte PDF",
      "text": "Kopie der PDF mit Rahmen, Pos.-Nr. und Kommentaren (Tabellenfilter gilt)."
     },
     {
      "rect": [
       67.19,
       26.92,
       29.65,
       65.38
      ],
      "pin": [
       67.19,
       26.92
      ],
      "title": "Review-Excel gewählte PDF",
      "text": "Excel mit einer Zeile je Fundstelle und Prüfstatus."
     }
    ]
   },
   {
    "img": "img/wf_review_dialog.png",
    "w": 560,
    "h": 309,
    "caption": "Review Auswahl/Bulk …",
    "marks": [
     {
      "rect": [
       1.96,
       3.56,
       96.07,
       30.42
      ],
      "pin": [
       1.96,
       3.56
      ],
      "title": "PDFs",
      "text": "Markierte oder alle gescannten PDFs."
     },
     {
      "rect": [
       3.75,
       43.04,
       92.5,
       5.83
      ],
      "pin": [
       3.75,
       43.04
      ],
      "title": "Redline-PDF je PDF",
      "text": "Farben wie im Viewer."
     },
     {
      "rect": [
       3.75,
       50.81,
       92.5,
       5.83
      ],
      "pin": [
       8.75,
       50.81
      ],
      "title": "Review-Excel je PDF",
      "text": "Pos.-Nr., Kommentar, Prüfstatus, Bemerkung."
     },
     {
      "rect": [
       3.75,
       58.58,
       92.5,
       5.83
      ],
      "pin": [
       3.75,
       58.58
      ],
      "title": "Review-Excel gesamt",
      "text": "Eine Mappe über alle gewählten PDFs."
     },
     {
      "rect": [
       13.75,
       74.11,
       65.71,
       8.74
      ],
      "pin": [
       13.75,
       74.11
      ],
      "title": "Zielordner",
      "text": "Wohin geschrieben wird; optional Unterordner mit Zeitstempel."
     },
     {
      "rect": [
       1.96,
       88.03,
       96.07,
       8.41
      ],
      "pin": [
       1.96,
       88.03
      ],
      "title": "Review starten",
      "text": "Erzeugt die Ausgaben; die Original-PDFs bleiben unverändert."
     }
    ]
   }
  ]
 },
 {
  "id": "export",
  "title": "Exportieren und weitergeben",
  "intro": "Gesamtlisten exportieren oder die Ergebnisse über Web-Server bzw. Offline-Bericht teilen. Jede Tabelle hat zusätzlich das Excel-Symbol in ihrer Ecke.",
  "figs": [
   {
    "img": "img/wf_export.png",
    "w": 683,
    "h": 104,
    "caption": "Menüband, Gruppen „5 Export“, „Web“, „Hilfe“",
    "marks": [
     {
      "rect": [
       1.46,
       26.92,
       9.37,
       65.38
      ],
      "pin": [
       1.46,
       26.92
      ],
      "title": "Export Excel …",
      "text": "Blätter „Dateien“ und „Tags“ über alle PDFs."
     },
     {
      "rect": [
       11.13,
       26.92,
       9.37,
       65.38
      ],
      "pin": [
       11.13,
       26.92
      ],
      "title": "Export CSV …",
      "text": "Tags plus _Dateien.csv (Trennzeichen ;)."
     },
     {
      "rect": [
       20.79,
       26.92,
       9.37,
       65.38
      ],
      "pin": [
       20.79,
       26.92
      ],
      "title": "Exportordner",
      "text": "Ordner mit allen Ausgaben öffnen."
     },
     {
      "rect": [
       31.48,
       26.92,
       12.3,
       65.38
      ],
      "pin": [
       31.48,
       26.92
      ],
      "title": "Web-Server",
      "text": "Web-Version für Kollegen im Firmennetz starten/stoppen."
     },
     {
      "rect": [
       56.22,
       26.92,
       10.4,
       65.38
      ],
      "pin": [
       56.22,
       26.92
      ],
      "title": "Offline-Bericht …",
      "text": "Eine HTML-Datei mit Tabellen und Viewer zum Weitergeben."
     },
     {
      "rect": [
       67.94,
       26.92,
       11.27,
       65.38
      ],
      "pin": [
       67.94,
       26.92
      ],
      "title": "Handbuch",
      "text": "Dieses Handbuch."
     }
    ]
   }
  ]
 }
];
