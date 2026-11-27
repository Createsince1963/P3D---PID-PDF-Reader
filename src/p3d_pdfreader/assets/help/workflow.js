/* Erzeugt von tools/make_help_workflow.py - nicht von Hand bearbeiten. */
const WF = [
 {
  "id": "overview",
  "title": "Überblick – das Hauptfenster",
  "intro": "So ist das Fenster aufgebaut. Die Gruppen im Menüband entsprechen den Arbeitsschritten; ein Klick auf die dunkelblaue Gruppenüberschrift klappt eine Gruppe ein oder aus.",
  "figs": [
   {
    "img": "img/wf_overview.png",
    "w": 3086,
    "h": 1180,
    "caption": "Hauptfenster mit Beispiel-PDFs",
    "marks": [
     {
      "rect": [
       0.26,
       4.07,
       19.38,
       1.61
      ],
      "pin": [
       0.26,
       4.07
      ],
      "title": "Menüband: Projekt",
      "text": "Projekt wählen, Projektmodus, Rohrleitungen, Projektdefinitionen, Pfade, Einstellungen."
     },
     {
      "rect": [
       19.93,
       4.07,
       10.08,
       1.61
      ],
      "pin": [
       19.93,
       4.07
      ],
      "title": "Menüband: 1 Einlesen",
      "text": "PDFs einlesen und Excel-Liste für den Datenlink importieren."
     },
     {
      "rect": [
       30.3,
       4.07,
       12.09,
       1.61
      ],
      "pin": [
       30.3,
       4.07
      ],
      "title": "Menüband: 2 Ansicht",
      "text": "Blätter wechseln, Viewer auf den 2. Monitor, Tabellen-Vorschau."
     },
     {
      "rect": [
       42.68,
       4.07,
       24.95,
       1.61
      ],
      "pin": [
       42.68,
       4.07
      ],
      "title": "Menüband: 3 Prüfen",
      "text": "Fundstellen, Filter, Tabelle bearbeiten, Review speichern."
     },
     {
      "rect": [
       67.92,
       4.07,
       9.62,
       1.61
      ],
      "pin": [
       67.92,
       4.07
      ],
      "title": "Menüband: 4 Review / Redline",
      "text": "Redline-PDF und Review-Excel erzeugen."
     },
     {
      "rect": [
       77.84,
       4.07,
       6.35,
       1.61
      ],
      "pin": [
       77.84,
       4.07
      ],
      "title": "Menüband: 5 Export",
      "text": "Alle Dateien und Tags als Excel oder CSV."
     },
     {
      "rect": [
       84.48,
       4.07,
       7.78,
       1.61
      ],
      "pin": [
       84.48,
       4.07
      ],
      "title": "Menüband: Web",
      "text": "Web-Server für Kollegen, Offline-Bericht."
     },
     {
      "rect": [
       92.55,
       4.07,
       6.77,
       1.61
      ],
      "pin": [
       92.55,
       4.07
      ],
      "title": "Menüband: Hilfe",
      "text": "Dieses Handbuch, Info und Sprache."
     },
     {
      "rect": [
       0.03,
       14.49,
       99.94,
       3.64
      ],
      "pin": [
       0.03,
       14.49
      ],
      "title": "Kopfband",
      "text": "Projekt, Quelle, Anzahl PDFs, Tags, Fehler und (Projektmodus) Abweichungen."
     },
     {
      "rect": [
       0.36,
       18.81,
       99.29,
       28.73
      ],
      "pin": [
       2.9,
       18.81
      ],
      "title": "Tabelle 1 – Dateien",
      "text": "Eine Zeile je PDF mit Schriftfeld-Werten. Auswahl einer Zeile lädt Tags und PDF."
     },
     {
      "rect": [
       0.36,
       47.97,
       65.17,
       49.75
      ],
      "pin": [
       0.36,
       47.97
      ],
      "title": "Tabelle 2 – Tags der gewählten PDF",
      "text": "Alle Tags mit Anzahl, Seiten, Review-Spalten und – mit Datenlink – Spalten aus der Excel-Liste."
     },
     {
      "rect": [
       65.68,
       47.97,
       33.96,
       49.75
      ],
      "pin": [
       65.68,
       47.97
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
  "id": "paths",
  "title": "Pfade festlegen",
  "intro": "Einmal einstellen: wo die PDFs liegen und wohin die Ausgaben gehen.",
  "figs": [
   {
    "img": "img/wf_paths.png",
    "w": 720,
    "h": 460,
    "caption": "Projekt › Pfade",
    "marks": [
     {
      "rect": [
       0.0,
       0.0,
       100.0,
       50.0
      ],
      "pin": [
       0.0,
       0.0
      ],
      "title": "Quell- und Exportordner",
      "text": "Quellordner hinzufügen oder entfernen und den Exportordner wählen. „Quellordner scannen“ (F5) liest die Quellordner ein."
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
    "w": 3072,
    "h": 347,
    "caption": "Tabelle 1 – Dateien nach dem Einlesen",
    "marks": [
     {
      "rect": [
       13.22,
       2.31,
       13.9,
       7.78
      ],
      "pin": [
       13.22,
       2.31
      ],
      "title": "Blattfilter",
      "text": "Sucht in allen Spalten der Dateiliste."
     },
     {
      "rect": [
       2.08,
       2.59,
       3.81,
       7.2
      ],
      "pin": [
       2.08,
       2.59
      ],
      "title": "Alle markieren",
      "text": "Alle PDFs markieren, z. B. für den Review."
     },
     {
      "rect": [
       6.02,
       2.59,
       4.59,
       7.2
      ],
      "pin": [
       6.02,
       2.59
      ],
      "title": "Review markierte …",
      "text": "Redline und Review-Excel für die markierten PDFs (Schritt 6)."
     },
     {
      "rect": [
       1.11,
       12.97,
       98.7,
       21.61
      ],
      "pin": [
       8.74,
       12.97
      ],
      "title": "Spaltenkopf mit Filterzeile",
      "text": "Klick sortiert, Feld darunter filtert, Doppelklick im Feld wählt Werte. Rechtsklick: Spaltenmenü."
     },
     {
      "rect": [
       1.11,
       34.58,
       98.7,
       20.46
      ],
      "pin": [
       1.11,
       34.58
      ],
      "title": "PDF wählen",
      "text": "Zeile anklicken: Tag-Tabelle und Viewer zeigen diese PDF. Mehrere mit Strg- oder Umschalt-Klick markieren."
     },
     {
      "rect": [
       0.13,
       91.07,
       13.22,
       7.78
      ],
      "pin": [
       0.13,
       91.07
      ],
      "title": "Tabellenansicht",
      "text": "Ansicht speichern, laden, zurücksetzen; der Regler rechts zoomt."
     },
     {
      "rect": [
       13.48,
       91.07,
       16.15,
       7.78
      ],
      "pin": [
       13.48,
       91.07
      ],
      "title": "Filter der Tag-Tabelle",
      "text": "Sucht in allen Spalten der Tags der gewählten PDF."
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
       2.21,
       49.67,
       17.38,
       8.33
      ],
      "pin": [
       2.21,
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
    "w": 3072,
    "h": 582,
    "caption": "Datenlink-Felder gesetzt: Köpfe dunkelgrün, Listenspalten angefügt",
    "marks": [
     {
      "rect": [
       7.81,
       7.73,
       6.02,
       12.89
      ],
      "pin": [
       7.81,
       7.73
      ],
      "title": "Datenlink-Feld Tabelle 1",
      "text": "Rechtsklick auf „Zeichnungsnr.“ › „als Datenlink-Feld setzen“ – der Kopf wird dunkelgrün."
     },
     {
      "rect": [
       4.62,
       72.85,
       6.18,
       12.89
      ],
      "pin": [
       4.62,
       72.85
      ],
      "title": "Datenlink-Feld Tabelle 2",
      "text": "Rechtsklick auf „Tag“ › „als Datenlink-Feld setzen“."
     },
     {
      "rect": [
       16.24,
       72.85,
       29.98,
       12.89
      ],
      "pin": [
       16.24,
       72.85
      ],
      "title": "Spalten aus der Liste",
      "text": "„Datenlink-Treffer“ (0 = Tag fehlt in der Liste) und alle übergebenen Spalten der Liste; gleichnamige mit „ (Liste)“. Spalten bei Bedarf über Rechtsklick › Spalten … nach vorne holen."
     }
    ]
   },
   {
    "img": "img/wf_link_menu.png",
    "w": 237,
    "h": 150,
    "caption": "Rechtsklick auf einen Spaltenkopf (Ausschnitt mit den Datenlink-Einträgen)",
    "marks": [
     {
      "rect": [
       1.27,
       2.0,
       97.05,
       15.33
      ],
      "pin": [
       1.27,
       2.0
      ],
      "title": "Datenlink-Feld entfernen",
      "text": "Erscheint auf dem gesetzten Feld."
     },
     {
      "rect": [
       1.27,
       34.67,
       97.05,
       15.33
      ],
      "pin": [
       1.27,
       34.67
      ],
      "title": "Als Datenlink-Feld setzen",
      "text": "Auf einer anderen Grundspalte: macht sie zum Datenlink-Feld."
     },
     {
      "rect": [
       1.27,
       17.33,
       97.05,
       15.33
      ],
      "pin": [
       13.08,
       17.33
      ],
      "title": "Datenlink: Importtabelle …",
      "text": "Öffnet die Importtabelle im Kachel-Editor."
     }
    ]
   }
  ]
 },
 {
  "id": "listcheck",
  "title": "PDF-Tags mit der Liste abgleichen",
  "intro": "Nach dem Setzen der Datenlink-Felder: Treffer ansehen, Richtung wählen und das Prüfblatt öffnen.",
  "figs": [
   {
    "img": "img/wf_listcheck.png",
    "w": 2019,
    "h": 520,
    "caption": "Leisten der Tag-Tabelle: Abgleich mit der Importliste",
    "marks": [
     {
      "rect": [
       46.9,
       1.54,
       5.7,
       4.81
      ],
      "pin": [
       46.9,
       1.54
      ],
      "title": "Importspalten",
      "text": "Spalten der Liste ein- oder ausblenden."
     },
     {
      "rect": [
       52.8,
       1.54,
       4.95,
       4.81
      ],
      "pin": [
       52.8,
       1.54
      ],
      "title": "Importliste",
      "text": "Link aufheben, Liste neu einlesen, bearbeiten, entfernen."
     },
     {
      "rect": [
       57.95,
       1.54,
       4.46,
       4.81
      ],
      "pin": [
       57.95,
       1.54
      ],
      "title": "Abgleich",
      "text": "Richtung wählen: PDF → Liste, Liste → PDF oder beide. Fehlendes = „n.a.“."
     },
     {
      "rect": [
       24.72,
       15.38,
       7.13,
       14.42
      ],
      "pin": [
       24.72,
       15.38
      ],
      "title": "Datenlink-Treffer",
      "text": "0 = Tag fehlt in der Liste. Der Bindestrich zwischen Kürzel und Nummer zählt nicht (FV-501 passt zu FV501)."
     }
    ]
   },
   {
    "img": "img/wf_listcheck_ribbon.png",
    "w": 790,
    "h": 104,
    "caption": "Menüband, Gruppe „3 Prüfen“",
    "marks": [
     {
      "rect": [
       57.22,
       26.92,
       10.0,
       65.38
      ],
      "pin": [
       57.22,
       26.92
      ],
      "title": "Review Importliste",
      "text": "Blatt mit dem Prüfergebnis über alle PDFs."
     }
    ]
   },
   {
    "img": "img/wf_listcheck_sheet.png",
    "w": 1297,
    "h": 520,
    "caption": "Blatt „Review Importliste“",
    "marks": [
     {
      "rect": [
       0.31,
       0.77,
       99.69,
       8.27
      ],
      "pin": [
       0.31,
       0.77
      ],
      "title": "Zählung",
      "text": "Anzahl je Prüfergebnis."
     },
     {
      "rect": [
       3.77,
       31.35,
       20.0,
       23.08
      ],
      "pin": [
       3.77,
       31.35
      ],
      "title": "Prüfergebnis je Zeile",
      "text": "OK, Nicht in Liste, Fehlt im PDF, Zeichnung nicht gescannt."
     }
    ]
   }
  ]
 },
 {
  "id": "types",
  "title": "Prüftypen wählen (Vorfilter)",
  "intro": "Vor der Prüfung festlegen, ob alles oder nur z. B. Equipment oder Instrument geprüft wird. Der Filter gilt auch für Redline, Review-Excel, Bulk und Export.",
  "figs": [
   {
    "img": "img/wf_types_ribbon.png",
    "w": 790,
    "h": 104,
    "caption": "Menüband, Gruppe „3 Prüfen“",
    "marks": [
     {
      "rect": [
       1.27,
       26.92,
       11.14,
       65.38
      ],
      "pin": [
       1.27,
       26.92
      ],
      "title": "Prüftypen",
      "text": "Öffnet die Optionstabelle."
     }
    ]
   },
   {
    "img": "img/wf_types_dialog.png",
    "w": 640,
    "h": 460,
    "caption": "Optionstabelle „Prüftypen“ (Beispiel: nur Instrument)",
    "marks": [
     {
      "rect": [
       2.03,
       14.35,
       9.38,
       39.13
      ],
      "pin": [
       2.03,
       14.35
      ],
      "title": "Haken je Typ",
      "text": "Nur angehakte Typen werden geprüft und ausgegeben."
     },
     {
      "rect": [
       11.41,
       14.35,
       55.31,
       6.52
      ],
      "pin": [
       11.41,
       14.35
      ],
      "title": "Doppelklick auf eine Zeile",
      "text": "Prüft nur diesen Typ."
     },
     {
      "rect": [
       66.72,
       7.17,
       15.62,
       7.17
      ],
      "pin": [
       66.72,
       7.17
      ],
      "title": "Anzahl Tags und PDFs",
      "text": "Wie oft der Typ in den gescannten PDFs vorkommt."
     },
     {
      "rect": [
       1.72,
       91.96,
       96.56,
       5.65
      ],
      "pin": [
       1.72,
       91.96
      ],
      "title": "OK",
      "text": "Übernimmt die Auswahl; die Kopfzeile nennt die geprüften Typen."
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
    "w": 1172,
    "h": 104,
    "caption": "Menüband, Gruppen „2 Ansicht“ und „3 Prüfen“",
    "marks": [
     {
      "rect": [
       6.83,
       26.92,
       5.8,
       65.38
      ],
      "pin": [
       6.83,
       26.92
      ],
      "title": "Alle Tags",
      "text": "Blatt mit den Tags aller PDFs."
     },
     {
      "rect": [
       12.8,
       26.92,
       6.57,
       65.38
      ],
      "pin": [
       12.8,
       26.92
      ],
      "title": "Viewer 2. Monitor",
      "text": "PDF-Viewer in eigenem Fenster."
     },
     {
      "rect": [
       47.78,
       26.92,
       6.48,
       65.38
      ],
      "pin": [
       47.78,
       26.92
      ],
      "title": "Fundstelle weiter",
      "text": "Nächste Fundstelle des gewählten Tags (F3, zurück: Umschalt+F3)."
     },
     {
      "rect": [
       54.44,
       26.92,
       7.94,
       65.38
      ],
      "pin": [
       54.44,
       26.92
      ],
      "title": "Nur doppelte Tags",
      "text": "Nur mehrfach vorkommende Tags (gelb)."
     },
     {
      "rect": [
       62.54,
       26.92,
       8.45,
       65.38
      ],
      "pin": [
       62.54,
       26.92
      ],
      "title": "Nur Projektabweichungen",
      "text": "Nur Tags mit Befund (Projektmodus)."
     },
     {
      "rect": [
       86.01,
       26.92,
       6.74,
       65.38
      ],
      "pin": [
       86.01,
       26.92
      ],
      "title": "Tabelle bearbeiten",
      "text": "Review-Spalten freischalten."
     },
     {
      "rect": [
       92.92,
       26.92,
       6.23,
       65.38
      ],
      "pin": [
       92.92,
       26.92
      ],
      "title": "Review speichern",
      "text": "Review-Einträge sichern (Strg+S)."
     }
    ]
   },
   {
    "img": "img/wf_check.png",
    "w": 3072,
    "h": 595,
    "caption": "Tag-Tabelle mit Leiste und PDF-Viewer",
    "marks": [
     {
      "rect": [
       1.56,
       1.34,
       5.86,
       4.2
      ],
      "pin": [
       1.56,
       1.34
      ],
      "title": "Aus PDF-Scan übernehmen",
      "text": "Ersteller, Checked, Rev … aus dem Schriftfeld als Spalten anfügen."
     },
     {
      "rect": [
       7.55,
       1.34,
       3.26,
       4.2
      ],
      "pin": [
       7.55,
       1.34
      ],
      "title": "Autofill OK",
      "text": "Alle OK-Tags: Review = OK, User, Datum; leeres WPO = Checked."
     },
     {
      "rect": [
       10.94,
       1.34,
       3.22,
       4.2
      ],
      "pin": [
       10.94,
       1.34
      ],
      "title": "Bearbeiten",
      "text": "Review, Änderung, Neuer Wert, Bemerkung, WPO eintragen (Datum/User automatisch)."
     },
     {
      "rect": [
       14.29,
       1.34,
       3.09,
       4.2
      ],
      "pin": [
       14.29,
       1.34
      ],
      "title": "Speichern",
      "text": "Review-Einträge dieser PDF speichern."
     },
     {
      "rect": [
       17.74,
       1.34,
       3.65,
       4.2
      ],
      "pin": [
       17.74,
       1.34
      ],
      "title": "Nur doppelte",
      "text": "Nur Tags, die mehrfach in der PDF stehen."
     },
     {
      "rect": [
       26.24,
       1.34,
       4.46,
       4.2
      ],
      "pin": [
       26.24,
       1.34
      ],
      "title": "Filter zurücksetzen",
      "text": "Alle Filter der Tag-Tabelle aufheben."
     },
     {
      "rect": [
       42.71,
       1.34,
       3.16,
       4.2
      ],
      "pin": [
       42.71,
       1.34
      ],
      "title": "Fundstelle",
      "text": "Zur nächsten Fundstelle springen (◀ zurück)."
     },
     {
      "rect": [
       46.22,
       1.34,
       2.34,
       4.2
      ],
      "pin": [
       46.22,
       1.34
      ],
      "title": "Excel",
      "text": "Tag-Tabelle als Excel sichern (mit Listenspalten)."
     },
     {
      "rect": [
       48.7,
       1.34,
       2.99,
       4.2
      ],
      "pin": [
       51.24,
       1.34
      ],
      "title": "Vorschau",
      "text": "Excel-Export vorher ansehen."
     },
     {
      "rect": [
       1.11,
       26.05,
       64.03,
       11.93
      ],
      "pin": [
       1.11,
       26.05
      ],
      "title": "Tag anklicken",
      "text": "Markiert den Tag im Viewer und zoomt hin; gelbe Zeilen = doppelte Tags."
     },
     {
      "rect": [
       65.76,
       0.67,
       34.11,
       5.55
      ],
      "pin": [
       65.76,
       0.67
      ],
      "title": "Viewer-Leiste",
      "text": "Einpassen, Zoom, Drehen, Monochrom, Seiten, Fundstellen, Redline, PDF öffnen, 2. Monitor."
     },
     {
      "rect": [
       65.76,
       13.11,
       34.11,
       86.22
      ],
      "pin": [
       70.85,
       13.11
      ],
      "title": "PDF-Ansicht",
      "text": "Rahmen grün = korrekt, rot = fehlerhaft, gelb = doppelt. Mausrad zoomt, Doppelklick passt ein."
     }
    ]
   }
  ]
 },
 {
  "id": "twotag",
  "title": "Doppelt angelegte Tags (2TAG)",
  "intro": "Wenn ein Tag in Plant 3D zweimal existiert, passt der Wert der Datenbank (PI-100?) nicht zur PDF (PI-100). 2TAG schließt diese Lücke und weist darauf hin.",
  "figs": [
   {
    "img": "img/wf_twotag.png",
    "w": 2019,
    "h": 520,
    "caption": "2TAG eingeschaltet",
    "marks": [
     {
      "rect": [
       3.52,
       8.65,
       3.62,
       4.81
      ],
      "pin": [
       3.52,
       8.65
      ],
      "title": "2TAG einschalten",
      "text": "Plant 3D schreibt doppelt angelegte Tags mit „?“ am Ende in die Datenbank. Mit 2TAG werden auch diese Zeilen verknüpft."
     },
     {
      "rect": [
       7.03,
       29.81,
       9.36,
       4.23
      ],
      "pin": [
       7.03,
       29.81
      ],
      "title": "Hellgelbe Tag-Zelle",
      "text": "„Multi Tag Eintrag in Projekt“: der Tooltip nennt die andere PID. Zählt unter „Nur Abweichungen“."
     },
     {
      "rect": [
       24.72,
       15.38,
       7.13,
       14.42
      ],
      "pin": [
       24.72,
       15.38
      ],
      "title": "Treffer",
      "text": "Zeigt beide Listenzeilen (mit und ohne „?“)."
     }
    ]
   }
  ]
 },
 {
  "id": "multitag",
  "title": "Doppelte Tags in der PDF kommentieren",
  "intro": "Einträge ansehen, bei Bedarf verschieben und die kommentierte Kopie erzeugen. Das Original bleibt unverändert.",
  "figs": [
   {
    "img": "img/wf_multitag_bar.png",
    "w": 2019,
    "h": 150,
    "caption": "Leiste „Multi Tag“ über der Tag-Tabelle",
    "marks": [
     {
      "rect": [
       7.33,
       30.0,
       5.79,
       16.67
      ],
      "pin": [
       7.33,
       30.0
      ],
      "title": "Multi-Tag-PDF",
      "text": "Kopie der PDF (gewählte oder alle) mit rotem Eintrag je doppeltem Tag."
     },
     {
      "rect": [
       13.32,
       30.0,
       5.65,
       16.67
      ],
      "pin": [
       13.32,
       30.0
      ],
      "title": "Reviewtabelle",
      "text": "Hängt Seiten mit allen Reviewpunkten an (Spalten wie in der Tag-Tabelle)."
     }
    ]
   },
   {
    "img": "img/wf_multitag_viewer.png",
    "w": 1056,
    "h": 595,
    "caption": "PDF-Viewer mit „Kommentare bearbeiten“",
    "marks": [
     {
      "rect": [
       6.72,
       7.56,
       15.62,
       4.2
      ],
      "pin": [
       6.72,
       7.56
      ],
      "title": "Kommentare bearbeiten",
      "text": "Zeigt die roten Einträge über der PDF."
     },
     {
      "rect": [
       36.36,
       30.42,
       27.46,
       13.78
      ],
      "pin": [
       36.36,
       30.42
      ],
      "title": "Eintrag ziehen",
      "text": "Mit der Maus verschieben; Rechtsklick setzt die Position zurück. Gilt für die Multi-Tag-PDF."
     },
     {
      "rect": [
       33.62,
       1.34,
       10.13,
       4.2
      ],
      "pin": [
       33.62,
       1.34
      ],
      "title": "Monochrom",
      "text": "Eingeschaltet wird auch die ausgegebene PDF schwarz-weiß; Review-Elemente bleiben farbig."
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
    "h": 333,
    "caption": "Review Auswahl/Bulk …",
    "marks": [
     {
      "rect": [
       1.96,
       3.3,
       96.07,
       28.23
      ],
      "pin": [
       1.96,
       3.3
      ],
      "title": "PDFs",
      "text": "Markierte oder alle gescannten PDFs."
     },
     {
      "rect": [
       3.75,
       39.94,
       92.5,
       5.41
      ],
      "pin": [
       3.75,
       39.94
      ],
      "title": "Redline-PDF je PDF",
      "text": "Farben wie im Viewer."
     },
     {
      "rect": [
       3.75,
       47.15,
       92.5,
       5.41
      ],
      "pin": [
       8.75,
       47.15
      ],
      "title": "Multi-Tag-PDF je PDF",
      "text": "Roter Eintrag über jedem doppelten Tag (braucht Datenlink 2)."
     },
     {
      "rect": [
       3.75,
       54.35,
       92.5,
       5.41
      ],
      "pin": [
       3.75,
       54.35
      ],
      "title": "Review-Excel je PDF",
      "text": "Pos.-Nr., Kommentar, Prüfstatus, Bemerkung."
     },
     {
      "rect": [
       3.75,
       61.56,
       92.5,
       5.41
      ],
      "pin": [
       8.75,
       61.56
      ],
      "title": "Review-Excel gesamt",
      "text": "Eine Mappe über alle gewählten PDFs."
     },
     {
      "rect": [
       13.75,
       75.98,
       65.71,
       8.11
      ],
      "pin": [
       13.75,
       75.98
      ],
      "title": "Zielordner",
      "text": "Wohin geschrieben wird; optional Unterordner mit Zeitstempel."
     },
     {
      "rect": [
       1.96,
       88.89,
       96.07,
       7.81
      ],
      "pin": [
       1.96,
       88.89
      ],
      "title": "Review starten",
      "text": "Erzeugt die Ausgaben; die Original-PDFs bleiben unverändert."
     }
    ]
   }
  ]
 },
 {
  "id": "preview",
  "title": "Excel-Export vorher ansehen",
  "intro": "Bei allen anderen Tabellen: Rechtsklick auf das Excel-Symbol in der Ecke › „Vorschau ansehen“.",
  "figs": [
   {
    "img": "img/wf_preview_bar.png",
    "w": 2019,
    "h": 150,
    "caption": "Leiste der Tag-Tabelle",
    "marks": [
     {
      "rect": [
       74.1,
       5.33,
       4.56,
       16.67
      ],
      "pin": [
       74.1,
       5.33
      ],
      "title": "Vorschau",
      "text": "Zeigt den Excel-Export vorher an."
     },
     {
      "rect": [
       70.33,
       5.33,
       3.57,
       16.67
      ],
      "pin": [
       70.33,
       5.33
      ],
      "title": "Excel",
      "text": "Direkt sichern, ohne Vorschau."
     }
    ]
   },
   {
    "img": "img/wf_preview_dialog.png",
    "w": 1100,
    "h": 520,
    "caption": "Vorschau des Excel-Exports",
    "marks": [
     {
      "rect": [
       1.0,
       5.96,
       98.0,
       85.77
      ],
      "pin": [
       1.0,
       5.96
      ],
      "title": "Tabelle wie in der Datei",
      "text": "Spalten, Reihenfolge, Breiten und Farben der Ansicht."
     },
     {
      "rect": [
       1.0,
       92.88,
       98.0,
       5.0
      ],
      "pin": [
       1.0,
       92.88
      ],
      "title": "Als Excel sichern …",
      "text": "Speichert die ganze Tabelle (die Vorschau zeigt höchstens 500 Zeilen)."
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
 },
 {
  "id": "tables",
  "title": "Mit Tabellen arbeiten",
  "intro": "Diese Bedienung gilt für alle Tabellen des Tools.",
  "figs": [
   {
    "img": "img/wf_tables.png",
    "w": 2019,
    "h": 595,
    "caption": "Standardfunktionen jeder Tabelle",
    "marks": [
     {
      "rect": [
       0.3,
       13.45,
       1.39,
       12.61
      ],
      "pin": [
       0.3,
       13.45
      ],
      "title": "Excel-Symbol",
      "text": "Klick: sichern. Rechtsklick: Vorschau ansehen."
     },
     {
      "rect": [
       7.03,
       13.45,
       9.41,
       12.61
      ],
      "pin": [
       7.03,
       13.45
      ],
      "title": "Spaltenkopf",
      "text": "Klick sortiert, Feld darunter filtert, Doppelklick im Feld wählt Werte, Rechtsklick öffnet das Spaltenmenü."
     },
     {
      "rect": [
       1.68,
       26.05,
       15.85,
       15.46
      ],
      "pin": [
       1.68,
       26.05
      ],
      "title": "Zellen markieren",
      "text": "Wie in Excel ziehen; Strg+C kopiert, Strg+V fügt in Review-Spalten ein."
     },
     {
      "rect": [
       0.2,
       94.96,
       90.0,
       4.37
      ],
      "pin": [
       0.2,
       94.96
      ],
      "title": "Ansicht speichern",
      "text": "Save / Load / Reset Layout."
     }
    ]
   }
  ]
 }
];
