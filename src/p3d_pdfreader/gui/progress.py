"""Quelle: P3D XCHANGE 0.5.0 (unveraendert uebernommen). Fortschrittsdialog wie in der Excel-Mappe: Titel, Meldung, Balken, "Schritt x von y" und Prozent."""
from __future__ import annotations

from contextlib import contextmanager

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout

from main_gui_kit.theme import LIGHT


class ProgressDialog(QDialog):
    def __init__(self, title: str, parent=None, steps: int = 1):
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint | Qt.CustomizeWindowHint)
        self.setModal(True)
        self.setWindowModality(Qt.WindowModal)
        self.setObjectName("ProgressDialog")
        # Feste Breite, Meldung einzeilig: was nicht passt, wird am Ende mit "…" gekuerzt (kein Umbruch,
        # keine springende Dialoghoehe).
        self.setFixedWidth(760)
        self._margins = (18, 16, 18, 12)
        self._full_message = ""
        self.setStyleSheet(
            f"#ProgressDialog {{ background: #F0F0F0; border: 1px solid #A0A0A0; }}"
            f"#ProgressDialog QLabel {{ background: transparent; color: #1F1F1F; }}"
            f"QProgressBar {{ border: none; background: white; height: 8px; }}"
            f"QProgressBar::chunk {{ background: #0F5EA8; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self._margins)
        layout.setSpacing(8)
        self.title_label = QLabel(title)
        font = self.title_label.font()
        font.setBold(True)
        font.setPointSizeF(10)
        self.title_label.setFont(font)
        self.message = QLabel("")
        self.message.setWordWrap(False)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        row = QHBoxLayout()
        self.step_label = QLabel("")
        self.percent_label = QLabel("0 %")
        for label in (self.step_label, self.percent_label):
            label.setStyleSheet(f"color: {LIGHT.txt_muted}; background: transparent;")
        row.addWidget(self.step_label)
        row.addStretch(1)
        row.addWidget(self.percent_label)
        for widget in (self.title_label, self.message, self.bar):
            layout.addWidget(widget)
        layout.addLayout(row)
        self.steps = max(1, steps)
        self.step = 1
        self.update_progress(0, "", 1)

    def update_progress(self, percent: int, message: str | None = None, step: int | None = None) -> None:
        percent = max(0, min(100, int(percent)))
        if message is not None and message != self._full_message:
            self._full_message = message
            available = self.width() - self._margins[0] - self._margins[2]
            self.message.setText(self.message.fontMetrics().elidedText(message, Qt.ElideRight, available))
            self.message.setToolTip(message if self.message.text() != message else "")
        if step is not None:
            self.step = step
        self.bar.setValue(percent)
        self.percent_label.setText(f"{percent} %")
        self.step_label.setText(f"Schritt {self.step} von {self.steps}")
        QApplication.processEvents()

    def open(self) -> "ProgressDialog":  # noqa: A003 - bewusst gleicher Name wie Qt, zeigt nicht-blockierend
        self.show()
        QApplication.processEvents()
        return self

    def part(self, start: int, end: int, step: int | None = None):
        """Rueckmeldung ``(erledigt, gesamt, text)`` einer Kernfunktion auf den Bereich ``start``-``end`` % abbilden."""
        def report(done: int, total: int, text: str) -> None:
            self.update_progress(start + (end - start) * done / max(1, total), text, step)
        return report


@contextmanager
def progress_task(parent, title: str, steps: int = 1, message: str = ""):
    """Fortschrittsdialog fuer einen Arbeitsschritt (Einlesen, Ausgeben, Im-/Export): zeigt sich sofort, Sanduhr waehrenddessen,
    schliesst sich auch bei Fehlern. ``with progress_task(self, "Mappe einlesen", 2) as dlg: ... dlg.update_progress(...)``"""
    window = parent.window() if parent is not None else None
    dlg = ProgressDialog(title, window, steps=steps).open()
    if message:
        dlg.update_progress(0, message, 1)
    QApplication.setOverrideCursor(Qt.WaitCursor)
    try:
        yield dlg
        dlg.update_progress(100, "Fertig")
    finally:
        QApplication.restoreOverrideCursor()
        dlg.close()
        dlg.deleteLater()
