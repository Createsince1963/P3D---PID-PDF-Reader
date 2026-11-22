"""Datenlink in der Oberflaeche (Nutzervorgabe 2026-11-22): Excel-Liste importieren, im Kachel-Editor mit Vorschau
bearbeiten, Datenlink 1 und 2 setzen und verknuepft an die Tabellen des Tools uebergeben.

* Anpassen der Liste: Vollfenster ``tile_editor.TileEditorWindow`` (Kachel-Editor aus P3D Tag Compliance, seit
                     1.0.32; vorher ein Dialog mit ``project_tiles``). Datenlink 1/2 per Rechtsklick auf den Tabellenkopf.
* ``LinkController`` im Hauptfenster: je Tool-Tabelle ein Datenlink-Feld per Rechtsklick auf den Spaltenkopf (Kopf
                     dann dunkelgruen), Zusatzspalten aus der Importtabelle.
* ``LinkHeaderPainter`` faerbt die Kopfzellen der Datenlink-Spalten dunkelgruen (passend zum dunkelblauen Kopf).

Farben nur aus ``appearance`` (dunkelgruen = zweite Akzentfarbe der Auswahl ``ACCENT_CHOICES``)."""
from __future__ import annotations

import copy
from typing import Callable

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QApplication, QInputDialog, QMenu, QMessageBox

from ..core.data_link import DataLink, ImportTable, read_sheet, sheet_names
from ..paths import config_dir
from . import appearance, last_paths

LINK_COLOR = appearance.ACCENT_CHOICES[1]      # dunkelgruen (#1B6B5A), passend zum dunkelblauen Tabellenkopf
FIELDS_KEY = "data_link_fields"                # config/state.json: {"files": Spaltenname, "tags": Spaltenname}
IMPORT_DIR = "last_data_link_dir"              # config/state.json: zuletzt gewaehlter Ordner der Importliste
HITS = "Datenlink-Treffer"
TABLE_NAMES = {1: "Tabelle 1 – Dateien", 2: "Tabelle 2 – Tags"}
PREFERRED_SHEET = "Gesamtliste"                # Gesamtliste aus P3D InstrumentationList


def link_marker(n: int) -> str:
    return f"Datenlink {n}"


# ----------------------------------------------------------------------------------------------------------------
# Kopf dunkelgruen
# ----------------------------------------------------------------------------------------------------------------
def import_color() -> QColor:
    """Heller Kopf der Importspalten: Datenlink-Gruen, stark zu Weiss aufgehellt (keine eigene Farbe)."""
    return mix(QColor(LINK_COLOR), QColor("white"), 0.2)


def mix(a: QColor, b: QColor, share_a: float) -> QColor:
    s = max(0.0, min(1.0, share_a))
    return QColor(round(a.red() * s + b.red() * (1 - s)), round(a.green() * s + b.green() * (1 - s)),
                  round(a.blue() * s + b.blue() * (1 - s)))


IMPORT_LABEL = "Import"


class LinkHeaderPainter(QObject):
    """Malt die Kopfzellen der Datenlink-Spalten dunkelgruen mit weisser Schrift. ``columns()`` liefert die logischen
    Spalten; ``bottom`` = Hoehe der Filterzeile unter der Beschriftung (Kit-Tabellen), sonst 0. Laeuft als Ereignis-
    filter: erst zeichnet der Kopf wie immer, dann wird darueber gemalt (Kit-Kopf bleibt unveraendert).

    ``imports()`` (seit 1.0.34) liefert die Spalten, die aus der Importtabelle stammen: heller gruener Kopf mit
    dunkelgruener Schrift und dem Hinweis „Import“ rechts im Kopf."""

    def __init__(self, header, columns: Callable[[], set[int]], bottom: Callable[[], int] = lambda: 0,
                 imports: Callable[[], set[int]] = set):
        super().__init__(header)
        self.header, self.columns, self.bottom, self.imports = header, columns, bottom, imports
        self._busy = False
        header.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):  # noqa: N802
        if event.type() != QEvent.Paint or self._busy:
            return False
        cols, imports = self.columns(), self.imports()
        if not cols and not imports:
            return False
        self._busy = True
        try:
            obj.removeEventFilter(self)
            QApplication.sendEvent(obj, event)              # normaler Kopf
        finally:
            obj.installEventFilter(self)
            self._busy = False
        self._paint(obj, cols, imports - cols)
        return True

    def _paint(self, viewport, cols: set[int], imports: set[int] = frozenset()) -> None:
        h = self.header
        model = h.model()
        if model is None:
            return
        painter = QPainter(viewport)
        try:
            bottom = max(0, int(self.bottom()))
            styles = [(c, False) for c in cols] + [(c, True) for c in imports]
            for c, is_import in styles:
                if c < 0 or c >= h.count() or h.isSectionHidden(c):
                    continue
                x, w = h.sectionViewportPosition(c), h.sectionSize(c)
                rect = viewport.rect().adjusted(0, 0, 0, -bottom)
                rect.setLeft(x)
                rect.setWidth(w - 1)
                painter.fillRect(rect, import_color() if is_import else QColor(LINK_COLOR))
                text = str(model.headerData(c, Qt.Horizontal, Qt.DisplayRole) or "")
                room = max(10, w - 10)
                if is_import:                                   # kleiner Hinweis „Import“ rechts
                    small = h.font()
                    small.setItalic(True)
                    small.setPointSizeF(max(6.0, small.pointSizeF() * 0.8))
                    painter.setFont(small)
                    painter.setPen(QColor(LINK_COLOR))
                    tag_w = painter.fontMetrics().horizontalAdvance(IMPORT_LABEL)
                    if tag_w + 30 < w:
                        painter.drawText(rect.adjusted(0, 0, -5, 0), Qt.AlignRight | Qt.AlignVCenter
                                         | Qt.TextSingleLine, IMPORT_LABEL)
                        room = max(10, w - 16 - tag_w)
                f = h.font()
                f.setBold(True)
                painter.setFont(f)
                painter.setPen(QColor(LINK_COLOR) if is_import else QColor("white"))
                painter.drawText(rect.adjusted(6, 0, -4, 0), Qt.AlignLeft | Qt.AlignVCenter | Qt.TextSingleLine,
                                 painter.fontMetrics().elidedText(text, Qt.ElideRight, room))
        finally:
            painter.end()


def guess_links(table: ImportTable) -> None:
    """Vorschlag fuer die Datenlinks (Gesamtliste: „P&ID No.“ bzw. „DWG Number“ und „Tag“); aendert nichts, wenn
    keine passende Spalte da ist."""
    folded = {h.casefold(): h for h in table.headers}
    if not table.link1:
        table.link1 = next((folded[k] for k in ("p&id no.", "dwg number", "zeichnungsnr.", "zeichnungsnummer")
                            if k in folded), "")
    if not table.link2:
        table.link2 = next((folded[k] for k in ("tag", "tag no.", "tag number") if k in folded), "")


def choose_excel(parent) -> ImportTable | None:
    """Excel-Datei und Blatt waehlen und einlesen (Blatt „Gesamtliste“ wird vorgeschlagen)."""
    files = last_paths.open_files(parent, "Excel-Liste für den Datenlink wählen", "Excel (*.xlsx *.xlsm)",
                                  kind=IMPORT_DIR)
    if not files:
        return None
    path = files[0]
    try:
        names = sheet_names(path)
        sheet = names[0] if names else None
        if len(names) > 1:
            start = names.index(PREFERRED_SHEET) if PREFERRED_SHEET in names else 0
            sheet, ok = QInputDialog.getItem(parent, "Excel-Liste", "Blatt:", names, start, False)
            if not ok:
                return None
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            headers, rows = read_sheet(path, sheet)
        finally:
            QApplication.restoreOverrideCursor()
    except Exception as exc:  # noqa: BLE001 - jede Lesestoerung als Meldung
        QMessageBox.warning(parent, "Excel-Liste", f"Die Datei ließ sich nicht lesen:\n{exc}")
        return None
    table = ImportTable(source=str(path), sheet=sheet or "", headers=headers, rows=rows)
    guess_links(table)
    return table


# ----------------------------------------------------------------------------------------------------------------
# Hauptfenster: Datenlink-Felder der Tabellen und Zusatzspalten
# ----------------------------------------------------------------------------------------------------------------
def load_fields() -> dict[str, str]:
    value = last_paths.get_value(FIELDS_KEY, {})
    return {k: str(v) for k, v in value.items() if v} if isinstance(value, dict) else {}


class LinkController:
    """Haelt Importtabelle, Datenlink-Felder und die daraus gebaute Verknuepfung. ``on_change`` baut die Tabellen
    des Hauptfensters neu auf."""

    def __init__(self, on_change: Callable[[], None], on_open: Callable[[], None] = lambda: None):
        self.on_change, self.on_open = on_change, on_open
        self.table = ImportTable.load(config_dir())
        self.fields = load_fields()
        self.link: DataLink | None = None
        self._build()

    def _build(self) -> None:
        self.link = DataLink(self.table, self.fields) if self.table is not None else None

    # --- Spalten ---------------------------------------------------------------------------------------------------
    def active(self, n: int) -> bool:
        return self.link is not None and self.link.active(n)

    def _extra(self, taken: list[str]) -> list[str]:
        """Treffer + exportierte Spalten der Importtabelle (Anpassung im Kachel-Editor); Namensgleichheit mit einer
        Tool-Spalte -> „ (Liste)“."""
        out = [HITS]
        for name in self.link.columns:
            label = name
            while label in taken or label in out:
                label += " (Liste)"
            out.append(label)
        return out

    def file_extra(self, taken: list[str] = ()) -> list[str]:
        """Zusatzspalten der Dateiliste (seit 1.0.35 wie die Tag-Tabelle mit allen exportierten Listenspalten)."""
        return self._extra(list(taken)) if self.active(1) else []

    def tag_extra(self, taken: list[str]) -> list[str]:
        """Zusatzspalten der Tag-Tabelle: Treffer + uebergebene Spalten (Namensgleichheit -> „ (Liste)“)."""
        return self._extra(taken) if self.active(2) else []

    def file_values(self, value) -> list:
        if not self.active(1):
            return []
        rows = self.link.file_rows(value)
        return [len(rows), *self.link.values(rows)]

    def tag_values(self, value, file_value=None) -> list:
        if not self.active(2):
            return []
        rows = self.link.tag_rows(value, file_value if self.active(1) else None)
        return [len(rows), *self.link.values(rows)]

    # --- Rechtsklick auf den Spaltenkopf --------------------------------------------------------------------------
    def install(self, key: str, data_table, base: list[str]) -> None:
        """Rechtsklick-Eintrag „Als Datenlink-Feld setzen“ (nur Grundspalten ``base``) und gruener Kopf."""
        from .sheet import _filter_height
        view = data_table.table
        n = 1 if key == "files" else 2

        def hook(menu: QMenu, logical: int) -> None:
            headers = data_table.headers
            if logical < 0 or logical >= len(headers):
                return
            name = headers[logical]
            menu.addSeparator()
            current = self.fields.get(key, "")
            if name == current:
                menu.addAction(f"Datenlink-Feld entfernen ({TABLE_NAMES[n]})",
                               lambda: self.set_field(key, ""))
            else:
                act = menu.addAction(f"„{name}“ als Datenlink-Feld setzen (Datenlink {n})",
                                     lambda: self.set_field(key, name))
                act.setEnabled(name in base)
            menu.addAction("Datenlink: Importtabelle …", self.on_open)

        view._shared_header_menu_hook = hook
        LinkHeaderPainter(view.horizontalHeader(), lambda: self._field_columns(key, data_table), _filter_height,
                          lambda: set(range(len(base), len(data_table.headers))))

    def _field_columns(self, key: str, data_table) -> set[int]:
        name = self.fields.get(key, "")
        return {data_table.headers.index(name)} if name in data_table.headers else set()

    def set_field(self, key: str, name: str) -> None:
        if name:
            self.fields[key] = name
        else:
            self.fields.pop(key, None)
        last_paths.set_value(FIELDS_KEY, dict(self.fields))
        self._build()
        self.on_change()

    # --- Import ----------------------------------------------------------------------------------------------------
    def edit(self, parent, new: bool = False) -> bool:
        """Importtabelle neu einlesen (``new``) oder die vorhandene bearbeiten; True nach „Übernehmen“."""
        table = None if new else self.table
        if table is None:
            table = choose_excel(parent)
            if table is None:
                return False
        else:
            table = copy.deepcopy(table)              # Abbrechen laesst die gespeicherte Tabelle unveraendert
        from .tile_editor import TileEditorWindow
        win = TileEditorWindow(table, parent)
        if not win.run():
            return False
        self.table = win.result
        self.table.save(config_dir())
        self._build()
        self.on_change()
        return True

    def remove(self) -> None:
        ImportTable.remove(config_dir())
        self.table = None
        self._build()
        self.on_change()

    def summary(self) -> str:
        if self.table is None:
            return "Keine Importtabelle."
        t = self.table
        parts = [f"{len(t.rows)} Zeilen aus {t.source}" + (f" (Blatt „{t.sheet}“)" if t.sheet else "")]
        for n, key in ((1, "files"), (2, "tags")):
            field = self.fields.get(key, "")
            state = "aktiv" if self.active(n) else "inaktiv"
            parts.append(f"Datenlink {n}: „{t.link(n) or '–'}“ ↔ {TABLE_NAMES[n]} „{field or '–'}“ ({state})")
        return "\n".join(parts)
