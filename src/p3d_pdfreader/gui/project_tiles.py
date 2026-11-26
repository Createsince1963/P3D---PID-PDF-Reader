"""Kachel-Editor und Tabellenfunktionen der Projektdefinitionen (Nutzervorgabe 2026-11-21: Funktionen wie im Fenster
„Project definitions“ von P3D Tag Compliance, dort ``pidtag_module/pidtag_gui.py`` + ``linetag_defs_tiles.py``).

* ``TileList``     links: die Tabellen/Listen als Kacheln - per Drag & Drop umsortieren, umbenennen (Doppelklick, F2,
                   Rechtsklick). Reihenfolge und Kachelnamen liegen in der Projekt-Datenbank (``meta``).
* ``ColumnTiles``  Kachel-Editor über der Tabelle: jede Spalte eine Kachel - verschieben, ein-/ausblenden, umbenennen,
                   einfügen, duplizieren, löschen (Spaltenänderungen nur bei Listen; feste Tabellen haben feste Spalten).
* ``GridEditing``  Rechtsklick-Menüs (Zelle, Zeilennummer, Spaltenkopf) wie Excel: Zeilen/Spalten einfügen, duplizieren,
                   kopieren, ausschneiden, einfügen, löschen, Inhalt löschen, sortieren, filtern; Rückgängig/Wiederholen
                   (Strg+Z / Strg+Y), Kopieren/Einfügen (Strg+C / Strg+V), Entf leert Zellen.

Der QML-Kachel-Editor von Tag Compliance (berechnete Spalten, Profile) wird nicht übernommen; hier sind es die
Bearbeitungsfunktionen für die Definitionstabellen. Farben nur aus design/appearance."""
from __future__ import annotations

import csv
import io
import json

from PySide6.QtCore import QItemSelectionModel, QSize, Qt, Signal
from PySide6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QInputDialog, QLabel, QListView, QListWidget,
                               QListWidgetItem, QMenu, QMessageBox, QTableWidgetItem, QVBoxLayout, QWidget)

from main_gui_kit.buttons import ButtonKind, action_button

from ..core.project_defs import code_col, sort_code_rows
from . import appearance
from .design import BAND, BORDER, NOTE_QSS, SECTION_QSS, TEXT
from .controls import tip_button

UNDO_LIMIT = 60
_CLIP: dict = {}                # zuletzt kopierte Zeilen/Spalten (die Zwischenablage bekommt den Text, tabulatorgetrennt)


def _tile_qss() -> str:
    sel = appearance.selection_color()
    return (f"QListWidget {{ background: {BAND}; border: 1px solid {BORDER}; }}"
            f"QListWidget::item {{ background: white; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 5px;"
            f" padding: 6px 8px; margin: 2px; }}"
            f"QListWidget::item:selected {{ background: {sel}; color: {TEXT}; border-color: {appearance.accent()}; }}"
            f"QListWidget::item:hover {{ border-color: {appearance.accent()}; }}")


def tsv(rows: list[list[str]]) -> str:
    def cell(v: str) -> str:
        return '"' + v.replace('"', '""') + '"' if any(ch in v for ch in '\t\n\r"') else v
    return "\n".join("\t".join(cell(str(v)) for v in r) for r in rows)


def parse_tsv(text: str) -> list[list[str]]:
    text = text.rstrip("\r\n")
    if not text:
        return []
    return [list(r) for r in csv.reader(io.StringIO(text), delimiter="\t")]


def _natural(v: str):
    import re
    return [(0, int(p), "") if p.isdigit() else (1, 0, p.casefold()) for p in re.split(r"(\d+)", v or "") if p]


# ----------------------------------------------------------------------------------------------------------------
# Linke Kachelliste (Tabellen und Listen)
# ----------------------------------------------------------------------------------------------------------------
class TileList(QListWidget):
    """Die Tabellen und Listen als Kacheln; ``reordered`` nach dem Ablegen, ``renameRequested(row)`` zum Umbenennen."""
    reordered = Signal()
    renameRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSpacing(2)
        self.setStyleSheet(_tile_qss())
        self.setToolTip("Kachel an eine andere Stelle ziehen – die Reihenfolge wird im Projekt gemerkt.\n"
                        "Doppelklick oder F2 benennt die Kachel um.")

    def mouseDoubleClickEvent(self, e):  # noqa: N802
        i = self.indexAt(e.position().toPoint())
        if i.isValid():
            self.renameRequested.emit(i.row())

    def keyPressEvent(self, e):  # noqa: N802
        if e.key() == Qt.Key_F2 and self.currentRow() >= 0:
            self.renameRequested.emit(self.currentRow())
        else:
            super().keyPressEvent(e)

    def contextMenuEvent(self, e):  # noqa: N802
        i = self.indexAt(e.pos())
        if i.isValid():
            m = QMenu(self)
            m.addAction("Kachel umbenennen …", lambda r=i.row(): self.renameRequested.emit(r))
            m.exec(e.globalPos())

    def dropEvent(self, e):  # noqa: N802
        self.blockSignals(True)                          # beim Verschieben keine andere Tabelle laden
        try:
            super().dropEvent(e)
        finally:
            self.blockSignals(False)
        self.reordered.emit()


# ----------------------------------------------------------------------------------------------------------------
# Kachel-Editor (Spalten als Kacheln)
# ----------------------------------------------------------------------------------------------------------------
class _ColumnList(QListWidget):
    dropped = Signal()
    menuRequested = Signal(int, object)                  # Kachelzeile, globale Position
    renameRequested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListView.ListMode)
        self.setFlow(QListView.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListView.Adjust)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setStyleSheet(_tile_qss())
        self.setMaximumHeight(118)                       # zwei Kachelreihen, dann Bildlauf

    def dropEvent(self, e):  # noqa: N802
        super().dropEvent(e)
        self.dropped.emit()

    def mouseDoubleClickEvent(self, e):  # noqa: N802
        i = self.indexAt(e.position().toPoint())
        if i.isValid():
            self.renameRequested.emit(i.row())

    def contextMenuEvent(self, e):  # noqa: N802
        i = self.indexAt(e.pos())
        if i.isValid():
            self.menuRequested.emit(i.row(), e.globalPos())


class ColumnTiles(QWidget):
    """Kachel-Editor: zeigt die Spalten der Tabelle als Kacheln in Tabellenreihenfolge. Haken = Spalte sichtbar."""

    def __init__(self, owner: "GridEditing", parent=None):
        super().__init__(parent)
        self.owner = owner
        self._filling = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 4)
        head = QHBoxLayout()
        caption = QLabel("Kachel-Editor – Spalten")
        caption.setStyleSheet(SECTION_QSS)
        head.addWidget(caption)
        self.note = QLabel()
        self.note.setStyleSheet(NOTE_QSS)
        head.addWidget(self.note, 1)
        self.b_add = tip_button("+ Spalte", ButtonKind.SECONDARY, "Neue Spalte rechts von der markierten Kachel")
        self.b_show = tip_button("Alle einblenden", ButtonKind.NEUTRAL, "Alle ausgeblendeten Spalten wieder zeigen")
        self.b_add.clicked.connect(self._add)
        self.b_show.clicked.connect(owner.show_all_columns)
        head.addWidget(self.b_add)
        head.addWidget(self.b_show)
        lay.addLayout(head)
        self.tiles = _ColumnList()
        self.tiles.itemChanged.connect(self._checked)
        self.tiles.dropped.connect(self._dropped)
        self.tiles.renameRequested.connect(lambda r: owner.rename_column(self._visual(r)))
        self.tiles.menuRequested.connect(self._menu)
        lay.addWidget(self.tiles)

    def _visual(self, tile_row: int) -> int:
        item = self.tiles.item(tile_row)
        return int(item.data(Qt.UserRole)) if item is not None else -1

    def selected_visual(self) -> list[int]:
        return sorted(int(i.data(Qt.UserRole)) for i in self.tiles.selectedItems())

    def refresh(self) -> None:
        o = self.owner
        labels, rows = o.grid_data()
        hidden = o.hidden_visual()
        editable = o.columns_editable()
        self._filling = True
        keep = set(self.selected_visual())
        self.tiles.clear()
        for v, label in enumerate(labels):
            filled = sum(1 for r in rows if v < len(r) and str(r[v]).strip())
            item = QListWidgetItem(f"{label}\n{filled} von {len(rows)} gefüllt")
            item.setData(Qt.UserRole, v)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled)
            item.setCheckState(Qt.Unchecked if v in hidden else Qt.Checked)
            item.setToolTip(f"Spalte „{label}“ – Haken = sichtbar, ziehen = verschieben"
                            + (", Doppelklick = umbenennen" if editable else " (feste Tabelle: Spalten fest)"))
            item.setSizeHint(QSize(max(110, 9 * len(label) + 40), 46))
            self.tiles.addItem(item)
            if v in keep:
                item.setSelected(True)
        self._filling = False
        self.b_add.setEnabled(editable)
        self.note.setText("Liste: Spalten verschieben, umbenennen, einfügen, löschen – „Speichern“ schreibt sie."
                          if editable else "Feste Tabelle: Spalten verschieben und ausblenden (nur Ansicht).")

    def _checked(self, item: QListWidgetItem) -> None:
        if not self._filling:
            self.owner.set_column_hidden(int(item.data(Qt.UserRole)), item.checkState() != Qt.Checked)

    def _dropped(self) -> None:
        order = [int(self.tiles.item(i).data(Qt.UserRole)) for i in range(self.tiles.count())]
        self.owner.move_columns(order)

    def _add(self) -> None:
        sel = self.selected_visual()
        self.owner.insert_columns((sel[-1] + 1) if sel else len(self.owner.grid_data()[0]), 1)

    def _menu(self, tile_row: int, pos) -> None:
        v = self._visual(tile_row)
        if v >= 0:
            self.owner.column_menu(v).exec(pos)


# ----------------------------------------------------------------------------------------------------------------
# Tabellenfunktionen (Mixin fuer den Projektdefinitionen-Dialog)
# ----------------------------------------------------------------------------------------------------------------
class GridEditing:
    """Erwartet: ``self.grid`` (QTableWidget), ``self._loading``, ``self._set_dirty(bool)``, ``self.filter`` (QLineEdit),
    ``columns_editable()`` und ``self.column_tiles`` (ColumnTiles oder None). Alle Aenderungen laufen ueber
    ``grid_data`` / ``set_grid`` (Anzeigereihenfolge) und sind rueckgaengig zu machen."""

    # --- Daten ------------------------------------------------------------------------------------------------
    def _visual_logical(self) -> list[int]:
        h = self.grid.horizontalHeader()
        return [h.logicalIndex(v) for v in range(h.count())]

    def grid_data(self) -> tuple[list[str], list[list[str]]]:
        """Spaltennamen und alle Zeilen in Anzeigereihenfolge der Spalten (auch ausgeblendete, auch ausgefilterte)."""
        logical = self._visual_logical()
        labels = [self.grid.horizontalHeaderItem(c).text() if self.grid.horizontalHeaderItem(c) else "" for c in logical]
        rows = [[(self.grid.item(r, c).text() if self.grid.item(r, c) else "") for c in logical]
                for r in range(self.grid.rowCount())]
        return labels, rows

    def hidden_visual(self) -> set[int]:
        return {v for v, c in enumerate(self._visual_logical()) if self.grid.isColumnHidden(c)}

    def set_grid(self, labels: list[str], rows: list[list[str]], hidden: set[str] | None = None) -> None:
        """Raster neu aufbauen (Spalten in dieser Reihenfolge); ``hidden`` = Namen ausgeblendeter Spalten."""
        widths = {}
        for v, c in enumerate(self._visual_logical()):
            item = self.grid.horizontalHeaderItem(c)
            if item is not None:
                widths[item.text()] = self.grid.columnWidth(c)
        self._loading = True
        h = self.grid.horizontalHeader()
        self.grid.clear()
        self.grid.setColumnCount(0)
        self.grid.setColumnCount(len(labels))
        for v in range(h.count()):                        # neue Spalten: Anzeige = logische Reihenfolge
            if h.visualIndex(v) != v:
                h.moveSection(h.visualIndex(v), v)
        self.grid.setHorizontalHeaderLabels(labels)
        self.grid.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c in range(len(labels)):
                self.grid.setItem(r, c, QTableWidgetItem(row[c] if c < len(row) else ""))
        for c, label in enumerate(labels):
            self.grid.setColumnHidden(c, bool(hidden) and label in hidden)
            if label in widths:
                self.grid.setColumnWidth(c, widths[label])
        self._paint_codes()
        self._loading = False
        self._apply_filter(self.filter.text())
        self._after_change()

    def _paint_codes(self) -> None:
        """Codes immer fett (wie Tag Compliance)."""
        labels = [self.grid.horizontalHeaderItem(c).text() for c in range(self.grid.columnCount())]
        ci = code_col(labels)
        if ci < 0:
            return
        for r in range(self.grid.rowCount()):
            it = self.grid.item(r, ci)
            if it is not None:
                f = it.font()
                f.setBold(True)
                it.setFont(f)

    def _hidden_labels(self) -> set[str]:
        labels, _rows = self.grid_data()
        return {labels[v] for v in self.hidden_visual()}

    # --- Rueckgaengig ------------------------------------------------------------------------------------------
    def reset_undo(self) -> None:
        self._undo: list[tuple] = []
        self._redo: list[tuple] = []
        self._snap = self._snapshot()

    def _snapshot(self) -> tuple:
        labels, rows = self.grid_data()
        return labels, rows, self._hidden_labels()

    def _change(self, labels: list[str], rows: list[list[str]], hidden: set[str] | None = None) -> None:
        """Eine rueckgaengig machbare Aenderung: alter Stand auf den Stapel, Raster neu, ungespeichert."""
        self._undo.append(self._snap)
        del self._undo[:-UNDO_LIMIT]
        self._redo.clear()
        self.set_grid(labels, rows, self._hidden_labels() if hidden is None else hidden)
        self._set_dirty(True)

    def _after_change(self) -> None:
        self._snap = self._snapshot()
        if getattr(self, "column_tiles", None) is not None and not self.column_tiles.isHidden():
            self.column_tiles.refresh()

    def cell_edited(self) -> None:
        """Nach dem Tippen in eine Zelle: ein Rueckgaengig-Schritt."""
        self._undo.append(self._snap)
        del self._undo[:-UNDO_LIMIT]
        self._redo.clear()
        self._after_change()

    def undo(self) -> None:
        if self._undo:
            self._redo.append(self._snapshot())
            self.set_grid(*self._undo.pop())
            self._set_dirty(True)

    def redo(self) -> None:
        if self._redo:
            self._undo.append(self._snapshot())
            self.set_grid(*self._redo.pop())
            self._set_dirty(True)

    def install_grid_functions(self) -> None:
        """Rechtsklick-Menues, Spalten verschiebbar, Tastenkuerzel."""
        self.reset_undo()
        h, vh = self.grid.horizontalHeader(), self.grid.verticalHeader()
        h.setSectionsMovable(True)
        h.sectionMoved.connect(self._section_moved)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.grid.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)   # nicht am Viewport: dort kommt das Signal nie an
        self.grid.customContextMenuRequested.connect(
            lambda p: self.cell_menu(self.grid.indexAt(p)).exec(self.grid.viewport().mapToGlobal(p)))
        vh.setContextMenuPolicy(Qt.CustomContextMenu)
        vh.customContextMenuRequested.connect(self._row_header_menu)
        h.setContextMenuPolicy(Qt.CustomContextMenu)
        h.customContextMenuRequested.connect(self._column_header_menu)
        for seq, fn in ((QKeySequence.Undo, self.undo), (QKeySequence.Redo, self.redo),
                        (QKeySequence.Copy, self.copy_cells), (QKeySequence.Paste, self.paste_cells),
                        (QKeySequence.Delete, self.clear_cells)):
            QShortcut(seq, self.grid, activated=fn, context=Qt.WidgetShortcut)   # nicht im Zelleditor

    def _section_moved(self, *_a) -> None:
        """Spaltenkopf gezogen: bei Listen eine Aenderung der Spaltenfolge (Speichern schreibt sie)."""
        if self._loading:
            return
        if self.columns_editable():
            self._set_dirty(True)
        self._after_change()

    # --- Auswahl -----------------------------------------------------------------------------------------------
    def selected_rows(self) -> list[int]:
        return sorted({i.row() for i in self.grid.selectedIndexes() if not self.grid.isRowHidden(i.row())})

    def _selected_cells(self) -> list[tuple[int, int]]:
        """(Zeile, Spalte in Anzeigereihenfolge) der markierten, sichtbaren Zellen."""
        h = self.grid.horizontalHeader()
        return sorted({(i.row(), h.visualIndex(i.column())) for i in self.grid.selectedIndexes()
                       if not self.grid.isRowHidden(i.row()) and not self.grid.isColumnHidden(i.column())})

    def _select_rows(self, rows: list[int]) -> None:
        sel = self.grid.selectionModel()
        self.grid.clearSelection()
        for k, r in enumerate(rows):
            if 0 <= r < self.grid.rowCount():
                if k == 0:
                    self.grid.setCurrentCell(r, self.grid.horizontalHeader().logicalIndex(0))
                    self.grid.scrollToItem(self.grid.item(r, 0))
                sel.select(self.grid.model().index(r, 0), QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def _select_columns(self, visual: list[int]) -> None:
        sel = self.grid.selectionModel()
        self.grid.clearSelection()
        for v in visual:
            c = self.grid.horizontalHeader().logicalIndex(v)
            sel.select(self.grid.model().index(0, c), QItemSelectionModel.Select | QItemSelectionModel.Columns)

    def _target_columns(self, visual: int) -> list[int]:
        """Die angeklickte Spalte oder alle markierten Spalten, wenn sie dazugehoert (wie Excel)."""
        cols = sorted({v for _r, v in self._selected_cells()})
        return cols if visual in cols and len(cols) > 1 else [visual]

    # --- Zeilen ------------------------------------------------------------------------------------------------
    def _unfilter(self) -> None:
        if self.filter.text():
            self.filter.clear()

    def insert_rows(self, at: int, n: int = 1) -> None:
        labels, rows = self.grid_data()
        at = max(0, min(at, len(rows)))
        rows[at:at] = [[""] * len(labels) for _ in range(n)]
        self._unfilter()
        self._change(labels, rows)
        self._select_rows(list(range(at, at + n)))

    def duplicate_rows(self, sel: list[int] | None = None) -> None:
        sel = sorted(set(self.selected_rows() if sel is None else sel))
        if not sel:
            return
        labels, rows = self.grid_data()
        for r in reversed(sel):
            rows.insert(r + 1, list(rows[r]))
        self._change(labels, rows)
        self._select_rows([r + 1 + i for i, r in enumerate(sel)])

    def delete_rows(self, sel: list[int] | None = None) -> None:
        sel = sorted(set(self.selected_rows() if sel is None else sel), reverse=True)
        if not sel:
            return
        labels, rows = self.grid_data()
        for r in sel:
            del rows[r]
        self._change(labels, rows)

    def clear_rows(self) -> None:
        sel = self.selected_rows()
        if sel:
            labels, rows = self.grid_data()
            for r in sel:
                rows[r] = [""] * len(labels)
            self._change(labels, rows)

    def copy_rows(self, cut: bool = False) -> None:
        sel = self.selected_rows()
        if not sel:
            return
        _labels, rows = self.grid_data()
        data = [list(rows[r]) for r in sel]
        _CLIP.update(kind="rows", payload=data, tsv=tsv(data))
        QGuiApplication.clipboard().setText(_CLIP["tsv"])
        if cut:
            self.delete_rows(sel)

    def _clip_rows(self) -> list[list[str]]:
        text = QGuiApplication.clipboard().text()
        if _CLIP.get("kind") == "rows" and text == _CLIP.get("tsv"):
            return [list(r) for r in _CLIP["payload"]]
        return [r for r in parse_tsv(text) if any(r)]

    def paste_rows(self, above: bool) -> None:
        data, sel = self._clip_rows(), self.selected_rows()
        if not data or not sel:
            return
        labels, rows = self.grid_data()
        at = sel[0] if above else sel[-1] + 1
        n = len(labels)
        rows[at:at] = [(list(r) + [""] * n)[:n] for r in data]
        self._change(labels, rows)
        self._select_rows(list(range(at, at + len(data))))

    def sort_by_code(self) -> None:
        labels, rows = self.grid_data()
        if code_col(labels) >= 0:
            sort_code_rows(labels, rows)
            self._change(labels, rows)

    def sort_by_column(self, visual: int, descending: bool = False) -> None:
        labels, rows = self.grid_data()
        rows.sort(key=lambda r: _natural(r[visual]), reverse=descending)
        self._change(labels, rows)

    # --- Zellen ------------------------------------------------------------------------------------------------
    def copy_cells(self) -> None:
        cells = self._selected_cells()
        if not cells:
            return
        _labels, rows = self.grid_data()
        rr = sorted({r for r, _v in cells})
        vv = sorted({v for _r, v in cells})
        chosen = set(cells)
        QGuiApplication.clipboard().setText(tsv([[rows[r][v] if (r, v) in chosen else "" for v in vv] for r in rr]))

    def paste_cells(self) -> None:
        """Tabulatorgetrennten Text (Excel) ab der aktuellen Zelle einfuegen; fehlende Zeilen werden angehaengt."""
        data = parse_tsv(QGuiApplication.clipboard().text())
        cur = self.grid.currentIndex()
        if not data or not cur.isValid():
            return
        labels, rows = self.grid_data()
        r0, v0 = cur.row(), self.grid.horizontalHeader().visualIndex(cur.column())
        visible = [v for v in range(len(labels)) if v not in self.hidden_visual()]
        start = visible.index(v0) if v0 in visible else 0
        for i, line in enumerate(data):
            r = r0 + i
            while r >= len(rows):
                rows.append([""] * len(labels))
            for k, value in enumerate(line):
                if start + k < len(visible):
                    rows[r][visible[start + k]] = value
        self._change(labels, rows)

    def clear_cells(self) -> None:
        cells = self._selected_cells()
        if cells:
            labels, rows = self.grid_data()
            for r, v in cells:
                rows[r][v] = ""
            self._change(labels, rows)

    # --- Spalten -----------------------------------------------------------------------------------------------
    def _unique(self, labels: list[str], base: str) -> str:
        used = {x.casefold() for x in labels}
        name, n = base, 2
        while name.casefold() in used:
            name, n = f"{base} {n}", n + 1
        return name

    def insert_columns(self, at: int, n: int = 1, names: list[str] | None = None,
                       values: list[list[str]] | None = None) -> None:
        if not self.columns_editable():
            return
        labels, rows = self.grid_data()
        at = max(0, min(at, len(labels)))
        for k in range(n):
            label = self._unique(labels, (names[k] if names and k < len(names) else "") or "Spalte")
            labels.insert(at + k, label)
            for ri, r in enumerate(rows):
                r.insert(at + k, values[k][ri] if values and k < len(values) and ri < len(values[k]) else "")
        self._change(labels, rows)
        self._select_columns(list(range(at, at + n)))

    def duplicate_columns(self, visual: list[int]) -> None:
        if not self.columns_editable():
            return
        labels, rows = self.grid_data()
        for v in sorted(set(visual), reverse=True):
            labels.insert(v + 1, self._unique(labels, labels[v] + " Kopie"))
            for r in rows:
                r.insert(v + 1, r[v])
        self._change(labels, rows)

    def delete_columns(self, visual: list[int]) -> None:
        labels, rows = self.grid_data()
        cols = sorted(set(visual), reverse=True)
        if not self.columns_editable() or not cols or len(cols) >= len(labels):
            return
        for v in cols:
            del labels[v]
            for r in rows:
                del r[v]
        self._change(labels, rows)

    def clear_columns(self, visual: list[int]) -> None:
        labels, rows = self.grid_data()
        for r in rows:
            for v in visual:
                r[v] = ""
        self._change(labels, rows)

    def copy_columns(self, visual: list[int], cut: bool = False) -> None:
        labels, rows = self.grid_data()
        cols = sorted(set(visual))
        names = [labels[v] for v in cols]
        data = [[r[v] for r in rows] for v in cols]
        _CLIP.update(kind="cols", payload=(names, data), tsv=tsv([names] + [[r[v] for v in cols] for r in rows]))
        QGuiApplication.clipboard().setText(_CLIP["tsv"])
        if cut:
            self.delete_columns(cols)

    def _clip_columns_ok(self) -> bool:
        return _CLIP.get("kind") == "cols" and QGuiApplication.clipboard().text() == _CLIP.get("tsv")

    def paste_columns(self, at: int) -> None:
        if self._clip_columns_ok():
            names, data = _CLIP["payload"]
            self.insert_columns(at, len(names), list(names), [list(d) for d in data])

    def rename_column(self, visual: int) -> None:
        labels, rows = self.grid_data()
        if not (0 <= visual < len(labels)):
            return
        if not self.columns_editable():
            QMessageBox.information(self.grid.window(), "Spalte umbenennen",
                                    "Die Spalten einer festen Tabelle lassen sich nicht umbenennen.")
            return
        name, ok = QInputDialog.getText(self.grid.window(), "Spalte umbenennen", "Neuer Name:", text=labels[visual])
        name = name.strip() if ok else ""
        if not name or name == labels[visual]:
            return
        if name.casefold() in {x.casefold() for i, x in enumerate(labels) if i != visual}:
            QMessageBox.warning(self.grid.window(), "Spalte umbenennen", f"Eine Spalte „{name}“ gibt es schon.")
            return
        hidden = self._hidden_labels()
        if labels[visual] in hidden:
            hidden = (hidden - {labels[visual]}) | {name}
        labels[visual] = name
        self._change(labels, rows, hidden)

    def set_column_hidden(self, visual: int, hidden: bool) -> None:
        logical = self._visual_logical()
        if 0 <= visual < len(logical):
            if hidden and len(self.hidden_visual() | {visual}) >= len(logical):
                self._after_change()                     # die letzte sichtbare Spalte bleibt
                return
            self.grid.setColumnHidden(logical[visual], hidden)
            self._after_change()

    def show_all_columns(self) -> None:
        for c in range(self.grid.columnCount()):
            self.grid.setColumnHidden(c, False)
        self._after_change()

    def move_columns(self, order: list[int]) -> None:
        """Neue Anzeigereihenfolge (Liste der bisherigen Anzeigepositionen). Bei Listen eine Aenderung der Spaltenfolge
        (wird gespeichert), bei festen Tabellen nur Ansicht."""
        labels, rows = self.grid_data()
        if sorted(order) != list(range(len(labels))) or order == list(range(len(labels))):
            self._after_change()
            return
        new_labels = [labels[v] for v in order]
        new_rows = [[r[v] for v in order] for r in rows]
        if self.columns_editable():
            self._change(new_labels, new_rows)
        else:
            h = self.grid.horizontalHeader()
            logical = self._visual_logical()
            self._loading = True
            for target, v in enumerate(order):
                h.moveSection(h.visualIndex(logical[v]), target)
            self._loading = False
            self._after_change()

    # --- Menues ------------------------------------------------------------------------------------------------
    @staticmethod
    def _fill_menu(menu: QMenu, entries: list) -> QMenu:
        for e in entries:
            if e is None:
                menu.addSeparator()
                continue
            text, fn, enabled = e[:3]
            act = menu.addAction(text, fn)
            act.setEnabled(bool(enabled))
            if len(e) > 3:
                act.setShortcut(e[3])
        return menu

    def _undo_entries(self) -> list:
        return [("Rückgängig", self.undo, bool(self._undo), "Ctrl+Z"),
                ("Wiederholen", self.redo, bool(self._redo), "Ctrl+Y")]

    def cell_menu(self, index) -> QMenu:
        """Rechtsklick in eine Zelle."""
        if index.isValid() and not self.grid.selectionModel().isSelected(index):
            self.grid.setCurrentIndex(index)
        sel = self.selected_rows()
        has = bool(sel)
        labels = self.grid_data()[0]
        value = str(index.data(Qt.DisplayRole) or "") if index.isValid() else ""
        short = value if len(value) <= 30 else value[:29] + "…"
        entries = [("Zeile hinzufügen", lambda: self.insert_rows(self.grid.rowCount()), True),
                   ("Zeile(n) duplizieren", self.duplicate_rows, has),
                   ("Zeile(n) löschen", self.delete_rows, has),
                   ("Nach Code A–Z sortieren", self.sort_by_code, code_col(labels) >= 0),
                   None,
                   ("Kopieren", self.copy_cells, has, "Ctrl+C"),
                   ("Einfügen", self.paste_cells, index.isValid() and bool(QGuiApplication.clipboard().text()),
                    "Ctrl+V"),
                   ("Inhalt löschen", self.clear_cells, has, "Del"),
                   None,
                   (f"Nur Zeilen mit „{short}“ zeigen", lambda: self.filter.setText(value), bool(value)),
                   ("Filter zurücksetzen", self.filter.clear, bool(self.filter.text())),
                   None]
        tiles = getattr(self, "toggle_tiles", None)
        if tiles is not None:
            entries.append(("Kachel-Editor ein/aus", tiles, True))
        export = getattr(self, "export_view", None)
        if export is not None:
            entries.append(("Ansicht nach Excel …", export, True))
        return self._fill_menu(QMenu(self.grid), entries + [None] + self._undo_entries())

    def row_header_menu(self) -> QMenu:
        """Rechtsklick auf die Zeilennummern (wie Excel)."""
        sel = self.selected_rows()
        n = len(sel)
        has = n > 0
        word = "Zeile" if n <= 1 else f"{n} Zeilen"
        paste_ok = has and bool(self._clip_rows())
        entries = [(f"{word} oberhalb einfügen", lambda: self.insert_rows(sel[0], max(1, n)), has),
                   (f"{word} unterhalb einfügen", lambda: self.insert_rows(sel[-1] + 1, max(1, n)), has),
                   None,
                   (f"{word} duplizieren", self.duplicate_rows, has),
                   (f"{word} kopieren", self.copy_rows, has),
                   (f"{word} ausschneiden", lambda: self.copy_rows(cut=True), has),
                   ("Zeilen oberhalb einfügen (Zwischenablage)", lambda: self.paste_rows(True), paste_ok),
                   ("Zeilen unterhalb einfügen (Zwischenablage)", lambda: self.paste_rows(False), paste_ok),
                   None,
                   (f"{word} löschen", self.delete_rows, has),
                   (f"Inhalt von {word} löschen", self.clear_rows, has),
                   None]
        return self._fill_menu(QMenu(self.grid), entries + self._undo_entries())

    def _row_header_menu(self, pos) -> None:
        vh = self.grid.verticalHeader()
        r = vh.logicalIndexAt(pos)
        if r >= 0 and r not in self.selected_rows():
            self._select_rows([r])
        self.row_header_menu().exec(vh.mapToGlobal(pos))

    def column_menu(self, visual: int) -> QMenu:
        """Rechtsklick auf einen Spaltenkopf oder eine Kachel des Kachel-Editors."""
        labels = self.grid_data()[0]
        cols = self._target_columns(visual)
        n = len(cols)
        word = "Spalte" if n == 1 else f"{n} Spalten"
        ed = self.columns_editable()
        can_remove = ed and n < len(labels)
        entries = [(f"„{labels[visual]}“ umbenennen …", lambda: self.rename_column(visual), ed),
                   ("Spalte links einfügen", lambda: self.insert_columns(cols[0], n), ed),
                   ("Spalte rechts einfügen", lambda: self.insert_columns(cols[-1] + 1, n), ed),
                   None,
                   (f"{word} duplizieren", lambda: self.duplicate_columns(cols), ed),
                   (f"{word} kopieren", lambda: self.copy_columns(cols), True),
                   (f"{word} ausschneiden", lambda: self.copy_columns(cols, cut=True), can_remove),
                   ("Spalte(n) links einfügen (Zwischenablage)", lambda: self.paste_columns(cols[0]),
                    ed and self._clip_columns_ok()),
                   ("Spalte(n) rechts einfügen (Zwischenablage)", lambda: self.paste_columns(cols[-1] + 1),
                    ed and self._clip_columns_ok()),
                   None,
                   (f"{word} löschen", lambda: self.delete_columns(cols), can_remove),
                   (f"Inhalt von {word} löschen", lambda: self.clear_columns(cols), True),
                   None,
                   ("Zeilen aufsteigend sortieren", lambda: self.sort_by_column(visual), True),
                   ("Zeilen absteigend sortieren", lambda: self.sort_by_column(visual, True), True),
                   None,
                   (f"{word} ausblenden", lambda: [self.set_column_hidden(v, True) for v in cols],
                    len(self.hidden_visual() | set(cols)) < len(labels)),
                   ("Alle Spalten einblenden", self.show_all_columns, bool(self.hidden_visual()))]
        if not ed:
            entries.append(("(feste Tabelle: Spalten lassen sich nicht ändern)", lambda: None, False))
        return self._fill_menu(QMenu(self.grid), entries + [None] + self._undo_entries())

    def _column_header_menu(self, pos) -> None:
        h = self.grid.horizontalHeader()
        c = h.logicalIndexAt(pos)
        if c >= 0:
            self.column_menu(h.visualIndex(c)).exec(h.mapToGlobal(pos))


def load_json_meta(db, key: str, default):
    try:
        value = json.loads(db.meta(key) or "null")
    except ValueError:
        value = None
    return value if isinstance(value, type(default)) else default
