"""Datenlink in der Oberflaeche (Nutzervorgabe 2026-11-22): Excel-Liste importieren, im Kachel-Editor mit Vorschau
bearbeiten, Datenlink 1 und 2 setzen und verknuepft an die Tabellen des Tools uebergeben.

* ``ImportDialog``   Vorschau der Importtabelle (schnelles Modell, auch fuer 1500 Zeilen x 300 Spalten) mit dem
                     Kachel-Editor aus ``project_tiles``: Spalten verschieben, ein-/ausblenden (= nicht uebergeben),
                     umbenennen, einfuegen, loeschen; Zellen bearbeiten. Rechtsklick auf Spaltenkopf oder Kachel:
                     „Als Datenlink 1/2 setzen“.
* ``LinkController`` im Hauptfenster: je Tool-Tabelle ein Datenlink-Feld per Rechtsklick auf den Spaltenkopf (Kopf
                     dann dunkelgruen), Zusatzspalten aus der Importtabelle.
* ``LinkHeaderPainter`` faerbt die Kopfzellen der Datenlink-Spalten dunkelgruen (passend zum dunkelblauen Kopf).

Farben nur aus ``appearance`` (dunkelgruen = zweite Akzentfarbe der Auswahl ``ACCENT_CHOICES``)."""
from __future__ import annotations

import copy
from typing import Callable

from PySide6.QtCore import QAbstractTableModel, QEvent, QModelIndex, QObject, QSortFilterProxyModel, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog, QFormLayout, QHBoxLayout,
                               QInputDialog, QLabel, QLineEdit, QMenu, QMessageBox, QTableView, QVBoxLayout)

from main_gui_kit.buttons import ButtonKind, action_button

from ..core.data_link import DataLink, ImportTable, read_sheet, sheet_names
from ..paths import config_dir
from . import appearance, last_paths
from .design import NOTE_QSS, SECTION_QSS
from .project_tiles import ColumnTiles

LINK_COLOR = appearance.ACCENT_CHOICES[1]      # dunkelgruen (#1B6B5A), passend zum dunkelblauen Tabellenkopf
FIELDS_KEY = "data_link_fields"                # config/state.json: {"files": Spaltenname, "tags": Spaltenname}
IMPORT_DIR = "last_data_link_dir"              # config/state.json: zuletzt gewaehlter Ordner der Importliste
HITS = "Datenlink-Treffer"
TABLE_NAMES = {1: "Tabelle 1 – Dateien", 2: "Tabelle 2 – Tags"}
PREFERRED_SHEET = "Gesamtliste"                # Gesamtliste aus P3D InstrumentationList


def link_marker(n: int) -> str:
    return f"⛓ Datenlink {n}"


# ----------------------------------------------------------------------------------------------------------------
# Kopf dunkelgruen
# ----------------------------------------------------------------------------------------------------------------
class LinkHeaderPainter(QObject):
    """Malt die Kopfzellen der Datenlink-Spalten dunkelgruen mit weisser Schrift. ``columns()`` liefert die logischen
    Spalten; ``bottom`` = Hoehe der Filterzeile unter der Beschriftung (Kit-Tabellen), sonst 0. Laeuft als Ereignis-
    filter: erst zeichnet der Kopf wie immer, dann wird darueber gemalt (Kit-Kopf bleibt unveraendert)."""

    def __init__(self, header, columns: Callable[[], set[int]], bottom: Callable[[], int] = lambda: 0):
        super().__init__(header)
        self.header, self.columns, self.bottom = header, columns, bottom
        self._busy = False
        header.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):  # noqa: N802
        if event.type() != QEvent.Paint or self._busy:
            return False
        cols = self.columns()
        if not cols:
            return False
        self._busy = True
        try:
            obj.removeEventFilter(self)
            QApplication.sendEvent(obj, event)              # normaler Kopf
        finally:
            obj.installEventFilter(self)
            self._busy = False
        self._paint(obj, cols)
        return True

    def _paint(self, viewport, cols: set[int]) -> None:
        h = self.header
        model = h.model()
        if model is None:
            return
        painter = QPainter(viewport)
        try:
            bottom = max(0, int(self.bottom()))
            for c in cols:
                if c < 0 or c >= h.count() or h.isSectionHidden(c):
                    continue
                x, w = h.sectionViewportPosition(c), h.sectionSize(c)
                rect = viewport.rect().adjusted(0, 0, 0, -bottom)
                rect.setLeft(x)
                rect.setWidth(w - 1)
                painter.fillRect(rect, QColor(LINK_COLOR))
                painter.setPen(QColor("white"))
                f = h.font()
                f.setBold(True)
                painter.setFont(f)
                text = str(model.headerData(c, Qt.Horizontal, Qt.DisplayRole) or "")
                painter.drawText(rect.adjusted(6, 0, -4, 0), Qt.AlignLeft | Qt.AlignVCenter | Qt.TextSingleLine,
                                 painter.fontMetrics().elidedText(text, Qt.ElideRight, max(10, w - 10)))
        finally:
            painter.end()


# ----------------------------------------------------------------------------------------------------------------
# Importtabelle: Modell + Dialog mit Kachel-Editor
# ----------------------------------------------------------------------------------------------------------------
class ImportModel(QAbstractTableModel):
    def __init__(self, table: ImportTable, parent=None):
        super().__init__(parent)
        self.t = table
        self.on_edit: Callable[[], None] = lambda: None

    def rowCount(self, parent=QModelIndex()):  # noqa: N802
        return 0 if parent.isValid() else len(self.t.rows)

    def columnCount(self, parent=QModelIndex()):  # noqa: N802
        return 0 if parent.isValid() else len(self.t.headers)

    def label(self, c: int) -> str:
        name = self.t.headers[c]
        marks = [link_marker(n) for n in (1, 2) if self.t.link(n) == name]
        return name + ("  " + " · ".join(marks) if marks else "")

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # noqa: N802
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.label(section) if 0 <= section < len(self.t.headers) else None
            return section + 1
        if role == Qt.ToolTipRole and orientation == Qt.Horizontal and 0 <= section < len(self.t.headers):
            return ("Rechtsklick: Datenlink 1/2 setzen, umbenennen, ausblenden, einfügen, löschen, sortieren")
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole):
            row = self.t.rows[index.row()]
            value = row[index.column()] if index.column() < len(row) else ""
            return value if role != Qt.ToolTipRole or len(value) > 30 else None
        return None

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsEditable

    def setData(self, index, value, role=Qt.EditRole):  # noqa: N802
        if role != Qt.EditRole or not index.isValid():
            return False
        row = self.t.rows[index.row()]
        while len(row) <= index.column():
            row.append("")
        text = str(value or "").strip()
        if row[index.column()] == text:
            return False
        row[index.column()] = text
        self.dataChanged.emit(index, index)
        self.on_edit()
        return True

    def reset(self) -> None:
        self.beginResetModel()
        self.endResetModel()


class _Tiles(ColumnTiles):
    def refresh(self) -> None:
        super().refresh()
        self.note.setText("Haken = Spalte wird an die Tag-Tabelle übergeben · ziehen = verschieben · Doppelklick = "
                          "umbenennen · Rechtsklick = Datenlink 1/2 setzen")


class ImportDialog(QDialog):
    """Vorschau und Bearbeitung der Importtabelle. Nach „Übernehmen“ steht das Ergebnis in ``self.table``."""

    def __init__(self, table: ImportTable, parent=None):
        super().__init__(parent)
        self.table = table
        self.dirty = False
        self._sync = False
        self.setWindowTitle("Datenlink – Importtabelle")
        self.resize(1360, 820)
        root = QVBoxLayout(self)

        head = QFormLayout()
        self.source_label = QLabel()
        self.source_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        src_row = QHBoxLayout()
        src_row.addWidget(self.source_label, 1)
        b = action_button("Andere Excel-Liste …", ButtonKind.SECONDARY, "Eine andere Excel-Datei bzw. ein anderes "
                                                                         "Blatt einlesen (ersetzt die Vorschau)")
        b.clicked.connect(self._reload_other)
        src_row.addWidget(b)
        head.addRow("Quelle", src_row)
        link_row = QHBoxLayout()
        self.link_boxes: dict[int, QComboBox] = {}
        for n in (1, 2):
            box = QComboBox()
            box.setMinimumWidth(260)
            box.setToolTip(f"Spalte der Importtabelle, die zum Datenlink-Feld der {TABLE_NAMES[n]} passt "
                           f"(dort per Rechtsklick auf den Spaltenkopf setzen)")
            box.currentIndexChanged.connect(lambda _i, n=n: self._box_changed(n))
            self.link_boxes[n] = box
            cap = QLabel(f"{link_marker(n)} ({TABLE_NAMES[n]}):")
            cap.setStyleSheet(SECTION_QSS)
            link_row.addWidget(cap)
            link_row.addWidget(box)
            link_row.addSpacing(16)
        link_row.addStretch(1)
        head.addRow("Datenlinks", link_row)
        root.addLayout(head)
        note = QLabel("Abgleich ohne Groß-/Kleinschreibung; ohne exakten Treffer zählt die Endung ab einem Bindestrich "
                      "(„301-30-149-TI-300“ passt zu Tag „TI-300“). Mit beiden Datenlinks zählen für einen Tag nur "
                      "Zeilen derselben Zeichnung.")
        note.setWordWrap(True)
        note.setStyleSheet(NOTE_QSS)
        root.addWidget(note)

        top = QHBoxLayout()
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("In dieser Tabelle filtern …")
        self.filter.setClearButtonEnabled(True)
        top.addWidget(self.filter, 1)
        self.tiles_button = action_button("Kachel-Editor", ButtonKind.PRIMARY, "Spalten als Kacheln ein-/ausblenden")
        self.tiles_button.setCheckable(True)
        self.tiles_button.toggled.connect(self._tiles_toggled)
        top.addWidget(self.tiles_button)
        root.addLayout(top)

        self.model = ImportModel(table, self)
        self.model.on_edit = lambda: self._set_dirty(True)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.filter.textChanged.connect(self.proxy.setFilterFixedString)
        self.grid = QTableView()
        self.grid.setModel(self.proxy)
        self.grid.setAlternatingRowColors(True)
        self.grid.setSortingEnabled(False)
        self.grid.verticalHeader().setDefaultSectionSize(22)
        self.grid.horizontalHeader().setStyleSheet(appearance.plain_header_qss())
        self.grid.horizontalHeader().setDefaultSectionSize(130)
        self.grid.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
                                  | QAbstractItemView.AnyKeyPressed)
        h = self.grid.horizontalHeader()
        h.setContextMenuPolicy(Qt.CustomContextMenu)
        h.customContextMenuRequested.connect(lambda p: self._header_menu(h.logicalIndexAt(p), h.mapToGlobal(p)))
        self.painter = LinkHeaderPainter(h, self._link_columns)
        self.column_tiles = _Tiles(self)
        root.addWidget(self.column_tiles)
        root.addWidget(self.grid, 1)

        bottom = QHBoxLayout()
        self.status = QLabel()
        self.status.setStyleSheet(NOTE_QSS)
        bottom.addWidget(self.status, 1)
        cancel = action_button("Abbrechen", ButtonKind.NEUTRAL)
        cancel.clicked.connect(self.reject)
        bottom.addWidget(cancel)
        self.ok_button = action_button("Übernehmen und verlinken", ButtonKind.SUCCESS,
                                       "Importtabelle speichern und – sobald Datenlinks gesetzt sind – an die Tabellen "
                                       "des Tools übergeben")
        self.ok_button.clicked.connect(self.accept)
        bottom.addWidget(self.ok_button)
        root.addLayout(bottom)

        self.tiles_button.setChecked(True)
        self._rebuild()

    # --- Schnittstelle fuer den Kachel-Editor (ColumnTiles) ------------------------------------------------------
    def grid_data(self) -> tuple[list[str], list[list[str]]]:
        return [self.model.label(c) for c in range(len(self.table.headers))], self.table.rows

    def hidden_visual(self) -> set[int]:
        hidden = set(self.table.hidden)
        return {c for c, name in enumerate(self.table.headers) if name in hidden}

    def columns_editable(self) -> bool:
        return True

    def show_all_columns(self) -> None:
        self.table.hidden = []
        self._changed()

    def set_column_hidden(self, visual: int, hidden: bool) -> None:
        name = self.table.headers[visual]
        names = [h for h in self.table.hidden if h != name] + ([name] if hidden else [])
        self.table.hidden = names
        self._changed(tiles=False)

    def move_columns(self, order: list[int]) -> None:
        t = self.table
        t.headers = [t.headers[c] for c in order]
        t.rows = [[(r[c] if c < len(r) else "") for c in order] for r in t.rows]
        self._changed()

    def _unique(self, base: str) -> str:
        name, n = base, 2
        while name in self.table.headers:
            name, n = f"{base} {n}", n + 1
        return name

    def insert_columns(self, at: int, n: int = 1) -> None:
        t = self.table
        for _ in range(max(1, n)):
            t.headers.insert(at, self._unique("Neue Spalte"))
            for r in t.rows:
                while len(r) < at:
                    r.append("")
                r.insert(at, "")
        self._changed()

    def delete_column(self, visual: int) -> None:
        t = self.table
        if len(t.headers) <= 1:
            return
        name = t.headers.pop(visual)
        for r in t.rows:
            if visual < len(r):
                del r[visual]
        t.hidden = [h for h in t.hidden if h != name]
        t.link1 = "" if t.link1 == name else t.link1
        t.link2 = "" if t.link2 == name else t.link2
        self._changed()

    def rename_column(self, visual: int) -> None:
        t = self.table
        if not 0 <= visual < len(t.headers):
            return
        old = t.headers[visual]
        new, ok = QInputDialog.getText(self, "Spalte umbenennen", "Neuer Spaltenname:", text=old)
        new = new.strip()
        if not ok or not new or new == old:
            return
        if new in t.headers:
            QMessageBox.information(self, "Spalte umbenennen", f"Eine Spalte „{new}“ gibt es schon.")
            return
        t.headers[visual] = new
        t.hidden = [new if h == old else h for h in t.hidden]
        t.link1 = new if t.link1 == old else t.link1
        t.link2 = new if t.link2 == old else t.link2
        self._changed()

    def sort_by_column(self, visual: int, descending: bool = False) -> None:
        self.table.rows.sort(key=lambda r: (r[visual] if visual < len(r) else "").casefold(), reverse=descending)
        self._changed(tiles=False)

    def set_link(self, n: int, visual: int | None) -> None:
        name = self.table.headers[visual] if visual is not None and 0 <= visual < len(self.table.headers) else ""
        if n == 1:
            self.table.link1 = name
        else:
            self.table.link2 = name
        self._changed()

    def column_menu(self, visual: int) -> QMenu:
        t = self.table
        name = t.headers[visual]
        m = QMenu(self)
        for n in (1, 2):
            if t.link(n) == name:
                m.addAction(f"{link_marker(n)} entfernen", lambda n=n: self.set_link(n, None))
            else:
                m.addAction(f"Als {link_marker(n)} setzen ({TABLE_NAMES[n]})", lambda n=n: self.set_link(n, visual))
        m.addSeparator()
        m.addAction(f"„{name}“ umbenennen …", lambda: self.rename_column(visual))
        m.addAction("Spalte rechts einfügen", lambda: self.insert_columns(visual + 1))
        m.addAction("Spalte löschen", lambda: self.delete_column(visual)).setEnabled(len(t.headers) > 1)
        m.addSeparator()
        m.addAction("Zeilen aufsteigend sortieren", lambda: self.sort_by_column(visual))
        m.addAction("Zeilen absteigend sortieren", lambda: self.sort_by_column(visual, True))
        m.addSeparator()
        hidden = name in t.hidden
        m.addAction("Einblenden (übergeben)" if hidden else "Ausblenden (nicht übergeben)",
                    lambda: self.set_column_hidden(visual, not hidden))
        m.addAction("Alle Spalten einblenden", self.show_all_columns).setEnabled(bool(t.hidden))
        return m

    # --- intern ------------------------------------------------------------------------------------------------
    def _header_menu(self, logical: int, pos) -> None:
        if logical >= 0:
            self.column_menu(logical).exec(pos)

    def _link_columns(self) -> set[int]:
        return {self.table.headers.index(self.table.link(n)) for n in (1, 2) if self.table.link(n) in self.table.headers}

    def _tiles_toggled(self, on: bool) -> None:
        self.column_tiles.setVisible(on)
        if on:
            self.column_tiles.refresh()

    def _set_dirty(self, dirty: bool) -> None:
        self.dirty = dirty
        self._status()

    def _changed(self, tiles: bool = True) -> None:
        self.dirty = True
        self._rebuild(tiles)

    def _rebuild(self, tiles: bool = True) -> None:
        self.model.reset()
        hidden = self.hidden_visual()
        for c in range(len(self.table.headers)):
            self.grid.setColumnHidden(c, c in hidden)
        self._fill_boxes()
        if tiles and not self.column_tiles.isHidden():
            self.column_tiles.refresh()
        self._status()

    def _fill_boxes(self) -> None:
        self._sync = True
        try:
            for n, box in self.link_boxes.items():
                box.clear()
                box.addItem("(kein Datenlink)", "")
                for name in self.table.headers:
                    box.addItem(name, name)
                box.setCurrentIndex(max(0, box.findData(self.table.link(n))))
        finally:
            self._sync = False

    def _box_changed(self, n: int) -> None:
        if self._sync:
            return
        name = self.link_boxes[n].currentData() or ""
        self.set_link(n, self.table.headers.index(name) if name in self.table.headers else None)

    def _status(self) -> None:
        t = self.table
        self.source_label.setText(f"{t.source or '–'}" + (f"  ·  Blatt „{t.sheet}“" if t.sheet else ""))
        links = ", ".join(f"Datenlink {n} = „{t.link(n)}“" for n in (1, 2) if t.link(n)) or "noch kein Datenlink"
        self.status.setText(f"{len(t.rows)} Zeilen · {len(t.transfer_columns())} von {len(t.headers)} Spalten werden "
                            f"übergeben · {links}" + (" · geändert" if self.dirty else ""))

    def _reload_other(self) -> None:
        table = choose_excel(self)
        if table is None:
            return
        keep1, keep2 = self.table.link1, self.table.link2
        self.table.source, self.table.sheet = table.source, table.sheet
        self.table.headers, self.table.rows, self.table.hidden = table.headers, table.rows, []
        self.table.link1 = keep1 if keep1 in table.headers else table.link1
        self.table.link2 = keep2 if keep2 in table.headers else table.link2
        self._changed()


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

    def file_extra(self) -> list[str]:
        return [HITS] if self.active(1) else []

    def tag_extra(self, taken: list[str]) -> list[str]:
        """Zusatzspalten der Tag-Tabelle: Treffer + uebergebene Spalten (Namensgleichheit -> „ (Liste)“)."""
        if not self.active(2):
            return []
        out = [HITS]
        for name in self.link.columns:
            label = name
            while label in taken or label in out:
                label += " (Liste)"
            out.append(label)
        return out

    def file_values(self, value) -> list:
        return [len(self.link.file_rows(value))] if self.active(1) else []

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
                act = menu.addAction(f"„{name}“ als Datenlink-Feld setzen (⛓ Datenlink {n})",
                                     lambda: self.set_field(key, name))
                act.setEnabled(name in base)
            menu.addAction("Datenlink: Importtabelle …", self.on_open)

        view._shared_header_menu_hook = hook
        LinkHeaderPainter(view.horizontalHeader(), lambda: self._field_columns(key, data_table), _filter_height)

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
        dlg = ImportDialog(table, parent)
        if dlg.exec() != QDialog.Accepted:
            return False
        self.table = dlg.table
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
