"""Optionstabelle „Prueftypen“ (1.0.58): welche Tag-Typen geprueft werden."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QHeaderView, QLabel, QTableWidget,
                               QTableWidgetItem, QVBoxLayout)

from main_gui_kit.buttons import ButtonKind, action_button

from ..core.patterns import TAG_TYPES
from . import appearance
from .design import NOTE_QSS


class TypeDialog(QDialog):
    """Tabelle: Prüfen (Haken), Typ, Anzahl Tags, PDFs. ``excluded()`` = abgewählte Typen."""

    def __init__(self, results: list, excluded, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prüftypen")
        self.resize(520, 420)
        counts: dict[str, list[int]] = {t: [0, 0] for t in TAG_TYPES}
        for result in results:
            seen = set()
            for tag in result.tags:
                entry = counts.setdefault(tag.type, [0, 0])
                entry[0] += 1
                entry[1] += tag.type not in seen
                seen.add(tag.type)
        for name in excluded:
            counts.setdefault(name, [0, 0])
        lay = QVBoxLayout(self)
        note = QLabel("Nur angehakte Typen werden geprüft: Tabellen, Viewer, Redline, Multi-Tag-PDF, Review und Export.")
        note.setWordWrap(True)
        note.setStyleSheet(NOTE_QSS)
        lay.addWidget(note)
        table = self.table = QTableWidget(len(counts), 4)
        table.setHorizontalHeaderLabels(["Prüfen", "Typ", "Anzahl Tags", "PDFs"])
        table.horizontalHeader().setStyleSheet(appearance.plain_header_qss())
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.verticalHeader().hide()
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        for row, (name, (tags, pdfs)) in enumerate(counts.items()):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            check.setCheckState(Qt.Unchecked if name in excluded else Qt.Checked)
            table.setItem(row, 0, check)
            for column, value in enumerate((name, tags, pdfs), start=1):
                item = QTableWidgetItem(str(value))
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                table.setItem(row, column, item)
        table.setColumnWidth(0, 60)
        table.cellDoubleClicked.connect(lambda row, _c: self.only(table.item(row, 1).text()))
        table.itemChanged.connect(lambda _i: self._update_ok())
        lay.addWidget(table, 1)
        row = QHBoxLayout()
        for text, state in (("Alle", True), ("Keine", False)):
            button = action_button(text, ButtonKind.NEUTRAL)
            button.clicked.connect(lambda _c=False, s=state: self.set_all(s))
            row.addWidget(button)
        hint = QLabel("Doppelklick auf eine Zeile: nur diesen Typ")
        hint.setStyleSheet(NOTE_QSS)
        row.addWidget(hint)
        row.addStretch(1)
        lay.addLayout(row)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        lay.addWidget(self.buttons)
        self._update_ok()

    def _rows(self):
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0) is not None and self.table.item(row, 1) is not None:
                yield self.table.item(row, 0), self.table.item(row, 1).text()

    def set_all(self, on: bool) -> None:
        for check, _name in self._rows():
            check.setCheckState(Qt.Checked if on else Qt.Unchecked)

    def only(self, wanted: str) -> None:
        for check, name in self._rows():
            check.setCheckState(Qt.Checked if name == wanted else Qt.Unchecked)

    def excluded(self) -> list[str]:
        return [name for check, name in self._rows() if check.checkState() != Qt.Checked]

    def _update_ok(self) -> None:
        if hasattr(self, "buttons"):
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(
                any(check.checkState() == Qt.Checked for check, _n in self._rows()))
