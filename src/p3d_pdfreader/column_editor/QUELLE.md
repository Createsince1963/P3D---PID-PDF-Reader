# Herkunft – nicht von Hand ändern

Kopie des Moduls `column_editor` (Modulversion 0.1.0) aus **P3D - Tag Compliance 0.9.416**
(`...\P3D - Engineering Tools\P3D - Tag Compliance\column_editor`), übernommen am 2026-11-22 mit P3D PDF Reader 1.0.32.

* Wie `main_gui_kit`: hier **nichts von Hand ändern**. Anpassungen an den P3D PDF Reader (deutsches Menüband, Seitenleiste,
  Ladebildschirm, Datenquelle) liegen in `p3d_pdfreader\gui\tile_editor\`.
* Aktualisieren: Ordner aus Tag Compliance neu kopieren (ohne `__pycache__`, Zeitstempel erhalten), danach Tests ausführen.
* QML-Dateien sind in `qml_resources.py` eingebaut (`qml.qrc`). Die EXE braucht QtQml / QtQuick / QtQuickWidgets.
* **Deutsche Texte (seit 1.0.33):** die Anzeigetexte (QML, Meldungen, Verlauf, Dialoge) übersetzt das Werkzeug
  `tools\translate_column_editor.py` per Wörterbuch und baut danach `qml_resources.py` neu. Nach jedem neuen Kopieren aus
  Tag Compliance erneut ausführen; es meldet Texte, die es nicht mehr findet. Neue Übersetzungen nur dort eintragen.
* Einbindung und Schnittstelle: `README_MODULE.md`.
