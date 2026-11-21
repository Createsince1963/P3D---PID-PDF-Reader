"""Pfadverwaltung: PDF-Quellordner, Exportordner, Speicherorte des Tools (``config/paths.json``)."""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QVBoxLayout)

from main_gui_kit.buttons import ButtonKind, action_button

from .. import paths
from . import last_paths
from .design import NOTE_QSS


def open_in_explorer(path) -> None:
    path = Path(path)
    if path.exists():
        os.startfile(str(path if path.is_dir() else path.parent))  # noqa: S606 - nur Explorer oeffnen


class PathsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pfade verwalten")
        self.resize(720, 460)
        self.settings = paths.PathSettings.load()
        root = QVBoxLayout(self)

        box = QGroupBox("PDF-Quellordner (werden beim Scan durchsucht, inkl. Unterordner)")
        lay = QVBoxLayout(box)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(lambda item: open_in_explorer(item.data(Qt.UserRole)))
        lay.addWidget(self.list)
        row = QHBoxLayout()
        for text, kind, slot in (("Hinzufügen", ButtonKind.SECONDARY, self._add),
                                 ("Entfernen", ButtonKind.DANGER, self._remove),
                                 ("Im Explorer", ButtonKind.NEUTRAL, self._explore)):
            b = action_button(text, kind)
            b.clicked.connect(slot)
            row.addWidget(b)
        row.addStretch(1)
        lay.addLayout(row)
        root.addWidget(box)

        form_box = QGroupBox("Export und Speicherorte")
        form = QFormLayout(form_box)
        exp_row = QHBoxLayout()
        self.export_edit = QLineEdit(self.settings.export_dir)
        self.export_edit.setPlaceholderText(str(paths.home_dir() / "exports"))
        pick = action_button("…", ButtonKind.NEUTRAL)
        pick.clicked.connect(self._pick_export)
        exp_row.addWidget(self.export_edit, 1)
        exp_row.addWidget(pick)
        form.addRow("Exportordner", exp_row)
        for label, value in (("Datenordner", paths.home_dir()), ("Konfiguration", paths.config_dir()),
                             ("Tag-Muster", paths.patterns_file()), ("Logs", paths.logs_dir())):
            lbl = QLabel(f'<a href="file:///{value}">{value}</a>')
            lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
            lbl.linkActivated.connect(lambda _l, v=value: open_in_explorer(v))
            form.addRow(label, lbl)
        note = QLabel(f"Datenordner über Umgebungsvariable {paths.ENV_HOME} änderbar.")
        note.setStyleSheet(NOTE_QSS)
        form.addRow("", note)
        root.addWidget(form_box)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self._fill()

    def _fill(self) -> None:
        self.list.clear()
        for s in self.settings.sources:
            ok = Path(s).exists()
            item = QListWidgetItem(("✓  " if ok else "✗  ") + s)
            item.setData(Qt.UserRole, s)
            item.setToolTip("vorhanden" if ok else "Ordner nicht gefunden")
            self.list.addItem(item)

    def _add(self) -> None:
        folder = last_paths.open_dir(self, "PDF-Quellordner wählen")
        if folder and self.settings.add_source(folder):
            self._fill()

    def _remove(self) -> None:
        for item in self.list.selectedItems():
            self.settings.remove_source(item.data(Qt.UserRole))
        self._fill()

    def _explore(self) -> None:
        item = self.list.currentItem()
        if item:
            open_in_explorer(item.data(Qt.UserRole))

    def _pick_export(self) -> None:
        folder = last_paths.open_dir(self, "Exportordner wählen", self.export_edit.text(), last_paths.EXPORT)
        if folder:
            self.export_edit.setText(str(Path(folder).resolve()))

    def _save(self) -> None:
        text = self.export_edit.text().strip()
        self.settings.export_dir = str(Path(text).resolve()) if text else ""
        self.settings.save()
        self.accept()
