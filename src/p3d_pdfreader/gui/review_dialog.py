"""Review / Audit einzeln oder im Bulk: fuer die markierten (oder alle) PDFs wahlweise Redline-PDF, Excel je PDF und
eine Gesamt-Excel erzeugen. Die Auswahl der Ausgaben und der Zielordner werden gemerkt (``config/state.json``)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QRadioButton, QVBoxLayout)

from main_gui_kit.buttons import ButtonKind, action_button

from .. import paths
from . import last_paths
from .design import NOTE_QSS

STATE_KEY = "review_options"


@dataclass
class ReviewOptions:
    only_marked: bool = True
    redline: bool = True
    excel_each: bool = False
    excel_total: bool = True
    subfolder: bool = True
    folder: str = ""
    multitag: bool = False


class ReviewDialog(QDialog):
    def __init__(self, marked: int, total: int, parent=None, linked: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Review / Audit")
        self.setMinimumWidth(560)
        saved = last_paths.get_value(STATE_KEY, {}) or {}
        opts = ReviewOptions(**{k: v for k, v in saved.items() if k in ReviewOptions.__dataclass_fields__})
        root = QVBoxLayout(self)

        scope = QGroupBox("PDFs")
        lay = QVBoxLayout(scope)
        self.rb_marked = QRadioButton(f"Markierte PDFs ({marked})")
        self.rb_all = QRadioButton(f"Alle gescannten PDFs ({total})")
        group = QButtonGroup(self)
        group.addButton(self.rb_marked)
        group.addButton(self.rb_all)
        (self.rb_marked if opts.only_marked and marked else self.rb_all).setChecked(True)
        self.rb_marked.setEnabled(marked > 0)
        lay.addWidget(self.rb_marked)
        lay.addWidget(self.rb_all)
        hint = QLabel("Mehrere PDFs in der Dateiliste mit Strg- oder Umschalt-Klick markieren.")
        hint.setStyleSheet(NOTE_QSS)
        lay.addWidget(hint)
        root.addWidget(scope)

        out = QGroupBox("Ausgaben")
        lay = QVBoxLayout(out)
        self.cb_redline = QCheckBox("Redline-PDF je PDF (Rahmen wie im Viewer: grün korrekt, rot fehlerhaft, doppelte gelb)")
        self.cb_excel_each = QCheckBox("Review-Excel je PDF (Pos.-Nr., Review-Kommentar, Prüfstatus, Bemerkung)")
        self.cb_excel_total = QCheckBox("Review-Excel gesamt über alle gewählten PDFs")
        self.cb_multitag = QCheckBox("Multi-Tag-PDF je PDF (roter Eintrag über jedem doppelten Tag)")
        self.cb_multitag.setEnabled(linked)
        if not linked:
            self.cb_multitag.setToolTip("Braucht eine Importliste mit Datenlink 2.")
        self.cb_multitag.setChecked(bool(opts.multitag) and linked)
        self.cb_subfolder = QCheckBox("Eigenen Unterordner „Review_<Zeitstempel>“ anlegen")
        for cb, value in ((self.cb_redline, opts.redline), (self.cb_excel_each, opts.excel_each),
                          (self.cb_excel_total, opts.excel_total), (self.cb_subfolder, opts.subfolder)):
            cb.setChecked(bool(value))
            lay.addWidget(cb)
        lay.insertWidget(1, self.cb_multitag)
        row = QHBoxLayout()
        self.folder = QLineEdit(opts.folder if opts.folder and Path(opts.folder).is_dir() else str(paths.exports_dir()))
        pick = action_button("…", ButtonKind.NEUTRAL)
        pick.clicked.connect(self._pick)
        row.addWidget(QLabel("Zielordner"))
        row.addWidget(self.folder, 1)
        row.addWidget(pick)
        lay.addLayout(row)
        root.addWidget(out)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Review starten")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _pick(self) -> None:
        folder = last_paths.open_dir(self, "Zielordner wählen", self.folder.text(), last_paths.EXPORT)
        if folder:
            self.folder.setText(str(Path(folder).resolve()))

    def options(self) -> ReviewOptions:
        return ReviewOptions(self.rb_marked.isChecked(), self.cb_redline.isChecked(), self.cb_excel_each.isChecked(),
                             self.cb_excel_total.isChecked(), self.cb_subfolder.isChecked(), self.folder.text().strip(),
                             self.cb_multitag.isChecked())

    def _accept(self) -> None:
        o = self.options()
        if not (o.redline or o.multitag or o.excel_each or o.excel_total):
            self.cb_redline.setFocus()
            return
        if not o.folder:
            return
        last_paths.set_value(STATE_KEY, o.__dict__)
        self.accept()
