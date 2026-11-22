"""Rechtsklick-Funktionen der Tabellen wie in P3D XCHANGE (Nutzervorgabe 2026-11-21).

* Rechtsklick auf das Excel-Symbol in der Tabellenecke: Dialog „Spalten …“ (verschieben, ein-/ausblenden, Standard) -
  Muster: XCHANGE 0.5.0 ``gui/columns_dialog.py`` (ohne Read only / Write, der PDF Reader schreibt keine Plant-3D-Daten).
* Rechtsklick in die Tabelle: Kopieren, nach dem Wert der Zelle filtern, Filter zuruecksetzen, Spalten …, nach Excel.
* Rechtsklick auf den Spaltenkopf: unveraendert das Kit-Menue (Spalte ausblenden, verschieben, Ausrichtung, Teilreiter).

Werkzeugeigene Eintraege: ``table._cell_menu_hook(menu, index)`` (Index des Proxy-Modells)."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QHBoxLayout, QHeaderView, QLabel, QMenu, QMessageBox,
                               QTableView, QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout)

from main_gui_kit.buttons import ButtonKind, action_button, equalize_widths

from .design import NOTE_QSS, TITLE_QSS

YES, NO = "Ja", "Nein"


# ---- Spaltenlayout -------------------------------------------------------------------------------------------------
def column_names(table: QTableView) -> list[str]:
    model = table.model()
    if model is None:
        return []
    return [str(model.headerData(c, Qt.Horizontal, Qt.DisplayRole) or "") for c in range(model.columnCount())]


def apply_columns(table: QTableView, order: list[int], hidden: set[int]) -> None:
    """Spalten in ``order`` (logische Indizes, von links) anordnen und ``hidden`` ausblenden."""
    header = table.horizontalHeader()
    for target, logical in enumerate(order):
        visual = header.visualIndex(logical)
        if visual >= 0 and visual != target:
            header.moveSection(visual, target)
    for logical in range(header.count()):
        table.setColumnHidden(logical, logical in hidden)
    reposition = getattr(header, "_position_editors", None)      # Filterfelder des Kit-Kopfs nachfuehren
    if reposition is not None:
        reposition()
    saver = getattr(table, "_shared_layout_saver", None)          # Anpassung des Nutzers als Standard merken
    if saver is not None:
        saver.start(0)


class ColumnsDialog(QDialog):
    """Reihenfolge (oben = links) und Sichtbarkeit der Spalten; „Standard“ = Zustand wie eingelesen."""

    def __init__(self, table: QTableView, parent=None):
        super().__init__(parent or table.window())
        self.setWindowTitle("Spalten")
        self.resize(520, 560)
        self.table = table
        header = table.horizontalHeader()
        names = column_names(table)
        order = sorted(range(len(names)), key=header.visualIndex)
        self.entries = [{"logical": c, "name": names[c], "visible": not table.isColumnHidden(c)} for c in order]
        layout = QVBoxLayout(self)
        title = QLabel("Spalten")
        title.setStyleSheet(TITLE_QSS)
        layout.addWidget(title)
        note = QLabel("„Anzeigen“: Ja = Spalte sichtbar, Nein = ausgeblendet; die Reihenfolge von oben nach unten ist "
                      "die Reihenfolge in der Tabelle. „Standard“ stellt den Zustand wie eingelesen wieder her.")
        note.setWordWrap(True)
        note.setStyleSheet(NOTE_QSS)
        layout.addWidget(note)
        from .sheet import plain_header_qss
        self.grid = QTableWidget(0, 2)
        self.grid.setHorizontalHeaderLabels(["Spalte", "Anzeigen"])
        self.grid.horizontalHeader().setStyleSheet(plain_header_qss())
        self.grid.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.grid.verticalHeader().setVisible(False)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.grid.setSelectionMode(QAbstractItemView.SingleSelection)
        self.grid.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.grid.itemChanged.connect(self._item_changed)
        layout.addWidget(self.grid, 1)
        row = QHBoxLayout()
        self.up_btn = action_button("Nach oben", ButtonKind.NEUTRAL)
        self.down_btn = action_button("Nach unten", ButtonKind.NEUTRAL)
        self.default_btn = action_button("Standard", ButtonKind.NEUTRAL)
        self.default_btn.setToolTip("Reihenfolge und Sichtbarkeit wie eingelesen")
        cancel, ok = action_button("Abbrechen", ButtonKind.NEUTRAL), action_button("Übernehmen", ButtonKind.PRIMARY)
        equalize_widths([cancel, ok])
        self.up_btn.clicked.connect(lambda: self._move(-1))
        self.down_btn.clicked.connect(lambda: self._move(1))
        self.default_btn.clicked.connect(self.set_default)
        cancel.clicked.connect(self.reject)
        ok.clicked.connect(self.accept)
        for widget in (self.up_btn, self.down_btn, self.default_btn):
            row.addWidget(widget)
        row.addStretch(1)
        row.addWidget(cancel)
        row.addWidget(ok)
        layout.addLayout(row)
        self._render(0)

    def _render(self, select: int = -1) -> None:
        self.grid.blockSignals(True)
        self.grid.setRowCount(len(self.entries))
        for r, entry in enumerate(self.entries):
            name = QTableWidgetItem(entry["name"])
            name.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.grid.setItem(r, 0, name)
            show = QTableWidgetItem(YES if entry["visible"] else NO)
            show.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
            show.setCheckState(Qt.Checked if entry["visible"] else Qt.Unchecked)
            show.setToolTip("Haken = Ja (Spalte anzeigen), ohne Haken = Nein (ausblenden)")
            self.grid.setItem(r, 1, show)
        self.grid.blockSignals(False)
        self.grid.resizeColumnToContents(1)
        if 0 <= select < len(self.entries):
            self.grid.selectRow(select)

    def _item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 1:
            return
        on = item.checkState() == Qt.Checked
        self.entries[item.row()]["visible"] = on
        self.grid.blockSignals(True)
        item.setText(YES if on else NO)
        self.grid.blockSignals(False)

    def _move(self, offset: int) -> None:
        row = self.grid.currentRow()
        target = row + offset
        if row < 0 or not 0 <= target < len(self.entries):
            return
        self.entries[row], self.entries[target] = self.entries[target], self.entries[row]
        self._render(target)

    def set_default(self) -> None:
        hidden = set(getattr(self.table, "_default_hidden", ()))
        self.entries.sort(key=lambda e: e["logical"])
        for entry in self.entries:
            entry["visible"] = entry["logical"] not in hidden
        self._render(0)

    def order(self) -> list[int]:
        return [e["logical"] for e in self.entries]

    def hidden(self) -> set[int]:
        return {e["logical"] for e in self.entries if not e["visible"]}

    def accept(self) -> None:
        if not any(e["visible"] for e in self.entries):
            QMessageBox.information(self, "Spalten", "Mindestens eine Spalte muss sichtbar bleiben.")
            return
        apply_columns(self.table, self.order(), self.hidden())
        super().accept()


def open_columns_dialog(table: QTableView) -> bool:
    if table.model() is None or table.model().columnCount() == 0:
        return False
    return bool(ColumnsDialog(table).exec())


# ---- Zellen: Kopieren und Filtern ----------------------------------------------------------------------------------
def selection_text(table: QTableView) -> str:
    """Markierte Zellen als Tabulator-Text (Zeilen und sichtbare Spalten in angezeigter Reihenfolge)."""
    indexes = table.selectionModel().selectedIndexes() if table.selectionModel() else []
    if not indexes:
        return ""
    header = table.horizontalHeader()
    rows = sorted({i.row() for i in indexes})
    cols = sorted({i.column() for i in indexes if not table.isColumnHidden(i.column())}, key=header.visualIndex)
    chosen = {(i.row(), i.column()) for i in indexes}
    model = table.model()
    lines = []
    for r in rows:
        cells = [str(model.index(r, c).data(Qt.DisplayRole) or "") if (r, c) in chosen else "" for c in cols]
        lines.append("\t".join(cells))
    return "\n".join(lines)


def row_text(table: QTableView, row: int, with_header: bool = False) -> str:
    model, header = table.model(), table.horizontalHeader()
    cols = [header.logicalIndex(v) for v in range(header.count())]
    cols = [c for c in cols if c >= 0 and not table.isColumnHidden(c)]
    line = "\t".join(str(model.index(row, c).data(Qt.DisplayRole) or "") for c in cols)
    if not with_header:
        return line
    return "\t".join(str(model.headerData(c, Qt.Horizontal, Qt.DisplayRole) or "") for c in cols) + "\n" + line


def filter_by_value(table: QTableView, column: int, value: str) -> bool:
    """Spalte auf genau diesen Wert einschraenken (Wertauswahl wie im Filterdialog des Kits)."""
    model = table.model()
    if model is None or not hasattr(model, "set_filter_values"):
        return False
    if hasattr(model, "set_column_filter"):
        model.set_column_filter(column, "")
    model.set_filter_values(column, [value])
    header = table.horizontalHeader()
    editors = getattr(header, "editors", None) or []
    if column < len(editors) and column in getattr(model, "value_filters", {}):
        total = len(model.available_values(column)) if hasattr(model, "available_values") else 0
        editors[column].blockSignals(True)
        editors[column].setText(f"1 / {total}" if total else "1")
        editors[column].blockSignals(False)
    signal = getattr(header, "filterChanged", None)
    if signal is not None:
        signal.emit()
    return True


def clear_column_filter(table: QTableView, column: int) -> None:
    model = table.model()
    if model is None:
        return
    if hasattr(model, "set_filter_values"):
        model.set_filter_values(column, None)
    if hasattr(model, "set_column_filter"):
        model.set_column_filter(column, "")
    editors = getattr(table.horizontalHeader(), "editors", None) or []
    if column < len(editors):
        editors[column].blockSignals(True)
        editors[column].clear()
        editors[column].blockSignals(False)
    signal = getattr(table.horizontalHeader(), "filterChanged", None)
    if signal is not None:
        signal.emit()


def _column_filtered(table: QTableView, column: int) -> bool:
    model = table.model()
    return column in (getattr(model, "value_filters", {}) or {}) or bool((getattr(model, "column_filters", {}) or {}).get(column))


def _short(text: str, limit: int = 40) -> str:
    text = text.replace("\n", " ")
    return text if len(text) <= limit else text[:limit - 1] + "…"


def cell_menu(table: QTableView, index: QModelIndex, *, on_clear_all: Callable[[], None] | None = None,
              on_filter: Callable[[], None] | None = None, on_export: Callable[[], None] | None = None) -> QMenu:
    """Kontextmenue einer Zelle aufbauen (fuer Tests getrennt von ``exec``)."""
    menu = QMenu(table)
    clip = QGuiApplication.clipboard()
    valid = index.isValid()
    value = str(index.data(Qt.DisplayRole) or "") if valid else ""
    column = index.column() if valid else -1
    name = str(table.model().headerData(column, Qt.Horizontal, Qt.DisplayRole) or "") if valid else ""
    copy = menu.addAction("Kopieren", lambda: clip.setText(selection_text(table)))
    copy.setShortcut("Ctrl+C")
    copy.setEnabled(bool(table.selectionModel() and table.selectionModel().hasSelection()))
    menu.addAction("Zeile kopieren", lambda: clip.setText(row_text(table, index.row()))).setEnabled(valid)
    menu.addAction("Zeile mit Überschriften kopieren",
                   lambda: clip.setText(row_text(table, index.row(), with_header=True))).setEnabled(valid)
    menu.addSeparator()

    def by_value() -> None:
        if filter_by_value(table, column, value) and on_filter:
            on_filter()

    def clear_col() -> None:
        clear_column_filter(table, column)
        if on_filter:
            on_filter()

    menu.addAction(f"Nur „{_short(value)}“ in „{name}“ zeigen" if valid else "Nach diesem Wert filtern",
                   by_value).setEnabled(valid and hasattr(table.model(), "set_filter_values"))
    menu.addAction(f"Filter von „{name}“ zurücksetzen" if valid else "Filter dieser Spalte zurücksetzen",
                   clear_col).setEnabled(valid and _column_filtered(table, column))
    if on_clear_all is not None:
        menu.addAction("Alle Filter zurücksetzen", on_clear_all)
    menu.addSeparator()
    menu.addAction("Spalten …", lambda: open_columns_dialog(table))
    if on_export is not None:
        menu.addAction("Nach Excel …", on_export)
    hook = getattr(table, "_cell_menu_hook", None)
    if callable(hook):
        try:
            hook(menu, index)
        except Exception:  # noqa: BLE001 - ein Werkzeug-Eintrag darf das Menue nie verhindern
            pass
    return menu


def install_table_menus(table: QTableView, excel_button: QToolButton | None = None, *,
                        on_clear_all: Callable[[], None] | None = None, on_filter: Callable[[], None] | None = None,
                        on_export: Callable[[], None] | None = None) -> None:
    """Rechtsklick in der Tabelle und auf dem Excel-Symbol einrichten; Standard-Spaltenlayout merken."""
    model = table.model()
    count = model.columnCount() if model is not None else 0
    table._default_hidden = {c for c in range(count) if table.isColumnHidden(c)}
    viewport = table.viewport()
    viewport.setContextMenuPolicy(Qt.CustomContextMenu)

    def open_menu(pos) -> None:
        index = table.indexAt(pos)
        if index.isValid() and table.selectionModel() and not table.selectionModel().isSelected(index):
            table.setCurrentIndex(index)
        cell_menu(table, index, on_clear_all=on_clear_all, on_filter=on_filter,
                  on_export=on_export).exec(viewport.mapToGlobal(pos))

    viewport.customContextMenuRequested.connect(open_menu)
    table._cell_menu_open = open_menu
    if excel_button is not None:
        excel_button.setToolTip(excel_button.toolTip() + "\nRechtsklick: Spalten …")
        excel_button.setContextMenuPolicy(Qt.CustomContextMenu)
        excel_button.customContextMenuRequested.connect(lambda _p: open_columns_dialog(table))
