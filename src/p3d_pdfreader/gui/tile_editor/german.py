"""Deutsche Beschriftung fuer das Menueband des Kachel-Editors.

Das Modul ``column_editor`` ist eine unveraenderte Kopie aus P3D Tag Compliance (englische Texte). Damit die Kopie
unveraendert bleibt, werden die Knoepfe des Menuebands NACH dem Aufbau umbeschriftet (Text, Tooltip, Menues) und die
Bereichsnamen vor dem Aufbau gesetzt. Die QML-Kacheln, Meldungen und Dialoge der Kopie uebersetzt
``tools/translate_column_editor.py`` (seit 1.0.33)."""
from __future__ import annotations

from PySide6.QtWidgets import QToolButton

TABS = {"Home": "Start", "Transform": "Umwandeln", "Add column": "Spalte hinzufügen"}

# englischer Knopftext -> (deutscher Text, deutscher Tooltip)
BUTTONS = {
    "Undo": ("Rückgängig", "Letzte Änderung zurücknehmen (Strg+Z)"),
    "Redo": ("Wiederholen", "Wiederholen (Strg+Y)"),
    "Hide / show": ("Aus-/einblenden", "Gewählte Kachel(n) in der Tabelle ausblenden oder wieder einblenden"),
    "Export yes / no": ("Export ja/nein", "Gewählte Spalte(n) nicht an das Tool übergeben bzw. wieder übergeben"),
    "Group tiles": ("Kacheln gruppieren", "Gewählte Kacheln gruppieren (Name, Block, optional Kopfzeile) (Strg+G)"),
    "Select group": ("Gruppe wählen", "Alle Kacheln der Gruppe der aktiven Kachel wählen"),
    "Ungroup": ("Gruppe auflösen", "Gruppe der gewählten Kachel(n) auflösen; die Kacheln bleiben"),
    "Reset column": ("Spalte zurücksetzen", "Gewählte Spalte auf die Originaleinstellungen zurücksetzen"),
    "Duplicate column": ("Spalte duplizieren", "Kopie der gewählten Spalte anlegen (das Original bleibt)"),
    "Add columns ...": ("Spalten hinzufügen …", "Mehrere leere Spalten auf einmal anlegen (Namen eintippen oder aus Excel einfügen)"),
    "Save as Excel": ("Als Excel speichern", "Die angepasste Liste (nur exportierte Spalten, Reihenfolge, Namen, berechnete "
                                             "Spalten) als Excel-Datei speichern – kompatibel zu „Liste importieren“"),
    "Trim": ("Leerzeichen", "Überzählige Leerzeichen entfernen"),
    "Clean": ("Bereinigen", "Versteckte Zeichen entfernen"),
    "UPPER": ("GROSS", "GROSSBUCHSTABEN"),
    "lower": ("klein", "kleinbuchstaben"),
    "Capitalise": ("Wortanfang", "Jedes Wort Mit Großem Anfangsbuchstaben"),
    "Replace ...": ("Ersetzen …", "Werte ersetzen"),
    "Add text ...": ("Text ergänzen …", "Text vorne/hinten anfügen oder mit Nullen auffüllen"),
    "Pipe size ...": ("Rohrgröße …", "Rohrgröße vereinheitlichen (Zoll / DN)"),
    "Extract": ("Extrahieren", "Einen Teil des Textes übernehmen"),
    "Split ...": ("Teilen …", "Spalte in mehrere Spalten teilen"),
    "Fill down": ("Nach unten füllen", "Wert nach unten in leere Zellen kopieren"),
    "Fill up": ("Nach oben füllen", "Wert nach oben in leere Zellen kopieren"),
    "Fill empty ...": ("Leere füllen …", "Leere Zellen der gewählten Spalte(n) oder der ganzen Gruppe mit einem Wert füllen"),
    "If ... then ...": ("Wenn … dann …", "Neue Spalte aus Regeln: wenn eine Spalte gleich / enthält … dann dieser Wert"),
    "Check list ...": ("Liste prüfen …", "Spalte gegen eine Codeliste prüfen (OK / NICHT IN LISTE)"),
    "From list ...": ("Aus Liste …", "Spalten aus einer anderen Excel-/CSV-Liste über eine passende Spalte holen"),
    "Yes / No column ...": ("Ja/Nein-Spalte …", "Neue logische Spalte (Ja/Nein) hinter der gewählten Kachel"),
    "Index column ...": ("Indexspalte …", "Laufende Nummer (Pos.) als ERSTE Spalte einfügen"),
}
MENU = {"First characters ...": "Erste Zeichen …", "Last characters ...": "Letzte Zeichen …",
        "Text before a separator ...": "Text vor einem Trennzeichen …",
        "Text after a separator ...": "Text nach einem Trennzeichen …",
        "Text between two separators ...": "Text zwischen zwei Trennzeichen …"}
AREAS = ((1, "Nicht exportiert", "notExportedCount"), (2, "Ausgeblendet", "hiddenCount"), (3, "Umbenannt", "renamedCount"))
AREA_KIND = {"Nicht exportiert": "area_not_exported", "Ausgeblendet": "area_hidden", "Umbenannt": "area_renamed"}
NEEDS = {"NEEDS_COLUMN": "Zuerst eine Spalten-Kachel wählen.  ",
         "NEEDS_GROUP": "Zuerst eine Kachel wählen, die in einer Gruppe ist.  ",
         "NEEDS_MULTI": "Zuerst zwei oder mehr Kacheln wählen (Strg+Klick).  "}


def prepare() -> None:
    """Vor dem Aufbau des ersten Kachel-Editors: Bereichsnamen und Hinweistexte deutsch (Modulvariablen, Datei bleibt)."""
    from ...column_editor import ribbon as R
    R.AREAS = AREAS
    R.KIND.update(AREA_KIND)
    for name, value in NEEDS.items():
        setattr(R, name, value)


def translate(ribbon) -> None:
    """Knoepfe, Reiter und Menues eines fertig aufgebauten Menuebands umbeschriften."""
    for i in range(ribbon.tabs.count()):
        ribbon.tabs.setTabText(i, TABS.get(ribbon.tabs.tabText(i), ribbon.tabs.tabText(i)))
    items = []
    for b, tip, needs in ribbon._items:
        de = BUTTONS.get(b.text())
        if de is not None:
            _relabel(b, de[0])
            tip = de[1]
        if b.menu() is not None:
            for act in b.menu().actions():
                act.setText(MENU.get(act.text(), act.text()))
        items.append((b, tip, needs))
    ribbon._items[:] = items
    for b in ribbon.findChildren(QToolButton):          # z. B. Knoepfe, die zweimal vorkommen
        de = BUTTONS.get(b.text())
        if de is not None:
            _relabel(b, de[0])
            b.setToolTip(de[1])
    ribbon.refresh()


def _relabel(b: QToolButton, text: str) -> None:
    b.setText(text)
    b.setAccessibleName(text)
    b.setMinimumSize(max(60, b.fontMetrics().horizontalAdvance(text) + 16), b.minimumHeight())
