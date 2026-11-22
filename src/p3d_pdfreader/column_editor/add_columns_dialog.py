"""Bulk "Add columns" dialog (tile editor, Add column tab): create several blank columns at once from typed or pasted
names. Plain Qt Widgets (like the Excel export designer's "Group by with calculations" dialog) - no new QML, the
existing "Add columns from another list" (lookup import, QML `LookupDialog`) is untouched and stays available next to
this.

Each new column is created through `ColumnEditorController.addColumns` (reuses add_derived / add_calculated, the same
plumbing every other calculated column uses - D9: the type is set through an explicit convert node); nothing here talks
to the table or the source table directly.
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog, QHBoxLayout, QHeaderView, QLabel,
                                QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout)

from .domain.column_types import ColumnType

FORMAT_ORDER = [ColumnType.TEXT, ColumnType.INTEGER, ColumnType.DECIMAL, ColumnType.DATE, ColumnType.DATETIME, ColumnType.BOOLEAN]
FORMAT_NAMES = {ColumnType.TEXT: "Text", ColumnType.INTEGER: "Ganzzahl", ColumnType.DECIMAL: "Dezimalzahl",
                ColumnType.DATE: "Datum", ColumnType.DATETIME: "Datum/Zeit", ColumnType.BOOLEAN: "Wahr/Falsch"}
FORMAT_ALIASES = {
    "text": ColumnType.TEXT, "string": ColumnType.TEXT,
    "number": ColumnType.DECIMAL, "decimal": ColumnType.DECIMAL, "decimal number": ColumnType.DECIMAL, "float": ColumnType.DECIMAL,
    "integer": ColumnType.INTEGER, "whole number": ColumnType.INTEGER, "whole": ColumnType.INTEGER, "int": ColumnType.INTEGER,
    "date": ColumnType.DATE,
    "date & time": ColumnType.DATETIME, "date and time": ColumnType.DATETIME, "date/time": ColumnType.DATETIME, "datetime": ColumnType.DATETIME,
    "boolean": ColumnType.BOOLEAN, "ganzzahl": ColumnType.INTEGER, "dezimalzahl": ColumnType.DECIMAL, "zahl": ColumnType.DECIMAL, "datum": ColumnType.DATE, "datum/zeit": ColumnType.DATETIME, "wahr/falsch": ColumnType.BOOLEAN, "ganzzahl": ColumnType.INTEGER, "dezimalzahl": ColumnType.DECIMAL, "zahl": ColumnType.DECIMAL, "datum": ColumnType.DATE, "datum/zeit": ColumnType.DATETIME, "wahr/falsch": ColumnType.BOOLEAN, "ganzzahl": ColumnType.INTEGER, "dezimalzahl": ColumnType.DECIMAL, "zahl": ColumnType.DECIMAL, "datum": ColumnType.DATE, "datum/zeit": ColumnType.DATETIME, "wahr/falsch": ColumnType.BOOLEAN, "bool": ColumnType.BOOLEAN, "true/false": ColumnType.BOOLEAN, "true / false": ColumnType.BOOLEAN,
}
NAME_COL, FORMAT_COL = 0, 1
BAD_BG = QColor("#FBE3E1")
OK_BG = QColor("#FFFFFF")


def parse_format(text: str) -> ColumnType | None:
    """Empty text -> Text (the default). Unmatched text -> None (caller marks the cell)."""
    t = text.strip().lower()
    return ColumnType.TEXT if not t else FORMAT_ALIASES.get(t)


class AddColumnsDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.ctl = controller
        self.setWindowTitle("Spalten hinzufügen")
        self.setMinimumSize(520, 420)
        lay = QVBoxLayout(self)
        hint = QLabel("Spaltennamen aus Excel oder einem Texteditor einfügen (einer je Zeile; zwei durch Tab getrennte Spalten = "
                      "Name + Format) oder unten Zeilen anlegen. Standardformat: Text.")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        self.table = QTableWidget(0, 2, self)
        self.table.setHorizontalHeaderLabels(["Spaltenname", "Format"])
        self.table.horizontalHeader().setSectionResizeMode(NAME_COL, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(FORMAT_COL, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        lay.addWidget(self.table, 1)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        lay.addWidget(self.status)
        row1 = QHBoxLayout()
        for text, cb in (("Zeile hinzufügen", self._add_empty_row), ("Gewählte Zeile(n) löschen", self._delete_selected),
                         ("Aus Zwischenablage einfügen", self._paste), ("Leeren", self._clear)):
            b = QPushButton(text)
            b.clicked.connect(cb)
            row1.addWidget(b)
        row1.addStretch(1)
        lay.addLayout(row1)
        row2 = QHBoxLayout()
        row2.addStretch(1)
        cancel = QPushButton("Abbrechen")
        cancel.clicked.connect(self.reject)
        add_btn = QPushButton("Spalten hinzufügen")
        add_btn.setDefault(True)
        add_btn.clicked.connect(self._add_columns)
        row2.addWidget(cancel)
        row2.addWidget(add_btn)
        lay.addLayout(row2)
        self._add_empty_row()

    # ---- grid rows -----------------------------------------------------------------------------------------------------
    def _add_empty_row(self) -> None:
        self._add_row("", ColumnType.TEXT)

    def _add_row(self, name: str, fmt: ColumnType) -> None:
        r = self.table.rowCount()
        self.table.insertRow(r)
        item = QTableWidgetItem(name)
        self.table.setItem(r, NAME_COL, item)
        combo = QComboBox()
        for t in FORMAT_ORDER:
            combo.addItem(FORMAT_NAMES[t], t.value)
        combo.setCurrentIndex(FORMAT_ORDER.index(fmt) if fmt in FORMAT_ORDER else 0)
        self.table.setCellWidget(r, FORMAT_COL, combo)

    def _delete_selected(self) -> None:
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.table.removeRow(r)
        if self.table.rowCount() == 0:
            self._add_empty_row()

    def _clear(self) -> None:
        self.table.setRowCount(0)
        self.status.setText("")
        self._add_empty_row()

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt override
        if event.matches(QKeySequence.Paste) and self.table.hasFocus():
            self._paste()
            return
        super().keyPressEvent(event)

    def _paste(self) -> None:
        text = QApplication.clipboard().text()
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if self.table.rowCount() == 1 and not self._row_name(0).strip():
            self.table.removeRow(0)                                 # replace the single still-empty starter row
        added, unknown = 0, 0
        for line in lines:
            if not line.strip():
                continue
            parts = line.split("\t")
            name = parts[0].strip()
            if not name:
                continue
            fmt_text = parts[1].strip() if len(parts) > 1 else ""
            fmt = parse_format(fmt_text)
            self._add_row(name, fmt or ColumnType.TEXT)
            if fmt_text and fmt is None:
                unknown += 1
                self._mark_bad(self.table.rowCount() - 1, FORMAT_COL, f"Unknown format \"{fmt_text}\" – eines aus der Liste wählen.")
            added += 1
        if self.table.rowCount() == 0:
            self._add_empty_row()
        if added:
            msg = f"{added} row(s) pasted."
            if unknown:
                msg += f" {unknown} mit unbekanntem Format (als Text gezeigt, rot markiert) – vor dem Hinzufügen korrigieren."
            self.status.setStyleSheet("color: #52606d;")
            self.status.setText(msg)
        else:
            self.status.setStyleSheet("color: #B42318;")
            self.status.setText("Nichts Brauchbares in der Zwischenablage.")

    # ---- validation ------------------------------------------------------------------------------------------------------
    def _row_name(self, r: int) -> str:
        item = self.table.item(r, NAME_COL)
        return item.text() if item else ""

    def _row_format_combo(self, r: int) -> QComboBox | None:
        return self.table.cellWidget(r, FORMAT_COL)

    def _mark_bad(self, r: int, c: int, tip: str) -> None:
        if c == NAME_COL:
            item = self.table.item(r, NAME_COL)
            if item:
                item.setBackground(BAD_BG)
                item.setToolTip(tip)
        else:
            combo = self._row_format_combo(r)
            if combo:
                combo.setStyleSheet(f"background: {BAD_BG.name()};")
                combo.setToolTip(tip)

    def _clear_marks(self) -> None:
        for r in range(self.table.rowCount()):
            item = self.table.item(r, NAME_COL)
            if item:
                item.setBackground(OK_BG)
                item.setToolTip("")
            combo = self._row_format_combo(r)
            if combo:
                combo.setStyleSheet("")
                combo.setToolTip("")

    def _validate(self) -> list[tuple[str, ColumnType]] | None:
        """The validated (name, type) list, or None with `self.status` set to why."""
        self._clear_marks()
        existing = {self.ctl.model.source.label(k).strip().casefold() for k in self.ctl.model.keys()}
        seen: dict[str, int] = {}
        problems: list[str] = []
        result: list[tuple[str, ColumnType]] = []
        for r in range(self.table.rowCount()):
            name = self._row_name(r).strip()
            combo = self._row_format_combo(r)
            fmt = ColumnType(combo.currentData()) if combo is not None else ColumnType.TEXT
            if not name:
                if self.table.rowCount() > 1:
                    self._mark_bad(r, NAME_COL, "Name ist leer.")
                    problems.append(f"Row {r + 1}: der Name ist leer.")
                continue
            key = name.casefold()
            if key in existing:
                self._mark_bad(r, NAME_COL, f"A column named \"{name}\" gibt es schon.")
                problems.append(f"Row {r + 1}: \"{name}\" gibt es schon.")
                continue
            if key in seen:
                self._mark_bad(r, NAME_COL, f"\"{name}\" steht mehrfach in der Liste.")
                self._mark_bad(seen[key], NAME_COL, f"\"{name}\" steht mehrfach in der Liste.")
                problems.append(f"Row {r + 1}: \"{name}\" doppelt zu Zeile {seen[key] + 1}.")
                continue
            seen[key] = r
            result.append((name, fmt))
        if problems:
            self.status.setStyleSheet("color: #B42318;")
            self.status.setText("Spalten können nicht hinzugefügt werden:\n" + "\n".join(problems))
            return None
        if not result:
            self.status.setStyleSheet("color: #B42318;")
            self.status.setText("Mindestens einen Spaltennamen eingeben.")
            return None
        return result

    def _add_columns(self) -> None:
        result = self._validate()
        if result is None:
            return
        err = self.ctl.addColumns([(name, fmt.value) for name, fmt in result])
        if err:
            self.status.setStyleSheet("color: #B42318;")
            self.status.setText(err)
            return
        n = len(result)
        QMessageBox.information(self, "Spalten hinzufügen", "1 Spalte hinzugefügt." if n == 1 else f"{n} Spalten hinzugefügt.")
        self.accept()


__all__ = ["AddColumnsDialog"]
